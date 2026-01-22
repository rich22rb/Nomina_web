import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json

st.set_page_config(page_title="Nómina 2026: Desglose Total", page_icon="🧾", layout="wide")

# --- 1. DATOS OFICIALES 2026 ---
# Fuente: Proyecciones Económicas y CONASAMI
VALORES_2026 = {
    "UMA_DIARIA": 117.31,        #
    "SALARIO_MINIMO": 315.04,    # Zona General
    "SALARIO_MINIMO_FN": 440.87, # Zona Frontera
    "TOPE_IMSS_UMAS": 25
}

# Tabla ISR (Anexo 8 vigente)
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

# --- 2. FUNCIONES DE CÁLCULO DETALLADO ---

def obtener_factor_integracion(anios):
    # Tabla Vacaciones Dignas
    if anios == 0: dias_vac = 12
    elif anios == 1: dias_vac = 12
    elif anios == 2: dias_vac = 14
    elif anios == 3: dias_vac = 16
    elif anios == 4: dias_vac = 18
    elif 5 <= anios <= 9: dias_vac = 20
    elif 10 <= anios <= 14: dias_vac = 22
    elif 15 <= anios <= 19: dias_vac = 24
    else: dias_vac = 26
    
    dias_aguinaldo = 15
    prima_vacacional = 0.25
    
    # Cálculo del Factor
    numerador = dias_aguinaldo + (dias_vac * prima_vacacional)
    factor = 1 + (numerador / 365)
    
    return factor, dias_vac, dias_aguinaldo

def calcular_desglose_imss(sbc, dias_trabajados):
    """Calcula cuotas obreras concepto por concepto"""
    uma = VALORES_2026["UMA_DIARIA"]
    
    # 1. Enfermedades y Maternidad (Exc. 3 UMA)
    base_exc = max(0, sbc - (3 * uma))
    cuota_exc = base_exc * 0.004 * dias_trabajados
    
    # 2. Prestaciones en Dinero (0.25%)
    cuota_dinero = sbc * 0.0025 * dias_trabajados
    
    # 3. Gastos Médicos Pensionados (0.375%)
    cuota_gmp = sbc * 0.00375 * dias_trabajados
    
    # 4. Invalidez y Vida (0.625%)
    cuota_iv = sbc * 0.00625 * dias_trabajados
    
    # 5. Cesantía y Vejez (1.125%)
    cuota_cv = sbc * 0.01125 * dias_trabajados
    
    total = cuota_exc + cuota_dinero + cuota_gmp + cuota_iv + cuota_cv
    
    # Crear DataFrame para visualización
    df = pd.DataFrame({
        "Rama del Seguro": [
            "Enf. y Mat. (Excedente)", 
            "Prestaciones en Dinero", 
            "Gastos Médicos Pens.", 
            "Invalidez y Vida", 
            "Cesantía y Vejez"
        ],
        "Base de Cálculo": [
            f"${base_exc:,.2f}" if base_exc > 0 else "N/A", 
            f"${sbc:,.2f}", 
            f"${sbc:,.2f}", 
            f"${sbc:,.2f}", 
            f"${sbc:,.2f}"
        ],
        "Tasa (%)": ["0.400%", "0.250%", "0.375%", "0.625%", "1.125%"],
        "Importe a Pagar": [cuota_exc, cuota_dinero, cuota_gmp, cuota_iv, cuota_cv]
    })
    return total, df

def calcular_desglose_isr(base_gravable):
    """Calcula el ISR y devuelve el procedimiento paso a paso"""
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_gravable >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break
            
    excedente = base_gravable - limite
    impuesto_marginal = excedente * porc
    isr_determinado = impuesto_marginal + cuota
    
    df = pd.DataFrame({
        "Concepto": [
            "1. Base Gravable Mensual", 
            "2. (-) Límite Inferior", 
            "3. (=) Excedente", 
            "4. (x) Tasa s/ Excedente", 
            "5. (=) Impuesto Marginal", 
            "6. (+) Cuota Fija", 
            "7. (=) ISR Determinado"
        ],
        "Monto": [
            base_gravable, 
            limite, 
            excedente, 
            porc, # Este formato lo arreglaremos en visualización
            impuesto_marginal, 
            cuota, 
            isr_determinado
        ]
    })
    return isr_determinado, df

# --- 3. INTERFAZ GRÁFICA ---
st.title("🧾 Nómina 2026: Desglose Analítico")
st.markdown("Cálculo exacto con **Salario Mínimo ($315.04)** y **UMA ($117.31)** proyectados.")

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.header("Datos del Empleado")
    sueldo_bruto = st.number_input("Sueldo Bruto Mensual", value=22000.0, step=100.0)
    periodo = st.selectbox("Periodo de Pago", ["Quincenal", "Mensual", "Semanal"])
    antiguedad = st.number_input("Años de Antigüedad", 0, 40, 1)
    zona = st.radio("Zona Geográfica", ["General", "Frontera Norte"])
    
    st.divider()
    if st.button("Calcular Nómina Completa ▶️", type="primary"):
        st.session_state.calculado = True

