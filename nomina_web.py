import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

st.set_page_config(page_title="Sistema de Nómina 2026 (Oficial)", page_icon="🇲🇽", layout="wide")

# --- 1. CONSTANTES LEGALES 2026 ---
# Fuente: Anexo 8 RMF 2026 y Resolución del H. Consejo de Representantes (CONASAMI)
VALORES_2026 = {
    "UMA_DIARIA": 117.31,           # Valor INEGI (Feb 2026)
    "SALARIO_MINIMO": 315.04,       # Zona General
    "SALARIO_MINIMO_FN": 440.87,    # Zona Frontera Norte
    "TOPE_IMSS_UMAS": 25,
    "PRIMA_VACACIONAL": 0.25,
    "EXENTO_AGUINALDO": 30 * 117.31 # Exención de 30 UMAS
}

# TABLA ISR MENSUAL 2026 (BASE)
# Fuente: DOF Anexo 8 (RMF 2026)
# Límite Inferior | Cuota Fija | % Excedente
TABLA_MENSUAL_2026 = [
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

# --- 2. MOTOR DE CÁLCULO (FACTOR 30.4) ---

def obtener_tabla_periodica(dias_periodo):
    """
    Genera la tabla ISR oficial para cualquier periodo (Semanal/Quincenal/Decenal)
    usando el factor de ley: (Mensual / 30.4) * DiasPeriodo.
    Referencia: Regla 3.12.2 RMF
    """
    factor = dias_periodo / 30.4
    tabla_calculada = []
    for renglon in TABLA_MENSUAL_2026:
        nuevo_limite = renglon[0] * factor
        nueva_cuota = renglon[1] * factor
        porcentaje = renglon[2] # El % no cambia
        tabla_calculada.append([nuevo_limite, nueva_cuota, porcentaje])
    return tabla_calculada

def calcular_isr_exacto(base_gravable, tabla_periodica):
    """Calcula el ISR usando la tabla específica del periodo"""
    limite, cuota, porc = 0, 0, 0
    for row in tabla_periodica:
        if base_gravable >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break
            
    excedente = base_gravable - limite
    marginal = excedente * porc
    isr = marginal + cuota
    
    # Datos para auditoría visual
    desglose = [
        {"Concepto": "1. Base Gravable", "Monto": base_gravable},
        {"Concepto": "2. (-) Límite Inferior", "Monto": limite},
        {"Concepto": "3. (=) Excedente", "Monto": excedente},
        {"Concepto": "4. (x) Tasa", "Monto": porc}, # Se formatea luego
        {"Concepto": "5. (=) Impuesto Marginal", "Monto": marginal},
        {"Concepto": "6. (+) Cuota Fija", "Monto": cuota},
        {"Concepto": "7. (=) ISR Determinado", "Monto": isr}
    ]
    return isr, desglose

def calcular_imss_proporcional(sbc, dias_pago):
    uma = VALORES_2026["UMA_DIARIA"]
    exc = max(0, sbc - (3 * uma))
    
    # Factores de cuotas obreras 2026
    cuotas = {
        "Enf. y Mat. (Exc)": exc * 0.004 * dias_pago,
        "Prest. Dinero": sbc * 0.0025 * dias_pago,
        "Gastos Médicos": sbc * 0.00375 * dias_pago,
        "Invalidez y Vida": sbc * 0.00625 * dias_pago,
        "Cesantía y Vejez": sbc * 0.01125 * dias_pago
    }
    return sum(cuotas.values()), cuotas

def obtener_factor_integracion(anios):
    """Vacaciones Dignas según antigüedad"""
    if anios == 0: dias_vac = 12
    elif anios == 1: dias_vac = 14
    elif anios == 2: dias_vac = 16
    elif anios == 3: dias_vac = 18
    elif anios == 4: dias_vac = 20
    elif 5 <= anios <= 9: dias_vac = 22
    else: dias_vac = 24
    
    # Factor = 1 + (Proporción diaria de Aguinaldo + Prima Vacacional)
    factor = 1 + ((15 + (dias_vac * VALORES_2026["PRIMA_VACACIONAL"])) / 365)
    return factor, dias_vac

# --- 3. INTERFAZ ---
st.sidebar.title("🧮 Nómina & Fiscal 2026")
modulo = st.sidebar.radio("Selecciona Módulo:", ["Nómina Periódica", "Aguinaldo", "Finiquito/Liquidación"])

# ==============================================================================
# MÓDULO 1: NÓMINA PERIÓDICA (CON TABLAS EXACTAS)
# ==============================================================================
if modulo == "Nómina Periódica":
    st.title("💼 Nómina 2026: Cálculo Exacto")
    st.markdown("Calculadora ajustada con factor **30.4** según Anexo 8 RMF 2026.")
    
    with st.sidebar:
        st.markdown("---")
        st.header("Datos de Pago")
        monto = st.number_input("Monto Bruto", value=12000.0, step=100.0)
        tipo_entrada = st.selectbox("Este monto es:", ["Mensual", "Quincenal", "Semanal"])
        periodo_pago = st.selectbox("Frecuencia de Pago (Tabla ISR):", ["Quincenal", "Semanal", "Mensual", "Decenal"])
        
        st.header("Datos Laborales")
        anios = st.number_input("Años de Antigüedad", 0, 40, 1)
        zona = st.radio("Zona Salarial", ["General", "Frontera Norte"])
        
        if st.button("Calcular Nómina ▶️", type="primary"):
            st.session_state.run = True

    if "run" in st.session_state:
        # A. DEFINIR DÍAS DE PAGO REALES
        if periodo_pago == "Mensual": dias_nom = 30.4
        elif periodo_pago == "Quincenal": dias_nom = 15
        elif periodo_pago == "Decenal": dias_nom = 10
        elif periodo_pago == "Semanal": dias_nom = 7
        
        # B. NORMALIZAR SUELDOS (Para SBC e ISR)
        # Convertimos todo a diario y luego al periodo
        if tipo_entrada == "Mensual": sueldo_diario = monto / 30.4
        elif tipo_entrada == "Quincenal": sueldo_diario = monto / 15
        elif tipo_entrada == "Semanal": sueldo_diario = monto / 7
        
        # Validar Mínimo 2026
        minimo = VALORES_2026["SALARIO_MINIMO_FN"] if zona == "Frontera Norte" else VALORES_2026["SALARIO_MINIMO"]
        if sueldo_diario < minimo:
            st.warning(f"⚠️ El sueldo diario (${sueldo_diario:,.2f}) está por debajo del mínimo 2026 (${minimo:,.2f}). Se ajustará automáticamente.")
            sueldo_diario = minimo
        
        sueldo_periodo = sueldo_diario * dias_nom
        
        # C. CÁLCULOS
        # 1. SBC
        factor_int, dias_vac = obtener_factor_integracion(anios)
        sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA_DIARIA"] * 25)
        
        # 2. IMSS (Proporcional a los días de pago)
        imss_total, desglose_imss = calcular_imss_proporcional(sbc, dias_nom)
        
        # 3. ISR (TABLA DINÁMICA OFICIAL) 🧠
        # Generamos la tabla exacta para 7, 10, 15 o 30.4 días
        tabla_oficial_periodo = obtener_tabla_periodica(dias_nom)
        isr_total, desglose_isr = calcular_isr_exacto(sueldo_periodo, tabla_oficial_periodo)
        
        neto = sueldo_periodo - imss_total - isr_total
        
        # D. RESULTADOS
        st.success(f"Cálculo para **{periodo_pago}** ({dias_nom} días).")
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Bruto Periodo", f"${sueldo_periodo:,.2f}")
        k2.metric("ISR", f"-${isr_total:,.2f}", delta_color="inverse")
        k3.metric("IMSS", f"-${imss_total:,.2f}", delta_color="inverse")
        k4.metric("NETO", f"${neto:,.2f}", delta_color="normal")
        
        # Pestañas de detalle
        tab1, tab2, tab3 = st.tabs(["📊 Gráfica", "🏛️ Auditoría ISR", "🏥 Auditoría IMSS"])
        
        with tab1:
            df_g = pd.DataFrame({'C':['Neto','ISR','IMSS'], 'V':[neto, isr_total, imss_total]})
            c = alt.Chart(df_g).mark_arc(innerRadius=60).encode(theta='V', color='C', tooltip=['C','V'])
            st.altair_chart(c, use_container_width=True)
            st.caption(f"Datos base: SBC ${sbc:,.2f} | Factor {factor_int:.4f} | Vacaciones {dias_vac} días")

        with tab2:
            st.subheader(f"Tabla ISR Oficial ({periodo_pago})")
            st.markdown("Tabla calculada según Regla 3.12.2 RMF (Factor 30.4).")
            
            # Formatear la tabla del desglose
            df_isr = pd.DataFrame(desglose)
            def fmt(val):
                if val < 1 and val > 0: return f"{val*100:.2f}%"
                return f"${val:,.2f}"
            
            st.table(df_isr.assign(Monto=df_isr["Monto"].apply(fmt)))

        with tab3:
            st.dataframe(pd.DataFrame(list(desglose_imss.items()), columns=["Rama", "Monto"]).style.format({"Monto":"${:,.2f}"}), use_container_width=True)

# ==============================================================================
# MÓDULO 2: AGUINALDO
# ==============================================================================
elif modulo == "Aguinaldo":
    st.title("🎄 Aguinaldo 2026")
    c1, c2 = st.columns(2)
    with c1:
        mensual = st.number_input("Sueldo Mensual", 10000.0)
        dias_ley = st.number_input("Días a Pagar", 15, 90, 15)
    with c2:
        dias_trab = st.number_input("Días Trabajados Año", 1, 365, 365)
        
    if st.button("Calcular"):
        bruto = (mensual/30) * dias_ley * (dias_trab/365)
        exento = VALORES_2026["EXENTO_AGUINALDO"]
        gravado = max(0, bruto - exento)
        
        # ISR Reglamento (Aproximación Tasa Efectiva)
        # Se calcula el ISR de (Mensual + Gravado) menos el ISR de (Mensual)
        tabla_mensual_oficial = obtener_tabla_periodica(30.4) # Tabla mensual estándar
        isr_base, _ = calcular_isr_exacto(mensual, tabla_mensual_oficial)
        isr_con_aguinaldo, _ = calcular_isr_exacto(mensual + gravado, tabla_mensual_oficial)
        isr_retener = isr_con_aguinaldo - isr_base
        
        st.divider()
        st.metric("Aguinaldo Neto", f"${bruto - isr_retener:,.2f}")
        st.caption(f"Bruto: ${bruto:,.2f} | Exento: ${exento:,.2f} | ISR: ${isr_retener:,.2f}")

# ==============================================================================
# MÓDULO 3: FINIQUITO / LIQUIDACIÓN
# ==============================================================================
elif modulo == "Finiquito/Liquidación":
    st.title("⚖️ Finiquito & Liquidación")
    with st.sidebar:
        ingreso = st.date_input("Fecha Ingreso", date(2023,1,1))
        baja = st.date_input("Fecha Baja", date.today())
        mensual = st.number_input("Sueldo Mensual", 20000.0)
        causa = st.selectbox("Causa", ["Renuncia Voluntaria", "Despido Injustificado"])
    
    if st.button("Calcular"):
        antig = (baja - ingreso).days + 1
        anios_c = int(antig/365.25)
        prop_anios = antig/365.25
        
        sd = mensual / 30
        factor, _ = obtener_factor_integracion(anios_c)
        sdi = sd * factor
        
        # Finiquito
        agui_prop = (15/365) * baja.timetuple().tm_yday * sd
        vac_pend = 6 * sd # Estimado
        prim_vac = vac_pend * 0.25
        finiquito = agui_prop + vac_pend + prim_vac
        
        # Liquidación
        liquidacion = 0
        if causa == "Despido Injustificado":
            indem_3m = 3 * 30 * sdi
            indem_20d = 20 * prop_anios * sdi
            prima_ant = 12 * prop_anios * min(sd, VALORES_2026["SALARIO_MINIMO"]*2)
            liquidacion = indem_3m + indem_20d + prima_ant
            
        st.subheader(f"Total a Pagar: ${finiquito + liquidacion:,.2f}")
        st.json({
            "Finiquito (Aguinaldo/Vacaciones)": f"${finiquito:,.2f}",
            "Liquidación (Indemnización)": f"${liquidacion:,.2f}",
            "Antigüedad": f"{anios_c} años"
        })
