from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    database_path: str = "pokedex.db"
    cache_ttl: int = 86400  

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()