import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np


# En sensibilidad.py

# Modifica la primera línea para recibir las variables:
    def mostrar_sensibilidad(eth_sys, mosto, K410):


    st.title("📊 Análisis de Sensibilidad Avanzado")
    
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
            st.subheader("1. Sensibilidad de la Temperatura del Mosto")
            
            t_mosto_rango = np.linspace(30, 90, 10)  # Rango de 30°C a 90°C
            energia_hx = []
            
            # Nota técnica: BioSTEAM usualmente trabaja en Kelvin (K) y Pascales (Pa) o bar.
            # Asegúrate de usar las unidades correctas de tu simulación.
            t_flash_fija = 110 + 273.15   # 110°C convertidos a Kelvin
            p_flash_fija = 1.01325        # 1 atm convertida a bar (o usa 101325 si es en Pa)
            
            for t in t_mosto_rango:
                # A. Fijamos la temperatura variable del mosto en la corriente de entrada
                mosto.T = t + 273.15  # Convertimos el paso actual a Kelvin
                
                # B. ESCENARIO FIJO: Forzamos las condiciones fijas en el separador K410
                W310.T = t_flash_fija
                K410.P = p_flash_fija
                
                # C. Corremos los balances de materia y energía con la nueva configuración
                eth_sys.simulate()
                
                # D. Recolectamos el consumo energético de los intercambiadores (HXutility)
                # Sumamos la carga térmica absoluta (|Q|) en kW de todas las utilidades de calor/frío
                q_total_kw = sum(abs(u.duty) for u in eth_sys.units if hasattr(u, 'duty')) / 3600
                energia_hx.append(q_total_kw)
            
            # Creamos el DataFrame y la gráfica con Plotly
            df1 = pd.DataFrame({
                "Temperatura Mosto (°C)": t_mosto_rango, 
                "Consumo Energético Total (kW)": energia_hx
            })
            
            fig1 = px.line(
                df1, 
                x="Temperatura Mosto (°C)", 
                y="Consumo Energético Total (kW)",
                markers=True,
                title="Impacto de T_mosto en Consumo Energético (Fijo: Flash a 110°C y 1 atm)"
            )
            
            # Estilizado de la gráfica
            fig1.update_traces(line_color="#FF4B4B") # Color rojo Streamlit
            st.plotly_chart(fig1, use_container_width=True)
            
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
