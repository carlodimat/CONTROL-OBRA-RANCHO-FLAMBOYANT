import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Control Pro Rancho Flamboyant", layout="wide")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("RANCHO.csv")
    except:
        df = pd.read_csv("DIMAQUINAS_C.A._RANCHO_FLAMBOYANT.csv")
    
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    # Limpiamos todas las columnas necesarias para el cálculo
    cols_financieras = ['MONTO ORIG', 'TASA', 'MONTO BASE USD', 'MONTO PAGADO', 'HONORARIOS']
    for col in cols_financieras:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    st.title('🏗️ Sistema de Control Integral: Rancho Flamboyant')
    st.subheader('Gestión Multimoneda - DIMAQUINAS C.A.')

    # MÉTRICAS PRINCIPALES
    df_ing = df[df['CLASE'] == 'INGRESO']
    df_gas = df[df['CLASE'] == 'GASTO']
    
    total_ing = df_ing['MONTO BASE USD'].sum()
    total_gas = df_gas['MONTO BASE USD'].sum()
    total_adm = df['HONORARIOS'].sum() 
    balance = total_ing - total_gas - total_adm

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Ingresos (USD)", f"${total_ing:,.2f}")
    m2.metric("Gastos Directos (USD)", f"${total_gas:,.2f}")
    m3.metric("Admin. Delegada", f"${total_adm:,.2f}")
    m4.metric("Saldo Caja", f"${balance:,.2f}")

    st.divider()

    tab_graficas, tab_ingresos, tab_egresos, tab_buscador = st.tabs([
        "📊 Análisis", "💰 Ingresos (Bs / $)", "💸 Egresos", "🔍 Buscador"
    ])

    with tab_graficas:
        frecuencia = st.radio("Frecuencia:", ["Semanal", "Mensual"], horizontal=True)
        freq_code = 'W' if frecuencia == "Semanal" else 'ME'
        df_time = df[df['CLASE'].isin(['INGRESO', 'GASTO'])].groupby([pd.Grouper(key='FECHA', freq=freq_code), 'CLASE'])['MONTO BASE USD'].sum().unstack().fillna(0)
        st.area_chart(df_time)

        col1, col2 = st.columns(2)
        with col1:
            st.write("#### Egresos por Tipo")
            df_tipo = df_gas.groupby('TIPO')['MONTO BASE USD'].sum().sort_values()
            fig1, ax1 = plt.subplots()
            bars1 = ax1.barh(df_tipo.index, df_tipo.values, color='#ff9999')
            ax1.bar_label(bars1, padding=3, fmt='$%1,.2f', fontweight='bold')
            st.pyplot(fig1)
        with col2:
            st.write("#### Top Proveedores")
            df_prov = df_gas.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(15)
            fig3, ax3 = plt.subplots(figsize=(10, 11))
            bars3 = ax3.barh(df_prov.index[::-1], df_prov.values[::-1], color='#d3d3d3')
            ax3.bar_label(bars3, padding=3, fmt='$%1,.2f', fontweight='bold')
            st.pyplot(fig3)

    with tab_ingresos:
        st.write("### Detalle de Ingresos y Conversión de Tasa")
        # Mostramos explícitamente el cálculo de Bs a USD
        listado_ing = df_ing[['FECHA', 'PROVEEDOR', 'MONTO ORIG', 'TASA', 'MONTO BASE USD', 'FORMA DE PAGO']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_ing.style.format({
            "MONTO ORIG": "{:,.2f} Bs.",
            "TASA": "{:,.2f}",
            "MONTO BASE USD": "{:,.2f} $"
        }), use_container_width=True)

    with tab_egresos:
        st.write("### Listado de Egresos")
        listado_gas = df_gas[['FECHA', 'AREA', 'PROVEEDOR', 'DESCRIPCION', 'MONTO BASE USD', 'FORMA DE PAGO']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_gas.style.format({"MONTO BASE USD": "{:,.2f}"}), use_container_width=True)

    with tab_buscador:
        st.write("### Buscador Global")
        texto = st.text_input("Buscar dato:")
        if texto:
            df_b = df[df.apply(lambda r: texto.lower() in r.astype(str).str.lower().values, axis=1)]
            st.dataframe(df_b, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
