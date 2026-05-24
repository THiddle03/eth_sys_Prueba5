import streamlit as st
import biosteam as bst
import thermosteam as tmo
import pandas as pd
import ollama as olla
import os
import uuid
import streamlit.components.v1 as components
import numpy as np

# =========================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONSTANTES
# =========================================================================
st.set_page_config(page_title="Simulador Bioetanol Pro v5", layout="wide")

# Mapeo de coordenadas para el archivo D_eth_sys.svg
ZONAS_EQUIPOS = {
    "P-110": [170, 55, 55, 55],
    "W-210": [375, 95, 95, 75],
    "W-310": [510, 290, 80, 70],
    "V-411": [660, 390, 60, 45],
    "K-410": [855, 320, 95, 180],
    "W-510": [975, 490, 80, 90],
    "P-510": [1040, 675, 60, 45],
    "Producto Final": [970, 725, 180, 100]
}

# Inicializar el control de navegación si no existe
if 'pagina' not in st.session_state:
    st.session_state['pagina'] = 'inicio'

# =========================================================================
# 2. FUNCIONES SOURCING Y CÁLCULO (MOTOR BIOSTEAM)
# =========================================================================
def correr_simulacion(t_mosto, t_flash, p_flash, 
                      precio_elec, precio_vapor, precio_agua, precio_mp, precio_etanol):
    
                          
    bst.main_flowsheet.clear()
    chemicals = tmo.Chemicals(["Water", "Ethanol"])
    bst.settings.set_thermo(chemicals)

    bst.PowerUtility.price = precio_elec
    vapor = bst.HeatUtility.get_agent("low_pressure_steam")
    vapor.heat_transfer_price = precio_vapor
    agua = bst.HeatUtility.get_agent("cooling_water")
    agua.heat_transfer_price = precio_agua

    mosto = bst.Stream("1_Mosto", Water=900, Ethanol=100, units="kg/hr",
                       T=t_mosto + 273.15, P=101325)
    mosto.price = precio_mp
    vinazas_retorno = bst.Stream("10_Vinazas_Retorno", T=t_flash+273.15, P=3*101325)

    P110 = bst.Pump("P110", ins=mosto, P=4*101325, outs=("2_Mosto_Presión"))
    W210 = bst.HXprocess("W210", ins=(P110-0, vinazas_retorno), outs=("4_Mosto_Pre", "3_Drenaje"), phase0="l", phase1="l")
    W210.outs[0].T = 85 + 273.15
    W310 = bst.HXutility("W310", ins=W210-0, outs="5_Líquido_Caliente", T=t_flash+273.15)
    V411 = bst.IsenthalpicValve("V411", ins=W310-0, outs="6_Mezcla_Flash", P=p_flash*101325)
    K410 = bst.Flash("K410", ins=V411-0, outs=("7_Vapor", "8_Vinazas"), P=p_flash*101325, Q=0)
    W510 = bst.HXutility("W510", ins=K410-0, outs="9_Producto_Final", T=25+273.15)
    
    producto = W510.outs[0]
    producto.price = precio_etanol
    P510 = bst.Pump("P510", ins=K410-1, outs=vinazas_retorno, P=3*101325)

    eth_sys = bst.System("eth_sys", path=(P110, W210, W310, V411, K410, W510, P510))
    
    try:
        eth_sys.simulate()
    except Exception as e:
        return None, None, None, None, None, f"Error: {e}"

    datos_mat = []
    for s in eth_sys.streams:
        if s.F_mass > 0.01:
            datos_mat.append({
                "Corriente": s.ID,
                "Temp (°C)": round(s.T - 273.15, 2),
                "Presión (bar)": round(s.P / 100000, 3),
                "Flujo (kg/h)": round(s.F_mass, 2),
                "% Etanol": f"{(s.imass['Ethanol']/s.F_mass if s.F_mass > 0 else 0):.1%}",
                "% Agua": f"{(s.imass['Water']/s.F_mass if s.F_mass > 0 else 0):.1%}"
            })
            
    datos_en = []
    for u in eth_sys.units:
        calor_util = sum([hu.duty for hu in u.heat_utilities])/3600 if hasattr(u, "heat_utilities") else 0
        if u.ID == "W210" and hasattr(u, 'H'):
            calor = u.duty / 3600
        else:
            calor = calor_util
        potencia = u.power_utility.rate if u.power_utility else 0
        if abs(calor) > 0.001 or potencia > 0.001:
            datos_en.append({"Equipo": u.ID, "Calor (kW)": round(calor, 2), "Potencia (kW)": round(potencia, 2)})

