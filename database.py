import sqlite3 as sqlite
from datetime import datetime


def initialize_database():
    with sqlite.connect("pokedex.db") as connection:
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
                queried_at DATETIME
            )
        ''')
        connection.commit()
        print("Database verified and tables are ready.")

def save_pokemon(pokemon_id, name, height, weight, types_list):
    types_text = ", ".join(types_list)

    with sqlite.connect("pokedex.db") as connection:
        cursor = connection.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO pokemon (id, name, height, weight, types)
            VALUES (?, ?, ?, ?, ?)
            ''', (pokemon_id, name, height, weight, types_text))
        connection.commit()

def log_query(pokemon_id):
    current_time = datetime.now()
    
    with sqlite.connect("pokedex.db") as connection:
        cursor = connection.cursor()

        cursor.execute('''
            INSERT INTO queries (pokemon_id, queried_at)
            VALUES (?, ?)
        ''', (pokemon_id, current_time))
        
        connection.commit()

def get_all_pokemon():
    pokemon_list = []

    with sqlite.connect("pokedex.db") as connection:
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
        
    return pokemon_list

def get_query_history():
    history_list = []

    with sqlite.connect("pokedex.db") as connection:
        cursor = connection.cursor()

        cursor.execute('''
            SELECT queries.id, pokemon.name, queries.queried_at
            FROM queries
            JOIN pokemon ON queries.pokemon_id = pokemon.id
            ORDER BY queries.queried_at DESC
        ''')

        rows = cursor.fetchall()

        for row in rows:
            history_dict = {
                "query_id": row[0],
                "pokemon_name": row[1],
                "queried_at": row[2]
            }

            history_list.append(history_dict)
        
    return history_list