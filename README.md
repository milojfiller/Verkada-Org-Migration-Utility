# Verkada-Org-Migration-Utility
A Python-based utility that uses the public Verkada API to automate org-to-org migrations and generate detailed manual checklists for components the API does not support. This tool dramatically reduces migration time and eliminates screenshot-heavy workflows.

---

## Features

### Automated Migration (Public API)

The utility pulls data from Org A and recreates all API-supported objects in Org B, including:

- Users, Groups, Access Group Membership
- BLE Unlock and Remote Unlock states
- Entry Codes, MFA, Keycards, License Plates
- Camera Cloud Backup settings
- Camera Audio settings
- People of Interest (POIs)
- Helix Event Types
- Guest Sites, Guest Types, and Hosts (export only)

All automated actions produce detailed logs and Markdown reports.

---

### Structured Manual Rebuild Workflow

Because some entities cannot be created or modified by the Public API, the tool outputs CSVs and Markdown instructions to rebuild:

- Access Levels
- Doors and Controller Hardware Configuration
- Door Exception Calendars
- Camera admin settings, grid layouts, alerts
- Guest documents, iPad pairings, access integrations
- Historical footage or visit logs (not migratable)

No screenshots from Org A are required — everything is captured as structured data.

---

## Generated Reports

Reports are created in `/Documentation/`:

- Access Control Migration Report
- Camera Migration Report
- Cloud Backup + Audio Restore Report
- Guest Migration Report
- Helix Event Type Migration Report
- Viewing Station Export Summary

Reports contain summaries, per-object breakdowns, success/failure tables, and complete manual workflows.

---

## Repository Structure

/CSVs — Exported data (doors, cameras, access levels, etc.)  
/Documentation — Markdown migration reports  
/scripts — Python migration modules:  
• Access.py  
• Cameras.py  
• CloudBackup&Audio.py  
• Guest.py  
• Helix.py  
• ViewingStations.py  
.env — stores VERKADA_API_KEY_A and VERKADA_API_KEY_B  

Each module runs independently or as part of a full migration.

---

## Environment Variables

Create a `.env` file:

VERKADA_API_KEY_A="ORG_A_API_KEY"  
VERKADA_API_KEY_B="ORG_B_API_KEY"

---

## Running the Migration

Execute modules individually:

python scripts/Access.py  
python scripts/Cameras.py  
python scripts/CloudBackup&Audio.py  
python scripts/Guest.py  
python scripts/Helix.py  
python scripts/ViewingStations.py  

You can also chain modules into an orchestrator script.

---

## Requirements

Install dependencies:

pip install -r requirements.txt

Required:

- Python 3.9+
- pykada
- requests
- python-dotenv

---

## Notes and Limitations

The Public API does NOT support:

- Historical camera footage
- Guest Visit history
- SSO configuration
- Door schedules, roll call, lockdown scenarios
- Controller hardware configuration
- Certain org-level camera settings

For these items, the tool generates CSVs and detailed manual-rebuild workflows.

---

## Contributions

Pull requests are welcome — especially improvements to error handling, mapping logic, API coverage, or optional UI integrations.
