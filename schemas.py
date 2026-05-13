from pydantic import BaseModel, ConfigDict, Field, field_validator

class PokemonResponse(BaseModel):
    id: int
    name: str
    height: int
    weight: int
    types: list[str]

    
    @field_validator("types", mode="before")
    @classmethod
    def parse_types(cls, v):
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 25,
                "name": "pikachu",
                "height": 4,
                "weight": 60,
                "types": ["electric"]
            }
        }
    )


class QueryHistoryResponse(BaseModel):
    query_id: int
    pokemon_name: str | None = None
    search_term: str
    queried_at: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": 1,
                "pokemon_name": "pikachu",
                "search_term": "pikachu",
                "queried_at": "2026-05-05T15:30:00"
            }
        }
    )