import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Control de Obra - Rancho Flamboyant", layout="wide")
st.title('🏗️ Control de Obra: Rancho Flamboyant')
st.subheader('DIMAQUINAS C.A.')

@st.cache_data
def load_data():
    # Asegúrate de que este nombre sea exacto al que tienes en GitHub
    df = pd.read_csv("RANCHO.csv")
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    cols_num = ['MONTO BASE USD', 'MONTO PAGADO', 'SALDO PENDIENTE', 'COSTO TOTAL']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# --- FILTROS DE DATOS ---
# Usamos "GASTO" porque así viene en tu CSV
df_gastos = df[df['CLASE'] == 'GASTO']
df_ingresos = df[df['CLASE'] == 'INGRESO']

# --- MÉTRICAS ---
total_ingresos = df_ingresos['MONTO BASE USD'].sum()
total_gastos = df_gastos['MONTO BASE USD'].sum()
balance = total_ingresos - total_gastos

m1, m2, m3 = st.columns(3)
m1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
m2.metric("Total Gastos Realizados", f"${total_gastos:,.2f}")
m3.metric("Saldo en Caja", f"${balance:,.2f}")

st.divider()

# --- GRÁFICAS ---
col_left, col_right = st.columns(2)

with col_left:
    st.write("### Gastos por Tipo de Partida")
    if not df_gastos.empty:
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        # Agrupamos por TIPO para ver en qué se va el dinero (Permisología, Equipos, etc.)
        df_tipo = df_gastos.groupby('TIPO')['MONTO BASE USD'].sum().sort_values()
        df_tipo.plot(kind='barh', color='skyblue', ax=ax1)
        ax1.set_xlabel("Monto USD")
        ax1.set_ylabel("")
        st.pyplot(fig1)

with col_right:
    st.write("### Top 10 Proveedores")
    if not df_gastos.empty:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        df_prov = df_gastos.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(10)
        sns.barplot(x=df_prov.values, y=df_prov.index, palette='magma', ax=ax2)
        ax2.set_xlabel("Monto USD")
        st.pyplot(fig2)

# --- ANÁLISIS POR MES ---
st.write("### Flujo Mensual (Ingresos vs Gastos)")
# Filtramos solo ingresos y gastos para la gráfica de tiempo
df_flujo = df[df['CLASE'].isin(['INGRESO', 'GASTO'])]
df_mes = df_flujo.groupby(['MES', 'CLASE'])['MONTO BASE USD'].sum().unstack().fillna(0)
st.area_chart(df_mes)

if st.checkbox('Ver listado completo de gastos'):
    st.dataframe(df_gastos[['FECHA', 'TIPO', 'PROVEEDOR', 'DESCRIPCION', 'MONTO BASE USD']])