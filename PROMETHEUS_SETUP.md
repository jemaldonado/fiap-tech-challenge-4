# Configuração Prometheus + Grafana no Render

## Visão Geral

Este projeto agora monitora a API LSTM em produção usando Prometheus para coleta de métricas e pode ser visualizado via Grafana.

### O que é monitorado:
- ✅ **Tempo de resposta da API** (latência em segundos)
- ✅ **Total de requisições** (contadas por endpoint e status code)
- ✅ **Total de previsões** (contadas por ticker e sinal de trading)
- ✅ **Taxa de erro** (HTTP 4xx, 5xx)

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    RENDER                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │   API-LSTM       │      │   PROMETHEUS     │   │
│  │  (porta 5000)    │◄────►│  (porta 9090)    │   │
│  │                  │      │                  │   │
│  │ Exporta métricas │      │ Scrapa a cada 15s│  │
│  │ em /metrics      │      │                  │   │
│  └──────────────────┘      └──────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
         ↑
         │ (opcional)
    ┌────▼────────┐
    │  GRAFANA    │
    │ (visualiza) │
    └─────────────┘
```

---

## Passo 1: Testar Localmente

### 1.1 Com docker-compose (recomendado)

```bash
cd fiap-tech-challenge-4-deploy
docker-compose up
```

Depois acesse:
- **API:** http://localhost:5000/
- **API Docs:** http://localhost:5000/apidocs
- **Prometheus:** http://localhost:9090/
- **Métricas bruto:** http://localhost:5000/metrics

### 1.2 Verificar métricas no Prometheus

No browser, acesse http://localhost:9090 e digite na caixa de busca:
- `api_requests_total` - Total de requisições
- `api_request_duration_seconds` - Latência
- `predictions_total` - Total de previsões

Clique em "Graph" para visualizar gráfico.

---

## Passo 2: Deploy no Render

### 2.1 Adicionar nova Web Service para Prometheus

No dashboard do Render, clique em "New +" > "Web Service"

**Configuração:**
- **Name:** `api-lstm-prometheus`
- **GitHub Repository:** seu repositório (mesmo do API)
- **Root Directory:** `fiap-tech-challenge-4-deploy`
- **Environment:** Python
- **Build Command:** 
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  docker run --name prometheus -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus:latest
  ```
  
  **OU** (melhor):
  ```
  docker build -f Dockerfile.prometheus -t prometheus . && docker run -p 9090:9090 prometheus
  ```

- **Plan:** Free tier (OK para monitoramento)

### 2.2 Configurar variáveis de ambiente

Deixe em branco (não precisa de env vars).

### 2.3 Conectar API ao Prometheus

No Render, a API existente já está exportando métricas em `/metrics`.

O Prometheus novo precisa "achar" a API. Adicione esta variável de ambiente ao serviço Prometheus:

```
PROMETHEUS_API_HOST=api-lstm.onrender.com
PROMETHEUS_API_PORT=443
PROMETHEUS_API_SCHEME=https
```

E modifique o `prometheus.yml` para usar variáveis:
```yaml
scrape_configs:
  - job_name: 'api-lstm'
    scheme: https
    static_configs:
      - targets: ['api-lstm.onrender.com']
```

---

## Passo 3: Visualizar com Grafana (Opcional)

### Opção A: Grafana Cloud (Recomendado)

1. Crie conta gratuita em https://grafana.com/auth/sign-up/create-account
2. Add data source: Prometheus
3. URL: `http://seu-prometheus.onrender.com:9090`
4. Create dashboards usando queries como:
   - `rate(api_requests_total[5m])` - Requisições por segundo
   - `histogram_quantile(0.95, api_request_duration_seconds_bucket)` - P95 latência
   - `rate(predictions_total[5m])` - Previsões por segundo

### Opção B: Grafana no Render

Adicione outro serviço Web Service:
- **Docker Image:** `grafana/grafana:latest`
- **Porta:** 3000
- **Data source:** http://api-lstm-prometheus:9090

---

## Métricas Disponíveis

### 1. `api_requests_total`
Contador de requisições HTTP
```
Labels: method (GET, POST), endpoint, status (200, 404, 500)
Exemplo: rate(api_requests_total[5m]) - requisições por segundo
```

### 2. `api_request_duration_seconds`
Latência das requisições
```
Labels: endpoint
Exemplo: histogram_quantile(0.95, api_request_duration_seconds_bucket) - P95
```

### 3. `predictions_total`
Contador de previsões feitas
```
Labels: ticker (NVDA, MELI, NU), signal (ALTA, BAIXA, NEUTRO)
Exemplo: rate(predictions_total{ticker="NVDA"}[5m])
```

---

## Dashboard Recomendado (Prometheus built-in)

Acesse http://prometheus-url/graph e customize:

```
1. HTTP Requests/sec
   Expressão: rate(api_requests_total[1m])

2. Error Rate (%)
   Expressão: rate(api_requests_total{status=~"[45].."}[1m]) / rate(api_requests_total[1m]) * 100

3. P95 Latência (ms)
   Expressão: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) * 1000

4. Previsões por Ticker
   Expressão: rate(predictions_total[5m])

5. API Status
   Expressão: up{job="api-lstm"}
```

---

## Troubleshooting

### Prometheus não consegue scraper a API

**Sintomas:**
- No Prometheus UI, job `api-lstm` mostra `DOWN`
- Aviso: "context deadline exceeded"

**Soluções:**
1. Verifique se a API está rodando: `curl https://api-lstm.onrender.com/health`
2. Verifique se `/metrics` responde: `curl https://api-lstm.onrender.com/metrics`
3. Aumente `scrape_timeout` em `prometheus.yml` para `20s`
4. Para Render, use HTTPS e adicione certificado se necessário

### Métricas não aparecem

**Soluções:**
1. Gere requisições à API: `curl https://api-lstm.onrender.com/prever/NVDA`
2. Espere 15 segundos (scrape_interval)
3. Acesse Prometheus e procure por `api_requests_total`

### Prometheus está muito pesado

**Solução:**
- Diminua retention: `--storage.tsdb.retention.time=7d` (padrão é 15 dias)
- Ou use Grafana Cloud em vez de rodar Prometheus no Render

---

## Comandos Úteis

```bash
# Testar API localmente
curl http://localhost:5000/health
curl http://localhost:5000/prever/NVDA
curl http://localhost:5000/metrics

# Testar Prometheus
curl http://localhost:9090/-/healthy

# Ver logs do Prometheus (docker)
docker logs prometheus

# Ver logs da API
docker logs api-lstm
```

---

## Próximos Passos

1. ✅ Adicionar Prometheus ao Render
2. ✅ Testar scraping de métricas
3. ⭕ Adicionar Grafana para visualização
4. ⭕ Criar alertas (opcional) se tempo resposta > 5s

---

**Data de Criação:** 2026-05-19  
**Última Atualização:** 2026-05-19
