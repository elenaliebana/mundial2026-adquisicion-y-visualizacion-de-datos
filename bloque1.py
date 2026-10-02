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

# Crear dataframe de partidos
partidos = matches["fecha_partido", "home_score", "away_score", "result_type", "home_penalty_score", "away_penalty_score", "referee_id"]





