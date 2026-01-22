import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

st.set_page_config(page_title="Nómina 2026 | Engine Pro", page_icon="💎", layout="wide")

# --- 1. DATOS OFICIALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,
    "SALARIO_MINIMO_FN": 440.87,
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

# --- 2. CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .metric-card small {
        color: #666666 !important; font-size: 13px; font-weight: 700; text-transform: uppercase;
    }
    .metric-value {
        color: #111827 !important; font-size: 26px; font-weight: 800; margin-top: 8px;
    }
    .neto-value { color: #059669 !important; }
    .deduction-value { color: #dc2626 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. CÁLCULO ---

def calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base):
    # Proyección
    base_mensual = sueldo_diario * dias_mes_base
    
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
            
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    
    # Prorrateo
    factor = dias_pago / dias_mes_base
    isr_periodo = isr_mensual * factor
    
    desglose = {
        "1. Base Mensual Proyectada": base_mensual,
        "2. (-) Límite Inferior": limite,
        "3. (=) Excedente": excedente,
        "4. (x) Tasa Aplicable": porc,
        "5. (=) Impuesto Marginal": marginal,
        "6. (+) Cuota Fija": cuota,
        "7. (=) ISR Mensual Total": isr_mensual,
        f"8. (x) Factor ({dias_pago}/{dias_mes_base})": factor,
        "9. (=) ISR A RETENER": isr_periodo
    }
    return isr_periodo, desglose

def calcular_imss_detallado(sbc, dias):
    uma = VALORES_2026["UMA"]
    exc = max(0, sbc - (3*uma))
    conceptos = {
        "Enf. y Mat. (Exc)": exc * 0.004 * dias,
        "Prest. Dinero": sbc * 0.0025 * dias,
        "Gastos Médicos": sbc * 0.00375 * dias,
        "Invalidez y Vida": sbc * 0.00625 * dias,
        "Cesantía y Vejez": sbc * 0.01125 * dias
    }
    return sum(conceptos.values()), conceptos

# --- 4. INTERFAZ ---

st.title("💎 Nómina 2026 Pro")

with st.container(border=True):
    # FILA 1
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
        dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
    with c2:
        periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual"])
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        else: dias_pago = dias_mes_base
    with c3:
        tipo_ingreso = st.selectbox("Tipo de Ingreso", ["Bruto Mensual", "Bruto por Periodo"])
    with c4:
        monto_input = st.number_input(f"Monto {tipo_ingreso}", value=15000.0, step=500.0)
        
        if tipo_ingreso == "Bruto Mensual":
            sueldo_diario = monto_input / dias_mes_base
        else:
            sueldo_diario = monto_input / dias_pago

    # FILA 2
    c5, c6 = st.columns([1, 3])
    with c5:
        antig = st.number_input("Años Antigüedad", 0, 50, 0)
    with c6:
        st.info(f"💡 **Base de Cálculo:** ${sueldo_diario:,.2f} diarios × {dias_mes_base} días = **${sueldo_diario*dias_mes_base:,.2f}** Base Mensual Integrada.")

    if st.button("Calcular Nómina 🚀", type="primary", use_container_width=True):
        st.session_state.run = True

# --- RESULTADOS ---
if "run" in st.session_state:
    st.divider()
    
    # Cálculos
    if antig == 0: dias_vac = 12
    else: dias_vac = 14
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    # 2. Tarjetas (USANDO HTML ENTITY &#36; PARA ELIMINAR DIAGONALES)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="metric-card"><small>Percepción {periodo}</small><div class="metric-value">&#36;{bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card"><small>ISR Retenido</small><div class="metric-value deduction-value">-&#36;{isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="metric-card"><small>IMSS Retenido</small><div class="metric-value deduction-value">-&#36;{imss:,.2f}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="metric-card" style="border: 2px solid #059669;"><small style="color:#059669 !important;">Neto a Pagar</small><div class="metric-value neto-value">&#36;{neto:,.2f}</div></div>""", unsafe_allow_html=True)

    # 3. Pestañas
    tab_visual, tab_isr, tab_imss = st.tabs(["🧠 Análisis Inteligente", "🏛️ Auditoría ISR", "🏥 Auditoría IMSS"])
    
    with tab_visual:
        c_chart, c_data = st.columns([1, 2])
        
        with c_chart:
            source = pd.DataFrame({"Concepto": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=60, outerRadius=90).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#059669', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", alt.Tooltip("Monto", format="$,.2f")]
            )
            st.altair_chart(pie, use_container_width=True)
            
        with c_data:
            # ANÁLISIS MEJORADO Y PROFUNDO
            impuestos_totales = isr + imss
            dias_para_impuestos = impuestos_totales / sueldo_diario
            tasa_efectiva = (impuestos_totales / bruto) * 100
            proyeccion_anual = impuestos_totales * (365 / dias_pago)
            
            st.markdown("#### 📉 Impacto en tu Bolsillo")
            st.markdown(f"""
            * **Día de Libertad Fiscal:** En este periodo de {dias_pago} días, trabajaste **{dias_para_impuestos:.1f} días** solo para pagar impuestos (ISR + IMSS). El resto es tuyo.
            * **Tasa Real vs Tablas:** Aunque caíste en el renglón del **{df_isr_raw['4. (x) Tasa Aplicable']*100:.2f}%** de la tabla, tu tasa *real efectiva* es del **{tasa_efectiva:.1f}%**.
            * **Proyección Anual:** A este ritmo, el gobierno recaudará aproximadamente **${proyeccion_anual:,.2f}** de tu trabajo este año.
            """)
            
            st.progress(tasa_efectiva/100, text=f"Porcentaje del sueldo destinado a impuestos: {tasa_efectiva:.1f}%")

    with tab_isr:
        st.subheader("Mecánica de Cálculo")
        df_audit = pd.DataFrame(list(df_isr_raw.items()), columns=["Paso", "Valor"])
        def fmt(x, p):
            if "Factor" in p: return f"{x:.4f}"
            if "Tasa" in p: return f"{x*100:.2f}%"
            return f"${x:,.2f}"
        df_audit["Valor"] = df_audit.apply(lambda x: fmt(x["Valor"], x["Paso"]), axis=1)
        st.dataframe(df_audit, hide_index=True, use_container_width=True)

    with tab_imss:
        st.subheader("Cuotas Obreras")
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        total_row = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
        df_imss = pd.concat([df_imss, total_row], ignore_index=True)
        st.dataframe(df_imss.style.format({"Monto": "${:,.2f}"}), hide_index=True, use_container_width=True)
