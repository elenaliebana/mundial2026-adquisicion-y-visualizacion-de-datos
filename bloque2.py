import pandas as pd
import plotly.express as px
import streamlit as st

partidos = pd.read_excel("partidosWC26.xlsx", index_col=0)
eventos = pd.read_excel("eventosWC26.xlsx", index_col=0)
jugadores = pd.read_excel("jugadoresWC2026.xlsx")

st.set_page_config(
    page_title = "Ventanas de Partidos",
    layout = "wide"
)

st.title("Análisis I: Ventanas de Partidos")
st.sidebar.header("Parámetros")

id_partido = st.sidebar.selectbox("Partido", partidos.index)

# 1) Gráfico de barras: eventos de un partido
st.subheader("1. Eventos de un partido")

ev1 = eventos[eventos["index_partido"] == id_partido]

fig1 = px.bar(
    ev1,
    x = "minuto_evento",                  
    y = [1] * len(ev1),   # [1] es la altura de cada barra              
    color = "tipo_evento",                       
    hover_data = ["minuto_evento"],  
    hover_name = "nombre_jugador",     
    title = "Eventos del partido",
    labels = {"minuto_evento": "Minuto del partido", "tipo_evento": "Tipo de evento", "y": "Nº de eventos"}
)

st.plotly_chart(fig1, use_container_width=True)

# 2) Mapa de calor
partidos2 = partidos.reset_index()[["index_partido", "ronda"]]
eventos = pd.merge(eventos, partidos2, on="index_partido", how="left")

tipos = st.sidebar.multiselect("Tipo de evento", eventos["tipo_evento"].unique())
rondas = st.sidebar.multiselect("Ronda", partidos["ronda"].unique())

ev2 = eventos[eventos["tipo_evento"].isin(tipos) & eventos["ronda"].isin(rondas)]

fig2 = px.density_heatmap(
    ev2,
    x = "minuto_evento",
    y="tipo_evento",
    nbinsx=25,                                             
    title="Densidad de eventos durante el partido",
    labels={"minuto_evento": "Minuto del partido", "tipo_evento": "Tipo de evento"}
)

st.plotly_chart(fig2, use_container_width=True)

# 3) Gráfico circular de una selección
seleccion = st.sidebar.selectbox("Selección", sorted(jugadores["seleccion_nacional"].unique()))
partidos_sel = partidos[(partidos["seleccion_local"] == seleccion) | (partidos["seleccion_visitante"] == seleccion)]
ev3 = eventos[eventos["index_partido"].isin(partidos_sel.index)].copy()

ev3["sentido"] = "en contra"
ev3.loc[(ev3["seleccion_evento"] == seleccion) & (ev3["tipo_evento"].isin(["Goal", "Assist", "Penalty Shootout Goal"])), "sentido"] = "a favor"
ev3.loc[(ev3["seleccion_evento"] != seleccion) & (ev3["tipo_evento"].isin(["Yellow Card", "Red Card", "Penalty Shootout Miss"])), "sentido"] = "a favor"
ev3.loc[ev3["tipo_evento"] == "VAR Review", "sentido"] = "neutral" # El VAR no favorece a nadie

ev3["categoria"] = ev3["tipo_evento"] + " (" + ev3["sentido"] + ")"
resumen3 = ev3.groupby("categoria").size().reset_index(name="número")

fig3 = px.pie(
    resumen3,
    names="categoria",                           
    values="número", 
    hole=0.4,                                                                    
    title="Eventos de " + seleccion)

st.plotly_chart(fig3, use_container_width=True)

st.header("Análisis II: Rendimiento de jugadores clave")

st.sidebar.header("Análisis II: filtros")

jugadores = jugadores.sort_values("valor_mercado", ascending=False).reset_index(drop=True) 
jugadores["ranking_valor"] = jugadores.index + 1

selecciones = st.sidebar.multiselect("Selecciones", sorted(jugadores["seleccion_nacional"].unique()))
posiciones = st.sidebar.multiselect("Posiciones", jugadores["posicion"].unique())

pj_min, pj_max = st.sidebar.slider(             
    "Partidos jugados",
    min_value=int(jugadores["partidos_jugados"].min()),
    max_value=int(jugadores["partidos_jugados"].max()),
    value=(int(jugadores["partidos_jugados"].min()), int(jugadores["partidos_jugados"].max()))
)

## ANÁLISIS II
# 4) Gráfico de dispersión
st.subheader("4. Valor de mercado vs calificación media")

vista = jugadores[
    (jugadores["minutos_jugados"] >= 180)                           
    & jugadores["seleccion_nacional"].isin(selecciones)           
    & jugadores["posicion"].isin(posiciones)                       
    & jugadores["partidos_jugados"].between(pj_min, pj_max)   
]

fig4 = px.scatter(
    vista,
    x="valor_mercado",                          
    y="calificacion_media",                     
    color="posicion",                          
    hover_name="nombre_jugador",                
    hover_data=["seleccion_nacional", "minutos_jugados"],
    title="Valor de mercado y calificación media",
    labels={
        "valor_mercado": "Valor de mercado",
        "calificacion_media": "Calificación media",
        "posicion": "Posición"
    }
)

st.plotly_chart(fig4, use_container_width=True)

correlacion = vista["valor_mercado"].corr(vista["calificacion_media"])   
st.metric("Correlación valor de mercado - calificación media", f"{correlacion:.2f}")

# 5) Top 15 en una métrica
metrica = st.sidebar.selectbox("Métrica", ["goles_min", "goles_asist_min", "asist_min", "concedidos_min", "amarillas_min", "rojas_min", "rendimiento"])

st.subheader("5. Top 15 jugadores en una métrica")
j5 = jugadores[jugadores["minutos_jugados"] >= 180].copy()

# Métricas por minuto
j5["goles_min"] = j5["goles"] / j5["minutos_jugados"]
j5["goles_asist_min"] = (j5["goles"] + j5["asistencias"]) / j5["minutos_jugados"]
j5["asist_min"] = j5["asistencias"] / j5["minutos_jugados"]
j5["concedidos_min"] = j5["goles_concedidos"] / j5["minutos_jugados"]
j5["amarillas_min"] = j5["tarjetas_amarillas"] / j5["minutos_jugados"]
j5["rojas_min"] = j5["tarjetas_rojas"] / j5["minutos_jugados"]

j5["rendimiento"] = (3 * j5["goles_min"] + 2 * j5["asist_min"] + 1 * j5["goles_asist_min"]
                     - 0.5 * j5["concedidos_min"] - 1 * j5["amarillas_min"] - 3 * j5["rojas_min"])

top = j5.sort_values(metrica, ascending=False).head(15)
top = top.sort_values(metrica)

fig5 = px.bar(
    top,
    x=metrica,                                   
    y="nombre_jugador",                                                    
    text="ranking_valor",                        
    title="Top 15 (el número de cada barra es su puesto en valor de mercado)",
    labels={metrica: "Valor de la métrica", "nombre_jugador": "Jugador"}
)

st.plotly_chart(fig5, use_container_width=True)