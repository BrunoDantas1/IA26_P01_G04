"""Pesquisa Greedy Best-First para o cenário inicial da Parte A."""

import heapq
from itertools import count

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


def greedy_best_first(
    problem: Problem, vehicle_id: int, start_time: pd.Timestamp
) -> tuple[State | None, int]:
    """Ordena a fronteira apenas por h(n); conta chamadas a actions().

    O contador desempata prioridades sem comparar objetos State. Não é preciso
    um conjunto de visitados neste espaço finito: cada artigo só é recolhido e
    entregue uma vez, e o regresso termina a rota.
    """
    initial = problem.initial_state(vehicle_id, start_time)
    tie_breaker = count()
    frontier = [(heuristic(problem, initial, vehicle_id), next(tie_breaker), initial)]
    expanded = 0

    while frontier:
        _, _, state = heapq.heappop(frontier)
        if problem.is_goal(state, vehicle_id=vehicle_id):
            return state, expanded
        expanded += 1
        for successor in problem.actions(state, vehicle_id):
            heapq.heappush(
                frontier,
                (heuristic(problem, successor, vehicle_id), next(tie_breaker), successor),
            )
    return None, expanded


def reconstruct_route(state: State, depot: int) -> list[tuple[str, int]]:
    """Converte o percurso acumulado para os pares aceites pelo validador."""
    route = [("start", depot)]
    for action, item_id, location_id, _ in state.route:
        route.append((action, location_id if action == "regresso" else item_id))
    return route


def main() -> None:
    start_time = pd.Timestamp("2026-10-19 07:30:00")
    problem = Problem(data_folder="data")
    target_items = {7, 10}
    problem.requests = [r for r in problem.requests if r.item_id in target_items]
    problem.requests_by_id = {r.item_id: r for r in problem.requests}

    for vehicle_id in (1, 2):
        goal, expanded = greedy_best_first(problem, vehicle_id, start_time)
        print(f"\nVeículo {vehicle_id} | Nós expandidos: {expanded}")
        if goal is None:
            print("Sem solução: a fronteira esgotou-se sem entregar todos os artigos e regressar.")
            continue
        depot = problem.vehicles[vehicle_id].center_location_id
        route = reconstruct_route(goal, depot)
        feasible, reason, _ = problem.route_feasibility_checker(
            route, vehicle_id, start_time
        )
        if not feasible:
            raise RuntimeError(f"A rota encontrada falhou a validação: {reason}")
        metrics = problem.cost_function(route, vehicle_id, start_time)
        print(f"Rota: {route}")
        print(f"Distância total: {metrics['total_distance_km']:.2f} km")
        print(f"Duração total: {metrics['total_time_min']:.2f} min")
        print(f"Viável: {feasible} | {reason}")
    print("\nGreedy não garante a rota ótima.")


if __name__ == "__main__":
    main()
