# ================================
# ACCESS CONTROL MIGRATION SCRIPT
# ================================

from dotenv import load_dotenv
import os
import csv
import json
from pprint import pprint
from pathlib import Path

load_dotenv(override=True)

# Load API keys
api_key_a = os.getenv("VERKADA_API_KEY_A")
api_key_b = os.getenv("VERKADA_API_KEY_B")

# Clients
from pykada.core_command import CoreCommandClient
from pykada.access_control import AccessControlClient

core_client_a = CoreCommandClient(api_key_a)
core_client_b = CoreCommandClient(api_key_b)

access_client_a = AccessControlClient(api_key_a)
access_client_b = AccessControlClient(api_key_b)

Path("../CSVs").mkdir(exist_ok=True)
Path("../Documentation").mkdir(exist_ok=True)

# ============================================
# FAILURE TRACKERS
# ============================================

failures = {
    "user_create": [],
    "group_create": [],
    "group_assign": [],
    "ble_toggle": [],
    "remote_toggle": [],
    "start_date": [],
    "end_date": [],
    "entry_code": [],
    "card_add": [],
    "mfa_add": [],
    "license_plates": []
}

stats = {
    "users_total": 0,
    "users_created": 0,
    "groups_total": 0,
    "groups_created": 0,
    "group_assign_attempted": 0,
    "group_assign_success": 0,
    "ble_attempted": 0,
    "ble_success": 0,
    "remote_attempted": 0,
    "remote_success": 0,
    "start_attempted": 0,
    "start_success": 0,
    "end_attempted": 0,
    "end_success": 0,
    "entry_attempted": 0,
    "entry_success": 0,
    "cards_attempted": 0,
    "cards_success": 0,
    "mfa_attempted": 0,
    "mfa_success": 0,
    "plates_attempted": 0,
    "plates_success": 0,
}

# ============================================
# STEP 1 — MIGRATE USERS
# ============================================

all_users_a = access_client_a.get_all_access_users()["access_members"]
stats["users_total"] = len(all_users_a)

# user_id → full_name
user_lookup = {}

for user in all_users_a:
    uid = user["user_id"]
    full_name = user["full_name"]
    email = user.get("email", "")
    user_lookup[uid] = full_name

    core_user = core_client_a.get_user(uid)

    first, *rest = full_name.split(" ")
    last = rest[0] if rest else ""

    try:
        core_client_b.create_user(
            external_id=uid,
            company_name=user.get("company_name"),
            department=user.get("department"),
            department_id=user.get("department_id"),
            email=email,
            employee_title=user.get("employee_title"),
            first_name=first,
            last_name=last,
            phone=core_user.get("phone")
        )
        stats["users_created"] += 1
    except Exception as e:
        failures["user_create"].append({
            "user_id": uid,
            "name": full_name,
            "email": email,
            "reason": str(e)
        })

# ============================================
# STEP 2 — MIGRATE ACCESS GROUPS
# ============================================

groups_a = access_client_a.get_access_groups()["access_groups"]

stats["groups_total"] = len(groups_a)

group_name_lookup = {g["group_id"]: g["name"] for g in groups_a}

group_name_to_b_id = {}

for g in groups_a:
    name = g["name"]
    try:
        created = access_client_b.create_access_group(name=name)
        group_name_to_b_id[name] = created["group_id"]
        stats["groups_created"] += 1
    except Exception as e:
        failures["group_create"].append({"group_name": name, "reason": str(e)})

# ============================================
# STEP 3 — USER ACCESS ATTRIBUTES
# ============================================

