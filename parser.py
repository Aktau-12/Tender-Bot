import json
import pandas as pd
import time
import sys
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Логирование
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s %(message)s')

SITE_URL = "https://zakup.sk.kz/#/ext"
JSON_FILE = "tenders.json"
EXCEL_FILE = "tenders.xlsx"
STOP_FILE = "stop.flag"
CATEGORIES = {"товары": "CP", "услуги": "CS", "работы": "CW"}

def get_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium"  # ✅ Render: бинарник хрома
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def select_category(driver, category):
    driver.get(SITE_URL)
    time.sleep(10)
    try:
        checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"//label[contains(text(), '{category.capitalize()}')]"))
        )
        driver.execute_script("arguments[0].click();", checkbox)
        time.sleep(2)
        logging.info(f"Категория '{category}' выбрана")
        search_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Найти')]"))
        )
        driver.execute_script("arguments[0].click();", search_btn)
        logging.info("Нажата кнопка 'Найти'")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "m-found-item"))
        )
    except Exception as e:
        logging.error(f"Ошибка выбора категории: {e}")

def scrape_tenders(driver):
    tenders = []
    while True:
        if os.path.exists(STOP_FILE):
            logging.info("Получен сигнал остановки")
            break
        elements = driver.find_elements(By.CLASS_NAME, "m-found-item")
        for elem in elements:
            try:
                title = elem.find_element(By.CLASS_NAME, "m-found-item__title").text.strip()
                price = elem.find_element(By.CLASS_NAME, "m-span--dark").text.strip()
                days_left = elem.find_element(By.XPATH, ".//div[contains(@class, 'm-found-item__col')]/span/span").text.strip()
                tender = {
                    "Название": title,
                    "Стоимость": price,
                    "Осталось дней": days_left
                }
                tenders.append(tender)
                append_to_json(tender)
            except Exception as e:
                logging.warning(f"Ошибка в элементе: {e}")
        try:
            next_btn = driver.find_element(By.XPATH, "//a[@aria-label='Next']")
            if "disabled" in next_btn.get_attribute("class"):
                break
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(5)
        except:
            logging.info("Нет следующей страницы")
            break
    return tenders

def append_to_json(tender):
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except:
        data = []
    data.append(tender)
    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def save_to_excel(data):
    df = pd.DataFrame(data)
    df.to_excel(EXCEL_FILE, index=False)

def main():
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
    else:
        category = input("Выберите категорию: ").lower()
    open(JSON_FILE, "w", encoding="utf-8").write("[]")
    driver = get_driver()
    tenders = []
    try:
        select_category(driver, category)
        tenders = scrape_tenders(driver)
    except KeyboardInterrupt:
        logging.info("Остановка по Ctrl+C")
    finally:
        driver.quit()
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)
        if tenders:
            save_to_excel(tenders)
            logging.info(f"Сохранено {len(tenders)} тендеров")
        else:
            logging.info("Нет новых тендеров")

if __name__ == "__main__":
    main()
