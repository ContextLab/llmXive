# Implementation Plan: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Branch**: `001-predict-immune-response` | **Date**: 2026-07-03 | **Spec**: `specs/001-predict-immune-response/spec.md`
**Input**: Feature specification from `specs/001-predict-immune-response/spec.md`

## Summary

This feature implements a computational pipeline to test the hypothesis that viral sequence features (codon usage, GC content, k-mers, repeat density, and predicted protein stability) can predict host immune response scores (Interferon Response, ISG-PC1) derived from transcriptomic data. The pipeline downloads viral genomes from NCBI Virus and host expression data from GEO, extracts features, trains an Elastic Net model with rigorous statistical validation (permutation tests, Debiased Lasso), and generates visualizations. The implementation strictly adheres to the Constitution's reproducibility and data hygiene principles, ensuring all artifacts are checksummed and reproducible on a CPU-first GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `biopython`, `gseapy`, `pandas`, `numpy`, `scikit-learn`, `xgboost`, `statsmodels`, `pyteomics`, `requests`, `gdown` (for GEO/NCBI access), `matplotlib`, `seaborn`, `joblib`, `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/artifacts`) with checksummed manifests  
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Computational biology pipeline / CLI  
**Performance Goals**: Complete end-to-end run within 4 hours on 2 CPU cores; memory usage < 7GB.  
**Constraints**: No local GPU; must stream or sample large datasets; strict adherence to FR-003 (ESM-1b) and FR-007 (A sufficient number of permutations) without silent reduction.  
**Scale/Scope**: A cohort of virus strains (limited by GEO availability and NCBI Virus completeness) and a corresponding set of samples will be collected to address the research question using the established method.

> **Note on Compute Feasibility**: The plan prioritizes CPU-tractable methods. ESM-1b inference is computationally expensive; to fit within the 4-hour/7GB RAM constraint on a 2-core CPU, the plan implements a **streaming/mini-batch** approach for protein stability calculation, processing **all** ORFs > 100aa (per FR-003) in batches. If the full ESM-1b load exceeds memory even with streaming, the system falls back to the "Uniform Stability Proxy" (AAC + Hydrophobicity) **only if** a ratified `docs/spec_amendments.md` entry exists. Otherwise, it aborts with a clear error, as per the unresolved concern regarding silent spec drift.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins all versions. `data/manifest.json` records checksums and NCBI/GEO versions. Random seeds pinned in `src/config.py`. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs (GEO, NCBI) are cited from the "Verified datasets" block. No hallucinated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Derived data in `data/processed/`. Checksums recorded in `data/manifest.json`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` trace to `data/artifacts/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. `state/` updated on artifact changes. |
| **VI. Viral Sequence Data Provenance** | **PASS** | `data/manifest.json` explicitly lists NCBI Virus accession IDs and database release date. |
| **VII. Statistical Validation Rigor** | **PASS** | Plan mandates permutations (FR-007) and 5-fold CV. **No silent reduction logic allowed.** If runtime exceeds limit, pipeline aborts. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-immune-response/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Global constants, seeds, paths
├── download.py          # NCBI Virus & GEO fetchers, manifest generation
├── preprocess.py        # Normalization, ISG mapping, ortholog mapping, score calc
├── features.py          # CAI, GC, k-mer, repeat density, protein stability (ESM-1b/Proxy)
├── models.py            # Elastic Net, Debiased Lasso, Permutation test
├── viz.py               # Feature importance, partial dependence
└── main.py              # Orchestration, CLI entry point

data/
├── raw/                 # Downloaded FASTA, GEO matrices (raw)
├── processed/           # Normalized counts, ISG scores, merged features
├── artifacts/           # Models, p-values, plots, manifest.json
└── manifest.json        # Checksums, versions, provenance

