# Project Structure Implementation

This document describes the implementation of the project directory structure for **PROJ-266**.

## Implemented Tasks

- **T001**: Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- **T008**: Setup directory structure for `data/raw/` and `data/processed/` with checksum generation utility.

## Directory Layout

The following directory structure is created by `code/setup_project_structure.py`:

```
PROJ-266/
├── code/
│ ├── utils/ # Utility modules (config, logging, reports)
│ └── data/ # Data processing and analysis scripts
├── tests/
│ └── contract/ # Contract tests for data schemas
├── data/
│ ├── raw/ # Raw downloaded data (ChEMBL)
│ ├── processed/ # Cleaned and processed data
│ └── interim/ # Intermediate data files
├── figures/ # Generated plots and visualizations
├── state/
│ └── projects/ # Project state and deviation records
└── specs/ # Feature specifications and design docs
```

## Usage

### 1. Initialize Project Structure

Run the setup script to create all necessary directories:

```bash
cd PROJ-266
python code/setup_project_structure.py
```

### 2. Data Integrity Checksums

The `code/data/setup_directories.py` script provides utilities for data integrity:

```bash
# Create data directories and generate checksums for existing files
python code/data/setup_directories.py
```

This will:
- Create `data/raw/`, `data/processed/`, `data/interim/`, and `figures/`
- Scan `data/raw/` and `data/processed/` for files
- Generate SHA-256 checksums for all found files
- Save manifests as `.checksum_manifest.json` in each directory

### 3. Run Tests

Verify the structure with unit tests:

```bash
python -m pytest tests/test_setup.py -v
```

## Checksum Manifest Format

Checksum manifests are stored as JSON files with the following structure:

```json
{
 "relative/path/file.csv": "sha256_hash_hex_string",
 "another/file.parquet": "another_sha256_hash"
}
```

This allows for easy verification of data integrity over time.
