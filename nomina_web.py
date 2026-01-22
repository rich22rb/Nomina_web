import streamlit as st
import pandas as pd
import altair as alt

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Nómina 2026 | Dark Enterprise",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATOS 2026 ---
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

# --- CSS PRO (DARK MODE) ---
st.markdown("""
<style>
    /* FONDO PRINCIPAL */
    .stApp {
        background-color: #0f172a; /* Slate 900 */
        color: #f8fafc;
    }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #1e293b; /* Slate 800 */
        border-right: 1px solid #334155;
    }

    /* TARJETAS KPI */
    .dark-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    
    /* TEXTOS */
    h1, h2, h3 { color: #f8fafc !important; }
    p, li, label { color: #cbd5e1 !important; }
    
    /* METRICAS */
    .kpi-label {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 5px;
        font-family: 'Roboto', sans-serif;
    }
    
    /* COLORES NEÓN */
    .neon-green { color: #34d399 !important; } 
    .neon-red { color: #f87171 !important; }   
    .neon-gold { color: #fbbf24 !important; }  
    .neon-blue { color: #60a5fa !important; }
    
    /* TABLAS */
    .stDataFrame {
        border: 1px solid #334155;
        border-radius: 8px;
    }
    
    /* INPUTS */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0f172a !important;
        color: white !important;
        border: 1px solid #475569 !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --- MOTORES DE CÁLCULO ---
def calcular_isr_engine(sueldo_diario, dias_pago, dias_mes_base):
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

def calcular_imss_engine(sbc, dias):
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

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=50)
    st.markdown("### ⚡ Configuración")
    
    with st.container(border=True):
        st.markdown("##### 1. Tiempos")
        criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
        dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
        
        periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual"])
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        else: dias_pago = dias_mes_base

    with st.container(border=True):
        st.markdown("##### 2. Ingresos")
        tipo_ingreso = st.radio("Base de Sueldo", ["Bruto Mensual", "Por Periodo"], horizontal=True)
        monto_input = st.number_input("Monto en Pesos", value=20000.0, step=500.0, format="%.2f")
        
        if tipo_ingreso == "Bruto Mensual":
            sueldo_diario = monto_input / dias_mes_base
        else:
            sueldo_diario = monto_input / dias_pago

    with st.container(border=True):
        st.markdown("##### 3. Antigüedad")
        antig = st.number_input("Años Cumplidos", 0, 60, 0)

    st.markdown("---")
    if st.button("CALCULAR AHORA ▶", type="primary", use_container_width=True):
        pass 

# --- DASHBOARD ---
st.markdown("## 🚀 Nómina Enterprise 2026")
st.markdown(f"Resumen Fiscal | Base Diaria: **${sueldo_diario:,.2f}** | Días Pagados: **{dias_pago}**")
st.markdown("---")

# CÁLCULOS
dias_vac = 14 if antig > 0 else 12
factor_int = 1 + ((15 + (dias_vac*0.25))/365)
sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

bruto = sueldo_diario * dias_pago
imss, df_imss_raw = calcular_imss_engine(sbc, dias_pago)
isr, df_isr_raw = calcular_isr_engine(sueldo_diario, dias_pago, dias_mes_base)
neto = bruto - imss - isr

# 1. TARJETAS KPI
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">Ingreso Bruto</div><div class="kpi-value">${bruto:,.2f}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Impuesto)</div><div class="kpi-value neon-red">-${isr:,.2f}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">IMSS (Seguro)</div><div class="kpi-value neon-gold">-${imss:,.2f}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Pagar</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. ANÁLISIS DETALLADO
tab_main, tab_isr, tab_imss = st.tabs(["🧠 Análisis Inteligente", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])

with tab_main:
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        # --- AQUÍ ESTÁ EL ARREGLO DE LA GRÁFICA ---
        source = pd.DataFrame({
            "Categoría": ["Neto (Tuyo)", "ISR (SAT)", "IMSS (Salud)"],
            "Monto": [neto, isr, imss]
        })
        
        # Base de la gráfica
        base = alt.Chart(source).encode(
            theta=alt.Theta("Monto", stack=True)
        )
        
        # El anillo (Donut)
        pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
            color=alt.Color(
                "Categoría",
                scale=alt.Scale(
                    domain=['Neto (Tuyo)', 'ISR (SAT)', 'IMSS (Salud)'], 
                    range=['#34d399', '#60a5fa', '#fbbf24']
                ),
                legend=alt.Legend(
                    orient='bottom',    # Leyenda abajo para no cortar
                    titleColor='white', # Texto blanco
                    labelColor='white'
                )
            ),
            tooltip=["Categoría", alt.Tooltip("Monto", format="$,.2f")]
        )
        
        # Configuración FINAL para quitar fondo y bordes
        final_chart = pie.configure_view(
            strokeWidth=0 # Quita el marco feo
        ).configure(
            background='transparent' # Quita el fondo negro/blanco
        )
        
        st.altair_chart(final_chart, use_container_width=True)
        
    with col_der:
        total_impuestos = isr + imss
        tasa_efectiva = (total_impuestos / bruto) * 100
        dias_impuestos = total_impuestos / sueldo_diario
        proyeccion_anual = total_impuestos * (365 / dias_pago)
        
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #60a5fa;">
            <ul style="line-height: 2;">
                <li><b>Día de Libertad Fiscal:</b> En este periodo, trabajas <b class="neon-red">{dias_impuestos:.1f} días</b> solo para pagar impuestos.</li>
                <li><b>Tasa Efectiva:</b> Realmente pagas el <b class="neon-gold">{tasa_efectiva:.1f}%</b> de tu ingreso bruto total.</li>
                <li><b>Proyección Anual:</b> Aportarás aprox. <b class="neon-blue">${proyeccion_anual:,.2f}</b> al sistema este año.</li>
                <li><b>Eficiencia:</b> Te quedas con <b class="neon-green">${(neto/bruto)*1000:,.2f}</b> de cada $1,000 ganados.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab_isr:
    # Tabla ISR
    data = [
        {"Concepto": "1. Base Mensual", "Monto": df_isr_raw["Base Mensual"]},
        {"Concepto": "2. Límite Inferior", "Monto": df_isr_raw["Límite Inf."]},
        {"Concepto": "3. Excedente", "Monto": df_isr_raw["Excedente"]},
        {"Concepto": "4. Tasa Aplicable", "Monto": df_isr_raw["Tasa"]},
        {"Concepto": "5. Impuesto Marginal", "Monto": df_isr_raw["Marginal"]},
        {"Concepto": "6. Cuota Fija", "Monto": df_isr_raw["Cuota Fija"]},
        {"Concepto": "7. ISR Mensual", "Monto": df_isr_raw["ISR Mes"]},
        {"Concepto": f"8. Factor ({dias_pago}/{dias_mes_base})", "Monto": df_isr_raw["Factor"]},
        {"Concepto": "9. RETENCIÓN ISR", "Monto": isr},
    ]
    df_isr = pd.DataFrame(data)
    
    def fmt(x, c):
        if "Tasa" in c: return f"{x*100:.2f}%"
        if "Factor" in c: return f"{x:.4f}"
        return f"${x:,.2f}"
    df_isr["Monto"] = df_isr.apply(lambda x: fmt(x["Monto"], x["Concepto"]), axis=1)
    
    st.dataframe(df_isr, use_container_width=True, hide_index=True)

with tab_imss:
    # Tabla IMSS
    df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
    total = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
    df_fin = pd.concat([df_imss, total], ignore_index=True)
    st.dataframe(df_fin.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
