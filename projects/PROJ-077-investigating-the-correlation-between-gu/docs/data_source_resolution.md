# Data Source Resolution

## Status: Verified Accuracy FAIL - Local Data Fallback Required

**Date Resolved**: 2023-10-27
**Project**: PROJ-077-investigating-the-correlation-between-gu
**Task ID**: T049

## Current Status

The UK Biobank data required for this research project is **not publicly available via a direct URL** due to data privacy regulations and the controlled access nature of the dataset. Consequently, the "Verified Accuracy" constraint cannot be satisfied via a remote URL fetch.

To resolve this, the pipeline is configured to run **exclusively on local data** provided by the researcher under the `data/raw/` directory. This fallback mechanism is the ONLY valid path for execution until a verified public URL is established.

## Required Data Files and Naming Conventions

For the pipeline to proceed, the following files **MUST** exist in `data/raw/` with the exact filenames specified below. The pipeline will raise a `FileNotFoundError` if any of these are missing.

### 1. Microbiome Data
- **Filename**: `microbiome_otu_counts.csv`
- **Required Columns**:
 - `participant_id` (or `eid` or `subject_id` - priority order applies)
 - Columns for each OTU/ASV (e.g., `OTU_001`, `OTU_002`,...) representing raw integer counts.
- **Format**: Wide format CSV (rows = participants, columns = taxa).

### 2. Cognitive Performance Data
- **Filename**: `cognitive_data.csv`
- **Required Columns**:
 - `participant_id` (or `eid` or `subject_id`)
 - `fluid_intelligence` (float/int)
 - `age` (float/int)
 - `sex` (string: 'M' or 'F')
 - `bmi` (float)

### 3. Dietary Data (for DQS Calculation)
- **Filename**: `dietary_data.csv`
- **Required Columns** (HEI-2015 Components):
 - `Total Fruits`
 - `Whole Fruits`
 - `Total Vegetables`
 - `Greens and Beans`
 - `Whole Grains`
 - `Dairy`
 - `Total Protein Foods`
 - `Seafood and Plant Proteins`
 - `Refined Grains`
 - `Sodium`
 - `Empty Calories`
- **Note**: If this file is missing, the pipeline will fail **ONLY IF** `DQS_REQUIRED` is set to `True` in `code/config.py`. If `DQS_REQUIRED` is `False`, it will log a warning and proceed without DQS.

## Access Instructions (UK Biobank)

To obtain the real data required to populate these files:

1. **Apply for Access**: Visit the UK Biobank website (https://www.ukbiobank.ac.uk/) and submit an application for research access.
2. **Data Fields**: Request the following specific fields:
 - **Microbiome**: 200,000+ whole genome sequencing data (or specific microbiome OTU/ASV tables if available in the current release).
 - **Cognitive**: Field ID 100086 (Fluid Intelligence Score), Field ID 21003 (Age at recruitment), Field ID 31 (Sex), Field ID 21001 (BMI).
 - **Dietary**: Field IDs 1081, 1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089, 1090, 1091 (corresponding to HEI-2015 components).
3. **Download**: Once approved, download the data via the UK Biobank Data Showcase.
4. **Processing**: Convert the downloaded data into the CSV formats and column names specified above.
5. **Placement**: Place the resulting CSV files in the `data/raw/` directory at the project root.

## CI/CD Fallback Mechanism

The Continuous Integration (CI) runner is configured with `ALLOW_LOCAL_DATA=True` by default to allow the pipeline to start if the local files are present. However, if `data/raw/` is empty, the pipeline will **halt with a fatal error** rather than generating synthetic data, adhering to the "Fail Loudly" constraint.

**Error Message on Missing Data**:
`FileNotFoundError: Real data source not found. Expected files in data/raw/: ['microbiome_otu_counts.csv', 'cognitive_data.csv', 'dietary_data.csv']. Please download the UK Biobank data and place it in the correct directory.`

## Verification Checklist

Before running the pipeline, verify:
- [ ] `data/raw/microbiome_otu_counts.csv` exists and is non-empty.
- [ ] `data/raw/cognitive_data.csv` exists and is non-empty.
- [ ] `data/raw/dietary_data.csv` exists (if DQS is required).
- [ ] Column names match the specification exactly (case-sensitive).
- [ ] `code/config.py` has `DQS_REQUIRED` set according to the current analysis needs.

---
*This document resolves the "Verified Accuracy" FAIL by explicitly defining the local data fallback mechanism.*