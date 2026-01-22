import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Nómina 2026: Auditoría Total", page_icon="🕵️", layout="wide")

# --- 1. CONSTANTES OFICIALES 2026 ---
VALORES_2026 = {
    "UMA_DIARIA": 117.31,
    "SALARIO_MINIMO": 315.04,
    "SALARIO_MINIMO_FN": 440.87,
    "TOPE_IMSS_UMAS": 25,
    "PRIMA_VACACIONAL_TASA": 0.25  # 25% de ley
}

TABLA_ISR_MENSUAL = [
    [0.01, 0.00, 0.0192],
    [746.05, 14.32, 0.0640],
    [6332.06, 371.83, 0.1088],
    [11128.02, 893.63, 0.1600],
    [12935.83, 1182.88, 0.1792],
    [15487.72, 1640.18, 0.2136],
    [31236.46, 5004.12, 0.2352],
    [49233.01, 9236.89, 0.3000],
    [93993.91, 22665.17, 0.3200],
    [125325.21, 32691.18, 0.3400],
    [375975.62, 117912.32, 0.3500]
]

# --- 2. LÓGICA DE NEGOCIO ---

def obtener_datos_antiguedad(anios_cumplidos):
    """
    Define días de vacaciones según LFT y Factor de Integración.
    Corrección: Si tienes 1 año cumplido, cotizas con prestaciones del año 2.
    """
    if anios_cumplidos == 0: dias_vac = 12
    elif anios_cumplidos == 1: dias_vac = 14
    elif anios_cumplidos == 2: dias_vac = 16
    elif anios_cumplidos == 3: dias_vac = 18
    elif anios_cumplidos == 4: dias_vac = 20
    elif 5 <= anios_cumplidos <= 9: dias_vac = 22
    elif 10 <= anios_cumplidos <= 14: dias_vac = 24
    else: dias_vac = 26
    
    dias_aguinaldo = 15
    prima_tasa = VALORES_2026["PRIMA_VACACIONAL_TASA"]
    
    # FÓRMULA DEL FACTOR DE INTEGRACIÓN
    # (Días Aguinaldo + (Días Vacaciones * Prima)) / 365
    numerador = dias_aguinaldo + (dias_vac * prima_tasa)
    factor = 1 + (numerador / 365)
    
    return factor, dias_vac, dias_aguinaldo

def calcular_desglose_imss(sbc, dias_cotizados):
    uma = VALORES_2026["UMA_DIARIA"]
    
    # Cálculos por rama
    exc_3uma_base = max(0, sbc - (3*uma))
    cuota_exc = exc_3uma_base * 0.004 * dias_cotizados
    
    cuota_dinero = sbc * 0.0025 * dias_cotizados
    cuota_medicos = sbc * 0.00375 * dias_cotizados
    cuota_invalidez = sbc * 0.00625 * dias_cotizados
    cuota_cesantia = sbc * 0.01125 * dias_cotizados
    
    total = cuota_exc + cuota_dinero + cuota_medicos + cuota_invalidez + cuota_cesantia
    
    # DataFrame para la tabla bonita
    df = pd.DataFrame({
        "Concepto IMSS": [
            "Enf. y Mat. (Excedente)", 
            "Prestaciones en Dinero", 
            "Gastos Médicos Pens.", 
            "Invalidez y Vida", 
            "Cesantía y Vejez"
        ],
        "Base Diario": [f"${exc_3uma_base:,.2f}", f"${sbc:,.2f}", f"${sbc:,.2f}", f"${sbc:,.2f}", f"${sbc:,.2f}"],
        "Cuota ($)": [cuota_exc, cuota_dinero, cuota_medicos, cuota_invalidez, cuota_cesantia]
    })
    return total, df

def calcular_desglose_isr(base_gravable):
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_gravable >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break
            
    excedente = base_gravable - limite
    marginal = excedente * porc
    isr = marginal + cuota
    
    df = pd.DataFrame({
        "Operación ISR": [
            "1. Base Gravable", 
            "2. (-) Límite Inferior", 
            "3. (=) Excedente", 
            "4. (x) Tasa %", 
            "5. (=) Impuesto Marginal", 
            "6. (+) Cuota Fija", 
            "7. (=) ISR Determinado"
        ],
        "Monto": [base_gravable, limite, excedente, porc, marginal, cuota, isr]
    })
    return isr, df

# --- 3. INTERFAZ ---
st.title("🕵️ Nómina 2026: Auditoría Detallada")

with st.sidebar:
    st.header("1. Configuración de Pago")
    sueldo_bruto = st.number_input("Sueldo Mensual Bruto", value=25000.0, step=100.0)
    periodo = st.selectbox("Frecuencia", ["Quincenal", "Mensual", "Semanal"])
    criterio_dias = st.radio("Días del Mes (Criterio)", ["Técnico (30.4)", "Comercial (30)"])
    
    st.markdown("---")
    st.header("2. Antigüedad")
    col_a, col_m = st.columns(2)
    with col_a: anios = st.number_input("Años", 0, 40, 1)
    with col_m: meses = st.number_input("Meses", 0, 11, 0)
    
    st.markdown("---")
    if st.button("CALCULAR DESGLOSE ▶️", type="primary"):
        st.session_state.run = True

