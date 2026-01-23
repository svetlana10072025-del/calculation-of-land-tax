import streamlit as st
import pandas as pd
import numpy as np

st.title("Калькулятор экологических налогов (Беларусь, 2026)")

@st.cache_data
def load_sheet(sheet_name):
    try:
        return pd.read_excel("Налоги_таблицы.xlsx", sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Ошибка загрузки листа '{sheet_name}': {e}")
        st.stop()

# Загрузка данных
df_air = load_sheet("Эконалог_воздух")
df_water = load_sheet("Эконалог_сточные")
df_waste = load_sheet("Эконалог_захоронение")

# Обработка отходов: создаём понятные метки
def format_waste_label(row):
    category = row["Категории отходов"]  # ← исправлено: "Категории", а не "Категория"
    specific = row["Конкретный вид отхода"]
    if pd.isna(specific) or str(specific).strip() == "":
        return category
    else:
        return f"{specific} ({category})"

# Применяем форматирование
df_waste = df_waste.copy()
df_waste["Отображаемое название"] = df_waste.apply(format_waste_label, axis=1)

# Выбор типа налога
tax_type = st.radio(
    "Выберите вид экологического налога",
    ["Выбросы в атмосферу", "Сброс сточных вод", "Обращение с отходами"],
    index=0
)

st.markdown("---")

# === 1. Выбросы в атмосферу ===
if tax_type == "Выбросы в атмосферу":
    st.subheader("Выбросы загрязняющих веществ в атмосферный воздух")
    classes = df_air["Классы опасности выбросов"].drop_duplicates().tolist()
    selected = st.selectbox("Класс опасности выбросов", classes)
    row = df_air[df_air["Классы опасности выбросов"] == selected].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "тонн"

# === 2. Сброс сточных вод ===
elif tax_type == "Сброс сточных вод":
    st.subheader("Сброс загрязняющих веществ со сточными водами")
    options = df_water["Куда сбрасываются сточные воды"].drop_duplicates().tolist()
    selected = st.selectbox("Куда сбрасываются сточные воды?", options)
    row = df_water[df_water["Куда сбрасываются сточные воды"] == selected].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "м³"

# === 3. Обращение с отходами ===
else:
    st.subheader("Захоронение и использование отходов")
    
    actions = df_waste["Способ обращения с отходами"].drop_duplicates().tolist()
    selected_action = st.selectbox("Способ обращения с отходами", actions)
    
    filtered = df_waste[df_waste["Способ обращения с отходами"] == selected_action]
    display_options = filtered["Отображаемое название"].drop_duplicates().tolist()
    selected_display = st.selectbox("Выберите отходы", display_options)
    
    row = filtered[filtered["Отображаемое название"] == selected_display].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "тонн"

# === Расчёт ===
st.markdown("---")
quantity = st.number_input(f"Объём ({unit})", min_value=0.0, value=1.0, step=0.1)

tax_2025 = stavka_2025 * quantity
tax_2026 = stavka_2026 * quantity
growth_abs = tax_2026 - tax_2025
growth_pct = (growth_abs / tax_2025 * 100) if tax_2025 > 0 else 0

st.subheader("Результаты расчёта")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Налог 2025", f"{tax_2025:.2f} BYN")
with col2:
    st.metric("Налог 2026", f"{tax_2026:.2f} BYN")
with col3:
    st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")

with st.expander("Детали"):
    st.write(f"**Ставка 2025:** {stavka_2025} BYN/{unit}")
    st.write(f"**Ставка 2026:** {stavka_2026} BYN/{unit}")
    st.write(f"**Объём:** {quantity} {unit}")
