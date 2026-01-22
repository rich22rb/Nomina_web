import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
import os

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Nominapp MX",
    page_icon="🚀",
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

# --- CSS DARK ENTERPRISE ---
st.markdown("""
<style>
    /* FONDO */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }

    /* TARJETAS DE RESULTADOS */
    .dark-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    
    /* TARJETA DE INSIGHTS (NUEVA) */
    .insight-card {
        background-color: #1e293b;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
    }
    
    /* TEXTOS */
    h1, h2, h3, h4 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    p, li, label, .stMarkdown { color: #cbd5e1 !important; }
    
    /* INPUTS */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #0f172a !important;
        color: white !important;
        border: 1px solid #475569 !important;
    }
    
    /* MÉTRICAS */
    .kpi-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        font-family: 'Roboto', sans-serif;
    }
    .insight-val { color: #ffffff; font-weight: 700; font-size: 1.1em; }
    
    /* COLORES NEÓN */
    .neon-green { color: #34d399 !important; } 
    .neon-red { color: #f87171 !important; }   
    .neon-gold { color: #fbbf24 !important; }  
    .neon-blue { color: #60a5fa !important; }
    
    /* TABLAS */
    .stDataFrame { border: 1px solid #334155; border-radius: 8px; }
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
    if os.path.exists("nominapp_logo.png"):
        st.image("nominapp_logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 Nominapp MX")

    st.markdown("---")
    
    with st.container(border=True):
        st.markdown("##### ⚙️ Parámetros")
        criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
        dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
        periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual"])
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        else: dias_pago = dias_mes_base

    with st.container(border=True):
        st.markdown("##### 💵 Ingresos")
        tipo_ingreso = st.radio("Modalidad de Pago", ["Bruto Mensual", "Por Periodo (Nómina)"], horizontal=True)
        monto_input = st.number_input("Monto Bruto ($)", value=20000.0, step=500.0, format="%.2f")
        
        if tipo_ingreso == "Bruto Mensual":
            sueldo_diario = monto_input / dias_mes_base
        else:
            sueldo_diario = monto_input / dias_pago

    with st.container(border=True):
        st.markdown("##### 📅 Antigüedad")
        antig = st.number_input("Años Laborados", 0, 60, 0)

    st.markdown("---")
    st.button("CALCULAR NÓMINA", type="primary", use_container_width=True)

# --- DASHBOARD ---
dias_vac = 14 if antig > 0 else 12
factor_int = 1 + ((15 + (dias_vac*0.25))/365)
sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

bruto = sueldo_diario * dias_pago
imss, df_imss_raw = calcular_imss_engine(sbc, dias_pago)
isr, df_isr_raw = calcular_isr_engine(sueldo_diario, dias_pago, dias_mes_base)
neto = bruto - imss - isr

# 1. KPIs
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">Ingreso Bruto</div><div class="kpi-value">${bruto:,.2f}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Retención)</div><div class="kpi-value neon-red">-${isr:,.2f}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="dark-card"><div class="kpi-label">IMSS (Cuota)</div><div class="kpi-value neon-gold">-${imss:,.2f}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Recibir</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. ANÁLISIS MEJORADO
tab_main, tab_isr, tab_imss = st.tabs(["🧠 Insights & Valor Real", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])

with tab_main:
    col_graph, col_insights = st.columns([1, 2])
    
    with col_graph:
        # Gráfica Dona Corregida
        source = pd.DataFrame({
            "Categoría": ["Neto (Tuyo)", "ISR (SAT)", "IMSS (Salud)"],
            "Monto": [neto, isr, imss]
        })
        base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
        pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(
            color=alt.Color("Categoría", scale=alt.Scale(range=['#34d399', '#60a5fa', '#fbbf24']),
                            legend=alt.Legend(orient="bottom", titleColor="white", labelColor="white")),
            tooltip=["Categoría", alt.Tooltip("Monto", format="$,.2f")]
        ).configure_view(strokeWidth=0).configure(background='transparent')
        st.altair_chart(pie, use_container_width=True)

    with col_insights:
        # --- LÓGICA DE INSIGHTS ÚTILES ---
        # 1. Valor Hora Real (Asumiendo 8h/día estandár)
        horas_periodo = dias_pago * 8
        valor_hora_bruta = bruto / horas_periodo
        valor_hora_neta = neto / horas_periodo
        
        # 2. Meses trabajando para el gobierno
        porcentaje_impuestos = (isr + imss) / bruto
        meses_para_gobierno = porcentaje_impuestos * 12
        
        # 3. Proyección Anual Neta (Cashflow)
        proyeccion_anual = neto * (365 / dias_pago)

        st.markdown("#### 💡 Análisis de Valor")
        
        # Tarjeta 1: Tu tiempo
        st.markdown(f"""
        <div class="insight-card" style="border-left-color: #34d399;">
            <span style="color:#94a3b8; font-size:0.9em; text-transform:uppercase; font-weight:700;">💰 Tu Hora Real</span><br>
            <span style="color:#cbd5e1;">Aunque te contraten por <b>${valor_hora_bruta:.2f}/hr</b>, realmente entran a tu bolsa:</span><br>
            <span style="font-size:1.8em; font-weight:800; color:#34d399;">${valor_hora_neta:.2f} MXN</span> <span style="font-size:0.9em;">por hora trabajada.</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Tarjeta 2: Tu esfuerzo fiscal
        st.markdown(f"""
        <div class="insight-card" style="border-left-color: #f87171;">
            <span style="color:#94a3b8; font-size:0.9em; text-transform:uppercase; font-weight:700;">🏛️ Socio Incómodo (SAT+IMSS)</span><br>
            <span style="color:#cbd5e1;">De los 12 meses del año, trabajas aproximadamente:</span><br>
            <span style="font-size:1.5em; font-weight:800; color:#f87171;">{meses_para_gobierno:.1f} meses</span> <span style="font-size:0.9em;">exclusivamente para pagar impuestos.</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Tarjeta 3: Proyección
        st.markdown(f"""
        <div class="insight-card" style="border-left-color: #60a5fa;">
            <span style="color:#94a3b8; font-size:0.9em; text-transform:uppercase; font-weight:700;">📅 Flujo Anual Proyectado</span><br>
            <span style="color:#cbd5e1;">Si mantienes este sueldo, recibirás en tu cuenta:</span><br>
            <span style="font-size:1.5em; font-weight:800; color:#60a5fa;">${proyeccion_anual:,.2f}</span> <span style="font-size:0.9em;">netos al año.</span>
        </div>
        """, unsafe_allow_html=True)

with tab_isr:
    data_isr = [
        {"Paso": "1. Base Gravable", "Monto": df_isr_raw["Base Mensual"]},
        {"Paso": "2. Límite Inferior", "Monto": df_isr_raw["Límite Inf."]},
        {"Paso": "3. Excedente", "Monto": df_isr_raw["Excedente"]},
        {"Paso": "4. Tasa %", "Monto": df_isr_raw["Tasa"]},
        {"Paso": "5. Impuesto Marginal", "Monto": df_isr_raw["Marginal"]},
        {"Paso": "6. Cuota Fija", "Monto": df_isr_raw["Cuota Fija"]},
        {"Paso": "7. ISR Mensual", "Monto": df_isr_raw["ISR Mes"]},
        {"Paso": f"8. Factor ({dias_pago:.1f} días)", "Monto": df_isr_raw["Factor"]},
        {"Paso": "9. RETENCIÓN ISR", "Monto": isr},
    ]
    df_isr_view = pd.DataFrame(data_isr)
    def fmt(x, c):
        if "Tasa" in c: return f"{x*100:.2f}%"
        if "Factor" in c: return f"{x:.4f}"
        return f"${x:,.2f}"
    df_isr_view["Monto"] = df_isr_view.apply(lambda x: fmt(x["Monto"], x["Paso"]), axis=1)
    st.dataframe(df_isr_view, use_container_width=True, hide_index=True)

with tab_imss:
    df_imss_view = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
    total_imss = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
    df_imss_final = pd.concat([df_imss_view, total_imss], ignore_index=True)
    st.dataframe(df_imss_final.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
