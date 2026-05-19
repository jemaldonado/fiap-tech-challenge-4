"""
ETAPA 5: API REST Simplificada - Versao 2.0
API intuitiva para prever precos de acoes - GET /prever/<symbol> e pronto!
Busca dados automaticamente do Yahoo Finance, normaliza e retorna em USD.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import json
import pickle
import os
from datetime import datetime, timedelta

app = Flask(__name__)

SYMBOLS = ['NVDA', 'MELI', 'NU']
WINDOW_SIZE = 120
models_cache = {}
metrics_cache = {}
scalers_cache = {}

def carregar_modelos():
    """Carrega todos os modelos treinados"""
    carregados = 0
    for symbol in SYMBOLS:
        try:
            model_path = f'./models/{symbol}/lstm_model.h5'
            metrics_path = f'./models/{symbol}/metrics.json'
            scaler_path = f'./data/raw/{symbol}/scaler.pkl'

            if os.path.exists(model_path) and os.path.exists(metrics_path):
                models_cache[symbol] = load_model(model_path)
                with open(metrics_path, 'r') as f:
                    metrics_cache[symbol] = json.load(f)
                with open(scaler_path, 'rb') as f:
                    scalers_cache[symbol] = pickle.load(f)
                carregados += 1
                print(f"[OK] Carregado: {symbol}")
        except Exception as e:
            print(f"[AVISO] Erro em {symbol}: {e}")
    return carregados

def buscar_ultimos_precos(symbol, n=60):
    """
    Busca últimos n dias de preços usando dados salvos
    Retorna um array de preços de fechamento
    """
    try:
        csv_path = f'./data/raw/{symbol}/raw_prices.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if len(df) >= n:
                precos = df['Close'].values[-n:].astype(float)
                datas = df.index[-n:].tolist()
                return precos, datas
            else:
                raise ValueError(f"Insuficiente dados no CSV: {len(df)} < {n}")

        # Fallback: tentar baixar do yfinance
        df = yf.download(symbol, period='6mo', progress=False)
        if df.empty or len(df) < n:
            raise ValueError(f"Insuficiente dados: {len(df)} < {n}")

        precos = df['Close'].values[-n:].astype(float)
        return precos, df.index[-n:].tolist()
    except Exception as e:
        raise Exception(f"Erro ao buscar {symbol}: {str(e)}")

def prever_amanha(symbol):
    """
    Orquestra o fluxo completo: busca dados → normaliza → prediz → desnormaliza
    Retorna previsão em USD com todas as informações necessárias
    """
    if symbol not in models_cache:
        raise ValueError(f"Modelo para {symbol} não disponível")

    model = models_cache[symbol]
    scaler = scalers_cache[symbol]
    metrics = metrics_cache[symbol]

    # Buscar últimos 60 dias de preços reais (USD)
    precos_usd, datas = buscar_ultimos_precos(symbol, WINDOW_SIZE)

    # Normalizar com o scaler treinado
    precos_normalizados = scaler.transform(precos_usd.reshape(-1, 1)).flatten()

    # Reshape para (1, 60, 1) e fazer previsão
    X = precos_normalizados.reshape(1, WINDOW_SIZE, 1)
    preco_pred_norm = model.predict(X, verbose=0)[0][0]

    # Desnormalizar para USD
    preco_pred_usd = scaler.inverse_transform([[preco_pred_norm]])[0][0]

    # Preço atual (último dia do histórico)
    preco_atual_usd = precos_usd[-1]

    # Calcular variação
    variacao_usd = preco_pred_usd - preco_atual_usd
    variacao_pct = (variacao_usd / preco_atual_usd) * 100 if preco_atual_usd > 0 else 0

    # Sinal de trading
    if variacao_pct > 1:
        sinal = "ALTA"
    elif variacao_pct < -1:
        sinal = "BAIXA"
    else:
        sinal = "NEUTRO"

    # Datas para documento
    if isinstance(datas[-1], str):
        data_ultima = datas[-1][:10]  # Pega apenas YYYY-MM-DD se for string
        data_primeira = datas[0][:10]
    else:
        data_ultima = datas[-1].strftime('%Y-%m-%d')
        data_primeira = datas[0].strftime('%Y-%m-%d')
    data_previsao = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    return {
        'ticker': symbol,
        'data_previsao': data_previsao,
        'preco_atual_usd': round(float(preco_atual_usd), 2),
        'preco_previsto_usd': round(float(preco_pred_usd), 2),
        'variacao_usd': round(float(variacao_usd), 2),
        'variacao_pct': round(float(variacao_pct), 2),
        'sinal': sinal,
        'dados_usados': {
            'periodo_inicio': data_primeira,
            'periodo_fim': data_ultima,
            'dias_historicos': WINDOW_SIZE
        },
        'modelo': {
            'mape_pct': round(float(metrics.get('mape', 0)), 2),
            'r_squared': round(float(metrics.get('r_squared', 0)), 4),
            'directional_accuracy_pct': round(float(metrics.get('directional_accuracy', 0)) * 100, 1),
            'interpretacao': f"Modelo explica {metrics.get('r_squared', 0)*100:.1f}% da variação de preços"
        },
        'timestamp': datetime.utcnow().isoformat()
    }

# ===== CARREGAR MODELOS =====
n_modelos = carregar_modelos()
print(f"\n{'='*60}")
print(f"[OK] {n_modelos}/{len(SYMBOLS)} modelo(s) carregado(s)")
print(f"{'='*60}\n")

# ===== ROTAS =====

@app.route('/')
def index():
    """Raiz da API com documentação"""
    return jsonify({
        'titulo': 'API de Previsão de Preços com LSTM',
        'versao': '2.0',
        'descricao': 'Preveja o preço de fechamento de ações para amanhã de forma simples',
        'endpoints': {
            'health': 'GET /health',
            'modelos_disponiveis': 'GET /modelos',
            'metricas_modelo': 'GET /modelos/<symbol>',
            'prever_ticker': 'GET /prever/<symbol>',
            'prever_todos': 'GET /prever/todos',
            'documentacao_interativa': 'GET /apidocs'
        },
        'tickers_disponiveis': SYMBOLS,
        'exemplo_uso': 'GET /prever/NVDA retorna previsão em USD para amanhã'
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check da API"""
    return jsonify({
        'status': 'operacional',
        'tipo': 'API LSTM - Previsão de Preços',
        'tickers_disponiveis': list(models_cache.keys()),
        'modelos_carregados': len(models_cache),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/modelos', methods=['GET'])
def listar_modelos():
    """Lista todos os modelos disponíveis com métricas resumidas"""
    resultado = {}
    for symbol, metrics in metrics_cache.items():
        resultado[symbol] = {
            'disponivel': True,
            'metricas': {
                'mape_pct': f"{metrics.get('mape', 0):.2f}%",
                'mae_usd': round(metrics.get('mae_real', 0), 2),
                'rmse_usd': round(metrics.get('rmse_real', 0), 2),
                'r_squared': round(metrics.get('r_squared', 0), 4),
                'directional_accuracy_pct': f"{metrics.get('directional_accuracy', 0)*100:.1f}%"
            }
        }
    return jsonify(resultado)

@app.route('/modelos/<symbol>', methods=['GET'])
def detalhes_modelo(symbol):
    """Retorna métricas detalhadas de um modelo específico"""
    symbol = symbol.upper()
    if symbol not in metrics_cache:
        return jsonify({'erro': f'Modelo para {symbol} não encontrado'}), 404

    metrics = metrics_cache[symbol]
    return jsonify({
        'ticker': symbol,
        'metricas': {
            'mape_pct': f"{metrics.get('mape', 0):.2f}%",
            'mae_usd': round(metrics.get('mae_real', 0), 2),
            'rmse_usd': round(metrics.get('rmse_real', 0), 2),
            'r_squared': round(metrics.get('r_squared', 0), 4),
            'directional_accuracy_pct': f"{metrics.get('directional_accuracy', 0)*100:.1f}%",
            'n_amostras_teste': metrics.get('n_test_samples', 0)
        },
        'interpretacoes': {
            'mape': 'Erro percentual. Menor é melhor.',
            'mae': 'Erro médio em dólares. Menor é melhor.',
            'rmse': 'Raiz do erro quadrático (penaliza erros grandes).',
            'r_squared': f"Modelo explica {metrics.get('r_squared', 0)*100:.1f}% da variação de preços.",
            'directional_accuracy': f"Acerta a direção (sobe/desce) {metrics.get('directional_accuracy', 0)*100:.1f}% das vezes."
        }
    })

@app.route('/prever/<symbol>', methods=['GET'])
def prever_preco(symbol):
    """
    Prever o preço de fechamento para amanhã
    Busca dados automaticamente do Yahoo Finance, normaliza e retorna em USD

    Exemplo: GET /prever/NVDA
    """
    symbol = symbol.upper()
    try:
        if symbol not in models_cache:
            return jsonify({'erro': f'Modelo para {symbol} não disponível'}), 404

        previsao = prever_amanha(symbol)
        return jsonify(previsao)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/prever/todos', methods=['GET'])
def prever_todos():
    """
    Prever os preços para amanhã de todos os tickers disponíveis

    Exemplo: GET /prever/todos
    """
    try:
        resultados = {}
        for symbol in models_cache.keys():
            resultados[symbol] = prever_amanha(symbol)
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/apidocs', methods=['GET'])
def swagger_ui():
    """Retorna Swagger UI (documentação interativa)"""
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>API LSTM - Documentação Interativa</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
        <style>
          html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
          *, *:before, *:after { box-sizing: inherit; }
          body { margin:0; padding:0; }
        </style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script>
          const ui = SwaggerUIBundle({
            url: "/swagger.json",
            dom_id: '#swagger-ui',
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout"
          })
          window.ui = ui
        </script>
      </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html'}

@app.route('/swagger.json', methods=['GET'])
def swagger_spec():
    """Retorna especificação Swagger em JSON"""
    import yaml
    import os
    swagger_path = os.path.join(os.path.dirname(__file__), 'swagger.yaml')
    with open(swagger_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    response = jsonify(spec)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

# ===== INICIAR =====
if __name__ == '__main__':
    print("=" * 60)
    print("API LSTM - PREVISÃO DE PREÇOS")
    print("=" * 60)
    print("\nAcesse em:")
    print("  [DOCS] Documentação interativa: http://localhost:5000/apidocs")
    print("  [INFO] Info geral: http://localhost:5000/")
    print("  [HEALTH] Health check: http://localhost:5000/health")
    print("  [MODELOS] Modelos: http://localhost:5000/modelos")
    print("  [PREVER] Prever NVDA: http://localhost:5000/prever/NVDA")
    print("\n" + "=" * 60 + "\n")

    app.run(debug=False, host='0.0.0.0', port=5000)
