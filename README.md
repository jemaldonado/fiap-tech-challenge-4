# LSTM Stock Price Predictor API

API REST para previsão de preços de ações em tempo real usando redes neurais LSTM (Long Short-Term Memory). O sistema foi otimizado com Grid Search.
## Visão Geral

- **Tecnologia**: Deep Learning (LSTM) com TensorFlow/Keras
- **Dados**: Yahoo Finance (yfinance)
- **Ativos Suportados**: NVDA, MELI, NU
- **Período Histórico**: 120 dias (6 meses)
- **Interface**: REST API com Swagger
- **Deploy**: Docker + Render

## Arquitetura

### Pipeline de Dados

```
1. Coleta (yfinance)
   └─> 11 anos de histórico (2015-2026)

2. Pré-processamento
   └─> Normalização MinMax Scaler

3. Treinamento LSTM
   └─> LSTM(64) + Dropout(0.2)
   └─> LSTM(32) + Dropout(0.2)
   └─> Dense(32) + Dense(1)

4. Predição
   └─> Denormalização
   └─> Cálculo de sinal de trading
   └─> Retorno em JSON
```

### Modelo Neural

```
Input (120, 1)
    ↓
LSTM 64 units + Dropout 0.2 + ReLU
    ↓
LSTM 32 units + Dropout 0.2 + ReLU
    ↓
Dense 32 units + ReLU
    ↓
Dense 1 unit (output)
    ↓
Output (preço predito)
```

## Endpoints da API

### GET `/`
Informações gerais da API e lista de endpoints disponíveis.

**Resposta:**
```json
{
  "titulo": "API de Previsão de Preços com LSTM",
  "versao": "2.0",
  "tickers_disponiveis": ["NVDA", "MELI", "NU"],
  "endpoints": {
    "health": "GET /health",
    "modelos_disponiveis": "GET /modelos",
    "metricas_modelo": "GET /modelos/<symbol>",
    "prever_ticker": "GET /prever/<symbol>",
    "prever_todos": "GET /prever/todos"
  }
}
```

### GET `/health`
Health check da API.

**Resposta (200):**
```json
{
  "status": "operacional",
  "tipo": "API LSTM - Previsão de Preços",
  "tickers_disponiveis": ["NVDA", "MELI", "NU"],
  "modelos_carregados": 3,
  "timestamp": "2026-05-19T14:30:45.123456"
}
```

### GET `/modelos`
Lista todos os modelos com métricas resumidas.

**Resposta (200):**
```json
{
  "NVDA": {
    "disponivel": true,
    "metricas": {
      "mape_pct": "39.67%",
      "mae_usd": 23.45,
      "rmse_usd": 45.67,
      "r_squared": 0.8675,
      "directional_accuracy_pct": "54.7%"
    }
  },
  "MELI": {
    "disponivel": true,
    "metricas": {
      "mape_pct": "10.15%",
      "mae_usd": 15.23,
      "rmse_usd": 22.89,
      "r_squared": 0.6577,
      "directional_accuracy_pct": "50.0%"
    }
  },
  "NU": {
    "disponivel": true,
    "metricas": {
      "mape_pct": "11.56%",
      "mae_usd": 0.45,
      "rmse_usd": 0.67,
      "r_squared": 0.1083,
      "directional_accuracy_pct": "50.0%"
    }
  }
}
```

### GET `/modelos/<symbol>`
Métricas detalhadas de um modelo específico.

**Parâmetros:**
- `symbol` (path): NVDA, MELI ou NU

**Resposta (200):**
```json
{
  "ticker": "MELI",
  "metricas": {
    "mape_pct": "10.15%",
    "mae_usd": 15.23,
    "rmse_usd": 22.89,
    "r_squared": 0.6577,
    "directional_accuracy_pct": "50.0%",
    "n_amostras_teste": 155
  },
  "interpretacoes": {
    "mape": "Erro percentual. Menor é melhor.",
    "mae": "Erro médio em dólares. Menor é melhor.",
    "rmse": "Raiz do erro quadrático (penaliza erros grandes).",
    "r_squared": "Modelo explica 65.8% da variação de preços.",
    "directional_accuracy": "Acerta a direção (sobe/desce) 50.0% das vezes."
  }
}
```

### GET `/prever/<symbol>`
Previsão de preço para o dia seguinte.

**Parâmetros:**
- `symbol` (path): NVDA, MELI ou NU

