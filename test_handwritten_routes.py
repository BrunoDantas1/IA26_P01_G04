from model import Problem, Request
import pandas as pd

p = Problem(data_folder="data")
# Filtra apenas itens válidos para o teste
valid_requests = [r for r in p.requests if r.ready_time <= r.availability_end]
p.requests = valid_requests
p.requests_by_id = {r.item_id: r for r in p.requests}

print(f"Pedidos válidos: {len(p.requests)}")

# Teste 1: Rota Válida com Item 5
start_t = pd.Timestamp("2026-10-10 12:00:00")
rota_valida_1 = [
    ("start", 6),
    ("pickup", 5),
    ("delivery", 5),
    ("return", 6)
]
viavel1, msg1, det1 = p.route_feasibility_checker(rota_valida_1, vehicle_id=1, start_time=start_t)
print("\n--- Teste Rota Válida 1 (Item 5) ---")
print(f"Viável: {viavel1} | {msg1}")
if viavel1:
    print(f"Distância: {det1['total_distance_km']} km | Tempo: {det1['total_time_min']} min (Viagem: {det1['total_travel_time_min']} min, Espera: {det1['total_wait_time_min']} min)")
    for step in det1['log']:
        print(f"  {step['action']} (Item {step['item_id']}) @ Loc {step['location_id']}: Chegada {step['arrival']} -> Saída {step['departure']} | Espera: {step['wait_min']}m | Carga: {step['load_kg']}kg")

# Teste 2: Rota Válida com 2 Itens no mesmo dia (2026-10-19: Itens 7 e 10)
start_t2 = pd.Timestamp("2026-10-19 07:30:00")
rota_valida_2 = [
    ("start", 6),
    ("pickup", 10),
    ("delivery", 10),
    ("pickup", 7),
    ("delivery", 7),
    ("return", 6)
]
viavel2, msg2, det2 = p.route_feasibility_checker(rota_valida_2, vehicle_id=1, start_time=start_t2)
print("\n--- Teste Rota Válida 2 (Itens 10 e 7) ---")
print(f"Viável: {viavel2} | {msg2}")
if viavel2:
    print(f"Distância: {det2['total_distance_km']} km | Tempo: {det2['total_time_min']} min")

# Teste 3: Rota Inválida por Precedência (entrega antes de recolha)
rota_invalida_prec = [
    ("start", 6),
    ("delivery", 5),
    ("pickup", 5),
    ("return", 6)
]
viavel3, msg3, _ = p.route_feasibility_checker(rota_invalida_prec, vehicle_id=1, start_time=start_t)
print("\n--- Teste Rota Inválida 1 (Precedência) ---")
print(f"Viável: {viavel3} | {msg3}")

# Teste 4: Rota Inválida por Janela Temporal (chega atrasado)
start_t_late = pd.Timestamp("2026-10-10 16:00:00")
rota_invalida_tempo = [
    ("start", 6),
    ("pickup", 5),
    ("delivery", 5),
    ("return", 6)
]
viavel4, msg4, _ = p.route_feasibility_checker(rota_invalida_tempo, vehicle_id=1, start_time=start_t_late)
print("\n--- Teste Rota Inválida 2 (Janela Temporal) ---")
print(f"Viável: {viavel4} | {msg4}")

# Teste 5: Rota Inválida por Excesso de Capacidade
class FakeReq:
    def __init__(self, base_req, fake_weight):
        for k, v in base_req.__dict__.items():
            setattr(self, k, v)
        self.weight_kg = fake_weight

p.requests_by_id[999] = FakeReq(p.requests_by_id[5], 2000.0)
rota_invalida_cap = [
    ("start", 6),
    ("pickup", 999),
    ("delivery", 999),
    ("return", 6)
]
viavel5, msg5, _ = p.route_feasibility_checker(rota_invalida_cap, vehicle_id=1, start_time=start_t)
print("\n--- Teste Rota Inválida 3 (Capacidade Excedida) ---")
print(f"Viável: {viavel5} | {msg5}")
