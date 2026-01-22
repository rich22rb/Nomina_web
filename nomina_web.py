import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image
import os
from datetime import date

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
    "SALARIO_MINIMO_FN": 474.07, # Dato estimado FN
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
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }

    /* TARJETAS */
    .dark-card {
        background-color: #1e293b; border: 1px solid #334155; border-radius: 12px;
        padding: 24px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .insight-card {
        background-color: #1e293b; border-left: 4px solid #3b82f6; border-radius: 8px;
        padding: 20px; margin-bottom: 15px; border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155;
    }
    
    /* TEXTOS */
    h1, h2, h3, h4 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    p, li, label, .stMarkdown { color: #cbd5e1 !important; }
    
    /* INPUTS */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input {
        background-color: #0f172a !important; color: white !important; border: 1px solid #475569 !important;
    }
    
    /* KPI METRICS */
    .kpi-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; }
    .kpi-value { font-size: 2.2rem; font-weight: 800; color: #ffffff; font-family: 'Roboto', sans-serif; }
    
    /* COLORES */
    .neon-green { color: #34d399 !important; } 
    .neon-red { color: #f87171 !important; }   
    .neon-gold { color: #fbbf24 !important; }  
    .neon-blue { color: #60a5fa !important; }
    
    /* TABLAS */
    .stDataFrame { border: 1px solid #334155; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE CÁLCULO GENERAL ---
def calcular_isr_engine(base_gravable, tabla_isr):
    limite, cuota, porc = 0, 0, 0
    for row in tabla_isr:
        if base_gravable >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
    excedente = base_gravable - limite
    marginal = excedente * porc
    isr = marginal + cuota
    return isr, {"Límite": limite, "Excedente": excedente, "Tasa": porc, "Cuota": cuota}

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

# --- SIDEBAR GLOBAL ---
with st.sidebar:
    if os.path.exists("nominapp_logo.png"):
        st.image("nominapp_logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 Nominapp MX")

    st.markdown("---")
    
    # *** SELECTOR DE MÓDULO PRINCIPAL ***
    modulo = st.sidebar.radio("📍 Selecciona Módulo", ["Nómina Periódica", "Aguinaldo", "Finiquito y Liquidación"])
    st.markdown("---")

# ==============================================================================
# MÓDULO 1: NÓMINA PERIÓDICA (TU CÓDIGO ORIGINAL)
# ==============================================================================
if modulo == "Nómina Periódica":
    with st.sidebar:
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

    # --- DASHBOARD NÓMINA ---
    dias_vac = 14 if antig > 0 else 12
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_engine(sbc, dias_pago)
    
    # Ajuste ISR para periodo
    base_mensual = sueldo_diario * dias_mes_base
    isr_mensual, isr_meta = calcular_isr_engine(base_mensual, TABLA_ISR_MENSUAL)
    isr = isr_mensual * (dias_pago / dias_mes_base)
    neto = bruto - imss - isr

    # UI NÓMINA
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Ingreso Bruto</div><div class="kpi-value">${bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Retención)</div><div class="kpi-value neon-red">-${isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="dark-card"><div class="kpi-label">IMSS (Cuota)</div><div class="kpi-value neon-gold">-${imss:,.2f}</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Recibir</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ANÁLISIS
    tab_main, tab_isr, tab_imss = st.tabs(["🧠 Insights & Valor Real", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])
    
    with tab_main:
        cg, ci = st.columns([1, 2])
        with cg:
            source = pd.DataFrame({"Cat": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(
                color=alt.Color("Cat", scale=alt.Scale(range=['#34d399', '#60a5fa', '#fbbf24']), legend=alt.Legend(orient="bottom", titleColor="white", labelColor="white")),
                tooltip=["Cat", alt.Tooltip("Monto", format="$,.2f")]
            ).configure_view(strokeWidth=0).configure(background='transparent')
            st.altair_chart(pie, use_container_width=True)
        with ci:
            horas_periodo = dias_pago * 8
            valor_hora_neta = neto / horas_periodo
            proyeccion = neto * (365 / dias_pago)
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #34d399;">
                <span style="color:#94a3b8; font-weight:700;">💰 TU HORA REAL</span><br>
                <span style="color:#cbd5e1;">Realmente ganas:</span> <span style="font-size:1.5em; font-weight:800; color:#34d399;">${valor_hora_neta:.2f} MXN</span>/hora libre de impuestos.
            </div>
            <div class="insight-card" style="border-left-color: #60a5fa;">
                <span style="color:#94a3b8; font-weight:700;">📅 FLUJO ANUAL</span><br>
                <span style="color:#cbd5e1;">Proyección neta anual:</span> <span style="font-size:1.5em; font-weight:800; color:#60a5fa;">${proyeccion:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with tab_isr:
        st.dataframe(pd.DataFrame([
            {"Concepto": "Base Mensual", "Monto": f"${base_mensual:,.2f}"},
            {"Concepto": "ISR Mensual (Tabla)", "Monto": f"${isr_mensual:,.2f}"},
            {"Concepto": "Factor Periodo", "Monto": f"{dias_pago/dias_mes_base:.4f}"},
            {"Concepto": "ISR Retenido", "Monto": f"${isr:,.2f}"}
        ]), use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 2: AGUINALDO
# ==============================================================================
elif modulo == "Aguinaldo":
    with st.sidebar:
        st.header("🎄 Configuración Aguinaldo")
        with st.container(border=True):
            sueldo_mensual = st.number_input("Sueldo Bruto Mensual", 10000.0, step=500.0)
            dias_aguinaldo = st.number_input("Días de Aguinaldo (Prestación)", 15, 90, 15)
            dias_trabajados = st.number_input("Días trabajados en el año", 1, 366, 365)
        st.button("CALCULAR AGUINALDO", type="primary", use_container_width=True)

    # CÁLCULOS AGUINALDO
    sueldo_diario = sueldo_mensual / 30
    aguinaldo_bruto = (dias_trabajados / 365) * dias_aguinaldo * sueldo_diario
    
    # Exención (30 UMAS)
    exento = 30 * VALORES_2026["UMA"]
    gravado = max(0, aguinaldo_bruto - exento)
    
    # ISR (Método Simplificado Tasa Marginal para Dashboard)
    # Se suma a la base mensual para ver el salto de ISR
    base_mensual = sueldo_mensual
    isr_base, _ = calcular_isr_engine(base_mensual, TABLA_ISR_MENSUAL)
    isr_con_aguinaldo, _ = calcular_isr_engine(base_mensual + gravado, TABLA_ISR_MENSUAL)
    isr_retener = isr_con_aguinaldo - isr_base
    neto_aguinaldo = aguinaldo_bruto - isr_retener

    st.markdown("## 🎄 Proyección de Aguinaldo 2026")
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Aguinaldo Bruto</div><div class="kpi-value">${aguinaldo_bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Monto Exento (SAT)</div><div class="kpi-value neon-blue">${min(exento, aguinaldo_bruto):,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Recibir</div><div class="kpi-value neon-green">${neto_aguinaldo:,.2f}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c_izq, c_der = st.columns([1, 2])
    with c_izq:
        st.markdown("#### 🔍 Desglose Fiscal")
        st.markdown(f"""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 8px;">
            <ul style="line-height: 2;">
                <li><b>Total Gravado:</b> <span class="neon-red">${gravado:,.2f}</span></li>
                <li><b>ISR Aprox:</b> <span class="neon-red">-${isr_retener:,.2f}</span></li>
                <li><b>Parte Libre de Impuestos:</b> <span class="neon-green">${min(exento, aguinaldo_bruto):,.2f}</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c_der:
        st.markdown("#### 💡 Dato Nominapp")
        st.info(f"El SAT permite exentar hasta 30 UMAS (${exento:,.2f}) de tu aguinaldo. Solo pagas impuestos por la diferencia. Este cálculo usa la metodología de sumar el gravado al ingreso mensual para determinar la tasa marginal.")

# ==============================================================================
# MÓDULO 3: FINIQUITO Y LIQUIDACIÓN
# ==============================================================================
elif modulo == "Finiquito y Liquidación":
    with st.sidebar:
        st.header("⚖️ Finiquito & Liquidación")
        with st.container(border=True):
            tipo_salida = st.selectbox("Motivo de Salida", ["Renuncia Voluntaria (Finiquito)", "Despido Injustificado (Liquidación)"])
            
            f_ingreso = st.date_input("Fecha Ingreso", date(2020, 1, 1))
            f_salida = st.date_input("Fecha Salida", date.today())
            
            sueldo_men = st.number_input("Sueldo Mensual Bruto", 20000.0, step=500.0)
            dias_pend_agui = st.number_input("Días Aguinaldo (Empresa)", 15)
            dias_vac_pend = st.number_input("Días Vacaciones Pendientes", 6)
            
        st.button("CALCULAR SALIDA", type="primary", use_container_width=True)

    # LÓGICA
    antiguedad_dias = (f_salida - f_ingreso).days
    anios_antig = antiguedad_dias / 365.25
    sd = sueldo_men / 30
    
    # Factor Integración (Simplificado Ley)
    dias_vac_ley = 12 # Mínimo
    if anios_antig > 1: dias_vac_ley = 14
    factor_int = 1 + ((15 + (dias_vac_ley*0.25))/365)
    sdi = sd * factor_int

    # 1. FINIQUITO (SIEMPRE SE PAGA)
    # Aguinaldo Proporcional
    dias_trab_anio = f_salida.timetuple().tm_yday
    prop_aguinaldo = (dias_trab_anio / 365) * dias_pend_agui * sd
    
    # Vacaciones y Prima
    monto_vac = dias_vac_pend * sd
    prima_vac = monto_vac * 0.25
    
    # Prima Antigüedad (Solo si > 15 años en renuncia, o siempre en despido)
    prima_antiguedad = 0
    tope_prima = 2 * VALORES_2026["SALARIO_MINIMO"]
    base_prima = min(sd, tope_prima)
    
    pagar_prima = False
    if tipo_salida == "Despido Injustificado": pagar_prima = True
    elif anios_antig >= 15: pagar_prima = True
    
    if pagar_prima:
        prima_antiguedad = 12 * anios_antig * base_prima

    total_finiquito = prop_aguinaldo + monto_vac + prima_vac + prima_antiguedad

    # 2. LIQUIDACIÓN (SOLO DESPIDO)
    indemnizacion = 0
    veinte_dias = 0
    if tipo_salida == "Despido Injustificado":
        indemnizacion = 3 * 30 * sdi # 3 meses constitucionales
        veinte_dias = 20 * anios_antig * sdi # 20 días por año (negativa reinstalación)

    total_liquidacion = indemnizacion + veinte_dias
    gran_total = total_finiquito + total_liquidacion

    # DISPLAY
    st.markdown(f"## ⚖️ Cálculo de {tipo_salida}")
    st.markdown(f"Antigüedad: **{anios_antig:.1f} años** | SDI: **${sdi:,.2f}**")
    
    col_tot1, col_tot2 = st.columns(2)
    with col_tot1:
         st.markdown(f"""<div class="dark-card" style="border: 1px solid #60a5fa;"><div class="kpi-label">Conceptos Finiquito</div><div class="kpi-value neon-blue">${total_finiquito:,.2f}</div><div class="kpi-sub">Parte Proporcional</div></div>""", unsafe_allow_html=True)
    with col_tot2:
         color_borde = "#34d399" if total_liquidacion == 0 else "#f87171"
         titulo = "Indemnización (0.00)" if total_liquidacion == 0 else "Indemnización + 20 días"
         st.markdown(f"""<div class="dark-card" style="border: 1px solid {color_borde};"><div class="kpi-label">{titulo}</div><div class="kpi-value neon-red">${total_liquidacion:,.2f}</div><div class="kpi-sub">Solo Despido</div></div>""", unsafe_allow_html=True)
    
    st.markdown("### 📋 Desglose Detallado")
    
    tab_fini, tab_liq = st.tabs(["🔹 Finiquito (Derechos Irrenunciables)", "🔸 Liquidación (Indemnización)"])
    
    with tab_fini:
        df_fini = pd.DataFrame([
            {"Concepto": "Aguinaldo Proporcional", "Monto": prop_aguinaldo},
            {"Concepto": "Vacaciones Pendientes", "Monto": monto_vac},
            {"Concepto": "Prima Vacacional (25%)", "Monto": prima_vac},
            {"Concepto": "Prima Antigüedad (12d/año topado)", "Monto": prima_antiguedad},
        ])
        st.dataframe(df_fini.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
        if prima_antiguedad > 0:
            st.success(f"✅ Se incluye Prima de Antigüedad por cumplir la condición legal (Despido o >15 años). Base topada: ${base_prima:,.2f}")
        else:
            st.info("ℹ️ No aplica Prima de Antigüedad (Menos de 15 años en renuncia).")

    with tab_liq:
        if tipo_salida == "Renuncia Voluntaria (Finiquito)":
            st.warning("⚠️ En Renuncia Voluntaria NO aplica pago de Indemnización ni 20 días por año.")
        else:
            df_liq = pd.DataFrame([
                {"Concepto": "3 Meses Constitucionales (SDI)", "Monto": indemnizacion},
                {"Concepto": "20 Días por Año (SDI)", "Monto": veinte_dias},
            ])
            st.dataframe(df_liq.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
            st.markdown(f"**Total a Pagar (Finiquito + Liquidación):** <span class='neon-green' style='font-size:1.5em; font-weight:bold'>${gran_total:,.2f}</span> (Antes de ISR)", unsafe_allow_html=True)
