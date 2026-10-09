import pandas as pd
import numpy as np
import re
from sklearn.linear_model import LinearRegression

### CARGA DE DATOS
matches = pd.read_csv("datasetsWC26/matches_mundial2026.csv", sep=";")
stages = pd.read_csv("datasetsWC26/tournament_stages.csv", sep=",")
venues = pd.read_csv("datasetsWC26/worldcup_venues.csv", sep=";")
referees = pd.read_csv("datasetsWC26/index_referees.csv", sep=";")
squads = pd.read_csv("datasetsWC26/2026squads_and_players.csv", sep=";")
player_stats = pd.read_csv("datasetsWC26/2026player_stats.csv", sep=";")
register = pd.read_csv("datasetsWC26/2026match_register.csv", sep=";")
teams = pd.read_csv("datasetsWC26/2026nationalteams.csv", sep=",")
teams = teams.dropna(subset=["team_id"]) # En teams hay varias filas con team_id nulo

### EXPLORACIÓN INCIAL

# Creo un diccionario con el nombre y todos los datasets para utilizar en un bucle
datasets = {
    "matches": matches,
    "stages": stages,
    "venues": venues,
    "referees": referees,
    "squads": squads,
    "player_stats": player_stats,
    "register": register,
    "teams": teams,
}

# Resumen
for name, df in datasets.items():
    print("=" * 90)
    print(f"DATASET: {name}")
    print("-" * 90)

    print("SHAPE:", df.shape)
    print("\nINFO:")
    df.info()
    print("\nDESCRIBE:")
    print(df.describe())

    print("\nCOLUMNAS:")
    print(df.columns)
    print("\nPRIMERAS FILAS:")
    print(df.head(3))
    print("\nFILAS DUPLICADAS:")
    print(df.duplicated().sum())

    print("\nRESUMEN POR COLUMNAS:")
    resumen = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "nulos": df.isna().sum(),
    "pct_nulos": df.isna().mean().mul(100).round(2),
    "n_unicos": df.nunique(dropna=False)})

    print(resumen)

# En "filas duplicadas" podemos observar que hay varios dataframes con duplicados exactos
# Los eliminamos para que al crear partidos, eventos y jugadores no haya duplicados
for name, df in datasets.items():
    df.drop_duplicates(inplace = True)
    print(f"Filas duplicadas en {name}:", df.duplicated().sum())
    
# Al imprimir las columnas de referees, vemos que hay dos que se llaman referee_id
# Para ver si es la misma creamos otra columna en la que aparezca 'True' si son iguales y 'False' si no
referees["check_id"] = referees["referee_id.1"] == referees["referee_id"]
print(referees["check_id"].value_counts())

# Como al ver los valores todos son 'True' (la columna está duplicada), eliminamos una de ellas y check_id
referees = referees.drop(columns=["referee_id.1", "check_id"])


### CREACIÓN DE LOS TRES DATAFRAMES

## PARTIDOS
# Selección de columnas
partidos = matches[["date", "stage_id", "venue_id", "home_team_id", "away_team_id","home_score", "away_score", "result_type","home_penalty_score", "away_penalty_score", "referee_id", "match_id"]]
partidos = pd.merge(partidos, stages[["stage_id", "stage_name"]], on="stage_id", how="left")
partidos = pd.merge(partidos, venues[["venue_id", "stadium_name", "city", "country"]], on="venue_id", how="left")
partidos = pd.merge(partidos, referees[["referee_id", "name"]], on="referee_id", how="left")

partidos = pd.merge(partidos, teams[["team_id", "team_name"]], left_on="home_team_id", right_on="team_id", how="left")
partidos = pd.merge(partidos, teams[["team_id", "team_name"]], left_on="away_team_id", right_on="team_id", how="left")

# Eliminar columnas sobrantes
partidos = partidos.drop(columns=["stage_id", "venue_id", "home_team_id", "away_team_id", "referee_id", "team_id_x", "team_id_y"])

# Renombrar columnas
partidos = partidos.rename(columns={
    "date": "fecha_partido",
    "stage_name": "ronda",
    "stadium_name": "estadio",
    "city": "ciudad_partido",
    "country": "pais_partido",
    "result_type": "prorroga",
    "home_score": "marcador_local",
    "away_score": "marcador_visitante",
    "home_penalty_score": "penalty_local",
    "away_penalty_score": "penalty_visitante",
    "name": "arbitro_partido",
    "team_name_x": "seleccion_local",
    "team_name_y": "seleccion_visitante"
})

# Establecemos el índice
partidos.index = range(1, len(partidos) + 1)
partidos.index.name = "index_partido"

print(partidos)

