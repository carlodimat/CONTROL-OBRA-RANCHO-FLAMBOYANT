import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# ─── Función para envolver texto en ejes (usando <br> para Plotly) ───
def wrap_label(text, width=18):
    """Divide etiquetas largas en múltiples líneas para los ejes de Plotly."""
    if not isinstance(text, str):
        return str(text)
    words = text.split()
    lines, current = [], []
    for word in words:
        if sum(len(w) for w in current) + len(current) + len(word) > width:
            if current:
                lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "<br>".join(lines)

def create_excel(df_report):
    """Genera un archivo Excel en memoria."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_report.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

def load_all_data():
    """Busca y carga los datos de Rancho Flamboyant."""
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
        except FileNotFoundError:
            continue
        except Exception as e:
            st.error(f"Error cargando {csv_name}: {e}")
            continue
    return None

df = load_all_data()

if df is not None:
    # --- VARIABLES INICIALES ---
    empresa = df['EMPRESA'].iloc[0] if 'EMPRESA' in df.columns else "DIMAQUINAS C.A."
    obra    = df['OBRA'].iloc[0]    if 'OBRA'    in df.columns else "RANCHO FLAMBOYANT"
    
    df_gastos_base = df[df['CLASE'] == 'GASTO'].copy()
    df_ingresos    = df[df['CLASE'] == 'INGRESO'].copy()

    # --- BARRA LATERAL DE FILTROS ---
    st.sidebar.header("🎯 FILTROS DE OBRA")
    tipos_sel = st.sidebar.multiselect("Filtrar por TIPO:",      options=sorted(df_gastos_base['TIPO'].unique()))
    areas_sel = st.sidebar.multiselect("Filtrar por ÁREA:",      options=sorted(df_gastos_base['AREA'].unique()))
    prov_sel  = st.sidebar.multiselect("Filtrar por PROVEEDOR:", options=sorted(df_gastos_base['PROVEEDOR'].unique()))

    # Determinar si hay algún filtro activo
    filtro_activo = bool(tipos_sel or areas_sel or prov_sel)

    # Aplicar filtros
    df_gastos = df_gastos_base.copy()
    if tipos_sel: df_gastos = df_gastos[df_gastos['TIPO'].isin(tipos_sel)]
    if areas_sel: df_gastos = df_gastos[df_gastos['AREA'].isin(areas_sel)]
    if prov_sel:  df_gastos = df_gastos[df_gastos['PROVEEDOR'].isin(prov_sel)]

    # --- CÁLCULOS ---
    total_ing        = df_ingresos['MONTO BASE USD'].sum()
    total_neto       = df_gastos['MONTO BASE USD'].sum()
    total_honorarios = df_gastos['HONORARIOS'].sum()
    gasto_total_real = total_neto + total_honorarios

    # Totales REALES sin filtrar para las métricas de arriba
    _hon_base       = df_gastos_base['HONORARIOS'].sum() if 'HONORARIOS' in df_gastos_base.columns else 0
    neto_base       = df_gastos_base['MONTO BASE USD'].sum()
    gasto_base_real = neto_base + _hon_base
    saldo_base_real = total_ing - gasto_base_real

    # --- ENCABEZADO ---
    st.markdown(
        f'<div class="header-box">'
        f'<p class="title-text">{empresa}</p>'
        f'<p class="subtitle-text">OBRA: {obra}</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # --- MÉTRICAS (Totales del proyecto completo) ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL INGRESOS",   f"$ {total_ing:,.2f}")
    m2.metric("GASTOS NETOS",     f"$ {neto_base:,.2f}")
    m3.metric("ADMIN. DELEGADA",  f"$ {_hon_base:,.2f}")
    m4.metric("SALDO REAL",       f"$ {saldo_base_real:,.2f}")

    st.divider()

    # --- RESUMEN GLOBAL DE FILTROS ---
    if filtro_activo:
        # Construir etiqueta de qué se está filtrando
        filtros_desc = []
        if tipos_sel: filtros_desc.append(f"Tipos: {', '.join(tipos_sel)}")
        if areas_sel: filtros_desc.append(f"Áreas: {', '.join(areas_sel)}")
        if prov_sel:  filtros_desc.append(f"Proveedores: {', '.join(prov_sel)}")
        
        lbl_filtros = " | ".join(filtros_desc)
        
        st.markdown(
            f"""<div style='background:#eff6ff; border: 2px solid #1e3a8a; padding: 20px; border-radius: 15px; margin-bottom: 25px;'>
                <h3 style='margin-top:0; color:#1e3a8a; font-size: 1.2rem;'>🔍 RESUMEN DE SELECCIÓN</h3>
                <p style='margin-bottom:8px; font-size: 0.9rem; color: #1e40af;'><b>Filtrado por:</b> {lbl_filtros}</p>
                <div style='display: flex; gap: 20px; flex-wrap: wrap;'>
                    <div style='background:white; padding: 10px 20px; border-radius: 10px; border: 1px solid #bfdbfe;'>
                        <span style='font-size: 0.8rem; color: #64748b; text-transform: uppercase;'>Registros</span><br>
                        <span style='font-size: 1.3rem; font-weight: 900; color: #1e3a8a;'>{len(df_gastos)}</span>
                    </div>
                    <div style='background:white; padding: 10px 20px; border-radius: 10px; border: 1px solid #bfdbfe;'>
                        <span style='font-size: 0.8rem; color: #64748b; text-transform: uppercase;'>Subtotal Neto</span><br>
                        <span style='font-size: 1.3rem; font-weight: 900; color: #1e3a8a;'>$ {total_neto:,.2f}</span>
                    </div>
                    <div style='background:white; padding: 10px 20px; border-radius: 10px; border: 1px solid #bfdbfe;'>
                        <span style='font-size: 0.8rem; color: #64748b; text-transform: uppercase;'>Admin. Delegada</span><br>
                        <span style='font-size: 1.3rem; font-weight: 900; color: #1e3a8a;'>$ {total_honorarios:,.2f}</span>
                    </div>
                    <div style='background:white; padding: 10px 20px; border-radius: 10px; border: 1px solid #bfdbfe;'>
                        <span style='font-size: 0.8rem; color: #64748b; text-transform: uppercase;'>TOTAL REAL FILTRADO</span><br>
                        <span style='font-size: 1.5rem; font-weight: 900; color: #1e3a8a;'>$ {gasto_total_real:,.2f}</span>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True
        )

    # ──────────────────────────────────────────────────────────
    # FUNCIÓN UNIFICADA PARA GRÁFICOS DE BARRAS HORIZONTALES
    # ──────────────────────────────────────────────────────────
    def horizontal_bar_chart(df_plot, x_col, y_col, color_scale, title, height=500):
        if df_plot.empty:
            st.info("No hay datos para este gráfico con los filtros actuales.")
            return

        df_sorted = df_plot.sort_values(x_col, ascending=True).copy()
        labels = [f"$ {v:,.2f}" for v in df_sorted[x_col]]

        # Colores
        vals = df_sorted[x_col].values
        max_v = vals.max() if vals.max() > 0 else 1
        norm  = vals / max_v

        import plotly.colors as pc
        palette = pc.get_colorscale(color_scale)
        bar_colors = pc.sample_colorscale(palette, norm)

        fig = go.Figure(go.Bar(
            x           = df_sorted[x_col],
            y           = df_sorted[y_col],
            orientation = 'h',
            marker_color= bar_colors,
            text        = labels,
            textposition= 'outside',
            textfont    = dict(size=11, color='#1e3a8a', family='Arial Black'),
            cliponaxis  = False,
        ))

        fig.update_layout(
            title       = dict(text=title, font=dict(size=14, color='#1e3a8a'), x=0.01),
            height      = height,
            margin      = dict(l=10, r=130, t=50, b=30),
            xaxis       = dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, max_v * 1.35]),
            yaxis       = dict(tickfont=dict(size=11, color='#000000'), showgrid=False),
            plot_bgcolor  = '#f8fafc',
            paper_bgcolor = '#ffffff',
            showlegend    = False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ──────────────────────────────────────────────────────────
    # TABS
    # ──────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["📊 GRÁFICOS", "💸 EGRESOS", "💰 INGRESOS", "🔍 BUSCADOR"])

    def filter_summary(df_filtrado, label_filtro):
        if filtro_activo:
            n   = len(df_filtrado)
            tot = df_filtrado['MONTO BASE USD'].sum()
            st.markdown(
                f"<div style='background:#e8f0fe;border-left:5px solid #1e3a8a;padding:10px 16px;border-radius:6px;margin-top:4px;'>🔍 <b>Filtro activo — {label_filtro}:</b> {n} registros | Subtotal neto: <b>$ {tot:,.2f}</b> | Total real: <b>$ {tot + total_honorarios:,.2f}</b></div>",
                unsafe_allow_html=True
            )

    with t1:
        st.write("### 📌 Inversión por Tipo")
        df_t = df_gastos.groupby('TIPO')['MONTO BASE USD'].sum().reset_index()
        df_t = pd.concat([df_t, pd.DataFrame({'TIPO': ['ADMINISTRACIÓN DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_t, 'MONTO BASE USD', 'TIPO', 'Viridis', '📌 Inversión total por Tipo de Gasto', height=max(350, len(df_t) * 45))
        filter_summary(df_gastos, "Tipo")

        st.divider()

        # ── 2. Por ÁREA ──────────────────────────────────────
        st.write("### 📐 Inversión por Área")
        df_a = df_gastos.groupby('AREA')['MONTO BASE USD'].sum().reset_index()
        df_a = pd.concat([df_a, pd.DataFrame({'AREA': ['ADMINISTRACIÓN DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_a, 'MONTO BASE USD', 'AREA', 'Blues', '📐 Inversión total por Área de Obra', height=max(400, len(df_a) * 42))
        filter_summary(df_gastos, "Área")

        st.divider()

        # ── 3. Top Proveedores ────────────────────────────────
        st.write("### 👥 Top Proveedores")
        df_p = (df_gastos.groupby('PROVEEDOR')['MONTO BASE USD']
                .sum().sort_values(ascending=False).head(20).reset_index())
        df_p = pd.concat([df_p, pd.DataFrame({'PROVEEDOR': ['ADMINISTRACIÓN DELEGADA'], 'MONTO BASE USD': [total_honorarios]})], ignore_index=True)
        horizontal_bar_chart(df_p, 'MONTO BASE USD', 'PROVEEDOR', 'Reds', '👥 Top 20 Proveedores por Gasto', height=max(500, len(df_p) * 40))
        filter_summary(df_gastos, "Proveedor")

        st.divider()

        # ── 4. Evolución acumulativa ─────────────
        st.write("### 📅 Evolución Acumulativa")
        freq_sel = st.radio("Agrupación:", options=["📅 Mensual", "🗓️ Semanal"], horizontal=True, key="freq_time")
        freq_code = "ME" if freq_sel == "📅 Mensual" else "W"

        if not df_ingresos.empty:
            fecha_inicio = df_ingresos['FECHA'].min()
        else:
            fecha_inicio = df_gastos_base['FECHA'].min()
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
            
            fig_time.update_layout(height=420, hovermode='x unified', margin=dict(l=10, r=20, t=40, b=30), plot_bgcolor='#f8fafc', paper_bgcolor='#ffffff')
            st.plotly_chart(fig_time, use_container_width=True)

            # Mini resumen debajo del gráfico
            color_sal_base = "🟢" if saldo_base_real >= 0 else "🔴"
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Ingresos Totales",   f"$ {total_ing:,.2f}")
            b2.metric("Gastos Netos",       f"$ {neto_base:,.2f}")
            b3.metric("Admin. Delegada",    f"$ {_hon_base:,.2f}")
            b4.metric(f"{color_sal_base} Saldo Real", f"$ {saldo_base_real:,.2f}")
            if filtro_activo:
                st.caption("⚠️ Valores del proyecto completo (sin filtros).")

    with t2:
        st.subheader("📝 Detalle de Gastos")
        
        # Resumen rápido para la tabla de egresos
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registros", f"{len(df_gastos)}")
        c2.metric("Total Neto", f"$ {total_neto:,.2f}")
        c3.metric("Admin. Delegada", f"$ {total_honorarios:,.2f}")
        c4.metric("TOTAL FILTRADO", f"$ {gasto_total_real:,.2f}")
        
        st.divider()
        
        cols_show = [c for c in ['FECHA', 'TIPO', 'AREA', 'PROVEEDOR', 'DESCRIPCION', 'MONTO ORIG', '% ADMIN', 'HONORARIOS', 'COSTO TOTAL'] if c in df_gastos.columns]
        fmt = {c: "${:,.2f}" for c in ['HONORARIOS', 'COSTO TOTAL', 'MONTO BASE USD'] if c in cols_show}
        fmt.update({c: "{:,.2f}" for c in ['MONTO ORIG', '% ADMIN'] if c in cols_show})
        
        st.dataframe(df_gastos[cols_show].sort_values('FECHA', ascending=False).style.format(fmt), use_container_width=True)
        
        excel_data = create_excel(df_gastos[cols_show].sort_values('FECHA', ascending=False))
        st.download_button(label="📊 Descargar Reporte Egresos (Excel)", data=excel_data, file_name=f"Egresos_{obra}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with t3:
        st.subheader("💰 Detalle de Ingresos")
        cols_ing = [c for c in ['FECHA', 'PROVEEDOR', 'MONTO BASE USD'] if c in df_ingresos.columns]
        st.dataframe(df_ingresos[cols_ing].sort_values('FECHA', ascending=False).style.format({"MONTO BASE USD": "${:,.2f}"}), use_container_width=True)

    with t4:
        st.subheader("🔍 Buscador por Descripción")
        q = st.text_input("📝 Escriba una palabra para buscar:")
        if q:
            import re
            mask = df['DESCRIPCION'].astype(str).str.contains(re.escape(q), case=False)
            res = df[mask]
            s_total = res['COSTO TOTAL'].sum() if 'COSTO TOTAL' in res.columns else 0
            st.success(f"🔍 **{len(res)}** registros encontrados | Total: **$ {s_total:,.2f}**")
            st.dataframe(res[cols_show].sort_values('FECHA', ascending=False).style.format(fmt), use_container_width=True)

else:
    st.error("❌ No se encontraron los archivos CSV. Verifica que 'RANCHO.csv' o similares estén en el directorio.")