# =========================================================================
# 3. TEA Robusto (Simulador económico)
# =========================================================================
                          
    class TEA_Robusto(bst.TEA):
        def _DPI(self, installed_equipment_cost): return self.purchase_cost
        def _TDC(self, DPI): return DPI
        def _FCI(self, TDC): return self.purchase_cost * self.lang_factor
        def _TCI(self, FCI): return FCI + self.WC
        def _FOC(self, FCI): return 0.0
        @property
        def VOC(self): return self.system.material_cost + self.system.utility_cost

    tea = TEA_Robusto(system=eth_sys, IRR=0.15, duration=(2025, 2045), depreciation='MACRS7',
                      income_tax=0.3, operating_days=330, lang_factor=4.0, construction_schedule=(0.4, 0.6),
                      WC_over_FCI=0.05, startup_months=6, startup_FOCfrac=0.5, startup_VOCfrac=0.5,
                      startup_salesfrac=0.5, finance_interest=0, finance_years=0, finance_fraction=0)
    tea.IRR = 0.0
    # CONTROL DE SEGURIDAD: Validar si la corriente tiene masa
    if producto.F_mass == 0:
    # Devolvemos un mensaje amigable en el último elemento (err)
       return None, None, None, None, None, "⚠️ **Alerta Composición Producto Final**: El flujo de etanol es 0 kg/h. Revisa que las temperaturas y presiones de los sliders permitan la separación del etanol."

    # Si tiene masa, procedemos normalmente
    costo_p = tea.solve_price(producto)
    ind_econ = {"Costo Producción ($/kg)": round(costo_p, 3), "Precio Venta ($/kg)": round(precio_etanol, 3),
                "NPV (MUSD)": round(tea.NPV/1e6, 2), "ROI (%)": round(tea.ROI*100, 1), "PBP (Años)": round(tea.PBP, 2)}

   # Asumiendo que 'tea' es tu objeto de análisis económico y 'costo_p' es el precio calculado
    datos_ec = [
        {"Indicador": "Inversión de Capital Total (TCI)", "Valor": tea.TCI, "Unidad": "USD"},
        {"Indicador": "Inversión en Capital Fijo (FCI)", "Valor": tea.FCI, "Unidad": "USD"},
        {"Indicador": "Costo de Operación Anual (AOC)", "Valor": tea.AOC, "Unidad": "USD/año"},
        {"Indicador": "Costo Operativo Variable (VOC)", "Valor": tea.VOC, "Unidad": "USD/año"},
        {"Indicador": "Costo Operativo Fijo (FOC)", "Valor": tea.FOC, "Unidad": "USD/año"},
        {"Indicador": "Ingresos por Ventas Totales", "Valor": tea.sales, "Unidad": "USD/año"},
        {"Indicador": "Precio Mínimo de Venta (MESP)", "Valor": costo_p, "Unidad": "USD/kg"}
    ]

    # Convertimos a DataFrame de Pandas
    df_ec = pd.DataFrame(datos_ec)                       
                          
    p_path = f"pfd_{uuid.uuid4().hex[:8]}.png"
    try:
        eth_sys.diagram(file=p_path.replace(".png", ""), format="png", display=False)
    except:
        p_path = None
# =========================================================================
# 4. ADVERTENCIAS (Temperatura de entraday temperatura W-310)
# =========================================================================
                          
    advertencias = []
    if mosto.phase != 'l' or mosto.V > 0.01:
        advertencias.append(f"⚠️ **Alerta Mosto:** La alimentación ha entrado en ebullición parcial (Fracción de Vapor: {mosto.V:.2%}). La alimentación debe mantenerse puramente líquida.")

    return pd.DataFrame(datos_mat), pd.DataFrame(datos_en), ind_econ, p_path, advertencias, None

# =========================================================================
# 5. PFD INTERACTIVO (Resultados en imagen SVG)
# =========================================================================