## JUGADORES
# Selección de columnas
jugadores = player_stats[["player_id", "player_name", "matches_played", "minutes_played", "goals", "assists", "shots", "yellow_cards", "red_cards", "saves", "goals_conceded", "average_rating"]]
jugadores = pd.merge(jugadores, squads[["player_id", "team_id", "player_name", "position", "club_team", "market_value_eur", "caps"]], on="player_id", how="left")
jugadores = pd.merge(jugadores, teams[["team_id", "team_name"]], on="team_id", how="left")

jugadores = jugadores.drop(columns=["team_id"])

jugadores = jugadores.rename(columns={
    "team_name": "seleccion_nacional",
    "club_team": "club_jugador",
    "market_value_eur": "valor_mercado",
    "caps": "partidos_seleccion",
    "position": "posicion",
    "matches_played": "partidos_jugados",
    "minutes_played": "minutos_jugados",
    "goals": "goles",
    "assists": "asistencias",
    "shots": "tiros",
    "yellow_cards": "tarjetas_amarillas",
    "red_cards": "tarjetas_rojas",
    "saves": "paradas",
    "goals_conceded": "goles_concedidos",
    "average_rating": "calificacion_media",
})

# Hay varios jugadores que se llaman "Mc" en player_name_y pero en player_name_x muchas de las 
# tildes vienen en un mal formato, asi que unificamos las dos columnas cogiendo los valores buenos
jugadores.loc[jugadores["player_name_y"]=="Mc", "player_name_y"] = jugadores["player_name_x"]

jugadores = jugadores.drop(columns="player_name_x")
jugadores = jugadores.rename(columns={"player_name_y": "nombre_jugador"})


print(jugadores)

## EVENTOS
# Primero eliminamos las filas del dataset register que tienen el id repetido
con_datos = register[register["player_id"].notna()].drop_duplicates(subset="event_id", keep="first")
sin_datos = register[register["player_id"].isna()] # Las filas vacías no cuentan como id repetido
register = pd.concat([con_datos, sin_datos]).sort_index()

# Selección de columnas
eventos = register[["match_id", "minute", "event_type", "team_id", "player_id"]]
eventos = pd.merge(eventos, partidos.reset_index()[["index_partido", "match_id"]], on="match_id", how="left") # .reset_index() para poder hacer merge con index_partido
eventos = pd.merge(eventos, jugadores[["player_id", "nombre_jugador"]], on="player_id", how="left")
eventos = pd.merge(eventos, teams[["team_id", "team_name"]], on="team_id", how="left")

eventos = eventos.drop(columns=["match_id", "player_id", "team_id"])
partidos = partidos.drop(columns=["match_id"])
jugadores = jugadores.drop(columns=["player_id"])
jugadores = jugadores.set_index("nombre_jugador")

eventos = eventos.rename(columns={
    "minute": "minuto_evento",
    "event_type": "tipo_evento",
    "player_name": "nombre_jugador",
    "team_name": "seleccion_evento",
})

eventos.index = range(1, len(eventos) + 1)
eventos.index.name = "index_evento"

print(eventos)

### EXPLORACIÓN DE LOS NUEVOS DATAFRAMES
datasets_new = {"partidos": partidos, "jugadores": jugadores, "eventos": eventos}

for nombre, df in datasets_new.items():
    print("=" * 60)
    print(nombre)
    print("=" * 60)
    print(df.info())
    print(df.describe(include="all"))
    print("Duplicados:", df.duplicated().sum())

    print("\nRESUMEN POR COLUMNAS:")
    resumen = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "nulos": df.isna().sum(),
    "pct_nulos": df.isna().mean().mul(100).round(2),
    "n_unicos": df.nunique(dropna=False)})
    print(resumen)


### TRATAMIENTO

## PARTIDOS
# Vemos todos los valores de cada columna
for columna in partidos.columns:
    print(columna, partidos[columna].unique())

# Como en la columna pais_partido hay dos versiones de escribir Estados Unidos, las unificamos
partidos["pais_partido"] = partidos["pais_partido"].replace({"usa":"USA"})
print(partidos["pais_partido"].unique())

# Actualizamos la columna de prorroga con valores SI / NO
partidos["prorroga"] = partidos["prorroga"].map({"Regular": "NO", "AET": "SI", "Penalties": "SI"})

# Actualizamos penaltis: 
# Hay valores de 20, 30, 40 por lo que parece que están todos multiplicados por 10
# Rellenamos los valores nulos con 0
partidos["penalty_local"] = partidos["penalty_local"] / 10
partidos["penalty_visitante"] = partidos["penalty_visitante"] / 10
partidos["penalty_local"] = partidos["penalty_local"].fillna(0)
partidos["penalty_visitante"] = partidos["penalty_visitante"].fillna(0)

