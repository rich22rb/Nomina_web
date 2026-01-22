import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="Nómina 2026 | Engine Pro", page_icon="💎", layout="wide")

# --- 1. DATOS OFICIALES 2026 (DO 2026) ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,
    "SALARIO_MINIMO_FN": 440.87,
    "FACTOR_MES": 30.4
}

# Tabla Mensual Oficial 2026
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

# --- 2. MOTOR DE CÁLCULO (LÓGICA SAP/NOMIPAQ) ---

def calcular_antiguedad(f_inicio):
    hoy = date.today()
    delta = hoy - f_inicio
    dias = delta.days + 1
    anios = int(dias / 365.25)
    semanas = int(dias / 7)
    # Formato ISO SAT (Ej: P21D para días, P1Y para años)
    if dias < 7: iso = f"P{dias}D"
    elif dias < 365: iso = f"P{semanas}W"
    else: iso = f"P{anios}Y"
    return anios, dias, weeks, iso

def calcular_isr_proyeccion_mensual(sueldo_diario, dias_periodo):
    """
    MÉTODO PRO: 
    1. Eleva el sueldo diario a mensual (x30.4).
    2. Calcula ISR con tabla mensual completa.
    3. Divide el ISR resultante entre 30.4 para tener ISR Diario.
    4. Multiplica por días del periodo.
    """
    # 1. Mensualizar
    base_mensual = sueldo_diario * 30.4
    
    # 2. Calcular ISR Mensual
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else:
            break
            
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    
    # 3. Prorratear al periodo
    factor_periodo = dias_periodo / 30.4
    isr_periodo = isr_mensual * factor_periodo
    
    # Datos para desglose (Visualmente mostraremos los datos mensuales para que cuadre con la tabla oficial)
    desglose = {
        "Base Proyectada (Mensual)": base_mensual,
        "Límite Inferior": limite,
        "Excedente": excedente,
        "Tasa (%)": porc,
        "Impuesto Marginal": marginal,
        "Cuota Fija": cuota,
        "ISR Mensual": isr_mensual,
        "Factor Periodo": factor_periodo,
        "ISR A RETENER": isr_periodo
    }
    return isr_periodo, desglose

def calcular_imss(sbc, dias):
    uma = VALORES_2026["UMA"]
    # Cuotas obreras simplificadas para ejemplo (suma de % de ley)
    exc = max(0, sbc - (3*uma))
    cuota_total = (exc*0.004) + (sbc*0.02375) # Suma aprox de ramas obreras
    return cuota_total * dias

