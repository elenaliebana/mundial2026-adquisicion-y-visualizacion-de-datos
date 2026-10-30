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

# Lista de selecciones que usaremos varias veces en el sidebar
SELECCIONES = sorted(jugadores["seleccion_nacional"].unique())

### ANÁLISIS I: VENTANAS DE PARTIDOS
st.header("Análisis I: Ventanas de partidos")

## 1) Gráfico de barras: eventos de un partido
st.subheader("1. Eventos de un partido")
st.sidebar.header("Filtros del gráfico 1")
p1 = partidos.copy()
p1["nombre_partido"] = p1["seleccion_local"] + " - " + p1["seleccion_visitante"] + " (" + p1["ronda"] + ")" # Nombre con el que aparece el partido en el selector
nombre_partido = st.sidebar.selectbox("Partido", p1["nombre_partido"])
id_partido = p1[p1["nombre_partido"] == nombre_partido].index[0] # el número del partido elegido
ev1 = eventos[eventos["index_partido"] == id_partido]


# Colores para cada tipo de evento
COLORES_EVENTO = {
    "Goal": "#1B8429",
    "Assist": "#5C68E9",
    "Yellow Card": "#F2C14E",
    "Red Card": "#C8102E",
    "VAR Review": "#BF41BF",
    "Penalty Shootout Goal": "#69DE79",
    "Penalty Shootout Miss": "#D78745"
}

fig1 = px.bar(
    ev1,
    x = "minuto_evento",                  
    y = [1] * len(ev1),   # [1] es la altura de cada barra              
    color = "tipo_evento", 
    color_discrete_map = COLORES_EVENTO, # colores definidos    
    category_orders = {"tipo_evento": ["Assist", "Goal"]}, # Para que el gol sobresalga más que la asistencia       
    hover_name = "nombre_jugador", 
    range_x = [0, 125],  # el eje cubre todo el partido y la prórroga
    height = 400,    
    title = "Eventos del partido",
    labels = {"minuto_evento": "Minuto del partido", "tipo_evento": "Tipo de evento", "y": "Nº de eventos"}
)

fig1.update_traces(width = 1) # barras más gruesas
fig1.update_yaxes(dtick = 1) # solo números enteros en el eje vertical


st.plotly_chart(fig1, use_container_width=True)

# Añadimos algunas métricas que pueden ser interesantes
c1, c2, c3 = st.columns(3)  
c1.metric("Goles", int((ev1["tipo_evento"] == "Goal").sum()))
c2.metric("Amarillas", int((ev1["tipo_evento"] == "Yellow Card").sum()))
c3.metric("Rojas", int((ev1["tipo_evento"] == "Red Card").sum()))


## 2) Mapa de calor

# A cada evento le copiamos la ronda de su partido (para filtrar por ronda)
p2 = partidos.reset_index()[["index_partido", "ronda"]]
eventos = pd.merge(eventos, p2, on="index_partido", how="left")

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
seleccion = st.sidebar.selectbox("Selección", SELECCIONES)
p3 = partidos[(partidos["seleccion_local"] == seleccion) | (partidos["seleccion_visitante"] == seleccion)]
ev3 = eventos[eventos["index_partido"].isin(p3.index)].copy()

# Columna de sentido para poder agrupar por a favor / en contra
ev3["sentido"] = "en contra"
ev3.loc[(ev3["seleccion_evento"] == seleccion) & (ev3["tipo_evento"].isin(["Goal", "Assist", "Penalty Shootout Goal"])), "sentido"] = "a favor"
ev3.loc[(ev3["seleccion_evento"] != seleccion) & (ev3["tipo_evento"].isin(["Yellow Card", "Red Card", "Penalty Shootout Miss"])), "sentido"] = "a favor"
ev3.loc[ev3["tipo_evento"] == "VAR Review", "sentido"] = "neutral" # El VAR no favorece a nadie

