import streamlit as st
import pandas as pd
import re

st.title("Калькулятор налога за добычу природных ресурсов (Беларусь, 2026)")

# === Вспомогательная функция: извлечение числа из любого значения ===
def safe_parse_number(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Удаляем всё, кроме цифр, точки, минуса
        cleaned = re.sub(r'[^\d\-\.]', '', value.replace(',', '.'))
        if not cleaned or cleaned in ['.', '-', '.-', '-.']:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None

# === Загрузка данных ===
try:
    df = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Добыча_ресурсов")
except Exception as e:
    st.error(f"Не удалось загрузить файл 'Налоги_таблицы.xlsx': {e}")
    st.stop()

# Очистка названий колонок
df.columns = df.columns.str.strip()

# === Поиск нужных колонок ===
resource_col = None
rate25_col = None
rate26_col = None
unit_col = None

for col in df.columns:
    if "Природные ресурсы" in col:
        resource_col = col
    elif "Ставка_2025" in col:
        rate25_col = col
    elif "Ставка_2026" in col:
        rate26_col = col
    elif "Единица налогообложения" in col:
        unit_col = col

# Проверка наличия всех колонок
missing = []
if not resource_col: missing.append("Природные ресурсы")
if not rate25_col: missing.append("Ставка_2025")
if not rate26_col: missing.append("Ставка_2026")
if not unit_col: missing.append("Единица налогообложения")

if missing:
    st.error(f"Не найдены колонки: {', '.join(missing)}")
    st.stop()

# === Преобразование ставок в числа ===
df["Ставка_2025_clean"] = df[rate25_col].apply(safe_parse_number)
df["Ставка_2026_clean"] = df[rate26_col].apply(safe_parse_number)

# Удаление строк с некорректными ставками
df = df.dropna(subset=["Ставка_2025_clean", "Ставка_2026_clean"])

if df.empty:
    st.error("Нет корректных данных для расчёта.")
    st.stop()

# === Выбор ресурса ===
resources = df[resource_col].astype(str).tolist()
selected_idx = st.selectbox("Выберите природный ресурс", range(len(resources)), 
                           format_func=lambda i: resources[i])

row = df.iloc[selected_idx]
resource = row[resource_col]
unit = str(row[unit_col]) if pd.notna(row[unit_col]) else "единица"
stavka_2025 = row["Ставка_2025_clean"]
stavka_2026 = row["Ставка_2026_clean"]

# === Расчёт роста ===
growth_pct = ((stavka_2026 - stavka_2025) / stavka_2025 * 100) if stavka_2025 != 0 else 0

# === Ввод объёма ===
quantity = st.number_input(
    f"Объём добычи ({unit})",
    min_value=0.0,
    value=1.0,
    step=0.1
)

# === Расчёт налога ===
tax_2025 = stavka_2025 * quantity
tax_2026 = stavka_2026 * quantity
growth_abs = tax_2026 - tax_2025

# === Вывод результатов ===
st.subheader("Результаты расчёта")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Налог 2025", f"{tax_2025:.2f} BYN")
with col2:
    st.metric("Налог 2026", f"{tax_2026:.2f} BYN")
with col3:
    st.metric("Рост", f"{growth_abs:.2f} BYN", delta=f"+{growth_pct:.1f}%")

with st.expander("Детали"):
    st.write(f"**Ресурс:** {resource}")
    st.write(f"**Единица налогообложения:** {unit}")
    st.write(f"**Ставка 2025:** {stavka_2025} BYN/{unit}")
    st.write(f"**Ставка 2026:** {stavka_2026} BYN/{unit}")
    st.write(f"**Объём:** {quantity} {unit}")