import sqlite3 as sqlite
from datetime import datetime
from config import settings

def initialize_database():
    with sqlite.connect(settings.database_path) as connection:
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pokemon (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                height INTEGER,
                weight INTEGER,
                types TEXT
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

    connection.close()

def save_pokemon(pokemon_id, name, height, weight, types_list):
    types_text = ", ".join(types_list)

    with sqlite.connect(settings.database_path) as connection:
        cursor = connection.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO pokemon (id, name, height, weight, types)
            VALUES (?, ?, ?, ?, ?)
            ''', (pokemon_id, name, height, weight, types_text))
        connection.commit()

    connection.close()

def log_query(pokemon_id, search_term):
    current_time = datetime.now().isoformat()
    
    with sqlite.connect(settings.database_path) as connection:
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO queries (pokemon_id, search_term, queried_at)
            VALUES (?, ?, ?)
        ''', (pokemon_id, search_term, current_time))
        
        connection.commit()

    connection.close()

def get_all_pokemon():
    pokemon_list = []

    with sqlite.connect(settings.database_path) as connection:
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM pokemon')

        rows = cursor.fetchall()

        for row in rows:
            types_string = row[4]
            types_list = types_string.split(", ")

            pokemon_dict = {
                "id": row[0],
                "name": row[1],
                "height": row[2],
                "weight": row[3],
                "types": types_list
            }

            pokemon_list.append(pokemon_dict)
        
    connection.close()

    return pokemon_list

    

def get_query_history():
    history_list = []

    with sqlite.connect(settings.database_path) as connection:
        cursor = connection.cursor()

        cursor.execute('''
            SELECT queries.id, pokemon.name, queries.search_term, queries.queried_at
            FROM queries
            LEFT JOIN pokemon ON queries.pokemon_id = pokemon.id
            ORDER BY queries.queried_at DESC
        ''')

        rows = cursor.fetchall()

        for row in rows:
            history_dict = {
                "query_id": row[0],
                "pokemon_name": row[1],
                "search_term": row[2],
                "queried_at": row[3]
            }

            history_list.append(history_dict)
        
    connection.close()
    return history_list