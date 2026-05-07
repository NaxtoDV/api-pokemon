import sys
import pytest
import pytest_asyncio
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database
from httpx import AsyncClient, ASGITransport

TEST_DB_PATH = "test_pokedex.db"
database.DATABASE_PATH = TEST_DB_PATH

from app import app 

@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Este fixture se ejecuta antes y después de cada test automáticamente.
    Garantiza que la base de datos esté limpia y lista.
    """

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        
    database.initialize_database()
    
    yield 
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest_asyncio.fixture
async def async_client():
    """
    Fixture para simular peticiones HTTP a la API usando httpx.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client