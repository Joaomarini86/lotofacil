# alimentar.py - Alimentar o banco com novos resultados
import psycopg2
import pandas as pd
from datetime import datetime
from config import DB_CONFIG, CAMINHO_EXCEL, SHEET_NAME, COLUNAS_BOLAS_DB

def inserir_sorteio(concurso, data, bolas):
    """Insere um sorteio manualmente"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO sorteios (concurso, data, 
                bola_1, bola_2, bola_3, bola_4, bola_5,
                bola_6, bola_7, bola_8, bola_9, bola_10,
                bola_11, bola_12, bola_13, bola_14, bola_15)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (concurso) DO UPDATE SET
                data = EXCLUDED.data,
                bola_1 = EXCLUDED.bola_1, bola_2 = EXCLUDED.bola_2,
                bola_3 = EXCLUDED.bola_3, bola_4 = EXCLUDED.bola_4,
                bola_5 = EXCLUDED.bola_5, bola_6 = EXCLUDED.bola_6,
                bola_7 = EXCLUDED.bola_7, bola_8 = EXCLUDED.bola_8,
                bola_9 = EXCLUDED.bola_9, bola_10 = EXCLUDED.bola_10,
                bola_11 = EXCLUDED.bola_11, bola_12 = EXCLUDED.bola_12,
                bola_13 = EXCLUDED.bola_13, bola_14 = EXCLUDED.bola_14,
                bola_15 = EXCLUDED.bola_15
        """, (concurso, data, *bolas))
        conn.commit()
        print(f"✅ Concurso {concurso} inserido/atualizado com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro: {e}")
    
    finally:
        cur.close()
        conn.close()

def inserir_do_excel(caminho_excel, sheet_name):
    """Importa sorteios de uma planilha Excel"""
    try:
        df = pd.read_excel(caminho_excel, sheet_name=sheet_name)
        
        # Verificar colunas
        colunas_esperadas = ['Concurso', 'Data'] + [f'bola {i}' for i in range(1, 16)]
        if not all(col in df.columns for col in colunas_esperadas):
            print(f"❌ Planilha não tem as colunas esperadas!")
            print(f"   Esperado: {colunas_esperadas}")
            print(f"   Encontrado: {list(df.columns)}")
            return
        
        total = 0
        for _, row in df.iterrows():
            concurso = int(row['Concurso'])
            data = datetime.strptime(str(row['Data']), '%d/%m/%Y').date()
            bolas = [int(row[f'bola {i}']) for i in range(1, 16)]
            
            inserir_sorteio(concurso, data, bolas)
            total += 1
        
        print(f"\n📊 Total: {total} sorteios importados da planilha!")
        
    except Exception as e:
        print(f"❌ Erro ao ler planilha: {e}")

def listar_ultimos(limite=10):
    """Lista os últimos sorteios cadastrados"""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(f"""
        SELECT concurso, data, bola_1, bola_2, bola_3, bola_4, bola_5,
               bola_6, bola_7, bola_8, bola_9, bola_10,
               bola_11, bola_12, bola_13, bola_14, bola_15
        FROM sorteios 
        ORDER BY concurso DESC 
        LIMIT {limite}
    """, conn)
    conn.close()
    
    print(f"\n📋 ÚLTIMOS {limite} SORTEIOS CADASTRADOS:")
    print("-" * 80)
    for _, row in df.iterrows():
        bolas = [int(row[f'bola_{i}']) for i in range(1, 16)]
        print(f"   Concurso {int(row['concurso'])} ({row['data']}): {bolas}")
    
    return df

def menu():
    """Menu interativo"""
    while True:
        print("\n" + "=" * 50)
        print("📥 ALIMENTADOR DE SORTEIOS")
        print("=" * 50)
        print("1. 📝 Inserir sorteio manualmente")
        print("2. 📂 Importar de planilha Excel")
        print("3. 📋 Listar últimos sorteios")
        print("4. ❌ Sair")
        
        opcao = input("\n👉 Escolha: ")
        
        if opcao == '1':
            try:
                concurso = int(input("   Nº do concurso: "))
                data_str = input("   Data (DD/MM/AAAA): ")
                data = datetime.strptime(data_str, '%d/%m/%Y').date()
                
                print("   Digite os 15 números separados por vírgula:")
                print("   Ex: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15")
                bolas_str = input("   ➜ ")
                bolas = [int(b.strip()) for b in bolas_str.split(',')]
                
                if len(bolas) != 15:
                    print(f"❌ Devem ser 15 números (você digitou {len(bolas)})")
                    continue
                
                if any(b < 1 or b > 25 for b in bolas):
                    print("❌ Números devem estar entre 1 e 25")
                    continue
                
                inserir_sorteio(concurso, data, bolas)
                
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        elif opcao == '2':
            caminho = input("   📁 Caminho da planilha .xlsx: ")
            if not caminho.strip():
                caminho = CAMINHO_EXCEL
                print(f"   Usando padrão: {caminho}")
            
            sheet = input(f"   📄 Nome da aba (Enter para '{SHEET_NAME}'): ")
            if not sheet.strip():
                sheet = SHEET_NAME
            
            inserir_do_excel(caminho, sheet)
        
        elif opcao == '3':
            try:
                limite = int(input("   Quantos listar? (Enter=10): ") or "10")
                listar_ultimos(limite)
            except:
                listar_ultimos()
        
        elif opcao == '4':
            print("👋 Até mais!")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    menu()
