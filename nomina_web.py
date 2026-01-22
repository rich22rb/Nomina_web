import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json

st.set_page_config(page_title="Nómina Online IA", page_icon="🌐", layout="wide")

# --- 1. AUTENTICACIÓN ---
try:
    # Intenta leer la llave de los secretos (para la nube)
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_ok = True
    else:
        # Si estás en local y no tienes secrets, intenta buscarla manual o avisa
        api_ok = False
except:
    api_ok = False

# --- 2. DATOS POR DEFECTO (Respaldo 2025) ---
# Usamos esto si no hay internet o falla la IA
TABLA_DEFAULT = [
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

if "tabla_isr" not in st.session_state:
    st.session_state["tabla_isr"] = TABLA_DEFAULT
    st.session_state["fuente"] = "Datos Default (2025)"

# --- 3. LÓGICA DE AGENTE WEB (Extracción con IA) ---
def obtener_tablas_desde_web(url):
    """Descarga una web, extrae texto y usa IA para hallar la tabla"""
    try:
        # A. Bajar el contenido de la web simulando ser un navegador
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # B. Limpiar la basura HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        # Borramos menús y scripts para que la IA lea solo el contenido
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
        texto_limpio = soup.get_text(separator=' ', strip=True)[:12000] # Leemos los primeros 12k caracteres
        
        # C. Instrucciones para Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analiza el siguiente texto de una página web fiscal de México.
        
        OBJETIVO: Encuentra la "Tarifa aplicable para el cálculo de los pagos provisionales mensuales" (Tabla ISR Mensual).
        
        SALIDA OBLIGATORIA: Un JSON válido (lista de listas).
        Formato: [[Limite_Inferior, Cuota_Fija, Porcentaje_Decimal], ...]
        Ejemplo: [[0.01, 0.0, 0.0192], [746.04, 14.32, 0.0640]]
        
        IMPORTANTE: 
        - Convierte porcentajes a decimal (ej: 30% -> 0.30).
        - Extrae SOLO la tabla MENSUAL (ignora anual, quincenal, subsidio).
        
        TEXTO WEB:
        {texto_limpio}
        """
        
        respuesta = model.generate_content(prompt)
        
        # D. Convertir respuesta de texto a datos reales
        json_str = respuesta.text.replace("```json", "").replace("```", "").strip()
        tabla_nueva = json.loads(json_str)
        
        # Validación simple: Si la tabla tiene más de 5 renglones, es válida
        if len(tabla_nueva) > 5:
            return tabla_nueva
        else:
            return None

    except Exception as e:
        st.error(f"Error leyendo la web: {e}")
        return None

def calcular_nomina(bruto, periodo, tabla):
    # Paso 1: Convertir todo a MENSUAL
    factor = 30.4 if periodo == "Diario" else (2 if periodo == "Quincenal" else 1)
    if periodo == "Semanal": factor = 30.4 / 7
    
    sueldo_mensual = bruto * factor
    
    # Paso 2: Calcular ISR usando la tabla activa
    limite, cuota, porc = 0, 0, 0
    for row in tabla:
        if sueldo_mensual >= row[0]:
            limite, cuota, porc = row[0], row[1], row[2]
        else:
            break
            
    isr_mensual = ((sueldo_mensual - limite) * porc) + cuota
    
    # Paso 3: Calcular IMSS (Estimado)
    imss_mensual = sueldo_mensual * 0.027
    if imss_mensual > 18000: imss_mensual = 18000 # Tope de ley aprox
    
    # Paso 4: Regresar al periodo original
    return {
        "Bruto": bruto,
        "ISR": isr_mensual / factor,
        "IMSS": imss_mensual / factor,
        "Neto": bruto - (isr_mensual/factor) - (imss_mensual/factor)
    }

# --- 4. INTERFAZ VISUAL ---
st.title("🌐 Nómina Inteligente (Online)")

# BARRA LATERAL (Configuración)
with st.sidebar:
    st.header("Fuente de Datos")
    
    # Estado actual
    if st.session_state['fuente'] == "Datos Default (2025)":
        st.warning(f"⚠️ Usando: {st.session_state['fuente']}")
    else:
        st.success(f"✅ Usando: {st.session_state['fuente']}")
    
    st.markdown("---")
    st.subheader("Actualizar Tablas")
    # URL sugerida (puedes cambiarla)
    url_input = st.text_input("URL de la Tabla ISR:", value="https://www.elcontribuyente.mx/2025/12/tablas-isr-2026/")
    
    if st.button("🌐 Buscar y Extraer Datos"):
        if api_ok:
            with st.spinner("🤖 Leyendo sitio web..."):
                nueva_tabla = obtener_tablas_desde_web(url_input)
                if nueva_tabla:
                    st.session_state["tabla_isr"] = nueva_tabla
                    st.session_state["fuente"] = "Extraído de Internet"
                    st.success("¡Datos actualizados!")
                    st.rerun() # Recarga la página para mostrar cambios
                else:
                    st.error("No encontré una tabla válida en esa página.")
        else:
            st.error("⚠️ Falta API Key. Configúrala en .streamlit/secrets.toml")

    with st.expander("Ver Tabla Técnica (Debug)"):
        st.dataframe(pd.DataFrame(st.session_state["tabla_isr"], columns=["LimInf", "Cuota", "%"]), hide_index=True)

# PANEL PRINCIPAL
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Datos del Empleado")
    periodo = st.selectbox("Periodo de Pago", ["Mensual", "Quincenal", "Semanal"])
    sueldo = st.number_input("Sueldo Bruto", value=18000.0, step=100.0)

with col2:
    st.subheader("Resultado")
    if st.button("Calcular Nómina 🚀", use_container_width=True):
        res = calcular_nomina(sueldo, periodo, st.session_state["tabla_isr"])
        
        st.divider()
        # Métricas grandes
        c1, c2, c3 = st.columns(3)
        c1.metric("Bruto", f"${res['Bruto']:,.2f}")
        c2.metric("Impuestos", f"-${res['ISR']+res['IMSS']:,.2f}", delta_color="inverse")
        c3.metric("NETO A PAGAR", f"${res['Neto']:,.2f}", delta_color="normal")
        
        # Gráfica
        datos_grafica = pd.DataFrame({
            'Concepto': ['Neto', 'ISR', 'IMSS'],
            'Monto': [res['Neto'], res['ISR'], res['IMSS']]
        })
        grafica = alt.Chart(datos_grafica).mark_bar().encode(
            x='Monto',
            y=alt.Y('Concepto', sort='-x'),
            color='Concepto',
            tooltip=['Concepto', 'Monto']
        )
        st.altair_chart(grafica, use_container_width=True)