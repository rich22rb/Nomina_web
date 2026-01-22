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

# --- FUNCIONES ---
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
# MÓDULO 1: NÓMINA PERIÓDICA
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
        
        st.button("CALCULAR NÓMINA", type="primary", use_container_width=True)

    # CÁLCULOS
    dias_vac = 14 if antig > 0 else 12
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)

    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_engine(sbc, dias_pago)
    
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
    
    t1, t2, t3 = st.tabs(["🧠 Insights", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])
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
            horas = dias_pago * 8
            valor_hora = neto / horas
            meses_gob = ((isr+imss)/bruto) * 12
            anual = neto * (365/dias_pago)
            
            # CORRECCIÓN DE INDENTACIÓN AQUÍ
            html_content = f"""
            <div class="insight-card" style="border-left-color: #34d399;">
                <span style="color:#94a3b8; font-weight:700;">💰 TU HORA REAL</span><br>
                <span style="color:#cbd5e1;">Realmente ganas:</span> <span style="font-size:1.5em; font-weight:800; color:#34d399;">${valor_hora:.2f} MXN</span>/hora.
            </div>
            <div class="insight-card" style="border-left-color: #f87171;">
                <span style="color:#94a3b8; font-weight:700;">🏛️ CARGA LABORAL</span><br>
                <span style="color:#cbd5e1;">Trabajas:</span> <span style="font-size:1.5em; font-weight:800; color:#f87171;">{meses_gob:.1f} meses</span> al año para impuestos.
            </div>
            <div class="insight-card" style="border-left-color: #60a5fa;">
                <span style="color:#94a3b8; font-weight:700;">📅 PROYECCIÓN ANUAL</span><br>
                <span style="color:#cbd5e1;">Ingreso neto proyectado:</span> <span style="font-size:1.5em; font-weight:800; color:#60a5fa;">${anual:,.2f}</span>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
            
    with t2:
        st.dataframe(pd.DataFrame([
            {"Paso": "Base Mensual", "Valor": f"${base_mensual_proy:,.2f}"},
            {"Paso": "ISR Mensual", "Valor": f"${isr_mensual_proy:,.2f}"},
            {"Paso": "Factor", "Valor": f"{dias_pago/dias_mes_base:.4f}"},
            {"Paso": "ISR Periodo", "Valor": f"${isr:,.2f}"}
        ]), use_container_width=True, hide_index=True)
    with t3:
        # Mostramos desglose IMSS
        df_imss_view = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        st.dataframe(df_imss_view.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)


# ==============================================================================
# MÓDULO 2: AGUINALDO
# ==============================================================================
elif modulo == "Aguinaldo":
    with st.sidebar:
        st.header("🎄 Aguinaldo 2026")
        with st.container(border=True):
            sueldo_mensual = st.number_input("Sueldo Mensual Bruto", 15000.0, step=500.0)
            dias_ley = st.number_input("Días de Prestación (Ley=15)", 15)
            
        with st.container(border=True):
            st.markdown("##### 🗓️ Cálculo de Días")
            calculo_tipo = st.radio("Periodo a pagar", ["Año Completo (2026)", "Proporcional (Ingresé este año)"])
            
            if calculo_tipo == "Proporcional (Ingresé este año)":
                f_ingreso_ag = st.date_input("Fecha de Ingreso", date(2026, 6, 1))
                f_fin_anio = date(2026, 12, 31)
                dias_trabajados = (f_fin_anio - f_ingreso_ag).days + 1
            else:
                dias_trabajados = 365
                
        st.button("CALCULAR AGUINALDO", type="primary", use_container_width=True)

    # LÓGICA
    sd = sueldo_mensual / 30
    aguinaldo_bruto = (dias_trabajados/365) * dias_ley * sd
    exento = 30 * VALORES_2026["UMA"]
    gravado = max(0, aguinaldo_bruto - exento)
    
    # ISR
    isr_base, _ = calcular_isr_engine(sueldo_mensual, TABLA_ISR_MENSUAL)
    isr_total, _ = calcular_isr_engine(sueldo_mensual + gravado, TABLA_ISR_MENSUAL)
    isr_retener = isr_total - isr_base
    neto = aguinaldo_bruto - isr_retener

    st.markdown("### 🎄 Resultado de Aguinaldo")
    st.markdown(f"Días calculados: **{dias_trabajados} laborados** = **{(dias_trabajados/365)*dias_ley:.2f} días de pago**.")
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Monto Bruto</div><div class="kpi-value">${aguinaldo_bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR (Retención)</div><div class="kpi-value neon-red">-${isr_retener:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto Final</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_det, col_vis = st.columns([2, 1])
    with col_det:
        st.markdown("#### 📋 Desglose Fiscal")
        df_agui = pd.DataFrame([
            {"Concepto": "Aguinaldo Devengado", "Monto": aguinaldo_bruto},
            {"Concepto": "(-) Exento (30 UMA)", "Monto": min(exento, aguinaldo_bruto)},
            {"Concepto": "(=) Base Gravable", "Monto": gravado},
            {"Concepto": "(-) ISR a Retener", "Monto": isr_retener},
            {"Concepto": "(=) NETO A PAGAR", "Monto": neto}
        ])
        st.dataframe(df_agui.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
        
    with col_vis:
        st.markdown("#### 💡 ¿Sabías qué?")
        st.info(f"El SAT te 'regala' libres de impuestos hasta 30 UMAS (${exento:,.2f}). Solo pagas por la diferencia.")


# ==============================================================================
# MÓDULO 3: FINIQUITO Y LIQUIDACIÓN
# ==============================================================================
elif modulo == "Finiquito y Liquidación":
    with st.sidebar:
        st.header("⚖️ Cálculo de Salida")
        with st.container(border=True):
            causa = st.selectbox("Motivo", ["Renuncia Voluntaria", "Despido Injustificado"])
            f_alta = st.date_input("Fecha Alta", date(2022, 1, 1))
            f_baja = st.date_input("Fecha Baja", date.today())
            sueldo_men = st.number_input("Sueldo Mensual Bruto", 25000.0)

        with st.container(border=True):
            st.markdown("##### Prestaciones Pendientes")
            # AUTOMATIZACIÓN DE DÍAS AGUINALDO
            inicio_anio_baja = date(f_baja.year, 1, 1)
            fecha_inicio_calculo = max(f_alta, inicio_anio_baja)
            dias_trabajados_anio = (f_baja - fecha_inicio_calculo).days + 1
            prop_dias_aguinaldo = (dias_trabajados_anio / 365) * 15 # Asumiendo 15 ley
            
            st.info(f"📅 Días trabajados año: {dias_trabajados_anio}")
            st.info(f"🎁 Aguinaldo proporcional: {prop_dias_aguinaldo:.2f} días")
            
            dias_vac_pend = st.number_input("Días Vacaciones Pendientes", value=6.0)

        st.button("CALCULAR LIQUIDACIÓN", type="primary", use_container_width=True)

    # 1. CÁLCULOS BASE
    antiguedad_dias = (f_baja - f_alta).days + 1
    anios_completos = antiguedad_dias // 365
    sd = sueldo_men / 30
    
    # SDI
    dias_vac_antig = 14 if anios_completos >= 1 else 12
    factor_int = 1 + ((15 + (dias_vac_antig*0.25))/365)
    sdi = sd * factor_int

    # 2. FINIQUITO
    monto_aguinaldo = prop_dias_aguinaldo * sd
    monto_vac = dias_vac_pend * sd
    monto_prima_vac = monto_vac * 0.25
    tope_prima = 2 * VALORES_2026["SALARIO_MINIMO"]
    base_prima = min(sd, tope_prima)
    prima_antiguedad = 0
    
    if causa == "Despido Injustificado" or anios_completos >= 15:
        prima_antiguedad = (antiguedad_dias / 365) * 12 * base_prima

    # 3. LIQUIDACIÓN
    indemnizacion = 0
    veinte_dias = 0
    if causa == "Despido Injustificado":
        indemnizacion = 3 * 30 * sdi
        veinte_dias = 20 * (antiguedad_dias / 365) * sdi

    # 4. IMPUESTOS
    _, desglose_isr_men = calcular_isr_engine(sueldo_men, TABLA_ISR_MENSUAL)
    tasa_marginal = desglose_isr_men["Tasa"]

    # Exenciones
    ex_agui = min(monto_aguinaldo, 30*VALORES_2026["UMA"])
    ex_pv = min(monto_prima_vac, 15*VALORES_2026["UMA"])
    tope_90_umas = 90 * VALORES_2026["UMA"] * anios_completos
    total_separacion = prima_antiguedad + indemnizacion + veinte_dias
    ex_separacion = min(total_separacion, tope_90_umas)
    
    # ISR Finiquito
    gravado_finiquito = (monto_aguinaldo - ex_agui) + (monto_prima_vac - ex_pv) + monto_vac
    isr_finiquito = gravado_finiquito * tasa_marginal
    
    # ISR Liquidación
    gravado_separacion = total_separacion - ex_separacion
    isr_mes_ordinario, _ = calcular_isr_engine(sueldo_men, TABLA_ISR_MENSUAL)
    tasa_efectiva_sep = isr_mes_ordinario / sueldo_men
    isr_separacion = gravado_separacion * tasa_efectiva_sep
    
    total_pagar = (total_separacion + monto_aguinaldo + monto_vac + monto_prima_vac)
    total_isr = isr_finiquito + isr_separacion
    total_neto = total_pagar - total_isr

    # DASHBOARD SALIDA
    st.markdown(f"### ⚖️ Hoja de Liquidación: {causa}")
    
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Gran Total Bruto</div><div class="kpi-value">${total_pagar:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR Total</div><div class="kpi-value neon-red">-${total_isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Entregar</div><div class="kpi-value neon-green">${total_neto:,.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # TABLA CONSOLIDADA
    st.markdown("#### 📋 Desglose Detallado por Concepto")
    
    detalle_data = [
        {"Concepto": "Aguinaldo Proporcional", "Bruto": monto_aguinaldo, "Exento": ex_agui, "ISR Aprox": (monto_aguinaldo-ex_agui)*tasa_marginal},
        {"Concepto": "Vacaciones Pendientes", "Bruto": monto_vac, "Exento": 0, "ISR Aprox": monto_vac*tasa_marginal},
        {"Concepto": "Prima Vacacional", "Bruto": monto_prima_vac, "Exento": ex_pv, "ISR Aprox": (monto_prima_vac-ex_pv)*tasa_marginal},
    ]
    
    separacion_bruto = prima_antiguedad + indemnizacion + veinte_dias
    if separacion_bruto > 0:
        detalle_data.append({
            "Concepto": "Pagos por Separación (Liq + Antig)", 
            "Bruto": separacion_bruto, 
            "Exento": ex_separacion, 
            "ISR Aprox": isr_separacion
        })

    df_detalle = pd.DataFrame(detalle_data)
    df_detalle["Neto"] = df_detalle["Bruto"] - df_detalle["ISR Aprox"]
    
    st.dataframe(
        df_detalle.style.format({
            "Bruto": "${:,.2f}", "Exento": "${:,.2f}", "ISR Aprox": "${:,.2f}", "Neto": "${:,.2f}"
        }), 
        use_container_width=True, 
        hide_index=True
    )
