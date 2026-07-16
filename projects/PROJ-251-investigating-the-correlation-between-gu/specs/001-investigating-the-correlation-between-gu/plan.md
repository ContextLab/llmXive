# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

**Branch**: `001-investigating-the-correlation-between-gu` | **Date**: 2026-06-29 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`
**Input**: Feature specification from `specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary

This project implements a statistical pipeline to investigate the association between gut microbiome composition (16S rRNA OTU data) and immune response to influenza vaccination (serology data). The pipeline ingests pre-processed data from NCBI SRA accession SRP (or raw FASTQ if pre-processed is unavailable), applies Centered Log-Ratio (CLR) transformation with pseudocount sensitivity analysis, performs Spearman correlation with Benjamini-Hochberg correction, and trains a Random Forest classifier with nested cross-validation. The model's predictive utility is validated against a permutation baseline (permuting microbiome rows relative to serology) to ensure statistical significance. The implementation strictly adheres to the "CPU-only, free-tier" constraints, ensuring all operations fit within 7GB RAM and 6 hours runtime.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `numpy`, `seaborn`, `pyyaml`, `requests`, `qiime2` (optional fallback), `dada2` (optional fallback)  
**Storage**: Local CSV/Parquet files (no external database)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research Pipeline  
**Critical Constraint**: Runtime ≤ 6h, Memory ≤ 7GB, Disk ≤ 14GB  
**Constraints**: No GPU, no 8-bit quantization, no heavy LLM inference, strict data validation before analysis.  
**Scale/Scope**: Cohort size N ≥ 50 (if < 50, pipeline halts); Taxa count typically ranges from tens to hundreds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; data fetched from canonical URL (SRP053178) or raw SRA; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Dataset URL for the SRP accession is verified and reachable. No fabricated URLs. |
| **III. Data Hygiene** | PASS | Checksums recorded in state; raw data preserved; derivations written to new files; PII scan passed. |
| **IV. Single Source of Truth** | PASS | All results trace to `data/` artifacts; no hand-typed statistics in `paper/`. N_count.json logged before halt. |
| **V. Versioning Discipline** | PASS | Content hashes used; `updated_at` timestamp updated on artifact change. |
| **VI. Statistical Rigor** | PASS | Benjamini-Hochberg correction applied; p < 0.05 threshold enforced; zero-variance taxa excluded; Pseudocount Sensitivity Analysis (T020-B) performed. |
| **VII. Sample-Size-Aware Validation** | PASS | Nested cross-validation with multiple folds enforced; feature selection inside loop; halt if N < 50; N logged as artifact before halt. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── correlation.schema.yaml
│   └── model.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-251-investigating-the-correlation-between-gu/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # Data download (SRP053178), filtering, validation, Strategy B (raw FASTQ)
│   ├── preprocessing.py       # Zero-variance removal, CLR, Shannon
│   ├── correlation.py         # Spearman, BH correction, Pseudocount Sensitivity
│   ├── modeling.py            # RF, Nested CV, Permutation Baseline, Threshold Sweep, Comparison
│   ├── utils.py               # Logging, memory monitoring, runtime monitoring
│   └── main.py                # Pipeline orchestration
├── data/
│   ├── raw/                   # Downloaded artifacts (checksummed)
│   ├── processed/             # Intermediate CSVs/Parquets
│   └── results/               # Final metrics, plots
├── tests/
│   ├── test_ingestion.py
│   ├── test_correlation.py
│   └── test_modeling.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Selected a modular single-project structure (`code/`) to facilitate end-to-end reproducibility on a single runner. All data flows through `data/` with strict separation of raw and processed artifacts. `ingestion.py` maps to the 'Ingestion' data flow step; `preprocessing.py` maps to the 'Transformation' step.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Nested CV** | Required by SC-003 and Spec to prevent overfitting in small N. | Single CV would inflate accuracy estimates; feature selection leakage would invalidate results. |
| **Sensitivity Analysis (Threshold)** | Required by Spec Assumptions (±10% threshold sweep). | Fixed threshold ignores uncertainty in responder definition; violates robustness requirement. |
| **Pseudocount Sensitivity** | Required by Concern methodology-c011f09e. | Single pseudocount value is a critical confound in CLR; stability must be verified. |
| **Permutation Baseline (Microbiome Shuffle)** | Required by Concern scientific_soundness-59d97c99. | Shuffling labels is tautological; permuting microbiome rows tests the true association. |
| **Memory Monitoring** | Required by Critical Constraint (7GB limit). | Default Python behavior may exceed RAM on large OTU tables; explicit checks ensure CI compliance. |
| **Zero-Variance Exclusion** | Required by Spec Edge Cases to avoid division by zero. | CLR on zero-variance taxa produces undefined values. |
| **Strategy B (Raw FASTQ)** | Required by FR-001 if pre-processed data is missing. | Relying solely on pre-processed data risks total pipeline failure if source is unavailable. |

## Implementation Phases & Tasks

### Phase 0: Data Ingestion & Validation
- **T011**: Implement data download/fetch logic with Strategy A and Strategy B.
  - *Strategy A (Primary)*: Fetch pre-processed CSV/Parquet for NCBI SRA accession SRP053178.
  - *Strategy B (Fallback)*: If Strategy A fails, download raw FASTQ files from SRA for the same accession and run a lightweight 16S processing pipeline (QIIME2 or DADA2) to generate the OTU table and taxonomy.
  - *Input*: Accession ID SRP053178.
  - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.
  - *Error Handling*: If both strategies fail, raise `DataUnavailableError`.