# --- LÓGICA DE PROCESAMIENTO ---
if "calculado" in st.session_state:
    
    # 1. Definir días del periodo para el cálculo
    dias_periodo = 30.4 if periodo == "Mensual" else (15.2 if periodo == "Quincenal" else 7)
    factor_mes = 30.4 / dias_periodo
    
    # 2. Cálculos Previos
    sueldo_diario = sueldo_bruto / 30.4
    factor_int, dias_vac, dias_agui = obtener_factor_integracion(antiguedad)
    sbc = sueldo_diario * factor_int
    
    # Tope de 25 UMAS
    tope_sbc = VALORES_2026["UMA_DIARIA"] * VALORES_2026["TOPE_IMSS_UMAS"]
    sbc_real = min(sbc, tope_sbc)
    
    # 3. Calcular Impuestos (Siempre se calculan mensual y se dividen)
    # IMSS
    imss_total_mensual, df_imss = calcular_desglose_imss(sbc_real, 30.4)
    imss_periodo = imss_total_mensual / factor_mes
    
    # ISR
    isr_total_mensual, df_isr = calcular_desglose_isr(sueldo_bruto)
    isr_periodo = isr_total_mensual / factor_mes
    
    # Netos
    sueldo_periodo = sueldo_bruto / factor_mes
    neto_pagar = sueldo_periodo - isr_periodo - imss_periodo
    
    # --- RESULTADOS VISUALES ---
    
    # A. TARJETAS PRINCIPALES
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bruto (Periodo)", f"${sueldo_periodo:,.2f}")
    c2.metric("ISR Retenido", f"${isr_periodo:,.2f}", delta_color="inverse")
    c3.metric("IMSS Obrero", f"${imss_periodo:,.2f}", delta_color="inverse")
    c4.metric("💰 NETO A RECIBIR", f"${neto_pagar:,.2f}")
    
    st.divider()
    
    # B. PESTAÑAS DE DESGLOSE (EL CORAZÓN DE LA APP)
    tab1, tab2, tab3 = st.tabs(["📊 Resumen Visual", "🔍 Desglose IMSS", "🧮 Auditoría ISR"])
    
    with tab1:
        # Gráfica de distribución
        col_graph, col_data = st.columns([1, 1])
        
        with col_graph:
            datos_pie = pd.DataFrame({
                'Concepto': ['Neto', 'ISR', 'IMSS'],
                'Valor': [neto_pagar, isr_periodo, imss_periodo]
            })
            chart = alt.Chart(datos_pie).mark_arc(innerRadius=60).encode(
                theta="Valor",
                color="Concepto",
                tooltip=["Concepto", "Valor"]
            )
            st.altair_chart(chart, use_container_width=True)
            
        with col_data:
            st.subheader("Datos Laborales")
            st.write(f"**Sueldo Diario:** ${sueldo_diario:,.2f}")
            st.write(f"**SBC (Cotización):** ${sbc_real:,.2f}")
            st.write(f"**Factor Integración:** {factor_int:.4f}")
            st.caption(f"Vacaciones: {dias_vac} días | Aguinaldo: {dias_agui} días")

    with tab2:
        st.subheader("Desglose de Cuotas Obreras (IMSS)")
        st.markdown(f"Calculado sobre un SBC de **${sbc_real:,.2f}**")
        
        # Formatear la tabla para que se vea bonita
        st.dataframe(
            df_imss.style.format({"Importe a Pagar": "${:,.2f}"}),
            use_container_width=True,
            hide_index=True
        )
        st.info(f"**Nota:** Este es el cálculo mensual (${imss_total_mensual:,.2f}). En tu pago {periodo.lower()} se descuentan **${imss_periodo:,.2f}**.")

    with tab3:
        st.subheader("Mecánica de Cálculo del ISR")
        st.markdown("Así determinó el SAT tu impuesto:")
        
        # Formateo especial para que la tasa se vea como porcentaje
        def format_isr_table(val):
            if isinstance(val, float):
                if val < 1.0 and val > 0: return f"{val*100:.2f}%" # Es tasa
                return f"${val:,.2f}" # Es dinero
            return val

        st.table(df_isr.assign(Monto=df_isr['Monto'].apply(format_isr_table)))
        
        st.success(f"ISR Total del Mes: **${isr_total_mensual:,.2f}** ÷ Factor Periodo = **${isr_periodo:,.2f}**")

else:
    st.info("👈 Ingresa los datos en la barra lateral y presiona 'Calcular' para ver la magia.")