for u in all_users_a:
    uid = u["user_id"]
    full = access_client_a.get_access_user(user_id=uid)
    full_name = user_lookup.get(uid, "(unknown user)")

    # BLE
    if full.get("ble_unlock"):
        stats["ble_attempted"] += 1
        try:
            access_client_b.activate_ble_for_access_user(external_id=uid)
            stats["ble_success"] += 1
        except Exception as e:
            failures["ble_toggle"].append({"user": full_name, "reason": str(e)})

    # Remote Unlock
    if full.get("remote_unlock"):
        stats["remote_attempted"] += 1
        try:
            access_client_b.activate_remote_unlock_for_user(external_id=uid)
            stats["remote_success"] += 1
        except Exception as e:
            failures["remote_toggle"].append({"user": full_name, "reason": str(e)})

    # Start/End Dates
    if full.get("start_date"):
        stats["start_attempted"] += 1
        try:
            access_client_b.set_start_date_for_user(
                external_id=uid,
                start_date=full["start_date"]
            )
            stats["start_success"] += 1
        except Exception as e:
            failures["start_date"].append({"user": full_name, "reason": str(e)})

    if full.get("end_date"):
        stats["end_attempted"] += 1
        try:
            access_client_b.set_end_date_for_user(
                external_id=uid,
                end_date=full["end_date"]
            )
            stats["end_success"] += 1
        except Exception as e:
            failures["end_date"].append({"user": full_name, "reason": str(e)})

    # Entry Code
    if full.get("entry_code"):
        stats["entry_attempted"] += 1
        try:
            access_client_b.set_entry_code_for_user(
                external_id=uid,
                entry_code=full["entry_code"]
            )
            stats["entry_success"] += 1
        except Exception as e:
            failures["entry_code"].append({"user": full_name, "reason": str(e)})

    # Group Assignments
    for g in full.get("access_groups", []):
        stats["group_assign_attempted"] += 1

        gname = g["name"]
        gid_b = group_name_to_b_id.get(gname)

        if not gid_b:
            failures["group_assign"].append({"user": full_name, "group": gname, "reason": "Missing in Org B"})
            continue

        try:
            access_client_b.add_user_to_access_group(external_id=uid, group_id=gid_b)
            stats["group_assign_success"] += 1
        except Exception as e:
            failures["group_assign"].append({"user": full_name, "group": gname, "reason": str(e)})

    # Keycards
    for card in full.get("cards", []):
        stats["cards_attempted"] += 1
        card_summary = f"{card.get('type')} — {card.get('card_number') or card.get('card_number_hex') or card.get('card_number_base36')}"

        try:
            kwargs = {}
            if card.get("card_number"):
                kwargs["card_number"] = card["card_number"]
            elif card.get("card_number_hex"):
                kwargs["card_number_hex"] = card["card_number_hex"]
            elif card.get("card_number_base36"):
                kwargs["card_number_base36"] = card["card_number_base36"]

            access_client_b.add_card_to_user(
                external_id=uid,
                active=card.get("active", False),
                facility_code=card.get("facility_code", ""),
                card_type=card.get("type", ""),
                **kwargs
            )
            stats["cards_success"] += 1
        except Exception as e:
            failures["card_add"].append({"user": full_name, "card": card_summary, "reason": str(e)})

    # MFA
    for m in full.get("mfa_codes", []):
        stats["mfa_attempted"] += 1
        code = m.get("code", "unknown")

        try:
            access_client_b.add_mfa_code_to_user(code=code, external_id=uid)
            stats["mfa_success"] += 1
        except Exception as e:
            failures["mfa_add"].append({"user": full_name, "code": code, "reason": str(e)})

    # License Plates
    for lp in full.get("license_plates", []):
        stats["plates_attempted"] += 1
        plate_summary = f"{lp.get('license_plate_number')} ({lp.get('name', '')})"

        try:
            access_client_b.add_license_plate_to_user(
                external_id=uid,
                license_plate_number=lp.get("license_plate_number"),
                name=lp.get("name", None),
                active=lp.get("active", False)
            )
            stats["plates_success"] += 1
        except Exception as e:
            failures["license_plates"].append({
                "user": full_name,
                "plate": plate_summary,
                "reason": str(e)
            })

# ============================================
# STEP 4 — EXPORT DOORS TO CSV
# ============================================

doors_a = access_client_a.get_doors().get("doors", [])

