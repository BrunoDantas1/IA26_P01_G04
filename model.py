"""
Módulo de Modelação do Problema de Otimização de Rotas de Distribuição Alimentar
Unidade Curricular: Inteligência Artificial - IPCA
Projeto 01 - Grupo 04 (IA26_P01_G04)
Elementos:
  - Gonçalo Correia (22840)
  - Bruno Dantas (27958)
  - Ricardo Ferreira (25426)
Repositório Oficial: https://github.com/BrunoDantas1/IA26_P01_G04.git
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class Request:
    """Representa um pedido/item de encomenda (uma linha de order_items).
    
    Contém os nós de recolha (no produtor) e de entrega (no cliente),
    o peso associado e as respetivas janelas temporais regulamentares.
    """
    item_id: int
    order_id: int
    product_id: int
    product_name: str
    weight_kg: float
    producer_id: int
    pickup_location_id: int       # location_id unificado em locations.csv
    delivery_location_id: int     # location_id unificado em locations.csv
    availability_start: pd.Timestamp
    availability_end: pd.Timestamp
    delivery_start: pd.Timestamp
    delivery_end: pd.Timestamp
    order_datetime: pd.Timestamp
    ready_time: pd.Timestamp       # max(order_datetime, availability_start)

    def __repr__(self) -> str:
        return (f"Request(Item {self.item_id}: "
                f"PickLoc {self.pickup_location_id} -> DelivLoc {self.delivery_location_id} | "
                f"{self.weight_kg:.2f}kg)")


@dataclass(frozen=True)
class Vehicle:
    """Representa um veículo da frota afeto a um centro de recolha base."""
    vehicle_id: int
    plate: str
    center_id: int
    center_location_id: int       # location_id do centro em locations.csv
    capacity_kg: float
    refrigerated: bool
    avg_speed_kmh: float

    def __repr__(self) -> str:
        return f"Vehicle({self.vehicle_id}, Cap: {self.capacity_kg:.1f}kg, CenterLoc: {self.center_location_id})"


@dataclass(frozen=True)
class RouteStep:
    """Representa uma ação individual num itinerário de rota."""
    action_type: str              # 'start', 'pickup', 'delivery', 'return'
    location_id: int
    item_id: Optional[int] = None
    arrival_time: Optional[pd.Timestamp] = None
    departure_time: Optional[pd.Timestamp] = None
    current_load_kg: float = 0.0
    distance_from_prev_km: float = 0.0
    travel_time_min: float = 0.0
    wait_time_min: float = 0.0

    def to_tuple(self) -> Tuple[str, Optional[int], int, str]:
        arr_str = str(self.arrival_time) if self.arrival_time else ""
        return (self.action_type, self.item_id, self.location_id, arr_str)


@dataclass
class State:
    """Representa o estado do sistema durante a procura de rotas para um veículo."""
    location_id: int
    current_time: pd.Timestamp
    current_load_kg: float = 0.0
    picked_items: frozenset[int] = frozenset()
    delivered_items: frozenset[int] = frozenset()
    route: Tuple[Tuple[str, int, int, str], ...] = ()
    accumulated_distance_km: float = 0.0
    accumulated_duration_min: float = 0.0

    @property
    def in_transit_items(self) -> frozenset[int]:
        """Artigos recolhidos que ainda aguardam entrega no veículo."""
        return self.picked_items - self.delivered_items


class Problem:
    """Motor central do problema: carrega os dados CSV, indexa matrizes,
    gera ações admissíveis, calcula custos e valida restrições de viabilidade.
    """

    def __init__(self, data_folder: str = "data", selected_date: Optional[str] = None):
        """Inicializa o problema a partir da pasta dos dados CSV.
        
        Args:
            data_folder: Caminho para a pasta contendo os ficheiros CSV.
            selected_date: Filtro opcional por data (ex: '2026-10-10'). Se None, carrega todos.
        """
        self.data_folder = Path(data_folder)
        # Se a pasta contiver uma subpasta 'data_tiny' com os ficheiros, adapta automaticamente
        if (self.data_folder / "data_tiny" / "producers.csv").exists():
            self.data_folder = self.data_folder / "data_tiny"

        self.selected_date = selected_date
        self.locations_df = pd.read_csv(self.data_folder / "locations.csv")
        self.distance_matrix_df = pd.read_csv(self.data_folder / "distance_matrix.csv")
        
        # Mapeamentos rápidos de distâncias e durações entre pares de location_id
        self.distance_km: Dict[Tuple[int, int], float] = {}
        self.duration_min: Dict[Tuple[int, int], float] = {}
        self._load_distance_matrix()

        # Carregar veículos e pedidos
        self.vehicles: Dict[int, Vehicle] = self._load_vehicles()
        self.requests: List[Request] = self._load_requests(selected_date=selected_date)
        self.requests_by_id: Dict[int, Request] = {r.item_id: r for r in self.requests}

    def _locate_unified_id(self, location_type: str, ref_id: int) -> int:
        """Converte (location_type, ref_id) para o respetivo location_id unificado."""
        subset = self.locations_df[(self.locations_df["location_type"] == location_type) & 
                                   (self.locations_df["ref_id"] == ref_id)]
        if subset.empty:
            raise KeyError(f"Localização não encontrada: type={location_type}, ref_id={ref_id}")
        return int(subset.iloc[0]["location_id"])

    def _load_distance_matrix(self) -> None:
        """Indexa a matriz de distâncias e durações."""
        for row in self.distance_matrix_df.itertuples(index=False):
            orig = int(row.origin_location_id)
            dest = int(row.destination_location_id)
            self.distance_km[(orig, dest)] = float(row.distance_km)
            self.duration_min[(orig, dest)] = float(row.duration_min)
            
        # Assegurar auto-distâncias nulas
        unique_locs = set(self.locations_df["location_id"].unique())
        for loc in unique_locs:
            self.distance_km[(loc, loc)] = 0.0
            self.duration_min[(loc, loc)] = 0.0

    def _load_vehicles(self) -> Dict[int, Vehicle]:
        """Carrega os veículos do ficheiro vehicles.csv."""
        df_vehicles = pd.read_csv(self.data_folder / "vehicles.csv")
        vehicles = {}
        for row in df_vehicles.itertuples(index=False):
            v_id = int(row.vehicle_id)
            center_loc_id = self._locate_unified_id("collection_center", int(row.center_id))
            vehicles[v_id] = Vehicle(
                vehicle_id=v_id,
                plate=str(row.plate),
                center_id=int(row.center_id),
                center_location_id=center_loc_id,
                capacity_kg=float(row.capacity_kg),
                refrigerated=bool(row.refrigerated),
                avg_speed_kmh=float(row.avg_speed_kmh)
            )
        return vehicles

    def _load_requests(self, selected_date: Optional[str] = None) -> List[Request]:
        """Carrega e cruza order_items, orders e products para instanciar Requests."""
        df_items = pd.read_csv(self.data_folder / "order_items.csv")
        df_orders = pd.read_csv(self.data_folder / "orders.csv")
        df_products = pd.read_csv(self.data_folder / "products.csv")

        merged = df_items.merge(df_orders, on="order_id").merge(df_products, on="product_id")
        
        requests = []
        for row in merged.itertuples(index=False):
            avail_start = pd.Timestamp(row.availability_start)
            avail_end = pd.Timestamp(row.availability_end)
            deliv_start = pd.Timestamp(row.delivery_start)
            deliv_end = pd.Timestamp(row.delivery_end)
            order_dt = pd.Timestamp(row.order_datetime)
            ready_time = max(order_dt, avail_start)

            # Filtro opcional por data de recolha/disponibilidade
            if selected_date is not None:
                if str(avail_start.date()) != selected_date and str(ready_time.date()) != selected_date:
                    continue

            pickup_loc = self._locate_unified_id("producer", int(row.producer_id))
            deliv_loc = self._locate_unified_id("delivery_location", int(row.delivery_location_id))
            weight = float(row.quantity) * float(row.unit_weight_kg)

            req = Request(
                item_id=int(row.order_item_id),
                order_id=int(row.order_id),
                product_id=int(row.product_id),
                product_name=str(row.name_y if "name_y" in row._fields else row.name),
                weight_kg=weight,
                producer_id=int(row.producer_id),
                pickup_location_id=pickup_loc,
                delivery_location_id=deliv_loc,
                availability_start=avail_start,
                availability_end=avail_end,
                delivery_start=deliv_start,
                delivery_end=deliv_end,
                order_datetime=order_dt,
                ready_time=ready_time
            )
            requests.append(req)

        # Ordenação consistente por id
        requests.sort(key=lambda r: r.item_id)
        return requests

    def get_travel_info(self, origin: int, destination: int) -> Tuple[float, float]:
        """Retorna (distância_km, tempo_minutos) entre duas localizações."""
        if origin == destination:
            return 0.0, 0.0
        dist = self.distance_km.get((origin, destination), float("inf"))
        dur = self.duration_min.get((origin, destination), float("inf"))
        return dist, dur

    def initial_state(self, vehicle_id: int, start_time: Optional[pd.Timestamp] = None) -> State:
        """Cria o estado inicial com o veículo no armazém e carga a zeros."""
        vehicle = self.vehicles[vehicle_id]
        if start_time is None:
            # Tempo inicial baseado no primeiro pedido disponível
            start_time = min((r.ready_time for r in self.requests), default=pd.Timestamp("2026-10-10 08:00:00"))
        
        return State(
            location_id=vehicle.center_location_id,
            current_time=pd.Timestamp(start_time),
            current_load_kg=0.0,
            picked_items=frozenset(),
            delivered_items=frozenset(),
            route=(),
            accumulated_distance_km=0.0,
            accumulated_duration_min=0.0
        )

    def actions(self, state: State, vehicle_id: int) -> List[State]:
        """Gera todos os estados sucessores viáveis respeitando janelas e capacidade.
        Se chegar antes do início da janela de abertura, aguarda até abrir.
        """
        vehicle = self.vehicles[vehicle_id]
        successors: List[State] = []

        for req in self.requests:
            # 1. AÇÃO DE RECOLHA
            if req.item_id not in state.picked_items:
                # Verificação de capacidade
                if state.current_load_kg + req.weight_kg > vehicle.capacity_kg + 1e-9:
                    continue
                
                dist, dur = self.get_travel_info(state.location_id, req.pickup_location_id)
                if dist == float("inf"):
                    continue
                    
                arrival_time = state.current_time + pd.Timedelta(minutes=dur)
                service_start = max(arrival_time, req.ready_time)
                wait_min = max(0.0, (service_start - arrival_time).total_seconds() / 60.0)

                # Restrição temporal: não pode chegar após fecho da janela de recolha
                if arrival_time > req.availability_end:
                    continue

                step_descr = ("recolha", req.item_id, req.pickup_location_id, str(service_start))
                next_state = State(
                    location_id=req.pickup_location_id,
                    current_time=service_start,
                    current_load_kg=state.current_load_kg + req.weight_kg,
                    picked_items=state.picked_items | {req.item_id},
                    delivered_items=state.delivered_items,
                    route=state.route + (step_descr,),
                    accumulated_distance_km=state.accumulated_distance_km + dist,
                    accumulated_duration_min=state.accumulated_duration_min + dur + wait_min
                )
                successors.append(next_state)

            # 2. AÇÃO DE ENTREGA (Precedência obrigatória: já deve ter sido recolhido)
            elif req.item_id not in state.delivered_items:
                dist, dur = self.get_travel_info(state.location_id, req.delivery_location_id)
                if dist == float("inf"):
                    continue
                    
                arrival_time = state.current_time + pd.Timedelta(minutes=dur)
                service_start = max(arrival_time, req.delivery_start)
                wait_min = max(0.0, (service_start - arrival_time).total_seconds() / 60.0)

                # Restrição temporal: não pode chegar após o limite de entrega
                if arrival_time > req.delivery_end:
                    continue

                step_descr = ("entrega", req.item_id, req.delivery_location_id, str(service_start))
                next_state = State(
                    location_id=req.delivery_location_id,
                    current_time=service_start,
                    current_load_kg=max(0.0, state.current_load_kg - req.weight_kg),
                    picked_items=state.picked_items,
                    delivered_items=state.delivered_items | {req.item_id},
                    route=state.route + (step_descr,),
                    accumulated_distance_km=state.accumulated_distance_km + dist,
                    accumulated_duration_min=state.accumulated_duration_min + dur + wait_min
                )
                successors.append(next_state)

        return successors

    def return_to_base(self, state: State, vehicle_id: int) -> State:
        """Conclui a rota regressando ao centro de recolha base."""
        vehicle = self.vehicles[vehicle_id]
        dist, dur = self.get_travel_info(state.location_id, vehicle.center_location_id)
        arrival_time = state.current_time + pd.Timedelta(minutes=dur)
        step_descr = ("regresso", 0, vehicle.center_location_id, str(arrival_time))
        
        return State(
            location_id=vehicle.center_location_id,
            current_time=arrival_time,
            current_load_kg=state.current_load_kg,
            picked_items=state.picked_items,
            delivered_items=state.delivered_items,
            route=state.route + (step_descr,),
            accumulated_distance_km=state.accumulated_distance_km + dist,
            accumulated_duration_min=state.accumulated_duration_min + dur
        )

    def is_goal(self, state: State, target_items: Optional[Set[int]] = None) -> bool:
        """Verifica se todos os pedidos (ou conjunto alvo) foram entregues."""
        target = target_items if target_items is not None else set(self.requests_by_id.keys())
        return target.issubset(state.delivered_items)

    def cost_function(
        self,
        route_steps: List[Tuple[str, int]],
        vehicle_id: int = 1,
        start_time: Optional[pd.Timestamp] = None
    ) -> Dict[str, Any]:
        """Calcula o custo detalhado de uma rota:
        distância total (km), tempo de viagem, tempo de espera e tempo total (min).
        
        Args:
            route_steps: Lista de pares (action_type, target_id):
                         ex: [('start', center_loc), ('pickup', item_id), ('delivery', item_id), ('return', center_loc)]
            vehicle_id: Veículo que executa a rota.
            start_time: Hora de início (se None, usa a do primeiro pedido da rota).
        """
        vehicle = self.vehicles[vehicle_id]
        if not route_steps:
            return {"feasible": False, "total_distance_km": float("inf"), "total_time_min": float("inf")}

        if start_time is None:
            # Determina o primeiro pedido para estabelecer o momento de partida
            first_items = [tid for act, tid in route_steps if act in ("pickup", "delivery") and tid in self.requests_by_id]
            if first_items:
                start_time = min(self.requests_by_id[first_items[0]].ready_time,
                                 self.requests_by_id[first_items[0]].availability_start)
            else:
                start_time = pd.Timestamp("2026-10-10 08:00:00")

        current_loc = vehicle.center_location_id
        current_time = pd.Timestamp(start_time)
        current_load = 0.0
        total_dist = 0.0
        total_travel_min = 0.0
        total_wait_min = 0.0
        timeline = []

        for step_idx, (action, target_id) in enumerate(route_steps):
            if action in ("start", "inicio", "partida"):
                current_loc = target_id if target_id else vehicle.center_location_id
                timeline.append({
                    "step": step_idx,
                    "action": "start",
                    "location_id": current_loc,
                    "arrival": current_time,
                    "departure": current_time,
                    "load_kg": current_load
                })
                continue

            if action in ("pickup", "recolha"):
                req = self.requests_by_id.get(target_id)
                if not req:
                    return {"feasible": False, "error": f"Item {target_id} não encontrado."}
                dest_loc = req.pickup_location_id
                window_start, window_end = req.ready_time, req.availability_end
                delta_load = req.weight_kg

            elif action in ("delivery", "entrega"):
                req = self.requests_by_id.get(target_id)
                if not req:
                    return {"feasible": False, "error": f"Item {target_id} não encontrado."}
                dest_loc = req.delivery_location_id
                window_start, window_end = req.delivery_start, req.delivery_end
                delta_load = -req.weight_kg

            elif action in ("return", "regresso"):
                dest_loc = target_id if (target_id and target_id > 0) else vehicle.center_location_id
                window_start, window_end = None, None
                delta_load = 0.0
            else:
                return {"feasible": False, "error": f"Ação desconhecida: {action}"}

            dist, dur = self.get_travel_info(current_loc, dest_loc)
            if dist == float("inf"):
                return {"feasible": False, "error": f"Sem ligação viável entre {current_loc} e {dest_loc}"}

            arrival = current_time + pd.Timedelta(minutes=dur)
            wait_min = 0.0
            departure = arrival

            if window_start is not None:
                if arrival < window_start:
                    wait_min = (window_start - arrival).total_seconds() / 60.0
                    departure = window_start

            current_load += delta_load
            total_dist += dist
            total_travel_min += dur
            total_wait_min += wait_min
            current_time = departure
            current_loc = dest_loc

            timeline.append({
                "step": step_idx,
                "action": action,
                "item_id": target_id if action in ("pickup", "delivery") else 0,
                "location_id": dest_loc,
                "distance_km": dist,
                "travel_time_min": dur,
                "wait_time_min": wait_min,
                "arrival": arrival,
                "departure": departure,
                "load_kg": current_load
            })

        total_time_min = total_travel_min + total_wait_min
        return {
            "feasible": True,
            "total_distance_km": round(total_dist, 2),
            "total_travel_time_min": round(total_travel_min, 2),
            "total_wait_time_min": round(total_wait_min, 2),
            "total_time_min": round(total_time_min, 2),
            "end_time": current_time,
            "timeline": timeline
        }

    def route_feasibility_checker(
        self,
        route_steps: List[Tuple[str, int]],
        vehicle_id: int = 1,
        start_time: Optional[pd.Timestamp] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Validador rigoroso de viabilidade de uma rota.
        
        Verifica detalhadamente:
          1. Partida e regresso ao CollectionCenter do veículo;
          2. Precedência obrigatória (recolha antes de entrega);
          3. Respeito rigoroso pela capacidade máxima do veículo em todos os passos;
          4. Janelas temporais de recolha [ready_time, availability_end] (inviável se chegar após o fim);
          5. Janelas temporais de entrega [delivery_start, delivery_end] (inviável se chegar após o fim);
          6. Existência de ligação na matriz de distâncias.
          
        Returns:
            Tuple[is_feasible, reason_message, evaluation_details]
        """
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            return False, f"Veículo {vehicle_id} não registado.", {}

        if not route_steps:
            return False, "Rota vazia.", {}

        # 1. Validação de partida no armazém
        first_act, first_loc = route_steps[0]
        if first_act in ("start", "inicio", "partida") and first_loc != vehicle.center_location_id:
            return False, (f"Violação de depósito: A rota inicia no local {first_loc}, "
                           f"mas o depósito do veículo {vehicle_id} é o local {vehicle.center_location_id}."), {}

        # 2. Validação de regresso ao armazém
        last_act, last_loc = route_steps[-1]
        if last_act in ("return", "regresso") and last_loc != 0 and last_loc != vehicle.center_location_id:
            return False, (f"Violação de depósito: O regresso foi feito ao local {last_loc}, "
                           f"mas o depósito do veículo {vehicle_id} é o local {vehicle.center_location_id}."), {}

        if start_time is None:
            first_items = [tid for act, tid in route_steps if act in ("pickup", "delivery", "recolha", "entrega") and tid in self.requests_by_id]
            if first_items:
                start_time = self.requests_by_id[first_items[0]].ready_time
            else:
                start_time = pd.Timestamp("2026-10-10 08:00:00")

        current_loc = vehicle.center_location_id
        current_time = pd.Timestamp(start_time)
        current_load = 0.0
        picked = set()
        delivered = set()
        total_dist = 0.0
        total_travel_min = 0.0
        total_wait_min = 0.0
        log_records = []

        for idx, (action, target_id) in enumerate(route_steps):
            if action in ("start", "inicio", "partida"):
                current_loc = target_id if target_id else vehicle.center_location_id
                continue

            if action in ("pickup", "recolha"):
                req = self.requests_by_id.get(target_id)
                if not req:
                    return False, f"Item {target_id} inexistente nos pedidos carregados.", {}
                
                # Verificação de precedência: não recolher duas vezes o mesmo item
                if target_id in picked:
                    return False, f"Violação de integridade: Item {target_id} recolhido repetidamente.", {}

                # Verificação de capacidade
                if current_load + req.weight_kg > vehicle.capacity_kg + 1e-9:
                    excesso = (current_load + req.weight_kg) - vehicle.capacity_kg
                    return False, (f"Violação de Capacidade no passo {idx}: Carga total atingiria "
                                   f"{(current_load + req.weight_kg):.2f} kg, excedendo o limite de "
                                   f"{vehicle.capacity_kg:.2f} kg do veículo em {excesso:.2f} kg."), {}

                dest_loc = req.pickup_location_id
                dist, dur = self.get_travel_info(current_loc, dest_loc)
                if dist == float("inf"):
                    return False, f"Desconexão de rede: Impossível viajar de {current_loc} para {dest_loc}.", {}

                arrival = current_time + pd.Timedelta(minutes=dur)
                
                # Verificação de janela temporal de recolha (fim de disponibilidade)
                if arrival > req.availability_end:
                    atraso = (arrival - req.availability_end).total_seconds() / 60.0
                    return False, (f"Violação de Janela Temporal de Recolha no passo {idx} (Item {target_id}): "
                                   f"Chegada às {arrival}, após o fecho da janela ({req.availability_end}) "
                                   f"com atraso de {atraso:.1f} minutos."), {}

                # Espera se chegar antes da abertura/prontidão
                wait_min = max(0.0, (req.ready_time - arrival).total_seconds() / 60.0) if arrival < req.ready_time else 0.0
                departure = max(arrival, req.ready_time)

                current_load += req.weight_kg
                picked.add(target_id)

            elif action in ("delivery", "entrega"):
                req = self.requests_by_id.get(target_id)
                if not req:
                    return False, f"Item {target_id} inexistente nos pedidos carregados.", {}

                # Verificação de precedência OBRIGATÓRIA: deve ter sido previamente recolhido
                if target_id not in picked:
                    return False, (f"Violação de Precedência no passo {idx}: Tentativa de entrega do Item {target_id} "
                                   f"sem ter sido previamente recolhido!"), {}

                if target_id in delivered:
                    return False, f"Violação de integridade: Item {target_id} entregue repetidamente.", {}

                dest_loc = req.delivery_location_id
                dist, dur = self.get_travel_info(current_loc, dest_loc)
                if dist == float("inf"):
                    return False, f"Desconexão de rede: Impossível viajar de {current_loc} para {dest_loc}.", {}

                arrival = current_time + pd.Timedelta(minutes=dur)

                # Verificação de janela temporal de entrega
                if arrival > req.delivery_end:
                    atraso = (arrival - req.delivery_end).total_seconds() / 60.0
                    return False, (f"Violação de Janela Temporal de Entrega no passo {idx} (Item {target_id}): "
                                   f"Chegada às {arrival}, após o fecho da janela ({req.delivery_end}) "
                                   f"com atraso de {atraso:.1f} minutos."), {}

                # Espera se chegar antes do início da janela de entrega
                wait_min = max(0.0, (req.delivery_start - arrival).total_seconds() / 60.0) if arrival < req.delivery_start else 0.0
                departure = max(arrival, req.delivery_start)

                current_load = max(0.0, current_load - req.weight_kg)
                delivered.add(target_id)

            elif action in ("return", "regresso"):
                dest_loc = target_id if (target_id and target_id > 0) else vehicle.center_location_id
                dist, dur = self.get_travel_info(current_loc, dest_loc)
                arrival = current_time + pd.Timedelta(minutes=dur)
                wait_min = 0.0
                departure = arrival
            else:
                return False, f"Ação desconhecida: {action}", {}

            total_dist += dist
            total_travel_min += dur
            total_wait_min += wait_min
            current_time = departure
            current_loc = dest_loc

            log_records.append({
                "step": idx,
                "action": action,
                "item_id": target_id,
                "location_id": dest_loc,
                "arrival": arrival,
                "departure": departure,
                "wait_min": wait_min,
                "load_kg": current_load
            })

        # Verificação se todos os itens recolhidos foram entregues antes do regresso
        if picked != delivered:
            undelivered = picked - delivered
            return False, f"Violação de Entrega: Os artigos {undelivered} foram recolhidos mas não foram entregues.", {}

        details = {
            "total_distance_km": round(total_dist, 2),
            "total_travel_time_min": round(total_travel_min, 2),
            "total_wait_time_min": round(total_wait_min, 2),
            "total_time_min": round(total_travel_min + total_wait_min, 2),
            "delivered_items_count": len(delivered),
            "log": log_records
        }
        return True, "Rota perfeitamente viável! Cumpre todas as restrições.", details


if __name__ == "__main__":
    print("=== TESTE DO MÓDULO MODEL.PY ===")
    p = Problem(data_folder="data")
    print(f"Pedidos carregados: {len(p.requests)}")
    print(f"Veículos carregados: {len(p.vehicles)}")
    for vid, v in p.vehicles.items():
        print(f"  {v}")
    
    # Teste de viabilidade com rota hand-written
    req_teste = p.requests[0]
    print(f"\nItem de teste selecionado: {req_teste}")
    
    rota_valida = [
        ("start", 6),
        ("pickup", req_teste.item_id),
        ("delivery", req_teste.item_id),
        ("return", 6)
    ]
    viavel, msg, details = p.route_feasibility_checker(rota_valida, vehicle_id=1)
    print(f"Rota Válida: {viavel} -> {msg}")
    if viavel:
        print(f"  Distância: {details['total_distance_km']} km | Duração: {details['total_time_min']} min")
