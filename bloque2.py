import pandas as pd
import plotly.express as px
import streamlit as st

# CONFIGURACIÓN Y DATOS
partidos = pd.read_excel("partidosWC26.xlsx", index_col=0)
eventos = pd.read_excel("eventosWC26.xlsx", index_col=0)
jugadores = pd.read_excel("jugadoresWC26.xlsx")

st.set_page_config(
    page_title = "Mundial 2026",
    layout = "wide"
)

st.title("Mundial 2026 - Análisis de datos")

### ANÁLISIS I: VENTANAS DE PARTIDOS
st.header("Análisis I: Ventanas de partidos")

## 1) Gráfico de barras: eventos de un partido
st.subheader("1. Eventos de un partido")
st.sidebar.header("Filtros del gráfico 1")
id_partido = st.sidebar.selectbox("Partido", partidos.index)
ev1 = eventos[eventos["index_partido"] == id_partido]

# Colores para cada tipo de evento
COLORES_EVENTO = {
    "Goal": "green",
    "Assist": "royalblue",
    "Yellow Card": "gold",
    "Red Card": "red",
    "VAR Review": "purple",
    "Penalty Shootout Goal": "darkgreen",
    "Penalty Shootout Miss": "orange"
}


fig1 = px.bar(
    ev1,
    x = "minuto_evento",                  
    y = [1] * len(ev1),   # [1] es la altura de cada barra              
    color = "tipo_evento", 
    color_discrete_map = COLORES_EVENTO, # colores definidos                     
    hover_data = ["minuto_evento"],  
    hover_name = "nombre_jugador", 
    range_x = [0, 125],  # el eje cubre todo el partido y la prórroga
    height = 400,    
    title = "Eventos del partido",
    labels = {"minuto_evento": "Minuto del partido", "tipo_evento": "Tipo de evento", "y": "Nº de eventos"}
)

fig1.update_traces(width = 0.8) # barras más gruesas
fig1.update_yaxes(dtick = 1) # solo números enteros en el eje vertical

st.plotly_chart(fig1, use_container_width=True)


## 2) Mapa de calor

# A cada evento le copiamos la ronda de su partido (para filtrar por ronda)
partidos2 = partidos.reset_index()[["index_partido", "ronda"]]
eventos = pd.merge(eventos, partidos2, on="index_partido", how="left")

st.sidebar.header("Filtros del gráfico 2")
tipo = st.sidebar.selectbox("Tipo de evento", eventos["tipo_evento"].unique())
rondas = st.sidebar.multiselect("Ronda", partidos["ronda"].unique())
ev2 = eventos[(eventos["tipo_evento"] == tipo) & (eventos["ronda"].isin(rondas))]

fig2 = px.density_heatmap(
    ev2,
    x = "minuto_evento",
    y="tipo_evento",
    nbinsx=25,                                             
    color_continuous_scale = "YlOrRd", # amarillo = pocos eventos, rojo = muchos
    range_x = [0, 125],
    height = 300,
    title = "Densidad de eventos durante el partido",
    labels = {"minuto_evento": "Minuto del partido", "tipo_evento": "Tipo de evento"}
    )

st.plotly_chart(fig2, use_container_width=True)

# 3) Gráfico circular de una selección
st.subheader("3. Eventos a favor y en contra de una selección")
st.sidebar.header("Filtros del gráfico 3")
seleccion = st.sidebar.selectbox("Selección", sorted(jugadores["seleccion_nacional"].unique()))
partidos_sel = partidos[(partidos["seleccion_local"] == seleccion) | (partidos["seleccion_visitante"] == seleccion)]
ev3 = eventos[eventos["index_partido"].isin(partidos_sel.index)].copy()

# Columna de sentido para poder agrupar por a favor / en contra
ev3["sentido"] = "en contra"
ev3.loc[(ev3["seleccion_evento"] == seleccion) & (ev3["tipo_evento"].isin(["Goal", "Assist", "Penalty Shootout Goal"])), "sentido"] = "a favor"
ev3.loc[(ev3["seleccion_evento"] != seleccion) & (ev3["tipo_evento"].isin(["Yellow Card", "Red Card", "Penalty Shootout Miss"])), "sentido"] = "a favor"
ev3.loc[ev3["tipo_evento"] == "VAR Review", "sentido"] = "neutral" # El VAR no favorece a nadie

ev3["evento_final"] = ev3["tipo_evento"] + " (" + ev3["sentido"] + ")"
grupos = ev3.groupby("evento_final").size().reset_index(name="número")

fig3 = px.pie(
    grupos,
    names="evento_final",                           
    values="número", 
    hole = 0.4, # gráfico de anillo  
    height = 450,                                                                   
    title="Eventos de " + seleccion)

st.plotly_chart(fig3, use_container_width=True)

### ANÁLISIS II: RENDIMIENTO DE JUGADORES CLAVE
st.header("Análisis II: Rendimiento de jugadores clave")

