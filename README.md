# Projeto 01 — Agente Inteligente de Otimização de Rotas de Distribuição Alimentar Local
## Unidade Curricular de Inteligência Artificial — IPCA (2026/2027)
### Entrega Preliminar (Fase 1): Modelação, Análise Exploratória e Validador de Rotas

**Repositório Oficial:** [https://github.com/BrunoDantas1/IA26_P01_G04.git](https://github.com/BrunoDantas1/IA26_P01_G04.git)

---

### 1. Identificação do Grupo (Grupo 04 — `IA26_P01_G04`)
* **Gonçalo Correia** — Nº 22840
* **Bruno Dantas** — Nº 27958
* **Ricardo Ferreira** — Nº 25426

---

### 2. Contexto do Problema e Objetivos da Entrega Preliminar
O objetivo deste projeto é o desenvolvimento de um agente inteligente de planeamento de rotas (*pickup-and-delivery* com restrições de janelas temporais e capacidade de carga) para distribuição alimentar local no distrito de Braga e Póvoa de Varzim, ligando três atores principais:
1. **Produtores Locais (*Producers*)**: Locais de recolha dos produtos com janelas horárias regulamentares $[availability\_start, availability\_end]$.
2. **Centros de Recolha / Armazéns (*CollectionCenters*)**: Plataformas logísticas de agregação e base operacional obrigatória da frota de veículos (*Vehicles*).
3. **Locais de Entrega (*DeliveryLocations / Customers*)**: Destinos finais onde as encomendas devem ser entregues dentro da janela $[delivery\_start, delivery\_end]$.
4. **Matriz de Distâncias e Tempos (*DistanceMatrix*)**: Distâncias ortodrómicas com fator rodoviário de 1.3 e durações com base numa velocidade de referência de 45 km/h entre todas as paragens unificadas (`locations.csv`).

Nesta **Entrega Preliminar (Fase 1)** focamo-nos na fundamentação rigorosa do problema:
* **Análise Exploratória de Dados (EDA)** exaustiva sobre o dataset `data_tiny`.
* **Validação de Integridade Referencial** das chaves primárias e estrangeiras.
* **Módulo de Modelação (`model.py`)** com classes tipadas (`Request`, `Vehicle`, `State`, `Problem`), função de custo e validador estrito de viabilidade de rotas.
* **Testes de Validação com Rotas Escritas à Mão (*Hand-Written Routes*)**, comprovando a deteção de rotas válidas e de violações de precedência, janelas temporais e capacidade máxima.

*(Nota: O desenvolvimento dos algoritmos de pesquisa informada, pesquisa local, CSP e coordenação de frota da Fase 2 será entregue na submissão final do projeto, encontrando-se guardado na branch `fase2-completa`).*

---

### 3. Estrutura de Ficheiros da Entrega Preliminar
```text
IA26_P01_G04/
│
├── data/                                 # Datasets em formato CSV (cópia normalizada)
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
├── data_tiny/                            # Dataset tiny original
│   └── ... (ficheiros CSV)
│
├── model.py                              # Módulo de modelação orientada a objetos:
│                                         # Request, Vehicle, State, Problem,
│                                         # Cost Function e Route Feasibility Checker rigoroso
│
├── EDA.ipynb                             # Cópia do notebook EDA conforme nomenclatura do Moodle
├── Proj01.ipynb                          # Notebook Principal da Entrega Preliminar (executado com outputs):
│                                         # Introdução, EDA executivo e Testes Hand-Written
│
├── test_handwritten_routes.py            # Script automatizado com 5 testes de rotas escritas à mão
│
├── README.md                             # Documentação da Entrega Preliminar em Markdown
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

#### 4.3. Execução dos Testes de Modelação e Rotas Escritas à Mão
Para validar as classes e o comportamento do detetor de viabilidade de rotas:
```bash
python model.py
python test_handwritten_routes.py
```

Resultados comprovados pelo teste:
1. **Rota Válida 1 (Item 5)**: Viável (164.51 km, 241.7 min com 22.3 min de espera legítima pela abertura da janela do cliente).
2. **Rota Válida 2 (Itens 10 e 7)**: Viável (263.23 km, 351.0 min).
3. **Rota Inválida 1 (Precedência)**: Rejeita a tentativa de entregar o Item 5 antes de ser recolhido.
4. **Rota Inválida 2 (Janela Temporal)**: Rejeita chegada às 17:26 após o fecho da janela das 15:00 (atraso de 146.7 min).
5. **Rota Inválida 3 (Capacidade Excedida)**: Rejeita carga de 2000.00 kg que excede os 1444.70 kg da capacidade máxima do veículo.

#### 4.4. Visualização e Execução dos Notebooks
Para abrir os notebooks no Jupyter:
```bash
jupyter notebook
```
Ou executar diretamente via linha de comandos:
```bash
python -m jupyter nbconvert --to notebook --execute 01_eda_tiny.ipynb --inplace
python -m jupyter nbconvert --to notebook --execute Proj01.ipynb --inplace