with open("../CSVs/doors_backup.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    # Updated header row
    writer.writerow([
        "door_id",
        "door_name",
        "site_id",
        "site_name",
        "controller_id",
        "controller_name"
    ])

    for d in doors_a:
        site = d.get("site", {}) or {}

        writer.writerow([
            d.get("door_id", ""),
            d.get("name", ""),
            site.get("site_id", ""),
            site.get("name", ""),
            d.get("acu_id", ""),
            d.get("acu_name", "")
        ])

door_lookup = {d.get("door_id"): d.get("name") for d in doors_a}

site_lookup = {}
for d in doors_a:
    site = d.get("site", {}) or {}
    sid = site.get("site_id")
    sname = site.get("name")
    if sid:
        site_lookup[sid] = sname

controller_lookup = {
    d.get("door_id"): d.get("acu_name") for d in doors_a
}

# ============================================
# STEP 5 — EXPORT ACCESS LEVELS to CSV
# ============================================

levels_response = access_client_a.get_all_access_levels()
levels_a = levels_response.get("access_levels", [])

with open("../CSVs/access_levels_backup.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "access_level_id",
        "name",
        "door_ids",
        "door_names",
        "site_ids",
        "site_names",
        "schedule"
    ])

    for lvl in levels_a:

        door_ids = lvl.get("doors", [])
        if isinstance(door_ids, str):
            door_ids = [door_ids]
        door_names = [door_lookup.get(d, "(Unknown Door)") for d in door_ids]

        site_ids = lvl.get("sites", [])
        if isinstance(site_ids, str):
            site_ids = [site_ids]
        site_names = [site_lookup.get(s, "(Unknown Site)") for s in site_ids]

        schedule = json.dumps(lvl.get("access_schedule_events", []))

        writer.writerow([
            lvl.get("access_level_id"),
            lvl.get("name"),
            ";".join(door_ids),
            ";".join(door_names),
            ";".join(site_ids),
            ";".join(site_names),
            schedule
        ])

# ============================================
# STEP 6 — EXPORT DOOR EXCEPTION CALENDARS TO CSV
# ============================================

exception_response = access_client_a.get_all_door_exception_calendars()
exception_cals = exception_response.get("door_exception_calendars", [])
exception_cal_count = len(exception_cals)

with open("../CSVs/door_exception_calendars_backup.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "calendar_id",
        "calendar_name",
        "door_ids",
        "door_names",
        "exception_count",
        "exceptions_readable"
    ])

    for cal in exception_cals:
        doors = cal.get("doors", [])
        door_names = [door_lookup.get(d, "(Unknown Door)") for d in doors]

        readable_exceptions = []
        for ex in cal.get("exceptions", []):
            readable = f"{ex.get('date')} {ex.get('door_status')} {ex.get('start_time')}-{ex.get('end_time')}"
            readable_exceptions.append(readable)

        writer.writerow([
            cal.get("door_exception_calendar_id"),
            cal.get("name"),
            ";".join(doors),
            ";".join(door_names),
            len(cal.get("exceptions", [])),
            "; ".join(readable_exceptions)
        ])

# ============================================
# STEP 7 — GENERATE FULL MARKDOWN REPORT
# ============================================

report_path = "../Documentation/access_control_migration_report.md"

