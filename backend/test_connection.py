
import os
from pathlib import Path

from dotenv import load_dotenv
from hdbcli import dbapi

# Load the .env file beside this script
env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(env_file, override=True)

# Check required settings
required = [
    "HANA_ADDRESS",
    "HANA_PORT",
    "HANA_USER",
    "HANA_PASSWORD",
]

missing = [key for key in required if not os.getenv(key)]

if missing:
    raise SystemExit(f"Missing settings in .env: {', '.join(missing)}")

address = os.environ["HANA_ADDRESS"].strip()
port = int(os.environ["HANA_PORT"])
user = os.environ["HANA_USER"].strip()
password = os.environ["HANA_PASSWORD"]

# Show configuration without revealing the password
print("Environment file:", env_file)
print("Hostname:", address)
print("Port:", port)
print("Username:", user)
print("Password loaded:", bool(password))
print("\nConnecting to SAP HANA...")

connection = None
cursor = None

try:
    # Start with the basic connection parameters
    connection = dbapi.connect(
        address=address,
        port=port,
        user=user,
        password=password,
        encrypt=True,
        sslValidateCertificate=True,
        connectTimeout=30000,
    )

    print("SUCCESS: Connected to SAP HANA!")

    cursor = connection.cursor()
    cursor.execute("SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY")
    result = cursor.fetchone()

    print("Database user:", result[0])
    print("Current schema:", result[1])

except Exception as exc:
    print("CONNECTION FAILED")
    print("Error type:", type(exc).__name__)
    print("Error details:", str(exc)[:500])

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None:
        connection.close()

    print("\nTest finished.")
