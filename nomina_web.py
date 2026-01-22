import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Nominapp MX",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATOS OFICIALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,  # Zona General
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
    
    /* KPIs */
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

# --- MOTORES DE CÁLCULO ---
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

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("nominapp_logo.png"):
        st.image("nominapp_logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 Nominapp MX")
    
    st.markdown("---")
    modulo = st.sidebar.radio("📍 Módulo", ["Nómina Periódica", "Aguinaldo", "Finiquito y Liquidación"])
    st.markdown("---")

# ==============================================================================
# MÓDULO 1: NÓMINA PERIÓDICA (RESTAURO EL ANÁLISIS COMPLETO)
# ==============================================================================
if modulo == "Nómina Periódica":
    with st.sidebar:
        with st.container(border=True):
            st.markdown("##### ⚙️ Configuración")
            criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
            dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
            periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual"])
            if periodo == "Quincenal": dias_pago = 15
            elif periodo == "Semanal": dias_pago = 7
            else: dias_pago = dias_mes_base

        with st.container(border=True):
            st.markdown("##### 💵 Ingreso")
            tipo_ingreso = st.radio("Base", ["Bruto Mensual", "Por Periodo (Nómina)"], horizontal=True)
            monto_input = st.number_input("Monto ($)", value=20000.0, step=500.0, format="%.2f")
            
            if tipo_ingreso == "Bruto Mensual":
                sueldo_diario = monto_input / dias_mes_base
            else:
                sueldo_diario = monto_input / dias_pago

        with st.container(border=True):
            st.markdown("##### 📅 Datos Laborales")
            antig = st.number_input("Años Laborados", 0, 60, 0)
        
        st.button("CALCULAR", type="primary", use_container_width=True)

    # CÁLCULOS
    dias_vac = 14 if antig > 0 else 12
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_engine(sbc, dias_pago)
    
    # ISR Proyección Mensual
    base_mensual_proy = sueldo_diario * dias_mes_base
    isr_mensual_proy, _ = calcular_isr_engine(base_mensual_proy, TABLA_ISR_MENSUAL)
    isr = isr_mensual_proy * (dias_pago / dias_mes_base)
    neto = bruto - imss - isr

    # DASHBOARD
    st.markdown("### 📊 Nómina del Periodo")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Ingreso Bruto</div><div class="kpi-value">${bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Retención)</div><div class="kpi-value neon-red">-${isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card"><div class="kpi-label">IMSS (Cuota)</div><div class="kpi-value neon-gold">-${imss:,.2f}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Recibir</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # ANÁLISIS RESTAURADO
    t1, t2, t3 = st.tabs(["🧠 Insights & Valor", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])
    
    with t1:
        col_g, col_i = st.columns([1, 2])
        with col_g:
            source = pd.DataFrame({"Cat": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(
                color=alt.Color("Cat", scale=alt.Scale(range=['#34d399', '#60a5fa', '#fbbf24']), legend=alt.Legend(orient="bottom", titleColor="white", labelColor="white")),
                tooltip=["Cat", alt.Tooltip("Monto", format="$,.2f")]
            ).configure_view(strokeWidth=0).configure(background='transparent')
            st.altair_chart(pie, use_container_width=True)
            
        with col_i:
            # LÓGICA DE INSIGHTS
            horas = dias_pago * 8
            valor_hora = neto / horas
            meses_gob = ((isr+imss)/bruto) * 12
            anual = neto * (365/dias_pago)
            
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #34d399;">
                <span style="color:#94a3b8; font-weight:700;">💰 TU HORA REAL</span><br>
                <span style="color:#cbd5e1;">Realmente ganas:</span> <span style="font-size:1.5em; font-weight:800; color:#34d399;">${valor_hora:.2f} MXN</span>/hora.
            </div>
            <div class="insight-card" style="border-left-color: #f87171;">
                <span style="color:#94a3b8; font-weight:700;">🏛️ CARGA LABORAL</span><br>
                <span style="color:#cbd5e1;">Trabajas:</span> <span style="font-size:1.5em; font-weight:800; color:#f87171;">{meses_gob:.1f} meses</span> al año para pagar impuestos.
            </div>
            <div class="insight-card" style="border-left-color: #60a5fa;">
                <span style="color:#94a3b8; font-weight:700;">📅 PROYECCIÓN ANUAL</span><br>
                <span style="color:#cbd5e1;">Ingreso neto proyectado:</span> <span style="font-size:1.5em; font-weight:800; color:#60a5fa;">${anual:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            
    with t2:
        st.dataframe(pd.DataFrame([
            {"Paso": "Base Mensual", "Valor": f"${base_mensual_proy:,.2f}"},
            {"Paso": "ISR Mensual", "Valor": f"${isr_mensual_proy:,.2f}"},
            {"Paso": "Factor", "Valor": f"{dias_pago/dias_mes_base:.4f}"},
            {"Paso": "ISR Periodo", "Valor": f"${isr:,.2f}"}
        ]), use_container_width=True, hide_index=True)

# ==============================================================================
# MÓDULO 2: AGUINALDO
# ==============================================================================
elif modulo == "Aguinaldo":
    with st.sidebar:
        st.header("🎄 Configuración")
        with st.container(border=True):
            sueldo_mensual = st.number_input("Sueldo Mensual", 15000.0, step=500.0)
            dias_agui = st.number_input("Días Aguinaldo", 15)
            dias_trab = st.number_input("Días Trabajados Año", 365)
        st.button("CALCULAR", type="primary", use_container_width=True)

    sd = sueldo_mensual / 30
    aguinaldo = (dias_trab/365) * dias_agui * sd
    exento = 30 * VALORES_2026["UMA"]
    gravado = max(0, aguinaldo - exento)
    
    # ISR (Marginal)
    isr_base, _ = calcular_isr_engine(sueldo_mensual, TABLA_ISR_MENSUAL)
    isr_total, _ = calcular_isr_engine(sueldo_mensual + gravado, TABLA_ISR_MENSUAL)
    isr_retener = isr_total - isr_base
    neto = aguinaldo - isr_retener
    
    st.markdown("### 🎄 Resultado Aguinaldo")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Monto Bruto</div><div class="kpi-value">${aguinaldo:,.2f}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Parte Exenta</div><div class="kpi-value neon-blue">${min(exento, aguinaldo):,.2f}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto Final</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO 3: FINIQUITO Y LIQUIDACIÓN (REPARADO Y PRECISO)
# ==============================================================================
elif modulo == "Finiquito y Liquidación":
    with st.sidebar:
        st.header("⚖️ Salida Laboral")
        with st.container(border=True):
            causa = st.selectbox("Causa", ["Renuncia (Voluntaria)", "Despido (Injustificado)"])
            f_alta = st.date_input("Fecha Alta", date(2020,1,1))
            f_baja = st.date_input("Fecha Baja", date.today())
            sueldo_men = st.number_input("Sueldo Mensual Bruto", 25000.0)
            
        with st.container(border=True):
            st.markdown("##### Pendientes")
            dias_agui_pend = st.number_input("Días Aguinaldo Pendiente", value=0.0, step=1.0, help="Días proporcionales del año actual")
            dias_vac_pend = st.number_input("Días Vacaciones No Gozadas", value=6.0, step=1.0)
            
        st.button("CALCULAR SALIDA", type="primary", use_container_width=True)

    # 1. CÁLCULOS BASE
    antiguedad_dias = (f_baja - f_alta).days + 1
    anios_completos = antiguedad_dias // 365
    
    # Salarios
    sd = sueldo_men / 30 # Salario Diario (Para Finiquito)
    
    # SDI (Para Indemnización)
    dias_vac_ley = 12
    if anios_completos >= 1: dias_vac_ley = 14 # Simplificado tabla 2026
    factor_int = 1 + ((15 + (dias_vac_ley*0.25))/365)
    sdi = sd * factor_int

    # 2. FINIQUITO (Se paga siempre)
    monto_aguinaldo = (dias_agui_pend / 365) * 15 * sd # Asumiendo 15 de ley si pone dias proporcionales trabajados, o directo si pone dias ganados.
    # Ajuste: Si el usuario pone "Dias Aguinaldo Pendiente" como "Dias trabajados en el año":
    # Vamos a asumir que el input son DIAS DE SALARIO ya calculados o proporcionales.
    # Mejor enfoque: Calcular proporcional automático por fecha si es año corriente.
    # Para simplificar y dar poder al usuario: asumimos que el input "Días Aguinaldo" son los días de prestación devengados.
    monto_aguinaldo = dias_agui_pend * sd # Corregido: Input directo de días ganados
    
    monto_vac = dias_vac_pend * sd
    monto_prima_vac = monto_vac * 0.25
    
    # Prima Antigüedad (Regla: 12 días x Año, Topado a 2 SM)
    # Aplica: Siempre en Despido. En Renuncia solo si > 15 años.
    tope_prima = 2 * VALORES_2026["SALARIO_MINIMO"] # Zona general
    base_prima = min(sd, tope_prima)
    
    pagar_prima = False
    if causa == "Despido (Injustificado)": pagar_prima = True
    elif anios_completos >= 15: pagar_prima = True
    
    prima_antiguedad = 0
    if pagar_prima:
        prima_antiguedad = (antiguedad_dias / 365) * 12 * base_prima

    total_finiquito = monto_aguinaldo + monto_vac + monto_prima_vac + prima_antiguedad

    # 3. LIQUIDACIÓN (Solo Despido)
    indem_3m = 0
    indem_20d = 0
    if causa == "Despido (Injustificado)":
        indem_3m = 3 * 30 * sdi
        indem_20d = 20 * (antiguedad_dias / 365) * sdi
    
    total_liquidacion = indem_3m + indem_20d
    gran_total_bruto = total_finiquito + total_liquidacion

    # 4. ISR (EL CÁLCULO DIFÍCIL)
    # A) ISR Finiquito (Se suma al mes y se tabla mensual - Simplificado)
    isr_base_men, _ = calcular_isr_engine(sueldo_men, TABLA_ISR_MENSUAL)
    
    # Exenciones Finiquito
    exento_agui = min(monto_aguinaldo, 30*VALORES_2026["UMA"])
    exento_prima_vac = min(monto_prima_vac, 15*VALORES_2026["UMA"])
    gravado_finiquito = (monto_aguinaldo - exento_agui) + (monto_prima_vac - exento_prima_vac) + monto_vac # Vacaciones gravan 100%
    
    # ISR Finiquito (Marginal)
    isr_total_fin, _ = calcular_isr_engine(sueldo_men + gravado_finiquito, TABLA_ISR_MENSUAL)
    isr_finiquito = isr_total_fin - isr_base_men
    
    # B) ISR Liquidación (Tasa Efectiva Anualizada - Art 96 LISR)
    isr_liquidacion = 0
    if total_liquidacion > 0 or prima_antiguedad > 0:
        # Total pagos por separación
        total_separacion = total_liquidacion + prima_antiguedad
        
        # Exención: 90 UMA por año trabajado
        exento_liq = 90 * VALORES_2026["UMA"] * anios_completos
        gravado_liq = max(0, total_separacion - exento_liq)
        
        if gravado_liq > 0:
            # Tasa Efectiva del Último Sueldo Mensual Ordinario (USMO)
            tasa_efectiva = (isr_base_men / sueldo_men)
            isr_liquidacion = gravado_liq * tasa_efectiva

    total_impuestos = isr_finiquito + isr_liquidacion
    neto_final = gran_total_bruto - total_impuestos

    # DASHBOARD SALIDA
    st.markdown(f"### ⚖️ Cálculo Final: {causa}")
    st.markdown(f"Antigüedad: **{antiguedad_dias/365:.1f} años** | SD: **${sd:,.2f}** | SDI: **${sdi:,.2f}**")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Gran Total Bruto</div><div class="kpi-value">${gran_total_bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Retención)</div><div class="kpi-value neon-red">-${total_impuestos:,.2f}</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Entregar</div><div class="kpi-value neon-green">${neto_final:,.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    t_fin, t_liq, t_isr = st.tabs(["🔹 Finiquito (Detalle)", "🔸 Liquidación (Detalle)", "🏛️ Cálculo Impuestos"])
    
    with t_fin:
        df_f = pd.DataFrame([
            {"Concepto": "Aguinaldo", "Monto": monto_aguinaldo},
            {"Concepto": "Vacaciones", "Monto": monto_vac},
            {"Concepto": "Prima Vacacional", "Monto": monto_prima_vac},
            {"Concepto": "Prima Antigüedad", "Monto": prima_antiguedad},
        ])
        st.dataframe(df_f.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
        if prima_antiguedad > 0: st.info(f"Prima Antigüedad calculada con tope 2xSM: ${min(sd, tope_prima):,.2f}")

    with t_liq:
        if total_liquidacion == 0:
            st.warning("No aplica indemnización en Renuncia Voluntaria.")
        else:
            df_l = pd.DataFrame([
                {"Concepto": "Indemnización 3 Meses", "Monto": indem_3m},
                {"Concepto": "20 Días por Año", "Monto": indem_20d},
            ])
            st.dataframe(df_l.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
            
    with t_isr:
        st.markdown("#### 1. ISR Finiquito (Marginal)")
        st.write(f"Gravado acumulable al mes: ${gravado_finiquito:,.2f}")
        st.write(f"ISR Retenido: ${isr_finiquito:,.2f}")
        
        st.markdown("#### 2. ISR Liquidación (Tasa Efectiva)")
        st.write(f"Total Separación: ${(total_liquidacion+prima_antiguedad):,.2f}")
        st.write(f"Exento (90 UMA x {anios_completos} años): ${90*VALORES_2026['UMA']*anios_completos:,.2f}")
        st.write(f"Base Gravable: ${max(0, (total_liquidacion+prima_antiguedad) - (90*VALORES_2026['UMA']*anios_completos)):,.2f}")
        st.write(f"Tasa Efectiva (ISR Mes / Sueldo Mes): {isr_base_men/sueldo_men:.4%}")
        st.write(f"ISR Liquidación: ${isr_liquidacion:,.2f}")
