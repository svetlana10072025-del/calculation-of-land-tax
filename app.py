import streamlit as st
import pandas as pd

# Заголовок
st.title("Калькулятор земельного налога (Беларусь, 2025–2026)")

# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Земельный налог")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Файл 'Налоги_таблицы.xlsx' не найден. Загрузите его в папку с приложением.")
    st.stop()

# Уникальные категории и классы
categories = sorted(df["Категория сельхозугодий"].unique())
classes = sorted(df["Кадастровая оценка земель (общий балл)"].unique())

# Ввод пользователя
st.subheader("Выберите параметры сельхозугодий")

col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("Категория угодий", categories)
with col2:
    klass = st.selectbox("Класс кадастровой оценки", classes)

area = st.number_input("Площадь, га", min_value=0.1, value=1.0, step=0.1)

# Поиск ставок
match = df[
    (df["Категория сельхозугодий"] == category) &
    (df["Кадастровская оценка земель (общий балл)"] == klass)
]

if match.empty:
    st.warning("Не найдено ставок для выбранной комбинации.")
else:
    row = match.iloc[0]
    stavka_2025 = row["Ставки_2025"]
    stavka_2026 = row["Ставки_2026"]
    
    tax_2025 = stavka_2025 * area
    tax_2026 = stavka_2026 * area
    growth_abs = tax_2026 - tax_2025
    growth_pct = (growth_abs / tax_2025 * 100) if tax_2025 > 0 else 0

    # Вывод результатов
    st.subheader("Результаты расчёта")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Налог 2025", f"{tax_2025:.2f} BYN")
    with col2:
        st.metric("Налог 2026", f"{tax_2026:.2f} BYN")
    with col3:
        st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")

    # Детали
    with st.expander("Детали"):
        st.write(f"**Ставка 2025:** {stavka_2025} BYN/га")
        st.write(f"**Ставка 2026:** {stavka_2026} BYN/га")
        st.write(f"**Площадь:** {area} га")