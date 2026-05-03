import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página
st.set_page_config(page_title="Control de Obra - Rancho Flamboyant", layout="wide")
st.title('🏗️ Control de Obra: Rancho Flamboyant')
st.subheader('DIMAQUINAS C.A.')

# Función para cargar datos
@st.cache_data
def load_data():
    # Cargamos el CSV (Streamlit lo buscará en tu repositorio de GitHub)
    df = pd.read_csv("RANCHO.csv")
    
    # Convertimos la fecha a formato datetime
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    
    # Aseguramos que los montos sean numéricos
    cols_num = ['MONTO BASE USD', 'MONTO PAGADO', 'SALDO PENDIENTE', 'COSTO TOTAL']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df = load_data()

# --- MÉTRICAS PRINCIPALES ---
ingresos = df[df['CLASE'] == 'INGRESO']['MONTO BASE USD'].sum()
egresos = df[df['CLASE'] == 'EGRESO']['MONTO BASE USD'].sum()
balance = ingresos - egresos

m1, m2, m3 = st.columns(3)
m1.metric("Total Ingresos (USD)", f"${ingresos:,.2f}")
m2.metric("Total Egresos (USD)", f"${egresos:,.2f}")
m3.metric("Balance en Caja", f"${balance:,.2f}", delta_color="normal")

st.divider()

# --- GRÁFICAS ---
col_left, col_right = st.columns(2)

with col_left:
    # 1. Gastos por Categoría (TIPO)
    st.write("### Distribución de Egresos por Tipo")
    df_egresos = df[df['CLASE'] == 'EGRESO']
    fig1, ax1 = plt.subplots()
    df_tipo = df_egresos.groupby('TIPO')['MONTO BASE USD'].sum().sort_values()
    df_tipo.plot(kind='barh', color='salmon', ax=ax1)
    ax1.set_xlabel("Monto USD")
    ax1.set_ylabel("")
    st.pyplot(fig1)

with col_right:
    # 2. Top Proveedores
    st.write("### Top 10 Proveedores (por Monto)")
    fig2, ax2 = plt.subplots()
    df_prov = df_egresos.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(10)
    sns.barplot(x=df_prov.values, y=df_prov.index, palette='Blues_d', ax=ax2)
    ax2.set_xlabel("Monto Pagado USD")
    st.pyplot(fig2)

# --- FLUJO DE CAJA ---
st.write("### Histórico de Movimientos (Ingresos vs Egresos)")
df_time = df.groupby(['MES', 'CLASE'])['MONTO BASE USD'].sum().unstack().fillna(0)
st.line_chart(df_time)

# --- TABLA DE DATOS ---
if st.checkbox('Ver tabla de datos detallada'):
    st.write(df)