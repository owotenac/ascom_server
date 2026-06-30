# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Data conversion scripts for astronomical catalogs. Converts CSV source data (NGC/IC/Messier deep sky objects, star catalogs) to JSON format for use by the companion `client` app.

## Commands

```bash
# Setup
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt

# Convert NGC catalog to ngc.json and messier.json
python converter.py --ngc data/NGC.csv

# Convert star catalog to stars.json
python converter.py --stars data/hr_v5.0.csv
```

## Data Pipeline

**Source**: `data/NGC.csv` (semicolon-separated, OpenNGC format)
**Output**: `data/ngc.json`, `data/messier.json`, `data/stars.json`

Key transformations in `converter.py`:
- RA/Dec conversion from sexagesimal (HH:MM:SS / DD:MM:SS) to decimal degrees
- Magnitude filtering (B-Mag < 14)
- Southern hemisphere exclusion (Dec > -40)
- Object type filtering (excludes stars, non-existent, duplicates)
- Messier objects extracted as subset where M column is not null

## Coordinate Conventions

- `ra_deg`: Right Ascension in decimal degrees (0-360)
- `dec_deg`: Declination in decimal degrees (-90 to +90)
- Formatted strings use `XXh YYm ZZs` / `XX° YYm ZZs` notation
