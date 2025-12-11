# ================================
# CAMERA MIGRATION SCRIPT
# ================================

import os
import csv
from pprint import pprint
from pathlib import Path
from dotenv import load_dotenv

from pykada.cameras import CamerasClient, get_camera_audio_status

load_dotenv(override=True)
api_key_a = os.getenv("VERKADA_API_KEY_A")
api_key_b = os.getenv("VERKADA_API_KEY_B")

cam_a = CamerasClient(api_key_a)
cam_b = CamerasClient(api_key_b)

Path("../CSVs").mkdir(exist_ok=True)
Path("../Documentation").mkdir(exist_ok=True)

# ============================================
# FAILURE TRACKERS + STATS
# ============================================

failures = {
    "poi_get": [],
    "camera_data": [],
    "cloud_backup_get": [],
    "audio_get": [],
    "lpoi_create": [],
}

stats = {
    "pois_total": 0,
    "pois_retrieved": 0,
    "lpois_total": 0,
    "lpois_created": 0,
    "cameras_total": 0,
}

# ============================================
# STEP 1 – GET + CREATE POIs
# ============================================

print("\n==============================")
print(" STEP 1: GET POIs")
print("==============================\n")

try:
    pois_a = list(cam_a.get_all_pois())
    stats["pois_retrieved"] = len(pois_a)
except Exception as e:
    pois_a = []
    failures["poi_get"].append(("ALL", str(e)))

POI_CSV = "../CSVs/pois_backup.csv"
try:
    pois_a = list(cam_a.get_all_pois())
    stats["pois_retrieved"] = len(pois_a)
except Exception as e:
    pois_a = []
    failures["poi_get"].append(("ALL", str(e)))

# -------- CSV EXPORT FOR POIs --------
with open(POI_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["poi_id", "label", "notes", "face_url"])

    for poi in pois_a:
        writer.writerow([
            poi.get("person_id"),
            poi.get("label"),
            poi.get("notes"),
        ])

# ============================================
# STEP 2 – GET CAMERA DATA + EXPORT CSV
# ============================================

print("\n=====================================")
print(" STEP 2: EXPORT CAMERA DATA")
print("=====================================\n")

try:
    data = cam_a.get_camera_data()
except Exception as e:
    data = {}
    failures["camera_data"].append(("ALL", str(e)))

cameras_list = (
    data.get("cameras_tests")
    or data.get("cameras")
    or data.get("devices")
    or data.get("camera_list")
    or []
)

stats["cameras_total"] = len(cameras_list)

CSV_OUT = "../CSVs/camera_data_backup.csv"

with open(CSV_OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "camera_id",
        "serial",
        "name",
        "model",

        "site",
        "site_id",

        "status",
        "timezone",

        "mac",
        "local_ip",
        "firmware",
        "firmware_update_schedule",

        "date_added",
        "last_online",

        "location",
        "location_lat",
        "location_lon",
        "location_angle",

        "people_history_enabled",
        "vehicle_history_enabled",

        "cloud_retention",
        "device_retention",

        "cloud_days_to_preserve",
        "cloud_enabled",
        "cloud_time_to_preserve",
        "cloud_upload_timeslot",
        "cloud_video_quality",
        "cloud_video_to_upload",

        "audio_enabled"
    ])

    for cam in cameras_list:
        cam_id = cam.get("camera_id") or cam.get("device_id")

        try:
            cloud = cam_a.get_cloud_backup_settings(cam_id)
        except Exception as e:
            cloud = {}
            failures["cloud_backup_get"].append((cam_id, str(e)))

        try:
            audio = cam_a.get_camera_audio_status(cam_id)
        except Exception as e:
            audio = {}
            failures["audio_get"].append((cam_id, str(e)))

        writer.writerow([
            cam_id,
            cam.get("serial"),
            cam.get("name"),
            cam.get("model"),

            cam.get("site"),
            cam.get("site_id"),

            cam.get("status"),
            cam.get("timezone"),

            cam.get("mac"),
            cam.get("local_ip"),
            cam.get("firmware"),
            cam.get("firmware_update_schedule"),

            cam.get("date_added"),
            cam.get("last_online"),

            cam.get("location"),
            cam.get("location_lat"),
            cam.get("location_lon"),
            cam.get("location_angle"),

            cam.get("people_history_enabled"),
            cam.get("vehicle_history_enabled"),

            cam.get("cloud_retention"),
            cam.get("device_retention"),

            cloud.get("days_to_preserve"),
            cloud.get("enabled"),
            cloud.get("time_to_preserve"),
            cloud.get("upload_timeslot"),
            cloud.get("video_quality"),
            cloud.get("video_to_upload"),

            audio.get("enabled"),
        ])

