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

app = FastAPI(lifespan=lifespan)

class PokemonResponse(BaseModel):
    id: int
    name: str
    height: int
    weight: int
    types: list[str]

class QueryHistoryResponse(BaseModel):
    query_id: int
    pokemon_name: str
    queried_at: str


@app.get('/pokemon/{pokemon_id_or_name}', response_model=PokemonResponse)
async def get_pokemon(pokemon_id_or_name: str):
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

        database.log_query(pokemon_id = pokemon_info["id"])

        return pokemon_info
    
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="That pokemon does not exist")
    else:
        raise HTTPException(status_code=500, detail="Error communicating with the PokeAPI")
    
@app.get('/pokemon', response_model=list[PokemonResponse])
def get_all_saved_pokemon():

    saved_pokemon = database.get_all_pokemon()
    return saved_pokemon 

@app.get('/history', response_model=list[QueryHistoryResponse])
def get_search_history():

    history = database.get_query_history()
    return history