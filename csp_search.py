from csp_model import CSPProblemModel

class CSPSearchEngine(CSPProblemModel):
    def __init__(self, orders_path, distance_matrix_path):
        super().__init__(orders_path, distance_matrix_path)
        self.backtracks = 0

    def forward_checking(self, var, value, current_domains, assignment):
        """Aplica Forward Checking para podar domínios de variáveis futuras."""
        updated_domains = {v: list(d) for v, d in current_domains.items()}
        
        for other_var in updated_domains:
            if other_var in assignment or other_var == var:
                continue
                
            # Remove valores do domínio que violam restrições de tempo/espaço
            updated_domains[other_var] = [
                v for v in updated_domains[other_var]
                if abs(v - value) >= 15  # Folga mínima
            ]
            
            if not updated_domains[other_var]:
                return None  # Domínio vazio detetado (falha antecipada)
                
        return updated_domains

    def backtracking(self, assignment=None, domains=None):
        """Implementa o Backtracking com Forward Checking."""
        if assignment is None:
            assignment = {}
        if domains is None:
            domains = self.domains

        # Caso base: todas as variáveis atribuídas
        if len(assignment) == len(self.variables):
            return assignment

        # Selecionar próxima variável não atribuída
        unassigned = [v for v in self.variables if v not in assignment]
        var = min(unassigned, key=lambda v: len(domains[v]))

        for value in domains[var]:
            if self.check_constraints(var, value, assignment):
                assignment[var] = value
                
                # Forward Checking
                reduced_domains = self.forward_checking(var, value, domains, assignment)
                if reduced_domains is not None:
                    result = self.backtracking(assignment, reduced_domains)
                    if result is not None:
                        return result
                
                # Retrocesso (Backtrack)
                del assignment[var]
                self.backtracks += 1

        return None