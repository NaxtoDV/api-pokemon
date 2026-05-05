### Diagrama Entidad-Relación
```mermaid
erDiagram
    POKEMON ||--o{ QUERIES : "tiene registradas"
    
    POKEMON {
        INTEGER id PK
        TEXT name
        INTEGER height
        INTEGER weight
        TEXT types
    }
    
    QUERIES {
        INTEGER id PK
        INTEGER pokemon_id FK
        TEXT search_term
        DATETIME queried_at
    }
```

### Diagrama de Arquitectura
<img width="742" height="772" alt="Diagrama sin título drawio" src="https://github.com/user-attachments/assets/92f8de1c-be9d-4d86-bf58-c797d9c2bd95" />
