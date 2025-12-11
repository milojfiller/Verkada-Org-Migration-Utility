# Verkada Org Migration Utility

## Introduction

Migrating a customer from one Verkada organization to another can be time-consuming, error-prone, and heavily dependent on screenshots and undocumented processes.  

The Verkada Org Migration Utility was developed to streamline this workflow by automating every step that the Verkada Public API supports, while generating structured reports and CSVs for everything that must be rebuilt manually.

The core objective is to provide SEs, partners, and developers with a repeatable, safe, and auditable migration process.

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

### 1. Access Control (`Access.py`)

Automated:
- Users (name, email, phone, department, title)
- Access Groups
- Group Membership
- Credentials: Entry Codes, MFA, Keycards, LPR Plates
- BLE Unlock state
- Remote Unlock state
- User start/end dates

Manual Rebuild Required:
- Access Levels
- Door hardware configuration
- Exception calendars
- Installer settings, AUX, REX
- Schedules, lockdown scenarios, roll call

Outputs:
- doors_backup.csv  
- access_levels_backup.csv  
- door_exception_calendars_backup.csv  
- Full Access migration report

---

### 2. Cameras (`Cameras.py`)

Automated:
- Cloud Backup settings
- Audio settings
- People / Vehicle Analytics flags
- Export of all camera metadata
- POI export and recreation

Manual:
- Camera admin settings
- Grids, layouts, alerts
- Historical footage (cannot be moved)

Outputs:
- camera_data_backup.csv  
- Camera Migration Report

---

### 3. Cloud Backup + Audio Restore (`CloudBackup&Audio.py`)

Automated:
- Serial → camera_id remapping in Org B
- Restore cloud backup settings
- Restore audio settings

Outputs:
- Detailed restore log

---

### 4. Guest (`Guest.py`)

Automated (Export Only):
- Guest Sites
- Guest Types (names, behavior, metadata)
- Hosts

Manual Rebuild:
- Guest Type workflows
- Documents (NDAs, safety forms)
- iPad kiosk pairing
- Printers
- Access & camera integrations
- Visit history

Outputs:
- guest_types.csv  
- guest_hosts.csv  
- Guest Migration Report

---

### 5. Helix Event Types (`Helix.py`)

Automated:
- Export Event Types
- Recreate Event Types in Org B

Manual:
- Historical events

Outputs:
- helix_event_types.csv  
- Helix Migration Report

---

### 6. Viewing Stations (`ViewingStations.py`)

Automated:
- Export all Viewing Stations + metadata

Manual:
- Claiming Viewing Stations
- Display configuration

Outputs:
- viewing_stations_backup.csv

---

## What the Utility Can and Cannot Automate

### Fully Automatable Today
- Users, groups, credentials  
- Access Group relationships  
- BLE / Remote unlock  
- Camera cloud backup + audio  
- POIs  
- Helix Event Types  
- Guest metadata exports  
- Viewing Station exports  

### Requires Manual Rebuild (API Limitations)
- Access Levels  
- Doors + controller hardware  
- Door schedules + exception calendars  
- Most camera admin settings  
- Guest workflows + documents  
- Historical footage / visit logs  
- SSO configuration  

All required manual steps are generated as Markdown reports.

---

## Safety and Safeguards

- Org A is always read-only  
- All write operations target only Org B  
- The tool never deletes, modifies, or unassigns devices in Org A  
- Worst case: Org B may need cleanup (all changes are additive)  
- Historical footage, logs, and sensitive customer data are never touched  
- The tool is safe to run multiple times  

This ensures SEs and partners can use the tool confidently during migrations.

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

