# Implementation Plan: GC Content and Thermal Stability of Archaeal tRNA Stems

**Branch**: `001-gc-content-thermal-stability` | **Date**: 2026-06-26 | **Spec**: `specs/001-gc-content-and-thermal-stability-of-arch/spec.md`
**Input**: Feature specification from `/specs/001-gc-content-and-thermal-stability-of-arch/spec.md`

## Summary

This project investigates the correlation between Guanine-Cytosine (GC) content in tRNA stem regions and the Optimal Growth Temperature (OGT) of Archaeal species. The approach involves retrieving tRNA sequences from GtRNAdb and metadata from BacDive, parsing sequences to isolate stem regions using `RNAfold` with fallback logic, and performing statistical regression (Weighted Least Squares and robust methods) with permutation testing and Phylogenetic Independent Contrasts (PIC) where data permits. The analysis is constrained to CPU-only execution on GitHub Actions, prioritizing statistical rigor (multiple-comparison correction, power acknowledgment, collinearity handling) and reproducibility.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `requests`, `biopython`, `statsmodels`, `dendropy` (for PIC/tree handling), `pyyaml`, `sklearn` (for LASSO/Stepwise)
**Storage**: Local CSV/JSON artifacts under `data/`; no external database.
**Testing**: `pytest` (contract tests against schema, unit tests for parsing logic).
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).
**Project Type**: Computational Biology / Data Analysis Script.
**Performance Goals**: Complete full pipeline (download, parse, analyze, report) within 4 hours to allow for CI buffer.
**Constraints**: No GPU; no deep learning; data subset to fit available RAM; strict adherence to verified dataset URLs; no un-specified constraints on hydration (handled by scope definition).
**Scale/Scope**: Minimum 30 archaeal species; analysis of D-stem, Anticodon-stem, Acceptor-stem, etc.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and checksummed data in `data/`. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset sources to the verified list (BacDive, GtRNAdb) and mandates citation validation. |
| **III. Data Hygiene** | **PASS** | Plan includes checksum generation and derivation logging; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats must trace to `data/` rows; no hand-typed values in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts; versioning of database snapshots (GtRNAdb/NCBI Taxonomy). |
| **VI. Database Snapshot Discipline** | **PASS** | Plan requires recording exact GtRNAdb release date/ID in metadata. |
| **VII. Phylogenetic Independence** | **PASS** | Plan includes conditional PIC execution with explicit ultrametricization. If tree missing, permutation test is skipped, and results are explicitly framed as 'Associational' with a disclaimer that phylogenetic independence was not controlled. |

**Reviewer Feedback Integration**:
*   **Hydration/Water Activity**: Reviewers (Rosalind Franklin, Linus Pauling) noted that thermal stability depends on hydration. This project is a *computational* analysis of sequence data (GC content) vs. *observed* growth temperature (OGT). We do not perform wet-lab melting experiments; thus, "hydration conditions" are inherent in the biological context of the OGT values retrieved from literature/databases. We explicitly frame the analysis as a correlation between *sequence composition* and *environmental adaptation*, not a direct measurement of melting temperature under controlled humidity. This scope is documented in `research.md`.
*   **Sample Size**: Reviewer (Marie Curie) emphasized sample size. Plan enforces the ≥30 species threshold (FR-001) and includes power limitation acknowledgment (FR-010).
*   **Helical Parameters**: Reviewer (Linus Pauling) asked for helical parameters. The plan uses standard cloverleaf secondary structure models (fixed geometry assumptions for stem identification) rather than predicting variable helical parameters per species, which is consistent with the scope of sequence-based analysis.

## Project Structure

### Documentation (this feature)

```text
specs/001-gc-content-thermal-stability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── analysis_output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-674-gc-content-and-thermal-stability-of-arch/
├── data/
│   ├── raw/               # Downloaded raw files (checksummed)
│   ├── processed/         # Cleaned CSVs, derived features
│   └── metadata.json      # Database versions, checksums
├── code/
│   ├── __init__.py
│   ├── download.py        # Fetches data from GtRNAdb/BacDive; validates against dataset.schema.yaml
│   ├── parse.py           # Cloverleaf parsing (RNAfold), GC calc
│   ├── analyze.py         # Regression (WLS, LASSO), PIC, Permutation; validates against analysis_output.schema.yaml
│   ├── utils.py           # Logging, validation helpers
│   └── main.py            # Orchestration script
├── tests/
│   ├── contract/          # Schema validation tests
│   ├── unit/              # Parsing logic tests
│   └── integration/       # End-to-end pipeline tests
├── requirements.txt       # Pinned dependencies
└── paper/                 # Draft manuscript (generated from results)
```

