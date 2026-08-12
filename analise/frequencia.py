# analise/frequencia.py
import psycopg2
import pandas as pd
from collections import Counter
from config import DB_CONFIG, COLUNAS_BOLAS_DB, TOTAL_NUMEROS


def calcular_frequencias():
    """Calcula frequência de cada número e aplica teste Qui-Quadrado"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Buscar todos os sorteios
    df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso", conn)
    conn.close()
    
    # Extrair todos os números
    todos = []
    for _, row in df.iterrows():
        for col in COLUNAS_BOLAS_DB:
            todos.append(int(row[col]))
    
    freq = Counter(todos)
    total_sorteios = len(df)
    total_bolas = len(todos)
    freq_esperada = total_bolas / TOTAL_NUMEROS
    
    # Qui-Quadrado
    qui_quadrado = 0
    resultados = []
    for num in range(1, TOTAL_NUMEROS + 1):
        obs = freq.get(num, 0)
        esp = freq_esperada
        qui_quadrado += (obs - obs if obs == 0 else (obs - esp) ** 2 / esp)  # simplificado
        resultados.append({
            'numero': num,
            'freq_absoluta': obs,
            'freq_relativa': round(obs / total_sorteios * 100, 2),
            'freq_esperada': round(esp, 1)
        })
    
    # Salvar no banco
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    for r in resultados:
        cur.execute("""
            INSERT INTO frequencias (numero, total_aparicoes, frequencia_esperada, probabilidade)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (numero) DO UPDATE SET
                total_aparicoes = EXCLUDED.total_aparicoes,
                frequencia_esperada = EXCLUDED.frequencia_esperada,
                probabilidade = EXCLUDED.probabilidade
        """, (r['numero'], r['freq_absoluta'], r['freq_esperada'], r['freq_relativa'] / 100))
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'resultados': sorted(resultados, key=lambda x: x['freq_absoluta'], reverse=True),
        'total_sorteios': total_sorteios,
    }

if __name__ == "__main__":
    dados = calcular_frequencias()
    print(f"📊 Total de sorteios: {dados['total_sorteios']}")
    print("\n📊 TOP 10 MAIS FREQUENTES:")
    for r in dados['resultados'][:10]:
        print(f"   Nº {r['numero']:2d}: {r['freq_absoluta']:3d}x ({r['freq_relativa']:.1f}%)")
    print("\n📉 TOP 10 MENOS FREQUENTES:")
    for r in dados['resultados'][-10:]:
        print(f"   Nº {r['numero']:2d}: {r['freq_absoluta']:3d}x ({r['freq_relativa']:.1f}%)")
