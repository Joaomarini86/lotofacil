# banco.py - Conexão e migração dos dados para PostgreSQL
import pandas as pd
import psycopg2
from config import DB_CONFIG, CAMINHO_EXCEL, SHEET_NAME, COLUNAS_BOLAS

def conectar():
    """Retorna conexão com o PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)

def criar_tabelas():
    """Cria a estrutura do banco de dados"""
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sorteios (
            concurso INTEGER PRIMARY KEY,
            data DATE NOT NULL,
            bola_1 INTEGER NOT NULL, bola_2 INTEGER NOT NULL,
            bola_3 INTEGER NOT NULL, bola_4 INTEGER NOT NULL,
            bola_5 INTEGER NOT NULL, bola_6 INTEGER NOT NULL,
            bola_7 INTEGER NOT NULL, bola_8 INTEGER NOT NULL,
            bola_9 INTEGER NOT NULL, bola_10 INTEGER NOT NULL,
            bola_11 INTEGER NOT NULL, bola_12 INTEGER NOT NULL,
            bola_13 INTEGER NOT NULL, bola_14 INTEGER NOT NULL,
            bola_15 INTEGER NOT NULL
        );
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS frequencias (
            numero INTEGER PRIMARY KEY,
            total_aparicoes INTEGER NOT NULL,
            frequencia_esperada NUMERIC(6,2),
            probabilidade NUMERIC(6,4),
            atraso_atual INTEGER DEFAULT 0,
            gap_medio NUMERIC(6,2),
            ultima_aparicao INTEGER
        );
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS co_ocorrencia (
            numero_a INTEGER,
            numero_b INTEGER,
            vezes_juntos INTEGER NOT NULL,
            PRIMARY KEY (numero_a, numero_b)
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tabelas criadas com sucesso!")

def migrar_excel_para_postgres():
    """Lê o Excel e insere no PostgreSQL"""
    df = pd.read_excel(CAMINHO_EXCEL, sheet_name=SHEET_NAME)
    
    conn = conectar()
    cur = conn.cursor()
    
    total = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO sorteios (concurso, data, 
                    bola_1, bola_2, bola_3, bola_4, bola_5,
                    bola_6, bola_7, bola_8, bola_9, bola_10,
                    bola_11, bola_12, bola_13, bola_14, bola_15)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (concurso) DO NOTHING
            """, (int(row['Concurso']), row['Data'],
                  int(row['bola 1']), int(row['bola 2']),
                  int(row['bola 3']), int(row['bola 4']),
                  int(row['bola 5']), int(row['bola 6']),
                  int(row['bola 7']), int(row['bola 8']),
                  int(row['bola 9']), int(row['bola 10']),
                  int(row['bola 11']), int(row['bola 12']),
                  int(row['bola 13']), int(row['bola 14']),
                  int(row['bola 15'])))
            total += 1
        except Exception as e:
            print(f"Erro no concurso {row['Concurso']}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ {total} sorteios migrados para PostgreSQL!")

if __name__ == "__main__":
    criar_tabelas()
    migrar_excel_para_postgres()
