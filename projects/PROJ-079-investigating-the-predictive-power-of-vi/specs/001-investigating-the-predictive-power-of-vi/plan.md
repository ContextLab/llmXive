# Implementation Plan: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Branch**: `001-predict-immune-response` | **Date**: 2026-06-24 | **Spec**: `specs/001-predict-immune-response/spec.md`
**Input**: Feature specification from `specs/001-predict-immune-response/spec.md`

## Summary

This feature implements a computational pipeline to investigate whether viral sequence features (CAI, GC-content, k-mers, repeat density, protein stability) can predict host immune response scores (Interferon-Response PC1) derived from transcriptomic data. The pipeline ingests viral genomes from NCBI Virus and host expression data from GEO, extracts features, trains an Elastic Net regression model with Debiased Lasso inference, and validates performance via permutation testing and cross-validation. The implementation must strictly adhere to the project's compute constraints (CPU-only, free-tier CI) and the rigorous statistical requirements defined in the spec (FR-001 to FR-017, SC-001 to SC-004).

**Critical Note on Compute Constraints**: The spec assumes an 8-core CPU environment (FR-011), but the implementation targets the GitHub Actions Free Tier (2 CPU cores, ~7GB RAM). A fixed runtime limit is enforced on the runner. If the workload exceeds a predetermined threshold, the pipeline aborts. The spec's 8-core assumption is noted as a discrepancy; the plan prioritizes the 2-core feasibility constraint.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `biopython`, `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `pyyaml`, `requests`, `scipy`, `matplotlib`, `seaborn`, `pysam`, `rpy2` (for `edgeR` TMM normalization), `gseapy` (or manual PCA), `h5py`.  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`). No external database.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7GB RAM).  
**Project Type**: Data Science Pipeline / CLI Tool.  
**Performance Goals**: Complete end-to-end execution within 4 hours on 2 CPU cores. Memory usage < 6GB.  
**Constraints**:  
- **NO GPU**: ESM-1b is too heavy for 2 CPU cores. The plan implements a **Uniform Stability Proxy** (Amino Acid Composition + Hydrophobicity Scales) as the **mandatory** method for protein stability for ALL samples. The Spec (FR-003) is **FLAGGED** for amendment to align with CPU-only feasibility and to eliminate method-switch bias.
- **Data Size**: Must handle the merged dataset without loading full FASTA files into memory simultaneously.
- **Statistical Rigor**: Must implement Debiased Lasso and permutation testing. Permutation test must re-run PCA on permuted data to handle HDLSS.
- **Feature Dimensionality**: To address the underdetermined system (N < 100 strains, P > 10,000 k-mers), k-mer frequency extraction is **restricted to k=3 and k=4 only**. This is a fixed, a priori selection protocol to ensure Debiased Lasso validity.