# --- 4. PROCESAMIENTO ---
if "run" in st.session_state:
    
    # A. DEFINICIÓN DE TIEMPOS
    dias_mes = 30.4 if criterio_dias == "Técnico (30.4)" else 30
    
    if periodo == "Mensual": dias_periodo = dias_mes
    elif periodo == "Quincenal": dias_periodo = dias_mes / 2
    elif periodo == "Semanal": dias_periodo = dias_mes / (30.4/7) # Aprox 7 días ajustados
    if periodo == "Semanal" and criterio_dias == "Comercial (30)": dias_periodo = 7 # Ajuste forzado comercial
    
    factor_proyeccion = dias_mes / dias_periodo
    
    # B. CÁLCULO SBC
    sueldo_diario = sueldo_bruto / dias_mes
    factor_int, dias_vac, dias_agui = obtener_datos_antiguedad(anios)
    sbc = sueldo_diario * factor_int
    
    # Tope UMA
    tope = VALORES_2026["UMA_DIARIA"] * 25
    sbc_real = min(sbc, tope)
    
    # C. CÁLCULO IMPUESTOS (MENSUALIZADOS)
    # IMSS
    imss_mes, df_imss = calcular_desglose_imss(sbc_real, dias_mes)
    imss_periodo = imss_mes / factor_proyeccion
    
    # ISR
    base_isr_mes = sueldo_diario * dias_mes
    isr_mes, df_isr = calcular_desglose_isr(base_isr_mes)
    isr_periodo = isr_mes / factor_proyeccion
    
    # D. RESULTADOS FINALES
    bruto_periodo = sueldo_bruto / factor_proyeccion
    neto_periodo = bruto_periodo - isr_periodo - imss_periodo
    
    # --- VISUALIZACIÓN ---
    
    # 1. TARJETAS DE RESUMEN
    st.success(f"Cálculo para: **{anios} años, {meses} meses** | Criterio: **{criterio_dias}**")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sueldo Bruto", f"${bruto_periodo:,.2f}")
    k2.metric("ISR", f"-${isr_periodo:,.2f}", delta_color="inverse")
    k3.metric("IMSS", f"-${imss_periodo:,.2f}", delta_color="inverse")
    k4.metric("NETO A PAGAR", f"${neto_periodo:,.2f}", delta_color="normal")
    
    st.divider()
    
    # 2. SISTEMA DE PESTAÑAS (Aquí está la magia)
    tab1, tab2, tab3 = st.tabs(["📊 Resumen & Factores", "🏥 Desglose IMSS", "⚖️ Auditoría ISR"])
    
    with tab1:
        c_graf, c_dato = st.columns([1, 1])
        with c_graf:
            d = pd.DataFrame({'Concepto':['Neto','ISR','IMSS'], 'Monto':[neto_periodo, isr_periodo, imss_periodo]})
            chart = alt.Chart(d).mark_arc(innerRadius=50).encode(theta="Monto", color="Concepto", tooltip=["Concepto", "Monto"])
            st.altair_chart(chart, use_container_width=True)
            
        with c_dato:
            st.subheader("¿Cómo se integra tu salario?")
            st.write(f"**Sueldo Diario:** ${sueldo_diario:,.2f}")
            st.write(f"**SBC (Base Cotización):** ${sbc_real:,.2f}")
            st.write(f"**Factor Integración:** {factor_int:.6f}")
            st.info(f"""
            **Tus Prestaciones (Año {anios+1}):**
            * 🏖️ Vacaciones: **{dias_vac} días**
            * 💰 Prima Vacacional: **25%** (Considerada en Factor)
            * 🎄 Aguinaldo: **{dias_agui} días**
            """)

    with tab2:
        st.subheader(f"Detalle de Cuotas IMSS ({periodo})")
        # Ajustamos la tabla mensual al periodo para que cuadre con el descuento
        df_imss["Cuota ($)"] = df_imss["Cuota ($)"] / factor_proyeccion
        st.dataframe(df_imss.style.format({"Cuota ($)": "${:,.2f}"}), hide_index=True, use_container_width=True)
        st.caption("*Estas cuotas son las que le corresponden al trabajador (Obreras).")

    with tab3:
        st.subheader("Cálculo del ISR (Mensual Proyectado)")
        # Función para formatear bonito
        def fmt(x): return f"{x*100:.2f}%" if x < 1 and x > 0 else f"${x:,.2f}"
        
        st.table(df_isr.assign(Monto=df_isr["Monto"].apply(fmt)))
        st.success(f"ISR Mensual: ${isr_mes:,.2f} ÷ Factor {factor_proyeccion:.2f} = **${isr_periodo:,.2f}** a retener.")

else:
    st.info("👈 Configura la nómina en el menú lateral.")
