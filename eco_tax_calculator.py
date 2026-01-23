import streamlit as st
import pandas as pd

st.title("Калькулятор экологических налогов (Беларусь, 2026)")

# === Загрузка данных ===
try:
    df_air = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_воздух")
    df_water = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_сточные")
    df_waste = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_захоронение")
except Exception as e:
    st.error(f"Не удалось загрузить файл 'Налоги_таблицы.xlsx': {e}")
    st.stop()

# === Очистка названий колонок от пробелов ===
df_air.columns = df_air.columns.str.strip()
df_water.columns = df_water.columns.str.strip()
df_waste.columns = df_waste.columns.str.strip()

# === Обработка отходов: заполнение NaN и форматирование ===
# Заполняем пустые значения в "Конкретный вид отхода"
df_waste["Конкретный вид отхода"] = df_waste["Конкретный вид отхода"].fillna("")

def format_waste_label(row):
    category = row["Категории отходов"]
    specific = row["Конкретный вид отхода"]
    if specific == "":
        return category
    else:
        return f"{specific} ({category})"

df_waste["Отображаемое название"] = df_waste.apply(format_waste_label, axis=1)

# === Выбор типа налога ===
tax_type = st.radio(
    "Выберите вид экологического налога",
    ["Выбросы в атмосферу", "Сброс сточных вод", "Обращение с отходами"],
    index=0
)

st.markdown("---")

# === 1. Выбросы в атмосферу ===
if tax_type == "Выбросы в атмосферу":
    st.subheader("Выбросы загрязняющих веществ в атмосферный воздух")
    if "Классы опасности выбросов" not in df_air.columns:
        st.error("В листе 'Эконалог_воздух' отсутствует колонка 'Классы опасности выбросов'")
        st.stop()
    
    classes = df_air["Классы опасности выбросов"].dropna().unique().tolist()
    selected_class = st.selectbox("Класс опасности выбросов", classes)
    row = df_air[df_air["Классы опасности выбросов"] == selected_class].iloc[0]
    
    stavka_2025 = pd.to_numeric(row["Ставка_2025"], errors="coerce")
    stavka_2026 = pd.to_numeric(row["Ставка_2026"], errors="coerce")
    unit = "тонн"

# === 2. Сброс сточных вод ===
elif tax_type == "Сброс сточных вод":
    st.subheader("Сброс загрязняющих веществ со сточными водами")
    col_name = "Куда сбрасываются сточные воды"
    if col_name not in df_water.columns:
        st.error(f"В листе 'Эконалог_сточные' отсутствует колонка '{col_name}'")
        st.stop()
    
    options = df_water[col_name].dropna().unique().tolist()
    selected_option = st.selectbox("Куда сбрасываются сточные воды?", options)
    row = df_water[df_water[col_name] == selected_option].iloc[0]
    
    stavka_2025 = pd.to_numeric(row["Ставка_2025"], errors="coerce")
    stavka_2026 = pd.to_numeric(row["Ставка_2026"], errors="coerce")
    unit = "м³"

# === 3. Обращение с отходами ===
else:
    st.subheader("Захоронение и использование отходов")
    if "Способ обращения с отходами" not in df_waste.columns:
        st.error("В листе 'Эконалог_захоронение' отсутствует колонка 'Способ обращения с отходами'")
        st.stop()
    
    actions = df_waste["Способ обращения с отходами"].dropna().unique().tolist()
    selected_action = st.selectbox("Способ обращения с отходами", actions)
    
    filtered = df_waste[df_waste["Способ обращения с отходами"] == selected_action]
    display_options = filtered["Отображаемое название"].dropna().unique().tolist()
    selected_display = st.selectbox("Выберите отходы", display_options)
    
    row = filtered[filtered["Отображаемое название"] == selected_display].iloc[0]
    stavka_2025 = pd.to_numeric(row["Ставка_2025"], errors="coerce")
    stavka_2026 = pd.to_numeric(row["Ставка_2026"], errors="coerce")
    unit = "тонн"

# === Проверка числовых значений ===
if pd.isna(stavka_2025) or pd.isna(stavka_2026):
    st.error("Ошибка: ставка не является числом. Проверьте Excel-файл.")
    st.stop()

# === Расчёт ===
quantity = st.number_input(f"Объём ({unit})", min_value=0.0, value=1.0, step=0.1)

tax_2025 = float(stavka_2025) * quantity
tax_2026 = float(stavka_2026) * quantity
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
