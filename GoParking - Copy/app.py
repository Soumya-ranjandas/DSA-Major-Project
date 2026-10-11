
import socket
import sqlite3
import html
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="GoParking",
    page_icon="🅿️",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "goparking.db"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

CAR_RATE = 20
BIKE_RATE = 10

# ---------------- DATABASE ----------------

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS parking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration TEXT NOT NULL,
                color TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                slot INTEGER,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                fee REAL DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registration TEXT NOT NULL,
                amount REAL NOT NULL,
                paid_at TEXT NOT NULL
            )
        """)


def db_execute(query, values=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(query, values)
        conn.commit()


def db_query(query, values=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(query, values).fetchall()
        ]


init_db()

# ---------------- JAVA CONNECTION ----------------

def send_to_java(command):
    try:
        with socket.create_connection(
            ("127.0.0.1", 5000), timeout=5
        ) as client:
            client.sendall((command + "\n").encode("utf-8"))

            with client.makefile(
                "r", encoding="utf-8"
            ) as reader:
                response = reader.readline()

        return (
            response.strip()
            if response
            else "ERROR|No response from Java"
        )

    except OSError:
        return "ERROR|Java server not running. Start ParkingServer first."


def get_status():
    response = send_to_java("STATUS")
    parts = response.split("|")

    if len(parts) == 4 and parts[0] == "STATUS":
        try:
            return tuple(map(int, parts[1:]))
        except ValueError:
            pass

    return 10, 0, 10


def get_slots():
    response = send_to_java("SLOTS")
    parts = response.split("|")

    if not parts or parts[0] != "SLOTS":
        return []

    slots = []
    i = 1

    try:
        while i < len(parts):
            number = int(parts[i])
            occupied = parts[i + 1].lower() == "true"

            if occupied:
                registration = parts[i + 2]
                color = parts[i + 3]
                vehicle_type = parts[i + 4]
            else:
                registration = ""
                color = ""
                vehicle_type = ""

            slots.append({
                "Slot": number,
                "Status": "Occupied" if occupied else "Available",
                "Registration": registration,
                "Color": color,
                "Type": vehicle_type
            })

            i += 5

    except (ValueError, IndexError):
        return []

    return slots


# ---------------- RESTORE ACTIVE VEHICLES ----------------

def sync_active_vehicles():
    """
    Restore vehicles whose exit_time is NULL.
    Existing vehicles are skipped to avoid duplicates.
    """

    status_response = send_to_java("STATUS")

    if not status_response.startswith("STATUS|"):
        return

    active_vehicles = db_query("""
        SELECT registration, color, vehicle_type, slot
        FROM parking_events
        WHERE exit_time IS NULL
        ORDER BY id ASC
    """)

    for vehicle in active_vehicles:
        registration = vehicle["registration"]
        color = vehicle["color"]
        vehicle_type = vehicle["vehicle_type"]
        slot = vehicle["slot"]

        # Skip if the vehicle already exists in Java.
        find_response = send_to_java(f"FIND|{registration}")

        if find_response.startswith("FOUND|"):
            continue

        if slot is None:
            continue

        restore_command = (
            f"RESTORE|{registration}|{color}|"
            f"{vehicle_type}|{int(slot)}"
        )

        restore_response = send_to_java(restore_command)

        if restore_response.startswith("OK|"):
            print(
                f"Restored {registration} to slot {slot}"
            )
        elif restore_response.startswith("ERROR|"):
            print(
                f"Restore issue for {registration}: "
                f"{restore_response}"
            )


# ---------------- DATABASE HISTORY ----------------

def record_entry(registration, color, vehicle_type, slot):
    now = datetime.now().isoformat(timespec="seconds")

    db_execute("""
        INSERT INTO parking_events
        (registration, color, vehicle_type, slot,
         entry_time, exit_time, fee)
        VALUES (?, ?, ?, ?, ?, NULL, 0)
    """, (
        registration, color, vehicle_type, slot, now
    ))


def record_exit(registration):
    events = db_query("""
        SELECT id, entry_time, vehicle_type
        FROM parking_events
        WHERE UPPER(registration) = UPPER(?)
          AND exit_time IS NULL
        ORDER BY id DESC
        LIMIT 1
    """, (registration,))

    if not events:
        return None

    event = events[0]
    now = datetime.now()
    entry = datetime.fromisoformat(event["entry_time"])

    seconds = max(0, (now - entry).total_seconds())
    hours = max(1, int(seconds // 3600) +
                (1 if seconds % 3600 else 0))

    rate = (
        BIKE_RATE
        if event["vehicle_type"].lower() == "bike"
        else CAR_RATE
    )
    fee = hours * rate

    db_execute("""
        UPDATE parking_events
        SET exit_time = ?, fee = ?
        WHERE id = ?
    """, (
        now.isoformat(timespec="seconds"),
        fee,
        event["id"]
    ))

    db_execute("""
        INSERT INTO payments (registration, amount, paid_at)
        VALUES (?, ?, ?)
    """, (
        registration,
        fee,
        now.isoformat(timespec="seconds")
    ))

    return fee


# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# ---------------- STYLE ----------------

st.markdown("""
<style>
.stApp {
    background: #0b1220;
    color: #f3f4f6;
}
.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
}
.hero {
    padding: 24px;
    border-radius: 18px;
    background: linear-gradient(120deg, #172554, #0f766e);
    margin-bottom: 22px;
}
.metric-card {
    padding: 18px;
    border-radius: 14px;
    background: #172033;
    border: 1px solid #29364d;
}
.slot-card {
    padding: 14px;
    border-radius: 12px;
    min-height: 105px;
    margin-bottom: 10px;
    color: white;
}
.slot-free {
    background: #14532d;
}
.slot-busy {
    background: #7f1d1d;
}
.small-note {
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)


# ---------------- LOGIN ----------------

if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
        <h1>🅿️ GoParking</h1>
        <p>Parking Allotment Management System</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input(
            "Password", type="password"
        )
        submitted = st.form_submit_button(
            "Login", use_container_width=True
        )

    if submitted:
        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.info(
        "Demo login: admin / admin123. "
        "Change these credentials before deployment."
    )
    st.stop()


# ---------------- SIDEBAR ----------------

st.sidebar.title("🅿️ GoParking")
st.sidebar.caption("Parking Management System")

pages = [
    "Dashboard",
    "Park Vehicle",
    "Remove Vehicle",
    "Search Vehicle",
    "Search by Color",
    "Parking Slots",
    "Parking History",
    "Fee Calculator",
    "Payments"
]

st.session_state.page = st.sidebar.radio(
    "Navigation",
    pages,
    index=(
        pages.index(st.session_state.page)
        if st.session_state.page in pages else 0
    )
)

if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()


st.markdown("""
<div class="hero">
    <h1>🅿️ GoParking Dashboard</h1>
    <p>Smart parking powered by Java DSA and Streamlit</p>
</div>
""", unsafe_allow_html=True)


# ---------------- LIVE METRICS ----------------

# Sync before reading the current Java parking status.
sync_active_vehicles()

total, occupied, available = get_status()

m1, m2, m3 = st.columns(3)

for col, label, value in [
    (m1, "Total Slots", total),
    (m2, "Occupied Slots", occupied),
    (m3, "Available Slots", available)
]:
    with col:
        st.markdown(
            f'<div class="metric-card"><p>{label}</p>'
            f'<h2>{value}</h2></div>',
            unsafe_allow_html=True
        )

st.divider()


# ---------------- DASHBOARD ----------------

page = st.session_state.page

if page == "Dashboard":
    st.subheader("Parking Overview")
    slots = get_slots()

    if slots:
        df = pd.DataFrame(slots)
        left, right = st.columns(2)

        with left:
            st.markdown("**Slot Availability**")
            st.bar_chart(df["Status"].value_counts())

        with right:
            st.markdown("**Parking Slot Map**")

            for start in range(0, len(slots), 5):
                cols = st.columns(5)

                for col, slot in zip(
                    cols, slots[start:start + 5]
                ):
                    css = (
                        "slot-busy"
                        if slot["Status"] == "Occupied"
                        else "slot-free"
                    )
                    title = f'Slot {slot["Slot"]}'
                    detail = (
                        html.escape(slot["Registration"])
                        if slot["Registration"]
                        else "Available"
                    )

                    col.markdown(
                        f'<div class="slot-card {css}">'
                        f'<b>{title}</b><br>{detail}</div>',
                        unsafe_allow_html=True
                    )

    history = db_query("""
        SELECT registration, entry_time, exit_time, fee
        FROM parking_events
        ORDER BY id DESC
        LIMIT 10
    """)

    st.subheader("Recent Activity")

    if history:
        st.dataframe(
            pd.DataFrame(history),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Abhi koi database history record nahi hai.")


# ---------------- PARK VEHICLE ----------------

elif page == "Park Vehicle":
    st.subheader("Park a Vehicle")

    with st.form("park_form"):
        registration = st.text_input(
            "Registration Number"
        ).strip().upper()
        color = st.text_input("Vehicle Color").strip()
        vehicle_type = st.selectbox(
            "Vehicle Type", ["Car", "Bike", "Other"]
        )
        submitted = st.form_submit_button(
            "Park Vehicle", use_container_width=True
        )

    if submitted:
        if not registration or not color:
            st.error(
                "Registration number aur color required hain."
            )
        elif any("|" in value for value in (
            registration, color, vehicle_type
        )):
            st.error("Vehicle details mein '|' character use nahi kar sakte.")
        else:
            response = send_to_java(
                f"PARK|{registration}|{color}|{vehicle_type}"
            )
            parts = response.split("|")

            if (
                len(parts) >= 6
                and parts[0] == "OK"
                and parts[1] == "Vehicle parked"
            ):
                slot = int(parts[5])
                record_entry(
                    registration, color, vehicle_type, slot
                )
                st.success(
                    f"Vehicle parked successfully at Slot {slot}."
                )
                st.rerun()
            else:
                st.error(response.replace("|", " "))


# ---------------- REMOVE VEHICLE ----------------

elif page == "Remove Vehicle":
    st.subheader("Remove a Vehicle")

    with st.form("remove_form"):
        registration = st.text_input(
            "Registration Number"
        ).strip().upper()
        submitted = st.form_submit_button(
            "Remove Vehicle", use_container_width=True
        )

    if submitted:
        if not registration:
            st.error("Registration number enter karo.")
        else:
            response = send_to_java(
                f"REMOVE|{registration}"
            )

            if response.startswith("OK|"):
                fee = record_exit(registration)

                if fee is None:
                    st.success(
                        "Vehicle removed. Is session ka history "
                        "record database mein nahi mila."
                    )
                else:
                    st.success(
                        f"Vehicle removed. Estimated parking fee: "
                        f"₹{fee:.2f}"
                    )

                st.rerun()
            else:
                st.error(response.replace("|", " "))


# ---------------- SEARCH VEHICLE ----------------

elif page == "Search Vehicle":
    st.subheader("Search by Registration Number")

    with st.form("search_form"):
        registration = st.text_input(
            "Registration Number"
        ).strip().upper()
        submitted = st.form_submit_button("Search")

    if submitted:
        response = send_to_java(f"FIND|{registration}")
        parts = response.split("|")

        if len(parts) == 5 and parts[0] == "FOUND":
            st.success("Vehicle found.")

            st.dataframe(
                pd.DataFrame([{
                    "Registration": parts[1],
                    "Color": parts[2],
                    "Type": parts[3],
                    "Slot": parts[4]
                }]),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning(response.replace("|", " "))


# ---------------- SEARCH BY COLOR ----------------

elif page == "Search by Color":
    st.subheader("Search Vehicles by Color")

    with st.form("color_form"):
        color = st.text_input("Enter Color").strip()
        submitted = st.form_submit_button("Search")

    if submitted:
        if not color:
            st.warning("Color enter karo.")
        elif "|" in color:
            st.warning("Color mein '|' character use nahi kar sakte.")
        else:
            response = send_to_java(f"COLOR|{color}")
            parts = response.split("|")

            if parts[0] == "COLOR":
                records = []
                data = parts[1:]

                for i in range(0, len(data), 4):
                    if i + 3 < len(data):
                        records.append({
                            "Registration": data[i],
                            "Color": data[i + 1],
                            "Type": data[i + 2],
                            "Slot": data[i + 3]
                        })

                if records:
                    st.dataframe(
                        pd.DataFrame(records),
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("Is color ka vehicle nahi mila.")
            else:
                st.info(response.replace("|", " "))


# ---------------- PARKING SLOTS ----------------

elif page == "Parking Slots":
    st.subheader("All Parking Slots")
    slots = get_slots()

    if slots:
        st.dataframe(
            pd.DataFrame(slots),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.error("Java server se slot data nahi mil raha.")


# ---------------- PARKING HISTORY ----------------

elif page == "Parking History":
    st.subheader("Parking History")

    records = db_query("""
        SELECT registration AS Registration,
               color AS Color,
               vehicle_type AS Type,
               slot AS Slot,
               entry_time AS Entry,
               exit_time AS Exit,
               fee AS Fee
        FROM parking_events
        ORDER BY id DESC
    """)

    if records:
        st.dataframe(
            pd.DataFrame(records),
            hide_index=True,
            use_container_width=True
        )

        csv_data = (
            pd.DataFrame(records)
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "Download History CSV",
            csv_data,
            file_name="goparking_history.csv",
            mime="text/csv"
        )
    else:
        st.info("Abhi parking history available nahi hai.")


# ---------------- FEE CALCULATOR ----------------

elif page == "Fee Calculator":
    st.subheader("Parking Fee Calculator")

    st.write(f"Car rate: ₹{CAR_RATE} per hour")
    st.write(f"Bike rate: ₹{BIKE_RATE} per hour")

    with st.form("fee_form"):
        vehicle_type = st.selectbox(
            "Vehicle Type", ["Car", "Bike"]
        )
        hours = st.number_input(
            "Parking Duration (hours)",
            min_value=1,
            max_value=720,
            value=1
        )
        submitted = st.form_submit_button("Calculate Fee")

    if submitted:
        rate = (
            BIKE_RATE if vehicle_type == "Bike"
            else CAR_RATE
        )
        fee = rate * hours
        st.metric("Estimated Parking Fee", f"₹{fee:.2f}")
        st.caption(
            "Actual fee on exit is calculated from "
            "recorded entry and exit times."
        )


# ---------------- PAYMENTS ----------------

elif page == "Payments":
    st.subheader("Parking Payments")

    payments = db_query("""
        SELECT registration AS Registration,
               amount AS Amount,
               paid_at AS PaidAt
        FROM payments
        ORDER BY id DESC
    """)

    if payments:
        st.dataframe(
            pd.DataFrame(payments),
            hide_index=True,
            use_container_width=True
        )

        total_collected = sum(
            float(p["Amount"]) for p in payments
        )
        st.metric(
            "Total Recorded Fees",
            f"₹{total_collected:.2f}"
        )
    else:
        st.info("Abhi koi fee record nahi hai.")


# ---------------- FOOTER ----------------

st.divider()
st.caption(
    "GoParking | Java DSA + Python Streamlit + SQLite"
)