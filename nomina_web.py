import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Nómina 2026 Oficial", page_icon="🇲🇽", layout="wide")

# --- 1. DATOS OFICIALES 2026 (Confirmados) ---
VALORES_2026 = {
    "UMA_DIARIA": 117.31,         # Fuente: INEGI 2026
    "SALARIO_MINIMO": 315.04,     # Fuente: CONASAMI 2026
    "SALARIO_MINIMO_FN": 440.87,  # Zona Frontera
    "TOPE_IMSS_UMAS": 25,
    "PRIMA_VACACIONAL": 0.25
}

# NUEVA TABLA ISR 2026 (Actualizada por inflación >10%)
# Fuente: Anexo 8 RMF 2026
TABLA_ISR_MENSUAL_2026 = [
    # Limite Inf, Cuota Fija, % Excedente
    [0.01,          0.00,       0.0192],
    [844.60,        16.22,      0.0640],
    [7168.52,       420.95,     0.1088],
    [12598.03,      1011.68,    0.1600],
    [14644.65,      1339.14,    0.1792],
    [17533.65,      1856.84,    0.2136],
    [35362.84,      5665.16,    0.2352],
    [55736.69,      10457.09,   0.3000],
    [106410.51,     25659.23,   0.3200],
    [141880.67,     37009.69,   0.3400],
    [425642.00,     133488.54,  0.3500]
]

# --- 2. FUNCIONES DE CÁLCULO (Motor de Nómina) ---

def obtener_factor_integracion(anios, meses):
    """
    Calcula prestaciones según antigüedad real.
    Regla: Si tienes 1 año cumplido, cotizas con prestaciones de año 2.
    """
    anios_efectivos = anios if anios > 0 else 0
    # Ajuste: Si ya cumplió el año, empieza a correr el siguiente escalón
    if anios > 0 or meses > 0: 
        # Si tiene >0 tiempo, validamos en qué escalón de LFT cae
        pass 
    
    # Tabla Vacaciones Dignas (Días por año cumplido o cursando)
    if anios == 0: dias_vac = 12
    elif anios == 1: dias_vac = 14
    elif anios == 2: dias_vac = 16
    elif anios == 3: dias_vac = 18
    elif anios == 4: dias_vac = 20
    elif 5 <= anios <= 9: dias_vac = 22
    elif 10 <= anios <= 14: dias_vac = 24
    else: dias_vac = 26
    
    dias_aguinaldo = 15
    prima_vac = VALORES_2026["PRIMA_VACACIONAL"]
    
    # Factor = 1 + (Proporción diaria de prestaciones)
    factor = 1 + ((dias_aguinaldo + (dias_vac * prima_vac)) / 365)
    return factor, dias_vac

def generar_tabla_periodo(tabla_mensual, dias_pago, dias_mes_base=30.4):
    """
    Ajusta la tabla mensual a quincenal/semanal matemáticamente.
    """
    factor = dias_mes_base / dias_pago
    tabla_ajustada = []
    for renglon in tabla_mensual:
        limite = renglon[0] / factor
        cuota = renglon[1] / factor
        porcentaje = renglon[2]
        tabla_ajustada.append([limite, cuota, porcentaje])
    return tabla_ajustada

def calcular_isr_exacto(sueldo_periodo, tabla_periodo):
    limite, cuota, porc = 0, 0, 0
    for row in tabla_periodo:
        if sueldo_periodo >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break # Se queda con el renglón anterior
            
    excedente = sueldo_periodo - limite
    marginal = excedente * porc
    isr = marginal + cuota
    
    return isr, {
        "Base": sueldo_periodo, "Límite Inf.": limite, 
        "Excedente": excedente, "Tasa": porc, 
        "Cuota Fija": cuota, "ISR": isr
    }

def calcular_imss_periodo(sbc, dias_pago):
    uma = VALORES_2026["UMA_DIARIA"]
    
    # Fórmulas de cuotas obreras 2026
    excedente = max(0, sbc - (3*uma))
    
    cuotas = {
        "Enf. y Mat. (Exc)": excedente * 0.004 * dias_pago,
        "Prest. Dinero": sbc * 0.0025 * dias_pago,
        "Gastos Médicos": sbc * 0.00375 * dias_pago,
        "Invalidez y Vida": sbc * 0.00625 * dias_pago,
        "Cesantía y Vejez": sbc * 0.01125 * dias_pago
    }
    
    total = sum(cuotas.values())
    return total, cuotas

# --- 3. INTERFAZ GRÁFICA ---
st.title("💼 Nómina 2026 (Datos Oficiales)")

