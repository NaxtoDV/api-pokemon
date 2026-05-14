import sqlite3 as sqlite
from datetime import datetime, timedelta
from contextlib import closing
from config import settings
from schemas import PokemonResponse, QueryHistoryResponse


def initialize_database():
    with closing(sqlite.connect(settings.database_path)) as connection:
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                height INTEGER,
                weight INTEGER,
                types TEXT,
                updated_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pokemon_id INTEGER,
                search_term TEXT,
                queried_at DATETIME
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pokemon_name ON pokemon(name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_queries_pokemon_id ON queries(pokemon_id)
        ''')

        connection.commit()
        print("Database verified and tables are ready.")


def save_pokemon(pokemon_id, name, height, weight, types_list):
    
    types_text = ", ".join(types_list)
    current_time = datetime.now().isoformat()

    with closing(sqlite.connect(settings.database_path)) as connection:
        cursor = connection.cursor()

        
        cursor.execute('''
            INSERT OR REPLACE INTO pokemon (id, name, height, weight, types, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (pokemon_id, name, height, weight, types_text, current_time))

        connection.commit()


def log_query(pokemon_id, search_term):
    current_time = datetime.now().isoformat()

    with closing(sqlite.connect(settings.database_path)) as connection:
        cursor = connection.cursor()

        
        cursor.execute('''
            INSERT INTO queries (pokemon_id, search_term, queried_at)
            VALUES (?, ?, ?)
        ''', (pokemon_id, search_term, current_time))

        connection.commit()


def get_pokemon_local(search_term):
    """
    Busca un Pokémon en la base de datos local por ID o por nombre.
    Retorna un diccionario con los datos si existe y NO ha caducado, o None.
    """
    with closing(sqlite.connect(settings.database_path)) as connection:
        
        connection.row_factory = sqlite.Row
        cursor = connection.cursor()

        
        if str(search_term).isdigit():
            cursor.execute('SELECT * FROM pokemon WHERE id = ?', (int(search_term),))
        else:
            cursor.execute('SELECT * FROM pokemon WHERE name = ?', (search_term,))

        row = cursor.fetchone()

    
    if not row:
        return None

    
    if not row["updated_at"]:
        return None

    
    last_update = datetime.fromisoformat(row["updated_at"])
    if datetime.now() >= last_update + timedelta(seconds=settings.cache_ttl):
        print(f"DEBUG: El caché de {search_term} ha caducado.")
        return None

    
    pokemon = PokemonResponse.model_validate(dict(row))
    return pokemon.model_dump()


def get_all_pokemon():
    with closing(sqlite.connect(settings.database_path)) as connection:
        
        connection.row_factory = sqlite.Row
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM pokemon')
        rows = cursor.fetchall()


    pokemon_list = []
    for row in rows:
        pokemon = PokemonResponse.model_validate(dict(row))
        pokemon_list.append(pokemon.model_dump())

    return pokemon_list


def get_query_history():
    with closing(sqlite.connect(settings.database_path)) as connection:
    
        connection.row_factory = sqlite.Row
        cursor = connection.cursor()

        cursor.execute('''
            SELECT queries.id        AS query_id,
                   pokemon.name      AS pokemon_name,
                   queries.search_term,
                   queries.queried_at
            FROM queries
            LEFT JOIN pokemon ON queries.pokemon_id = pokemon.id
            ORDER BY queries.queried_at DESC
        ''')
        rows = cursor.fetchall()

    history_list = []
    for row in rows:
        query = QueryHistoryResponse.model_validate(dict(row))
        history_list.append(query.model_dump())

    return history_list