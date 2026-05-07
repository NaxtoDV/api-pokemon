import pytest
import database

def test_database_save_and_retrieve_pokemon():
    """Prueba Unitaria: Verifica que la BD guarde y recupere un Pokémon correctamente"""
    
    
    database.save_pokemon(
        pokemon_id=25,
        name="pikachu",
        height=4,
        weight=60,
        types_list=["electric"]
    )
    
    
    saved_pokemon = database.get_all_pokemon()
    
    assert len(saved_pokemon) == 1
    assert saved_pokemon[0]["name"] == "pikachu"
    assert saved_pokemon[0]["types"] == ["electric"]

def test_database_log_query():
    """Prueba Unitaria: Verifica que el historial registre las búsquedas"""
    
    database.log_query(pokemon_id=25, search_term="pikachu")
    
    history = database.get_query_history()
    
    assert len(history) == 1
    assert history[0]["search_term"] == "pikachu"


@pytest.mark.asyncio
async def test_get_pokemon_endpoint_success(async_client):
    """Prueba Integración: Búsqueda exitosa en /pokemon/{name}"""
    
    response = await async_client.get("/pokemon/ditto")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "ditto"
    assert "types" in data
    
    history = database.get_query_history()
    assert len(history) > 0
    assert history[0]["search_term"] == "ditto"

@pytest.mark.asyncio
async def test_get_pokemon_endpoint_not_found(async_client):
    """Prueba Integración: Búsqueda fallida en /pokemon/{name}"""
    
    response = await async_client.get("/pokemon/digimon_infiltrado")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "That pokemon does not exist"
    
    history = database.get_query_history()
    assert len(history) > 0
    assert history[0]["search_term"] == "digimon_infiltrado"

@pytest.mark.asyncio
async def test_get_all_saved_pokemon_endpoint(async_client):
    """Prueba Integración: Endpoint /pokemon lista los guardados"""
    
    await async_client.get("/pokemon/mew")
    
    response = await async_client.get("/pokemon")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert any(p["name"] == "mew" for p in data)

@pytest.mark.asyncio
async def test_get_history_endpoint(async_client):
    """Prueba Integración: Endpoint /history devuelve las búsquedas en orden"""
    
    await async_client.get("/pokemon/snorlax")
    await async_client.get("/pokemon/eevee")
    
    response = await async_client.get("/history")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 2
    
    
    assert data[0]["search_term"] == "eevee"