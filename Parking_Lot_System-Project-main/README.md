# Parking_Lot_System-Project
# GoParking Setup and Usage

## Prerequisites

- Python with the installed `streamlit` and `pandas` packages.
- A JDK for compiling the Java files when `.class` files are absent or stale.
- Windows Command Prompt, PowerShell, or another terminal.

The project has no `requirements.txt`, `pyproject.toml`, Maven, or Gradle
manifest. If required, install the Python runtime packages into the intended
environment:

```cmd
python -m pip install streamlit pandas
```

## Configure the first administrator

When no administrator is present, set the following variables in the same
terminal session that starts Streamlit:

```cmd
set GOPARKING_ADMIN_NAME=Parking Administrator
set GOPARKING_ADMIN_EMAIL=admin@example.com
set GOPARKING_ADMIN_PASSWORD=replace-with-a-long-unique-password
```

Use a unique password with at least 12 characters. Never publish real
credentials. The first successful bootstrap creates the administrator and
assigns any historical rows without owners to that account. Subsequent app
starts do not reset credentials from the environment.

For PowerShell, use `$env:GOPARKING_ADMIN_NAME = "..."`, and similarly set the
email and password before starting Streamlit. In Command Prompt, use `set`,
not PowerShell's `Set-Location`; use `cd /d "C:\path\to\project"` to change
drives and directories.

## Start the Java parking server

Open a terminal and compile/start the server:

```cmd
cd /d "C:\path\to\GoParking - Copy\java_backend"
javac *.java
java -cp . ParkingServer
```

The server listens on local port 5000. Keep this process running.

## Start the Streamlit application

Open a second terminal:

```cmd
cd /d "C:\path\to\GoParking - Copy"
streamlit run app.py
```

For first-run admin creation, configure the environment variables in this
same terminal before the Streamlit command. Open the local URL printed by
Streamlit, usually `http://localhost:8501`.

Keep the `.streamlit` configuration and `static/parking` image folder beside
`app.py`; Streamlit uses them to serve the locally bundled page backgrounds.
Restart Streamlit after changing the static-serving configuration.

## Typical user workflow

1. Create an account with a valid email shape and a password of at least 12
   characters.
2. Sign in and optionally complete the profile.
3. Register a vehicle under **Register Vehicle**, or use **Park Vehicle**,
   which also registers an eligible new vehicle.
4. Use the parking dashboard or **Parking Slots** to inspect occupancy.
5. Use **Search Vehicle**, **Search by Color**, or **My Vehicles** to find
   account-owned vehicles.
6. Remove an owned parked vehicle to record its exit and calculated fee.
7. Review **Parking History** or **Payments** for the account's records.

Administrators also have **User Management** and **Fee Settings**. The admin
role can view system-wide records and change hourly rate settings.

## Backup and privacy

Stop Streamlit before making a manual backup of `goparking.db`. Keep backups
private; the database includes account contact information, password hashes,
vehicle registrations, and payment records. Do not expose the Java server's
port 5000 to an untrusted network.

## Troubleshooting

| Symptom | Action |
|---|---|
| Streamlit says the Java server is unavailable | Start `ParkingServer` and verify local port 5000 is free |
| First-admin warning remains | Set all three environment variables in the Streamlit terminal and restart |
| User cannot see another vehicle | This is expected: vehicle and history details are owner-scoped |
| Data appears empty after Java restart | Confirm SQLite has active events; startup restoration is best effort |
| Browser page differs from source | Stop the old Streamlit process and start the intended project folder |
| `Set-Location` is not recognized | The terminal is Command Prompt; use `cd /d "..."` instead |