with open(report_path, "w", encoding="utf-8") as f:
    # ===========================================================
    # HEADER
    # ===========================================================
    f.write("# Verkada Access Control Migration Report\n")
    f.write("Generated automatically by the Org Migration Utility\n\n")
    f.write("---\n\n")

    # ===========================================================
    # INTRODUCTION
    # ===========================================================
    f.write("## Introduction\n\n")
    f.write(
        "This report summarizes all data exported and migrated from **Org A** into "
        "**Org B** using the Verkada Access Control Migration Utility. "
        "All API-supported attributes are migrated automatically; remaining components "
        "must be manually recreated in Org B using the structured data and instructions included in this report.\n\n"
    )

    f.write(
        "This report provides:\n"
        "- A summary of what was migrated automatically\n"
        "- A list of items requiring manual recreation\n"
        "- A complete workflow for finishing the Access migration\n"
    )
    f.write("---\n\n")

    # ===========================================================
    # MIGRATED AUTOMATICALLY
    # ===========================================================
    f.write("## What Was Migrated Automatically\n\n")
    f.write(
        "The migration utility recreated all API-supported Access Control data "
        "in **Org B**. The following attributes were migrated:\n\n"
        "- Access Groups\n"
        "- Users (first name, last name, email, department, title, phone, etc.)\n"
        "- Group membership\n"
        "- BLE unlock state\n"
        "- Remote unlock state\n"
        "- Start and end dates\n"
        "- Entry codes\n"
        "- Keycards\n"
        "- License plates\n"
        "- MFA codes\n\n"
    )

    f.write(
        "**SCIM Note:** If the customer uses SCIM, identities continue being sourced "
        "from the identity provider. Migrated credentials and user information will "
        "automatically attach to SCIM-provisioned users.\n\n"
    )
    f.write("---\n\n")

    # ===========================================================
    # ITEMS REQUIRING MANUAL REBUILD
    # ===========================================================
    f.write("## What Must Be Rebuilt Manually\n\n")
    f.write(
        "The Public API does **not** support creating the following Access components:\n\n"
        "- **Access Levels** — names, doors, sites, schedules\n"
        "- **Door Exception Calendars** — holiday/special schedules\n"
        "- **Doors** — controller assignment, port, lock type, inputs, etc.\n"
        "- **Controller hardware configuration**\n"
        "- **Door schedules, lockdown scenarios, AUX behaviors, etc.\n\n"
    )
    f.write("---\n\n")

    # ===========================================================
    # MIGRATION SUMMARY TABLE
    # ===========================================================
    f.write("## Migration Summary\n\n")
    f.write("| Category | Success | Total |\n")
    f.write("|----------|--------:|------:|\n")
    f.write(f"| Users | {stats['users_created']} | {stats['users_total']} |\n")
    f.write(f"| Access Groups | {stats['groups_created']} | {stats['groups_total']} |\n")
    f.write(f"| Group Assignments | {stats['group_assign_success']} | {stats['group_assign_attempted']} |\n")
    f.write(f"| BLE Unlock | {stats['ble_success']} | {stats['ble_attempted']} |\n")
    f.write(f"| Remote Unlock | {stats['remote_success']} | {stats['remote_attempted']} |\n")
    f.write(f"| Start Dates | {stats['start_success']} | {stats['start_attempted']} |\n")
    f.write(f"| End Dates | {stats['end_success']} | {stats['end_attempted']} |\n")
    f.write(f"| Entry Codes | {stats['entry_success']} | {stats['entry_attempted']} |\n")
    f.write(f"| Keycards | {stats['cards_success']} | {stats['cards_attempted']} |\n")
    f.write(f"| MFA Codes | {stats['mfa_success']} | {stats['mfa_attempted']} |\n")
    f.write(f"| License Plates | {stats['plates_success']} | {stats['plates_attempted']} |\n")
    f.write("\n---\n")

    # ===========================================================
    # FAILURE SECTION
    # ===========================================================
    f.write("## Items Requiring Manual Review\n\n")
    f.write("The following items failed migration and must be validated in Org B:\n\n")
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

    # ===========================================================
    # FULL ACCESS CONTROL MIGRATION WORKFLOW
    # ===========================================================
    f.write("## Full Access Control Migration Workflow\n\n")
    f.write(
        "This workflow describes how to rebuild a complete Access Control system in Org B using the data exported "
        "from Org A. Automated API migration is already complete; the steps below guide manual reconstruction. Please see **Migration** "
        "**Summary** and **Items Requiring Manual Review** above to ensure that full API migration is completed before moving on! \n\n"
    )

    # ---------------------------- CSV Exports
    f.write("### Step 1: Note What The CSV Exports Provide\n\n")
    f.write("The utility generates three CSV files that replace manual screenshotting from Org A:\n\n")

    f.write("**doors_backup.csv**\n")
    f.write("- Door ID\n- Door name\n- Site ID\n- Site name\n- Controller ID\n- Controller name\n\n")

    f.write("**access_levels_backup.csv**\n")
    f.write("- Access level name\n- All associated doors (IDs + names)\n")
    f.write("- All associated sites\n- Full schedule blocks\n\n")

    f.write("**door_exception_calendars_backup.csv**\n")
    f.write("- Calendar name\n- Door assignments\n- Exception dates\n\n")
    f.write("---\n\n")

    # ---------------------------- Controllers
    f.write("### Step 2: Controller Migration and Hardware Configuration\n\n")
    f.write("#### Gather Controller & Door Hardware Configurations (manually):\n\n")
    f.write(
        "For Controllers, make sure to fully capture:\n- Specific Port(s) Tied to Each Door\n- AUX Input/Output Settings & Actions \n- Location\n- Connected Card Readers & Associated Ports\n\n"
        "For Doors, make sure to fully capture: \n- Paired Cameras\n- DPI Settings \n- DHO Settings\n- REX Settings\n- Installer Settings\n- Verkada Pass Settings\n\n"
        "Additionally if the customer would like, make sure to fully capture: \n- Door Schedules\n- Access Exceptions \n- Roll Call Templates\n- General Access Settings\n\n"
        "!! For best practice and to avoid any manual screenshots, please use the following spreadsheet for organized, efficient tracking: https://docs.google.com/spreadsheets/d/1KemJ9zjU4fcy64WNLZOOrL78p7EqEoohtbzkjZ5-ST4/edit?usp=sharing.\n\n"
    )
    # ---------------------------- Dummy Controller Best Practice
    f.write("#### ☆ Another Migration Option: Use Dummy Serial Numbers Before Migrating Real Hardware\n\n")
    f.write(
        "To ensure a smooth, low-risk migration, it is recommended to **use temporary "
        "dummy serial numbers** in Org B *before moving any real serial numbers* from Org A. This "
        "allows all doors to be fully built and configured in Org B without touching hardware.\n\n"
    )

    f.write("#### Workflow Using Dummy Serial Numbers\n")
    f.write(
        "1. Create one or more **dummy Access Controllers** in Org B using placeholder serial numbers. Please see: https://docs.google.com/spreadsheets/d/1-kfPNNbBR8JfiS1uFSsh3GNwqQwsVFlCd3LTENjT_BA/edit?usp=sharing\n"
        "2. Using `doors_backup.csv`, recreate every door and assign it to the dummy controller:\n"
        "   - Assign door → site\n"
        "   - Assign door → dummy controller & correct port\n"
        "   - Re-enter all installer and hardware settings captured in Step 2\n"
        "3. When ready for full hardware migration, **claim the real Access Controllers** from Org A into Org B:\n"
        "   - Download list of Org A's Access Devices as CSV\n"
        "   - Decommission controllers in Org A\n"
        "   - Claim controllers into Org B by then importing the downloaded list\n"
        "4. In Org B, **migrate each door—and all of its settings—from the dummy controller to the real ACU**\n"
        "5. Delete dummy controllers once all doors are mapped to real hardware\n\n"
    )
    f.write(
        "This workflow ensures all doors can be fully created and configured in Org B **before any real "
        "serial numbers leave Org A**. When the real controllers are claimed, the migration becomes a simple, "
        "controlled reassignment from dummy controller → real ACU.\n\n"
        "**!! NOTE:** if you do not want to use dummy serial numbers, skip to step 3.\n\n"
    )


    # ---------------------------- Prepare Org B
    f.write("### Step 3: Prepare Org B's Environment\n\n")
    f.write(
        "**Sites**: Create all sites matching Org A.\n\n"
        "**Buildings & Floors**: Recreate buildings & floors.\n\n"

        "If you did not use dummy serial numbers and have not yet, use `doors_backup.csv`to recreate every door after commissioning Org A's hardware into Org B:\n"
        "- Assign door to site\n"
        "- Select correct controller & port\n"
        "- Re-enter all hardware & installer settings that were captured in Step 2\n"
        "- Match names correctly\n\n"
    )
    f.write(
        "**Important:** Doors should exist before Access Levels are recreated for efficient migration.\n\n"
    )
    f.write("---\n\n")

    # ---------------------------- Access Levels
    f.write("### Step 4: Rebuild Access Levels in Org B\n\n")
    f.write(
        "Access Levels cannot be created or modified via the Public API and must be manually recreated.\n"
        "For each Access Level:\n"
        "- Create Access Level with same name\n"
        "- Add all associated doors\n"
        "- Add associated sites\n"
        "- Rebuild each schedule block\n"
        "- Assign Access Level to the correct Access Groups\n\n"
    )
    f.write("Full details for each Access Level are included below, so no screenshots are required. Please follow the below list as you manually recreate:\n\n")
    f.write("---\n\n")

    # ===========================================================
    # ACCESS LEVEL DETAIL OUTPUT
    # ===========================================================
    for lvl in levels_a:
        name = lvl.get("name")
        lvl_id = lvl.get("access_level_id")

        doors = lvl.get("doors", [])
        if isinstance(doors, str):
            doors = [doors]

        sites = lvl.get("sites", [])
        if isinstance(sites, str):
            sites = [sites]

        schedules = lvl.get("access_schedule_events", [])

        f.write(f"### **Access Level Name:** {name}\n")

        f.write("### **Doors:**\n")
        if doors:
            for d in doors:
                f.write(f"- {door_lookup.get(d, '(Unknown Door)')} (`{d}`)\n")
        else:
            f.write("- None\n")

        f.write("\n### **Schedule Blocks:**\n")

        normalized = [
            (
                ev.get("weekday"),
                ev.get("start_time"),
                ev.get("end_time"),
                ev.get("door_status")
            )
            for ev in schedules
        ]

        # Check for 24/7 access across all 7 days
        ALL_DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

        is_247 = (
                len(normalized) == 7 and
                all(
                    (day, "00:00", "23:59", "access_granted") in normalized
                    for day in ALL_DAYS
                )
        )

        if is_247:
            f.write("- Access granted **24/7**\n")
        else:
            if schedules:
                for ev in schedules:
                    f.write(
                        f"- {ev.get('weekday')} {ev.get('start_time')} → {ev.get('end_time')} "
                        f"({ev.get('door_status')})\n"
                    )
            else:
                f.write("- No schedule (likely 24/7)\n")

        f.write("\n---\n\n")

    # ---------------------------- Exception Calendars
    f.write("### Step 5: Recreate Door Exception Calendars\n\n")
    f.write(
        f"There are **{exception_cal_count} Door Exception Calendar(s)** in Org A.\n"
        "These must be manually recreated in Org B.\n\n"
    )
    f.write(
        "Use `door_exception_calendars_backup.csv` to restore these calendars.\n\n"
    )
    f.write("---\n\n")

    # ---------------------------- Additional Logic
    f.write("### Step 6: Restore Additional Access Logic (If Required)\n\n")
    f.write(
        "Depending on the customer’s configuration & expectations for migration, manually restore:\n"
        "- Door Schedules\n"
        "- Lockdown Scenarios\n"
        "- Access Exceptions\n"
        "- Roll Call Templates\n"
        "- General Access Settings\n"
    )
    f.write("---\n\n")

    # ---------------------------- Final Validation
    f.write("### Step 7: Final Validation\n\n")
    f.write(
        "**Licensing:** Verify all doors in Org B have valid Access licenses. Please reach out to licensing@verkada.com for additional support as needed.\n\n"
        "**Functional testing:** Access → Live Feed matches expected behavior\n\n"
    )
    f.write("---\n\n")

    f.write(
        "## Congratulations! Access Control Migration Complete. Please run next script(s) as needed to complete full migration process.\n\n")

# END REPORT
print(f"\n✔ Migration completed. Markdown report saved to: {report_path}\n")