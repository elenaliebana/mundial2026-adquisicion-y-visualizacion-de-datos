import pandas as pd
import numpy as np
import re

# Partidos
matches = pd.read_csv("datasetsWC26/matches_mundial2026.csv", sep=";")
stages = pd.read_csv("datasetsWC26/tournament_stages.csv", sep=",")
venues = pd.read_csv("datasetsWC26/worldcup_venues.csv", sep=";")
referees = pd.read_csv("datasetsWC26/index_referees.csv", sep=";")

# Jugadores
squads = pd.read_csv("datasetsWC26/2026squads_and_players.csv", sep=";")
player_stats = pd.read_csv("datasetsWC26/2026player_stats.csv", sep=";")

# Eventos
register = pd.read_csv("datasetsWC26/2026match_register.csv", sep=";")

# Todos
teams = pd.read_csv("datasetsWC26/2026nationalteams.csv", sep=",")
teams = teams.dropna(subset=["team_id"]) # En teams hay varias filas con team_id nulo

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
# Para ver si es la misma creamos otra columna en la que aparezca 'True' si son inguales y 'False' si no

referees["check_id"] = referees["referee_id.1"] == referees["referee_id"]
print(referees["check_id"].value_counts())

# Como al ver los valores todos son 'True' (la columna está duplicada), eliminamos una de ellas y check_id
referees = referees.drop(columns=["referee_id.1", "check_id"])




# PARTIDOS
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

# Actualizamos columnas de prorroga y penaltis
partidos["prorroga"] = partidos["prorroga"].map({"Regular": "NO", "AET": "SI", "Penalties": "SI"})
partidos["penalty_local"] = partidos["penalty_local"].fillna(0)
partidos["penalty_visitante"] = partidos["penalty_visitante"].fillna(0)

partidos.index = range(1, len(partidos) + 1)
partidos.index.name = "index_partido"

print(partidos)

# JUGADORES
jugadores = player_stats[["player_id", "matches_played", "minutes_played", "goals", "assists", "shots", "yellow_cards", "red_cards", "saves", "goals_conceded", "average_rating"]]
jugadores = pd.merge(jugadores, squads[["player_id", "team_id", "player_name", "position", "club_team", "market_value_eur", "caps"]], on="player_id", how="left")
jugadores = pd.merge(jugadores, teams[["team_id", "team_name"]], on="team_id", how="left")

jugadores = jugadores.drop(columns=["player_id", "team_id"])

jugadores = jugadores.rename(columns={
    "player_name": "nombre_jugador",
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

jugadores = jugadores.set_index("nombre_jugador")

print(jugadores)

# EVENTOS
eventos = register[["match_id", "minute", "event_type", "team_id", "player_id"]]
eventos = pd.merge(eventos, partidos.reset_index()[["index_partido", "match_id"]], on="match_id", how="left") # .reset_index() para poder hacer merge con index_partido
eventos = pd.merge(eventos, squads[["player_id", "player_name"]], on="player_id", how="left")
eventos = pd.merge(eventos, teams[["team_id", "team_name"]], on="team_id", how="left")

eventos = eventos.drop(columns=["match_id", "player_id", "team_id"])
partidos = partidos.drop(columns=["match_id"])

eventos = eventos.rename(columns={
    "minute": "minuto_evento",
    "event_type": "tipo_evento",
    "player_name": "nombre_jugador",
    "team_name": "seleccion_evento",
})

eventos.index = range(1, len(eventos) + 1)
eventos.index.name = "index_evento"

print(eventos)


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


# TRATAMIENTO

# Partidos
# 1 árbitro nulo
partidos["arbitro_partido"] = partidos["arbitro_partido"].fillna("Desconocido")

# Jugadores
# Hay muchos nulos en columnas numéricas (goles, asistencias,...)
# Tiene sentido que los nulos sean en realidad 0, por lo que sustituimos los valores
columnas_nulos =["paradas", "goles_concedidos", "goles", "asistencias", "tarjetas_amarillas", "tarjetas_rojas"]
for columna in columnas_nulos:
    jugadores[columna] = jugadores[columna].fillna(0)

# Eventos

# Minutos anómalos --> Hay minutos negativos o por encima de la duración del partido que ponemos como nulos para imputarlos más adelante
eventos.loc[(eventos["minuto_evento"] < 0) | (eventos["minuto_evento"] > 130), "minuto_evento"] = np.nan

eventos["tipo_evento"].unique() # Vemos que VAR review y review VAR son lo mismo
eventos["tipo_evento"] = eventos["tipo_evento"].replace({"Review VAR": "VAR Review"})
eventos["tipo_evento"].unique()

# Fechas
import re

MESES_LISTA = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
               "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}
MESES_EN = {
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
        return int(dia), int(mes), int(anio)

    # 20260619 
    pattern = re.match(r"(\d{4})(\d{2})(\d{2})$", fecha)
    if pattern:
        anio, mes, dia = pattern.groups()
        return int(dia), int(mes), int(anio)

    # 25-jun-26
    pattern = re.match(r"(\d{1,2})-([a-zA-Z]{3})-(\d{2})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return int(dia), MESES_EN[mes_txt.lower()], 2000 + int(anio)

    # 06-21-2026  
    pattern = re.match(r"(\d{2})-(\d{2})-(\d{4})$", fecha)
    if pattern:
        mes, dia, anio = pattern.groups()
        return int(dia), int(mes), int(anio)

    # 26.06.2026 
    pattern = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})$", fecha)
    if pattern:
        dia, mes, anio = pattern.groups()
        return int(dia), int(mes), int(anio)

    # 27/06/2026 
    pattern = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", fecha)
    if pattern:
        a, b, anio = pattern.groups()
        a, b, anio = int(a), int(b), int(anio)
        # El Mundial solo se juega en junio (6) y julio (7)

        if b in (6, 7):
            dia, mes = a, b
        else:
            dia, mes = b, a
        return dia, mes, anio

    # Jun 20 2026  
    pattern = re.match(r"([a-zA-Z]{3})\s+(\d{1,2})\s+(\d{4})$", fecha)
    if pattern:
        mes_txt, dia, anio = pattern.groups()
        return int(dia), MESES_EN[mes_txt.lower()], int(anio)

    # June 22, 2026  
    pattern = re.match(r"([a-zA-Z]+)\s+(\d{1,2}),\s*(\d{4})$", fecha)
    if pattern:
        mes_txt, dia, anio = pattern.groups()
        return int(dia), MESES_EN[mes_txt.lower()], int(anio)

    # 21 June 2026  
    pattern = re.match(r"(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return int(dia), MESES_EN[mes_txt.lower()], int(anio)

    # 20 de junio de 2026
    pattern = re.match(r"(\d{1,2}) de ([a-zA-Zñ]+) de (\d{4})$", fecha)
    if pattern:
        dia, mes_txt, anio = pattern.groups()
        return int(dia), MESES_ES[mes_txt.lower()], int(anio)

def formato_fecha(resultado):
    dia, mes, anio = resultado
    return f"{dia:02d}/{MESES_LISTA[mes - 1]}/{anio % 100:02d}"

partidos["fecha_partido"] = partidos["fecha_partido"].apply(actualizar_fecha).apply(formato_fecha)