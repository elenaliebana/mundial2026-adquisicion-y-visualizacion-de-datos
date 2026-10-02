import pandas as pd

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
partidos = matches[["date", "stage_id", "venue_id", "home_team_id", "away_team_id","home_score", "away_score", "result_type","home_penalty_score", "away_penalty_score", "referee_id"]]
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



