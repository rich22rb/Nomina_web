import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

st.set_page_config(page_title="Nómina 2026 | Dashboard", page_icon="📊", layout="wide")

# --- 1. CONSTANTES OFICIALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,
    "SALARIO_MINIMO_FN": 440.87,
}

# Tabla ISR Mensual Oficial 2026
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

# --- 2. CSS PERSONALIZADO (FIX DE COLORES) ---
st.markdown("""
<style>
    /* Estilo para las Tarjetas (Cards) */
    .metric-card {
        background-color: #ffffff; /* Fondo Blanco */
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    /* Forzamos texto oscuro para que se lea en Dark Mode */
    .metric-card small {
        color: #666666 !important; 
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        color: #1f2937 !important; /* Gris muy oscuro casi negro */
        font-size: 28px;
        font-weight: 800;
        margin-top: 5px;
    }
    .metric-sub {
        font-size: 12px;
        color: #999999 !important;
    }
    /* Colores específicos para Netos y Deducciones */
    .neto-value { color: #10b981 !important; } /* Verde */
    .deduction-value { color: #ef4444 !important; } /* Rojo */
</style>
""", unsafe_allow_html=True)

# --- 3. FUNCIONES DE CÁLCULO ---

def calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base):
    # 1. Proyección Mensual
    base_mensual = sueldo_diario * dias_mes_base
    
    # 2. Cálculo ISR Mensual
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
            
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    
    # 3. Ajuste al Periodo
    factor = dias_pago / dias_mes_base
    isr_periodo = isr_mensual * factor
    
    # Datos para auditoría
    desglose = {
        "Base Mensual": base_mensual,
        "Límite Inf.": limite,
        "Excedente": excedente,
        "Tasa": porc,
        "Impuesto Marg.": marginal,
        "Cuota Fija": cuota,
        "ISR Mensual": isr_mensual,
        "ISR Periodo": isr_periodo
    }
    return isr_periodo, desglose

def calcular_imss_detallado(sbc, dias):
    uma = VALORES_2026["UMA"]
    exc = max(0, sbc - (3*uma))
    
    # Desglose de ramas (Cuotas Obreras)
    conceptos = {
        "Enf. y Mat. (Exc)": exc * 0.004 * dias,
        "Prest. Dinero": sbc * 0.0025 * dias,
        "Gastos Médicos": sbc * 0.00375 * dias,
        "Invalidez y Vida": sbc * 0.00625 * dias,
        "Cesantía y Vejez": sbc * 0.01125 * dias
    }
    total = sum(conceptos.values())
    return total, conceptos

# --- 4. INTERFAZ ---

st.title("📊 Nómina 2026: Dashboard Profesional")

# --- SECCIÓN DE INPUTS (PANEL SUPERIOR) ---
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
        dias_mes_base = 30.0 if "30" in criterio else 30.4
    
    with col2:
        periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual", "Catorcenal"])
        # Mapeo de días
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        elif periodo == "Mensual": dias_pago = dias_mes_base
        else: dias_pago = 14
        
    with col3:
        # Input flexible
        sueldo_input = st.number_input("Sueldo Bruto (Mensual)", value=20000.0, step=500.0)
        sueldo_diario = sueldo_input / dias_mes_base
        
    with col4:
        # Antigüedad
        f_inicio = st.date_input("Fecha Inicio", date(2024, 1, 1))
        antiguedad_dias = (date.today() - f_inicio).days + 1
        anios = int(antiguedad_dias / 365.25)
        
    if st.button("Calcular Nómina Detallada 🚀", type="primary", use_container_width=True):
        st.session_state.run = True

