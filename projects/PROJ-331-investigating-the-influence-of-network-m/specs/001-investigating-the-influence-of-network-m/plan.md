# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-06-27 | **Spec**: `spec.md`

## Summary

This project implements a reproducible, CPU-constrained pipeline to investigate whether specific 3-node network motif configurations in structural brain connectomes constrain individual variation in resting-state functional connectivity (rsFC). The system downloads HCP diffusion and rs-fMRI data (or uses pre-seeded data), constructs Schaefer parcellated connectomes (preserving both binary and weighted forms), enumerates small-node motifs against degree-preserving null models (A fixed number of iterations), and computes partial correlations controlling for network density. Statistical rigor is enforced via FDR (Benjamini-Hochberg) correction, permutation testing, and power analysis, with all results rendered in a single PDF report.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `networkx`, `matplotlib`, `seaborn`, `nibabel`, `requests`, `reportlab`, `tqdm`, `joblib`, `dipy` (for streamline counting)  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `results/`)  
**Testing**: `pytest` (unit tests for motif counting, integration tests for pipeline steps)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, no GPU)  
**Project Type**: Scientific data pipeline / CLI  
**Performance Goals**: Motif enumeration ≤ 300s/subject; Full pipeline ≤ 6h; PDF generation ≤ 2m  
**Constraints**: No GPU; Memory ≤ 7GB; Disk ≤ 14GB; Must handle missing subjects gracefully; Must include mandatory associational disclaimer.  
**Scale/Scope**: N=50 subjects; -node motifs only; Schaefer-100 parcellation (100x100 matrices).

> **Dataset Fit Note**: The plan relies on the HCP S1200 Release which provides raw diffusion tractography (streamlines/NIFTI) and resting-state fMRI for the same subjects. The pipeline performs local tractography-to-matrix conversion (streamline counting) and applies the Schaefer-100 parcellation to ensure node correspondence.

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Compliance Check | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `random.seed(42)` pinned in all stochastic steps (null model generation, permutation). `requirements.txt` pins all versions. Pipeline runs end-to-end on fresh CI. |
| **II. Verified Accuracy** | **PASS** | Citations (Schaefer et al., 2018; HCP) will be validated against primary sources before final report generation. |
| **III. Data Hygiene** | **PASS** | Raw HCP data stored in `data/raw/` with checksums (SHA256) recorded in `data/raw/.checksums.json`. Derived matrices stored in `data/processed/` with provenance metadata. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the PDF are generated directly from `results/` CSVs/JSONs produced by the code. No manual typing. Power analysis results written to `results/power_analysis.json`. |
| **V. Versioning Discipline** | **PASS** | Phase 0 includes execution of `scripts/hash_artifacts.sh` to generate content hashes for all data/code artifacts and update `state/...yaml` with `updated_at` timestamp. |
| **VI. Structural Data Integrity** | **PASS** | Raw diffusion matrices preserved. Binary and weighted connectomes derived via Schaefer parcellation saved as new files with source reference. |
| **VII. Statistical Transparency** | **PASS** | Scripts record exact seeds, library versions, and parameters (N_perm, alpha, correction method) in `pipeline.log` and report metadata. |

## Project Structure

### Source Code

