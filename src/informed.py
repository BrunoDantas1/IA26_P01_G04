"""Comparação de pesquisas informadas no cenário inicial da Parte A."""

import heapq
from itertools import count
from time import perf_counter
from typing import Callable

import pandas as pd

from model import Problem, State


def heuristic(problem: Problem, state: State, vehicle_id: int) -> float:
    """Estima km restantes pela maior cadeia individual ainda necessária.

    Cada cadeia inclui recolha (se faltar), entrega e regresso ao depósito.
    Ignora janelas, espera e partilha de deslocações entre artigos. Não calcula
    uma rota completa nem garante que o Greedy encontre a solução ótima.
    """
    depot = problem.vehicles[vehicle_id].center_location_id
    estimates = [problem.get_travel_info(state.location_id, depot)[0]]
    for request in problem.requests:
        if request.item_id in state.delivered_items:
            continue
        if request.item_id in state.picked_items:
            remaining = problem.get_travel_info(
                state.location_id, request.delivery_location_id
            )[0]
        else:
            remaining = problem.get_travel_info(
                state.location_id, request.pickup_location_id
            )[0]
            remaining += problem.get_travel_info(
                request.pickup_location_id, request.delivery_location_id
            )[0]
        remaining += problem.get_travel_info(request.delivery_location_id, depot)[0]
        estimates.append(remaining)
    return max(estimates)


def heuristic_mst(problem: Problem, state: State, vehicle_id: int) -> float:
    """Estima km restantes pela árvore de expansão mínima dos locais obrigatórios.

    Inclui posição atual, depósito, recolhas pendentes e entregas pendentes,
    sem repetir locais. Usa Prim e o menor custo entre os dois sentidos de
    cada ligação. Ignora ordem, capacidade e janelas temporais. Qualquer rota
    viável liga estes locais e custa pelo menos esta árvore, no dataset atual
    com distâncias que respeitam a desigualdade triangular.
    """
    depot = problem.vehicles[vehicle_id].center_location_id
    locations = {state.location_id, depot}
    for request in problem.requests:
        if request.item_id in state.delivered_items:
            continue
        locations.add(request.delivery_location_id)
        if request.item_id not in state.picked_items:
            locations.add(request.pickup_location_id)

    connected = {state.location_id}
    remaining = locations - connected
    total = 0.0
    while remaining:
        distance, destination = min(
            (
                min(
                    problem.get_travel_info(origin, destination)[0],
                    problem.get_travel_info(destination, origin)[0],
                ),
                destination,
            )
            for origin in connected
            for destination in remaining
        )
        total += distance
        connected.add(destination)
        remaining.remove(destination)
    return total


def greedy_best_first(
    problem: Problem, vehicle_id: int, start_time: pd.Timestamp,
    heuristic_function: Callable[[Problem, State, int], float] = heuristic,
) -> tuple[State | None, int]:
    """Ordena a fronteira apenas por h(n); conta chamadas a actions().

    O contador desempata prioridades sem comparar objetos State. Não é preciso
    um conjunto de visitados neste espaço finito: cada artigo só é recolhido e
    entregue uma vez, e o regresso termina a rota.
    """
    initial = problem.initial_state(vehicle_id, start_time)
    tie_breaker = count()
    frontier = [(heuristic_function(problem, initial, vehicle_id), next(tie_breaker), initial)]
    expanded = 0

    while frontier:
        _, _, state = heapq.heappop(frontier)
        if problem.is_goal(state, vehicle_id=vehicle_id):
            return state, expanded
        expanded += 1
        for successor in problem.actions(state, vehicle_id):
            heapq.heappush(
                frontier,
                (heuristic_function(problem, successor, vehicle_id), next(tie_breaker), successor),
            )
    return None, expanded


def a_star_search(
    problem: Problem, vehicle_id: int, start_time: pd.Timestamp,
    heuristic_function: Callable[[Problem, State, int], float] = heuristic,
) -> tuple[State | None, int]:
    """Pesquisa por f(n) = distância acumulada + estimativa restante.

    Mantém os percursos na fronteira sem eliminar estados por localização:
    hora, carga e artigos também condicionam a viabilidade. O espaço é finito,
    porque cada artigo só é recolhido e entregue uma vez e o regresso termina
    a rota. Conta uma expansão por chamada a actions(), excluindo o objetivo.
    """
    initial = problem.initial_state(vehicle_id, start_time)
    tie_breaker = count()
    initial_priority = initial.accumulated_distance_km + heuristic_function(
        problem, initial, vehicle_id
    )
    frontier = [(initial_priority, next(tie_breaker), initial)]
    expanded = 0

    while frontier:
        _, _, state = heapq.heappop(frontier)
        if problem.is_goal(state, vehicle_id=vehicle_id):
            return state, expanded
        expanded += 1
        for successor in problem.actions(state, vehicle_id):
            priority = successor.accumulated_distance_km + heuristic_function(
                problem, successor, vehicle_id
            )
            heapq.heappush(frontier, (priority, next(tie_breaker), successor))
    return None, expanded


def reconstruct_route(state: State, depot: int) -> list[tuple[str, int]]:
    """Converte o percurso acumulado para os pares aceites pelo validador."""
    route = [("start", depot)]
    for action, item_id, location_id, _ in state.route:
        route.append((action, location_id if action == "regresso" else item_id))
    return route


def main() -> None:
    start_time = pd.Timestamp("2026-10-19 07:30:00")
    problem = Problem(data_folder="data_tiny")
    target_items = {7, 10}
    problem.requests = [r for r in problem.requests if r.item_id in target_items]
    problem.requests_by_id = {r.item_id: r for r in problem.requests}

    results = []
    for algorithm_name, search in (("Greedy", greedy_best_first), ("A*", a_star_search)):
        for estimate in (heuristic, heuristic_mst):
            for vehicle_id in (1, 2):
                started = perf_counter()
                goal, expanded = search(problem, vehicle_id, start_time, estimate)
                elapsed_ms = (perf_counter() - started) * 1000
                print(f"\n{algorithm_name} | {estimate.__name__} | Veículo {vehicle_id}")
                feasible = False
                distance = duration = float("inf")
                if goal is None:
                    print("Sem solução: a fronteira esgotou-se sem entregar todos os artigos e regressar.")
                else:
                    depot = problem.vehicles[vehicle_id].center_location_id
                    route = reconstruct_route(goal, depot)
                    feasible, reason, _ = problem.route_feasibility_checker(
                        route, vehicle_id, start_time
                    )
                    if not feasible:
                        raise RuntimeError(f"A rota encontrada falhou a validação: {reason}")
                    metrics = problem.cost_function(route, vehicle_id, start_time)
                    distance = metrics["total_distance_km"]
                    duration = metrics["total_time_min"]
                    print(f"Rota: {route}")
                    print(f"Viável: {feasible} | {reason}")
                results.append({
                    "Algoritmo": algorithm_name,
                    "Heurística": estimate.__name__,
                    "Veículo": vehicle_id,
                    "Distância (km)": distance,
                    "Duração (min)": duration,
                    "Nós expandidos": expanded,
                    "Pesquisa (ms)": elapsed_ms,
                    "Viável": feasible,
                })
    print("\nComparação — artigos 7 e 10, partida em 19/10/2026 às 07:30")
    print(pd.DataFrame(results).to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print("\nTempos medem apenas a pesquisa, sem validação ou apresentação.")
    print("Uma execução por combinação não permite concluir qual algoritmo é mais rápido.")
    print("\nGreedy não garante a rota ótima.")


if __name__ == "__main__":
    main()
