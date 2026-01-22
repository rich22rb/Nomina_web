import streamlit as st
import pandas as pd
import altair as alt

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="Nómina 2026 | Enterprise Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATOS OFICIALES 2026 ---
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

# --- CSS "FINTECH" (FIX DE INPUTS INCLUIDO) ---
st.markdown("""
<style>
    /* 1. ESTILO GENERAL */
    [data-testid="stAppViewContainer"] {
        background-color: #f8fafc; /* Gris muy claro 'Slate-50' */
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* 2. ARREGLO DE INPUTS (La parte crítica) */
    /* Forzamos que el texto dentro de los inputs sea negro siempre */
    input[type="number"], input[type="text"], .stNumberInput input {
        color: #0f172a !important; /* Negro intenso */
        background-color: #ffffff !important;
        font-weight: 600;
        -webkit-text-fill-color: #0f172a !important;
    }
    /* El contenedor del input */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    /* Etiquetas de los inputs */
    .stNumberInput label, .stSelectbox label {
        color: #334155 !important; /* Gris oscuro */
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* 3. TARJETAS DE RESULTADOS (KPIs) */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 2rem;
        font-weight: 800;
        font-family: 'Inter', sans-serif;
    }
    .kpi-sub {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    
    /* Colores Específicos */
    .val-green { color: #059669 !important; }
    .val-red { color: #dc2626 !important; }
    .val-blue { color: #2563eb !important; }

    /* Títulos */
    h1, h2, h3 { color: #1e293b !important; font-family: 'Inter', sans-serif; }
    
    /* Tablas */
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE CÁLCULO ---
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
        "Límite Inf.": limite,
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

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=50)
    st.markdown("### Configuración de Nómina")
    
    # Bloque 1: Tiempo
    with st.container(border=True):
        criterio = st.selectbox("📅 Criterio de Días", ["Comercial (30)", "Fiscal (30.4)"])
        dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
        
        periodo = st.selectbox("⏱️ Frecuencia", ["Quincenal", "Semanal", "Mensual"])
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        else: dias_pago = dias_mes_base

    # Bloque 2: Dinero
    with st.container(border=True):
        tipo_ingreso = st.radio("💰 Ingreso Base", ["Bruto Mensual", "Por Periodo"])
        
        # AQUÍ ES DONDE ANTES NO SE VEÍA EL NÚMERO
        monto_input = st.number_input(
            "Monto del Sueldo", 
            value=20000.0, 
            step=500.0, 
            format="%.2f"
        )
        
        if tipo_ingreso == "Bruto Mensual":
            sueldo_diario = monto_input / dias_mes_base
        else:
            sueldo_diario = monto_input / dias_pago

    # Bloque 3: Antigüedad
    with st.container(border=True):
        # OTRO CAMPO QUE DABA PROBLEMAS
        antig = st.number_input("🎂 Años Antigüedad", 0, 50, 0)
        
    # Botón Principal
    st.markdown("---")
    btn_calc = st.button("🔄 Actualizar Cálculo", type="primary", use_container_width=True)
    
    st.caption(f"Salario Diario Base: ${sueldo_diario:,.2f}")


# --- PANEL PRINCIPAL (RESULTADOS) ---

# Título Principal
st.markdown("## Dashboard de Resultados 2026")
st.markdown("Resumen fiscal y financiero del periodo.")
st.markdown("---")

# CÁLCULOS (Siempre activos por defecto o al pulsar botón)
dias_vac = 14 if antig > 0 else 12
factor_int = 1 + ((15 + (dias_vac*0.25))/365)
sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

bruto = sueldo_diario * dias_pago
imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
neto = bruto - imss - isr

# 1. FILA DE TARJETAS (KPIs)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Ingreso Bruto</div>
        <div class="kpi-value">&#36;{bruto:,.2f}</div>
        <div class="kpi-sub">{dias_pago} días laborados</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">ISR (Impuesto)</div>
        <div class="kpi-value val-red">-&#36;{isr:,.2f}</div>
        <div class="kpi-sub">Tasa: {(isr/bruto)*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">IMSS (Social)</div>
        <div class="kpi-value val-red">-&#36;{imss:,.2f}</div>
        <div class="kpi-sub">SBC: &#36;{sbc:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 5px solid #059669;">
        <div class="kpi-title val-green">Neto a Pagar</div>
        <div class="kpi-value val-green">&#36;{neto:,.2f}</div>
        <div class="kpi-sub">Disponible</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. SECCIÓN DE DETALLES (TABS)
tab_main, tab_fiscal = st.tabs(["📊 Análisis Visual", "📋 Desglose Técnico"])

with tab_main:
    c_chart, c_insight = st.columns([1, 2])
    
    with c_chart:
        # Gráfica Dona Limpia
        source = pd.DataFrame({
            "Categoría": ["Neto (Tuyo)", "ISR (Gobierno)", "IMSS (Seguro)"],
            "Monto": [neto, isr, imss]
        })
        base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
        pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
            color=alt.Color("Categoría", scale=alt.Scale(domain=['Neto (Tuyo)', 'ISR (Gobierno)', 'IMSS (Seguro)'], range=['#059669', '#3b82f6', '#f59e0b'])),
            tooltip=["Categoría", alt.Tooltip("Monto", format="$,.2f")]
        )
        st.altair_chart(pie, use_container_width=True)
        
    with c_insight:
        st.markdown("#### 💡 Distribución de tu Dinero")
        # Tarjeta de Insights
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <p style="font-size: 1.1rem; line-height: 1.6;">
            De tu sueldo total, te llevas a casa el <b>{(neto/bruto)*100:.1f}%</b>. <br>
            Las deducciones suman un total de <b style="color:#dc2626;">&#36;{isr+imss:,.2f}</b> en este periodo.
            </p>
            <ul style="color: #475569;">
                <li>Por cada $100 pesos, pagas <b>${(isr/bruto)*100:.1f}</b> de ISR.</li>
                <li>Por cada $100 pesos, ahorras/pagas <b>${(imss/bruto)*100:.1f}</b> al IMSS.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab_fiscal:
    col_isr, col_imss = st.columns(2)
    
    with col_isr:
        st.markdown("##### 🏛️ Mecánica del ISR")
        data_isr = [
            {"Paso": "1. Base Mensual", "Monto": df_isr_raw["Base Mensual"]},
            {"Paso": "2. Límite Inferior", "Monto": df_isr_raw["Límite Inf."]},
            {"Paso": "3. Excedente", "Monto": df_isr_raw["Excedente"]},
            {"Paso": "4. Tasa %", "Monto": df_isr_raw["Tasa"]},
            {"Paso": "5. Marginal", "Monto": df_isr_raw["Marginal"]},
            {"Paso": "6. Cuota Fija", "Monto": df_isr_raw["Cuota Fija"]},
            {"Paso": "7. ISR Mensual", "Monto": df_isr_raw["ISR Mes"]},
            {"Paso": "8. Factor Periodo", "Monto": df_isr_raw["Factor"]},
            {"Paso": "9. RETENCIÓN", "Monto": isr},
        ]
        df_isr_view = pd.DataFrame(data_isr)
        
        # Formateador simple
        def fmt(x, p):
            if "Tasa" in p: return f"{x*100:.2f}%"
            if "Factor" in p: return f"{x:.4f}"
            return f"${x:,.2f}"
        df_isr_view["Monto"] = df_isr_view.apply(lambda x: fmt(x["Monto"], x["Paso"]), axis=1)
        st.dataframe(df_isr_view, hide_index=True, use_container_width=True)

    with col_imss:
        st.markdown("##### 🏥 Cuotas IMSS")
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Importe"])
        total_row = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Importe": imss}])
        df_imss = pd.concat([df_imss, total_row], ignore_index=True)
        st.dataframe(df_imss.style.format({"Importe": "${:,.2f}"}), hide_index=True, use_container_width=True)
