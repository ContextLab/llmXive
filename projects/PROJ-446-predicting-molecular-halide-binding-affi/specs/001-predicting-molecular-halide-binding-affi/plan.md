# Implementation Plan: Predicting Molecular Halide Binding Affinities with Machine Learning

**Branch**: `001-predicting-halide-binding-affinities` | **Date**: 2024-01-15 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-predicting-molecular-halide-binding-affi/spec.md`

## Summary

This project implements a machine learning pipeline to predict molecular halide binding affinities using experimental data from NIST and PubChem. The approach involves ingesting and cleaning binding constant data, generating molecular fingerprints (ECFP4) and descriptors via RDKit, and training Random Forest and Gradient Boosting models. The pipeline strictly adheres to a host-molecule-based cross-validation strategy to prevent data leakage, performs per-halide statistical comparisons using **Bootstrap Resampling** (to generate 95% Confidence Intervals for the difference in mean performance), and generates interpretable feature importance analyses. All operations are constrained to run on a CPU-only GitHub Actions free-tier environment.

**Critical Note on Data Availability**: No verified dataset containing the full tuple (Host SMILES, Halide ID, Binding Constant) exists in the provided verified list. The project relies on a **physics-based simulated data fallback** to demonstrate the pipeline. If real data is found, the scope is comparative analysis; otherwise, the scope is reduced to single-halide prediction with a warning that the comparative question is unanswerable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `requests`, `pyyaml`  
**Storage**: Local CSV/Parquet files under `data/` (checksummed)  
**Testing**: `pytest` (contract tests for schemas, unit tests for data processing logic)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete full pipeline (ingestion to reporting) within ≤6 hours; peak RAM ≤7 GB.  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; strict host-based data splitting; no causal claims.  
**Scale/Scope**: Target dataset: ≥50 host molecules with ≥3 halide measurements each. Fallback: Simulated data if primary sources are insufficient.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | ✅ | Random seeds pinned in `code/`. External datasets fetched from canonical HuggingFace sources. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | ✅ | All dataset URLs in `research.md` are strictly from the verified list. Citations validated against primary sources by the **Reference-Validator Agent**. |
| **III. Data Hygiene** | ✅ | Raw data preserved in `data/raw/`. Derived data in `data/processed/` with checksums recorded in state YAML. No in-place modifications. |
| **IV. Single Source of Truth** | ✅ | All figures/stats in `paper/` generated directly from `data/processed/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | ✅ | Artifacts tracked with content hashes. The **Advancement-Evaluator Agent** updates `state.yaml` on artifact changes. |
| **VI. Halide-Specific Evaluation** | ✅ | Metrics (R², RMSE) calculated and reported separately for F⁻, Cl⁻, Br⁻, I⁻. No aggregate-only reporting. |
| **VII. Molecular Split Validation** | ✅ | 5-fold CV splits performed by `host_id` (not measurement ID) to prevent leakage. Verified by code execution agent. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-halide-binding-affinities/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/001-predicting-molecular-halide-binding-affinities/
├── data/
│   ├── raw/                 # Downloaded raw files (NIST, PubChem)
│   ├── processed/           # Cleaned CSVs, feature matrices
│   └── checksums.yaml       # Artifact hashes
├── code/
│   ├── __init__.py
│   ├── data_ingestion.py    # FR-001, FR-010, FR-011
│   ├── feature_engineering.py # FR-002, FR-003
│   ├── model_training.py    # FR-004, FR-005
│   ├── analysis.py          # FR-006, FR-007, FR-009, FR-012, FR-013
│   └── report_generator.py  # FR-008
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── unit/                # Data processing logic tests
│   └── integration/         # End-to-end pipeline tests
├── docs/
│   └── paper/               # Generated report/paper
└── requirements.txt
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. Data separation (`raw` vs `processed`) enforces Constitution Principle III. Modular `code/` structure aligns with FRs and facilitates independent testing of ingestion, modeling, and analysis.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Host-based Splitting** | Prevents data leakage where the same host appears in train/test. | Random splitting would leak host-specific structural features, inflating R² and violating FR-004/Constitution VII. |
| **Fallback to Simulated Data** | Ensures pipeline runs if real-world data is insufficient (<50 hosts). | Aborting on missing data prevents demonstration of the full pipeline and violates FR-011. |
| **Per-Halide Statistical Testing** | Required to detect selectivity trends (Constitution VI). | Aggregate testing masks differences between specific halide interactions. |

