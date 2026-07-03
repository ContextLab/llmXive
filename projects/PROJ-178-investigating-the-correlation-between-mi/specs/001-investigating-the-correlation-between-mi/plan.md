# Implementation Plan: Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

**Branch**: `001-mitochondrial-aging-correlation` | **Date**: 2026-06-12 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-mitochondrial-aging-correlation/spec.md`

## Summary

This project investigates the associational link between mitochondrial DNA (mtDNA) heteroplasmy burden and chronological age. **CRITICAL DATA WARNING**: The primary dataset (1000 Genomes Project) is a population genetics reference and **does not contain individual chronological ages**. This plan includes a mandatory "Data Availability Gate" (Phase 0). If the `age` column is missing or unverified, the pipeline will **halt** and re-scope to a descriptive analysis of heteroplasmy burden distribution, or flag the project as "Data Unavailable" for the original hypothesis. If age data is found (e.g., via a verified external source or a specific subset), the analysis proceeds with robust statistical methods (Rank-OLS) to adjust for covariates, depth-stratified burden calculation, and sensitivity analyses. All computations are constrained to run on a CPU-only GitHub Actions free-tier runner (2 CPU, 7 GB RAM, ≤6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `numpy`, `scipy`, `vcfpy`, `haplogrep2` (via CLI), `requests`, `tqdm`.  
**Storage**: Local filesystem (`data/` for raw/processed, `code/` for scripts).  
**Testing**: `pytest` with unit tests for data loading and statistical outputs.  
**Target Platform**: Linux (GitHub Actions Ubuntu runner).  
**Performance Goals**: Complete end-to-end analysis (download, process, model, report) within 6 hours on 2 CPU cores, 7 GB RAM.  
**Constraints**: No GPU; no deep learning; streaming VCF processing with in-memory accumulators; data subsampling if RAM limits are approached.  
**Scale/Scope**: Processing a large cohort of samples from Genomes Phase 3; outputting summary statistics and correlation plots (if age data exists).

> **Data Validity Note**: The 1000 Genomes Project metadata does not contain precise chronological ages. The pipeline will perform a strict check for the `age` column. If missing, the analysis will not proceed with correlation tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | ✅ PASS | Random seeds pinned in `code/`. External data fetched from canonical 1000 Genomes FTP. `requirements.txt` pins versions. |
| II. Verified Accuracy | ⚠️ WARNING | The `age` variable source is unverified/missing in the primary dataset. The plan halts if age is not found. Citations restricted to verified sources. |
| III. Data Hygiene | ✅ PASS | Raw data preserved; derivations written to new files with checksums recorded in `state/`. PII scan enforced. |
| IV. Single Source of Truth | ✅ PASS | All statistics in `paper/` trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| V. Versioning Discipline | ✅ PASS | Content hashes used for artifacts; `updated_at` timestamps managed by state file. |
| VI. Mitochondrial Variant Quality | ✅ PASS | Plan explicitly filters VCFs to `PASS` status and applies 1% VAF threshold for burden calculation. Output files recorded in `data/`. |
| VII. Ancestry and Population Controls | ✅ PASS | Models include ancestry PCs and sex; stratified analyses by continental ancestry are mandated. Ancestry assignments traceable to metadata in `data/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-mitochondrial-aging-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded VCFs and metadata (not committed, .gitignored)
│   ├── processed/       # Cleaned CSV/Parquet files (committed)
│   └── checksums.txt    # Checksums for data hygiene
├── analysis/
│   ├── load_data.py     # Download and parse VCFs
│   ├── preprocess.py    # Filter variants, calculate burden (depth-stratified), assign haplogroups
│   ├── model.py         # Rank-OLS, Spearman (unadjusted), BH correction
│   ├── sensitivity.py   # Threshold sweep, subgroup analysis, depth stratification
│   └── visualize.py     # Plot generation
├── tests/
│   ├── test_data.py
│   ├── test_model.py
│   └── test_sensitivity.py
├── requirements.txt
└── run_analysis.py      # Entry point script (includes runtime timer)

