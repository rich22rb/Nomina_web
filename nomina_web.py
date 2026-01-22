import streamlit as st
import pandas as pd
import altair as alt

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="Nómina 2026 | Pro", page_icon="👔", layout="wide")

# --- 1. DATOS OFICIALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,
}

TABLA_ISR_MENSUAL = [
    {"limite": 0.01, "cuota": 0.00, "porc": 0.0192},
    {"limite": 844.60, "cuota": 16.22, "porc": 0.0640},
    {"limite": 7168.52, "cuota": 420.95, "porc": 0.1088},
    {"limite": 12598.03, "cuota": 1011.68, "porc": 0.1600},
    {"limite": 14644.65, "cuota": 1339.14, "porc": 0.1792},
    {"limite": 17533.65, "cuota": 1856.84, "porc": 0.2136},
    {"limite": 35362.84, "cuota": 5665.16, "porc": 0.2352},
    {"limite": 55736.69, "cuota": 10457.09, "porc": 0.3000},
    {"limite": 106410.51, "cuota": 25659.23, "porc": 0.3200},
    {"limite": 141880.67, "cuota": 37009.69, "porc": 0.3400},
    {"limite": 425642.00, "cuota": 133488.54, "porc": 0.3500},
]

# --- 2. CSS CORRECTIVO (FIX INPUTS & TEXTOS) ---
st.markdown("""
<style>
    /* 1. Fondo de la App */
    .stApp {
        background-color: #f1f5f9;
    }

    /* 2. FIX CRÍTICO DE INPUTS (Fondo Blanco, Texto Negro) */
    /* Input de Texto/Número */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }
    input[class] {
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: #0f172a !important;
    }
    
    /* Selectores (Dropdowns) */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }
    div[data-baseweb="select"] span {
        color: #0f172a !important;
    }
    
    /* Etiquetas de los Inputs */
    .stNumberInput label p, .stSelectbox label p, .stDateInput label p {
        color: #334155 !important;
        font-weight: 600;
        font-size: 14px;
    }

    /* 3. ESTILO DE TARJETAS (CARDS) */
    .pro-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
    }

    /* 4. TIPOGRAFÍA OSCURA GLOBAL */
    h1, h2, h3, h4, p, li, div, span {
        color: #0f172a !important; /* Azul muy oscuro (Casi negro) */
        font-family: 'Inter', sans-serif;
    }
    
    /* Métricas */
    .metric-label {
        font-size: 0.75rem;
        color: #64748b !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a !important;
        margin-top: 5px;
    }
    
    /* Colores Semánticos */
    .text-green { color: #059669 !important; }
    .text-red { color: #dc2626 !important; }
    .text-blue { color: #2563eb !important; }

    /* Ocultar índices tabla */
    thead tr th:first-child {display:none}
    tbody th {display:none}
    
</style>
""", unsafe_allow_html=True)

# --- 3. MOTORES DE CÁLCULO ---
def calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base):
    base_mensual = sueldo_diario * dias_mes_base
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    factor = dias_pago / dias_mes_base
    isr_periodo = isr_mensual * factor
    
    desglose = {
        "Base Mensual": base_mensual,
        "Límite Inferior": limite,
        "Excedente": excedente,
        "Tasa": porc,
        "Marginal": marginal,
        "Cuota Fija": cuota,
        "ISR Mes": isr_mensual,
        "Factor": factor,
        "Retención": isr_periodo
    }
    return isr_periodo, desglose

def calcular_imss_detallado(sbc, dias):
    uma = VALORES_2026["UMA"]
    exc = max(0, sbc - (3*uma))
    conceptos = {
        "Enfermedad (Exc)": exc * 0.004 * dias,
        "Prest. Dinero": sbc * 0.0025 * dias,
        "Gastos Médicos": sbc * 0.00375 * dias,
        "Invalidez y Vida": sbc * 0.00625 * dias,
        "Cesantía y Vejez": sbc * 0.01125 * dias
    }
    return sum(conceptos.values()), conceptos

# --- 4. INTERFAZ ---

# Encabezado
c1, c2 = st.columns([0.5, 6])
with c1:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=55)
with c2:
    st.markdown("<h1>Nómina 2026 Enterprise</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top:-15px; color:#64748b;'>Sistema de Cálculo Fiscal Profesional</p>", unsafe_allow_html=True)

st.markdown("---")