ev3["evento_final"] = ev3["tipo_evento"] + " (" + ev3["sentido"] + ")"
grupos = ev3.groupby("evento_final").size().reset_index(name="número")

# Colores por evento (anillo)
COLORES_PIE= {
    "Goal (a favor)": "#1B8429",
    "Assist (a favor)": "#5C68E9",
    "Yellow Card (a favor)": "#F2C14E",
    "Red Card (a favor)": "#C8102E",
    "VAR Review (neutral)": "#BF41BF",
    "Penalty Shootout Goal (a favor)": "#69DE79",
    "Penalty Shootout Miss (a favor)": "#D78745",

    "Goal (en contra)": "#00C2A8",                 
    "Assist (en contra)": "#4FC3F7",              
    "Yellow Card (en contra)": "#FFE600",          
    "Red Card (en contra)": "#FF6F91",             
    "Penalty Shootout Goal (en contra)": "#B6E800", 
    "Penalty Shootout Miss (en contra)": "#FF6D00"} 

fig3 = px.pie(
    grupos,
    names="evento_final",                           
    values="número", 
    color = "evento_final",                    
    color_discrete_map = COLORES_PIE,
    hole = 0.4, # gráfico de anillo  
    height = 450,                                                                   
    title="Eventos de " + seleccion)

st.plotly_chart(fig3, use_container_width=True)

### ANÁLISIS II: RENDIMIENTO DE JUGADORES CLAVE
st.header("Análisis II: Rendimiento de jugadores clave")

## 4) Gráfico de dispersión
st.subheader("4. Valor de mercado vs calificación media")
st.sidebar.header("Filtros del gráfico 4")

todas4 = st.sidebar.checkbox("Todas las selecciones", key="todas4") # Opción de marcar todas las selecciones a la vez
selecciones4 = st.sidebar.multiselect("Selecciones", SELECCIONES, disabled=todas4, key="selecciones4") # disabled --> desactiva el multiselect si la casilla está marcada.
if todas4:
    selecciones4 = SELECCIONES

posiciones = st.sidebar.multiselect("Posiciones", jugadores["posicion"].unique())

# Utilizamos un rango de partidos jugados
pj_min, pj_max = st.sidebar.slider(
    "Partidos jugados",
    min_value = int(jugadores["partidos_jugados"].min()),
    max_value = int(jugadores["partidos_jugados"].max()),
    value = (int(jugadores["partidos_jugados"].min()), int(jugadores["partidos_jugados"].max())))

j4 = jugadores[
    (jugadores["minutos_jugados"] >= 180)                           
    & jugadores["seleccion_nacional"].isin(selecciones4)           
    & jugadores["posicion"].isin(posiciones)                       
    & jugadores["partidos_jugados"].between(pj_min, pj_max)]

COLORES_POSICION = {
    "Portero": "#93101D",
    "Defensa": "#1A9523" ,
    "Centrocampista": "#E1D225" ,
    "Delantero": "#2143DA" 
}


