import streamlit as st
import pandas as pd
import time

# Получаем параметры URL
query_params = st.experimental_get_query_params()

# Проверяем, это запрос для прогрева
if "_warmup" in query_params:
    # Минимальный ответ для прогрева
    st.write("OK")
    
    # Небольшая пауза, чтобы убедиться, что приложение запущено
    time.sleep(1)
    
    # Останавливаем дальнейшее выполнение
    st.stop()

st.title("Калькулятор налога за добычу нефти (Беларусь, 2026)")

# Загрузка данных
try:
    df = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Ставки на нефть")
except Exception as e:
    st.error(f"Не удалось загрузить файл: {e}")
    st.stop()

# Очистка названий колонок от пробелов и лишних символов
df.columns = df.columns.str.strip()

# Автоматическое определение колонок по ключевым словам
price_col = None
rate25_col = None
rate26_col = None

for col in df.columns:
    if "Средняя цена" in col and "$" in col:
        price_col = col
    elif "Ставка_2025" in col and "BYN" in col:
        rate25_col = col
    elif "Ставка_2026" in col and "BYN" in col:
        rate26_col = col

if not all([price_col, rate25_col, rate26_col]):
    st.error("Не найдены необходимые колонки. Проверьте лист 'Ставки на нефть'.")
    st.stop()

# Преобразуем ставки в числа (на случай, если Excel сохранил как текст)
df[rate25_col] = pd.to_numeric(df[rate25_col], errors='coerce')
df[rate26_col] = pd.to_numeric(df[rate26_col], errors='coerce')

# Удаляем строки с ошибками
df = df.dropna(subset=[rate25_col, rate26_col])

# Выбор диапазона цены
price_ranges = df[price_col].astype(str).tolist()
selected_index = st.selectbox(
    "Выберите ценовой диапазон (средняя цена за 1000 кг нефти, $)",
    range(len(price_ranges)),
    format_func=lambda i: price_ranges[i]
)

row = df.iloc[selected_index]
stavka_2025 = float(row[rate25_col])
stavka_2026 = float(row[rate26_col])
price_range_label = row[price_col]

# Расчёт роста (даже если он есть в Excel — пересчитываем для надёжности)
growth_pct = ((stavka_2026 - stavka_2025) / stavka_2025 * 100) if stavka_2025 != 0 else 0

# Ввод объёма нефти (в тоннах или 1000 кг)
quantity = st.number_input(
    "Объём нефти (в тоннах = 1000 кг)",
    min_value=0.0,
    value=1.0,
    step=0.1,
    help="Акциз рассчитывается за каждую тонну (1000 кг) нефти"
)

# Расчёт налога
tax_2025 = stavka_2025 * quantity
tax_2026 = stavka_2026 * quantity
growth_abs = tax_2026 - tax_2025

# Вывод результатов
st.subheader("Результаты расчёта")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ставка 2025", f"{tax_2025:.2f} BYN")
with col2:
    st.metric("Ставка 2026", f"{tax_2026:.2f} BYN")
with col3:
    st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")

with st.expander("Детали"):
    st.write(f"**Ценовой диапазон:** {price_range_label}")
    st.write(f"**Ставка 2025:** {stavka_2025} BYN/тонну")
    st.write(f"**Ставка 2026:** {stavka_2026} BYN/тонну")

    st.write(f"**Объём:** {quantity} тонн")