**Structure Decision**: Single project structure selected. The workflow is linear (Download → Parse → Analyze → Report) and fits within a single Python package. No separate frontend/backend is required as this is a batch processing research tool.

**Contract Validation Integration**:
- `download.py` MUST validate the downloaded and merged data against `contracts/dataset.schema.yaml` before proceeding to analysis.
- `analyze.py` MUST validate its final output against `contracts/analysis_output.schema.yaml` before writing to `data/results/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Phylogenetic Control (PIC)** | Required by Constitution Principle VII and FR-007 to address non-independence of species data. | Ignoring phylogeny would violate the constitution and invalidate statistical claims for evolutionary biology studies. |
| **Multiple-Comparison Correction** | Required by FR-005 as multiple stem types are tested. | Uncorrected p-values inflate Type I error rates, violating statistical rigor (SC-002). |
| **Permutation Test** | Required by FR-006 to validate significance without assuming normality. | Standard parametric tests may be invalid with small sample sizes (n≥30) or non-normal distributions. |
| **Weighted Regression (WLS)** | Required to address heteroscedasticity when aggregating tRNA types per species (methodology-f77cf667). | Simple OLS on species means ignores the varying reliability (tRNA_count) of those means. |
| **Composite Metric & LASSO** | Required to handle collinearity of stem types and identify drivers (scientific_soundness-80b98998). | Treating stems as independent tests inflates Type I error; descriptive stats alone do not answer "which stem?". |
| **Ultrametricization** | Required for valid PIC contrasts (scientific_soundness-0e504e6e). | Non-ultrametric trees yield mathematically invalid contrasts. |
| **Stratified Permutation** | Required to respect phylogenetic structure in null generation (scientific_soundness-7b94746f). | Standard permutation ignores phylogenetic non-independence. |

## Methodology (High Level)

1.  **Data Retrieval & Preprocessing**:
    -   **Download**: Fetch tRNA sequences for Archaeal species from GtRNAdb.
    -   **Metadata**: Load OGT from verified BacDive CSV. Fuzzy match species IDs (Levenshtein > 0.9). Fallback to GTDB/Literature if match fails.
    -   **Parsing**: Use `RNAfold` (MFE, partition function) to predict structure. Fallback to coordinate-based parsing if prediction fails or deviates from cloverleaf.
    -   **Feature Engineering**: Calculate GC% for each stem. Compute **Composite Stem GC** (mean of all stems) and individual stem GCs. Count `tRNA_count` per species.
    -   **Filtering**: Exclude species with missing OGT or incomplete stems. Target: ≥30 valid species.

2.  **Statistical Analysis**:
    -   **Primary Model**: Weighted Least Squares (WLS) of OGT ~ Composite Stem GC, weighted by `tRNA_count`.
    -   **Secondary Model**: LASSO regression to identify significant stem types (penalizing collinearity).
    -   **Metrics**: Pearson r, p-value, 95% CI.
    -   **Multiple Comparisons**: Benjamini-Hochberg for per-stem descriptive stats (not independent tests).
    -   **Validation**:
        -   **If Tree Available**: Compute PIC (tree ultrametricized via `dendropy`). Run stratified permutation (min clade size).
        -   **If No Tree**: Skip permutation. Flag results as "Associational" with explicit disclaimer that phylogenetic independence was not controlled.
    -   **Power**: Calculate Minimum Detectable Effect Size (MDES) using observed variance, alpha=0.05, power=0.80.

3.  **Sensitivity & Reporting**:
    -   **Sensitivity**: Sweep thresholds (low, medium, high nt) and methods (WLS, Huber).
    -   **Tree Subset**: Exclude species not in tree from PIC; report subset N and potential bias.
    -   **Output**: JSON report with all stats, flags, and MDES.