fig4 = px.scatter(
    j4,
    x="valor_mercado",                          
    y="calificacion_media",                     
    color="posicion",    
    color_discrete_map = COLORES_POSICION,                       
    hover_name="nombre_jugador",                
    hover_data=["seleccion_nacional", "minutos_jugados"],
    opacity = 0.85,                                         
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

# Para la ponderación hemos seleccionado valores que consideramos adecuados
j5["rendimiento"] = (3 * j5["goles_min"] + 2 * j5["asist_min"] + 1 * j5["goles_asist_min"]
                     - 1 * j5["concedidos_min"] - 2 * j5["amarillas_min"] - 3 * j5["rojas_min"])

top = j5.sort_values(metrica, ascending=False).head(15)
top = top.sort_values(metrica)

fig5 = px.bar(
    top,
    x=metrica,                                   
    y="nombre_jugador",  
    orientation = "h",                                                  
    text="ranking_valor", # número escrito en la barra
    color_discrete_sequence = ["#93101D"],
    height = 550,                   
    title="Top 15 (+ puesto en valor de mercado)",
    labels={metrica: "Valor de la métrica", "nombre_jugador": "Jugador"}
)

fig5.update_traces(textangle = 0, textposition = "outside", cliponaxis = False) # Posiciona el número al lado de la barra (ángulo 0, posición fuera, cliponaxis = False evita que se corte el número)
st.plotly_chart(fig5, use_container_width=True)

# Métricas útiles
mejor = top.iloc[-1]   
c1, c2, c3 = st.columns(3)
c1.metric("Nº 1 del top", mejor["nombre_jugador"])
c2.metric("Selección", mejor["seleccion_nacional"])
c3.metric(metrica, f"{mejor[metrica]:.4f}") 

## 6) Gráfico de burbujas
st.subheader("6. Minutos jugados, calificación media y valor de mercado")
st.sidebar.header("Filtros del gráfico 6")

todas6 = st.sidebar.checkbox("Todas las selecciones", key="todas6")
selecciones6 = st.sidebar.multiselect("Selecciones", SELECCIONES, disabled=todas6, key="selecciones6") 
if todas6:
    selecciones6 = SELECCIONES
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
    color_discrete_map = {"SI": "#93101D", "NO": "#D9D9D9"},
    category_orders = {"ha_marcado": ["NO", "SI"]}, # los grises se dibujan primero y los rojos encima                         
    size_max=35,                               
    opacity=0.8,                                
    hover_name="nombre_jugador",
    hover_data={"ha_marcado": False,         
            "valor_mercado": True,      
            "seleccion_nacional": True,
            "posicion": True,
            "goles": True},
    height = 550,
    title="Minutos, calificación media y valor de mercado",
    labels={"minutos_jugados": "Minutos jugados", "calificacion_media": "Calificación media",
        "ha_marcado": "¿Ha marcado?", "valor_mercado": "Valor de mercado",
        "seleccion_nacional": "Selección", "posicion": "Posición", "goles": "Goles"})

st.plotly_chart(fig6, use_container_width=True)

### ANÁLISIS III: IMPACTO ARBITRAL
st.header("Análisis III: Impacto arbitral")

## 7) Diagrama de cajas: tarjetas por partido y ronda
st.subheader("7. Tarjetas por partido según la ronda")
tarjetas = eventos[eventos["tipo_evento"].isin(["Yellow Card", "Red Card"])]["index_partido"].value_counts().sort_index()

p7 = partidos.copy()
p7["tarjetas"] = tarjetas
p7["tarjetas"] = p7["tarjetas"].fillna(0)

fig7 = px.box(
    p7,
    x = "ronda",
    y = "tarjetas",
    points = "all", # Un punto por partido                                       
    hover_data = ["seleccion_local", "seleccion_visitante"],  
    color_discrete_sequence = ["#93101D"],
    height = 500,
    title = "Tarjetas por partido en cada ronda",
    labels = {"ronda": "Ronda", "tarjetas": "Tarjetas en el partido"})

st.plotly_chart(fig7, use_container_width=True)

## 8) Índice de Intervención Arbitral
st.subheader("8. Índice de Intervención Arbitral por árbitro")

eventos["peso"] = eventos["tipo_evento"].map({"Yellow Card": 1, "Red Card": 3, "VAR Review": 1, "Goal": 0.2}).fillna(0)

p = partidos.copy()
p["indice_arbitral"] = eventos.groupby("index_partido")["peso"].sum()
p["indice_arbitral"] = p["indice_arbitral"].fillna(0)

st.sidebar.header("Filtros del gráfico 8")
rondas8 = st.sidebar.multiselect("Ronda", partidos["ronda"].unique(), key="rondas8")
todas8 = st.sidebar.checkbox("Todas las selecciones", key="todas8")
selecciones8 = st.sidebar.multiselect("Selecciones", SELECCIONES, disabled=todas8, key="selecciones8")
if todas8:
    selecciones8 = SELECCIONES