def generar_pfd_interactivo(datos_simulacion):
    ruta_svg = "D_eth_sys.svg"
    if not os.path.exists(ruta_svg):
        return None
    
    with open(ruta_svg, "r", encoding="utf-8") as f:
        svg_content = f.read()

    capa_interactiva = ""
    for equipo, pos in ZONAS_EQUIPOS.items():
        id_sim = equipo.replace("-", "").replace(" ", "")
        info = datos_simulacion.get(id_sim, datos_simulacion.get(equipo, {"Estado": "Monitoreando..."}))
        
        tooltip_html = f"<b>{equipo}</b><br>"
        for clave, valor in info.items():
            tooltip_html += f"{clave}: {valor}<br>"
        
        capa_interactiva += f"""
        <rect x="{pos[0]}" y="{pos[1]}" width="{pos[2]}" height="{pos[3]}" 
              fill="white" fill-opacity="0" style="cursor:pointer;"
              onmouseover="showTip(event, '{tooltip_html}')" 
              onmouseout="hideTip()"
              onclick="alert('{equipo}\\n{'-'*15}\\n' + '{tooltip_html}'.replace(/<br>/g, '\\n').replace(/<b>/g, '').replace(/<\\/b>/g, ''))"/>
        """

   

    return f"""
    <div id="wrapper" style="position: relative; display: inline-block; width: 100%;">
        <div id="tooltip-box" style="position: fixed; display: none; background: rgba(20, 20, 20, 0.9); 
             color: #00ffcc; padding: 12px; border-radius: 8px; font-family: 'Segoe UI', Tahoma; 
             font-size: 13px; z-index: 10000; pointer-events: none; border: 1px solid #00ffcc;
             box-shadow: 0px 0px 15px rgba(0,255,204,0.3);"></div>
        {svg_content.replace('</svg>', capa_interactiva + '</svg>')}
    </div>
    <script>
        const tipBox = document.getElementById('tooltip-box');
        function showTip(e, text) {{
            tipBox.innerHTML = text;
            tipBox.style.display = 'block';
            moverTip(e);
        }}
        function hideTip() {{ tipBox.style.display = 'none'; }}
        function moverTip(e) {{
            tipBox.style.left = (e.clientX + 20) + 'px';
            tipBox.style.top = (e.clientY + 20) + 'px';
        }}
        document.addEventListener('mousemove', moverTip);
    </script>
    """

