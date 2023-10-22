import psycopg2

def check_authentication_client(contract_number, password):
    conn = psycopg2.connect(dbname='hackaton', user='postgres', 
                            password='egor123', host='localhost')
    cursor = conn.cursor()
    cursor.execute('SELECT Contract FROM Client WHERE Contract = %s', (contract_number,))
    client_contract_number = cursor.fetchone()
    cursor.execute('SELECT password FROM Client WHERE Contract = %s', (contract_number,))
    client_password = cursor.fetchone()
    conn.close()
    if client_contract_number: return False
    try:
        return password == client_password[0]
    except:
        return False

print(check_authentication_client("111","gosha2"))
