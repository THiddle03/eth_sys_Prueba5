# Proyecto Final del Curso Introducción a la simulación de procesos y diseño de plantas

#A continuación se explicará la secuencia que compone el presente repositorio. La programación se realiza utiliando lenguaje de Python,
#basada en un código previo realizado en Colab.

#=============================================================================================
# 1. requirements.txt
#=============================================================================================
#En el archivo se enlistan las librerias que necesita la aplicaicón para funcionar. 
#Además de que se especifica la versión mínima necesaria tanto de altair (versión 5.0.0) y streamlit (versión 1.31.0)

#=============================================================================================
# 2. app.py
#=============================================================================================
#Como su nombre lo indica es el corazón de la aplicación.
#Esta compuesta por 11 secciones, las cuales se encuentran identificadas y numeradas.
#Primero se importan las librerias necesarias para correr la aplicación.
#La PRIMER SECCIÓN identifica la página de introducción como "inicio". Tambien define las coordenadas de la imagen SVG.

#La SEGUNDA SECCIÓN plantea la simulación del proceso en BioSTEAM, es decir, identifica las corrientes con nombres y números, define
#los valores de las corrientes como puede ser masa, presión y temperatura, conecta las corrientes a los equipos, define la secuencia  
#que deben seguir los equipos de acuerdo al proceso de la simulación.
#Y finalmente define el sistema como "eth_sys" y ordena los resultados de las corrientes y energía en una lista, con las unidades y
#valores necesarios para presentarlos en la aplicación.

#La TERCER SECCIÓN es la simulación económica, la cual se nombra TEA Robusto. Se definen los indicadores a calcula y las suposiciones
#de ciertos valores económicos. Tambien se calcula el precio de la electricidad, servicios auxiliares y precio de mosto y etanol.
#Aquí tambien se incluye la primer alerta, la cual consiste en avisar cuando los valores escogidos con los sliders de "🌡️ Parámetros de
#proceso" provocan no haya una separación al ingresar al flash y por lo tanto no haya un "Producto Final".
#Finalmente, se guardan los valores calculados en un dataframe, para facilitar su diseño al prenetarlos en una tabla.

#La CUARTA SECCIÓN incluye la segunda advertencia, que va ligada a la temperatura de la corriente de mosto. Se activa cuando la temperatura
#seleccionada por el slider provoca que la corriente entre como una mezcla bifásica.

#La QUINTA SECCIÓN es la programación de los recuadrso emergentes de la imagen SVG del diagrama de proceso.

#La SEXTA SECCIÓN es la programación necesaria para la página de "inicio", se tiene una breve descripción del proceso, una lista de lo que 
#se observará en la página de "simulacion" y el botón para ingresar al simulador.

#La SÉPTIMA SECCIÓN integra los sliders de los "🌡️ Parámetros Proceso" y "💰 Parámetros Económicos" mencionados anteriormente. 
#De igual forma, se tiene el botón para regresar a la página de inicio y una función para guardar los valores de la simulación
#los cuales se utilizarán en las gráficas de sensibilidad. Por último se programan los botones para ir a las gráficas de sensibilidad 
#("📊 Ver Análisis de Sensibilidad") y diagramas de proceso en AutoCAD Plant 3D ("🗺️ Ver Diagramas de Ingeniería").

#La OCTAVA SECCIÓN despliega los resultados a partir de dataframes de las corrientes del proceso, la energía utilizada y los inidicadores
#económicos.

#La NOVENA SECCIÓN es la integración del Tutor IA, el cual usa Gemini para responder en menos de 250 palabras las dudas que el usuario
#tenga acerca del proceso simulado en la aplicación.

#La DÉCIMA SECCIÓN vincula los resultados de la simulación en diagrama SVG, solo para los equipos y la corriente de Producto Final.

#LA UNDÉCIMA SECCIÓN es el "ENRUTADOR DE PÁGINAS", vinvula la progrmación y resultados del archivo 'app.py' con los otros archivos del repositorio.

#=============================================================================================
# 3. sensibilidad.py
#=============================================================================================
#Es la página que aparece al oprimir "📊 Ver Análisis de Sensibilidad" en 'app.py'. En ella se presentan 3 gráficos de sensibilidad.

#La GRÁFICA 1 compara el efecto que tiene la temperatura de la corriente mosto en el consumo de energía necesario en el proceso, mientras
#mantiene fijo los valores de temperatura y presión del separador flash, 110°C y 1 atm, respectivamente.
#La GRÁFICA 2 compara el efecto que tiene la presión del flash en la concentración másica del Producto Final. Ahora mantiendo fijo la
#temperatura de la corriente de mosto y del separador flash.
#La GRÁFICA 3 compara el Precio de venta definido contra el ROI, esto para predecir que precio es el más adecuado utilizar si se desea
#tener un ROI positivo y de mayor valor.

#=============================================================================================
# 4. diagramas.py
#=============================================================================================
#Es la página que aparece al oprimir "🗺️ Ver Diagramas de Ingeniería", se presentan los tres diagramas del proceso: uno de bloques,
#uno de flujo de proceso y por último el de tubería e instrumentación. Además de visualizarse, se tiene la posibilidad de descargar
#los archivos, los cuales se realizaron en AutoCAD Plant 3D.

#Gracias por su atención.



