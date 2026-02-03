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

# === Загрузка и очистка данных (как в вашем скрипте) ===
@st.cache_data
def load_data():
    df = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Транспортный")
    df.columns = df.columns.astype(str).str.replace('\xa0', ' ').str.strip()
    df = df.dropna(how='all')
    
    for col in ["Налог_2025", "Налог_2026"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(' ', '')
            .str.replace('\xa0', '')
            .str.replace(',', '.')
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna(subset=["Налог_2025", "Налог_2026"])
    df["Рост_%"] = ((df["Налог_2026"] - df["Налог_2025"]) / df["Налог_2025"]) * 100
    return df

df = load_data()

# === Интерфейс ===
st.set_page_config(page_title="Калькулятор транспортного налога", layout="centered")
st.title("Калькулятор транспортного налога 2026")
st.markdown("Узнайте, как изменится налог для вашего парка транспортных средств")

# Выбор категории
vehicle_type = st.selectbox(
    "Выберите тип транспортного средства",
    options=df["Тип транспортных средств"].tolist()
)

# Ввод количества
count = st.number_input("Количество единиц", min_value=1, value=1, step=1)

# Расчёт
row = df[df["Тип транспортных средств"] == vehicle_type].iloc[0]
tax_2025 = row["Налог_2025"] * count
tax_2026 = row["Налог_2026"] * count
diff_abs = tax_2026 - tax_2025
diff_pct = row["Рост_%"]

# === Вывод результатов ===
st.subheader("Результат")
col1, col2 = st.columns(2)
col1.metric("Налог 2025", f"{tax_2025:,.0f} BYN")
col2.metric("Налог 2026", f"{tax_2026:,.0f} BYN")

st.metric("Разница", f"{diff_abs:,.0f} BYN", delta=f"+{diff_pct:.1f}%")