## 4) Gráfico de dispersión
st.subheader("4. Valor de mercado vs calificación media")
st.sidebar.header("Filtros del gráfico 4")
selecciones = st.sidebar.multiselect("Selecciones", sorted(jugadores["seleccion_nacional"].unique()))
posiciones = st.sidebar.multiselect("Posiciones", jugadores["posicion"].unique())
pj_min, pj_max = st.sidebar.slider(
    "Partidos jugados",
    min_value = int(jugadores["partidos_jugados"].min()),
    max_value = int(jugadores["partidos_jugados"].max()),
    value = (int(jugadores["partidos_jugados"].min()), int(jugadores["partidos_jugados"].max()))
)

j4 = jugadores[
    (jugadores["minutos_jugados"] >= 180)                           
    & jugadores["seleccion_nacional"].isin(selecciones)           
    & jugadores["posicion"].isin(posiciones)                       
    & jugadores["partidos_jugados"].between(pj_min, pj_max)   
]

fig4 = px.scatter(
    j4,
    x="valor_mercado",                          
    y="calificacion_media",                     
    color="posicion",                          
    hover_name="nombre_jugador",                
    hover_data=["seleccion_nacional", "minutos_jugados"],
    opacity = 0.7,                                         
    height = 500,
    title = "Valor de mercado y calificación media",
    labels = {"valor_mercado": "Valor de mercado", "calificacion_media": "Calificación media", "posicion": "Posición"}

)

st.plotly_chart(fig4, use_container_width=True)

correlacion = j4["valor_mercado"].corr(j4["calificacion_media"])   
st.metric("Correlación valor de mercado - calificación media", f"{correlacion:.2f}")

## 5) Top 15 en una métrica
st.subheader("5. Top 15 jugadores en una métrica")
st.sidebar.header("Filtros del gráfico 5")
metrica = st.sidebar.selectbox("Métrica",["goles_min", "goles_asist_min", "asist_min", "concedidos_min", "amarillas_min", "rojas_min", "rendimiento"])

jugadores = jugadores.sort_values("valor_mercado", ascending=False).reset_index(drop=True) 
jugadores["ranking_valor"] = jugadores.index + 1


j5 = jugadores[jugadores["minutos_jugados"] >= 180].copy()

# Métricas por minuto
j5["goles_min"] = j5["goles"] / j5["minutos_jugados"]
j5["goles_asist_min"] = (j5["goles"] + j5["asistencias"]) / j5["minutos_jugados"]
j5["asist_min"] = j5["asistencias"] / j5["minutos_jugados"]
j5["concedidos_min"] = j5["goles_concedidos"] / j5["minutos_jugados"]
j5["amarillas_min"] = j5["tarjetas_amarillas"] / j5["minutos_jugados"]
j5["rojas_min"] = j5["tarjetas_rojas"] / j5["minutos_jugados"]

# Ponderación
j5["rendimiento"] = (3 * j5["goles_min"] + 2 * j5["asist_min"] + 1 * j5["goles_asist_min"]
                     - 0.5 * j5["concedidos_min"] - 1 * j5["amarillas_min"] - 3 * j5["rojas_min"])

top = j5.sort_values(metrica, ascending=False).head(15)
top = top.sort_values(metrica)

fig5 = px.bar(
    top,
    x=metrica,                                   
    y="nombre_jugador",  
    orientation = "h",                                                  
    text="ranking_valor", # número escrito en la barra
    height = 550,                   
    title="Top 15 (el número de cada barra es su puesto en valor de mercado)",
    labels={metrica: "Valor de la métrica", "nombre_jugador": "Jugador"}
)

st.plotly_chart(fig5, use_container_width=True)

## 6) Gráfico de burbujas
st.subheader("6. Minutos jugados, calificación media y valor de mercado")
st.sidebar.header("Filtros del gráfico 6")
selecciones6 = st.sidebar.multiselect("Selecciones", sorted(jugadores["seleccion_nacional"].unique()), key="selecciones6") # key para que no de error con los parametros del gráfico 5
posiciones6 = st.sidebar.multiselect("Posiciones", jugadores["posicion"].unique(), key="posiciones6")

j6 = jugadores[(jugadores["minutos_jugados"] > 0) &  # quitamos a quien no ha jugado ningún minuto
               jugadores["seleccion_nacional"].isin(selecciones6) 
               & jugadores["posicion"].isin(posiciones6)].copy()

j6["ha_marcado"] = "NO"
j6.loc[j6["goles"] > 0, "ha_marcado"] = "SI"

fig6 = px.scatter(
    j6,
    x="minutos_jugados",                         
    y="calificacion_media",                      
    size="valor_mercado",                      
    color="ha_marcado",                           
    size_max=35,                               
    opacity=0.7,                                
    hover_name="nombre_jugador",
    hover_data=["seleccion_nacional", "posicion", "goles"],
    height = 550,
    title="Minutos, calificación media y valor de mercado",
    labels={
        "minutos_jugados": "Minutos jugados",
        "calificacion_media": "Calificación media",
        "ha_marcado": "¿Ha marcado?"
    }
)

st.plotly_chart(fig6, use_container_width=True)