with st.sidebar:
    st.header("1. Configuración de Pago")
    monto = st.number_input("Sueldo Bruto", value=15000.0, step=100.0)
    tipo_sueldo = st.radio("El sueldo ingresado es:", ["Mensual", "Quincenal"], horizontal=True)
    periodo_pago = st.selectbox("Frecuencia de Pago", ["Quincenal", "Mensual", "Semanal"])
    
    st.markdown("---")
    st.header("2. Datos Laborales")
    criterio_dias = st.radio("Días de Cálculo", ["Ley (30.4)", "Comercial (30)"])
    col_a, col_m = st.columns(2)
    with col_a: anios = st.number_input("Años", 0, 50, 0)
    with col_m: meses = st.number_input("Meses", 0, 11, 0)
    
    if st.button("CALCULAR NÓMINA ▶️", type="primary"):
        st.session_state.run = True

# --- 4. LÓGICA DE EJECUCIÓN ---
if "run" in st.session_state:
    
    # A. Normalizar tiempos
    dias_mes = 30.4 if criterio_dias == "Ley (30.4)" else 30.0
    
    if periodo_pago == "Mensual": dias_periodo = dias_mes
    elif periodo_pago == "Quincenal": dias_periodo = dias_mes / 2
    elif periodo_pago == "Semanal": dias_periodo = 7
    
    # B. Determinar Sueldo Diario y del Periodo
    if tipo_sueldo == "Mensual":
        sueldo_diario = monto / dias_mes
        sueldo_periodo = sueldo_diario * dias_periodo
    else: # Quincenal
        # Si ingresó 10k quincenales, mensual es 20k aprox (según criterio)
        sueldo_periodo_input = monto
        factor_conv = dias_mes / (dias_mes/2) # ~2
        sueldo_diario = (sueldo_periodo_input * factor_conv) / dias_mes
        sueldo_periodo = sueldo_diario * dias_periodo

    # C. Validar Salario Mínimo 2026
    minimo = VALORES_2026["SALARIO_MINIMO"]
    if sueldo_diario < minimo:
        st.error(f"⚠️ El sueldo diario (${sueldo_diario:.2f}) es menor al Mínimo 2026 (${minimo}). Ajustando cálculo al mínimo.")
        sueldo_diario = minimo
        sueldo_periodo = sueldo_diario * dias_periodo

    # D. Calcular SBC
    factor_int, dias_vac = obtener_factor_integracion(anios, meses)
    sbc = sueldo_diario * factor_int
    sbc_tope = min(sbc, VALORES_2026["UMA_DIARIA"] * 25)

    # E. Calcular Impuestos
    # 1. IMSS
    imss_total, desglose_imss = calcular_imss_periodo(sbc_tope, dias_periodo)
    
    # 2. ISR (Tabla Ajustada)
    tabla_ajustada = generar_tabla_periodo(TABLA_ISR_MENSUAL_2026, dias_periodo, dias_mes)
    isr_total, desglose_isr = calcular_isr_exacto(sueldo_periodo, tabla_ajustada)
    
    neto = sueldo_periodo - imss_total - isr_total
    
    # --- RESULTADOS ---
    st.success(f"Cálculo con Tablas 2026 Actualizadas (Límite Inf. Mensual: ${TABLA_ISR_MENSUAL_2026[1][0]:,.2f})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sueldo Periodo", f"${sueldo_periodo:,.2f}")
    c2.metric("ISR Retenido", f"-${isr_total:,.2f}", delta_color="inverse")
    c3.metric("IMSS Retenido", f"-${imss_total:,.2f}", delta_color="inverse")
    c4.metric("NETO A PAGAR", f"${neto:,.2f}", delta_color="normal")
    
    # Desglose en Pestañas
    tab1, tab2, tab3 = st.tabs(["📊 Resumen", "🏛️ Detalle ISR", "🏥 Detalle IMSS"])
    
    with tab1:
        col_L, col_R = st.columns(2)
        with col_L:
            df_chart = pd.DataFrame({'C':['Neto','ISR','IMSS'], 'V':[neto, isr_total, imss_total]})
            c = alt.Chart(df_chart).mark_arc(innerRadius=60).encode(theta='V', color='C', tooltip=['C','V'])
            st.altair_chart(c, use_container_width=True)
        with col_R:
            st.caption("Datos Técnicos:")
            st.write(f"**UMA 2026:** ${VALORES_2026['UMA_DIARIA']}")
            st.write(f"**Salario Mínimo:** ${minimo}")
            st.write(f"**SBC:** ${sbc_tope:,.2f}")
            st.write(f"**Factor Integración:** {factor_int:.4f}")
            
    with tab2:
        st.subheader(f"Tabla ISR Ajustada ({periodo_pago})")
        st.write("Tu cálculo se realizó sobre esta base:")
        # Mostrar solo los datos relevantes del cálculo
        st.json(desglose_isr)
        
    with tab3:
        st.subheader("Cuotas IMSS Obreras")
        st.dataframe(pd.DataFrame(list(desglose_imss.items()), columns=["Rama", "Monto"]).style.format({"Monto":"${:,.2f}"}), use_container_width=True)
