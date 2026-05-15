"""
conftest.py — Fixtures compartidos para pruebas unitarias y de integración.
Cada prueba usa una base de datos temporal en memoria para garantizar aislamiento total.
"""
import sys
import os
import pytest
import pytest_asyncio
import sqlite3 as sqlite
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Ruta de BD en memoria (aislada por prueba) ──────────────────────────────
TEST_DB_PATH = ":memory:"


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """
    Redirige TODAS las conexiones SQLite a un archivo temporal único por prueba.
    Se aplica automáticamente a cada test (autouse=True).
    - tmp_path: directorio temporal provisto por pytest (borrado al terminar).
    - monkeypatch: reemplaza settings.database_path en tiempo de ejecución.
    """
    db_file = str(tmp_path / "test_pokedex.db")

    # Parchamos el valor de settings en ambos módulos que lo importan
    monkeypatch.setattr("config.settings.database_path", db_file)
    monkeypatch.setattr("database.settings.database_path", db_file)

    # Inicializamos el esquema en la BD temporal
    import database
    database.initialize_database()

    yield db_file  # el test recibe la ruta si la necesita


@pytest_asyncio.fixture
async def async_client():
    """
    Cliente HTTP asíncrono que habla directamente con la app FastAPI (sin red real).
    Importamos 'app' dentro del fixture para que los parches de settings ya estén activos.
    """
    from app import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_pokeapi_success():
    """
    Mock de httpx.AsyncClient.get que devuelve una respuesta exitosa de PokeAPI
    para 'ditto' (id=132). Reutilizable en varias pruebas de integración.
    """
    fake_payload = {
        "id": 132,
        "name": "ditto",
        "height": 3,
        "weight": 40,
        "types": [{"type": {"name": "normal"}}],
    }

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_payload

    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        yield mock_get


@pytest.fixture
def mock_pokeapi_not_found():
    """Mock de httpx.AsyncClient.get que simula un 404 de PokeAPI."""
    mock_response = AsyncMock()
    mock_response.status_code = 404

    mock_get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient.get", mock_get):
        yield mock_get


@pytest.fixture
def mock_pokeapi_timeout():
    """Mock que simula un TimeoutException de PokeAPI."""
    import httpx

    mock_get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("httpx.AsyncClient.get", mock_get):
        yield mock_get


@pytest.fixture
def mock_pokeapi_connect_error():
    """Mock que simula un ConnectError de PokeAPI."""
    import httpx

    mock_get = AsyncMock(side_effect=httpx.ConnectError("no connection"))

    with patch("httpx.AsyncClient.get", mock_get):
        yield mock_get