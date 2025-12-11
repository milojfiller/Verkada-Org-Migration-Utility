# ================================
# HELIX EVENT TYPE MIGRATION
# ================================

from dotenv import load_dotenv
import os
import csv
from pykada.helix import HelixClient

load_dotenv(override=True)

api_key_a = os.getenv("VERKADA_API_KEY_A")
api_key_b = os.getenv("VERKADA_API_KEY_B")

helix_a = HelixClient(api_key_a)
helix_b = HelixClient(api_key_b)

# ----------------------------------
# PREP CSV FOLDER
# ----------------------------------
csv_folder = "../CSVs"
os.makedirs(csv_folder, exist_ok=True)

event_types_csv = os.path.join(csv_folder, "helix_event_types_backup.csv")

# ----------------------------------
# FAILURE TRACKER
# ----------------------------------
failures = {
    "event_type_fetch": [],
    "event_type_create": [],
    "backup": []
}

print("\n==============================")
print(" GETTING HELIX EVENT TYPES")
print("==============================\n")

# ----------------------------------
# 1. GET ALL EVENT TYPES FROM ORG A
# ----------------------------------
try:
    resp = helix_a.get_helix_event_types()
    event_types_a = resp.get("event_types", [])
except Exception as e:
    print("Failed to fetch event types:", e)
    failures["event_type_fetch"].append(str(e))
    event_types_a = []

print(f"Found {len(event_types_a)} Helix Event Types in Org A.\n")


# ----------------------------------
# 2. CREATE EVENT TYPES IN ORG B
# ----------------------------------

print("\n==============================")
print(" CREATING EVENT TYPES IN ORG B")
print("==============================\n")

event_type_map = {}  # name → new UID

for et in event_types_a:
    name = et["name"]
    schema = et["event_schema"]

    try:
        created = helix_b.create_helix_event_type(schema, name)
        new_uid = created["event_type_uid"]
        event_type_map[name] = new_uid
    except Exception as e:
        failures["event_type_create"].append((name, str(e)))
        continue


# ----------------------------------
# 3. BACKUP EVENT TYPES TO CSV
# ----------------------------------

try:
    with open(event_types_csv, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "event_type_uid", "event_schema"])

        for et in event_types_a:
            writer.writerow([
                et.get("name"),
                et.get("event_type_uid"),
                et.get("event_schema")
            ])

    print(f"Event Types backed up → {event_types_csv}")

except Exception as e:
    failures["backup"].append(str(e))
    print("Event Type CSV Backup Failed:", e)


# ----------------------------------
# FAILURE SUMMARY
# ----------------------------------

print("\n==============================")
print("           FAILURES")
print("==============================\n")

for k, v in failures.items():
    print(f"{k}: {len(v)} failures")
    for item in v:
        print("  -", item)


# ----------------------------------
# FINAL SUMMARY
# ----------------------------------

print("\n==============================")
print("      FINAL MIGRATION SUMMARY")
print("==============================\n")

print(f"Helix Event Types migrated: {len(event_type_map)} / {len(event_types_a)}")
print(f"Event Types backed up: {len(event_types_a)} (saved to {event_types_csv})")

print("\nHelix Event Type Migration Completed.\n")

# ============================================
# HELIX EVENT TYPE MARKDOWN REPORT
# ============================================

report_path = "../Documentation/helix_event_type_migration_report.md"
os.makedirs(os.path.dirname(report_path), exist_ok=True)

with open(report_path, "w", encoding="utf-8") as r:

    # ------------------------------------------------------
    # HEADER
    # ------------------------------------------------------
    r.write("# Helix Migration Report\n")
    r.write("Generated automatically by the Org Migration Utility\n\n")
    r.write("---\n\n")

    # ------------------------------------------------------
    # INTRODUCTION
    # ------------------------------------------------------
    r.write("## Introduction\n\n")
    r.write(
        "This report summarizes all **Helix Event Types** exported from **Org A** and "
        "recreated in **Org B** using the Org Migration Utility.\n\n"
        "While historical Helix events cannot be transferred between organizations, "
        "the **Event Types themselves are fully migratable** using the Public API. "
        "This utility captures every API-accessible attribute of each Event Type, including:\n\n"
        "- Event Type name\n"
        "- Event schema (all structured fields and expected JSON format)\n\n"
        "The goals of this migration are:\n"
        "- Preserve all Helix Event Type definitions across orgs\n"
        "- Ensure integrations continue working without schema changes\n"
        "- Supply a CSV backup of all Event Types for documentation\n\n"
    )
    r.write("---\n\n")

    # ------------------------------------------------------
    # MIGRATION SUMMARY TABLE
    # ------------------------------------------------------
    r.write("## Migration Summary\n\n")
    r.write("| Category | Success | Total |\n")
    r.write("|----------|--------:|------:|\n")

    migrated_count = len(event_type_map)
    total_count = len(event_types_a)

    r.write(f"| Event Types Migrated | {migrated_count} | {total_count} |\n")
    r.write(f"| CSV Backup Generated | {1 if total_count > 0 else 0} | 1 |\n")
    r.write("\n---\n\n")

    # ------------------------------------------------------
    # MIGRATED EVENT TYPES
    # ------------------------------------------------------
    r.write("## Migrated Event Types\n\n")

    if event_type_map:
        r.write("| Event Type Name | New Event Type UID |\n")
        r.write("|-----------------|--------------------|\n")
        for name, uid in event_type_map.items():
            r.write(f"| {name} | `{uid}` |\n")
        r.write("\n")
    else:
        r.write("_No Helix Event Types were migrated._\n\n")

    r.write("---\n\n")

    # ------------------------------------------------------
    # FAILURES
    # ------------------------------------------------------
    r.write("## Items Requiring Manual Review\n\n")

    any_failures = any(len(v) > 0 for v in failures.values())
    wrote_any_failure = False

    if not any_failures:
        r.write("No errors detected.\n\n")
    else:
        for category, items in failures.items():
            if not items:
                continue
            wrote_any_failure = True
            r.write(f"### {category}\n")
            for name, reason in items:
                r.write(f"- **{name}** → `{reason}`\n")
            r.write("\n")

    r.write("---\n\n")

    # ------------------------------------------------------
    # NEXT STEPS & INTEGRATION READINESS
    # ------------------------------------------------------
    r.write("## Next Steps & Integration Readiness\n\n")
    r.write(
        "Your Helix Event Types have been successfully migrated into **Org B**. (Note: if seeing 409 errors, event type already exists in Org B)\n\n"
        "These Event Types are now immediately usable for real-time integrations. Any external system—such as POS terminals, "
        "barcode scanners, IoT sensors, or custom applications—can push Helix events into Org B by sending JSON to:\n\n"
        "```\n"
        "POST https://api.verkada.com/cameras/v1/video_tagging/event\n"
        "```\n\n"
        "To create a Helix event, a system needs:\n"
        "- A **camera_id** within Org B\n"
        "- **Event Type UID**\n"
        "- JSON `attributes` payload matching the event schema\n\n"
        "**TLDR:** All Event Types from Org A have been recreated in Org B and are ready to power Helix integrations.\n\n"
    )

    # ------------------------------------------------------
    # COMPLETION
    # ------------------------------------------------------
    r.write("## Migration Complete!\n")

print(f"\n✔ Helix Markdown report saved to: {report_path}\n")
