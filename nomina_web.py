import streamlit as st
import pandas as pd
import altair as alt
import os
from datetime import date, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Nominapp MX | Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATOS OFICIALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO_GENERAL": 315.04,
    "SALARIO_MINIMO_ZLFN": 440.87,
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
    .stApp { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid #334155; }
    .dark-card { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3); }
    .insight-card { background-color: #1e293b; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155; }
    h1, h2, h3, h4 { color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    p, li, label, .stMarkdown { color: #cbd5e1 !important; }
    .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stRadio label { background-color: #0f172a !important; color: white !important; border: 1px solid #475569 !important; }
    .kpi-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; }
    .kpi-value { font-size: 2.2rem; font-weight: 800; color: #ffffff; font-family: 'Roboto', sans-serif; }
    .neon-green { color: #34d399 !important; } .neon-red { color: #f87171 !important; } .neon-gold { color: #fbbf24 !important; } .neon-blue { color: #60a5fa !important; } .neon-purple { color: #a78bfa !important; }
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
    return isr, {"Límite": limite, "Excedente": excedente, "Tasa (%)": porc, "Impuesto Marginal": marginal, "Cuota Fija": cuota, "ISR Determinado": isr}

def calcular_imss_obrero(sbc, dias):
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

def calcular_imss_patronal(sbc, dias, prima_riesgo):
    uma = VALORES_2026["UMA"]
    exc = max(0, sbc - (3*uma))
    veces_uma = sbc / uma
    if veces_uma <= 1.0: tasa_cyv = 0.0315
    elif veces_uma <= 1.5: tasa_cyv = 0.0420
    elif veces_uma <= 2.0: tasa_cyv = 0.0655
    elif veces_uma <= 2.5: tasa_cyv = 0.0796
    elif veces_uma <= 3.0: tasa_cyv = 0.0937
    elif veces_uma <= 3.5: tasa_cyv = 0.1077
    elif veces_uma <= 4.0: tasa_cyv = 0.11875
    else: tasa_cyv = 0.11875
    conceptos = {
        "Cuota Fija": (uma * 0.204) * dias,
        "Excedente 3 UMA": exc * 0.011 * dias,
        "Prest. Dinero": sbc * 0.007 * dias,
        "Gastos Médicos": sbc * 0.0105 * dias,
        "Riesgo Trabajo": sbc * (prima_riesgo/100) * dias,
        "Invalidez y Vida": sbc * 0.0175 * dias,
        "Guarderías": sbc * 0.01 * dias,
        "Retiro (SAR)": sbc * 0.02 * dias,
        "Cesantía y Vejez": sbc * tasa_cyv * dias,
        "Infonavit": sbc * 0.05 * dias
    }
    return sum(conceptos.values()), conceptos

def obtener_dias_vacaciones_ley(anios_antiguedad):
    """Tabla de vacaciones dignas 2026"""
    anios = int(anios_antiguedad)
    if anios < 1: return 12 # Proporcional de 12
    if anios == 1: return 12
    if anios == 2: return 14
    if anios == 3: return 16
    if anios == 4: return 18
    if anios == 5: return 20
    if 6 <= anios <= 10: return 22
    if 11 <= anios <= 15: return 24
    if 16 <= anios <= 20: return 26
    if 21 <= anios <= 25: return 28
    if 26 <= anios <= 30: return 30
    return 32

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("nominapp_logo.png"):
        st.image("nominapp_logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 Nominapp MX")
    
    st.markdown("---")
    
    zona_geo = st.selectbox("🌍 Zona Geográfica", ["Resto del País", "Frontera Norte (ZLFN)"])
    if zona_geo == "Resto del País":
        sm_aplicable = VALORES_2026["SALARIO_MINIMO_GENERAL"]
    else:
        sm_aplicable = VALORES_2026["SALARIO_MINIMO_ZLFN"]
    st.caption(f"Salario Mínimo Zona: **${sm_aplicable:.2f}**")
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
            st.markdown("##### 💵 Ingreso del Periodo")
            tipo_ingreso = st.radio("Base", ["Bruto Mensual", "Por Periodo"], horizontal=True)
            monto_input = st.number_input("Monto ($)", value=25000.0, step=500.0, format="%.2f")
            if tipo_ingreso == "Bruto Mensual": sueldo_diario = monto_input / dias_mes_base
            else: sueldo_diario = monto_input / dias_pago
            
            st.markdown("##### 🔄 Ajuste de Impuestos")
            es_ajuste = st.toggle("¿Es cierre de mes (Ajuste)?", value=False)
            ingreso_acumulado_prev = 0.0
            isr_retenido_prev = 0.0
            if es_ajuste:
                st.info("Ingresa los datos previos del mes:")
                ingreso_acumulado_prev = st.number_input("Ingresos Gravados Previos", value=0.0)
                isr_retenido_prev = st.number_input("ISR Retenido Previo", value=0.0)

        with st.container(border=True):
            st.markdown("##### 🏢 Datos Patronales")
            prima_riesgo = st.number_input("Prima Riesgo Trabajo %", value=0.50000, step=0.1, format="%.5f")
            tasa_isn = st.number_input("Tasa ISN (Estatal) %", value=3.0, step=0.5)
            antig = st.number_input("Años Antigüedad", 1)
        
        st.button("CALCULAR NÓMINA", type="primary", use_container_width=True)

    dias_vac = obtener_dias_vacaciones_ley(antig)
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    bruto_periodo = sueldo_diario * dias_pago
    imss_obrero, df_imss_obr = calcular_imss_obrero(sbc, dias_pago)
    
    es_salario_minimo = False
    desglose_isr_men = {}
    
    if sueldo_diario <= (sm_aplicable + 1.0):
        es_salario_minimo = True
        isr_periodo = 0.0
        base_mensual_proy = sueldo_diario * dias_mes_base
        _, desglose_isr_men = calcular_isr_engine(base_mensual_proy, TABLA_ISR_MENSUAL)
    else:
        if es_ajuste:
            total_ingreso_mensual = ingreso_acumulado_prev + bruto_periodo
            isr_total_mes, desglose_isr_men = calcular_isr_engine(total_ingreso_mensual, TABLA_ISR_MENSUAL)
            isr_periodo = isr_total_mes - isr_retenido_prev
        else:
            base_mensual_proy = sueldo_diario * dias_mes_base
            isr_mensual_proy, desglose_isr_men = calcular_isr_engine(base_mensual_proy, TABLA_ISR_MENSUAL)
            isr_periodo = isr_mensual_proy * (dias_pago / dias_mes_base)

    neto = bruto_periodo - imss_obrero - isr_periodo
    imss_patronal, df_imss_pat = calcular_imss_patronal(sbc, dias_pago, prima_riesgo)
    isn = bruto_periodo * (tasa_isn / 100)
    costo_total = bruto_periodo + imss_patronal + isn

    titulo_kpi = "Nómina con Ajuste Mensual" if es_ajuste else f"Nómina: {periodo}"
    st.markdown(f"### 📊 {titulo_kpi}")
    
    if es_salario_minimo:
        st.success(f"✅ **Salario Mínimo ({zona_geo}) Detectado:** ISR Exento por Ley.")

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Ingreso Bruto</div><div class="kpi-value">${bruto_periodo:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR ({'Ajustado' if es_ajuste else 'Retención'})</div><div class="kpi-value neon-red">-${isr_periodo:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card"><div class="kpi-label">IMSS (Cuota)</div><div class="kpi-value neon-gold">-${imss_obrero:,.2f}</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Recibir</div><div class="kpi-value neon-green">${neto:,.2f}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    active_tabs = st.tabs(["🧠 Insights", "🏛️ Desglose ISR", "🏥 IMSS Obrero", "🏢 Costo Empresa"])
    
    with active_tabs[0]:
        col_g, col_i = st.columns([1, 2])
        with col_g:
            source = pd.DataFrame({"Rubro": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr_periodo, imss_obrero]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=70, outerRadius=110).encode(
                color=alt.Color("Rubro", scale=alt.Scale(range=['#34d399', '#60a5fa', '#fbbf24']), legend=alt.Legend(orient="bottom", titleColor="white", labelColor="white")),
                tooltip=["Rubro", alt.Tooltip("Monto", format="$,.2f")]
            ).configure_view(strokeWidth=0).configure(background='transparent')
            st.altair_chart(pie, use_container_width=True)
        with col_i:
            horas = dias_pago * 8
            valor_hora = neto / horas
            meses_gob = ((isr_periodo+imss_obrero)/bruto_periodo) * 12 if bruto_periodo > 0 else 0
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

    with active_tabs[1]:
        st.markdown("#### 🔍 Auditoría de Cálculo ISR")
        if not es_salario_minimo:
            tasa_marginal = desglose_isr_men.get("Tasa (%)", 0) * 100
            tasa_efectiva = (isr_periodo / bruto_periodo) * 100 if bruto_periodo > 0 else 0
            st.markdown(f"""
            <div style="display:flex; gap:20px; margin-bottom:20px;">
                <div class="insight-card" style="flex:1; text-align:center; border-left-color: #fbbf24;">
                    <span style="color:#94a3b8; font-size:0.8em; font-weight:700;">TASA MARGINAL</span><br>
                    <span style="font-size:1.8em; font-weight:800; color:#fbbf24;">{tasa_marginal:.1f}%</span>
                </div>
                <div class="insight-card" style="flex:1; text-align:center; border-left-color: #34d399;">
                    <span style="color:#94a3b8; font-size:0.8em; font-weight:700;">TASA EFECTIVA</span><br>
                    <span style="font-size:1.8em; font-weight:800; color:#34d399;">{tasa_efectiva:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            audit_data = [
                {"Paso": "1. Base Mensual", "Monto": desglose_isr_men.get("Base Mensual", 0)},
                {"Paso": "2. (-) Límite Inferior", "Monto": desglose_isr_men.get("Límite Inferior", 0)},
                {"Paso": "3. (=) Excedente", "Monto": desglose_isr_men.get("Excedente", 0)},
                {"Paso": f"4. (x) Tasa ({tasa_marginal:.2f}%)", "Monto": desglose_isr_men.get("Impuesto Marginal", 0)},
                {"Paso": "5. (+) Cuota Fija", "Monto": desglose_isr_men.get("Cuota Fija", 0)},
                {"Paso": "6. (=) ISR Mensual", "Monto": desglose_isr_men.get("ISR Determinado", 0)},
            ]
            if not es_ajuste:
                audit_data.append({"Paso": f"7. (x) Factor Días ({dias_pago}/{dias_mes_base})", "Monto": isr_periodo})
            
            df_audit = pd.DataFrame(audit_data)
            st.dataframe(df_audit.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("No aplica desglose por Salario Mínimo.")

    with active_tabs[2]:
        st.markdown("#### 🏥 Distribución IMSS")
        imss_salud = df_imss_obr["Enfermedad (Exc)"] + df_imss_obr["Prest. Dinero"] + df_imss_obr["Gastos Médicos"]
        imss_futuro = df_imss_obr["Invalidez y Vida"] + df_imss_obr["Cesantía y Vejez"]
        st.markdown(f"""
        <div style="display:flex; gap:20px; margin-bottom:20px;">
            <div class="insight-card" style="flex:1; border-left-color: #60a5fa;">
                <span style="color:#60a5fa; font-weight:700;">🩺 SALUD HOY</span><br>
                <span style="font-size:1.4em; font-weight:800; color:white;">${imss_salud:,.2f}</span>
            </div>
            <div class="insight-card" style="flex:1; border-left-color: #a78bfa;">
                <span style="color:#a78bfa; font-weight:700;">👴 TU FUTURO</span><br>
                <span style="font-size:1.4em; font-weight:800; color:white;">${imss_futuro:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        df_obr = pd.DataFrame(list(df_imss_obr.items()), columns=["Concepto", "Monto"])
        st.dataframe(df_obr.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)
        
    with active_tabs[3]:
        st.markdown("#### 🏢 Costo Real para la Empresa")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1: st.metric("Sueldo Bruto", f"${bruto_periodo:,.2f}")
        with c_p2: st.metric("Carga Social", f"${imss_patronal+isn:,.2f}", delta=f"{((imss_patronal+isn)/bruto_periodo)*100:.1f}% Extra", delta_color="inverse")
        with c_p3: st.metric("Costo Total", f"${costo_total:,.2f}")
        df_pat = pd.DataFrame(list(df_imss_pat.items()), columns=["Concepto Patronal", "Monto"])
        df_pat.loc[len(df_pat)] = ["Impuesto Sobre Nómina (ISN)", isn]
        st.dataframe(df_pat.style.format({"Monto": "${:,.2f}"}), use_container_width=True, hide_index=True)

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

    sd = sueldo_mensual / 30
    aguinaldo_bruto = (dias_trabajados/365) * dias_ley * sd
    exento = 30 * VALORES_2026["UMA"]
    gravado = max(0, aguinaldo_bruto - exento)
    isr_base, _ = calcular_isr_engine(sueldo_mensual, TABLA_ISR_MENSUAL)
    isr_total, _ = calcular_isr_engine(sueldo_mensual + gravado, TABLA_ISR_MENSUAL)
    isr_retener = isr_total - isr_base
    neto = aguinaldo_bruto - isr_retener

    st.markdown("### 🎄 Resultado de Aguinaldo")
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
        st.info(f"El SAT te 'regala' libres de impuestos hasta 30 UMAS (${exento:,.2f}).")

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
            # CÁLCULO AUTOMÁTICO DE PROPORCIONALES
            antiguedad_dias_total = (f_baja - f_alta).days + 1
            anios_completos = int(antiguedad_dias_total / 365.25)
            
            # Aguinaldo Prop: Días del año en curso
            inicio_anio_baja = date(f_baja.year, 1, 1)
            fecha_inicio_ag = max(f_alta, inicio_anio_baja)
            dias_ag_trab = (f_baja - fecha_inicio_ag).days + 1
            prop_agui = (dias_ag_trab / 365) * 15 # Ley
            
            # Vacaciones Prop: Días desde último aniversario
            # Fecha último aniversario:
            fecha_aniversario = date(f_baja.year, f_alta.month, f_alta.day)
            if fecha_aniversario > f_baja:
                fecha_aniversario = date(f_baja.year - 1, f_alta.month, f_alta.day)
            
            dias_desde_aniversario = (f_baja - fecha_aniversario).days + 1
            dias_ley_tocan = obtener_dias_vacaciones_ley(anios_completos + 1) # Del año que corre
            prop_vac = (dias_desde_aniversario / 365) * dias_ley_tocan
            
            st.info(f"🎁 Aguinaldo Prop: {prop_agui:.2f} días")
            st.info(f"🏖️ Vacaciones Prop: {prop_vac:.2f} días ({dias_ley_tocan} ley)")
            
            dias_vac_no_gozadas = st.number_input("Días Vacaciones Años Anteriores (No gozadas)", value=0.0)
            total_dias_vac = prop_vac + dias_vac_no_gozadas

        st.button("CALCULAR LIQUIDACIÓN", type="primary", use_container_width=True)

    sd = sueldo_men / 30
    factor_int = 1 + ((15 + (dias_ley_tocan*0.25))/365)
    sdi = sd * factor_int

    monto_aguinaldo = prop_agui * sd
    monto_vac = total_dias_vac * sd
    monto_prima_vac = monto_vac * 0.25
    
    tope_prima = 2 * sm_aplicable
    base_prima = min(sd, tope_prima)
    prima_antiguedad = 0
    if causa == "Despido Injustificado" or anios_completos >= 15:
        prima_antiguedad = (antiguedad_dias_total / 365) * 12 * base_prima

    indemnizacion = 0
    veinte_dias = 0
    if causa == "Despido Injustificado":
        indemnizacion = 3 * 30 * sdi
        veinte_dias = 20 * (antiguedad_dias_total / 365) * sdi

    # IMPUESTOS
    _, desglose_isr_men = calcular_isr_engine(sueldo_men, TABLA_ISR_MENSUAL)
    tasa_marginal = desglose_isr_men["Tasa (%)"]

    ex_agui = min(monto_aguinaldo, 30*VALORES_2026["UMA"])
    ex_pv = min(monto_prima_vac, 15*VALORES_2026["UMA"])
    tope_90_umas = 90 * VALORES_2026["UMA"] * anios_completos
    total_separacion = prima_antiguedad + indemnizacion + veinte_dias
    ex_separacion = min(total_separacion, tope_90_umas)
    
    # ISR Finiquito (Simplificado)
    isr_finiquito = ((monto_aguinaldo - ex_agui) + (monto_prima_vac - ex_pv) + monto_vac) * tasa_marginal
    
    # ISR Liquidación (Tasa Efectiva)
    gravado_sep = total_separacion - ex_separacion
    isr_ord_men, _ = calcular_isr_engine(sueldo_men, TABLA_ISR_MENSUAL)
    tasa_efectiva = isr_ord_men / sueldo_men if sueldo_men > 0 else 0
    isr_separacion = gravado_sep * tasa_efectiva
    
    total_pagar = total_separacion + monto_aguinaldo + monto_vac + monto_prima_vac
    total_isr = isr_finiquito + isr_separacion
    total_neto = total_pagar - total_isr

    st.markdown(f"### ⚖️ Hoja de Liquidación: {causa}")
    k1, k2, k3 = st.columns(3)
    with k1: st.markdown(f"""<div class="dark-card"><div class="kpi-label">Gran Total Bruto</div><div class="kpi-value">${total_pagar:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="dark-card"><div class="kpi-label">ISR Total</div><div class="kpi-value neon-red">-${total_isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="dark-card" style="border: 1px solid #34d399;"><div class="kpi-label neon-green">Neto a Entregar</div><div class="kpi-value neon-green">${total_neto:,.2f}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📋 Desglose Detallado por Concepto")
    
    detalle_data = [
        {"Concepto": "Aguinaldo Proporcional", "Bruto": monto_aguinaldo, "Exento": ex_agui, "ISR Aprox": (monto_aguinaldo-ex_agui)*tasa_marginal},
        {"Concepto": "Vacaciones (Prop + Pend)", "Bruto": monto_vac, "Exento": 0, "ISR Aprox": monto_vac*tasa_marginal},
        {"Concepto": "Prima Vacacional", "Bruto": monto_prima_vac, "Exento": ex_pv, "ISR Aprox": (monto_prima_vac-ex_pv)*tasa_marginal},
    ]
    if total_separacion > 0:
        detalle_data.append({"Concepto": "Pagos por Separación (Liq + Antig)", "Bruto": total_separacion, "Exento": ex_separacion, "ISR Aprox": isr_separacion})

    df_detalle = pd.DataFrame(detalle_data)
    df_detalle["Neto"] = df_detalle["Bruto"] - df_detalle["ISR Aprox"]
    st.dataframe(df_detalle.style.format({"Bruto": "${:,.2f}", "Exento": "${:,.2f}", "ISR Aprox": "${:,.2f}", "Neto": "${:,.2f}"}), use_container_width=True, hide_index=True)
