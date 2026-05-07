import sys
import pytest
import pytest_asyncio
import os

os.environ["DATABASE_PATH"] = "test_pokedex.db"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
import database
from httpx import AsyncClient, ASGITransport
from app import app 

@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Garantiza que la base de datos de prueba esté limpia.
    Usa settings.database_path que ahora vale 'test_pokedex.db'.
    """
    db_path = settings.database_path
    if os.path.exists(db_path):
        os.remove(db_path)
        
    database.initialize_database()
    
    yield 
    
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest_asyncio.fixture
async def async_client():
    """
    Fixture para simular peticiones HTTP a la API usando httpx.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client