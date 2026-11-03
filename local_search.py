"""Pesquisa local (Hill-Climbing) sobre rotas de recolha e entrega.

Uma solução é uma rota completa [("start", depósito), ..., ("regresso", depósito)].
A solução inicial vem do Greedy (informed.py). A vizinhança é gerada por
movimentos "relocate" e "swap" sobre os passos intermédios; cada vizinho é
validado por route_feasibility_checker() e avaliado por cost_function().
"""

import random
from time import perf_counter

import pandas as pd

from model import Problem


def evaluate(problem: Problem, route: list, vehicle_id: int, start_time: pd.Timestamp) -> tuple:
    """Custo de uma rota: (distância km, duração min). Rota inviável -> (inf, inf)."""
    feasible, _, _ = problem.route_feasibility_checker(route, vehicle_id, start_time)
    if not feasible:
        return (float("inf"), float("inf"))
    metrics = problem.cost_function(route, vehicle_id, start_time)
    return (metrics["total_distance_km"], metrics["total_time_min"])


def neighbours(route: list):
    """Gera vizinhos por relocate (mover um passo) e swap (trocar dois passos).

    Os passos de partida e de regresso mantêm-se fixos.
    """
    head, inner, tail = route[:1], route[1:-1], route[-1:]
    n = len(inner)
    seen = {tuple(inner)}
    for i in range(n):  # relocate: retira o passo i e insere-o na posição j
        for j in range(n):
            if i == j:
                continue
            moved = inner[:i] + inner[i + 1:]
            moved.insert(j, inner[i])
            key = tuple(moved)
            if key not in seen:
                seen.add(key)
                yield ("relocate", i, j), head + moved + tail
    for i in range(n):  # swap: troca os passos i e j
        for j in range(i + 1, n):
            swapped = inner[:]
            swapped[i], swapped[j] = swapped[j], swapped[i]
            key = tuple(swapped)
            if key not in seen:
                seen.add(key)
                yield ("swap", i, j), head + swapped + tail


def hill_climbing(problem: Problem, initial_route: list, vehicle_id: int,
                  start_time: pd.Timestamp, max_iterations: int = 1000) -> dict:
    """Hill-Climbing de melhor vizinho (steepest ascent).

    Em cada iteração avalia toda a vizinhança e move-se para o melhor vizinho
    se este for estritamente melhor (distância; desempate pela duração).
    Pára no primeiro ótimo local. Devolve rota, custo e histórico por iteração.
    """
    current = list(initial_route)
    current_cost = evaluate(problem, current, vehicle_id, start_time)
    if current_cost[0] == float("inf"):
        raise ValueError("A solução inicial tem de ser viável.")
    history = [current_cost[0]]
    evaluated = 0
    started = perf_counter()

    for _ in range(max_iterations):
        best_route, best_cost = None, current_cost
        for _, candidate in neighbours(current):
            evaluated += 1
            cost = evaluate(problem, candidate, vehicle_id, start_time)
            if cost < best_cost:
                best_route, best_cost = candidate, cost
        if best_route is None:  # nenhum vizinho melhora: ótimo local
            break
        current, current_cost = best_route, best_cost
        history.append(current_cost[0])

    return {
        "route": current,
        "distance_km": current_cost[0],
        "duration_min": current_cost[1],
        "iterations": len(history) - 1,
        "evaluated": evaluated,
        "history": history,
        "time_ms": (perf_counter() - started) * 1000,
    }


def random_feasible_route(problem: Problem, items: list, vehicle_id: int,
                          start_time: pd.Timestamp, rng: random.Random,
                          attempts: int = 5000) -> list | None:
    """Gera uma rota viável aleatória (recolha antes de entrega) para reinícios."""
    depot = problem.vehicles[vehicle_id].center_location_id
    for _ in range(attempts):
        steps = [("recolha", i) for i in items] + [("entrega", i) for i in items]
        rng.shuffle(steps)
        route = [("start", depot)] + steps + [("regresso", depot)]
        if evaluate(problem, route, vehicle_id, start_time)[0] != float("inf"):
            return route
    return None


def random_restart_hill_climbing(problem: Problem, items: list, vehicle_id: int,
                                 start_time: pd.Timestamp, restarts: int = 10,
                                 seed: int = 42) -> dict:
    """Repete o Hill-Climbing a partir de rotas aleatórias viáveis; devolve a melhor."""
    rng = random.Random(seed)
    best = None
    started = perf_counter()
    for _ in range(restarts):
        start_route = random_feasible_route(problem, items, vehicle_id, start_time, rng)
        if start_route is None:
            continue
        result = hill_climbing(problem, start_route, vehicle_id, start_time)
        if best is None or (result["distance_km"], result["duration_min"]) < (
                best["distance_km"], best["duration_min"]):
            best = result
    if best is not None:
        best = {**best, "time_ms": (perf_counter() - started) * 1000, "restarts": restarts}
    return best


def main() -> None:
    from informed import greedy_best_first, heuristic, reconstruct_route

    start_time = pd.Timestamp("2026-10-19 07:30:00")
    items = [7, 10, 17, 22]
    problem = Problem(data_folder="data")
    problem.requests = [r for r in problem.requests if r.item_id in items]
    problem.requests_by_id = {r.item_id: r for r in problem.requests}

    for vehicle_id in (1, 2):
        depot = problem.vehicles[vehicle_id].center_location_id
        goal, _ = greedy_best_first(problem, vehicle_id, start_time, heuristic)
        initial = reconstruct_route(goal, depot)
        result = hill_climbing(problem, initial, vehicle_id, start_time)
        print(f"Veículo {vehicle_id}: Greedy {result['history'][0]:.2f} km -> "
              f"Hill-Climbing {result['distance_km']:.2f} km "
              f"({result['iterations']} iterações, {result['evaluated']} vizinhos)")
        print("  Rota:", result["route"])


if __name__ == "__main__":
    main()