p8 = p[(p["arbitro_partido"] != "No disponible") & p["ronda"].isin(rondas8) & (p["seleccion_local"].isin(selecciones8) | p["seleccion_visitante"].isin(selecciones8))]


puntos = p8[["arbitro_partido", "indice_arbitral"]].copy() # Índice de cada partido
puntos["tipo"] = "Partido"
puntos["tamaño"] = 1 # Tamaño de cada punto

medias = p8.groupby("arbitro_partido")["indice_arbitral"].mean().reset_index() # Media de cada árbitro
medias["tipo"] = "Media"
medias["tamaño"] = 2 # La media se dibuja más grande 

fig8 = px.scatter(
    pd.concat([puntos, medias]),
    x = "indice_arbitral",
    y = "arbitro_partido",
    color = "tipo", # El color y el símbolo dependen de si es el índice por partido o la media
    symbol = "tipo",
    symbol_map = {"Partido": "circle", "Media": "diamond"}, # círculo para los partidos y rombo para la media
    size = "tamaño",
    size_max = 12,
    hover_data = {"tamaño": False}, # No mostrar el tamaño al pasar el ratón
    color_discrete_map = {"Partido": "#93101D", "Media": "#D6D609"}, # Colores para la media y el partido
    category_orders = {"tipo": ["Media", "Partido"]}, # La media se dibuja primero y los partidos encima
    height = max(400, 40 * len(medias)), # Más árbitros, más alto
    title = "Índice de intervención arbitral por árbitro",
    labels = {"indice_arbitral": "Índice de intervención arbitral", "arbitro_partido": "Árbitro", "tipo": ""}
)

st.plotly_chart(fig8, use_container_width=True)


# Dataframes de resúmenes

local = p[["seleccion_local", "arbitro_partido", "indice_arbitral"]].rename(columns={"seleccion_local": "seleccion"})
visitante = p[["seleccion_visitante", "arbitro_partido", "indice_arbitral"]].rename(columns={"seleccion_visitante": "seleccion"})
por_seleccion = pd.concat([local, visitante])
por_seleccion = por_seleccion[por_seleccion["arbitro_partido"] != "No disponible"] 

media_sel = por_seleccion.groupby(["seleccion", "arbitro_partido"])["indice_arbitral"].mean().reset_index()

menos = media_sel.sort_values("indice_arbitral").groupby("seleccion").head(1) # Árbitro con el índice medio más bajo
mas = media_sel.sort_values("indice_arbitral", ascending=False).groupby("seleccion").head(1) # Árbitro con el índice medio más alto

resumen8 = pd.merge(menos, mas, on="seleccion", suffixes=("_menos", "_mas")) # Resumen para ver el árbitro más y menos severo por seleccion

c1, c2, c3 = st.columns([2, 1, 1])

c1.caption("Árbitro menos y más severo con cada selección")
c1.dataframe(
    resumen8.round(2).rename(columns={
        "seleccion": "Selección",
        "arbitro_partido_menos": "Menos severo",
        "indice_arbitral_menos": "Índice (-)",
        "arbitro_partido_mas": "Más severo",
        "indice_arbitral_mas": "Índice (+)"
    }),
    hide_index = True,
    use_container_width = True
)

veces_menos = resumen8["arbitro_partido_menos"].value_counts().reset_index()
veces_menos.columns = ["Árbitro", "Veces"]
c2.caption("Árbitros menos severos")
c2.dataframe(veces_menos, hide_index = True, use_container_width = True)

veces_mas = resumen8["arbitro_partido_mas"].value_counts().reset_index()
veces_mas.columns = ["Árbitro", "Veces"]
c3.caption("Árbitros más severos")
c3.dataframe(veces_mas, hide_index = True, use_container_width = True)