## Simulated Data Flag Propagation

The `data_ingestion.py` module sets a global `is_simulated` flag (or a column `source='Simulated'`) if the fallback is triggered. This flag is propagated through the pipeline:
1. `feature_engineering.py`: Reads the flag and applies any specific simulation filters.
2. `model_training.py`: Logs the flag and adjusts scope (disables comparative analysis if `is_simulated`).
3. `analysis.py`: Uses the flag to **skip pairwise comparisons** if `is_simulated` is true, and ensures the report reflects the reduced scope.
4. `report_generator.py`: Includes a prominent "Simulated Data Warning" in the final report if the flag is set.

## Simulated Data Schema Validation

The `data_ingestion.py` module MUST validate the generated simulated data against `contracts/dataset.schema.yaml` before writing to `data/processed/`. This ensures that the simulated data adheres to the required schema (e.g., valid SMILES pattern, correct enum values for halide identity, numeric binding constants).

## Statistical Analysis Update

The plan replaces the Paired Wilcoxon test with **Bootstrap Resampling** (1000 iterations) to generate 95% Confidence Intervals for the **distribution of the difference in mean R² and RMSE** between halide pairs. This addresses the statistical invalidity of applying Wilcoxon to N=5 fold-level aggregates.
- **Conditional Execution**: If `is_simulated` is true, pairwise comparisons are **skipped** entirely, and the report states that comparative analysis is unanswerable.
- **Correction**: Benjamini-Hochberg (FDR ≤ 0.05) is applied to p-values if hypothesis testing is performed on the bootstrap distribution.
- **Power Analysis**: Removed. Replaced with reporting of 95% Confidence Intervals.

## Domain Sanity Check

The plan implements a **Domain Sanity Check** (FR-013, SC-007) that validates a curated subset of top-ranked features against a curated list of known chemical determinants: **{HBD, HBA, TPSA, MolWt, Cavity Size (MolVol)}**.
- **Curated List**: Defined as {Hydrogen Bond Donor Count, Hydrogen Bond Acceptor Count, Topological Polar Surface Area, Molecular Weight, Cavity Size}.
- **Validation Logic**: The model is flagged as "chemically implausible" if:
  1. None of the top 3 features match the curated list, OR
  2. The slope direction of the top feature's relationship with binding affinity contradicts electrostatic theory (e.g., negative correlation for electrostatic attraction where positive is expected).
- This replaces the circular 'overlap' check with an independent validation of the model's learning mechanism.

## Scope Reduction Logic (FR-011)

If the primary dataset contains < 50 host molecules or lacks the `binding_constant` column:
1. **Trigger**: The system detects the condition during `data_ingestion.py`.
2. **Action**: Switch to the physics-based simulated dataset.
3. **Scope Change**: Reduce scope to **single-halide prediction** only. Comparative analysis (US-4) is abandoned.
4. **Warning**: Log the exact message: "WARNING: Primary dataset insufficient (<50 hosts or missing columns). Scope reduced to single-halide prediction. Comparative analysis unanswerable with available data."
5. **Flag**: Set `is_simulated = True` and `comparative_analysis_enabled = False`.

## FR-001 Implementation Details

- **Scraping Logic**: `data_ingestion.py` will use `requests` with a rate limit of 1 request per second to NIST/PubChem.
- **Error Handling**: If a request fails (HTTP 429, 503, or timeout), the system will retry up to 3 times with exponential backoff. If all retries fail, the record is skipped and logged.
- **Parsing**: Use `BeautifulSoup` to parse HTML tables for 'log K' and 'halide' keywords.
- **Fallback Trigger**: If the scraped data does not contain the required columns (Host SMILES, Halide ID, Binding Constant, Solvent) or the count of valid hosts is < 50, the fallback is triggered.