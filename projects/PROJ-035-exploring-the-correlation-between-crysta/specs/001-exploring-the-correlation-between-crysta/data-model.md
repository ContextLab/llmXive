# Data Model: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

## Overview
The project produces a single canonical merged dataset that serves as the single source of truth for all downstream analyses. The schema below defines required columns, types, and validation rules.

**Note on VIF**: Variance Inflation Factor (VIF) is a diagnostic computed during regression phase (FR‑008). It is NOT stored in the canonical merged dataset. VIF values are stored only in regression results (`results/regression_summary.json`) for descriptors that pass the VIF filter.

**Note on Temperature**: The `temperature` column stores the ORIGINAL measurement temperature (pre-normalization). Thermal conductivity values are normalized to 300 K ± 10 K per FR‑013 before any analysis. The normalized value is stored in `thermal_conductivity`.

## Merged Perovskite Dataset (`data/cleaned/merged_perovskite.csv`)

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `structure_id` | string | Unique identifier from Materials Project (e.g., `"mp-12345"`). | Non‑null, unique. |
| `chemical_formula` | string | Stoichiometric formula, must match regex `^[A-Z][a-z]?[A-Z][a-z]?[A-Z][a-z]?$` (ABX₃). | Non‑null, ABX₃ only (FR‑001). |
| `chemistry_class` | string | One of `"oxide"`, `"halide"`, `"nitride"`. | Non‑null, enum (FR‑014). |
| `thermal_conductivity` | float | Conductivity (W·m⁻¹·K⁻¹) normalized to 300 K ± 10 K (FR‑013). | Non‑null, > 0. |
| `temperature` | float | Original measurement temperature (K) BEFORE normalization. | Non‑null; if outside 300 K ± 10 K, corrected per Slack (FR‑013). |
| `source_reference` | string | Bibliographic citation or NIST entry URL. | Non‑null, peer‑reviewed or NIST (FR‑010). |
| `tilting_angle` | float | Octahedral tilting angle (degrees). | Non‑null after descriptor calculation (FR‑003). |
| `bond_length_variance` | float | Variance of bond lengths (Å²). | Non‑null (FR‑003). |
| `tolerance_factor` | float | Goldschmidt tolerance factor. | Non‑null (FR‑003). |
| `unit_cell_volume` | float | Unit cell volume (Å³). | Non‑null (FR‑003). |

**Note**: `vif` column removed from merged dataset. VIF is computed during regression phase and stored in `results/regression_summary.json` only for descriptors that pass the VIF filter (VIF ≤ 5).

## Derived Files
- `data/derived/descriptors.csv`: Same rows as merged dataset plus computed descriptor columns (identical to above without `vif`).  
- `results/correlation_matrix_{class}.csv`: Correlation coefficients, raw p‑values, corrected p‑values per descriptor and chemistry class.  
- `results/regression_summary.json`: Cross‑validated metrics, test‑set R², RMSE, feature importance scores, VIF values for included features.  

All files are CSV/JSON with UTF‑8 encoding and include a header row.

---