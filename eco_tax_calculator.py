import streamlit as st
import pandas as pd
import re

def parse_rate(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r'[^\d\-\.]', '', value.replace(',', '.'))
        if not cleaned or cleaned in ['.', '-', '.-', '-.']:
            return None
        try:
            return float(cleaned)
        except:
            return None
    return None

st.title("Калькулятор экологических налогов (Беларусь, 2026)")

# Загрузка
df_air = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_воздух")
df_water = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_сточные")
df_waste = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_захоронение")

# Очистка колонок
df_air.columns = df_air.columns.str.strip()
df_water.columns = df_water.columns.str.strip()
df_waste.columns = df_waste.columns.str.strip()

# Обработка отходов
df_waste["Конкретный вид отхода"] = df_waste["Конкретный вид отхода"].fillna("")
def format_waste_label(row):
    cat = row["Категории отходов"]
    spec = row["Конкретный вид отхода"]
    return cat if spec == "" else f"{spec} ({cat})"
df_waste["Отображаемое название"] = df_waste.apply(format_waste_label, axis=1)

# Выбор типа
tax_type = st.radio("Выберите вид экологического налога", 
                   ["Выбросы в атмосферу", "Сброс сточных вод", "Обращение с отходами"])

st.markdown("---")

if tax_type == "Выбросы в атмосферу":
    st.subheader("Выбросы...")
    selected = st.selectbox("Класс...", df_air["Классы опасности выбросов"].unique())
    row = df_air[df_air["Классы опасности выбросов"] == selected].iloc[0]

elif tax_type == "Сброс сточных вод":
    st.subheader("Сброс...")
    col = "Куда сбрасываются сточные воды"
    selected = st.selectbox("Куда...", df_water[col].unique())
    row = df_water[df_water[col] == selected].iloc[0]

else:
    st.subheader("Отходы...")
    action = st.selectbox("Способ...", df_waste["Способ обращения с отходами"].unique())
    filtered = df_waste[df_waste["Способ обращения с отходами"] == action]
    display = st.selectbox("Отходы...", filtered["Отображаемое название"].unique())
    row = filtered[filtered["Отображаемое название"] == display].iloc[0]

# Парсинг ставок
stavka_2025 = parse_rate(row["Ставка_2025"])
stavka_2026 = parse_rate(row["Ставка_2026"])

if stavka_2025 is None or stavka_2026 is None:
    st.error("Не удалось прочитать ставки. Проверьте Excel.")
    st.stop()

unit = "тонн" if tax_type != "Сброс сточных вод" else "м³"
quantity = st.number_input(f"Объём ({unit})", min_value=0.0, value=1.0, step=0.1)

tax_2025 = stavka_2025 * quantity
tax_2026 = stavka_2026 * quantity
growth_abs = tax_2026 - tax_2025
growth_pct = (growth_abs / tax_2025 * 100) if tax_2025 > 0 else 0

st.subheader("Результаты")
col1, col2, col3 = st.columns(3)
with col1: st.metric("Налог 2025", f"{tax_2025:.2f} BYN")
with col2: st.metric("Налог 2026", f"{tax_2026:.2f} BYN")
with col3: st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")
