# testar_janelas.py - Testa diferentes janelas de tempo
import psycopg2
import pandas as pd
import numpy as np
from config import DB_CONFIG, COLUNAS_BOLAS_DB

PRECOS = {15: 3.50}
sorteados_3757 = [1, 2, 3, 4, 6, 8, 11, 12, 15, 17, 20, 21, 22, 23, 24]
sorteados_3758 = [1, 3, 4, 5, 8, 9, 11, 12, 13, 14, 17, 18, 20, 24, 25]

def testar_janela(janela):
    """Testa o desempenho de uma janela específica"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    if janela == 0:
        df_total = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC", conn)
    else:
        df_total = pd.read_sql(f"""
            SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {janela}
        """, conn)
    
    df_desc = df_total.copy()
    conn.close()
    
    ultimo = df_desc.iloc[0]
    ultimos_numeros = [int(ultimo[col]) for col in COLUNAS_BOLAS_DB]
    
    total = len(df_total)
    
    # Calcular scores com base APENAS na janela
    scores = {}
    for num in range(1, 26):
        count = 0
        for _, row in df_total.iterrows():
            if num in [int(row[col]) for col in COLUNAS_BOLAS_DB]:
                count += 1
        freq = count / total if total > 0 else 0
        
        atraso = 0
        for _, row in df_desc.iterrows():
            if num in [int(row[col]) for col in COLUNAS_BOLAS_DB]:
                break
            atraso += 1
        
        bonus_ultimo = 0.20 if num in ultimos_numeros else 0
        score = freq * 0.30 + (1 - 0.4**atraso) * 0.50 + bonus_ultimo * 0.20
        scores[num] = score
    
    ranking = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    # Gerar 6 jogos (como R$ 20)
    jogos = []
    base = sorted(ranking[:15])
    jogos.append(base)
    
    reservas = ranking[15:]
    for i in range(min(len(reservas), 5)):
        piores = sorted(base, key=lambda x: scores[x])[:2]
        if i < len(reservas):
            novo = [n for n in base if n not in [piores[i % 2]]] + [reservas[i]]
            novo = sorted(novo)
            if novo not in jogos:
                jogos.append(novo)
    
    jogos = jogos[:6]
    
    # Testar contra 3757
    acertos_3757 = []
    for jogo in jogos:
        acertos_3757.append(len(set(jogo) & set(sorteados_3757)))
    
    # Testar contra 3758 (se tiver mais de 1 jogo)
    acertos_3758 = []
    for jogo in jogos:
        acertos_3758.append(len(set(jogo) & set(sorteados_3758)))
    
    return {
        'janela': janela if janela > 0 else 'TODOS',
        'qtd': len(jogos),
        'media_3757': np.mean(acertos_3757),
        'max_3757': max(acertos_3757),
        'onze_3757': sum(1 for a in acertos_3757 if a >= 11),
        'media_3758': np.mean(acertos_3758),
        'max_3758': max(acertos_3758),
        'onze_3758': sum(1 for a in acertos_3758 if a >= 11),
        'scores': scores,
        'ultimos': ultimos_numeros
    }

if __name__ == "__main__":
    print("🔬 TESTE DE DIFERENTES JANELAS DE TEMPO")
    print("=" * 60)
    print(f"{'Janela':<10} {'Média3757':<12} {'Max3757':<10} {'11+3757':<10} {'Média3758':<12} {'Max3758':<10} {'11+3758':<10}")
    print("-" * 70)
    
    janelas = [50, 100, 200, 500, 1000, 0]  # 0 = TODOS
    
    resultados = []
    for janela in janelas:
        r = testar_janela(janela)
        label = str(janela) if janela > 0 else 'TODOS'
        resultados.append(r)
        print(f"{label:<10} {r['media_3757']:<12.1f} {r['max_3757']:<10} {r['onze_3757']:<10} {r['media_3758']:<12.1f} {r['max_3758']:<10} {r['onze_3758']:<10}")
    
    print("\n" + "=" * 60)
    print("MELHOR JANELA PARA CADA CRITÉRIO:")
    print("=" * 60)
    
    melhor_media = max(resultados, key=lambda x: x['media_3757'] + x['media_3758'])
    print(f"✅ Melhor média geral: {melhor_media['janela']} sorteios")
    
    melhor_onze = max(resultados, key=lambda x: x['onze_3757'] + x['onze_3758'])
    print(f"✅ Mais 11+ acertos: {melhor_onze['janela']} sorteios")
    
    print(f"\n📊 Detalhes da melhor janela ({melhor_media['janela']}):")
    print(f"   Último sorteio da janela: {melhor_media['ultimos']}")
    print(f"   Top 10 scores:")
    for n in sorted(melhor_media['scores'].keys(), key=lambda x: melhor_media['scores'][x], reverse=True)[:10]:
        print(f"      Nº {n:2d}: {melhor_media['scores'][n]:.4f}")
