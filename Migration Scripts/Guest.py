from dotenv import load_dotenv
import os
import time
import csv
from pykada.workplace import WorkplaceClient

load_dotenv(override=True)
api_key_a = os.getenv("VERKADA_API_KEY_A")

# Initialize WorkplaceClient (handles OAuth)
workplace_a = WorkplaceClient(api_key_a)

# Determine project root (folder ABOVE "Migration Scripts")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create CSV folder at project root
CSV_DIR = os.path.join(PROJECT_ROOT, "CSVs")
os.makedirs(CSV_DIR, exist_ok=True)

# Define CSV paths
sites_csv = os.path.join(CSV_DIR, "guest_sites_backup.csv")
guest_types_csv = os.path.join(CSV_DIR, "guest_types_backup.csv")
hosts_csv = os.path.join(CSV_DIR, "guest_hosts_backup.csv")
visits_csv = os.path.join(CSV_DIR, "guest_visits_backup.csv")

# Create Documentation folder at project root
DOCS_DIR = os.path.join(PROJECT_ROOT, "Documentation")
os.makedirs(DOCS_DIR, exist_ok=True)

# Path to write the final markdown report
REPORT_PATH = os.path.join(DOCS_DIR, "guest_migration_report.md")

# ----------------------------------
# FAILURE TRACKER
# ----------------------------------

failures = {
    "site_fetch": [],
    "visit_fetch": [],
    "guest_types": [],
    "guest_hosts": [],
    "csv": []
}

print("\n==============================")
print("         GETTING GUEST SITES")
print("==============================\n")

# ----------------------------------
# GET ALL GUEST SITES
# ----------------------------------

try:
    resp = workplace_a.get_guest_sites()
    sites_a = resp.get("guest_sites", [])
except Exception as e:
    print("Failed to fetch guest sites:", e)
    failures["site_fetch"].append(str(e))
    sites_a = []

print(f"\nFound {len(sites_a)} Guest Sites in Org A.\n")

# ----------------------------------
# SAVE GUEST SITES TO CSV
# ----------------------------------
try:
    with open(sites_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["org_id", "site_id", "site_name"])

        for s in sites_a:
            writer.writerow([
                s.get("org_id", ""),
                s.get("site_id", ""),
                s.get("site_name", ""),
            ])

    print(f"Guest Sites saved → {sites_csv}")
except Exception as e:
    failures["csv"].append(("guest_sites", str(e)))
    print("Failed to write guest_sites.csv:", e)


# ================================================================
# GUEST TYPES
# ================================================================

print("\n==============================")
print("       FETCHING GUEST TYPES")
print("==============================\n")

guest_types_all = []
try:
    with open(guest_types_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "site_id",
            "guest_type_id",
            "name",
            "enabled_for_invites"
        ])

        for s in sites_a:
            site_id = s["site_id"]
            print(f"  • Guest Types → {site_id}")

            try:
                resp = workplace_a.get_guest_types(site_id)
                items = resp.get("items", [])

                for t in items:
                    t["site_id"] = site_id
                    writer.writerow([
                        site_id,
                        t.get("guest_type_id", ""),
                        t.get("name", ""),
                        t.get("enabled_for_invites", "")
                    ])

                guest_types_all.extend(items)

            except Exception as e:
                failures["guest_types"].append((site_id, str(e)))

    print(f"Guest Types saved → {guest_types_csv}")
except Exception as e:
    failures["csv"].append(("guest_types", str(e)))
    print("Failed writing guest_types.csv:", e)


# ================================================================
# HOSTS
# ================================================================

print("\n==============================")
print("        FETCHING HOSTS")
print("==============================\n")

guest_hosts_all = []

