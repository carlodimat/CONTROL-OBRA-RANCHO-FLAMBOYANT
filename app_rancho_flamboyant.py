import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="DIMAQUINAS C.A. - RANCHO FLAMBOYANT", layout="wide", page_icon="🏗️")

# 2. DISEÑO CSS
st.markdown("""
    <style>
    .stMetric { border: 1px solid #1e3a8a; padding: 15px; border-radius: 12px; background: #f8fafc; }
    .header-box { background-color: #1e3a8a; color: white; padding: 80px 20px; border-radius: 15px; margin-bottom: 30px; text-align: center; }
    .title-text { font-weight: 900; margin: 0; text-transform: uppercase; line-height: 1.1; }

    @media (max-width: 600px) {
        .title-text { font-size: 35px !important; }
        .subtitle-text { font-size: 18px !important; }
        .header-box { padding: 40px 10px !important; }
    }
    @media (min-width: 601px) {
        .title-text { font-size: 100px; }
        .subtitle-text { font-size: 35px; }
    }
    html, body, [class*="st-"] { color: #000000; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# ─── Función para envolver texto en ejes (usando \n para Plotly) ───
def wrap_label(text, width=18):
    if not isinstance(text, str): return str(text)
    words = text.split()
    lines, current = [], []
    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) > width:
            if current: lines.append(" ".join(current))
            current = [word]
        else: current.append(word)
    if current: lines.append(" ".join(current))
    return "<br>".join(lines)

def create_pdf(df_report, title_report, totals_info=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    
    # Encabezado
    pdf.cell(190, 10, title_report, ln=True, align='C')
    pdf.set_font("helvetica", "", 10)
    pdf.cell(190, 10, f"Generado el: {pd.Timestamp.today().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    
    if totals_info:
        pdf.set_font("helvetica", "B", 10)
        pdf.multi_cell(190, 10, totals_info)
        pdf.ln(5)

    # Tabla
    pdf.set_font("helvetica", "B", 8)

    cols = [c for c in ['FECHA', 'PROVEEDOR', 'DESCRIPCION', 'MONTO ORIG', 'HONORARIOS', 'COSTO TOTAL'] if c in df_report.columns]
    widths = [20, 35, 65, 25, 20, 25]
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 8, col, border=1, align='C')
    pdf.ln()
    pdf.set_font("helvetica", "", 7)
    for _, row in df_report.iterrows():
        for i, col in enumerate(cols):
            val = str(row[col])
            if 'MONTO' in col or 'HONORARIOS' in col or 'COSTO' in col:
                try: val = f"{float(row[col]):,.2f}"
                except: pass
            elif 'FECHA' in col:
                try: val = row[col].strftime('%d/%m/%Y')
                except: pass
            
            # Sanitizar texto
            val = val.encode('latin-1', 'replace').decode('latin-1')
            
            if col == 'DESCRIPCION' and len(val) > 45: val = val[:42] + "..."
            pdf.cell(widths[i], 7, val, border=1)
        pdf.ln()
    return bytes(pdf.output())


def load_all_data():
    csv_options = ["RANCHO.csv", "DIMAQUINAS C.A._RANCHO FLAMBOYANT (3).csv", "DIMAQUINAS_C.A._RANCHO_FLAMBOYANT.csv"]
    for csv_name in csv_options:
        try:
            df = pd.read_csv(csv_name)
            df['FECHA'] = pd.to_datetime(df['FECHA'])
            cols_fin = ['MONTO BASE USD', 'MONTO PAGADO', 'HONORARIOS', 'COSTO TOTAL', '% ADMIN', 'MONTO ORIG', 'TASA']
            for col in cols_fin:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except FileNotFoundError: continue
    return None

df = load_all_data()

if df is not None:
    empresa = df['EMPRESA'].iloc[0] if 'EMPRESA' in df.columns else "DIMAQUINAS C.A."
    obra = df['OBRA'].iloc[0] if 'OBRA' in df.columns else "RANCHO FLAMBOYANT"
    df_gastos_base = df[df['CLASE'] == 'GASTO'].copy()
    df_ingresos = df[df['CLASE'] == 'INGRESO'].copy()

    st.sidebar.header("🎯 FILTROS DE OBRA")
    tipos_sel = st.sidebar.multiselect("Filtrar por TIPO:", options=sorted(df_gastos_base['TIPO'].unique()))
    areas_sel = st.sidebar.multiselect("Filtrar por AREA:", options=sorted(df_gastos_base['AREA'].unique()))
    prov_sel = st.sidebar.multiselect("Filtrar por PROVEEDOR:", options=sorted(df_gastos_base['PROVEEDOR'].unique()))

    df_gastos = df_gastos_base.copy()
    if tipos_sel: df_gastos = df_gastos[df_gastos['TIPO'].isin(tipos_sel)]
    if areas_sel: df_gastos = df_gastos[df_gastos['AREA'].isin(areas_sel)]
    if prov_sel: df_gastos = df_gastos[df_gastos['PROVEEDOR'].isin(prov_sel)]

    total_ing = df_ingresos['MONTO BASE USD'].sum()
    total_neto = df_gastos['MONTO BASE USD'].sum()
    total_honorarios = df_gastos['HONORARIOS'].sum()
    gasto_total_real = total_neto + total_honorarios

    _hon_base = df_gastos_base['HONORARIOS'].sum() if 'HONORARIOS' in df_gastos_base.columns else 0
    neto_base = df_gastos_base['MONTO BASE USD'].sum()
    gasto_base_real = neto_base + _hon_base
    saldo_base_real = total_ing - gasto_base_real

    st.markdown(f'<div class="header-box"><p class="title-text">{empresa}</p><p class="subtitle-text">OBRA: {obra}</p></div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL INGRESOS", f"$ {total_ing:,.2f}")
    m2.metric("GASTOS NETOS", f"$ {neto_base:,.2f}")
    m3.metric("ADMIN. DELEGADA", f"$ {_hon_base:,.2f}")
    m4.metric("SALDO REAL", f"$ {saldo_base_real:,.2f}")
    st.divider()

    def horizontal_bar_chart(df_plot, x_col, y_col, color_scale, title, height=500):
        if df_plot.empty: return
        df_sorted = df_plot.sort_values(x_col, ascending=True).copy()
        fig = go.Figure(go.Bar(x=df_sorted[x_col], y=df_sorted[y_col], orientation='h', marker_color=df_sorted[x_col], text=[f"$ {v:,.2f}" for v in df_sorted[x_col]], textposition='outside'))
        fig.update_layout(title=title, height=height, margin=dict(l=10, r=130, t=50, b=30), xaxis=dict(showticklabels=False, range=[0, df_sorted[x_col].max() * 1.35]))
        st.plotly_chart(fig, use_container_width=True)

    t1, t2, t3, t4 = st.tabs(["📊 GRAFICOS", "💸 EGRESOS", "💰 INGRESOS", "🔍 BUSCADOR"])

    filtro_activo = bool(tipos_sel or areas_sel or prov_sel)
    def filter_summary(df_filtrado, label_filtro):
        if filtro_activo:
            n = len(df_filtrado)
            tot = df_filtrado['MONTO BASE USD'].sum()
            st.markdown(f"<div style='background:#e8f0fe;border-left:5px solid #1e3a8a;padding:10px 16px;border-radius:6px;margin-top:4px;'>🔍 <b>Filtro activo &mdash; {label_filtro}:</b> {n} registros | Subtotal: <b>$ {tot:,.2f}</b> | Total Real: <b>$ {tot + total_honorarios:,.2f}</b></div>", unsafe_allow_html=True)

    with t1:
        st.write("### 📌 Inversión por Tipo")
        df_t = df_gastos.groupby('TIPO')['MONTO BASE USD'].sum().reset_index()
        df_t = pd.concat([df_t, pd.DataFrame({'TIPO': ['ADMINISTRACION DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_t, 'MONTO BASE USD', 'TIPO', 'Viridis', '📌 Inversión total por Tipo de Gasto', height=max(350, len(df_t)*45))
        filter_summary(df_gastos, "Tipo")
        st.divider()

        st.write("### 📐 Inversión por Área")
        df_a = df_gastos.groupby('AREA')['MONTO BASE USD'].sum().reset_index()
        df_a = pd.concat([df_a, pd.DataFrame({'AREA': ['ADMINISTRACION DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_a, 'MONTO BASE USD', 'AREA', 'Blues', '📐 Inversión total por Área de Obra', height=max(400, len(df_a)*42))
        filter_summary(df_gastos, "Área")
        st.divider()

        st.write("### 👥 Top Proveedores")
        df_p = df_gastos.groupby('PROVEEDOR')['MONTO BASE USD'].sum().sort_values(ascending=False).head(20).reset_index()
        df_p = pd.concat([df_p, pd.DataFrame({'PROVEEDOR': ['ADMINISTRACION DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_p, 'MONTO BASE USD', 'PROVEEDOR', 'Reds', '👥 Top 20 Proveedores por Gasto', height=max(500, len(df_p)*40))
        filter_summary(df_gastos, "Proveedor")
        st.divider()

        st.write("### 📅 Evolución Acumulativa")
        freq_sel = st.radio("Agrupación:", options=["📅 Mensual", "🗓️ Semanal"], horizontal=True, key="freq_time")
        freq_code = "ME" if freq_sel == "📅 Mensual" else "W"
        fecha_inicio = df_ingresos['FECHA'].min() if not df_ingresos.empty else df_gastos_base['FECHA'].min()
        fecha_hoy = pd.Timestamp.today().normalize()
        idx_full = pd.date_range(start=fecha_inicio, end=fecha_hoy, freq=freq_code)

        if not df_gastos.empty:
            df_gastos_chart = df_gastos.copy()
            hon_col = df_gastos_chart['HONORARIOS'] if 'HONORARIOS' in df_gastos_chart.columns else 0
            df_gastos_chart['_GASTO_REAL'] = df_gastos_chart['MONTO BASE USD'] + hon_col
            s_gastos = (df_gastos_chart.set_index('FECHA')['_GASTO_REAL'].resample(freq_code).sum().reindex(idx_full, fill_value=0).cumsum())
            s_ingresos = (df_ingresos.set_index('FECHA')['MONTO BASE USD'].resample(freq_code).sum().reindex(idx_full, fill_value=0).cumsum())
            df_evol = pd.DataFrame({'FECHA': idx_full, 'GASTOS': s_gastos.values, 'INGRESOS': s_ingresos.values})
            
            fig_time = go.Figure()
            fig_time.add_trace(go.Scatter(x=df_evol['FECHA'], y=df_evol['INGRESOS'], name='Ingresos Acum.', mode='lines', fill='tozeroy', line=dict(color='#22c55e')))
            fig_time.add_trace(go.Scatter(x=df_evol['FECHA'], y=df_evol['GASTOS'], name='Gastos Acum.', mode='lines', fill='tozeroy', line=dict(color='#1e3a8a')))
            fig_time.update_layout(height=420, hovermode='x unified', margin=dict(l=10, r=20, t=40, b=30))
            st.plotly_chart(fig_time, use_container_width=True)

            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Ingresos Totales", f"$ {total_ing:,.2f}")
            b2.metric("Gastos Netos", f"$ {neto_base:,.2f}")
            b3.metric("Admin. Delegada", f"$ {_hon_base:,.2f}")
            b4.metric("Saldo Real", f"$ {saldo_base_real:,.2f}")

    with t2:
        st.subheader("📝 Detalle de Gastos")
        st.info(f"📋 **{len(df_gastos)}** movimientos - Total Neto: **$ {total_neto:,.2f}**")
        cols_show = [c for c in ['FECHA', 'TIPO', 'AREA', 'PROVEEDOR', 'DESCRIPCION', 'MONTO ORIG', '% ADMIN', 'HONORARIOS', 'COSTO TOTAL'] if c in df_gastos.columns]
        fmt = {c: "${:,.2f}" for c in ['HONORARIOS', 'COSTO TOTAL', 'MONTO BASE USD'] if c in cols_show}
        fmt.update({c: "{:,.2f}" for c in ['MONTO ORIG', '% ADMIN'] if c in cols_show})
        st.dataframe(df_gastos[cols_show].sort_values('FECHA', ascending=False).style.format(fmt), use_container_width=True)
        
        pdf_data = create_pdf(df_gastos.sort_values('FECHA', ascending=False), f"REPORTE DE EGRESOS - {obra}", f"Total Real: $ {gasto_total_real:,.2f}")
        st.download_button(label="📄 Descargar Egresos en PDF", data=pdf_data, file_name=f"Egresos_{obra}.pdf", mime="application/pdf")

    with t3:
        st.subheader("💰 Detalle de Ingresos")
        st.success(f"💵 **{len(df_ingresos)}** ingresos - Total: **$ {total_ing:,.2f}**")
        st.dataframe(df_ingresos[['FECHA', 'PROVEEDOR', 'MONTO BASE USD']].sort_values('FECHA', ascending=False).style.format({"MONTO BASE USD": "${:,.2f}"}), use_container_width=True)
        pdf_ing = create_pdf(df_ingresos.sort_values('FECHA', ascending=False), f"REPORTE DE INGRESOS - {obra}", f"Total Ingresos: $ {total_ing:,.2f}")
        st.download_button(label="📄 Descargar Ingresos en PDF", data=pdf_ing, file_name=f"Ingresos_{obra}.pdf", mime="application/pdf")

    with t4:
        st.subheader("🔍 Buscador por Descripción")
        q = st.text_input("Escriba una palabra para buscar:")
        if q:
            import re
            mask = df['DESCRIPCION'].astype(str).str.contains(re.escape(q), case=False)
            res = df[mask]
            s_orig = res['MONTO ORIG'].sum() if 'MONTO ORIG' in res.columns else 0
            s_hon = res['HONORARIOS'].sum() if 'HONORARIOS' in res.columns else 0
            s_total = res['COSTO TOTAL'].sum() if 'COSTO TOTAL' in res.columns else 0
            st.success(f"🔍 **{len(res)}** registros encontrados\n\n💰 Neto: **{s_orig:,.2f}** | Admin: **$ {s_hon:,.2f}** | Total: **$ {s_total:,.2f}**")
            st.dataframe(res[cols_show].sort_values('FECHA', ascending=False).style.format(fmt), use_container_width=True)
