import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

# CONFIGURACIÓN DE PÁGINA "FULL WIDTH"
st.set_page_config(page_title="Nómina 2026 | Enterprise", page_icon="🏢", layout="wide")

# --- 1. CONSTANTES LEGALES 2026 ---
VALORES_2026 = {
    "UMA": 117.31,
    "SALARIO_MINIMO": 315.04,
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

# --- 2. ESTILOS CSS PROFESIONALES (MODERNO) ---
st.markdown("""
<style>
    /* Fondo general más limpio */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Estilo de Tarjetas (Cards) */
    .pro-card {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Tipografía */
    h1, h2, h3 {
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    
    /* Métricas */
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 8px;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    
    /* Colores semánticos */
    .text-green { color: #10b981 !important; }
    .text-red { color: #ef4444 !important; }
    .text-blue { color: #3b82f6 !important; }
    
    /* Tablas más limpias */
    .stDataFrame { border: none !important; }
    
</style>
""", unsafe_allow_html=True)

# --- 3. MOTORES DE CÁLCULO ---
def calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base):
    base_mensual = sueldo_diario * dias_mes_base
    limite, cuota, porc = 0, 0, 0
    for row in TABLA_ISR_MENSUAL:
        if base_mensual >= row["limite"]:
            limite, cuota, porc = row["limite"], row["cuota"], row["porc"]
        else: break
    excedente = base_mensual - limite
    marginal = excedente * porc
    isr_mensual = marginal + cuota
    factor = dias_pago / dias_mes_base
    isr_periodo = isr_mensual * factor
    
    desglose = {
        "Base Mensual": base_mensual,
        "Límite Inferior": limite,
        "Excedente": excedente,
        "Tasa": porc,
        "Marginal": marginal,
        "Cuota Fija": cuota,
        "ISR Mes": isr_mensual,
        "Factor": factor,
        "Retención": isr_periodo
    }
    return isr_periodo, desglose

def calcular_imss_detallado(sbc, dias):
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

# --- 4. INTERFAZ ---

# Header Minimalista
c_logo, c_title = st.columns([1, 10])
with c_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=60)
with c_title:
    st.markdown("# Nómina Enterprise 2026")
    st.markdown("<div style='margin-top: -15px; color: #64748b;'>Sistema de Cálculo Fiscal y Seguridad Social</div>", unsafe_allow_html=True)

st.markdown("---")