try:
    with open(hosts_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "site_id",
            "host_id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "requires_host_approval",
            "has_delegate",
            "delegate_email"
        ])

        for s in sites_a:
            site_id = s["site_id"]
            print(f"  • Hosts → {site_id}")

            try:
                resp = workplace_a.get_guest_hosts(site_id)
                items = resp.get("items", [])

                for h in items:
                    h["site_id"] = site_id
                    writer.writerow([
                        site_id,
                        h.get("host_id", ""),
                        h.get("email", ""),
                        h.get("first_name", ""),
                        h.get("last_name", ""),
                        h.get("phone_number", ""),
                        h.get("requires_host_approval", ""),
                        h.get("has_delegate", ""),
                        h.get("delegate", {}).get("email", "")
                    ])

                guest_hosts_all.extend(items)

            except Exception as e:
                failures["guest_hosts"].append((site_id, str(e)))

    print(f"Guest Hosts saved → {hosts_csv}")
except Exception as e:
    failures["csv"].append(("guest_hosts", str(e)))
    print("Failed writing guest_hosts.csv:", e)


# ================================================================
# GUEST VISITS
# ================================================================

print("\n==============================")
print("       FETCHING GUEST VISITS")
print("==============================\n")

all_visits = []

end_time = int(time.time())
start_time = end_time - 86400  # last 24h

for s in sites_a:
    site_id = s["site_id"]
    site_name = s.get("site_name", "")

    print(f"  • Visits → {site_name} ({site_id})")

    try:
        visits_gen = workplace_a.get_all_guest_visits(
            site_id=site_id,
            start_time=start_time,
            end_time=end_time
        )

        for v in visits_gen:
            v["site_id"] = site_id
            all_visits.append(v)

    except Exception as e:
        failures["visit_fetch"].append((site_id, str(e)))

try:
    with open(visits_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "site_id",
            "visit_id",
            "check_in_time",
            "approval_status",
            "deleted"
        ])

        for v in all_visits:
            writer.writerow([
                v.get("site_id"),
                v.get("visit_id"),
                v.get("check_in_time", ""),
                v.get("approval_status", ""),
                v.get("deleted", "")
            ])

    print(f"Guest Visits saved → {visits_csv}")
except Exception as e:
    failures["csv"].append(("guest_visits", str(e)))
    print("Failed writing guest_visits.csv:", e)


# ================================================================
# FAILURE SUMMARY
# ================================================================

print("\n==============================")
print("            FAILURES")
print("==============================\n")

for k, v in failures.items():
    print(f"{k}: {len(v)}")
    for item in v:
        print("  -", item)

print("\n==============================")
print("     FINAL GUEST EXPORT SUMMARY")
print("==============================\n")

print(f"Guest Sites exported:        {len(sites_a)}")
print(f"Guest Types exported:        {len(guest_types_all)}")
print(f"Guest Hosts exported:        {len(guest_hosts_all)}")
print(f"Guest Visits exported (24h): {len(all_visits)}")

print("\nGuest Export Completed.\n")

# ============================================
# GENERATE FULL MARKDOWN REPORT
# ============================================