print(f"Camera CSV exported → {CSV_OUT}")

# ============================================
# STEP 3 – LPOIs
# ============================================

print("\n==============================")
print(" STEP 3: LPOIs")
print("==============================\n")

try:
    lp_full = cam_a.get_lpois()
    lpois = lp_full.get("license_plate_of_interest", [])
    stats["lpois_total"] = len(lpois)
except Exception as e:
    lpois = []
    failures["lpoi_create"].append(("ALL", str(e)))

LPOI_CSV = "../CSVs/lpois_backup.csv"

# -------- CSV EXPORT FOR LPOIs --------
with open(LPOI_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["plate", "description", "lpoi_id"])

    for lp in lpois:
        writer.writerow([
            lp.get("license_plate"),
            lp.get("description"),
        ])

print(f"LPOI CSV exported → {LPOI_CSV}")

for lp in lpois:
    plate = lp.get("license_plate")
    desc = lp.get("description")
    try:
        cam_b.create_lpoi(plate, desc)
        stats["lpois_created"] += 1
    except Exception:
        failures["lpoi_create"].append((plate, "Failed to create"))

# ============================================
# CAMERA MIGRATION MARKDOWN REPORT
# ============================================

report_path = "../Documentation/camera_migration_report.md"

with open(report_path, "w", encoding="utf-8") as f:

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------
    f.write("# Verkada Camera Migration Report\n")
    f.write("Generated automatically by the Org Migration Utility\n\n")
    f.write("---\n\n")

    # ------------------------------------------------------
    # INTRO
    # ------------------------------------------------------
    f.write("## Introduction\n\n")
    f.write(
        "This report summarizes all camera-related configurations exported from **Org A** using the Org Migration Utility.\n"
        "While camera configurations cannot be fully migrated via the Public API, this utility captures every API-accessible setting including:\n\n"
        "- People of Interest (saved in CSV)\n"
        "- License Plates of Interest (Migrated & saved in CSV)\n"
        "- Full individual camera configuration data for efficient migration:\n"
        "  - Cloud Backup settings (can migrate, see step 3)\n"
        "  - Audio enable/disable state (can migrate, see step 3)\n"
        "  - Camera metadata (model, serial, site, firmware, MAC, IP)\n"
        "  - People & Vehicle analytics toggle state\n"
        "  - Location (+ lat/lon)\n\n"
        "  - **Note:** all of this data is stored in: camera_data_backup.csv\n\n"

        "This report provides:\n"
        "- Everything exported automatically\n"
        "- What must be recreated manually\n"
        "- A **per-camera rebuild guide** populated directly from the CSV export\n"
        "- A complete workflow to restore full camera functionality in Org B\n\n"
    )
    f.write("---\n\n")

    # ------------------------------------------------------
    # WHAT MUST BE RECREATED MANUALLY
    # ------------------------------------------------------
    f.write("## What Must Be Recreated Manually\n\n")
    f.write("The Public API does **not** allow migration of:\n\n")
    f.write("- Camera claiming / decommissioning\n")
    f.write("- Motion zones\n")
    f.write("- Privacy regions\n")
    f.write("- Detection zones (people/vehicle analytics)\n")
    f.write("- Alerts\n")
    f.write("- Archive history\n")
    f.write("- Historical footage\n")
    f.write("- Incidents\n")
    f.write("---\n\n")

    # ============================================
    # MIGRATION SUMMARY
    # ============================================

    f.write("## Migration Summary\n\n")
    f.write("| Category | Success | Total |\n")
    f.write("|----------|--------:|------:|\n")

    # POIs
    f.write(f"| POIs Extracted | {stats['pois_retrieved']} | {stats['pois_retrieved']} |\n")
    # LPOIs
    f.write(f"| LPOIs Migrated | {stats['lpois_created']} | {stats['lpois_total']} |\n")
    # Cameras
    f.write(f"| Cameras Detected | {stats['cameras_total']} | {stats['cameras_total']} |\n")
    # Cloud Backup
    cloud_success = stats['cameras_total'] - len(failures['cloud_backup_get'])
    f.write(f"| Cloud Backup Settings Extracted | {cloud_success} | {stats['cameras_total']} |\n")
    # Audio Status
    audio_success = stats['cameras_total'] - len(failures['audio_get'])
    f.write(f"| Audio Settings Extracted | {audio_success} | {stats['cameras_total']} |\n")
    f.write("\n---\n\n")

    # ------------------------------------------------------
    # FAILURE SECTION
    # ------------------------------------------------------
    f.write("## Items Requiring Manual Review\n\n")
    wrote_any_failure = False
    for category, items in failures.items():
        if not items:
            continue
        wrote_any_failure = True
        f.write(f"### {category}\n")
        for item in items:
            f.write(f"- {item}\n")
        f.write("\n")

    if not wrote_any_failure:
        f.write("No errors detected.\n\n")

    f.write("---\n\n")

    # ------------------------------------------------------
    # CAMERA MIGRATION WORKFLOW
    # ------------------------------------------------------
    f.write("## Full Camera Migration Workflow\n\n")

    f.write("### Step 1: Capture All Required Camera Settings From Org A (Manually)\n\n")

    f.write(
        "Before recreating cameras in Org B, review and capture the following settings that "
        "cannot be exported via API but are essential for a full rebuild:\n\n"
    )

    f.write(
        "**Admin Settings**\n"
        "- Feature Manager: (If Applicable) Enable AI-powered Search, People Analytics, Vehicle Analytics, LPR\n"
        "- Camera Audio\n"
        "- Privacy Features\n"
        "- Data Privacy (as needed)\n"
        "- Etc.\n\n"
    )

    f.write(
        "**General Cameras Settings** (if not default in Org A)\n"
        "- Default History Playback Quality\n"
        "- Maximum Archive Duration\n"
        "- Default Live Face Blur Setting\n"
        "- Etc.\n\n"
    )

    f.write("**Additional considerations that customers may want migrated:**\n")
    f.write(
        "- Grid Layouts\n"
        "- Alerts\n\n"
    )

    f.write(
        "**Note:** For individual camera settings migration, the CSV generated by this script provides all API-exportable settings; "
        "use it as a reference when recreating cameras in Org B so you do not have to take screenshots (see Step 4).\n\n"
    )
    f.write("---\n\n")

    f.write("### Step 2: Decommission Devices from Org A & Commission into Org B\n\n")
    f.write("a\\) Download list of Org A's Cameras as CSV\n\n")
    f.write("b\\) Decommission controllers in Org A\n\n")
    f.write("c\\) Claim controllers into Org B by then importing the downloaded list\n\n")
    f.write("---\n\n")


    f.write("### Step 3: Run Cloud Backup & Audio Restore Script\n")
    f.write("Run this script after cameras are claimed in Org B:\n\n")
    f.write("```\nCloudBackup&Audio.py\n```\n\n")
    f.write("The script will:\n")
    f.write("- Restore cloud backup settings\n")
    f.write("- Restore audio settings\n")
    f.write("---\n\n")

    f.write("### Step 4: Manual Rebuild Items\n\n")

    # ------------------------------------------------------
    # CAMERA-BY-CAMERA SUMMARY
    # ------------------------------------------------------

    f.write("### Camera-by-Camera Configuration Summary\n")
    f.write(
        "Below is a complete breakdown for every camera found in Org A.\n"
        "These values come directly from the migration CSV and should be used to rebuild settings in Org B.\n\n"
    )

    f.write(
        "To simplify bulk-rebuilding settings in Org B, cameras are grouped into four sections based on their People and Vehicle analytics states. For most efficient migration, after importing all cameras via CSV, bulk edit their settings based on People/Vehicle Analytics (see grouping below). Then, if other settings are required, refer to camera_data_backup.csv for detailed information on a per-camera basis.\n\n"
        "1. **People = ENABLED, Vehicle = NOT ENABLED**\n"
        "2. **People = ENABLED, Vehicle = ENABLED**\n"
        "3. **People = NOT ENABLED, Vehicle = NOT ENABLED**\n"
        "4. **People = NOT ENABLED, Vehicle = ENABLED**\n\n"
    )


    def icon(val):
        return "ENABLED ✅" if val else "NOT ENABLED ❌"


    bucket_1 = []
    bucket_2 = []
    bucket_3 = []
    bucket_4 = []

    for cam in cameras_list:
        people = cam.get("people_history_enabled")
        vehicle = cam.get("vehicle_history_enabled")

        if people and not vehicle:
            bucket_1.append(cam)
        elif people and vehicle:
            bucket_2.append(cam)
        elif not people and not vehicle:
            bucket_3.append(cam)
        else:
            bucket_4.append(cam)

    ordered_buckets = [
        ("1. People ENABLED / Vehicle NOT ENABLED", bucket_1),
        ("2. People ENABLED / Vehicle ENABLED", bucket_2),
        ("3. People NOT ENABLED / Vehicle NOT ENABLED", bucket_3),
        ("4. People NOT ENABLED / Vehicle ENABLED", bucket_4),
    ]

    for title, bucket in ordered_buckets:
        f.write(f"### {title}\n\n")

        if not bucket:
            f.write("_No cameras in this category._\n\n")
            continue

        for cam in bucket:
            cam_id = cam.get("camera_id") or cam.get("device_id")
            serial = cam.get("serial") or cam.get("serial_number")
            model = cam.get("model")
            name = cam.get("name") or f"{model} · {serial}"

            people = cam.get("people_history_enabled")
            vehicle = cam.get("vehicle_history_enabled")

            f.write(f"#### **Camera: {name}**\n")
            f.write(f"- **Serial:** {serial}\n")
            f.write(f"- **Model:** {model}\n")
            f.write(f"- **People Analytics:** {icon(people)}\n")
            f.write(f"- **Vehicle Analytics:** {icon(vehicle)}\n")
            f.write("\n")

        f.write("---\n\n")

    # ------------------------------------------------------
    # POI-BY-POI SUMMARY
    # ------------------------------------------------------

    f.write("\n### People of Interest (POI) Summary\n")
    f.write(
        "Below is a complete list of all People of Interest pulled from Org A.\n"
        "These should be recreated in Org B as needed.\n\n"
    )

    if not pois_a:
        f.write("_No POIs found in Org A._\n\n")
    else:
        for poi in pois_a:
            label = poi.get("label", "Unknown")
            poi_id = poi.get("person_id") or poi.get("poi_id") or "(No ID Provided)"
            created_at = poi.get("created") or poi.get("created_at") or "Unknown"
            updated_at = poi.get("updated") or poi.get("updated_at") or "Unknown"
            img_url = poi.get("image_url") or "(Image unavailable)"

            f.write(f"#### **POI: {label}**\n")
            f.write(f"**POI ID:** `{poi_id}`,\n")
            f.write(f"**Created At:** {created_at}\n")

            f.write("---\n\n")


    f.write("**Note:** if needed, do not forget to manually recreate the settings acquired from Step 2!\n")

    f.write("### Step 5) Final Validation\n")
    f.write(
        "**Licensing:** Verify all cameras in Org B have valid licenses. Please reach out to licensing@verkada.com for additional support as needed.\n\n"
        "**Functional testing:** All settings match expected behavior.\n\n"
    )
    f.write("---\n\n")

    # ------------------------------------------------------
    # FINISH
    # ------------------------------------------------------
    f.write(
        "## Congratulations! Camera Migration Complete. Please run next script(s) as needed to complete full migration process.\n\n"
    )

print(f"\n✔ Camera Markdown report saved to: {report_path}\n")