paper/
├── draft.md             # Draft manuscript
└── figures/             # Generated plots
```

**Structure Decision**: Single project structure with modular analysis scripts. This minimizes overhead and ensures all data flows through a single `code/` directory, satisfying reproducibility and data hygiene requirements.

## Complexity Tracking

No violations detected. The project scope is contained within the constraints of a CPU-only runner. The use of `haplogrep2` via subprocess is acceptable. The plan includes a hard gate for data availability to prevent scientifically invalid runs.

## Implementation Phases

### Phase 0: Data Availability Gate (Blocking)
1.  **Check Age Column**: Verify the presence of the `age` column in the 1000 Genomes sample metadata panel.
    -   **If Missing**: Log error, halt pipeline, and output "Data Unavailable for Hypothesis" report. Re-scope to descriptive analysis only if user approves.
    -   **If Present**: Proceed to Phase 1.
2.  **Verify Source**: Confirm the metadata file is from the canonical 1000 Genomes FTP (or a verified alternative).

### Phase 1: Data Preparation
1.  **Download & Parse**: Download mitochondrial VCFs (chrM) and sample metadata. Stream VCFs to avoid RAM overflow.
2.  **Filter Variants**: Retain only `PASS` status variants on `chrM`.
3.  **Haplogroup Assignment**: Execute `haplogrep2` on the filtered VCF to assign haplogroups. Store results in the processed dataset. (Addresses FR-003).
4.  **Calculate Heteroplasmy Burden**:
    -   Use an in-memory `defaultdict(int)` accumulator to count variants per sample across VCF chunks.
    -   Apply VAF threshold of **1.0%** (0.01) for the primary burden metric.
    -   **Depth Stratification**: Calculate burden separately for depth bins (Low, Medium, High) to control for depth bias (Addresses scientific soundness concern).
5.  **Merge Data**: Join variant burden, haplogroups, and metadata (age, sex, population, PCs, depth).
6.  **Missing Data Check**: Test if missing `age` correlates with ancestry/depth (logistic regression). If MNAR, flag bias.

### Phase 2: Statistical Analysis
1.  **Unadjusted Check**: Compute Spearman rank correlation between `heteroplasmy_burden` and `age` (unadjusted).
2.  **Adjusted Analysis (Rank-OLS)**:
    -   Rank-transform all continuous variables (`age`, `burden`, `depth`, `PC1`, `PC2`).
    -   Fit OLS regression: `rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)`.
    -   Extract coefficient and p-value for `rank(burden)`. (Addresses methodology concern: robust adjustment).
3.  **Multiple Testing Correction**: Apply Benjamini-Hochberg (BH) correction to all p-values generated (primary, sensitivity, subgroup). (Addresses SC-002).
4.  **Power Analysis**: Re-calculate power based on the *attenuated* effect size (accounting for potential age binning).

### Phase 3: Sensitivity & Robustness
1. **Threshold Sweep**: Recalculate burden and re-run Rank-OLS for thresholds **0.5% (0.005), 1.0% (0.01), and [deferred] (0.02)**. (Addresses FR-005).
2.  **Subgroup Analysis**: Repeat Rank-OLS within continental ancestry groups: **EUR, AFR, EAS, SAS, AMR**. (Addresses FR-006).
3.  **Measurement Error Simulation**: Simulate binned age data using fixed-width intervals. and re-run correlation to estimate attenuation bias.

### Phase 4: Reporting & Validation
1.  **Runtime Measurement**: Wrap the entire pipeline in a timer. Log total execution time to `logs/runtime.log`. (Addresses SC-005).
2.  **Generate Outputs**: Save `analysis_results.csv` and plots to `paper/figures/`.
3.  **Constitution Re-check**: Verify all outputs trace to `data/` and `code/`.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Rank-OLS instead of Partial Spearman | Standard Spearman is bivariate; Rank-OLS allows multivariate adjustment while preserving rank robustness. |
| Depth-Stratified Burden | Controls for non-linear relationship between sequencing depth and heteroplasmy detection sensitivity. |
| Hard Halt on Missing Age | Prevents scientifically invalid analysis; 1000 Genomes lacks precise age data. |
| Remove Power-Law Hypothesis | Kleiber's law is interspecific; applying it to intraspecific aging is a category error. |
| BH Correction on All P-values | Ensures FDR control across all sensitivity and subgroup tests. |