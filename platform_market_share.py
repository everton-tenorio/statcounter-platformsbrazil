from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import requests
import datetime
import csv
import sqlite3


# Ano atual
ano_atual = str(datetime.date.today().year)


# Configurações do Chrome
def configure_chrome_headless():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    return webdriver.Chrome(options=chrome_options)


# Download e parse do CSV
def download_and_parse_csv(csv_url):
    response = requests.get(csv_url)
    csv_data = response.text
    csv_reader = csv.reader(csv_data.splitlines(), delimiter=',')
    # next(csv_reader)  # Pular cabeçalho
    rows = list(csv_reader)
    return rows


# Conectar e salvar no SQLite
def save_to_sqlite(data, year):
    conn = sqlite3.connect('platform_share.db')
    cur = conn.cursor()

    # Obter o cabeçalho do CSV para determinar as colunas
    csv_header = data[0]

    # Criar a tabela com as colunas adequadas
    if year == ano_atual:
        table_creation_sql = (f"CREATE TABLE IF NOT EXISTS platform_share_interval_one_year ("
                              f"{csv_header[0]} DATE, {csv_header[1]} FLOAT, {csv_header[2]} FLOAT")
    else:
        table_creation_sql = (f"CREATE TABLE IF NOT EXISTS platform_share_{year} ("
                              f"{csv_header[0]} DATE, {csv_header[1]} FLOAT, {csv_header[2]} FLOAT")

    # Adicionar a coluna "tablet" se estiver presente no cabeçalho
    if "Tablet" in csv_header:
        table_creation_sql += ", tablet FLOAT"

    table_creation_sql += ")"

    try:
        cur.execute(table_creation_sql.lower())
    except sqlite3.OperationalError as e:
        print(f"Erro ao criar tabela para o ano {year}: {e}")

    # Inserir dados na tabela
    for row in data[1:]:
        try:
            if len(row) == 4:
                if year == ano_atual:
                    cur.execute(f"INSERT INTO platform_share_interval_one_year VALUES (?, ?, ?, ?)",
                                (row[0], row[1], row[2], row[3]))
                else:
                    cur.execute(f"INSERT INTO platform_share_{year} VALUES (?, ?, ?, ?)",
                                (row[0], row[1], row[2], row[3]))
            elif len(row) == 3:
                cur.execute(f"INSERT INTO platform_share_{year} VALUES (?, ?, ?)",
                            (row[0], row[1], row[2]))
        except sqlite3.OperationalError as e:
            print(f"Erro ao inserir dados para o ano {year}: {e}")

    conn.commit()
    cur.close()
    conn.close()


def main():
    driver = configure_chrome_headless()

    base_url = "https://gs.statcounter.com/platform-market-share/desktop-mobile-tablet/brazil/"
    anos = [str(ano) for ano in range(2009, datetime.date.today().year + 1)]

    for ano in anos:
        if ano == ano_atual:
            url = f"{base_url}"
        else:
            url = f"{base_url}{ano}"
        driver.get(url)

        csv_link = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.ID, 'download-csv'))
        ).find_element(By.TAG_NAME, 'a').get_attribute('href')

        print(f"Ano: {ano}, Link CSV: {csv_link}")
        data = download_and_parse_csv(csv_link)
        save_to_sqlite(data, ano)

    driver.quit()


# Executar a função principal
if __name__ == "__main__":
    main()
