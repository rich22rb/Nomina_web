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

# --- 3. MOTORES DE CÁLCULO ---

def calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base):
    # Lógica PRO: Elevamos a mensual -> Calculamos -> Prorrateamos
    base_mensual = sueldo_diario * dias_mes_base
    
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
            
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    
    # Factor de ajuste (Aquí es donde Fiscal vs Comercial hace la magia)
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
        f"8. (x) Factor ({dias_pago}/{dias_mes_base})": factor, # Mostrar el factor explícito
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
    # FILA 1: Configuración Global
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        criterio = st.selectbox("Criterio Días", ["Comercial (30)", "Fiscal (30.4)"])
        # CORRECCIÓN DEL BUG: Usamos "Comercial" explícitamente
        dias_mes_base = 30.0 if "Comercial" in criterio else 30.4
    
    with c2:
        periodo = st.selectbox("Frecuencia", ["Quincenal", "Semanal", "Mensual", "Catorcenal"])
        if periodo == "Quincenal": dias_pago = 15
        elif periodo == "Semanal": dias_pago = 7
        elif periodo == "Mensual": dias_pago = dias_mes_base
        else: dias_pago = 14
        
    with c3:
        # MEJORA: Tipo de Entrada
        tipo_ingreso = st.selectbox("Tipo de Ingreso", ["Bruto Mensual", "Bruto por Periodo"])
    
    with c4:
        monto_input = st.number_input(f"Monto {tipo_ingreso}", value=15000.0, step=500.0)
        
        # Lógica de conversión a Diario (El corazón del cálculo)
        if tipo_ingreso == "Bruto Mensual":
            sueldo_diario = monto_input / dias_mes_base
        else:
            # Si ingresa por periodo, lo convertimos a diario directo
            sueldo_diario = monto_input / dias_pago

    # FILA 2: Datos Adicionales
    c5, c6 = st.columns([1, 3])
    with c5:
        antig = st.number_input("Años Antigüedad", 0, 50, 0)
    with c6:
        st.info(f"💡 **Base de Cálculo:** ${sueldo_diario:,.2f} diarios × {dias_mes_base} días mes = **${sueldo_diario*dias_mes_base:,.2f}** Mensual Integrado.")

    if st.button("Calcular Nómina 🚀", type="primary", use_container_width=True):
        st.session_state.run = True

# --- RESULTADOS ---
if "run" in st.session_state:
    st.divider()
    
    # 1. Ejecución
    if antig == 0: dias_vac = 12
    else: dias_vac = 14
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    # 2. Tarjetas
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="metric-card"><small>Percepción {periodo}</small><div class="metric-value">\${bruto:,.2f}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card"><small>ISR Retenido</small><div class="metric-value deduction-value">-\${isr:,.2f}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="metric-card"><small>IMSS Retenido</small><div class="metric-value deduction-value">-\${imss:,.2f}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="metric-card" style="border: 2px solid #059669;"><small style="color:#059669 !important;">Neto a Pagar</small><div class="metric-value neto-value">\${neto:,.2f}</div></div>""", unsafe_allow_html=True)

    # 3. Pestañas
    tab_visual, tab_isr, tab_imss = st.tabs(["📊 Distribución", "🏛️ Auditoría ISR", "🏥 Auditoría IMSS"])
    
    with tab_visual:
        c1, c2 = st.columns([1, 2])
        with c1:
            source = pd.DataFrame({"Concepto": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=60, outerRadius=100).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#059669', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", alt.Tooltip("Monto", format="$,.2f")]
            )
            st.altair_chart(pie, use_container_width=True)
        with c2:
            st.write("### Análisis de Impacto")
            st.write(f"- Factor de Días usado: **{dias_mes_base}** ({criterio})")
            st.write(f"- Sueldo Diario Base: **\${sueldo_diario:,.2f}**")
            st.caption("Si cambias entre Fiscal/Comercial, observa cómo cambia el Sueldo Diario y por tanto la Base Gravable.")

    with tab_isr:
        st.subheader("Mecánica de Cálculo")
        df_audit = pd.DataFrame(list(df_isr_raw.items()), columns=["Paso", "Valor"])
        def fmt(x, p):
            if "Factor" in p: return f"{x:.4f}" # Mostrar 4 decimales en el factor
            if "Tasa" in p: return f"{x*100:.2f}%"
            return f"\${x:,.2f}"
        df_audit["Valor"] = df_audit.apply(lambda x: fmt(x["Valor"], x["Paso"]), axis=1)
        st.dataframe(df_audit, hide_index=True, use_container_width=True)

    with tab_imss:
        st.subheader("Cuotas Obreras")
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Concepto", "Monto"])
        total_row = pd.DataFrame([{"Concepto": "TOTAL IMSS", "Monto": imss}])
        df_imss = pd.concat([df_imss, total_row], ignore_index=True)
        st.dataframe(df_imss.style.format({"Monto": "\${:,.2f}"}), hide_index=True, use_container_width=True)
