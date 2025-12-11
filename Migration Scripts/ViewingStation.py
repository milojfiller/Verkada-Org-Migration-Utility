# ================================
# VIEWING STATION BACKUP SCRIPT
# (No Report Generated)
# ================================

from dotenv import load_dotenv
import os
import csv

from pykada.api_tokens import VerkadaTokenManager
from pykada.verkada_requests import VerkadaRequestManager

load_dotenv(override=True)

api_key_a = os.getenv("VERKADA_API_KEY_A")

# ----------------------------------
# TOKEN + REQUEST MANAGER
# ----------------------------------

token_manager = VerkadaTokenManager(api_key=api_key_a)
request_manager = VerkadaRequestManager(token_manager=token_manager)

VIEWING_STATION_URL = "https://api.verkada.com/viewing_station/v1/devices"

# ----------------------------------
# FAILURE TRACKER
# ----------------------------------

failures = {
    "device_fetch": [],
    "csv": []
}

print("\n==============================")
print("     GETTING VIEWING STATIONS")
print("==============================\n")

# ----------------------------------
# 1. GET VIEWING STATIONS
# ----------------------------------

try:
    resp = request_manager.get(url=VIEWING_STATION_URL)
    devices_a = resp.get("devices", [])

except Exception as e:
    print("Failed to fetch viewing stations:", e)
    failures["device_fetch"].append(str(e))
    devices_a = []

print(devices_a)
print(f"\nFound {len(devices_a)} Viewing Stations in Org A.\n")

# ----------------------------------
# 2. WRITE CSV (to ../CSVs/)
# ----------------------------------

csv_folder = "../CSVs"
os.makedirs(csv_folder, exist_ok=True)

vx_csv = os.path.join(csv_folder, "viewing_stations_backup.csv")

try:
    with open(vx_csv, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "device_id",
            "name",
            "claimed_serial_number",
            "ip_address",
            "last_status",
            "last_seen_at",
            "site_id",
            "timezone",
            "app_version"
        ])

        for d in devices_a:
            writer.writerow([
                d.get("device_id", ""),
                d.get("name", ""),
                d.get("claimed_serial_number", ""),
                d.get("ip_address", ""),
                d.get("last_status", ""),
                d.get("last_seen_at", ""),
                d.get("site_id", ""),
                d.get("timezone", ""),
                d.get("app_version", "")
            ])

except Exception as e:
    failures["csv"].append(("viewing_stations_backup", str(e)))
    print("Failed to write viewing_stations_backup.csv:", e)


# ----------------------------------
# SUMMARY
# ----------------------------------

print("\n==============================")
print("  FINAL VIEWING STATION EXPORT")
print("==============================\n")

print(f"Viewing Stations exported: {len(devices_a)} (saved to {vx_csv})")
print("\nViewing Station Export Completed.\n")
