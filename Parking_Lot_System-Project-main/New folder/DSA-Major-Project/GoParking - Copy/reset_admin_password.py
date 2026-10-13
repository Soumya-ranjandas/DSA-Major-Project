import sqlite3
import getpass
from pathlib import Path
from auth_security import hash_password

DB_PATH = Path(__file__).resolve().parent / "goparking.db"


def main():
    print("\n=== GoParking Admin Password Reset ===\n")

    admin_email = input("Enter existing admin email: ").strip()

    new_password = getpass.getpass(
        "Enter new password (minimum 12 characters): "
    )
    confirm_password = getpass.getpass(
        "Confirm new password: "
    )

    if len(new_password) < 12:
        print("Error: Password must contain at least 12 characters.")
        return

    if new_password != confirm_password:
        print("Error: Passwords do not match.")
        return

    if not DB_PATH.is_file():
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            admin = conn.execute(
                """
                SELECT id, email
                FROM users
                WHERE email = ? COLLATE NOCASE
                  AND role = 'admin'
                """,
                (admin_email,)
            ).fetchone()

            if admin is None:
                print("Error: Existing admin account not found.")
                return

            conn.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    session_version = session_version + 1
                WHERE id = ?
                """,
                (hash_password(new_password), admin["id"])
            )

            print("\nAdmin password updated successfully.")
            print("Admin email:", admin["email"])
            print("Parking records have not been deleted.")

    except sqlite3.Error as error:
        print("Database error:", error)


if __name__ == "__main__":
    main()