# --- SECCIÓN DE RESULTADOS ---
if "run" in st.session_state:
    st.divider()
    
    # 1. CÁLCULOS
    # Prestaciones (SBC)
    if anios == 0: dias_vac = 12
    else: dias_vac = 14 # Simplificado para demo
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    # Nómina
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    # 2. TARJETAS DE RESUMEN (CSS FIXED)
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <small>Percepción {periodo}</small>
            <div class="metric-value">${bruto:,.2f}</div>
            <div class="metric-sub">{dias_pago} días pagados</div>
        </div>
        """, unsafe_allow_html=True)
        
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <small>Retención ISR</small>
            <div class="metric-value deduction-value">-${isr:,.2f}</div>
            <div class="metric-sub">Tasa efectiva: {(isr/bruto)*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <small>Retención IMSS</small>
            <div class="metric-value deduction-value">-${imss:,.2f}</div>
            <div class="metric-sub">SBC: ${sbc:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid #10b981;">
            <small style="color:#10b981 !important;">Neto a Pagar</small>
            <div class="metric-value neto-value">${neto:,.2f}</div>
            <div class="metric-sub">Disponible</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. PESTAÑAS DE DETALLE (EL REGRESO)
    tab_visual, tab_isr, tab_imss = st.tabs(["📊 Distribución Visual", "🏛️ Desglose ISR", "🏥 Desglose IMSS"])
    
    with tab_visual:
        col_g1, col_g2 = st.columns([1, 2])
        
        with col_g1:
            # GRÁFICA DE DONA
            source = pd.DataFrame({
                "Concepto": ["Neto", "ISR", "IMSS"],
                "Monto": [neto, isr, imss]
            })
            
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=70).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#10b981', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", "Monto"]
            )
            text = base.mark_text(radius=100).encode(
                text=alt.Text("Monto", format=",.0f"),
                order=alt.Order("Monto", sort="descending"),
                color=alt.value("black")  
            )
            st.altair_chart(pie + text, use_container_width=True)
            
        with col_g2:
            st.info("💡 **Análisis Rápido:**")
            st.write(f"- De cada $1,000 pesos que ganas, te llevas a casa **${(neto/bruto)*1000:,.2f}**.")
            st.write(f"- El **{(imss/bruto)*100:.1f}%** de tu sueldo se va a tu ahorro/salud (IMSS).")
            st.write(f"- El **{(isr/bruto)*100:.1f}%** se paga de impuestos (ISR).")
            
            st.markdown("---")
            st.caption(f"Antigüedad Calculada: {anios} años ({antiguedad_dias} días naturales).")

    with tab_isr:
        st.subheader("Auditoría Fiscal (ISR)")
        st.markdown(f"Cálculo basado en proyección mensual (Ingreso mensual base: **${sueldo_input:,.2f}**)")
        
        # Convertimos el diccionario a DataFrame para mostrarlo lindo
        audit_data = [
            {"Paso": "1. Base Mensual", "Monto": df_isr_raw["Base Mensual"]},
            {"Paso": "2. Límite Inferior", "Monto": df_isr_raw["Límite Inf."]},
            {"Paso": "3. Excedente", "Monto": df_isr_raw["Excedente"]},
            {"Paso": "4. Tasa Aplicable", "Monto": df_isr_raw["Tasa"]}, # Formatear %
            {"Paso": "5. Impuesto Marginal", "Monto": df_isr_raw["Impuesto Marg."]},
            {"Paso": "6. Cuota Fija", "Monto": df_isr_raw["Cuota Fija"]},
            {"Paso": "7. ISR Mensual Total", "Monto": df_isr_raw["ISR Mensual"]},
            {"Paso": f"8. Proporción Periodo ({periodo})", "Monto": isr}
        ]
        
        df_audit = pd.DataFrame(audit_data)
        
        # Función de formato
        def fmt_money(x, paso):
            if "Tasa" in paso: return f"{x*100:.2f}%"
            return f"${x:,.2f}"
            
        df_audit["Valor"] = df_audit.apply(lambda x: fmt_money(x["Monto"], x["Paso"]), axis=1)
        st.table(df_audit[["Paso", "Valor"]])

    with tab_imss:
        st.subheader("Cuotas Obreras (Descuento al Empleado)")
        st.markdown(f"Calculado sobre un SBC de **${sbc:,.2f}**")
        
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        st.dataframe(
            df_imss,
            column_config={
                "Monto": st.column_config.NumberColumn("Descuento", format="$%.2f")
            },
            use_container_width=True,
            hide_index=True
        )
