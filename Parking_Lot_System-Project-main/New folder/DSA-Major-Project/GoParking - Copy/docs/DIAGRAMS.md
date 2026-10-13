# GoParking Architecture and UML Diagrams

## Component architecture

```mermaid
flowchart LR
    Browser[User browser]
    UI[Streamlit app.py]
    Auth[auth_security.py]
    DB[(SQLite goparking.db)]
    Java[Java ParkingServer]
    Lot[ParkingLot]
    Slots[ParkingSlot and Vehicle]

    Browser --> UI
    UI --> Auth
    UI -->|account, registry, history, fees| DB
    UI -->|local TCP commands| Java
    Java --> Lot
    Lot --> Slots
```

The app database and Java in-memory allocation state are separate stores.
Restoration on startup is best effort; operations are not a distributed
transaction.

## Park vehicle sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit app
    participant DB as SQLite
    participant Java as ParkingServer
    participant Lot as ParkingLot

    User->>UI: Submit vehicle details
    UI->>DB: Check registration owner
    DB-->>UI: Owner record / no registration
    UI->>DB: Create or update authorized vehicle record
    UI->>Java: PARK|registration|color|type
    Java->>Lot: Validate and allocate
    Lot-->>Java: Lowest available slot
    Java-->>UI: OK|Vehicle parked|...|slot
    UI->>DB: Insert owner-scoped active event
    UI-->>User: Show allocated slot
```

## Account entity relationships

```mermaid
erDiagram
    USERS ||--o{ VEHICLES : owns
    USERS ||--o{ PARKING_EVENTS : records
    USERS ||--o{ PAYMENTS : receives
    VEHICLES {
        int id PK
        int owner_user_id FK
        string registration UK
        string vehicle_type
        string color
        string created_at
    }
    USERS {
        int id PK
        string full_name
        string email UK
        string mobile
        string password_hash
        string role
        string created_at
    }
    PARKING_EVENTS {
        int id PK
        int owner_user_id FK
        string registration
        string color
        string vehicle_type
        int slot
        string entry_time
        string exit_time
        float fee
    }
    PAYMENTS {
        int id PK
        int owner_user_id FK
        string registration
        float amount
        string paid_at
    }
```

## Parking allocation activity

```mermaid
flowchart TD
    A[Receive PARK command] --> B{Details valid and supported?}
    B -- No --> X[Return error]
    B -- Yes --> C{Registration already parked?}
    C -- Yes --> X
    C -- No --> D{Any available slot?}
    D -- No --> X
    D -- Yes --> E[Select smallest TreeSet slot]
    E --> F[Remove slot from available set]
    F --> G[Store registration in HashMap]
    G --> H[Append vehicle and history]
    H --> I[Return allocated slot]
```
