# gerador.py - FINAL PRODUÇÃO
import psycopg2
import pandas as pd
import numpy as np
from config import DB_CONFIG, COLUNAS_BOLAS_DB

PRECOS = {15: 3.50, 16: 56.00, 17: 476.00}

def carregar_dados(janela=0):
    conn = psycopg2.connect(**DB_CONFIG)
    df_total = pd.read_sql("SELECT COUNT(*) as total FROM sorteios", conn)
    total_banco = df_total['total'].iloc[0]
    
    if janela == 0:
        limite = total_banco
        label = "TODOS"
    elif janela == 1000:
        limite = 1000
        label = "1000"
    else:
        limite = int(total_banco * 0.5)
        label = f"50% ({limite})"
    
    if limite >= total_banco:
        df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC", conn)
    else:
        df = pd.read_sql(f"SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {limite}", conn)
    conn.close()
    
    ultimo = df.iloc[0]
    ultimos_numeros = [int(ultimo[col]) for col in COLUNAS_BOLAS_DB]
    
    scores = {}
    for num in range(1, 26):
        count = sum(1 for _, r in df.iterrows() 
                    if num in [int(r[c]) for c in COLUNAS_BOLAS_DB])
        freq = count / len(df)
        atraso = 0
        for _, r in df.iterrows():
            if num in [int(r[c]) for c in COLUNAS_BOLAS_DB]:
                break
            atraso += 1
        bonus = 0.20 if num in ultimos_numeros else 0
        scores[num] = freq * 0.30 + (1 - 0.4**atraso) * 0.50 + bonus * 0.20
    
    return scores, ultimos_numeros, len(df), label

def gerar_jogo(ultimos, scores, semente):
    np.random.seed(semente)
    qtd_repetir = 8 if np.random.random() < 0.5 else 9
    qtd_fora = 15 - qtd_repetir
    
    repetir_ordenados = sorted(ultimos, key=lambda x: scores[x], reverse=True)
    fixos = repetir_ordenados[:5]
    candidatos = [n for n in repetir_ordenados if n not in fixos]
    np.random.shuffle(candidatos)
    variaveis = candidatos[:qtd_repetir - 5]
    escolhidos = fixos + variaveis
    
    nao_sairam = [n for n in range(1, 26) if n not in ultimos]
    fora_ordenados = sorted(nao_sairam, key=lambda x: scores[x], reverse=True)
    fixos_fora = fora_ordenados[:3]
    candidatos_fora = [n for n in fora_ordenados if n not in fixos_fora]
    np.random.shuffle(candidatos_fora)
    variaveis_fora = candidatos_fora[:qtd_fora - 3]
    
    escolhidos = escolhidos + fixos_fora + variaveis_fora
    jogo = sorted(set(escolhidos))[:15]
    while len(jogo) < 15:
        extras = [n for n in range(1, 26) if n not in jogo]
        extras.sort(key=lambda x: scores[x], reverse=True)
        jogo = sorted(jogo + [extras[0]])
    return jogo[:15]

def calcular_opcoes(orcamento):
    opcoes = []
    qtd_15 = int(orcamento / PRECOS[15])
    opcoes.append({'id': 1, 'label': f"{qtd_15} jogos de 15", 'qtd_15': qtd_15, 'qtd_16': 0, 'qtd_17': 0, 'total': int(qtd_15 * PRECOS[15])})
    if orcamento >= PRECOS[16]:
        resto = orcamento - PRECOS[16]; qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 2, 'label': f"1 de 16 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 1, 'qtd_17': 0, 'total': int(PRECOS[16] + qtd_15 * PRECOS[15])})
    if orcamento >= PRECOS[16] * 2:
        resto = orcamento - PRECOS[16] * 2; qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 3, 'label': f"2 de 16 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 2, 'qtd_17': 0, 'total': int(PRECOS[16] * 2 + qtd_15 * PRECOS[15])})
    if orcamento >= PRECOS[17]:
        resto = orcamento - PRECOS[17]; qtd_15 = int(resto / PRECOS[15])
        opcoes.append({'id': 4, 'label': f"1 de 17 + {qtd_15} de 15", 'qtd_15': qtd_15, 'qtd_16': 0, 'qtd_17': 1, 'total': int(PRECOS[17] + qtd_15 * PRECOS[15])})
    return opcoes