tests/
├── unit/                # Feature extraction tests
├── integration/         # Pipeline flow tests
└── contract/            # Schema validation tests
```

**Structure Decision**: Single project structure selected to minimize overhead for a computational pipeline. All data flow is linear (Download -> Preprocess -> Features -> Model -> Viz), making a monolithic `src/` directory with clear module separation efficient.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **ESM-1b Inference** | Required by FR-003 for accurate protein stability. | Using only AAC/Hydrophobicity violates FR-003 and Constitution Principle II (Accuracy). A "proxy" is only acceptable if the full model fails and a formal amendment is ratified. |
| **1000 Permutations** | Required by FR-007 and Constitution Principle VII. | Reducing permutations for speed violates the statistical rigor requirement. The pipeline must abort if time exceeds limits rather than silently lowering the bar. |
| **Strain-Level Splitting** | Required by FR-005 to prevent data leakage. | Sample-level splitting would inflate R² by allowing the model to "memorize" strain-specific noise. |

## Traceability Matrix

| Contract Schema | Generating Task ID | Phase | Description |
| :--- | :--- | :--- | :--- |
| `dataset_schema.schema.yaml` | T021 | 1.10 | Merged dataset schema (k=3-6) |
| `feature_pvalues.schema.yaml` | T030 | 2.4 | Feature p-values schema |
| `metrics_schema.schema.yaml` | T034 | 2.6 | Global metrics schema |
| `permutation_test.schema.yaml` | T032b | 2.5 | Permutation test output schema |

## Implementation Phases

### Phase 1: Data Acquisition & Preprocessing

**Goal**: Produce a clean, aggregated dataset of viral features and host response scores.

1.  **T012a: Fetch Viral Genomes**
    *   **Input**: List of virus accessions from GEO metadata.
    *   **Action**: Download FASTA from NCBI Virus.
    *   **Artifact**: `data/raw/viral_genomes.fasta`.
2.  **T012b: Fetch GEO Data**
    *   **Input**: GEO Series IDs.
    *   **Action**: Download raw counts matrix AND metadata (Series Matrix file) using `GEOparse`.
    *   **Artifact**: `data/raw/GSEXXXXX_counts.csv` (Tab-separated, genes as index, samples as columns) AND `data/raw/GSEXXXXX_metadata.txt`.
3.  **T012c: Generate Manifest**
    *   **Input**: Accessions, GEO IDs, checksums, **and metadata file**.
    *   **Action**: Generate `data/manifest.json` with provenance. **CRITICAL VALIDATION**: Read metadata file to check `virus_strain_accession` linkage. Abort with `FatalError: >10% samples lack valid strain link (FR-014)` if validation fails.
    *   **Artifact**: `data/manifest.json`.
4.  **T015a: Map ISG Genes**
    *   **Input**: Host species, ISG list.
    *   **Action**: Map orthologs using Ensembl Compara.
    *   **Artifact**: `data/processed/ortholog_map.csv` (Columns: `human_gene`, `ortholog_gene`, `species`, `source`).
5.  **T015b: Validate ISG Mapping**
    *   **Input**: **Raw counts matrix from T012b**, ortholog map.
    *   **Action**: Verify mapped orthologs exist in raw counts.
    *   **Artifact**: Log of validation status.
6.  **T014: Normalize Counts**
    *   **Input**: Raw counts, ortholog map, **validated gene set from T015b**.
    *   **Action**: TMM normalization (edgeR).
    *   **Artifact**: `data/processed/normalized_counts.csv` (Genes as index, samples as columns).
7.  **T015c: Calculate ISG Score**
    *   **Input**: Normalized counts, ISG list.
    *   **Action**: PCA to compute ISG-PC1.
    *   **Artifact**: `data/processed/isg_scores.csv` (Sample ID index, `isg_score` column).
8.  **T018a-d: Extract Viral Features**
    *   **Input**: Viral genomes.
    *   **Action**: Extract CAI, GC, k-mer (k=3,4,5,6), repeat density.
    *   **Artifact**: `data/processed/viral_features.csv`.
9.  **T020: Calculate Protein Stability**
    *   **Input**: Viral ORFs.
    *   **Action**: ESM-1b (streaming) or Proxy (if amendment ratified).
    *   **Artifact**: `data/processed/stability_scores.csv` (Keys: `aac_A`...`hydrophobicity_kytedoolittle`).
10. **T021: Merge Datasets**
    *   **Input**: Viral features, ISG scores.
    *   **Action**: Merge on strain accession.
    *   **Artifact**: `data/processed/merged_dataset.csv`.
11. **T022: Aggregate by Strain**
    *   **Input**: Merged dataset.
    *   **Action**: Average ISG-PC1 for multiple samples of same strain.
    *   **Artifact**: `data/processed/aggregated_strains.csv`.
12. **T023: Validation**
    *   **Input**: Aggregated strains.
    *   **Action**: Check `len >= 30`. Abort if not.
    *   **Artifact**: Validation log.

### Phase 2: Modeling & Validation

**Goal**: Train model, validate rigorously, generate artifacts.

1.  **T026: Split Data**
    *   **Input**: Aggregated strains.
    *   **Action**: Strain-level split (/20), ensure test set >= 5 strains.
    *   **Artifact**: `data/processed/train.csv`, `data/processed/test.csv`.
2.  **T028: Train Elastic Net**
    *   **Input**: Train set.
    *   **Action**: 5-fold CV for alpha/lambda tuning.
    *   **Artifact**: `data/artifacts/model.joblib`.
3.  **T030: Debiased Lasso p-values**
    *   **Input**: Model, Test set.
    *   **Action**: Compute coefficients and p-values.
    *   **Artifact**: `data/artifacts/pvalues_exploratory.json` (Schema: `feature_name`, `coefficient`, `p_value_raw`, `p_value_fdr`).
4.  **T032b: Permutation Test**
    *   **Input**: Model, Test set.
    *   **Action**: **Strictly 1000 permutations**. **ABORT with fatal error if runtime > 4h.** Do NOT reduce permutation count.
    *   **Artifact**: `data/artifacts/permutation_pvalue.json`.
5.  **T033: Evaluate Model**
    *   **Input**: Model, Test set.
    *   **Action**: Calculate R², RMSE.
    *   **Artifact**: Metrics.
6.  **T034: Log Metrics**
    *   **Input**: All metrics.
    *   **Action**: Save to `data/artifacts/model_metrics.json`.
    *   **Artifact**: `data/artifacts/model_metrics.json`.
7.  **T010: Visualize**
    *   **Input**: Model, p-values.
    *   **Action**: Generate plots.
    *   **Artifact**: `data/artifacts/plots/`.

## Statistical Methodology

### 1. Unit of Analysis: Strain-Level
The pipeline strictly adheres to FR-016: **Strain-Level Aggregation**. Multiple host samples for the same virus strain are averaged to produce a single ISG-PC1 score per strain. This ensures the unit of analysis is the strain, preventing data leakage and ensuring the test set (>=5 strains) has sufficient power for generalization claims. The pipeline aborts if the final dataset contains a limited number of strains (FR-013).

### 2. Permutation-Calibrated Inference (Resolving Post-Selection Bias)
To address the "p > n" issue and the invalidity of asymptotic p-values in high-dimensional settings (concerns scientific_soundness-03cf85cd, scientific_soundness-d1f6be74), the plan replaces the "univariate screening" pre-selection step with a **Permutation-Calibrated Inference** strategy:
*   **No Pre-Selection**: All features (k=3-6, CAI, etc.) are retained.
*   **Elastic Net Shrinkage**: Elastic Net is used for regularization and feature selection (shrinking irrelevant coefficients to zero).
*   **Global Permutation**: The **entire pipeline** (including the Elastic Net selection step) is run a substantial number of times on permuted labels.
*   **Calibration**: The observed coefficient magnitudes are compared against the distribution of coefficients obtained from the permuted runs. This accounts for the selection bias introduced by Elastic Net, providing valid p-values without relying on asymptotic assumptions.

### 3. Feature Dimensionality Check
If the final dataset has < 50 strains, the plan triggers a **Feature Dimensionality Check**. In this regime, high-dimensional k-mer features (k=5, 6) are excluded to ensure n > p for the stability of the permutation calibration. This is a strict power safeguard.

### 4. VIF as Diagnostic Only
Variance Inflation Factor (VIF) is calculated for all predictors (FR-008) but is used **only for diagnostic reporting**. Features are **not** removed based on VIF > 5. This prevents selection bias where VIF-based removal interacts with the subsequent Debiased Lasso step.

### 5. Proxy Validation Strategy
For ESM-1b, if the full set cannot be processed, the system calculates the "Uniform Stability Proxy" for the full dataset **only after** validating the proxy's correlation with ESM-1b on a representative subset (top strains by genome length). If the correlation (R²) on the subset is < 0.8, the pipeline aborts. This ensures the proxy is not used blindly (concern data_resources-c74a6ebc).

### 6. Metadata Linkage Validation
A dedicated validation step (T012c) checks for the `virus_strain_accession` field in GEO metadata. If the linkage is ambiguous for >10% of samples, the pipeline aborts with `FatalError: >10% samples lack valid strain link (FR-014)`. This prevents "garbage in" scenarios (concern methodology-47168d70).

### 7. Viral Load Control
The preprocessing phase includes a **Viral Load Control** step. If viral load metadata is available, it is regressed out from the ISG-PC1 score. If not, samples are stratified by infection time point to ensure the model predicts immune response specificity, not just viral load magnitude (concern scientific_soundness-1c10c620).

### 8. Ortholog Mapping
Ortholog mapping uses **Ensembl Compara (latest version)

The research question investigates the comparative genomic relationships across vertebrate species. The method employs whole-genome alignments and gene tree reconciliation using the Ensembl Compara pipeline. References: Flicek et al. (n.d.); Aken et al. ().** (FR-015) for non-human/mouse species. The specific version is hardcoded in `src/preprocess.py`.