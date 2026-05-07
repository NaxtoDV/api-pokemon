from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

class PokemonResponse(BaseModel):
    id: int
    name: str
    height: int
    weight: int
    types: list[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "types": ["electric"]
            }
        }

class QueryHistoryResponse(BaseModel):
    query_id: int
    pokemon_name: str |None = None
    search_term: str
    queried_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": 1,
                "pokemon_name": "pikachu",
                "search_term": "pikachu",
                "queried_at": "2026-05-05T15:30:00"
            }
        }


@app.get(
        '/pokemon/{pokemon_id_or_name}', 
        response_model=PokemonResponse,
        summary="Obtener un Pokemon",
        description="Busca un Pokemon por nombre o ID en la PokéAPI. Si se encuentra, guarda sus datos localmente y registra la consulta. Si no existe, solo se guarda el término buscado en el historial sin almacenar ningún Pokemon.",
        tags=["Pokemon"])
async def get_pokemon(pokemon_id_or_name: str):

    """
    Busca un Pokemon por nombre o ID en la PokéAPI.
    Si existe, lo guarda en la base local y registra la búsqueda.
    Si no existe, solo registra la búsqueda fallida.
    """

    search_term = pokemon_id_or_name.lower()
    pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{search_term}"

    async with httpx.AsyncClient() as client:
        response = await client.get(pokeapi_url)

    if response.status_code == 200:
        pokemon_data = response.json()
        pokemon_info = {
            "id": pokemon_data["id"],
            "name": pokemon_data["name"],
            "height": pokemon_data["height"],
            "weight": pokemon_data["weight"],
            "types": [type_info["type"]["name"] for type_info in pokemon_data["types"]]
        }

        database.save_pokemon(
            pokemon_id = pokemon_info["id"],
            name = pokemon_info["name"],
            height = pokemon_info["height"],
            weight = pokemon_info["weight"],
            types_list= pokemon_info["types"]
        )

        database.log_query(pokemon_id = pokemon_info["id"], search_term= search_term)

        return pokemon_info
    
    elif response.status_code == 404:
        database.log_query(pokemon_id = None, search_term = search_term)
        raise HTTPException(status_code=404, detail="That pokemon does not exist")
    else:
        raise HTTPException(status_code=500, detail="Error communicating with the PokeAPI")
    
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