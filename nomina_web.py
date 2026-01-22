import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Nómina 2026 Master", page_icon="🧮", layout="wide")

# --- 1. CONSTANTES OFICIALES 2026 ---
VALORES_2026 = {
    "UMA_DIARIA": 117.31,
    "SALARIO_MINIMO": 315.04,
    "SALARIO_MINIMO_FN": 440.87,
    "TOPE_IMSS_UMAS": 25
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

def obtener_factor_integracion_corregido(anios_cumplidos):
    """
    CORRECCIÓN: Si tienes 1 año cumplido, cotizas con las prestaciones 
    del 2do año (porque ya estás cursando el 2do).
    """
    if anios_cumplidos == 0: dias_vac = 12
    elif anios_cumplidos == 1: dias_vac = 14  # Ajustado: Antes 12
    elif anios_cumplidos == 2: dias_vac = 16
    elif anios_cumplidos == 3: dias_vac = 18
    elif anios_cumplidos == 4: dias_vac = 20
    elif 5 <= anios_cumplidos <= 9: dias_vac = 22
    elif 10 <= anios_cumplidos <= 14: dias_vac = 24
    else: dias_vac = 26
    
    dias_aguinaldo = 15
    prima_vacacional = 0.25
    
    factor = 1 + ((dias_aguinaldo + (dias_vac * prima_vacacional)) / 365)
    return factor, dias_vac

def calcular_imss(sbc, dias_cotizados):
    uma = VALORES_2026["UMA_DIARIA"]
    # Ramas del seguro (Cuotas Obreras)
    exc_3uma = max(0, sbc - (3*uma)) * 0.004
    prest_dinero = sbc * 0.0025
    gastos_med = sbc * 0.00375
    invalidez = sbc * 0.00625
    cesantia = sbc * 0.01125
    
    cuota_diaria = exc_3uma + prest_dinero + gastos_med + invalidez + cesantia
    return cuota_diaria * dias_cotizados

def calcular_isr(base, tabla):
    limite, cuota, porc = 0, 0, 0
    for row in tabla:
        if base >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break
    return ((base - limite) * porc) + cuota

# --- 3. INTERFAZ ---
st.title("🧮 Nómina 2026: Multicriterio")

with st.sidebar:
    st.header("1. Datos del Puesto")
    sueldo_bruto = st.number_input("Sueldo Mensual Bruto", value=22000.0, step=100.0)
    periodo = st.selectbox("Frecuencia de Pago", ["Quincenal", "Mensual", "Semanal"])
    zona = st.radio("Zona", ["General", "Frontera Norte"], horizontal=True)
    
    st.header("2. Datos Personales")
    antiguedad = st.number_input("Años Cumplidos", 0, 40, 1)
    
    st.markdown("---")
    st.header("3. Configuración Avanzada")
    # EL NUEVO SELECTOR QUE CAMBIA TODO
    criterio_dias = st.radio(
        "Días para cálculo mensual:",
        ["Técnico (30.4)", "Comercial (30)"],
        help="30.4 es exacto anual. 30 es estándar en algunas empresas."
    )
    
    if st.button("Calcular Nómina", type="primary"):
        st.session_state.run_calc = True

# --- 4. PROCESAMIENTO ---
if "run_calc" in st.session_state:
    
    # A. DEFINIR EL DIVISOR SEGÚN CRITERIO
    if criterio_dias == "Técnico (30.4)":
        dias_mes = 30.4
        dias_quincena = 15.2
    else: # Comercial (30)
        dias_mes = 30
        dias_quincena = 15
        
    # B. UNIFICAR SUELDO DIARIO
    # Si pagan 30k al mes y el criterio es 30, diario gana 1000.
    # Si el criterio es 30.4, diario gana 986.
    sueldo_diario = sueldo_bruto / dias_mes
    
    # C. CALCULAR SBC (INTEGRADO)
    factor, dias_vac = obtener_factor_integracion_corregido(antiguedad)
    sbc = sueldo_diario * factor
    
    # Tope 25 UMAS
    tope = VALORES_2026["UMA_DIARIA"] * 25
    sbc_real = min(sbc, tope)
    
    # D. CALCULAR IMPUESTOS (MENSUALIZADOS PRIMERO)
    # IMSS Mensual
    imss_mensual = calcular_imss(sbc_real, dias_mes)
    
    # ISR Mensual
    # Nota: El ISR se calcula sobre la base mensual proyectada
    base_gravable_mes = sueldo_diario * dias_mes
    isr_mensual = calcular_isr(base_gravable_mes, TABLA_ISR_MENSUAL)
    
    # E. AJUSTAR AL PERIODO DE PAGO
    if periodo == "Mensual":
        factor_ajuste = 1
    elif periodo == "Quincenal":
        factor_ajuste = 2 # Divide el mes en 2 pagos
    elif periodo == "Semanal":
        factor_ajuste = dias_mes / 7
        
    pago_bruto = base_gravable_mes / factor_ajuste
    pago_isr = isr_mensual / factor_ajuste
    pago_imss = imss_mensual / factor_ajuste
    pago_neto = pago_bruto - pago_isr - pago_imss
    
    # --- RESULTADOS ---
    st.success(f"Cálculo realizado usando: **Días={dias_mes}** | **Antigüedad={antiguedad} años** (Factor {factor:.4f})")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sueldo Bruto", f"${pago_bruto:,.2f}")
    col2.metric("ISR", f"-${pago_isr:,.2f}", delta_color="inverse")
    col3.metric("IMSS", f"-${pago_imss:,.2f}", delta_color="inverse")
    col4.metric("NETO A PAGAR", f"${pago_neto:,.2f}", delta_color="normal")
    
    # TABLA COMPARATIVA RAPIDA
    st.subheader("Auditoría de Factores")
    st.table(pd.DataFrame({
        "Concepto": ["Sueldo Diario", "SBC (Cotización)", "Días Vacaciones", "Días Aguinaldo"],
        "Valor": [f"${sueldo_diario:,.2f}", f"${sbc_real:,.2f}", dias_vac, 15]
    }))

else:
    st.info("Configura los datos en la izquierda y calcula.")
