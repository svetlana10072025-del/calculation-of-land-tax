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

st.title("Калькулятор акцизов (Беларусь, 2025–2026)")

@st.cache_data
def load_data():
    return pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Акцизы")

try:
    df = load_data()
except Exception as e:
    st.error(f"Ошибка загрузки данных: {e}")
    st.stop()

# Сохраняем исходный порядок товаров
seen = set()
products = []
for val in df["Подакцизный_товар"]:
    if val not in seen:
        products.append(val)
        seen.add(val)

product = st.selectbox("Выберите подакцизный товар", products)

row = df[df["Подакцизный_товар"] == product].iloc[0]
unit = row["Единица налогообложения"]
stavka_2025 = row["Ставка_2025"]
stavka_2026 = row["Ставка_2026"]

quantity = st.number_input(f"Количество ({unit})", min_value=0.0, value=1.0, step=0.1)

tax_2025 = stavka_2025 * quantity
tax_2026 = stavka_2026 * quantity
growth_abs = tax_2026 - tax_2025
growth_pct = (growth_abs / tax_2025 * 100) if tax_2025 > 0 else 0

st.subheader("Результаты расчёта")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Акциз 2025", f"{tax_2025:.2f} BYN")
with col2:
    st.metric("Акциз 2026", f"{tax_2026:.2f} BYN")
with col3:
    st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")

with st.expander("Детали"):
    st.write(f"**Ставка 2025:** {stavka_2025} BYN/{unit}")
    st.write(f"**Ставка 2026:** {stavka_2026} BYN/{unit}")

    st.write(f"**Количество:** {quantity} {unit}")
