# analise/atraso.py
import psycopg2
import pandas as pd
import numpy as np
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS, NUMEROS_POR_SORTEIO

def calcular_atrasos():
    """Calcula atraso atual e probabilidade binomial para cada número"""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso DESC", conn)
    conn.close()
    
    total_sorteios = len(df)
    prob_sair = NUMEROS_POR_SORTEIO / TOTAL_NUMEROS
    prob_nao_sair = 1 - prob_sair
    
    resultados = []
    for num in range(1, TOTAL_NUMEROS + 1):
        # Calcular atraso atual
        atraso = 0
        for _, row in df.iterrows():
            if num in [int(row[col]) for col in COLUNAS_BOLAS_DB]:
                break
            atraso += 1
        
        # Probabilidade binomial deste atraso ocorrer
        prob_atraso = round(prob_nao_sair ** atraso * 100, 4)
        
        # Buscar concursos onde o número apareceu
        conn2 = psycopg2.connect(**DB_CONFIG)
        cur = conn2.cursor()
        cur.execute("""
            SELECT concurso FROM sorteios 
            WHERE bola_1 = %s OR bola_2 = %s OR bola_3 = %s OR bola_4 = %s OR bola_5 = %s
               OR bola_6 = %s OR bola_7 = %s OR bola_8 = %s OR bola_9 = %s OR bola_10 = %s
               OR bola_11 = %s OR bola_12 = %s OR bola_13 = %s OR bola_14 = %s OR bola_15 = %s
            ORDER BY concurso
        """, tuple([num] * 15))
        concursos = [r[0] for r in cur.fetchall()]
        cur.close()
        conn2.close()
        
        if len(concursos) > 1:
            gaps = [concursos[i+1] - concursos[i] for i in range(len(concursos)-1)]
            gap_medio = float(round(np.mean(gaps), 2))  # <-- FORÇA float
        else:
            gap_medio = 0.0
        
        resultados.append({
            'numero': num,
            'atraso': atraso,
            'prob_atraso': prob_atraso,
            'gap_medio': gap_medio,
            'total_aparicoes': len(concursos)
        })
    
    # Atualizar banco
    conn3 = psycopg2.connect(**DB_CONFIG)
    cur = conn3.cursor()
    for r in resultados:
        cur.execute("""
            UPDATE frequencias SET 
                atraso_atual = %s,
                gap_medio = %s,
                ultima_aparicao = %s
            WHERE numero = %s
        """, (int(r['atraso']), float(r['gap_medio']), int(r['atraso']), int(r['numero'])))
    conn3.commit()
    cur.close()
    conn3.close()
    
    # Ordenar por atraso decrescente
    resultados.sort(key=lambda x: x['atraso'], reverse=True)
    return resultados

if __name__ == "__main__":
    dados = calcular_atrasos()
    print("\n⏰ TOP 10 MAIS ATRASADOS:")
    for r in dados[:10]:
        print(f"   🔴 Nº {r['numero']:2d}: {r['atraso']:3d} sorteios sem sair "
              f"(prob: {r['prob_atraso']:.4f}% | gap médio: {r['gap_medio']:.1f})")
    print("\n✅ NÚMEROS COM MENOR ATRASO:")
    for r in dados[-10:]:
        print(f"   ✅ Nº {r['numero']:2d}: {r['atraso']:3d} sorteios sem sair "
              f"(prob: {r['prob_atraso']:.4f}% | gap médio: {r['gap_medio']:.1f})")
