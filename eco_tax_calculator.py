import streamlit as st
import pandas as pd

st.title("🔍 Тест загрузки Excel")

try:
    df = pd.read_excel("Налоги_таблицы.xlsx", sheet_name="Эконалог_захоронение")
    st.write("✅ Лист 'Эконалог_захоронение' загружен")
    st.write("Колонки:", df.columns.tolist())
    st.write("Первые 3 строки:")
    st.write(df.head(3))
except Exception as e:
    st.error(f"Ошибка: {e}")