```text
code/
├── __init__.py
├── config.py              # Paths, seeds, constants
├── pipeline.py            # Orchestration: download, preprocess, analyze
├── download.py            # HCP data fetching logic (CI-safe)
├── preprocess.py          # Tractography-to-matrix, parcellation, rsFC calc
├── motifs.py              # 3-node motif enumeration, null model generation
├── stats.py               # Correlation, FDR, Permutation, Power Analysis
├── report.py              # PDF generation (matplotlib + reportlab)
├── utils.py               # Logging, error handling, file I/O, checksum generation
└── scripts/
    └── hash_artifacts.sh  # Versioning script

tests/
├── unit/
│   ├── test_motifs.py     # Motif counting correctness, edge cases
│   ├── test_stats.py      # Correlation, p-value calculation
│   └── test_preprocess.py # Parcellation logic
├── integration/
│   └── test_pipeline.py   # End-to-end run on small subset
└── conftest.py

data/
├── raw/                   # HCP downloads (symlinked or direct)
│   └── .checksums.json    # SHA256 manifest
├── processed/             # .npy matrices, motif profiles
└── logs/                  # pipeline.log

results/
└── report.pdf
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead and fits the CLI nature of the scientific pipeline. No separate backend/frontend required.

## Phase Plan & FR/SC Mapping

### Phase 0: Research & Data Verification (Pre-Implementation)
*   **Goal**: Verify dataset availability, variable fit, and versioning setup.
*   **FR/SC Mapping**:
    *   **FR-001 / SC-001**: Verify HCP S1200 Release contains both DWI and rs-fMRI for A substantial number of subjects.
    *   **FR-010 / SC-005**: Verify power analysis parameters (N=50, alpha=0.05) are feasible.
    *   **Constitution V**: Execute `scripts/hash_artifacts.sh` to generate SHA256 hashes for all data/code artifacts and update `state/...yaml` `updated_at` timestamp.
*   **Action**: Query verified dataset sources (see `research.md`). Confirm Schaefer-100 atlas compatibility. Generate initial checksums for any pre-seeded data.

### Phase 1: Data Pipeline (Download & Preprocess)
*   **Goal**: Download and transform raw data into binary and weighted connectomes, and rsFC matrices.
*   **FR/SC Mapping**:
    *   **FR-001**: Download DWI and rs-fMRI (or verify pre-seeded data in `data/raw/`).
    *   **FR-002**: Apply Schaefer-100 parcellation to DWI -> Binary Adjacency (density thresholded at incremental levels) AND Weighted Adjacency (streamline count).
    *   **FR-003**: Compute rsFC (Pearson) and Global Efficiency (on **weighted**, unthresholded graph).
    *   **FR-008**: Log steps to `pipeline.log`.
    *   **SC-001**: ≥95% success rate (skip missing, log warning).
    *   **Data Hygiene**: Run `sha256sum` on all raw files and record manifest in `data/raw/.checksums.json`.
*   **Edge Case Handling**: If subject missing, log warning and skip (US-1, Edge Case).
*   **Data Conversion**: Use `dipy` to count streamlines between Schaefer-100 nodes. Save weighted matrix (float32) and binary matrices (uint8) at three density thresholds.

### Phase 2: Motif Quantification
*   **Goal**: Enumerate 3-node motifs and compute z-scores.
*   **FR/SC Mapping**:
    *   **FR-004**: Enumerate 3-node subgraphs; generate degree-preserving nulls (Maslov-Sneppen); compute z-scores.
    *   **SC-002**: Ensure execution ≤ 300s/subject on 2-core CPU (achieved by limiting to 100 iterations and using `networkx`).
    *   **Edge Case**: If null model fails to converge after a predetermined number of retries, exclude subject from that specific motif's analysis (set z-score to `null` in JSON, do not assign 0).
*   **Method**: `networkx` for subgraph isomorphism counting. Output normalized to `motif_profile.schema.yaml`.
*   **Thresholding Strategy**: Compute z-scores at three density thresholds. Aggregate final `motif_z_scores` using the **median** value across thresholds to mitigate thresholding bias. Raw per-threshold scores stored in `motif_z_scores_raw`.

### Phase 3: Statistical Analysis
*   **Goal**: Correlate motifs with rsFC metrics, apply corrections.
*   **FR/SC Mapping**:
    *   **FR-005**: Partial Pearson/Spearman (controlling for **network density**); FDR (Benjamini-Hochberg) correction for multiple testing.
    *   **FR-006**: Permutation test (≥1000) for significant motifs.
    *   **FR-010**: Power analysis module; results written to `results/power_analysis.json` (Single Source of Truth).
    *   **SC-003**: Report corrected p-values for all motifs.
    *   **Edge Case**: Zero-variance detection (skip test, flag in report). VIF check for collinearity.
*   **Statistical Rigor**:
    *   **Multiple Comparisons**: FDR (Benjamini-Hochberg) applied across all directed 3-node motifs. Bonferroni is avoided as it is overly conservative for correlated tests.
    *   **Power**: With N=50 and FDR-adjusted alpha, detectable r is likely moderate (two-tailed test assumed for conservatism). This is explicitly reported.
    *   **Causal Claims**: None. The plan explicitly frames results as associational (FR-009, Constitution Principle VII).
    *   **Collinearity**: VIF check performed. If VIF > 5 for the control variable, report collinearity and switch to Spearman or uncorrected correlations with caveats.
    *   **Circularity Avoidance**: Global Efficiency calculated on *weighted* (unthresholded) graph; Motifs on *binary* (thresholded) graph. Control variable is *network density* (not global degree) to avoid redundancy with the null model which preserves degree.
    *   **Control Variable Justification**: Z-scores are defined as deviations from a degree-preserving null. Controlling for global degree would be statistically redundant. Controlling for network density (which varies with thresholding) accounts for the thresholding confound.

### Phase 4: Reporting
*   **Goal**: Generate PDF report with plots and disclaimers.
*   **FR/SC Mapping**:
    *   **FR-007**: Scatter plots, CIs, p-values, permutation results per motif.
    *   **FR-009**: Mandatory disclaimer: "These findings are associational only..."
    *   **SC-004**: PDF ≤ 5MB, generation ≤ 2m.

## Statistical Rigor & Feasibility Notes

*   **Multiple Comparisons**: Benjamini-Hochberg (FDR) correction applied across all directed 3-node motifs to account for correlation structure. Bonferroni is avoided as it is overly conservative for correlated tests.
*   **Power**: With N=50 and FDR-adjusted alpha, detectable r is likely moderate in magnitude (two-tailed test assumed for conservatism). This is explicitly reported in the power analysis section (FR-010). The report will acknowledge the risk of Type II errors for moderate effect sizes.
*   **Causal Claims**: None. The plan explicitly frames results as associational (FR-009, Constitution Principle VII).
*   **Collinearity**: VIF check performed before partial correlation. If VIF > 5 for the control variable, the plan reports collinearity and adjusts the statistical approach.
*   **Circularity**: Global Efficiency is calculated on the *weighted* structural graph (unthresholded), while motifs are calculated on the *binary* graph (thresholded). The control variable is *network density* (not global degree) to avoid statistical redundancy with the null model which preserves degree.
*   **Compute Feasibility**:
    *   **Motif Counting**: Motifs on 100-node graphs are computationally feasible.
    *   **Null Models**: 100 iterations per subject (reduced from 1000 to ensure SC-002 compliance). Edge-switching algorithms (Maslov-Sneppen) are used.
    *   **Memory**: 50 subjects * 100x100 matrices is negligible. Processing is sequential to stay under 7GB RAM.
    *   **Timeout**: A timeout wrapper (s) is implemented for motif counting. If exceeded, the subject is skipped for that motif and logged.