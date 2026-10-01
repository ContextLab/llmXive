# Data Sources for Materials Property Analysis

This file defines the specific HuggingFace dataset IDs and API endpoints for the 2-3 target properties
required for this study, as per the amended scope (FR-001).

## Target Properties

The following properties are selected based on data availability and scientific relevance:

1. **Formation Energy**
 - **Dataset ID**: `materials_project/formation_energy`
 - **Description**: Formation energy per atom (eV/atom) from the Materials Project database.
 - **Target Count**: ~150,000 entries.

2. **Band Gap**
 - **Dataset ID**: `materials_project/band_gap`
 - **Description**: Band gap energy (eV) from the Materials Project database.
 - **Target Count**: ~150,000 entries.

3. **Bulk Modulus** (Optional fallback if needed)
 - **Dataset ID**: `materials_project/bulk_modulus`
 - **Description**: Bulk modulus (GPa) from the Materials Project database.
 - **Target Count**: ~150,000 entries.

## Usage Instructions

The `code/download_data.py` script reads this file to determine exactly which datasets to fetch.
Do not modify this list unless a specific dataset is unavailable; if so, replace the ID with a
verified alternative from the same source (Materials Project via HuggingFace).

## Verification

- All datasets are hosted on HuggingFace Hub.
- Access requires a valid HuggingFace token (configured in `config.yaml` or environment).
- Streaming is enabled for large datasets to maintain memory efficiency.