# --- 3. ESTILOS CSS (PARA QUE SE VEA PRO) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .big-font { font-size: 24px !important; font-weight: bold; color: #1f77b4; }
    .header-style { font-size: 18px; font-weight: 600; color: #444; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. INTERFAZ ---

st.title("💎 Nómina 2026 Professional")

# CONTENEDOR DE INPUTS (ARRIBA, LIMPIO)
with st.container(border=True):
    st.markdown("### ⚙️ Parámetros del Cálculo")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        f_inicio = st.date_input("Fecha Inicio", date(2025, 1, 1))
        # Cálculo automático de antigüedad
        hoy = date.today()
        dias_trab = (hoy - f_inicio).days + 1
        anios_trab = int(dias_trab/365.25)
        semanas_imss = int(dias_trab/7)
        antiguedad_sat = f"P{dias_trab}D" # Formato ISO simple

    with c2:
        periodo = st.selectbox("Periodo de Pago", ["Quincenal", "Semanal", "Mensual", "Catorcenal"])
        # Definir días exactos
        mapa_dias = {"Mensual": 30.4, "Quincenal": 15, "Semanal": 7, "Catorcenal": 14}
        dias_periodo = mapa_dias[periodo]

    with c3:
        # Input Inteligente: El usuario suele pensar en SUELDO MENSUAL BRUTO aunque pague quincenal
        sueldo_base_input = st.number_input("Sueldo Bruto (Mensual)", value=18000.0, step=500.0)
        sueldo_diario = sueldo_base_input / 30.4
    
    with c4:
        st.markdown(f"**Días a Pagar:** {dias_periodo}")
        st.markdown(f"**Sueldo Diario:** ${sueldo_diario:,.2f}")
        st.markdown(f"**Antigüedad:** {anios_trab} años")

    btn_calc = st.button("Calcular Nómina", type="primary", use_container_width=True)

# --- RESULTADOS ---
if btn_calc:
    
    # 1. EJECUCIÓN DEL MOTOR
    # Nota: Usamos vacaciones de ley 2026 para SBC
    if anios_trab == 0: dias_vac = 12
    else: dias_vac = 14 # Simplificado
    
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"]*25)
    
    # Calculos Core
    bruto_periodo = sueldo_diario * dias_periodo
    imss_periodo = calcular_imss(sbc, dias_periodo)
    isr_periodo, desglose_isr = calcular_isr_proyeccion_mensual(sueldo_diario, dias_periodo)
    
    neto = bruto_periodo - imss_periodo - isr_periodo
    
    st.divider()
    
    # 2. LAYOUT DE RESULTADOS (Izquierda Métricas, Derecha Tabla)
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown('<p class="header-style">Resumen del Periodo</p>', unsafe_allow_html=True)
        
        # Tarjetas visuales usando HTML simple para control total
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div class="metric-card">
                <small>Percepción {periodo}</small><br>
                <span class="big-font" style="color:#333">${bruto_periodo:,.2f}</span>
            </div>
             <div class="metric-card">
                <small>Neto a Pagar</small><br>
                <span class="big-font" style="color:#28a745">${neto:,.2f}</span>
            </div>
            <div class="metric-card">
                <small>Retención ISR</small><br>
                <span style="color:#dc3545; font-weight:bold">-${isr_periodo:,.2f}</span>
            </div>
            <div class="metric-card">
                <small>Retención IMSS</small><br>
                <span style="color:#dc3545; font-weight:bold">-${imss_periodo:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        # Datos Informativos (Semanas, SAT)
        r1, r2, r3 = st.columns(3)
        r1.metric("Semanas IMSS", semanas_imss)
        r2.metric("Antigüedad SAT", antiguedad_sat)
        r3.metric("SBC", f"${sbc:,.2f}")

    with col_right:
        st.markdown('<p class="header-style">Desglose ISR (Mecánica Mensual)</p>', unsafe_allow_html=True)
        st.info("El cálculo se realiza sobre la base mensual proyectada y se ajusta al periodo.")
        
        # Preparamos el DataFrame para que se vea igual a tu imagen
        datos_tabla = [
            {"Concepto": "Base Gravable (Mensual)", "Monto": desglose_isr["Base Proyectada (Mensual)"]},
            {"Concepto": "Limite Inferior", "Monto": desglose_isr["Límite Inferior"]},
            {"Concepto": "Excedente", "Monto": desglose_isr["Excedente"]},
            {"Concepto": "% Tasa", "Monto": desglose_isr["Tasa (%)"]}, # Se arregla formato abajo
            {"Concepto": "Impuesto Marginal", "Monto": desglose_isr["Impuesto Marginal"]},
            {"Concepto": "Cuota Fija", "Monto": desglose_isr["Cuota Fija"]},
            {"Concepto": "= ISR Mensual", "Monto": desglose_isr["ISR Mensual"]},
            {"Concepto": f"ISR del Periodo ({periodo})", "Monto": isr_periodo},
        ]
        
        df_show = pd.DataFrame(datos_tabla)
        
        # Configuración visual de la tabla
        st.dataframe(
            df_show,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Concepto": st.column_config.TextColumn("Concepto", width="medium"),
                "Monto": st.column_config.NumberColumn(
                    "Monto MXN",
                    format="$%.2f" # Formato moneda
                )
            }
        )
