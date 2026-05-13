from fastapi import FastAPI, HTTPException, Query
from schemas import PokemonResponse, QueryHistoryResponse
from contextlib import asynccontextmanager
import httpx
import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting...")

    database.initialize_database()

    yield

    print("Shutting down...")

app = FastAPI(
    lifespan=lifespan,
    title= "Pokemon API",
    description="API para consultar Pokemon desde la PokeAPI y mantener un historial de busquedas",
    version="1.0.0")


async def fetch_and_save_pokemon(search_term: str):
    
    local_pokemon = database.get_pokemon_local(search_term)
    
    if local_pokemon:
        database.log_query(pokemon_id=local_pokemon["id"], search_term=search_term)
        return local_pokemon

    pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{search_term}"

    async with httpx.AsyncClient() as client:
        response = await client.get(pokeapi_url)

    if response.status_code == 404:
        database.log_query(pokemon_id=None, search_term=search_term)
        raise HTTPException(status_code=404, detail="That pokemon does not exist")
        
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error communicating with the PokeAPI")

    pokemon_data = response.json()
    pokemon_info = { 
        "id": pokemon_data["id"],
        "name": pokemon_data["name"],
        "height": pokemon_data["height"],
        "weight": pokemon_data["weight"],
        "types": [type_info["type"]["name"] for type_info in pokemon_data["types"]]
    }

    database.save_pokemon(
        pokemon_id=pokemon_info["id"],
        name=pokemon_info["name"],
        height=pokemon_info["height"],
        weight=pokemon_info["weight"],
        types_list=pokemon_info["types"]
    )

    database.log_query(pokemon_id=pokemon_info["id"], search_term=search_term)
    return pokemon_info

@app.get(
    '/pokemon/search', 
    response_model=PokemonResponse,
    summary="Buscar un Pokemon por nombre",
    description="Busca un Pokemon estrictamente por su nombre utilizando un Query Parameter.",
    tags=["Pokemon"]
)
async def search_pokemon(query: str = Query(..., description="Nombre del Pokemon a buscar")):
    """
    Busca un Pokemon por nombre.
    """
    if query.isdigit():
        raise HTTPException(
            status_code=400, 
            detail="Para buscar por número, utiliza el endpoint /pokemon/{id}"
        )

    search_term = query.lower()
    return await fetch_and_save_pokemon(search_term)

@app.get(
    '/pokemon/{id}', 
    response_model=PokemonResponse,
    summary="Obtener un Pokemon por ID",
    description="Busca un Pokemon estrictamente por su ID numérico utilizando un Path Parameter.",
    tags=["Pokemon"]
)
async def get_pokemon_by_id(id: int):
    """
    Busca un Pokemon por ID numérico.
    """
    search_term = str(id)
    return await fetch_and_save_pokemon(search_term)
    
@app.get('/pokemon', 
         response_model=list[PokemonResponse],
         summary="Listar Pokemon guardados",
         description="Devuelve una lista de todos los Pokémon que han sido consultados y almacenados localmente.",
         tags=["Pokemon"])
def get_all_saved_pokemon():

    """Devuelve todos los Pokemon que han sido consultados y almacenados localmente."""

    saved_pokemon = database.get_all_pokemon()
    return saved_pokemon 

@app.get('/history', response_model=list[QueryHistoryResponse],
         summary="Ver historial de búsquedas",
         description="Devuelve una lista de todas las búsquedas realizadas en la API.",
         tags=["Historial"],)
def get_search_history():

    """Devuelve el historial completo de búsquedas realizadas, incluyendo las que no encontraron ningún Pokemon."""

    history = database.get_query_history()
    return history