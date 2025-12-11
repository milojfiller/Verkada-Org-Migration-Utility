# Verkada Org Migration Utility

## Introduction

Migrating a customer from one Verkada organization to another can be time-consuming, error-prone, and heavily dependent on screenshots and undocumented processes.  

The Verkada Org Migration Utility was developed to streamline this workflow by automating every step that the Verkada Public API supports, while generating structured reports and CSVs for everything that must be rebuilt manually.

The core objective is to provide individuals with a repeatable, safe, and auditable migration process.

---

## About Verkada

Verkada provides a unified, cloud-managed physical security platform across:

- Video Security  
- Access Control  
- Sensors  
- Alarms  
- Workplace (Guest & Mailroom)  
- Intercom  
- Gateways (Cellular & WiFi)

This utility interacts exclusively with Verkada’s publicly documented APIs at:  
https://apidocs.verkada.com/

Important:  
This project is not an official Verkada product and is not supported or endorsed by Verkada Inc.  
Use at your own discretion.

---

## What This Utility Does

The utility is built as a collection of product-specific Python modules.  
For each subsystem, the tool:

- Exports all API-accessible data from Org A  
- Recreates all API-supported objects in Org B  
- Generates Markdown reports detailing:  
  - What was migrated  
  - What could not be migrated  
  - What must be manually rebuilt  
  - Step-by-step workflows for finishing the migration  

---

## Migration Capabilities by Product

### Access Control (`Access.py`)

Automated:
- Access Groups
- Users (first name, last name, email, department, title, phone, etc.)
- Group membership
- BLE unlock state
- Remote unlock state
- Start and end dates
- Entry codes
- Keycards
- License plates
- MFA codes

Manual Rebuild Required:
- Access Levels: names, doors, sites, schedules
- Door Exception Calendars
- Doors: controller assignment, port, lock type, inputs, etc.
- Controller hardware configuration
- Door schedules, lockdown scenarios, AUX behaviors, etc.

Outputs:
- Full Access Migration Report
- doors_backup.csv  
- access_levels_backup.csv  
- door_exception_calendars_backup.csv  

---

### Cameras (`Cameras.py`)

Automated:
- Cloud Backup settings
- Audio settings
- LPOIs
- POIs (just saved in CSV)
- Full individual camera configuration data for efficient migration:
  - Camera metadata (model, serial, site, firmware, MAC, IP)
  - People & Vehicle analytics toggle state
  - Location (+ lat/lon)

Manual:
- Camera claiming / decommissioning
- Motion zones
- Privacy regions
- Detection zones (people/vehicle analytics)
- Alerts
- Archive history
- Historical footage
- Incidents

Outputs:
- Camera Migration Report
- camera_data_backup.csv
- pois_backup.csv
- lpois_backup.csv

---

### Cloud Backup + Audio Restore (`CloudBackup&Audio.py`)

Automated:
- Restore cloud backup settings
- Restore audio settings

Outputs:
- Detailed restore information

---

### Guest (`Guest.py`)

Automated (Backup Only):
- Guest Sites
- Guest Types
- Hosts
- Guest Visit History (24 hours)

Manual Rebuild:
- Branding, logos, badge themes
- iPad pairing
- Printer pairing
- Guest Type steps, questionnaires, documents
- Camera feeds displayed on kiosk
- Access Control integrations
- Deny lists
- Etc.

Outputs:
- Guest Migration Report
- guest_sites_backup
- guest_types_backup
- guest_hosts_backup
- guest_visits_backup
  
---

### Helix Event Types (`Helix.py`)

Automated:
- Helix Event Types

Outputs:
- Helix Migration Report
- helix_event_types.csv  

---

### Viewing Stations (`ViewingStations.py`)

Automated (Backup Only):
- Viewing Stations + metadata

Manual:
- Claiming Viewing Stations
- Display configuration

Outputs:
- viewing_stations_backup.csv

---

## Safety and Safeguards

- Org A is always read-only  
- All write operations target only Org B  
- The tool never deletes, modifies, or unassigns devices in Org A  
- Historical footage, logs, and sensitive customer data are never touched
  
---

## Repository Structure

/CSVs → Exported data (doors, cameras, access levels…)
/Documentation → Markdown migration reports
/scripts → Product-specific migration logic
  - Access.py  
  - Cameras.py  
  - CloudBackup&Audio.py  
  - Guest.py  
  - Helix.py  
  - ViewingStations.py
.env → Stores VERKADA_API_KEY_A and VERKADA_API_KEY_B

---

## Requirements

Python 3.9+

Install dependencies:
pip install -r requirements.txt

---

## Environment Variables

`.env` file:

VERKADA_API_KEY_A="ORG_A_API_KEY"
VERKADA_API_KEY_B="ORG_B_API_KEY"

---

## Running the Migration

Run modules individually based on migration/customer need:

python scripts/Access.py
python scripts/Cameras.py
python scripts/CloudBackup&Audio.py
python scripts/Guest.py
python scripts/Helix.py
python scripts/ViewingStations.py

---
## Quick Start Guide

This section provides the fastest way to run a basic Org A → Org B migration.

### 1. Download the Repository

You may obtain the project in either of the following ways:

Option A: Clone using Git 
git clone https://github.com/milofiller/Verkada-Org-Migration-Utility.git  
cd Verkada-Org-Migration-Utility

Option B Download ZIP (no Git required)  
1. Click the green “Code” button on GitHub  
2. Select “Download ZIP”  
3. Extract the ZIP file  
4. Open the folder in your editor 

### 2. Create a Python Virtual Environment

python3 -m venv venv
source venv/bin/activate

### 3. Install Dependencies

pip install -r requirements.txt

### 4. Add Your API Keys

`.env` in the project root:

VERKADA_API_KEY_A="API_KEY_FOR_ORG_A"
VERKADA_API_KEY_B="API_KEY_FOR_ORG_B"

Org A = Source  
Org B = Destination  

### 5. Run a Migration Script

Each subsystem can be migrated independently.

Running a script will:

1. Export data from Org A  
2. Recreate supported objects in Org B  
3. Generate detailed Markdown reports in `/Documentation`  
4. Save all CSV backups in `/CSVs`

---
## Thank you for exploring this utility!
Please feel free to provide any feedback as needed.