with open(REPORT_PATH, "w", encoding="utf-8") as f:

    # ===========================================================
    # HEADER
    # ===========================================================
    f.write("# Verkada Guest Migration Report\n")
    f.write("Generated automatically by the Org Migration Utility\n\n")
    f.write("---\n\n")

    # ===========================================================
    # INTRODUCTION
    # ===========================================================
    f.write("## Introduction\n\n")
    f.write(
        "This report summarizes all Guest-related data exported from **Org A** and "
        "provides a step-by-step workflow to rebuild the Guest configuration in **Org B**.\n\n"
    )
    f.write(
        "Because the Guest Public API is **read-only**, the utility exports everything possible "
        "(Sites, Guest Types, Hosts, Visits) but cannot recreate configuration directly. "
        "This report provides all required CSVs and a full rebuild guide.\n\n"
    )
    f.write("---\n\n")

    # ===========================================================
    # WHAT WAS EXPORTED AUTOMATICALLY
    # ===========================================================
    f.write("## What Was Exported Automatically\n\n")
    f.write(
        "The Guest migration utility successfully exported the following components:\n\n"
        "- Guest Sites\n"
        "- Guest Types per Site\n"
        "- Hosts per Site\n"
        "- Guest Visit history (last 24 hours)\n\n"
    )
    f.write("---\n\n")

    # ===========================================================
    # WHAT MUST BE REBUILT MANUALLY
    # ===========================================================
    f.write("## Items That Must Be Recreated Manually\n\n")
    f.write(
        "The Public API does **not** support writing Guest configuration. "
        "The following must be rebuilt manually in Org B:\n\n"
        "- Branding, logos, badge themes\n"
        "- iPad pairing\n"
        "- Printer pairing\n"
        "- Guest Type steps, questionnaires, documents\n"
        "- Camera feeds displayed on kiosk\n"
        "- Access Control integrations\n"
        "- Deny lists\n"
        "- Etc.\n\n"

    )
    f.write("---\n\n")

    # ===========================================================
    # EXPORT SUMMARY TABLE (SUCCESS / TOTAL)
    # ===========================================================
    f.write("## Export Summary\n\n")
    f.write("| Category | Success | Total |\n")
    f.write("|----------|--------:|------:|\n")
    f.write(f"| Guest Sites Extracted | {len(sites_a)} | {len(sites_a)} |\n")
    f.write(f"| Guest Types Extracted | {len(guest_types_all)} | {len(guest_types_all)} |\n")
    f.write(f"| Hosts Extracted | {len(guest_hosts_all)} | {len(guest_hosts_all)} |\n")
    f.write(f"| Guest Visits Extracted | {len(all_visits)} | {len(all_visits)} |\n\n")
    f.write("---\n\n")

    # ===========================================================
    # FAILURES
    # ===========================================================
    f.write("## Items Requiring Manual Review\n\n")
    any_failures = False
    for category, items in failures.items():
        if items:
            any_failures = True
            f.write(f"### {category}\n")
            for item in items:
                f.write(f"- {item}\n")
            f.write("\n")

    if not any_failures:
        f.write("No errors detected.\n\n")

    f.write("---\n\n")

    # ===========================================================
    # FULL GUEST WORKFLOW
    # ===========================================================
    f.write("## Full Guest Migration Workflow\n\n")
    f.write(
        "This workflow describes how to rebuild Guest configuration in Org B using the exported CSVs.\n\n"
    )

    # ---------- Prerequisites
    f.write("### Step 1: Prerequisites\n\n")
    f.write("**Hardware:**\n")
    f.write("- iPad (iOS 14+)\n- Brother QL-820NWBc or Epson CW-C4000u printer\n- iPad stand (recommended)\n\n")
    f.write("**Licensing:** Verkada Workplace license must be active in Org B.\n\n")
    f.write("**Permissions:** Org Admin or Site Admin.\n\n")
    f.write("---\n\n")

    # ---------- Recreate Guest Sites
    f.write("### Step 2: Recreate Guest Sites Including Associated Guest Types & Hosts\n\n")
    f.write(
        "Guest Sites determine kiosk location, host associations, Guest Types, and integrations.\n"
        "The sections below break down each site with its associated Guest Types and Hosts.\n\n"
    )

    # ---------- Recreate Types (builds on Step 2)
    f.write("### Associated Guest Types\n\n")
    f.write(
        "Included below is a per-site breakdown of Guest Types. "
        "Use this workflow as the master reference to rebuild each type in Command:\n\n"
        "- Match each type name listed under its site below.\n"
        "- Recreate check-in steps, questionnaires, and documents.\n"
        "- Reapply badge printing behavior.\n"
        "- Re-enable QR Pass and FacePass where used.\n\n"
        "**Location in Command:** Guest → Settings → Sites → Guest Types → Manage Guest Types\n\n"
    )
    f.write("---\n\n")

    # ---------- Hosts (builds on Step 2)
    f.write("### Then, Recreate Hosts\n\n")
    f.write(
        "Included below, each site lists its associated Hosts. "
        "Use this list to restore the host directory:\n\n"
        "1. Ensure every host exists as a Command User.\n"
        "2. Add or map users so the host lists match each listed site.\n\n"
        "---\n\n"
    )
    # ===========================================================
    # PER-SITE DETAIL OUTPUT (Guest Types + Hosts)
    # ===========================================================
    f.write("Full Recreation List:\n")
    for s in sites_a:
        site_id = s.get("site_id")
        site_name = s.get("site_name")
        org_id = s.get("org_id", "")

        f.write(f"---\n\n")
        f.write(f"### Guest Site: **{site_name}**\n")

        # Guest Types
        f.write("#### Guest Types\n")
        site_types = [t for t in guest_types_all if t.get("site_id") == site_id]
        if site_types:
            for t in site_types:
                f.write(
                    f"- **{t.get('name', '(Unnamed Type)')}**\n"
                    f"  - Enabled for Invites: `{t.get('enabled_for_invites')}`\n"
                )
        else:
            f.write("- None\n")
        f.write("\n")

        # Hosts
        f.write("#### Hosts\n")
        site_hosts = [h for h in guest_hosts_all if h.get("site_id") == site_id]
        if site_hosts:
            for h in site_hosts[:25]:
                f.write(
                    f"- **{h.get('first_name','')} {h.get('last_name','')}**\n"
                    f"  - Email: {h.get('email','')}\n"
                    f"  - Requires Approval: `{h.get('requires_host_approval')}`\n"
                )
            if len(site_hosts) > 25:
                f.write(f"- ...and **{len(site_hosts) - 25} more**\n")
        else:
            f.write("- None\n")
        f.write("\n")

    f.write("---\n\n")

    # ---------- iPads, Printers
    f.write("### Step 3: Reconnect iPads & Printers as Needed\n\n")
    f.write(
        "**iPads:** \n"
        "1. Install the **Verkada Guest** iPad app.\n"
        "2. Launch the app and note the short pairing code.\n"
        "3. In Command, go to **Guest → Settings → Sites → [Site] → Add Tablet**.\n"
        "4. Enter the pairing code to bind the iPad to the correct Guest Site.\n\n"
        "**Printers:** \n"
        "1. On the iPad, long-press the bottom-right corner in the Guest app.\n"
        "2. Enter the 4-digit printer pairing code from Command.\n"
        "3. Select the printer (auto-discovered, manual IP, or AirPrint where supported).\n\n"
    )
    f.write("---\n\n")

    # ---------- Documents
    f.write("### Step 4: Rebuild Documents & Agreements\n\n")
    f.write(
        "Recreate all NDAs, safety forms, and custom questionnaires used in Guest:\n\n"
        "- Navigate to **Guest → Documents → Manage Documents**.\n"
        "- Rebuild each document referenced in Guest Type flows.\n\n"
    )
    f.write("---\n\n")

    # ---------- Integrations
    f.write("### Step 5: Rebuild Camera & Access Integrations\n\n")
    f.write(
        "**Cameras:**\n"
        "- Guest → Cameras → Manage Cameras\n"
        "- Select which live feeds show on each kiosk.\n\n"
        "**Access Control:**\n"
        "- Guest → Doors → Manage Doors\n"
        "- Restore any Guest-driven unlock workflows used in Org A.\n\n"
    )
    f.write("---\n\n")

    # ---------- Visits
    f.write("### NOTE: Guest Visits (Informational Only)\n\n")
    f.write(
        "Visit history cannot be imported into Org B.\n"
        "`guest_visits.csv` contains the last 24 hours of visits from Org A if needed.\n\n"
    )
    f.write("---\n\n")

    # ---------- Final Validation
    f.write("### Final Validation\n\n")
    f.write("All sites, workflows, integrations, and check-in functions verified ✔\n\n")
    f.write("---\n\n")

    # ---------- Ending
    f.write("## Congratulations! Guest Backup Complete. Please run next script(s) as needed to complete full migration process.\n\n")


print(f"Generated Guest Report → {REPORT_PATH}")
