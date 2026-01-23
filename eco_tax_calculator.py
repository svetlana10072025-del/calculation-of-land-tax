import streamlit as st
import pandas as pd
import re

st.title("Калькулятор экологических налогов (Беларусь, 2026)")

# === Вспомогательные функции ===

def clean_column_name(col):
    """Очищает название колонки от невидимых символов и приводит к стандартному виду"""
    if not isinstance(col, str):
        col = str(col)
    # Удаляем всё, кроме букв, цифр, пробелов и кириллицы
    clean = re.sub(r'[^\w\s\u0400-\u04FF]', '', col)
    clean = clean.strip()
    # Заменяем пробелы и спецсимволы на подчёркивания для совместимости
    clean = re.sub(r'\s+', '_', clean)
    return clean

def safe_to_numeric(series):
    """Преобразует серию в числовой формат, заменяя запятые на точки"""
    series = series.astype(str).str.replace(',', '.')
    return pd.to_numeric(series, errors='coerce')

# === Загрузка и очистка данных ===

try:
    # Загружаем все три листа
    df_air_raw = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_воздух")
    df_water_raw = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_сточные")
    df_waste_raw = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_захоронение")
except Exception as e:
    st.error(f"Не удалось загрузить Excel-файл: {e}")
    st.stop()

# Очищаем названия колонок
df_air_raw.columns = [clean_column_name(col) for col in df_air_raw.columns]
df_water_raw.columns = [clean_column_name(col) for col in df_water_raw.columns]
df_waste_raw.columns = [clean_column_name(col) for col in df_waste_raw.columns]

# Преобразуем ставки в числа
for df in [df_air_raw, df_water_raw, df_waste_raw]:
    if "Ставка_2025" in df.columns:
        df["Ставка_2025"] = safe_to_numeric(df["Ставка_2025"])
    if "Ставка_2026" in df.columns:
        df["Ставка_2026"] = safe_to_numeric(df["Ставка_2026"])

df_air = df_air_raw
df_water = df_water_raw
df_waste = df_waste_raw

# === Обработка отходов: формируем понятные названия ===
def format_waste_label(row):
    category = row.get("Категории_отходов", "") or ""
    specific = row.get("Конкретный_вид_отхода", "") or ""
    if not specific.strip():
        return category
    else:
        return f"{specific} ({category})"

# Применяем форматирование только если есть нужные колонки
if "Категории_отходов" in df_waste.columns:
    df_waste["Отображаемое_название"] = df_waste.apply(format_waste_label, axis=1)
else:
    st.error("В листе 'Эконалог_захоронение' не найдена колонка 'Категории отходов'")
    st.stop()

# === Выбор типа налога ===
tax_type = st.radio(
    "Выберите вид экологического налога",
    ["Выбросы в атмосферу", "Сброс сточных вод", "Обращение с отходами"],
    index=0
)

st.markdown("---")

# === 1. Выбросы в атмосферу ===
if tax_type == "Выбросы в атмосферу":
    if "Классы_опасности_выбросов" not in df_air.columns:
        st.error("В листе 'Эконалог_воздух' не найдена колонка 'Классы опасности выбросов'")
        st.stop()
    
    st.subheader("Выбросы загрязняющих веществ в атмосферный воздух")
    classes = df_air["Классы_опасности_выбросов"].dropna().unique().tolist()
    selected = st.selectbox("Класс опасности выбросов", classes)
    row = df_air[df_air["Классы_опасности_выбросов"] == selected].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "тонн"

# === 2. Сброс сточных вод ===
elif tax_type == "Сброс сточных вод":
    col_name = "Куда_сбрасываются_сточные_воды"
    if col_name not in df_water.columns:
        st.error(f"В листе 'Эконалог_сточные' не найдена колонка 'Куда сбрасываются сточные воды'")
        st.stop()
    
    st.subrowser("Сброс загрязняющих веществ со сточными водами")
    options = df_water[col_name].dropna().unique().tolist()
    selected = st.selectbox("Куда сбрасываются сточные воды?", options)
    row = df_water[df_water[col_name] == selected].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "м³"

# === 3. Обращение с отходами ===
else:
    if "Способ_обращения_с_отходами" not in df_waste.columns:
        st.error("В листе 'Эконалог_захоронение' не найдена колонка 'Способ обращения с отходами'")
        st.stop()
    
    st.subheader("Захоронение и использование отходов")
    actions = df_waste["Способ_обращения_с_отходами"].dropna().unique().tolist()
    selected_action = st.selectbox("Способ обращения с отходами", actions)
    
    filtered = df_waste[df_waste["Способ_обращения_с_отходами"] == selected_action]
    display_options = filtered["Отображаемое_название"].dropna().unique().tolist()
    selected_display = st.selectbox("Выберите отходы", display_options)
    
    row = filtered[filtered["Отображаемое_название"] == selected_display].iloc[0]
    stavka_2025 = row["Ставка_2025"]
    stavka_2026 = row["Ставка_2026"]
    unit = "тонн"

# === Проверка числовых значений ===
if pd.isna(stavka_2025) or pd.isna(stavka_2026):
    st.error("Ошибка: ставка не является числом. Проверьте Excel-файл.")
    st.stop()

# === Расчёт ===
st.markdown("---")
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