**Note on Dataset Strategy**: The "Verified datasets" block provided for this project contains **no** direct links to the specific NCBI Virus genomes or GEO transcriptomic series required by the spec (FR-001, FR-002). The verified URLs are for medical imaging and unrelated data. Therefore, the pipeline **MUST** implement dynamic fetching from NCBI Virus (via `biopython` Entrez) and GEO (via `GEOparse`), handling the "No verified source" constraint by explicitly stating in `research.md` that these sources are fetched programmatically from their canonical public portals.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and programmatic data fetching (NCBI/GEO) rather than static dumps. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` will be validated against primary sources. Dataset fetching logic will log source URLs. |
| **III. Data Hygiene** | **PASS** | Pipeline will compute checksums for downloaded FASTA and GEO matrices. Intermediate files will be versioned. |
| **IV. Single Source of Truth** | **PASS** | Final metrics (R², p-values) will be derived strictly from `data/processed` outputs and logged to `data/metrics.json`. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `data/` artifacts will be recorded in the state YAML. |
| **VI. Viral Sequence Data Provenance** | **PASS** | **Step 1.4** in Key Implementation Steps mandates `download.py` to generate `manifest.json` listing all NCBI accessions, **database release version**, and download timestamps. |
| **VII. Statistical Validation Rigor** | **PASS** | Plan explicitly includes k-fold CV, a large number of permutations (with re-run PCA), and Debiased Lasso implementation. |

## Key Implementation Steps

### Phase 1: Data Acquisition & Provenance
1.  **Step 1.1**: Fetch viral genomes from NCBI Virus using `biopython.Entrez` for all accessions in `config/studies.yaml`.
2.  **Step 1.2**: Fetch host transcriptomic data from GEO using `GEOparse`.
3.  **Step 1.3**: Compute checksums for all raw files.
4.  **Step 1.4**: **Generate Manifest**: `download.py` MUST create `data/manifest.json` containing:
    -   List of all `accession_id`.
    -   `database_release_version`: The NCBI Virus release version string (extracted from download headers or metadata).
    -   `download_timestamp`.
    -   `file_checksum`.
    -   *Abort if manifest generation fails.*

### Phase 2: Preprocessing & Validation
1.  **Step 2.1**: **Ortholog Mapping**: For non-human/mouse species, use `rpy` to call `Ensembl Compara v109` (via API) to map ISG genes. **CRITICAL VALIDATION**: Immediately after mapping, verify that the mapped orthologs exist in the normalized counts matrix. If the overlap is insufficient (e.g., < 80% of the set present), mark the sample as `excluded` (FR-015) and log the reason. Do not proceed to PCA if the set is empty.
2.  **Step 2.2**: **Strain Link Validation**: Calculate the ratio of samples lacking a valid `virus_strain_accession` link. **If (missing_count / total_count) > 0.10**, **ABORT** with fatal error (FR-014).
3.  **Step 2.3**: Normalize counts using **TMM** (via `edgeR` loaded via `rpy2`).
4.  **Step 2.4**: Compute ISG-PC (First PC of 50 ISG genes) using `scikit-learn` PCA. **CRITICAL VALIDATION**: Before running PCA, verify that the ISG gene set (mapped or standard) is present in the matrix and has non-zero variance. If the set is empty or constant, exclude the sample or abort.
5.  **Step 2.5**: Extract Viral Features:
    -   CAI (relative to human/mouse reference).
    -   GC Content (Global & 1kb windows).
    -   k-mer frequencies (**k=3, 4 ONLY**). This fixed reduction is necessary for dimensionality control.
    -   Repeat Density.
    -   **Protein Stability**: Use **Uniform Stability Proxy** (AAC + Hydrophobicity) for **ALL** samples. *Note: Spec FR-003 flagged for amendment.*

### Phase 3: Aggregation & Splitting
1.  **Step 3.1**: **Strain-Level Aggregation**: Average ISG-PC1 scores for all samples belonging to the same `virus_strain_accession` (FR-016).
2.  **Step 3.2**: **Strain-Level Split**: Split the aggregated dataset into Train/Test at the **strain level**.
    -   **Validation**: **Verify** that the Test set contains **≥ 5 distinct virus strains** (FR-017). **If not, ABORT** with fatal error.
    -   Ensure no strain appears in both splits.

### Phase 4: Modeling & Inference
1.  **Step 4.1**: **Assumption Check**: Verify design matrix incoherence and sparsity before Debiased Lasso. If assumptions fail, log warning and fallback to coefficient reporting without p-values.
2.  **Step 4.2**: Train Elastic Net with 5-fold CV (inside training set only).
3.  **Step 4.3**: **Permutation Test**: Run a sufficient number of permutations. **Crucial**: For each permutation, **re-run PCA** on the permuted feature matrix (or permuted labels) to generate the null distribution of R². This prevents inflated Type I errors in HDLSS regimes (FR-007).
4.  **Step 4.4**: Compute Debiased Lasso p-values (FR-012) and VIF (FR-008).
5.  **Step 4.5**: Apply Benjamini-Hochberg FDR correction (FR-009).

### Phase 5: Visualization & Reporting
1.  **Step 5.1**: Generate plots (Feature Importance, Partial Dependence).
2.  **Step 5.2**: Log runtime. **If > 4 hours (on 2-core runner)**, abort (FR-011).

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
├── data/
│   ├── download.py      # NCBI Virus & GEO fetching (FR-001, FR-002), Manifest Gen (Step 1.4)
│   ├── preprocess.py    # Normalization, ISG-PC1, Feature Extraction (FR-002, FR-003)
│   └── merge.py         # Strain-level aggregation, Splitting, Validation (Step 2.2, 3.2)
├── models/
│   ├── train.py         # Elastic Net, CV tuning (FR-006)
│   ├── evaluate.py      # R², RMSE, Permutation Test (FR-007)
│   └── inference.py     # Debiased Lasso, VIF, FDR (FR-008, FR-009, FR-012)
├── viz/
│   └── plots.py         # Bar plots, Partial Dependence (FR-010)
├── utils/
│   ├── config.py        # Constants, paths
│   └── logging.py       # Runtime tracking (FR-011)
└── main.py              # Orchestration entry point

tests/
├── unit/
│   ├── test_preprocess.py
│   ├── test_models.py
│   └── test_viz.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # Downloaded FASTA, GEO matrices (checksummed)
├── processed/           # Merged CSV, Feature Matrix
├── interim/             # Intermediate PCA, VIF calculations
└── artifacts/           # Manifests, logs, metrics.json
```

**Structure Decision**: Single `src/` layout chosen to simplify dependency management and pathing for the data pipeline. `tests/` separated for clarity. `data/` follows the hygiene requirement (raw vs processed).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Debiased Lasso Implementation** | FR-012 requires p-values for Elastic Net, which standard `sklearn` does not provide. | Using standard t-tests on coefficients is invalid for regularized models. Must implement the specific debiasing algorithm or use `hdi` library (if CPU compatible). |
| **Strain-Level Aggregation** | FR-016 requires averaging host scores per strain to avoid pseudoreplication. | Treating samples as independent would violate statistical assumptions and inflate R². |
| **Uniform Stability Proxy** | ESMb is too heavy for 2 CPU cores and creates a method-switch confound. | Running ESMb on 2 CPU cores would exceed the 4h runtime limit. A physics-based proxy (hydrophobicity) is used as the **standard, uniform** method for all samples to ensure feasibility and eliminate bias. Spec FR-003 flagged for amendment. |
| **PCA Re-run in Permutation** | HDLSS regime requires preserving feature correlation structure in null distribution. | Permuting final reduced features without re-running PCA leads to inflated Type I errors. |
| **Ensembl Compara Mapping** | FR-015 requires ortholog mapping for non-human/mouse species. | Hardcoding ISG sets for all species is impossible; dynamic mapping is required. |
| **Pre-modeling Abort Logic** | FR-014 and FR-017 require strict abort conditions. | Delaying these checks to post-modeling would waste compute and violate spec. |
| **Fixed k-mer Order (3,4)** | N < 100 strains vs P > 10,000 k-mers creates an underdetermined system. | Including k=5,6 would make the problem unsolvable without extreme regularization that destroys interpretability. Fixed reduction to k=3,4 is the only viable CPU-tractable path. |
| **Ortholog/ISG Validation** | FR-015 and FR-002 require valid scores. | Silent failure on missing genes would produce invalid PCA results. Explicit checks are mandatory. |
| **VIF Diagnostic Only** | Debiased Lasso requires a fixed feature set for valid inference. | Dynamically excluding features based on VIF introduces post-selection bias, invalidating p-values. VIF is now strictly for reporting collinearity. |