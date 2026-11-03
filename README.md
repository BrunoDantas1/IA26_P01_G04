# Projeto 01 — Agente Inteligente de Otimização de Rotas de Distribuição Alimentar Local
## Unidade Curricular de Inteligência Artificial — IPCA (2026/2027)
### Modelação, Análise Exploratória, Pesquisa Informada e Pesquisa Local

**Repositório Oficial:** [https://github.com/BrunoDantas1/IA26_P01_G04.git](https://github.com/BrunoDantas1/IA26_P01_G04.git)

---

### 1. Identificação do Grupo (Grupo 04 — `IA26_P01_G04`)
* **Gonçalo Correia** — Nº 22840
* **Bruno Dantas** — Nº 27958
* **Ricardo Ferreira** — Nº 25426

---

### 2. Contexto do Problema e Objetivos
O objetivo deste projeto é o desenvolvimento de um agente inteligente de planeamento de rotas (*pickup-and-delivery* com restrições de janelas temporais e capacidade de carga) para distribuição alimentar local no distrito de Braga e Póvoa de Varzim, ligando três atores principais:
1. **Produtores Locais (*Producers*)**: Locais de recolha dos produtos com janelas horárias regulamentares $[availability\_start, availability\_end]$.
2. **Centros de Recolha / Armazéns (*CollectionCenters*)**: Plataformas logísticas de agregação e base operacional obrigatória da frota de veículos (*Vehicles*).
3. **Locais de Entrega (*DeliveryLocations / Customers*)**: Destinos finais onde as encomendas devem ser entregues dentro da janela $[delivery\_start, delivery\_end]$.
4. **Matriz de Distâncias e Tempos (*DistanceMatrix*)**: Distâncias ortodrómicas com fator rodoviário de 1.3 e durações com base numa velocidade de referência de 45 km/h entre todas as paragens unificadas (`locations.csv`).

O projeto está organizado nas seguintes componentes:
* **Análise Exploratória de Dados (EDA)** sobre o dataset `data`, com validação de integridade referencial das chaves primárias e estrangeiras.
* **Módulo de Modelação (`model.py`)** com classes tipadas (`Request`, `Vehicle`, `State`, `Problem`), função de custo e validador estrito de viabilidade de rotas.
* **Testes com Rotas Escritas à Mão**, que comprovam a deteção de rotas válidas e de violações de precedência, janelas temporais e capacidade máxima.
* **Pesquisa informada (`informed.py`)**: Greedy Best-First e A* com duas heurísticas (maior cadeia individual e árvore de expansão mínima), comparados em 8 combinações (2 algoritmos × 2 heurísticas × 2 veículos).
* **Pesquisa local (`local_search.py`)**: Hill-Climbing de melhor vizinho (movimentos *relocate* e *swap*) a partir da solução do Greedy, com curva de custo por iteração e reinícios aleatórios.

**Estado atual:** a formulação como **CSP** (variáveis, domínios, restrições, backtracking) e a secção final de **Result Analysis & Conclusion** do `01_Project01_G04.ipynb` estão em desenvolvimento e não fazem ainda parte desta versão.

---

### 3. Estrutura de Ficheiros
```text
IA26_P01_G04/
│
├── data/                                 # Dataset CSV usado pelo projeto
│   ├── collection_centers.csv
│   ├── customers.csv
│   ├── delivery_locations.csv
│   ├── distance_matrix.csv
│   ├── localities.csv
│   ├── locations.csv
│   ├── order_items.csv
│   ├── orders.csv
│   ├── producers.csv
│   ├── products.csv
│   └── vehicles.csv
│
├── src/
│   ├── model.py                          # Modelação: Request, Vehicle, State, Problem,
│   │                                     # função de custo e validador de viabilidade de rotas
│   ├── informed.py                       # Greedy Best-First, A* e heurísticas
│   └── local_search.py                   # Hill-Climbing e Hill-Climbing com reinícios aleatórios
│
├── notebooks/
│   ├── 01_Project01_G04.ipynb            # Notebook principal (executado com outputs):
│   │                                     # Introdução, EDA, Modelação, Pesquisa informada (4.1)
│   │                                     # e Pesquisa local (4.2)
│   ├── 02_eda_tiny.ipynb                 # Análise exploratória de dados (dataset tiny)
│   └── 03_local_search.ipynb             # Notebook da pesquisa local (Hill-Climbing)
│
├── test_handwritten_routes.py            # Demonstração de 5 cenários de rotas
│
├── README.md                             # Este ficheiro
└── requirements.txt                      # Dependências Python do projeto
```

---

### 4. Instruções de Instalação e Execução

#### 4.1. Pré-requisitos
* Python 3.10 ou superior (validado em Python 3.14).
* Gestor de pacotes `pip`.

#### 4.2. Instalação das Dependências
No terminal ou PowerShell na raiz do projeto:
```bash
pip install -r requirements.txt
```

#### 4.3. Execução do Modelo e Demonstrações de Rotas Escritas à Mão
Para validar as classes e o comportamento do detetor de viabilidade de rotas:
```bash
python src/model.py
python test_handwritten_routes.py
```

Resultados esperados das cinco demonstrações:
1. **Rota Válida 1 (Item 5)**: Viável (164.51 km, 241.7 min com 22.3 min de espera legítima pela abertura da janela do cliente).
2. **Rota Válida 2 (Itens 10 e 7)**: Viável (263.23 km, 351.0 min).
3. **Rota Inválida 1 (Precedência)**: Rejeita a tentativa de entregar o Item 5 antes de ser recolhido.
4. **Rota Inválida 2 (Janela Temporal)**: Rejeita início de serviço às 17:26:42 após o fecho da recolha às 15:00 (atraso de 146,7 min).
5. **Rota Inválida 3 (Capacidade Excedida)**: Rejeita carga de 2000.00 kg que excede os 1444.70 kg da capacidade máxima do veículo.

#### 4.4. Pesquisa Informada e Pesquisa Local
Para executar as comparações em linha de comandos:
```bash
python src/informed.py
python src/local_search.py
```
Resultados no cenário usado nos notebooks:
* **Pesquisa informada** (artigos 7 e 10, partida a 19/10/2026 às 07:30): as 8 combinações (Greedy e A*, duas heurísticas, dois veículos) encontram a mesma rota, de **171,71 km**.
* **Pesquisa local** (artigos 7, 10, 17 e 22, partida a 19/10/2026 às 07:30): o Greedy obtém **343,91 km** e o Hill-Climbing melhora a rota para **304,69 km** em 2 iterações, valor igual ao ótimo encontrado pelo A* neste cenário.

#### 4.5. Visualização e Execução dos Notebooks
Para abrir os notebooks no Jupyter:
```bash
jupyter notebook
```
Ou executar diretamente via linha de comandos:
```bash
python -m jupyter nbconvert --to notebook --execute notebooks/02_eda_tiny.ipynb --inplace
python -m jupyter nbconvert --to notebook --execute notebooks/01_Project01_G04.ipynb --inplace
python -m jupyter nbconvert --to notebook --execute notebooks/03_local_search.ipynb --inplace
```

Todos os comandos são executados a partir da raiz do repositório. A primeira célula de cada notebook ajusta o diretório de trabalho e o `sys.path`, pelo que os notebooks também podem ser abertos diretamente a partir de `notebooks/`.

### 5. Valores confirmados diretamente nos CSV

* 11 CSV; 10 encomendas, 23 artigos e 248,96 kg de procura agregada.
* Veículos: 1444,70 kg e 1009,80 kg, ambos sem refrigeração. Centro: 3232,90 kg, em Terras de Bouro.
* Procura/capacidade: 17,23% do veículo 1 e 24,65% do veículo 2. Estas proporções não demonstram viabilidade de uma rota única.
* Pico por data de abertura da recolha: 43,58 kg em 19/10/2026. Não equivale a um plano diário viável.
* 12 artigos têm `ready_time > availability_end`: 1, 3, 4, 9, 13, 14, 15, 16, 18, 20, 21 e 23. Os restantes 11 são candidatos, sujeitos à validação da rota.
* Encomendar após a abertura é permitido. A recolha só é possível a partir de `max(order_datetime, availability_start)` e até ao fecho, inclusive.
* Janelas de entrega: 1 a 4 horas; algumas ocorrem no dia seguinte à disponibilidade.
* 12 localizações e 132 pares dirigidos sem diagonal (12 × 11). Distâncias do centro aos destinos: 9,14–50,94 km.

### 6. Contrato de validação

Uma rota exige partida explícita e regresso final ao depósito do veículo. Não permite partidas ou regressos intermédios. Todos os artigos recolhidos devem ser entregues antes do regresso. As janelas aplicam-se ao início do serviço, depois de eventual espera; o serviço tem duração zero e os limites são inclusivos.

O gerador de ações e o validador verificam as mesmas restrições temporais. O objetivo exige entrega dos artigos alvo, carga vazia e regresso ao depósito. `is_goal` aceita `vehicle_id` opcional (por omissão, 1). `return_to_base` lança `ValueError` se houver carga por entregar ou ligação de regresso inválida.

`cost_function` usa o validador antes de calcular métricas: uma rota inválida tem `feasible=False`, motivo em `error` e custo infinito. Mantêm-se os aliases portugueses das ações e os valores das duas rotas válidas originais.