# --- AREA DE INPUTS (CARD FLOTANTE) ---
st.markdown('<div class="pro-card">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    criterio = st.selectbox("📅 Criterio de Días", ["Comercial (30)", "Fiscal (30.4)"])
    dias_mes_base = 30.0 if "Comercial" in criterio else 30.4

with col2:
    periodo = st.selectbox("⏱️ Frecuencia de Pago", ["Quincenal", "Semanal", "Mensual"])
    if periodo == "Quincenal": dias_pago = 15
    elif periodo == "Semanal": dias_pago = 7
    else: dias_pago = dias_mes_base
    
with col3:
    tipo_ingreso = st.selectbox("💰 Tipo de Ingreso", ["Bruto Mensual", "Bruto por Periodo"])

with col4:
    monto_input = st.number_input(f"Monto ({tipo_ingreso})", value=20000.0, step=500.0)
    if tipo_ingreso == "Bruto Mensual":
        sueldo_diario = monto_input / dias_mes_base
    else:
        sueldo_diario = monto_input / dias_pago

# Fila 2 de inputs
col5, col6 = st.columns([1, 3])
with col5:
    antig = st.number_input("🎂 Años Antigüedad", 0, 50, 0)
with col6:
    # AQUÍ ARREGLAMOS EL TEXTO PEGADO USANDO HTML PURO
    st.info(f"ℹ️ **Base de Cálculo:** El sistema integró un Salario Diario de **${sueldo_diario:,.2f}** para efectos fiscales.")

if st.button("Generar Cálculo", type="primary", use_container_width=True):
    st.session_state.run = True
st.markdown('</div>', unsafe_allow_html=True) # Cierra card inputs


# --- RESULTADOS ---
if "run" in st.session_state:
    
    # Lógica
    if antig == 0: dias_vac = 12
    else: dias_vac = 14
    factor_int = 1 + ((15 + (dias_vac*0.25))/365)
    sbc = min(sueldo_diario * factor_int, VALORES_2026["UMA"] * 25)
    
    bruto = sueldo_diario * dias_pago
    imss, df_imss_raw = calcular_imss_detallado(sbc, dias_pago)
    isr, df_isr_raw = calcular_isr_proyeccion(sueldo_diario, dias_pago, dias_mes_base)
    neto = bruto - imss - isr
    
    # --- DASHBOARD METRICS ---
    st.markdown("### 📊 Resultado del Periodo")
    
    k1, k2, k3, k4 = st.columns(4)
    
    # Usamos HTML Injection para control total del diseño de las cards
    with k1:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">Ingreso Bruto</div>
            <div class="metric-value">&#36;{bruto:,.2f}</div>
            <div class="metric-sub">{dias_pago} días laborados</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">ISR (Impuesto)</div>
            <div class="metric-value text-red">-&#36;{isr:,.2f}</div>
            <div class="metric-sub">Tasa Efec: {(isr/bruto)*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="pro-card">
            <div class="metric-label">IMSS (Seguridad)</div>
            <div class="metric-value text-red">-&#36;{imss:,.2f}</div>
            <div class="metric-sub">SBC: &#36;{sbc:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="pro-card" style="border-left: 5px solid #10b981;">
            <div class="metric-label text-green">Neto a Pagar</div>
            <div class="metric-value text-green">&#36;{neto:,.2f}</div>
            <div class="metric-sub">Disponible en cuenta</div>
        </div>
        """, unsafe_allow_html=True)

    # --- TABS DE DETALLE ---
    
    tab_vis, tab_isr, tab_imss = st.tabs(["🧠 Análisis Financiero", "🏛️ Auditoría Fiscal (ISR)", "🏥 Seguridad Social (IMSS)"])
    
    with tab_vis:
        st.markdown('<div class="pro-card">', unsafe_allow_html=True)
        cg1, cg2 = st.columns([1, 2])
        
        with cg1:
            # Gráfica Dona Minimalista
            source = pd.DataFrame({"Concepto": ["Neto", "ISR", "IMSS"], "Monto": [neto, isr, imss]})
            base = alt.Chart(source).encode(theta=alt.Theta("Monto", stack=True))
            pie = base.mark_arc(innerRadius=65, outerRadius=105).encode(
                color=alt.Color("Concepto", scale=alt.Scale(domain=['Neto', 'ISR', 'IMSS'], range=['#10b981', '#3b82f6', '#f59e0b'])),
                tooltip=["Concepto", alt.Tooltip("Monto", format="$,.2f")]
            )
            st.altair_chart(pie, use_container_width=True)
            
        with cg2:
            st.markdown("#### Distribución de Ingresos")
            # Corrección de espacios en texto usando HTML entities
            st.markdown(f"""
            <ul style="line-height: 2.2;">
                <li>De cada <b>&#36;1,000.00 pesos</b> que genera tu puesto:</li>
                <li>Te llevas a casa: <b class="text-green">&#36;{(neto/bruto)*1000:,.2f}</b> libres.</li>
                <li>Pagas de impuestos: <b class="text-blue">&#36;{(isr/bruto)*1000:,.2f}</b> (ISR).</li>
                <li>Aportas al seguro: <b class="text-red">&#36;{(imss/bruto)*1000:,.2f}</b> (IMSS).</li>
            </ul>
            """, unsafe_allow_html=True)
            
            st.caption("Cálculo basado en tablas oficiales 2026 (Anexo 8 RMF).")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_isr:
        # Tabla limpia sin índice
        data_isr = [
            {"Concepto": "1. Base Gravable Mensual", "Monto": df_isr_raw["Base Mensual"]},
            {"Concepto": "2. (-) Límite Inferior", "Monto": df_isr_raw["Límite Inferior"]},
            {"Concepto": "3. (=) Excedente", "Monto": df_isr_raw["Excedente"]},
            {"Concepto": "4. (x) Tasa Aplicable", "Monto": df_isr_raw["Tasa"]},
            {"Concepto": "5. (=) Impuesto Marginal", "Monto": df_isr_raw["Marginal"]},
            {"Concepto": "6. (+) Cuota Fija", "Monto": df_isr_raw["Cuota Fija"]},
            {"Concepto": "7. (=) ISR Mensual", "Monto": df_isr_raw["ISR Mes"]},
            {"Concepto": f"8. (x) Factor Periodo ({periodo})", "Monto": df_isr_raw["Factor"]},
            {"Concepto": "9. (=) RETENCIÓN FINAL", "Monto": isr},
        ]
        df_audit = pd.DataFrame(data_isr)
        
        # Formateador
        def fmt(x, label):
            if "Factor" in label: return f"{x:.4f}"
            if "Tasa" in label: return f"{x*100:.2f}%"
            return f"${x:,.2f}"
            
        df_audit["Monto"] = df_audit.apply(lambda x: fmt(x["Monto"], x["Concepto"]), axis=1)
        
        st.dataframe(
            df_audit, 
            hide_index=True, 
            use_container_width=True,
            column_config={"Concepto": st.column_config.TextColumn("Operación", width="large")}
        )

    with tab_imss:
        # Tabla limpia con Total
        df_imss = pd.DataFrame(list(df_imss_raw.items()), columns=["Rama", "Importe"])
        total_row = pd.DataFrame([{"Rama": "TOTAL RETENCIÓN IMSS", "Importe": imss}])
        df_imss = pd.concat([df_imss, total_row], ignore_index=True)
        
        st.dataframe(
            df_imss, 
            hide_index=True, 
            use_container_width=True, 
            column_config={"Importe": st.column_config.NumberColumn("Descuento", format="$%.2f")}
        )
