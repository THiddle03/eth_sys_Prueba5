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
#Esta compuesta por 10 secciones, las cuales se encuentran identificadas y numeradas.
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

#La SEXTA SECCIÓN es la programación necesaria para la página de "inicio"