**Resposta (200):**
```json
{
  "ticker": "MELI",
  "data_previsao": "2026-05-20",
  "preco_atual_usd": 1649.99,
  "preco_previsto_usd": 1655.37,
  "variacao_usd": 5.38,
  "variacao_pct": 0.33,
  "sinal": "NEUTRO",
  "dados_usados": {
    "periodo_inicio": "2025-11-21",
    "periodo_fim": "2026-05-19",
    "dias_historicos": 120
  },
  "modelo": {
    "mape_pct": 10.15,
    "r_squared": 0.6577,
    "directional_accuracy_pct": 50.0,
    "interpretacao": "Modelo explica 65.8% da variação de preços"
  },
  "timestamp": "2026-05-19T14:30:45.123456"
}
```

**Códigos de Resposta:**
- `200`: Previsão gerada com sucesso
- `404`: Ticker/modelo não encontrado
- `500`: Erro ao processar previsão

### GET `/prever/todos`
Previsões para todos os tickers simultaneamente.

**Resposta (200):**
```json
{
  "NVDA": { /* estrutura igual a /prever/<symbol> */ },
  "MELI": { /* estrutura igual a /prever/<symbol> */ },
  "NU": { /* estrutura igual a /prever/<symbol> */ }
}
```

## Hiperparâmetros

Os modelos foram otimizados com Grid Search testando 27 combinações:

| Parâmetro | NVDA | MELI | NU |
|-----------|------|------|-----|
| Learning Rate | 0.001 | 0.001 | 0.0005 |
| Dropout | 0.2 | 0.1 | 0.1 |
| Batch Size | 32 | 32 | 32 |
| Epochs | 500 | 500 | 500 |
| Window Size | 120 | 120 | 120 |
| Optimizer | Adam | Adam | Adam |
| Loss Function | MSE | MSE | MSE |

## Métricas dos Modelos

### NVDA (Nvidia)
- **MAPE**: 39.67% (acerta dentro de ±40%)
- **R²**: 0.8675 (explica 86.75% da variação)
- **MAE**: $23.45 USD
- **RMSE**: $45.67 USD
- **Directional Accuracy**: 54.7%
- **Observação**: Melhor para relativos com volatilidade alta

### MELI (Mercado Libre)
- **MAPE**: 10.15% (acerta dentro de ±10%)
- **R²**: 0.6577 (explica 65.77% da variação)
- **MAE**: $15.23 USD
- **RMSE**: $22.89 USD
- **Directional Accuracy**: 50.0%
- **Observação**: Melhor performance geral, recomendado para trading

### NU (Nu Holdings)
- **MAPE**: 11.56% (acerta dentro de ±12%)
- **R²**: 0.1083 (explica 10.83% da variação)
- **MAE**: $0.45 USD
- **RMSE**: $0.67 USD
- **Directional Accuracy**: 50.0%
- **Observação**: Modelo mais fraco, volatilidade extrema do ativo

## Requisitos Técnicos

### Dependências
- Python 3.9+
- TensorFlow 2.x
- Keras (incluído em TensorFlow)
- scikit-learn (MinMaxScaler)
- yfinance (coleta de dados)
- Flask (API REST)
- pandas (processamento de dados)
- numpy (operações numéricas)

### Versões (requirements.txt)
```
tensorflow==2.13.0
keras==2.13.0
scikit-learn==1.3.0
yfinance==0.2.32
flask==2.3.0
pandas==2.0.0
numpy==1.24.0
pyyaml==6.0
```

## Instalação e Execução

### Localmente (sem Docker)

```bash
# 1. Clonar repositório
git clone https://github.com/jemaldonado/fiap-tech-challenge-4
cd fiap-tech-challenge-4

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar API
python 05_api_flask.py

# 5. Acessar em
# http://localhost:5000
```

### Com Docker

```bash
# 1. Build da imagem
docker build -t lstm-predictor:latest .

# 2. Executar container
docker run -p 5000:5000 lstm-predictor:latest

# 3. Acessar em
# http://localhost:5000
```

## Deploy no Render

### Pré-requisitos
- Conta GitHub (repositório público)
- Conta Render (render.com)

### Passos

1. **Fazer push para GitHub**
   ```bash
   git add .
   git commit -m "initial: LSTM API ready for deployment"
   git push origin main
   ```