# =========================================================================
# 6. PÁGINA DE INICIO (LANDING PAGE)
# =========================================================================
def mostrar_inicio():
    st.title("💭 Simulador de Planta de Concentración de Etanol con Integración Energética Versión 5")
    st.subheader("Plataforma con Interfaz de Streamlit, simulada en Python con el programa BioSTEAM")
    st.subheader("Introducción a la simulación de procesos y diseño de plantas")
    st.subheader("IQ. Tania Bravo Cassab")
    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""        
        ### 🧪 Sobre el Proceso
       La planta tiene como objetivo concentrar una corriente de alimentación de "Mosto"(solución acuosa de etanol en agua) mediante una separación flash adiabática.
       Se considera una coreinte de recirculación de la corriente de fondo del separador flash "Vinazas" para precalentar la alimentación y reducir el consumo energético.

        ### ⚙️ Características Principales
        *   **Cálculo Termodinámico Riguroso:** Respaldado por el framework *BioSTEAM* y *Thermosteam* para asegurar balances de masa y energía exactos en mezclas no ideales de Etanol y Agua.
        *   **Gemelo Digital Interactivo:** Visualización dinámica a través de un diagrama PFD embebido en SVG con lecturas operativas al pasar el cursor sobre los equipos.
        *   **Análisis Económico (TEA):** Monitoreo instantáneo del Costo de Producción, ROI (Retorno de Inversión), y el valor neto actual (NPV) del diseño.
        *   **Tutor Inteligente Integrado:** Consultas analíticas potenciadas por IA para resolver dudas de diseño y optimizar variables operativas.
        """)
        
        st.write("")
        # Botón con redirección y limpieza para evitar atascos de código
        if st.button("💻 Ingresar al Simulador de Procesos", type="primary", use_container_width=True):
            st.session_state['pagina'] = 'simulacion'
            st.rerun()

    with col2:
        st.info("""
        **💡 Nota de Uso:**
        Para un rendimiento óptimo, asegúrate de mantener la corriente de alimentación en rangos de líquido subenfriado para evitar la cavitación en la bomba de carga inicial P-110.
        """)
        st.metric(label="Estado del Servidor", value="Operativo / En Línea", delta="BioSTEAM v5.0")

# =========================================================================
# 7. PÁGINA DEL SIMULADOR (TU CÓDIGO ORIGINAL MODULARIZADO)
# =========================================================================
def mostrar_simulacion():
    # Botón discreto en la barra lateral para volver a la Home
    if st.sidebar.button("🏠 Volver a Inicio"):
        st.session_state['pagina'] = 'inicio'
        st.rerun()

    st.title("🌡️ Panel de Simulación y Control Operativo")
    
    # CONFIGURACIÓN DE LA BARRA LATERAL
    st.sidebar.header("🌡️ Parámetros Proceso")
    t_mosto = st.sidebar.slider("Temp. Alimentación Mosto (°C)", 25, 150, 50)
    t_flash = st.sidebar.slider("Temp. Salida W310 (°C)", 90, 200, 90)
    p_flash = st.sidebar.slider("Presión Separador K410 (atm)", 0.1, 5.0, 1.0, step=0.1)

    st.sidebar.divider()
    st.sidebar.header("💰 Parámetros Económicos")
    p_elec = st.sidebar.slider("Precio Electricidad ($/kWh)", 0.01, 5.0, 2.0, step=0.5)
    p_agua_c = st.sidebar.slider("Precio Agua Enfr. ($/MJ)", 0.01, 5.0, 2.0, step=0.2)
    p_vapor = st.sidebar.slider("Precio Vapor ($/MJ)", 0.5, 15.0, 5.0, step=1.0)
    p_mp = st.sidebar.slider("Precio Materia Prima ($/kg)", 0.01, 5.0, 2.0, step=0.2)
    p_etanol = st.sidebar.slider("Precio Venta Etanol ($/kg)", 0.1, 6.0, 2.0, step=0.1)

    if st.sidebar.button("Simular Proceso", type="primary"):
        # 1. Recibimos los 6 elementos que devuelve la función (añadimos 'advs')
        dm, de, ec, pf, advs, err = correr_simulacion(
            t_mosto, 
            t_flash, 
            p_flash, 
            p_elec, 
            p_vapor, 
            p_agua_c, 
            p_mp, 
            p_etanol
        )
        
        if err:
            st.error(err)
        else:
            # 2. Guardamos las 5 variables necesarias en la sesión (añadimos 'advs')
            st.session_state['resultados'] = (dm, de, ec, pf, advs)
            st.rerun() # Forzamos el refresco para mostrar resultados inmediatamente

    if st.button("📊 Ver Análisis de Sensibilidad", type="secondary"):
        # Guardamos una copia de los sliders actuales como valores base
        st.session_state['params_base'] = {
            't_mosto': t_mosto, 't_flash': t_flash, 'p_flash': p_flash,
            'p_elec': p_elec, 'p_vapor': p_vapor, 'p_agua_c': p_agua_c,
            'p_mp': p_mp, 'p_etanol': p_etanol
              }
        st.session_state['pagina'] = 'sensibilidad'
        st.rerun()

# =========================================================================
# 8. DESPLIEGUE DE RESULTADOS (Mostrar resultados)
# =========================================================================
    if 'resultados' in st.session_state:
        dm, de, ec, pf, advs = st.session_state['resultados']
        
        if advs:
            for alerta in advs:
                st.warning(alerta)
            st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Balances de Materia")
            st.dataframe(dm, use_container_width=True)
            st.subheader("📈 Economía")
            st.dataframe(ec, use_container_width=True)
            
        with col2:
            st.subheader("⚡ Energía")
            st.dataframe(de, use_container_width=True)

# =========================================================================
# 9. TUTOR IA Interactivo (Ollama - DeepSeek)
# =========================================================================
        st.divider()
        st.subheader("🤖 Tutor IA Interactivo (DeepSeek)")
        
        user_question = st.text_input("Hazle una pregunta al tutor sobre los resultados:")
        
        if st.button("Enviar al Tutor"):
            if user_question:
                with st.spinner('DeepSeek analizando simulación...'):
                    # Importación local de Ollama
                    from ollama import chat
        
                    contexto = f"""
                    Actúa como un tutor experto en simulación de procesos, balances de materia y energía, diseño de plantas y análisis económico. Explica los resultados de forma clara para estudiantes de ingeniería química. Utiliza únicamente los valores calculados o mostrados por la aplicación. No inventes datos. Si falta información, indícalo de forma explícita y sugiere qué dato sería necesario para mejorar el análisis.
                    Resultados: {dm.to_string()}
                    Economía: {ec}
                    Precios: Elec={p_elec}$, Agua={p_agua_c}$, Vapor={p_vapor}$, MP={p_mp}$, Etanol={p_etanol}$.
                    Condiciones: Temp={t_flash}C, Pres={p_flash}atm.
                    Responde en <250 palabras de forma didáctica.
                    """
                    
                    full_prompt = f"{contexto}\n\nPregunta: {user_question}"
                    
                    try:
                        # Llamada oficial usando el SDK de Ollama
                        response = chat(
                            model='deepseek-v4-pro:cloud',
                            messages=[{'role': 'user', 'content': full_prompt}],
                        )
                        
                        # Desplegamos la respuesta en la interfaz de Streamlit
                        st.info(response.message.content)
                        
                    except Exception as e:
                        st.error(f"Error al conectar con Ollama: {e}")
            else:
                st.warning("Por favor, escribe una pregunta primero.")
        
        if pf and os.path.exists(pf):
            st.divider()
            st.image(pf, caption="Gráfico estructural estático (BioSTEAM)")

# =========================================================================
# 10. INTEGRACIÓN SVG (mostrar resultados en SVG)
# =========================================================================
    row_p_final = dm[dm['Corriente'] == '9_Producto_Final']
        if not row_p_final.empty:
            p_bar = row_p_final['Presión (bar)'].values[0]
            p_atm = round(p_bar / 1.01325, 3)
            t_c = row_p_final['Temp (°C)'].values[0]
            f_mass = row_p_final['Flujo (kg/h)'].values[0]
            pct_eth = row_p_final['% Etanol'].values[0]
            pct_agua = row_p_final['% Agua'].values[0]
        else:
            t_c, p_atm, f_mass, pct_eth, pct_agua = "N/D", "N/D", "N/D", "N/D", "N/D"

        datos_actualizados = {
            "P110": {"Potencia": f"{de[de['Equipo']=='P110']['Potencia (kW)'].values[0] if 'P110' in de['Equipo'].values else '0.0'} kW"},
            "W210": {"Carga Térmica": f"{de[de['Equipo']=='W210']['Calor (kW)'].values[0] if 'W210' in de['Equipo'].values else 'Recuperación'} kW"},
            "W310": {"Calor (Vapor)": f"{de[de['Equipo']=='W310']['Calor (kW)'].values[0] if 'W310' in de['Equipo'].values else '0.0'} kW"},
            "V411": {"Presión": f"{dm[dm['Corriente']=='6_Mezcla_Flash']['Presión (bar)'].values[0] if '6_Mezcla_Flash' in dm['Corriente'].values else '1.0'} bar"},
            "K410": {
                "Temp": f"{dm[dm['Corriente']=='7_Vapor']['Temp (°C)'].values[0] if '7_Vapor' in dm['Corriente'].values else '92.17'} °C",
                "Presión": f"{dm[dm['Corriente']=='7_Vapor']['Presión (bar)'].values[0] if '7_Vapor' in dm['Corriente'].values else '1.00'} bar"
            },
            "W510": {"Calor (Enf.)": f"{de[de['Equipo']=='W510']['Calor (kW)'].values[0] if 'W510' in de['Equipo'].values else '0.0'} kW"},
            "P510": {"Potencia": f"{de[de['Equipo']=='P510']['Potencia (kW)'].values[0] if 'P510' in de['Equipo'].values else '0.0'} kW"},
            "Producto Final": {
                "Temperatura": f"{t_c} °C",
                "Presión": f"{p_atm} atm",
                "Flujo Másico": f"{f_mass} kg/h",
                "% Etanol": pct_eth,
                "% Agua": pct_agua
            }
        }

        st.divider()
        st.subheader("🧪 Gemelo Digital: Monitoreo en Tiempo Real")
        
        html_interactivo = generar_pfd_interactivo(datos_actualizados)
        
        if html_interactivo is None:
            st.error("🚨 **Error de visualización:** El archivo `'D_eth_sys.svg'` no fue localizado en el servidor. Revisa que esté subido en la raíz de GitHub con ese nombre exacto.")
        else:
            st.info("Pase el mouse sobre los equipos o la línea de 9_Producto Final para observar los resultados en vivo")
            components.html(html_interactivo, height=750, scrolling=True)
    else:
        st.info("Por favor, ajusta los parámetros en la barra lateral y presiona 'Simular Proceso' para ver los resultados analíticos.")

# =========================================================================
# 11. ENRUTADOR DE PÁGINAS (FLUJO PRINCIPAL)
# =========================================================================
if st.session_state['pagina'] == 'inicio':
    mostrar_inicio()
elif st.session_state['pagina'] == 'simulacion':
    mostrar_simulacion()    
elif st.session_state['pagina'] == 'sensibilidad':
    from sensibilidad import mostrar_sensibilidad
    # Pasamos la función como un objeto y los parámetros de los sliders
    mostrar_sensibilidad(correr_simulacion, st.session_state.get('params_base', {}))
