# ================================
# CLOUD BACKUP & AUDIO SCRIPT
# (Run after Cameras.py)
# ================================

import os
import csv
from dotenv import load_dotenv
from pykada.cameras import CamerasClient

load_dotenv(override=True)

# Org B keys (post-migration)
api_key_b = os.getenv("VERKADA_API_KEY_B")

cam_b = CamerasClient(api_key_b)

CSV_CAMERA_FILE = "../CSVs/camera_data_backup.csv"

print("\n==============================")
print(" RESTORING CLOUD BACKUP + AUDIO INTO ORG B")
print("==============================\n")

# ---------------------------------------------------------
# BUILD SERIAL → NEW camera_id MAP FOR ORG B
# ---------------------------------------------------------
serial_map = {}

camera_data_b = cam_b.get_camera_data()

cameras_b = (
    camera_data_b.get("cameras_tests")
    or camera_data_b.get("cameras")
    or camera_data_b.get("devices")
    or camera_data_b.get("camera_list")
    or camera_data_b.get("cameras_list")
    or []
)

print(f"DEBUG: Raw camera_data_b keys = {list(camera_data_b.keys())}")
print(f"Found {len(cameras_b)} cameras in Org B.\n")

for c in cameras_b:
    serial = c.get("serial_number") or c.get("serial")
    cam_id = c.get("camera_id") or c.get("device_id")
    if serial and cam_id:
        serial_map[serial] = cam_id

print(f"Built serial map for {len(serial_map)} cameras in Org B.\n")

# ---------------------------------------------------------
# READ CSV & RESTORE SETTINGS
# ---------------------------------------------------------
with open(CSV_CAMERA_FILE, "r") as f:
    reader = csv.DictReader(f)

    for row in reader:

        serial = row["serial"]

        if serial not in serial_map:
            print(f"Skipping serial {serial} — not found in Org B")
            continue

        cam_id_b = serial_map[serial]

        print(f"\nRestoring settings for {serial} → Camera ID {cam_id_b}")

        # -----------------------------------------
        # CLOUD BACKUP RESTORE
        # -----------------------------------------
        try:
            cam_b.update_cloud_backup_settings(
                camera_id=cam_id_b,
                days_to_preserve=row["cloud_days_to_preserve"],
                enabled=int(row["cloud_enabled"]),
                time_to_preserve=row["cloud_time_to_preserve"],
                upload_timeslot=row["cloud_upload_timeslot"],
                video_quality=row["cloud_video_quality"],
                video_to_upload=row["cloud_video_to_upload"]
            )
            print("Cloud backup restored.")
        except Exception as e:
            print(f"Cloud backup restore FAILED: {e}")

        # -----------------------------------------
        # AUDIO RESTORE
        # -----------------------------------------
        try:
            audio_enabled = row["audio_enabled"].lower() == "true"
            cam_b.set_camera_audio_status(cam_id_b, audio_enabled)
            print(f"Audio restored → {audio_enabled}")
        except Exception as e:
            print(f"Audio restore FAILED: {e}")

print("\n=====================================")
print(" RESTORE SCRIPT COMPLETED SUCCESSFULLY")
print("=====================================\n")


