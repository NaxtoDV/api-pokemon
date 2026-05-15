"""
test_unit.py — Pruebas UNITARIAS de las funciones de database.py.

Solo se prueba lógica propia del proyecto, no comportamiento de librerías externas.
"""

import sqlite3 as sqlite
import pytest
from datetime import datetime, timedelta

import database
from config import settings


# initialize_database
class TestInitializeDatabase:

    def test_creates_tables(self):
        """Las tablas pokemon y queries deben existir tras inicializar la BD."""
        with sqlite.connect(settings.database_path) as conn:
            tables = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        assert "pokemon" in tables
        assert "queries" in tables



# save_pokemon
class TestSavePokemon:

    def test_saves_multiple_types_as_comma_string(self):
        """Tipos múltiples deben unirse con coma al guardarse en BD."""
        database.save_pokemon(6, "charizard", 17, 905, ["fire", "flying"])

        with sqlite.connect(settings.database_path) as conn:
            row = conn.execute("SELECT types FROM pokemon WHERE id = 6").fetchone()

        assert row[0] == "fire, flying"

    def test_upsert_does_not_duplicate(self):
        """Guardar el mismo Pokémon dos veces actualiza el registro, no lo duplica."""
        database.save_pokemon(1, "bulbasaur", 7, 69, ["grass"])
        database.save_pokemon(1, "bulbasaur", 7, 69, ["grass", "poison"])

        with sqlite.connect(settings.database_path) as conn:
            rows = conn.execute("SELECT * FROM pokemon WHERE id = 1").fetchall()

        assert len(rows) == 1
        assert rows[0][4] == "grass, poison"



# log_query
class TestLogQuery:

    def test_logs_failed_query_with_null_pokemon_id(self):
        """Búsqueda fallida debe registrarse con pokemon_id=NULL, no omitirse."""
        database.log_query(pokemon_id=None, search_term="digimon")

        history = database.get_query_history()

        assert len(history) == 1
        assert history[0]["search_term"] == "digimon"
        assert history[0]["pokemon_name"] is None

    def test_each_query_creates_independent_entry(self):
        """Buscar el mismo Pokémon dos veces genera dos entradas distintas."""
        database.save_pokemon(25, "pikachu", 4, 60, ["electric"])
        database.log_query(pokemon_id=25, search_term="pikachu")
        database.log_query(pokemon_id=25, search_term="pikachu")

        history = database.get_query_history()
        assert len(history) == 2



# get_pokemon_local — lógica de caché y TTL
class TestGetPokemonLocal:

    def test_returns_none_when_cache_expired(self):
        """Pokémon con updated_at expirado no debe devolverse del caché."""
        expired_date = (datetime.now() - timedelta(days=2)).isoformat()

        with sqlite.connect(settings.database_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pokemon (id, name, height, weight, types, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (1, "bulbasaur", 7, 69, "grass, poison", expired_date),
            )

        assert database.get_pokemon_local("bulbasaur") is None

    def test_returns_none_when_updated_at_is_missing(self):
        """Registro sin updated_at (dato corrupto) debe tratarse como expirado."""
        with sqlite.connect(settings.database_path) as conn:
            conn.execute(
                "INSERT INTO pokemon (id, name, height, weight, types, updated_at) "
                "VALUES (?, ?, ?, ?, ?, NULL)",
                (999, "missingno", 10, 10, "normal"),
            )

        assert database.get_pokemon_local("missingno") is None

    def test_types_parsed_as_list(self):
        """Los tipos se guardan como string pero deben devolverse como lista."""
        database.save_pokemon(6, "charizard", 17, 905, ["fire", "flying"])
        result = database.get_pokemon_local("charizard")

        assert result is not None
        assert isinstance(result["types"], list)
        assert result["types"] == ["fire", "flying"]