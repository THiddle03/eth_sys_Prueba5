import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def mostrar_sensibilidad(correr_simulacion_func, params_base):
    st.title("📊 Análisis de Sensibilidad del Proceso")
    
    # Botón para regresar de forma segura
    if st.button("⬅️ Volver al Panel de Simulación"):
        st.session_state['pagina'] = 'simulacion'
        st.rerun()
        
    # Verificar que existan parámetros base, de lo contrario asignar por defecto
    if not params_base:
        st.warning("No se detectaron parámetros base de la simulación. Se usarán valores estándar.")
        params_base = {
            't_mosto': 50, 't_flash': 110, 'p_flash': 1.0,
            'p_elec': 0.085, 'p_vapor': 0.025, 'p_agua_c': 0.0005,
            'p_mp': 0.05, 'p_etanol': 1.2
        }

    st.markdown("### Generación de Escenarios Dinámicos")
    st.write("El sistema ejecutará iteraciones en BioSTEAM manteniendo los parámetros económicos y operativos de tus sliders constantes, modificando únicamente las variables de interés.")

    if st.button("Ejecutar Análisis de Sensibilidad", type="primary", use_container_width=True):
        with st.spinner("Corriendo simulaciones iterativas en BioSTEAM... Por favor espera."):
            
            # =========================================================================
            # GRÁFICA 1: T_mosto vs Consumo de Energía (Fijo: t_flash=110°C, p_flash=1 atm)
            # =========================================================================
            t_mosto_rango = np.linspace(30, 90, 11) # 8 puntos entre 30 y 90 °C
            datos_g1 = []
            
            for t in t_mosto_rango:
                dm, de, ec, pf, advs, err = correr_simulacion_func(
                    t_mosto=t, 
                    t_flash=110.0, # Condición fija solicitada
                    p_flash=1.0,   # Condición fija solicitada
                    precio_elec=params_base['p_elec'],
                    precio_vapor=params_base['p_vapor'],
                    precio_agua=params_base['p_agua_c'],
                    precio_mp=params_base['p_mp'],
                    precio_etanol=params_base['p_etanol']
                )
                if not err and de is not None:
                    # Sumamos el calor absoluto consumido/removido reportado en tu df 'de'
                    total_calor = de['Calor (kW)'].abs().sum()
                    datos_g1.append({"T_mosto": t, "Energia_Total_kW": total_calor})
            
            df_g1 = pd.DataFrame(datos_g1)
            
            # =========================================================================
            # GRÁFICA 2: Presión Separador vs % Etanol en '9_Producto_Final'
            # =========================================================================
            p_flash_rango = np.linspace(0.2, 5.0, 8) # 8 puntos de presión de 0.2 a 5 atm
            datos_g2 = []
            
            for p in p_flash_rango:
                dm, de, ec, pf, advs, err = correr_simulacion_func(
                    t_mosto=params_base['t_mosto'],
                    t_flash=params_base['t_flash'],
                    p_flash=p,
                    precio_elec=params_base['p_elec'],
                    precio_vapor=params_base['p_vapor'],
                    precio_agua=params_base['p_agua_c'],
                    precio_mp=params_base['p_mp'],
                    precio_etanol=params_base['p_etanol']
                )
                if not err and dm is not None:
                    # Buscamos la corriente '9_Producto_Final' en tu df 'dm'
                    row = dm[dm['Corriente'] == '9_Producto_Final']
                    if not row.empty:
                        # Tu df guarda el % como string (ej: "85.2%"), lo convertimos a flotante
                        pct_str = row['% Etanol'].values[0].replace('%', '')
                        datos_g2.append({"Presion_atm": p, "Pureza_Etanol": float(pct_str)})
            
            df_g2 = pd.DataFrame(datos_g2)
            
            # =========================================================================
            # GRÁFICA 3: Precio de Venta vs ROI
            # =========================================================================
            precio_rango = np.linspace(0.5, 5.0, 8) # Rango comercial de precios de venta
            datos_g3 = []
            
            for pr in precio_rango:
                dm, de, ec, pf, advs, err = correr_simulacion_func(
                    t_mosto=params_base['t_mosto'],
                    t_flash=params_base['t_flash'],
                    p_flash=params_base['p_flash'],
                    precio_elec=params_base['p_elec'],
                    precio_vapor=params_base['p_vapor'],
                    precio_agua=params_base['p_agua_c'],
                    precio_mp=params_base['p_mp'],
                    precio_etanol=pr
                )
                if not err and ec is not None:
                    # Tu diccionario 'ec' ya guarda el ROI (%) calculado directamente
                    datos_g3.append({"Precio_Venta": pr, "ROI": ec.get("ROI (%)", 0)})
                    
            df_g3 = pd.DataFrame(datos_g3)

            # =========================================================================
            # DESPLIEGUE DE GRÁFICAS EN INTERFAZ
            # =========================================================================
            st.success("¡Análisis completado exitosamente!")
            
            # Gráfica 1
            if not df_g1.empty:
                fig1 = px.line(df_g1, x="T_mosto", y="Energia_Total_kW", markers=True,
                               labels={"T_mosto": "Temperatura de Alimentación Mosto (°C)", "Energia_Total_kW": "Consumo Energético Total (kW)"},
                               title="1. Impacto de T_mosto en Consumo Energético (Fijo: Flash a 110°C y 1 atm)")
                fig1.update_traces(line_color="#FF4B4B")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.error("No se pudieron generar datos para la Gráfica 1 debido a errores de convergencia.")

            st.divider()

            # Gráfica 2
            if not df_g2.empty:
                fig2 = px.line(df_g2, x="Presion_atm", y="Pureza_Etanol", markers=True,
                               labels={"Presion_atm": "Presión del Separador K410 (atm)", "Pureza_Etanol": "Concentración de Etanol (%)"},
                               title="2. Presión del Separador K410 vs. Pureza del Producto Final")
                fig2.update_traces(line_color="#00CC96")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.error("No se pudieron generar datos para la Gráfica 2. Valida las condiciones del Flash.")

            st.divider()

            # Gráfica 3
            if not df_g3.empty:
                fig3 = px.line(df_g3, x="Precio_Venta", y="ROI", markers=True,
                               labels={"Precio_Venta": "Precio de Venta Sugerido ($/kg)", "ROI": "Retorno de Inversión - ROI (%)"},
                               title="3. Viabilidad Financiera: Precio de Venta vs. Retorno de Inversión (ROI)")
                fig3.update_traces(line_color="#AB63FA")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.error("No se pudieron generar datos para la Gráfica 3. Revisa la configuración del TEA.")
