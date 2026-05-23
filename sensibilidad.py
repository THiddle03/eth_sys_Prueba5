import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def mostrar_sensibilidad():
    st.title("📊 Análisis de Sensibilidad")
    
    # Botón para regresar
    if st.button("⬅️ Volver a la Simulación"):
        st.session_state['pagina'] = 'simulacion'
        st.rerun()
        
    st.write("Haz clic en el botón de abajo para calcular los escenarios dinámicos.")
    
    if st.button("Calcular Curvas de Sensibilidad", type="primary"):
        with st.spinner("🤖 Ejecutando simulaciones iterativas en BioSTEAM..."):
            
            # ----------------------------------------------------
            # GRÁFICA 1: T_mosto vs Consumo de Energía (HXutility)
            # ----------------------------------------------------
            t_mosto_rango = np.linspace(30, 90, 10) # 10 puntos de 30°C a 90°C
            energia_hx = []
            
            for t in t_mosto_rango:
                # 1. Modificas la temperatura en tu corriente de entrada: mosto.T = t + 273.15
                # 2. Corres la simulación: sistema.simulate()
                # 3. Sumas la energía de los intercambiadores (ejemplo conceptual):
                # q_total = sum(u.H for u in unidades if isinstance(u, bst.HXutility))
                energia_hx.append(t * 1.5) # Reemplaza con tu variable real de BioSTEAM
                
            df1 = pd.DataFrame({"T_mosto": t_mosto_rango, "Energia_kW": energia_hx})
            fig1 = px.line(df1, x="T_mosto", y="Energia_kW", title="Impacto de T_mosto en Consumo Energético")
            
            # ----------------------------------------------------
            # GRÁFICA 2: P_K410 vs % Etanol en '9_Producto_Final'
            # ----------------------------------------------------
            p_flash_rango = np.linspace(0.1, 5.0, 10) # de 0.1 a 2 atm
            concen_etanol = []
            
            for p in p_flash_rango:
                # K410.P = p
                # sistema.simulate()
                # %_etanol = corriente_9.imass['Ethanol'] / corriente_9.F_mass * 100
                concen_etanol.append(100 - (p * 15)) # Reemplaza con tu variable real
                
            df2 = pd.DataFrame({"Presion_atm": p_flash_rango, "Concentracion": concen_etanol})
            fig2 = px.line(df2, x="Presion_atm", y="Concentracion", title="Presión de Flash vs Pureza de Etanol")
            
            # ----------------------------------------------------
            # GRÁFICA 3: Precio de Venta vs ROI
            # ----------------------------------------------------
            precio_rango = np.linspace(0.5, 2.5, 10) # de 0.5 a 2.5 USD/kg
            roi_valores = []
            
            for precio in precio_rango:
                # producto_final.price = precio
                # sistema.simulate()
                # roi = tea.ROI * 100 (BioSTEAM devuelve el ROI en fracción decimal)
                roi_valores.append((precio * 20) - 15) # Reemplaza con tu variable real
                
            df3 = pd.DataFrame({"Precio_USD": precio_rango, "ROI": roi_valores})
            fig3 = px.line(df3, x="Precio_USD", y="ROI", title="Precio de Venta Sugerido vs Retorno de Inversión (ROI)")
            
            # --- Desplegar las gráficas en Streamlit ---
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.plotly_chart(fig3, use_container_width=True)
