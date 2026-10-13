# GoParking Technical Documentation

## 1. Architecture

The project uses an existing Python Streamlit interface, Java parking engine,
and SQLite database:

1. Streamlit authenticates the current browser session and presents the UI.
2. Python connects to the Java server at `127.0.0.1:5000` for live parking
   operations.
3. The Java `ParkingLot` owns the in-memory slot allocation state.
4. Python writes the web app's account, vehicle, parking-event, fee, and
   payment records to `goparking.db`.

The Java process is the allocation authority. SQLite history is not
transactionally coordinated with Java memory, so an application or process
failure between the two operations can leave the systems out of sync. On
startup, `sync_active_vehicles()` attempts to restore database events whose
exit time is still null.

## 2. Components and files

```text
GoParking - Copy/
├── app.py
├── auth_security.py
├── goparking.db
├── .streamlit/
│   └── config.toml
├── static/
│   └── parking/
│       ├── aerial-parking.jpg
│       ├── multilevel-garage.jpg
│       └── underground-garage.jpg
├── tests/
│   ├── test_auth_security.py
│   └── ParkingLotSmokeTest.java
├── java_backend/
│   ├── Main.java
│   ├── ParkingServer.java
│   ├── ParkingLot.java
│   ├── ParkingSlot.java
│   ├── Vehicle.java
│   └── ParkingHistory.java
└── docs/
```

`app.py` contains Streamlit pages, SQL access, Java socket commands, and
inline HTML/CSS/SVG. `auth_security.py` contains password hashing and basic
email-shape validation. The Java sources preserve the existing console menu
and allocation model.

## 3. Identity, roles, and account scope

Accounts are stored in SQLite with unique case-insensitive email addresses,
name, optional mobile number, password hash, role, and creation timestamp.
Self-service registration always assigns the `user` role. Role is read from
the database on each Streamlit rerun; navigation alone is not the access
control. Administrator-only fee settings and user listing also check the
current role in the page branch.

Passwords use PBKDF2-HMAC-SHA256 with a random 16-byte salt and 600,000
iterations. The database stores the algorithm, iteration count, salt, and
digest—not the original password. Account passwords require at least 12
characters. Recovery email is not configured; users can change their
password after authenticating. Each account has a session version. The app
checks the signed-in version against the database on reruns; changing a
password increments it, revoking previous app sessions while updating the
current session to remain active.

Vehicle registry rows have one owner. Non-administrator vehicle lists,
history, payments, registration lookup, color results, and removal checks
are scoped to that owner. Slot status and overall occupancy remain shared,
but other users' registration, type, and color are hidden in the slot view.
Administrators can view system-wide records.

The Python app applies these ownership checks before it uses Java's
registration-based `FIND`, `COLOR`, or `REMOVE` commands. The Java protocol
itself has no user identity and is intended to remain local; it must not be
exposed as a network-facing authorization boundary.

## 4. Database and startup migration

`init_db()` creates `users`, `vehicles`, `parking_events`, `payments`, and
`parking_settings`. For an older database, it adds the session-version field
to `users`, nullable `owner_user_id` columns to events and payments, and
supporting indexes. It does not drop existing rows.

The first administrator is created only when no administrator exists and all
of these environment variables are configured:

- `GOPARKING_ADMIN_NAME`
- `GOPARKING_ADMIN_EMAIL`
- `GOPARKING_ADMIN_PASSWORD`

The initial admin bootstrap assigns legacy null-owner event/payment rows to
that admin and seeds a vehicle registry from recorded event history. This is
a one-time local migration. Back up `goparking.db` before running a new
version against important data.

## 5. Java TCP protocol

The Python client opens one TCP connection per request, sends a UTF-8 command
terminated by a newline, and reads one response line. The Java server listens
on port 5000 on the local host.

| Command | Purpose |
|---|---|
| `STATUS` | Return total, occupied, and available counts |
| `SLOTS` | Return each slot and occupied vehicle fields |
| `PARK|registration|color|type` | Allocate the lowest-numbered available slot |
| `REMOVE|registration` | Remove an active vehicle |
| `FIND|registration` | Find one parked vehicle |
| `COLOR|color` | Find parked vehicles of a color |
| `RESTORE|registration|color|type|slot` | Restore an active database event |

Fields use `|` as a delimiter. The UI rejects that character in vehicle
registration and color fields. Java validates non-empty fields and supports
the vehicle-type allowlist in `ParkingLot.java`.

## 6. Allocation and fees

The Java parking lot uses a `TreeSet<Integer>` for free slot numbers. Adding
slots and selecting the lowest available slot are logarithmic operations;
the minimum is obtained with `first()`. A `HashMap` indexes registrations to
occupied slots for expected constant-time lookup and removal. Lists preserve
vehicle and parking-history order.

Fee calculation rounds elapsed parking time upward to whole hours and
charges a one-hour minimum. Motorcycle, scooter, bicycle, and legacy `Bike`
use the two-wheel rate; other categories use the car/vehicle rate. The rates
are editable by administrators and stored in `parking_settings`. Exit fees
are recorded as database payments; they are not collected by an external
payment provider.

## 7. Interface and accessibility

The app uses inline CSS, an SVG garage illustration, responsive layout rules,
and lightweight transitions. Three optimized Unsplash photos are bundled
under `static/parking/`; `PARKING_PAGE_PHOTOS` selects a page-specific
photograph and a separate administrator dashboard background. Authenticated
page styling is applied after sidebar navigation is resolved.
`.streamlit/config.toml` enables Streamlit static file serving for the local
photos. Keep this configuration and the `static` directory when deploying.
A `prefers-reduced-motion` media rule suppresses decorative animations.
Streamlit widgets provide the forms, sidebar navigation, tables, and buttons.

## 8. Known operational limitations

- Java parking state is in memory and is reset when the Java server restarts;
  Python restoration is best effort.
- Java actions and SQLite updates are not one distributed transaction.
- The Java server has no authentication and must remain local/trusted.
- SQLite is a local single-file store without a separate migration framework.
- Password reset email, external payments, reserved slots, and vehicle-size
  allocation are not implemented.
- A production multi-user deployment needs hardened session handling,
  transport security, server-side API authorization, database concurrency
  planning, backups, and monitoring.
