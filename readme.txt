================================================================================
PROJETO 01 - AGENTE INTELIGENTE DE OTIMIZACAO DE ROTAS DE DISTRIBUICAO ALIMENTAR
Unidade Curricular de Inteligencia Artificial - IPCA (2026/2027)
ENTREGA PRELIMINAR (FASE 1)
Repositorio Oficial: https://github.com/BrunoDantas1/IA26_P01_G04.git
================================================================================

1. IDENTIFICACAO DO GRUPO (GRUPO 04 - IA26_P01_G04)
--------------------------------------------------------------------------------
* Goncalo Correia - No 22840
* Bruno Dantas    - No 27958
* Ricardo Ferreira- No 25426

2. CONTEXTO DO PROBLEMA E OBJETIVOS DA ENTREGA PRELIMINAR
--------------------------------------------------------------------------------
Desenvolvimento de um agente inteligente para planeamento e otimizacao de rotas
de distribuicao alimentar local (pickup-and-delivery com janelas temporais e
restricoes de capacidade de carga) nos concelhos do distrito de Braga e Povoa
de Varzim.

Atores principais:
- Producers (Produtores locais com janelas [availability_start, availability_end]);
- CollectionCenters (Centros de recolha e bases operacionais dos veiculos);
- Customers / DeliveryLocations (Locais de entrega com janelas [delivery_start, delivery_end]);
- Vehicles (Carrinhas com capacidades maximas de 1444.7 kg e 1009.8 kg).

Conteudo da Entrega Preliminar:
- Analise Exploratoria de Dados (EDA) completa sobre o dataset data_tiny;
- Validacao da integridade referencial de todas as chaves primarias e estrangeiras;
- Modulo de modelacao orientada a objetos (model.py) com Request, Vehicle, State,
  Problem, cost_function e route_feasibility_checker rigoroso;
- Validacao experimental com rotas escritas a mao (hand-written routes) demonstrando
  rotas viaveis e confimacao de rejeicao de violacoes de precedencia, tempo e capacidade.
(Nota: O desenvolvimento dos algoritmos da Fase 2 sera entregue na submissao final,
estando guardado na branch fase2-completa).

3. ESTRUTURA DOS FICHEIROS DA ENTREGA PRELIMINAR
--------------------------------------------------------------------------------
- data/                 : Ficheiros CSV do dataset tiny
- data_tiny/            : Dataset tiny original
- model.py              : Modulo de modelacao (Request, Vehicle, State, Problem,
                          Cost Function e Route Feasibility Checker)
- 01_eda_tiny.ipynb     : Notebook de Analise Exploratoria de Dados (EDA completa)
- EDA.ipynb             : Copia conforme especificacao de submissao Moodle
- Proj01.ipynb          : Notebook Principal da Entrega Preliminar (executado com outputs)
- test_handwritten_routes.py : Testes automatizados das rotas manuais
- README.md             : Documentacao em formato Markdown
- readme.txt            : Este ficheiro em formato de texto simples
- requirements.txt      : Lista de dependencias Python

4. INSTRUCOES DE INSTALACAO E EXECUCAO
--------------------------------------------------------------------------------
Passo 1: Instalar dependencias Python (Python 3.10 ou superior):
    pip install -r requirements.txt

Passo 2: Executar testes de modelacao e rotas escritas a mao:
    python model.py
    python test_handwritten_routes.py

Passo 3: Executar e visualizar os notebooks Jupyter:
    jupyter notebook
    (abrir 01_eda_tiny.ipynb ou Proj01.ipynb)

    Para correr diretamente no terminal:
    python -m jupyter nbconvert --to notebook --execute 01_eda_tiny.ipynb --inplace
    python -m jupyter nbconvert --to notebook --execute Proj01.ipynb --inplace
================================================================================