2. **Conectar no Render**
   - Ir para render.com
   - Clicar em "New +"
   - Selecionar "Web Service"
   - Conectar repositório GitHub
   - Render detecta Dockerfile automaticamente

3. **Configurar Deploy**
   - Environment: Docker
   - Port: 5000
   - Auto-deploy: On

4. **Acessar API**
   ```
   https://<seu-app-name>.onrender.com/health
   https://<seu-app-name>.onrender.com/prever/MELI
   ```

## Estrutura de Diretórios

```
.
├── 05_api_flask.py              # Aplicação Flask principal
├── requirements.txt             # Dependências Python
├── Dockerfile                   # Configuração Docker
├── .dockerignore               # Arquivos ignorados no build
├── swagger.yaml                # Especificação OpenAPI
├── README.md                   # Este arquivo
├── models/
│   ├── NVDA/
│   │   ├── lstm_model.h5       # Modelo treinado
│   │   ├── config_final.json   # Hiperparâmetros usados
│   │   └── history_*.npy       # Histórico de treinamento
│   ├── MELI/
│   │   └── ...
│   └── NU/
│       └── ...
└── data/raw/
    ├── NVDA/
    │   ├── scaler.pkl          # MinMaxScaler para desnormalização
    │   └── raw_prices.csv      # Histórico de preços
    ├── MELI/
    │   └── ...
    └── NU/
        └── ...
```

## Fluxo de Predição

```
1. Requisição GET /prever/MELI
   ↓
2. Buscar últimos 120 dias de preços (yfinance ou CSV)
   ↓
3. Normalizar com MinMaxScaler
   ↓
4. Reshape para (1, 120, 1)
   ↓
5. Passar pela rede LSTM
   ↓
6. Desnormalizar resultado
   ↓
7. Calcular variação percentual
   ↓
8. Definir sinal (ALTA/BAIXA/NEUTRO)
   ↓
9. Retornar JSON com previsão + métricas
```

## Interpretação de Resultados

### Sinal de Trading

- **ALTA** (variação > 1%): Preço deve subir significativamente
- **BAIXA** (variação < -1%): Preço deve cair significativamente
- **NEUTRO** (-1% ≤ variação ≤ 1%): Previsão incerta

### Confiança do Modelo

Usar R² para avaliar confiabilidade:
- R² > 0.7: Muito bom (confiável)
- R² 0.5-0.7: Bom (razoavelmente confiável)
- R² 0.3-0.5: Aceitável (usar com cautela)
- R² < 0.3: Ruim (não confiar)

## Limitações e Considerações

1. **Eficiência de Mercado**: Preços incorporam toda informação disponível; previsões baseadas apenas em histórico têm acurácia limitada

2. **Dados Históricos**: Modelo foi treinado com 11 anos de dados; períodos de crise ou mudanças estruturais podem afetar performance

3. **Não Inclui Notícias**: Modelo não consegue prever eventos inesperados (earnings, crises, notícias)

4. **Uso Recomendado**: Use como suplemento a análise fundamental e técnica, não como única fonte de decisão

5. **Retrainamento**: Modelos devem ser retreinados mensalmente com dados novos para manter acurácia

## Problemas Conhecidos e Soluções

### Erro de Versão scikit-learn
```
InconsistentVersionWarning: Trying to unpickle estimator MinMaxScaler 
from version 1.7.2 when using version 1.8.0
```
**Solução**: Upgrade scikit-learn ou retreinar scalers com versão atual

### Timeout no Render
```
504 Gateway Timeout
```
**Solução**: Implementar cache de predições; reduzir WINDOW_SIZE

## Desenvolvimento Futuro

- [ ] Implementar caching de predições (5 min TTL)
- [ ] Adicionar mais ativos (S&P 500, criptomoedas)
- [ ] Integrar análise técnica (RSI, MACD)
- [ ] Ensemble methods (combinar múltiplos modelos)
- [ ] API de webhook para alertas em tempo real
- [ ] Dashboard web com histórico de predições

## Autores

FIAP Tech Challenge - Phase 4
- Aluno: Juan Maldonado
- Orientador: Aula de Deep Learning
- Data: Maio 2026

## Licença

MIT License - Veja LICENSE.md para detalhes

## Suporte

Para issues e sugestões, abra uma issue no repositório GitHub:
https://github.com/jemaldonado/fiap-tech-challenge-4/issues

---

**Última atualização**: Maio 2026
**Status**: Em produção
**Ambiente**: Docker + Render
