"""CSP de ordenação de recolhas e entregas para um veículo existente."""

import pandas as pd

from model import Problem


class CSPProblemModel:
    """Cada variável é uma posição da rota; cada valor é (ação, item_id).

    Os horários são calculados pelo Problem, sem discretização temporal.
    A partida e o regresso ao depósito são fixos, fora das variáveis.
    """

    def __init__(self, problem: Problem, item_ids, vehicle_id=1, start_time=None):
        self.problem = problem
        self.vehicle_id = vehicle_id
        self.vehicle = problem.vehicles[vehicle_id]
        item_ids = tuple(item_ids)
        if not item_ids or len(set(item_ids)) != len(item_ids):
            raise ValueError("Selecionar artigos distintos e pelo menos um artigo.")
        self.requests = tuple(problem.requests_by_id[item] for item in item_ids)
        self.start_time = pd.Timestamp(start_time) if start_time is not None else min(
            request.ready_time for request in self.requests
        )
        self.variables = tuple(range(1, 2 * len(self.requests) + 1))
        actions = tuple(
            (action, request.item_id)
            for request in self.requests
            for action in ("recolha", "entrega")
        )
        self.domains = {position: list(actions) for position in self.variables}

    def route(self, assignment):
        """Converte uma atribuição completa numa rota do validador existente."""
        depot = self.vehicle.center_location_id
        return [("start", depot)] + [assignment[p] for p in self.variables] + [
            ("regresso", depot)
        ]

    def validate_solution(self, assignment):
        """Exige cobertura exata dos artigos, além da viabilidade da rota."""
        if set(assignment) != set(self.variables):
            return False, "Atribuição incompleta.", {}
        expected = set(self.domains[self.variables[0]])
        if set(assignment.values()) != expected:
            return False, "Cada recolha e entrega deve ocorrer exatamente uma vez.", {}
        return self.problem.route_feasibility_checker(
            self.route(assignment), self.vehicle_id, self.start_time
        )

    def check_constraints(self, var, value, assignment):
        """Verifica unicidade, precedência e viabilidade do prefixo conhecido.

        Em atribuições com lacunas, verifica apenas o prefixo consecutivo e
        precedências decididas. Não rejeita uma ação por faltarem passos antes.
        """
        if var not in self.domains or value not in self.domains[var]:
            return False
        candidate = dict(assignment)
        candidate[var] = value
        if any(p not in self.domains or v not in self.domains[p]
               for p, v in candidate.items()):
            return False
        if len(set(candidate.values())) != len(candidate):
            return False
        positions = {action: position for position, action in candidate.items()}
        for request in self.requests:
            pickup = positions.get(("recolha", request.item_id))
            delivery = positions.get(("entrega", request.item_id))
            if pickup is not None and delivery is not None and pickup >= delivery:
                return False

        # O gerador central aplica tempos de viagem, espera, janelas e carga.
        state = self.problem.initial_state(self.vehicle_id, self.start_time)
        for position in self.variables:
            if position not in candidate:
                break
            action, item_id = candidate[position]
            successor = next((s for s in self.problem.actions(state, self.vehicle_id)
                              if s.route[-1][:2] == (action, item_id)), None)
            if successor is None:
                return False
            state = successor
        if len(candidate) == len(self.variables):
            return self.validate_solution(candidate)[0]
        return True