partidos["penalty_local"] = partidos["penalty_local"].astype(int)
partidos["penalty_visitante"] = partidos["penalty_visitante"].astype(int)

# 1 árbitro nulo
partidos["arbitro_partido"] = partidos["arbitro_partido"].fillna("Desconocido")

# La ronda "quarter_finals" tiene un espacio innecesario después del nombre
partidos["ronda"] = partidos["ronda"].str.strip()


## JUGADORES
# Vemos todos los valores de cada columna
for columna in jugadores.columns:
    print(columna, jugadores[columna].unique())

# Hay muchos nulos en columnas numéricas (goles, asistencias,...)
# Tiene sentido que los nulos sean en realidad 0, por lo que sustituimos los valores
columnas_nulos =["paradas", "tiros", "goles_concedidos", "goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]
for columna in columnas_nulos:
    jugadores[columna] = jugadores[columna].fillna(0).astype(int)

# Hay varios jugadores con calificación media o valor de mercado 0, lo que parece un valor 
# de relleno ya que en el resto de casos la calificación / valor es mucho más alta, por lo 
# que convertimos a nulo para imputarlo más tarde
jugadores.loc[jugadores["calificacion_media"] == 0, "calificacion_media"] = np.nan
jugadores.loc[jugadores["valor_mercado"] == 0, "valor_mercado"] = np.nan

print(jugadores)

## EVENTOS
# Vemos todos los valores de cada columna
for columna in eventos.columns:
    print(columna, eventos[columna].unique()) 

# Minutos anómalos --> Hay minutos negativos o por encima de la duración del partido 
# que ponemos como nulos para imputarlos más adelante
eventos.loc[(eventos["minuto_evento"] < 0) | (eventos["minuto_evento"] > 130), "minuto_evento"] = np.nan

# VAR review y review VAR son lo mismo
eventos["tipo_evento"] = eventos["tipo_evento"].replace({"Review VAR": "VAR Review"})
eventos["tipo_evento"].unique()

print(eventos)

# FECHAS - EXPRESIONES REGULARES

# Creo una lista y un diccionario que usaré luego para convertir todos los diferentes
# formatos de meses a letra
MESES_LISTA = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
               "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6, "july": 7,
    "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

def actualizar_fecha(texto):
    fecha = str(texto).strip()

    # 2026-06-19T19:00:00Z 
    pattern = re.match(r"(\d{4})-(\d{2})-(\d{2})T", fecha)
    if pattern:
        anio, mes, dia = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[int(mes) - 1]}/{anio[2:]}"

    # 20260619 
    pattern = re.match(r"(\d{4})(\d{2})(\d{2})$", fecha)
    if pattern:
        anio, mes, dia = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[int(mes) - 1]}/{anio[2:]}"

    # 25-jun-26
    pattern = re.match(r"(\d{1,2})-([a-zA-Z]{3})-(\d{2})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[int(MESES[mes_txt.lower()]) - 1]}/{anio}"

    # 06-21-2026  
    pattern = re.match(r"(\d{2})-(\d{2})-(\d{4})$", fecha)
    if pattern:
        mes, dia, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[int(mes) - 1]}/{anio[2:]}"

    # 26.06.2026 
    pattern = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})$", fecha)
    if pattern:
        dia, mes, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[int(mes) - 1]}/{anio[2:]}"

    # 27/06/2026 
    pattern = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", fecha)
    if pattern:
        a, b, anio = pattern.groups()
        a, b = int(a), int(b)
        # El Mundial solo se juega en junio (6) y julio (7)

        if b in (6, 7):
            dia, mes = a, b
        else:
            dia, mes = b, a
        return f"{int(dia):02d}/{MESES_LISTA[mes - 1]}/{anio[2:]}"

    # Jun 20 2026  
    pattern = re.match(r"([a-zA-Z]{3})\s+(\d{1,2})\s+(\d{4})$", fecha)
    if pattern:
        mes_txt, dia, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[MESES[mes_txt.lower()] - 1]}/{anio[2:]}"

    # June 22, 2026  
    pattern = re.match(r"([a-zA-Z]+)\s+(\d{1,2}),\s*(\d{4})$", fecha)
    if pattern:
        mes_txt, dia, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[MESES[mes_txt.lower()] - 1]}/{anio[2:]}"

    # 21 June 2026  
    pattern = re.match(r"(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[MESES[mes_txt.lower()] - 1]}/{anio[2:]}"

    # 20 de junio de 2026
    pattern = re.match(r"(\d{1,2}) de ([a-zA-Zñ]+) de (\d{4})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return f"{int(dia):02d}/{MESES_LISTA[MESES[mes_txt.lower()] - 1]}/{anio[2:]}"

partidos["fecha_partido"] = partidos["fecha_partido"].apply(actualizar_fecha)

### IMPUTACIÓN
## Imputación por la Media: valor mercado
medias = jugadores.groupby("seleccion_nacional")["valor_mercado"].mean()

medias_tabla = medias.reset_index() 

medias_tabla.rename(columns={"valor_mercado": "valor_media"}, inplace = True)

# Al hacer el merge, se elimina el índice de nombre_jugador,
# así que lo reseteamos y luego lo volvemos a poner
jugadores = jugadores.reset_index() 
jugadores = pd.merge(jugadores, medias_tabla, on="seleccion_nacional", how="left")

jugadores.loc[jugadores["valor_mercado"].isna(), "valor_mercado"] = jugadores["valor_media"]
jugadores.drop(columns=["valor_media"], inplace = True)

print(jugadores["valor_mercado"].isnull().sum())
jugadores = jugadores.set_index("nombre_jugador")

## Imputación por Regresión: calificación_media
porteros = jugadores[jugadores["posicion"] == "GK"]
resto = jugadores[jugadores["posicion"] != "GK"]

# Eliminamos las filas que no tienen calificación media. La regresión necesita ejemplos completos para aprender
train_gk = porteros.dropna(subset=["calificacion_media"])
train_resto = resto.dropna(subset=["calificacion_media"])

# Entrenamos el modelo. El modelo aprende la relación entre paradas/goles_concedidos/tarjetas y la calificacion_media de un portero.
# .fit(X, y) x- variable explicativa; y - variable objetivo 

model_gk = LinearRegression().fit(
    train_gk[["paradas", "goles_concedidos", "tarjetas_amarillas", "tarjetas_rojas"]],
    train_gk["calificacion_media"]
)

model_resto = LinearRegression().fit(
    train_resto[["goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]],
    train_resto["calificacion_media"]
)

# Creamos una copia para imputar
jugadores_imputed = jugadores.copy()

# Máscara de valores faltantes
mask_gk = (jugadores_imputed["posicion"] == "GK") & (jugadores_imputed["calificacion_media"].isna())
mask_resto = (jugadores_imputed["posicion"] != "GK") & (jugadores_imputed["calificacion_media"].isna())

# Filtramos los valores faltantes y predecimos sus valores a partir del modelo
jugadores_imputed.loc[mask_gk, "calificacion_media"] = model_gk.predict(
    jugadores_imputed.loc[mask_gk, ["paradas", "goles_concedidos", "tarjetas_amarillas", "tarjetas_rojas"]]
)

jugadores_imputed.loc[mask_resto, "calificacion_media"] = model_resto.predict(
    jugadores_imputed.loc[mask_resto, ["goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]]
)

# Marcamos que datos fueron imputados
jugadores_imputed["imputed"] = mask_gk | mask_resto
jugadores = jugadores_imputed
jugadores = jugadores.drop(columns=["imputed"])

print(jugadores)

## Imputación por Interpolación: minutos_evento
eventos_imputed = eventos.copy()

eventos_imputed["minuto_evento"] = (
    eventos_imputed.groupby("index_partido")["minuto_evento"] # Agrupar por partido para interpolar con eventos del mismo partido
    .transform(lambda x: x.interpolate("linear").bfill()) # Hay que utilizar transform porque interpolate no es un atributo de 'SeriesGroupBy'
)

eventos_imputed["minuto_evento"] = eventos_imputed["minuto_evento"].round()
eventos = eventos_imputed

# Convertimos a entero los valores numéricos necesarios
eventos["minuto_evento"] = eventos["minuto_evento"].astype("Int64")
eventos["index_partido"] = eventos["index_partido"].astype("Int64")


### ORDENAR COLUMNAS: Siguiendo el orden del enunciado
partidos = partidos[["fecha_partido", "ronda", "estadio", "ciudad_partido", "pais_partido",
                     "seleccion_local", "seleccion_visitante", "marcador_local",
                     "marcador_visitante", "prorroga", "penalty_local", "penalty_visitante",
                     "arbitro_partido"]]

jugadores = jugadores[["seleccion_nacional", "club_jugador", "partidos_seleccion", "posicion",
                       "valor_mercado", "partidos_jugados", "minutos_jugados", "goles",
                       "asistencias", "tiros", "tarjetas_amarillas", "tarjetas_rojas",
                       "paradas", "goles_concedidos", "calificacion_media"]]

eventos = eventos[["minuto_evento", "index_partido", "nombre_jugador",
                   "tipo_evento", "seleccion_evento"]]


### EXPORTACIÓN DE DATOS
partidos.to_excel("partidosWC26.xlsx")
eventos.to_excel("eventosWC26.xlsx")
jugadores.to_excel("jugadoresWC2026.xlsx")