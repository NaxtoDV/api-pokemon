"""
test_integration.py — Pruebas de INTEGRACIÓN de los endpoints FastAPI.

Verifica que los componentes (endpoint → lógica → BD) funcionen correctamente juntos.
PokeAPI siempre está mockeada: se prueba el sistema, no la red externa.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import database



# Helpers
def _build_pokeapi_response(pokemon_id, name, height, weight, types):
    return {
        "id": pokemon_id,
        "name": name,
        "height": height,
        "weight": weight,
        "types": [{"type": {"name": t}} for t in types],
    }


def _make_mock_client(payload=None, status_code=200, exception=None):
    """
    Construye un mock completo de httpx.AsyncClient como context manager.
    Parchamos 'app.httpx.AsyncClient' (donde realmente se usa), no httpx global.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = payload or {}

    mock_client_instance = AsyncMock()

    if exception:
        mock_client_instance.get = AsyncMock(side_effect=exception)
    else:
        mock_client_instance.get = AsyncMock(return_value=mock_response)

    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

    return mock_client_class, mock_client_instance



# GET /pokemon/search
class TestSearchEndpoint:

    @pytest.mark.asyncio
    async def test_successful_search_persists_pokemon_and_logs_history(self, async_client):
        """
        Una búsqueda exitosa debe hacer tres cosas a la vez:
        responder 200, guardar el Pokémon en BD y registrar la búsqueda en historial.
        """
        payload = _build_pokeapi_response(132, "ditto", 3, 40, ["normal"])
        mock_client_class, _ = _make_mock_client(payload=payload)

        with patch("app.httpx.AsyncClient", mock_client_class):
            response = await async_client.get("/pokemon/search?query=ditto")

        assert response.status_code == 200
        assert response.json()["name"] == "ditto"

        saved = database.get_all_pokemon()
        assert any(p["name"] == "ditto" for p in saved)

        history = database.get_query_history()
        assert history[0]["search_term"] == "ditto"
        assert history[0]["pokemon_name"] == "ditto"

    @pytest.mark.asyncio
    async def test_failed_search_logs_history_without_pokemon(self, async_client):
        """
        Una búsqueda fallida (404) debe registrarse en el historial con
        pokemon_name=null y no guardar nada en la tabla de pokemon.
        """
        mock_client_class, _ = _make_mock_client(status_code=404)

        with patch("app.httpx.AsyncClient", mock_client_class):
            response = await async_client.get("/pokemon/search?query=digimon")

        assert response.status_code == 404

        assert database.get_all_pokemon() == []

        history = database.get_query_history()
        assert history[0]["search_term"] == "digimon"
        assert history[0]["pokemon_name"] is None

    @pytest.mark.asyncio
    async def test_second_request_uses_cache_without_calling_pokeapi(self, async_client):
        """
        El segundo request al mismo Pokémon debe usar el caché local.
        PokeAPI solo debe llamarse una vez, no dos.
        """
        payload = _build_pokeapi_response(25, "pikachu", 4, 60, ["electric"])
        mock_client_class, mock_instance = _make_mock_client(payload=payload)

        with patch("app.httpx.AsyncClient", mock_client_class):
            await async_client.get("/pokemon/search?query=pikachu")
            await async_client.get("/pokemon/search?query=pikachu")

        assert mock_instance.get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_hit_still_logs_to_history(self, async_client):
        """
        Incluso cuando se usa el caché, la búsqueda debe quedar registrada
        en el historial. Cada request cuenta.
        """
        payload = _build_pokeapi_response(25, "pikachu", 4, 60, ["electric"])
        mock_client_class, _ = _make_mock_client(payload=payload)

        with patch("app.httpx.AsyncClient", mock_client_class):
            await async_client.get("/pokemon/search?query=pikachu")
            await async_client.get("/pokemon/search?query=pikachu")

        assert len(database.get_query_history()) == 2

    @pytest.mark.asyncio
    async def test_timeout_returns_504(self, async_client):
        """Timeout de PokeAPI debe traducirse en 504 al cliente, no en error genérico."""
        import httpx
        mock_client_class, _ = _make_mock_client(exception=httpx.TimeoutException("timeout"))

        with patch("app.httpx.AsyncClient", mock_client_class):
            response = await async_client.get("/pokemon/search?query=pikachu")

        assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_connect_error_returns_503(self, async_client):
        """Error de conexión con PokeAPI debe traducirse en 503 al cliente."""
        import httpx
        mock_client_class, _ = _make_mock_client(exception=httpx.ConnectError("error"))

        with patch("app.httpx.AsyncClient", mock_client_class):
            response = await async_client.get("/pokemon/search?query=pikachu")

        assert response.status_code == 503



# GET /pokemon/{id}
class TestGetByIdEndpoint:

    @pytest.mark.asyncio
    async def test_successful_search_by_id_persists_pokemon(self, async_client):
        """
        Buscar por ID debe responder 200, guardar el Pokémon en BD
        y registrar la búsqueda en historial, igual que por nombre.
        """
        payload = _build_pokeapi_response(132, "ditto", 3, 40, ["normal"])
        mock_client_class, _ = _make_mock_client(payload=payload)

        with patch("app.httpx.AsyncClient", mock_client_class):
            response = await async_client.get("/pokemon/132")

        assert response.status_code == 200
        assert response.json()["id"] == 132

        assert any(p["id"] == 132 for p in database.get_all_pokemon())

    @pytest.mark.asyncio
    async def test_cache_shared_between_name_and_id(self, async_client):
        """
        Buscar por nombre y luego por ID del mismo Pokémon solo debe
        llamar a PokeAPI una vez: el caché es compartido.
        """
        payload = _build_pokeapi_response(25, "pikachu", 4, 60, ["electric"])
        mock_client_class, mock_instance = _make_mock_client(payload=payload)

        with patch("app.httpx.AsyncClient", mock_client_class):
            await async_client.get("/pokemon/search?query=pikachu")
            await async_client.get("/pokemon/25")

        assert mock_instance.get.call_count == 1



# GET /pokemon  (listar guardados)
class TestListPokemonEndpoint:

    @pytest.mark.asyncio
    async def test_failed_search_does_not_appear_in_list(self, async_client):
        """
        Un Pokémon no encontrado no debe aparecer en /pokemon.
        Solo los encontrados exitosamente se listan.
        """
        mock_client_class, _ = _make_mock_client(status_code=404)

        with patch("app.httpx.AsyncClient", mock_client_class):
            await async_client.get("/pokemon/search?query=digimon")

        response = await async_client.get("/pokemon")
        assert response.json() == []



# GET /history
class TestHistoryEndpoint:

    @pytest.mark.asyncio
    async def test_history_ordered_most_recent_first(self, async_client):
        """
        El historial debe mostrar la búsqueda más reciente primero,
        independientemente del orden en que se realizaron.
        """
        for name in ("snorlax", "eevee"):
            payload = _build_pokeapi_response(1, name, 5, 50, ["normal"])
            mock_client_class, _ = _make_mock_client(payload=payload)
            with patch("app.httpx.AsyncClient", mock_client_class):
                await async_client.get(f"/pokemon/search?query={name}")

        response = await async_client.get("/history")
        data = response.json()

        assert data[0]["search_term"] == "eevee"
        assert data[1]["search_term"] == "snorlax"