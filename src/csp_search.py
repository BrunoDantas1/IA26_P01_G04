"""Backtracking simples e Backtracking com Forward Checking para o CSP."""

from time import perf_counter

from csp_model import CSPProblemModel


class CSPSearchEngine:
    def __init__(self, model: CSPProblemModel):
        self.model = model

    def forward_checking(self, current_domains, assignment):
        """Filtra cada domínio não atribuído contra a atribuição atual.

        Cada ramo recebe listas novas. Um domínio vazio provoca falha imediata.
        Não calcula consistência de arco entre duas variáveis não atribuídas.
        """
        reduced = {var: list(values) for var, values in current_domains.items()}
        for var in self.model.variables:
            if var in assignment:
                continue
            reduced[var] = [
                value for value in reduced[var]
                if self.model.check_constraints(var, value, assignment)
            ]
            self.pruned_values += len(current_domains[var]) - len(reduced[var])
            if not reduced[var]:
                return None
        return reduced

    def backtracking(self, use_forward_checking=False):
        """Procura a primeira solução viável; não minimiza a distância.

        Retrocesso = remoção de uma atribuição consistente cujo ramo falhou.
        Valores rejeitados antes de atribuir contam como tentativas, não recuos.
        A ordem das posições e dos valores é fixa e reproduzível.
        """
        self.backtracks = 0
        self.attempts = 0
        self.nodes = 0
        self.pruned_values = 0
        started = perf_counter()

        def search(assignment, domains):
            self.nodes += 1
            if len(assignment) == len(self.model.variables):
                return dict(assignment) if self.model.validate_solution(assignment)[0] else None
            var = next(v for v in self.model.variables if v not in assignment)
            for value in domains[var]:
                self.attempts += 1
                if not self.model.check_constraints(var, value, assignment):
                    continue
                assignment[var] = value
                reduced = (self.forward_checking(domains, assignment)
                           if use_forward_checking else domains)
                result = search(assignment, reduced) if reduced is not None else None
                if result is not None:
                    return result
                del assignment[var]
                self.backtracks += 1
            return None

        assignment = search({}, self.model.domains)
        valid, message, details = (self.model.validate_solution(assignment)
                                   if assignment is not None else
                                   (False, "Sem solução para o cenário selecionado.", {}))
        return {
            "algorithm": "Forward Checking" if use_forward_checking else "Backtracking",
            "assignment": assignment,
            "route": self.model.route(assignment) if valid else None,
            "feasible": valid,
            "message": message,
            "details": details,
            "backtracks": self.backtracks,
            "attempts": self.attempts,
            "nodes": self.nodes,
            "pruned_values": self.pruned_values,
            "elapsed_seconds": perf_counter() - started,
        }
