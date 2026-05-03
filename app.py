import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Configuración de la página
st.set_page_config(page_title="Control Pro Rancho Flamboyant", layout="wide")

# 2. Función para cargar datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("RANCHO.csv")
    except:
        df = pd.read_csv("DIMAQUINAS_C.A._RANCHO_FLAMBOYANT.csv")
    
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    cols_financieras = ['MONTO BASE USD', 'MONTO PAGADO', 'HONORARIOS', 'COSTO TOTAL']
    for col in cols_financieras:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    st.title('🏗️ Sistema de Control Integral: Rancho Flamboyant')
    st.subheader('Gestión de DIMAQUINAS C.A.')

    # 3. Cálculos de métricas
    df_ingresos_solo = df[df['CLASE'] == 'INGRESO']
    df_gastos_solo = df[df['CLASE'] == 'GASTO']
    
    total_ing = df_ingresos_solo['MONTO BASE USD'].sum()
    total_gas = df_gastos_solo['MONTO BASE USD'].sum()
    total_adm = df['HONORARIOS'].sum() 
    balance = total_ing - total_gas - total_adm

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Ingresos", f"${total_ing:,.2f}")
    m2.metric("Egresos (Gastos)", f"${total_gas:,.2f}")
    m3.metric("Admin. Delegada", f"${total_adm:,.2f}")
    m4.metric("Saldo Disponible", f"${balance:,.2f}")

    st.divider()

    # 4. Organización por Pestañas
    tab_graficas, tab_ingresos, tab_egresos, tab_buscador = st.tabs([
        "📊 Análisis de Egresos", 
        "💰 Listado de Ingresos", 
        "💸 Listado de Egresos", 
        "🔍 Buscador de Datos"
    ])

    with tab_graficas:
        frecuencia = st.radio("Ver evolución temporal:", ["Semanal", "Mensual"], horizontal=True)
        freq_code = 'W' if frecuencia == "Semanal" else 'ME'
        
        df_flujo = df[df['CLASE'].isin(['INGRESO', 'GASTO'])].copy()
        df_time = df_flujo.groupby([pd.Grouper(key='FECHA', freq=freq_code), 'CLASE'])['MONTO BASE USD'].sum().unstack().fillna(0)
        st.area_chart(df_time)

        st.divider()
        col_1, col_2 = st.columns(2)
        
        with col_1:
            st.write("#### Egresos por Tipo de Partida")
            df_tipo = df_gastos_solo.groupby('TIPO')['MONTO BASE USD'].sum().sort_values()
            fig1, ax1 = plt.subplots()
            bars1 = ax1.barh(df_tipo.index, df_tipo.values, color='#ff9999')
            ax1.bar_label(bars1, padding=3, fmt='$%1.0f', fontweight='bold')
            ax1.set_xlabel("Monto USD")
            st.pyplot(fig1)

            st.write("#### Egresos por Área de la Obra")
            df_area = df_gastos_solo.groupby('AREA')['MONTO BASE USD'].sum().sort_values()
            fig2, ax2 = plt.subplots()
            bars2 = ax2.barh(df_area.index, df_area.values, color='#ffcc99')
            ax2.bar_label(bars2, padding=3, fmt='$%1.0f', fontweight='bold')
            ax2.set_xlabel("Monto USD")
            st.pyplot(fig2)

        with col_2:
            st.write("#### Top Proveedores por Monto")
            df_prov = df_gastos_solo.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(15)
            fig3, ax3 = plt.subplots(figsize=(10, 11))
            bars3 = ax3.barh(df_prov.index[::-1], df_prov.values[::-1], color='#d3d3d3')
            ax3.bar_label(bars3, padding=3, fmt='$%1.0f', fontweight='bold')
            ax3.set_xlabel("Monto USD")
            st.pyplot(fig3)

    with tab_ingresos:
        st.write("### Detalle de Ingresos (Abonos)")
        # SE AÑADE 'FORMA DE PAGO'
        listado_ing = df_ingresos_solo[['FECHA', 'PROVEEDOR', 'DESCRIPCION', 'FORMA DE PAGO', 'MONTO BASE USD']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_ing, use_container_width=True)

    with tab_egresos:
        st.write("### Detalle Completo de Egresos")
        # SE AÑADE 'FORMA DE PAGO'
        listado_gas = df_gastos_solo[['FECHA', 'AREA', 'TIPO', 'PROVEEDOR', 'DESCRIPCION', 'FORMA DE PAGO', 'MONTO BASE USD']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_gas, use_container_width=True)

    with tab_buscador:
        st.write("### Buscador Global")
        texto_buscar = st.text_input("Buscar cualquier dato:")
        if texto_buscar:
            df_busqueda = df[df.apply(lambda row: texto_buscar.lower() in row.astype(str).str.lower().values, axis=1)]
            st.dataframe(df_busqueda, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
    st.error(f"Error técnico al cargar el sistema: {e}")
    st.info("Revisa que el archivo 'RANCHO.csv' esté subido correctamente a GitHub.")
