import streamlit as st
import pandas as pd
import altair as alt

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Nómina Enterprise", page_icon="💼", layout="wide")

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

# --- 2. CSS "ENTERPRISE" (CONTRA DARK MODE) ---
st.markdown("""
<style>
    /* 1. FORZAR FONDO CLARO EN TODA LA APP */
    .stApp {
        background-color: #f8fafc; /* Gris muy muy claro */
    }

    /* 2. FORZAR TEXTOS OSCUROS EN WIDGETS DE STREAMLIT (Inputs, Selectbox, etc) */
    /* Esto arregla que las etiquetas se vean blancas */
    .stSelectbox label p, .stNumberInput label p, .stDateInput label p {
        color: #334155 !important; /* Gris Oscuro */
        font-weight: 600;
    }
    
    /* Textos generales y Headers */
    h1, h2, h3, p, li {
        color: #0f172a !important; /* Casi negro */
    }
    
    /* Ajuste para el texto dentro de los inputs */
    div[data-baseweb="select"] span {
        color: #0f172a !important;
    }
    input {
        color: #0f172a !important;
    }

    /* 3. ESTILO DE TARJETAS PERSONALIZADAS */
    .pro-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* 4. MÉTRICAS DENTRO DE LAS CARDS */
    .metric-label {
        font-size: 0.85rem;
        color: #64748b !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a !important;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #94a3b8 !important;
        margin-top: 4px;
    }

    /* Colores Semánticos */
    .text-green { color: #059669 !important; }
    .text-red { color: #dc2626 !important; }
    .text-blue { color: #2563eb !important; }

    /* Ocultar índices de tablas */
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

# Header con Logo
c_head1, c_head2 = st.columns([0.5, 5])
with c_head1:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=50)
with c_head2:
    st.markdown("<h1>Nómina Enterprise 2026</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: -15px; color: #64748b;'>Sistema Profesional de Cálculo Fiscal</p>", unsafe_allow_html=True)

st.markdown("---")

# --- AREA DE INPUTS (CONTENEDOR NATIVO CON BORDE) ---
# Usamos st.container(border=True) porque respeta mejor los inputs, 
# pero le aplicamos estilos globales para que parezca nuestra "Card blanca".
with st.container(border=True):
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
        # Texto informativo protegido con HTML
        st.info(f"Salario Diario Integrado para cálculo: ${sueldo_diario:,.2f}")

    btn_calc = st.button("Generar Cálculo", type="primary", use_container_width=True)


# --- RESULTADOS ---
if btn_calc:
    
    # Lógica
    dias_vac = 14 if antig > 0 else 12
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- METRICS CARDS (HTML PURO PARA CONTROL TOTAL) ---
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">Ingreso Bruto</div>
            <div class="metric-value">&#36;{bruto:,.2f}</div>
            <div class="metric-sub">{dias_pago} días laborados</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">ISR (Impuesto)</div>
            <div class="metric-value text-red">-&#36;{isr:,.2f}</div>
            <div class="metric-sub">Tasa Efec: {(isr/bruto)*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">IMSS (Seguridad)</div>
            <div class="metric-value text-red">-&#36;{imss:,.2f}</div>
            <div class="metric-sub">SBC: &#36;{sbc:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="pro-card" style="border-left: 6px solid #10b981;">
            <div class="metric-label text-green">Neto a Pagar</div>
            <div class="metric-value text-green">&#36;{neto:,.2f}</div>
            <div class="metric-sub">Disponible</div>
        </div>
        """, unsafe_allow_html=True)

    # --- TABS DE DETALLE ---
    
    tab_vis, tab_isr, tab_imss = st.tabs(["📊 Análisis Visual", "🏛️ Auditoría ISR", "🏥 Auditoría IMSS"])
    
    with tab_vis:
        c1, c2 = st.columns([1, 2])
        with c1:
            source = pd.DataFrame({"Concepto": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#10b981', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", alt.Tooltip("Monto", format="$,.2f")]
            )
            st.altair_chart(pie, use_container_width=True)
        with c2:
            st.markdown("#### Distribución de Nómina")
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;">
                <ul style="margin: 0; padding-left: 20px; line-height: 2;">
                    <li><b>Sueldo Bruto:</b> &#36;{bruto:,.2f}</li>
                    <li style="color: #dc2626;"><b>Deducciones Totales:</b> -&#36;{isr+imss:,.2f}</li>
                    <li style="color: #059669; font-weight: bold; font-size: 1.1em;"><b>Neto Recibido:</b> &#36;{neto:,.2f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab_isr:
        # Preparamos datos para tabla
        data = [
            {"Concepto": "1. Base Gravable Mensual", "Valor": df_isr_raw["Base Mensual"]},
            {"Concepto": "2. Límite Inferior", "Valor": df_isr_raw["Límite Inferior"]},
            {"Concepto": "3. Excedente", "Valor": df_isr_raw["Excedente"]},
            {"Concepto": "4. Tasa %", "Valor": df_isr_raw["Tasa"]},
            {"Concepto": "5. Impuesto Marginal", "Valor": df_isr_raw["Marginal"]},
            {"Concepto": "6. Cuota Fija", "Valor": df_isr_raw["Cuota Fija"]},
            {"Concepto": "7. ISR Mensual", "Valor": df_isr_raw["ISR Mes"]},
            {"Concepto": f"8. Factor ({periodo})", "Valor": df_isr_raw["Factor"]},
            {"Concepto": "9. RETENCIÓN ISR", "Valor": isr},
        ]
        df = pd.DataFrame(data)
        
        # Formateador
        def fmt(x, c):
            if "Tasa" in c: return f"{x*100:.2f}%"
            if "Factor" in c: return f"{x:.4f}"
            return f"${x:,.2f}"
            
        df["Valor"] = df.apply(lambda x: fmt(x["Valor"], x["Concepto"]), axis=1)
        
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_imss:
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        total = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
        df_final = pd.concat([df_imss, total], ignore_index=True)
        st.dataframe(df_final.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