- **T012**: Implement data filtering logic.
  - *Input*: Raw CSVs.
  - *Logic*: Filter for subjects with complete baseline microbiome and post-vaccination titer records.
  - *Output*: `data/processed/filtered.csv`.
- **T015-A**: Calculate N (subject count) from `filtered.csv`.
- **T015-B**: Log N to `data/results/N_count.json`.
- **T015-C**: Conditional check: If N < 50, prepare error message.
- **T015-D**: Raise `InsufficientSampleSizeError` with message including N if condition met.

### Phase 1: Preprocessing & Transformation
- **T019**: Implement Zero-Variance Exclusion.
  - *Input*: `filtered.csv`.
  - *Logic*: Identify and remove taxa with zero variance across all subjects.
  - *Output*: `data/processed/filtered_no_zero_var.csv`.
- **T020-A**: Implement CLR Transformation (Default Pseudocount).
  - *Input*: `filtered_no_zero_var.csv`.
  - *Logic*: Relative abundance -> CLR (add 1e-6).
  - *Output*: `data/processed/cleared_default.csv`.
- **T020-B**: Implement Pseudocount Sensitivity Analysis.
  - *Input*: `filtered_no_zero_var.csv`.
  - *Logic*: Run CLR with pseudocounts. Compare the stability of the most significant taxa.
  - *Output*: `data/results/pseudocount_sensitivity.json`.
- **T020-C**: Calculate Shannon Diversity Index.
  - *Input*: `filtered_no_zero_var.csv`.
  - *Output*: `data/processed/cleared_with_diversity.csv`.

### Phase 2: Correlation Analysis
- **T025**: Implement Spearman Correlation & BH Correction.
  - *Input*: `cleared_with_diversity.csv`.
  - *Logic*: Spearman between CLR taxa and log-titer. Apply BH correction.
  - *Output*: `data/results/correlations.csv`.
- **T026**: Implement Significant Taxa Count & Range Check.
  - *Input*: `correlations.csv`.
  - *Logic*: Count taxa with adj-p < 0.05. Compare against expected range (low single-digit to high single-digit). Log result.
  - *Output*: `data/results/significant_taxa_count.json`.

### Phase 3: Predictive Modeling
- **T030-A**: Define Seroconversion Logic (Fold-change ≥ 4).
- **T030-B**: Define Absolute Titer Logic (HAI ≥ 40).
- **T030-C**: Implement Threshold Parameterization.
- **T030-D**: Implement Responder Status Definition with Fallback.
  - *Logic*: If pre-vaccination titers exist, use Seroconversion OR Absolute. Else, use Absolute only. Log mode used.
  - *Output*: `data/processed/responder_labels.csv`.
- **T034-A**: Implement Nested K-Fold Cross-Validation (Random Forest).
  - *Input*: `cleared_with_diversity.csv`, `responder_labels.csv`.
  - *Logic*: Outer loop -fold. Inner loop feature selection (top taxa) + hyperparameter tuning.
  - *Output*: `data/results/cv_metrics.json`.
- **T034-B**: Implement Permutation Baseline Testing (Microbiome Shuffle).
  - *Input*: `cleared_with_diversity.csv`, `responder_labels.csv`.
  - *Logic*: Permute microbiome rows relative to serology labels (break association). Train RF on permuted data. Repeat times to build null distribution.
  - *Output*: `data/results/null_distribution.csv`.
- **T034-C**: Implement Threshold Sweep & Robustness Check.
  - *Logic*: Sweep responder threshold ±10%. For each threshold, run T034-B and compare model accuracy p-value against baseline.
  - *Output*: `data/results/sensitivity_analysis.csv`.
- **T035**: Implement Statistical Comparison.
  - *Logic*: Compare RF accuracy (T034-A) against null distribution (T034-B). If p < 0.05, flag as significant. Else, flag as not significant. Halt or flag if condition not met.
  - *Output*: `data/results/model_significance.json`.

### Phase 4: Reporting & Verification
- **T042**: Implement Runtime Verification.
  - *Logic*: Measure total runtime.
  - *Constraint*: Must be ≤ 6h.
- **T043**: Implement Memory & Runtime Verification.
  - *Logic*: Measure peak memory usage.
  - *Constraint*: Must be ≤ 7GB.
  - *Output*: `data/results/resource_usage.json`.
- **T045**: Generate Final Report.
  - *Input*: All result JSONs/CSVs.
  - *Output*: `data/results/final_report.md`.

## Critical Constraint Checklist

| Constraint | Verification Task | Pass Condition |
| :--- | :--- | :--- |
| **Runtime ≤ 6h** | T042 | Total runtime ≤ 21600 seconds. |
| **Memory ≤ 7GB** | T043 | Peak memory ≤ 7340 MB. |
| **Sample Size ≥ 50** | T015-D | N ≥ 50 (Else halt). |
| **Data Completeness** | T012 | No nulls in key columns. |
| **Statistical Significance** | T035 | Model p-value < 0.05 vs null. |
| **Zero-Variance Handling** | T019 | All zero-variance taxa removed before T020. |

## Risk Assessment

- **Data Availability**: Low risk. SRP is a verified, accessible accession. Strategy B (raw FASTQ) provides a fallback.
- **Sample Size**: Medium risk. If N < 50, pipeline halts gracefully with logged N.
- **Overfitting**: Medium risk. Mitigated by Nested CV and Permutation Baseline.
- **Compositional Bias**: Low risk. Mitigated by CLR and Pseudocount Sensitivity Analysis.