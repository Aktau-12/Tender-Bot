import json
import pandas as pd

# Читаем JSON файл
with open('tenders.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Проверяем, есть ли данные
if not data:
    print("⚠️ В файле tenders.json нет данных!")
else:
    # Делаем таблицу DataFrame
    df = pd.DataFrame(data)

    # Переименовываем колонки на понятный язык
    df.rename(columns={
        'Название': 'Название тендера',
        'Стоимость за единицу': 'Стоимость за единицу',
        'Стоимость': 'Общая стоимость',
        'Осталось дней': 'Осталось дней'
    }, inplace=True)

    # Сохраняем в Excel
    excel_file = 'tenders.xlsx'
    df.to_excel(excel_file, index=False)

    print(f"✅ Файл {excel_file} успешно создан с {len(df)} строками!")
