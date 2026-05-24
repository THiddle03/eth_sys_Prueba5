import streamlit as st
import os
import base64

def visualizar_y_descargar_pdf(nombre_archivo, titulo_bonito):
    """Función auxiliar para leer, mostrar en iframe y permitir descarga de un PDF"""
    ruta_completa = f"{nombre_archivo}.pdf" # Asume que los subes como DB.pdf, DFP.pdf, etc.
    
    if os.path.exists(ruta_completa):
        # 1. Botón de Descarga Nativo
        with open(ruta_completa, "rb") as f:
            pdf_bytes = f.read()
            
        st.download_button(
            label=f"📥 Descargar {titulo_bonito} (PDF)",
            data=pdf_bytes,
            file_name=f"{nombre_archivo}.pdf",
            mime="application/pdf",
            type="primary"
        )
        
        st.write("") # Espacio visual
        
        # 2. Visor de PDF embebido mediante iframe y Base64
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
    else:
        st.error(f"🚨 **Archivo no encontrado:** El archivo `'{ruta_completa}'` no está en la raíz del repositorio. Asegúrate de subirlo a GitHub con ese nombre exacto (respetando mayúsculas y la extensión .pdf).")

def mostrar_diagramas():
    st.title("🗺️ Planos y Diagramas de Ingeniería del Proceso")
    st.write("Consulta y descarga la documentación técnica oficial de la planta de concentración de bioetanol.")
    
    # Botón para regresar al simulador de forma segura
    if st.button("⬅️ Volver al Panel de Simulación"):
        st.session_state['pagina'] = 'simulacion'
        st.rerun()
        
    st.divider()
    
    # Creamos 3 pestañas limpias para no saturar la pantalla
    tab1, tab2, tab3 = st.tabs([
        "📊 1. Diagrama de Bloques (DB)", 
        "📈 2. Diagrama de Flujo de Proceso (DFP)", 
        "🛠️ 3. Diagrama de Tuberías e Instrumentación (DTI)"
    ])
    
    with tab1:
        st.subheader("Diagrama de Bloques del Proceso (DB)")
        st.info("Muestra la estructura general de las etapas del proceso, flujos principales y balances globales globales de masa.")
        visualizar_y_descargar_pdf("DB", "Diagrama de Bloques")
        
    with tab2:
        st.subheader("Diagrama de Flujo de Proceso (DFP / PFD)")
        st.info("Muestra la interconexión de los equipos principales (P-110, W-210, K-410), la recirculación de vinazas y los controles operativos principales.")
        visualizar_y_descargar_pdf("DFP", "Diagrama de Flujo de Proceso")
        
    with tab3:
        st.subheader("Diagrama de Tubería e Instrumentación (DTI / P&ID)")
        st.info("Detalle mecánico de tuberías, especificación de válvulas, lazos de control automático e instrumentación de seguridad del lazo flash.")
        visualizar_y_descargar_pdf("DTI", "Diagrama de Tubería e Instrumentación")
