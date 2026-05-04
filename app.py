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
        # Intento con el nombre original detectado en el sistema
        df = pd.read_csv("DIMAQUINAS_C.A._RANCHO_FLAMBOYANT.csv")
    
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    # Limpieza exhaustiva de columnas financieras detectadas
    cols_financieras = ['MONTO ORIG', 'TASA', 'MONTO BASE USD', 'MONTO PAGADO', 'HONORARIOS', 'COSTO TOTAL']
    for col in cols_financieras:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    st.title('🏗️ Sistema de Control Integral: Rancho Flamboyant')
    st.subheader('Gestión de DIMAQUINAS C.A.')

    # 3. Cálculos de métricas generales
    df_ingresos_solo = df[df['CLASE'] == 'INGRESO']
    df_gastos_solo = df[df['CLASE'] == 'GASTO']
    
    total_ing = df_ingresos_solo['MONTO BASE USD'].sum()
    total_gas = df_gastos_solo['MONTO BASE USD'].sum()
    total_adm = df['HONORARIOS'].sum() 
    balance = total_ing - total_gas - total_adm

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Ingresos (USD)", f"${total_ing:,.2f}")
    m2.metric("Egresos (Gastos)", f"${total_gas:,.2f}")
    m3.metric("Admin. Delegada", f"${total_adm:,.2f}")
    m4.metric("Saldo Disponible", f"${balance:,.2f}")

    st.divider()

    # 4. Organización por Pestañas
    tab_graficas, tab_ingresos, tab_egresos, tab_buscador = st.tabs([
        "📊 Análisis Acumulado", 
        "💰 Listado de Ingresos", 
        "💸 Listado de Egresos", 
        "🔍 Buscador Universal"
    ])

    with tab_graficas:
        frecuencia = st.radio("Ver evolución temporal:", ["Semanal", "Mensual"], horizontal=True)
        # Ajuste de frecuencia para Pandas 2.2+
        freq_code = 'W' if frecuencia == "Semanal" else 'ME'
        
        st.write(f"### Evolución Acumulada del Flujo de Caja ({frecuencia})")
        df_flujo = df[df['CLASE'].isin(['INGRESO', 'GASTO'])].copy()
        df_time = df_flujo.groupby([pd.Grouper(key='FECHA', freq=freq_code), 'CLASE'])['MONTO BASE USD'].sum().unstack().fillna(0)
        df_acumulado = df_time.cumsum() 
        st.area_chart(df_acumulado)

        st.divider()
        col_1, col_2 = st.columns(2)
        
        with col_1:
            # Gráfica TIPO
            st.write("#### Egresos por Tipo de Partida")
            df_tipo = df_gastos_solo.groupby('TIPO')['MONTO BASE USD'].sum().sort_values()
            fig1, ax1 = plt.subplots()
            bars1 = ax1.barh(df_tipo.index, df_tipo.values, color='#ff9999')
            # CORRECCIÓN: horizontalalignment='right' reemplaza a textAlign
            ax1.bar_label(bars1, labels=[f'${x:,.2f}' for x in df_tipo.values], padding=-10, label_type='edge', fontweight='bold', fontsize=9, color='black', horizontalalignment='right')
            ax1.set_xlabel("Monto USD")
            st.pyplot(fig1)

            # Gráfica ÁREA
            st.write("#### Egresos por Área de la Obra")
            df_area = df_gastos_solo.groupby('AREA')['MONTO BASE USD'].sum().sort_values()
            fig2, ax2 = plt.subplots()
            bars2 = ax2.barh(df_area.index, df_area.values, color='#ffcc99')
            ax2.bar_label(bars2, labels=[f'${x:,.2f}' for x in df_area.values], padding=-10, label_type='edge', fontweight='bold', fontsize=9, color='black', horizontalalignment='right')
            ax2.set_xlabel("Monto USD")
            st.pyplot(fig2)

        with col_2:
            # Gráfica PROVEEDOR
            st.write("#### Top Proveedores por Monto")
            df_prov = df_gastos_solo.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(15)
            fig3, ax3 = plt.subplots(figsize=(10, 11))
            df_prov_plot = df_prov.sort_values(ascending=True)
            bars3 = ax3.barh(df_prov_plot.index, df_prov_plot.values, color='#d3d3d3')
            ax3.bar_label(bars3, labels=[f'${x:,.2f}' for x in df_prov_plot.values], padding=-10, label_type='edge', fontweight='bold', fontsize=9, color='black', horizontalalignment='right')
            ax3.set_xlabel("Monto USD")
            st.pyplot(fig3)

    with tab_ingresos:
        st.write("### Detalle de Ingresos (Bs / $)")
        listado_ing = df_ingresos_solo[['FECHA', 'PROVEEDOR', 'MONTO ORIG', 'TASA', 'MONTO BASE USD', 'FORMA DE PAGO']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_ing.style.format({
            "MONTO ORIG": "{:,.2f}", "TASA": "{:,.2f}", "MONTO BASE USD": "{:,.2f}"
        }), use_container_width=True)

    with tab_egresos:
        st.write("### Detalle Completo de Egresos")
        listado_gas = df_gastos_solo[['FECHA', 'AREA', 'TIPO', 'PROVEEDOR', 'DESCRIPCION', 'FORMA DE PAGO', 'MONTO PAGADO']].sort_values('FECHA', ascending=False)
        st.dataframe(listado_gas.style.format({"MONTO PAGADO": "{:,.2f}"}), use_container_width=True)

    with tab_buscador:
        st.write("### 🔍 Buscador Universal")
        texto_buscar = st.text_input("Filtrar por cualquier palabra:")
        if texto_buscar:
            mask = df.apply(lambda row: row.astype(str).str.contains(texto_buscar, case=False, na=False).any(), axis=1)
            df_busqueda_raw = df[mask].copy()
            suma_pagado = df_busqueda_raw['MONTO PAGADO'].sum()
            st.success(f"**Total Monto Pagado en esta búsqueda:** ${suma_pagado:,.2f}")
            columnas_visibles = ['FECHA', 'CLASE', 'AREA', 'TIPO', 'PROVEEDOR', 'DESCRIPCION', 'FORMA DE PAGO', 'MONTO PAGADO']
            cols_finales = [c for c in columnas_visibles if c in df_busqueda_raw.columns]
            st.dataframe(df_busqueda_raw[cols_finales].style.format({"MONTO PAGADO": "{:,.2f}"}), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
