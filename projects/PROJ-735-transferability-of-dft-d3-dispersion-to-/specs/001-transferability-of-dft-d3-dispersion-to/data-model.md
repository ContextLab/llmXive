# Data Model: Transferability of DFT‑D3 Dispersion to Ionic Liquids

## Overview
Defines all data structures, schemas, and transformation pathways from raw inputs to final reports. Every artefact is immutable or version‑controlled, satisfying the Constitution’s Data Hygiene and Single‑Source‑of‑Truth principles.

## Entities

| Entity | Description | Fields |
|--------|-------------|--------|
| **IonPair (raw)** | One ion‑pair complex from the benchmark set; includes a `cluster_id` to capture shared cation/anion groups. | `pair_id` (str), `xyz_path` (str), `reference_energy` (float, kcal mol⁻¹), `cations` (str), `anions` (str), `cluster_id` (str) |
| **CalculationResult (derived)** | Holds energies extracted from Psi4 and error metrics. | `pair_id` (str), `dft_total_energy` (float), `d3_dispersion_energy` (float), `bsse_correction` (float), `calculation_status` (enum: success/failed/skipped), `error_signed` (float), `dispersion_only_error` (float) |
| **BulkProperty (raw)** | Experimental bulk data for an ion pair. | `pair_id` (str), `density` (float, g/cm³), `viscosity` (float, cP), `source` (str) |
| **ScalingResult (derived)** | Scalar correction for the D3 term, with statistics. | `scaling_factor` (float > 0), `ci_lower` (float), `ci_upper` (float), `p_value` (float), `mae_corrected` (float), `mae_original` (float) |
| **PartialCorrelationResult (derived)** | Result of a partial correlation controlling for electrostatic energy and size. | `test_name` (str), `method` (enum: Pearson/Spearman), `coefficient` (float), `p_value` (float), `p_value_bonferroni` (float), `ci_lower` (float), `ci_upper` (float), `n` (int), `is_significant` (bool) |
| **CorrelationResult (derived)** | Mirrors the CSV output; each row corresponds to a (partial) correlation test. | `metric_name` (str), `coefficient` (float), `r_squared` (float), `p_value` (float), `p_value_bonferroni` (float), `ci_lower` (float), `ci_upper` (float), `n_samples` (int), `is_significant` (bool) |
| **ScalingDiagnostics (derived)** | Residual‑diagnostics after applying the scaling factor (FR‑018). | `histogram_path` (str), `shapiro_wilk_stat` (float), `shapiro_wilk_p` (float), `breusch_pagan_stat` (float), `breusch_pagan_p` (float), `diagnostic_summary` (str) |

## File Specifications

| File | Location | Format | Schema |
|------|----------|--------|--------|
| `IL‑Benchmark‑local.zip` | `data/raw/` | ZIP (contains `metadata.csv` + `XYZ/` files) | – |
| `metadata.csv` | extracted from ZIP | CSV | Columns: `pair_id`, `xyz_file`, `reference_energy`, `cations`, `anions` |
| `validated_metadata.csv` | `data/derived/` | CSV | Same columns as `metadata.csv`; all rows pass FR‑002 validation. |
| `validation.log` | `data/derived/` | Text | Logs warnings about missing fields; used for reproducibility audit. |
| `experimental_bulk_properties.csv` | `data/raw/` | CSV | Columns: `pair_id`, `density`, `viscosity` |
| `raw_energies.csv` | `data/derived/` | CSV | **Schema**: `contracts/raw_energies.schema.yaml`. |
| `scaling_factor.txt` | `data/derived/` | Text (JSON block) | **Schema**: `contracts/scaling_factor.schema.yaml`. |
| `scaling_diagnostics.md` | `data/derived/` | Markdown | Summarizes histogram, Shapiro‑Wilk, Breusch‑Pagan results after scaling (FR‑018). |
| `correlation_results.csv` | `data/derived/` | CSV | **Schema**: `contracts/correlation_results.schema.yaml`. |
| `correlation_report.md` | `docs/` | Markdown (JSON representation) | **Schema**: `contracts/correlation_report.schema.yaml`. |
| `benchmark_report.md` | `docs/` | Markdown | Human‑readable summary of raw MAE, RMSE, MSE, and MAE CI. |
| `code/lint_report.txt` | `code/` | Text | Must end with `Exit code: 0`. |
| `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml` | `state/projects/` | YAML | SHA‑256 checksums for all raw and derived artefacts. |

## Constraints
- **Immutability**: Files under `data/raw/` are never overwritten. Derived files are written to `data/derived/` with timestamps if regenerated.  
- **Missing Data Handling** (`FR‑002`): Records lacking `pair_id` or `reference_energy` are logged in `validation.log` and omitted; bulk‑property gaps lead to exclusion from correlation (edge‑case handling).  
- **Unit Consistency**: Energies in kcal mol⁻¹, densities in g cm⁻³, viscosities in cP.  
- **Checksum Recording**: SHA‑256 hashes of all raw and derived files are stored in `state/projects/...yaml` for reproducibility verification.  

## Alignment with Specification
- **FR‑001** – Data acquisition attempts to download from Zenodo; if that fails, the pipeline **aborts** unless the user explicitly enables the fallback with `--allow-fallback`.  
- **FR‑008** – Bulk‑property data are loaded from the NIST API first; on failure the pipeline **aborts** unless the fallback flag is set.  
- **FR‑009‑FR‑011** – Partial correlation, bootstrap, and Bonferroni correction are implemented in Phase 5, with results captured in `correlation_results.csv` and `correlation_report.md`.  
- **FR‑014** – Raw MAE bootstrap CI is produced in Phase 3 and reported in `benchmark_report.md`.  
- **FR‑018** – Residual diagnostics after scaling are captured in `scaling_diagnostics.md`.  

---