# INPUTS EN CARD
st.markdown('<div class="pro-card">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    criterio = st.selectbox("📅 Criterio de Días", ["Comercial (30)", "Fiscal (30.4)"])
    dias_mes_base = 30.0 if "Comercial" in criterio else 30.4

with col2:
    periodo = st.selectbox("⏱️ Frecuencia", ["Quincenal", "Semanal", "Mensual"])
    if periodo == "Quincenal": dias_pago = 15
    elif periodo == "Semanal": dias_pago = 7
    else: dias_pago = dias_mes_base
    
with col3:
    tipo_ingreso = st.selectbox("💰 Tipo de Ingreso", ["Bruto Mensual", "Bruto por Periodo"])
    
with col4:
    monto_input = st.number_input(f"Monto ({tipo_ingreso})", value=20000.0, step=500.0)
    if tipo_ingreso == "Bruto Mensual":
        sueldo_diario = monto_input / dias_mes_base
    else:
        sueldo_diario = monto_input / dias_pago

# Fila 2
col5, col6 = st.columns([1, 3])
with col5:
    antig = st.number_input("🎂 Años Antigüedad", 0, 50, 0)
with col6:
    st.info(f"ℹ️ **Dato Técnico:** Salario Diario calculado: ${sueldo_diario:,.2f} | Base Mensual Integrada: ${sueldo_diario*dias_mes_base:,.2f}")

if st.button("Ejecutar Cálculo", type="primary", use_container_width=True):
    st.session_state.run = True
st.markdown('</div>', unsafe_allow_html=True)


# RESULTADOS
if "run" in st.session_state:
    
    # Cálculos
    dias_vac = 14 if antig > 0 else 12
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    # METRICAS
    st.markdown("### 📊 Resumen Financiero")
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">Ingreso Bruto</div>
            <div class="metric-value">&#36;{bruto:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">ISR (Impuesto)</div>
            <div class="metric-value text-red">-&#36;{isr:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">IMSS (Seguridad)</div>
            <div class="metric-value text-red">-&#36;{imss:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="pro-card" style="border-left: 5px solid #059669;">
            <div class="metric-label text-green">Neto a Pagar</div>
            <div class="metric-value text-green">&#36;{neto:,.2f}</div>
        </div>""", unsafe_allow_html=True)

    # TABS (AQUÍ RESTAURÉ EL ANÁLISIS)
    tab1, tab2, tab3 = st.tabs(["🧠 Análisis Visual", "🏛️ Auditoría ISR", "🏥 Auditoría IMSS"])
    
    with tab1:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        g1, g2 = st.columns([1, 2])
        
        with g1:
            # Gráfica Dona
            source = pd.DataFrame({"Concepto": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#059669', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", alt.Tooltip("Monto", format="$,.2f")]
            )
            st.altair_chart(pie, use_container_width=True)
            
        with g2:
            st.markdown("#### 💡 Insights de tu Nómina")
            st.markdown(f"""
            <ul style="line-height: 2; color:#1e293b;">
                <li><b>Eficiencia Salarial:</b> De cada &#36;1,000 pesos, te quedas con <b class="text-green">&#36;{(neto/bruto)*1000:,.2f}</b>.</li>
                <li><b>Carga Fiscal:</b> El <b class="text-blue">{(isr/bruto)*100:.1f}%</b> de tu trabajo se va en impuestos.</li>
                <li><b>Costo Social:</b> Aportas el <b class="text-red">{(imss/bruto)*100:.1f}%</b> al IMSS para tu retiro y salud.</li>
            </ul>
            """, unsafe_allow_html=True)
            st.caption("Cálculos basados en Tablas ISR 2026 (Anexo 8).")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # Tabla ISR
        data = [
            {"Concepto": "1. Base Gravable Mensual", "Valor": df_isr_raw["Base Mensual"]},
            {"Concepto": "2. Límite Inferior", "Valor": df_isr_raw["Límite Inferior"]},
            {"Concepto": "3. Excedente", "Valor": df_isr_raw["Excedente"]},
            {"Concepto": "4. Tasa Aplicable", "Valor": df_isr_raw["Tasa"]},
            {"Concepto": "5. Impuesto Marginal", "Valor": df_isr_raw["Marginal"]},
            {"Concepto": "6. Cuota Fija", "Valor": df_isr_raw["Cuota Fija"]},
            {"Concepto": "7. ISR Mensual Total", "Valor": df_isr_raw["ISR Mes"]},
            {"Concepto": f"8. Factor ({periodo})", "Valor": df_isr_raw["Factor"]},
            {"Concepto": "9. RETENCIÓN FINAL", "Valor": isr},
        ]
        df = pd.DataFrame(data)
        def fmt(x, c):
            if "Tasa" in c: return f"{x*100:.2f}%"
            if "Factor" in c: return f"{x:.4f}"
            return f"${x:,.2f}"
        df["Valor"] = df.apply(lambda x: fmt(x["Valor"], x["Concepto"]), axis=1)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        # Tabla IMSS
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        total = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
        df_final = pd.concat([df_imss, total], ignore_index=True)
        st.dataframe(df_final.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
