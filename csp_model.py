import pandas as pd

class CSPProblemModel:
    def __init__(self, orders_path, distance_matrix_path):
        self.orders = pd.read_csv(orders_path)
        self.distance_matrix = pd.read_csv(distance_matrix_path)
        self.variables = []
        self.domains = {}
        self.setup_variables_and_domains()

    def setup_variables_and_domains(self):
        """Define as variáveis e os respetivos domínios baseados nas janelas temporais."""
        for index, row in self.orders.iterrows():
            var_name = f"Order_{row.get('order_id', index)}"
            self.variables.append(var_name)
            
            # Domínio: instantes de tempo válidos entre o início e o fim da entrega
            start = int(row.get('delivery_start', 480)) # ex: 08:00 (480 min)
            end = int(row.get('delivery_end', 1000))     # ex: 16:40 (1000 min)
            self.domains[var_name] = list(range(start, end + 1, 10))

    def check_constraints(self, var, value, assignment):
        """Verifica se a atribuição respeita as restrições do problema."""
        if value not in self.domains[var]:
            return False
        
        # Restrições adicionais entre tarefas atribuídas (ex: distância/tempo)
        for other_var, other_val in assignment.items():
            if other_var != var:
                # Exemplo de restrição temporal/espaço entre paragens
                if abs(value - other_val) < 10:
                    pass # Aplicar lógica de restrição se necessário
        return True