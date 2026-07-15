# Implementation Plan: Investigating Microbial Community Succession in Constructed Wetlands

**Branch**: `001-microbial-succession` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-microbial-succession/spec.md`

## Summary

This project implements a reproducible, CPU-tractable pipeline to investigate microbial community succession in constructed wetlands using public 16S rRNA datasets. The approach involves retrieving pre-processed feature tables and metadata, filtering for samples with nitrogen/phosphorus removal metrics, calculating diversity indices, performing PERMANOVA for community differences, constructing Spearman-based co-occurrence networks, and correlating taxa with nutrient removal rates. All analyses adhere to strict memory and time constraints of free-tier CI runners.

**Critical Data Note**: The pipeline includes a strict "Data Gap" protocol. If no verified public dataset containing both 16S feature tables and N/P removal metrics is found in the allowed sources, the pipeline halts immediately. No synthetic data is generated to bypass this requirement.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-bio`, `networkx`, `statsmodels`, `seaborn`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`), JSON config (`data/config/dataset_ids.json`)  
**Testing**: `pytest` (unit tests for data loading, schema validation, statistical output integrity)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Biology / Data Analysis Pipeline  
**Performance Goals**: Complete full pipeline (download to final stats) within 6 hours on 2 CPU cores; peak RAM < 7 GB.  
**Constraints**: No GPU; no raw read processing (only pre-processed tables); strict adherence to verified dataset URLs; all statistical tests must include multiple-comparison correction and power analysis gates.  
**Scale/Scope**: Target ≥30 samples (≥10 per stage) based on literature effect sizes (R²=0.15); network construction limited to cases where n_samples ≥ n_taxa; sensitivity analysis on subsampling and correlation thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action/Justification |
|-----------|-------------------|----------------------|
| **I. Reproducibility** | ✅ Compliant | All random seeds pinned in `code/`; dataset IDs stored in `data/config/dataset_ids.json`; pipeline runs end-to-end in isolated env. |
| **II. Verified Accuracy** | ✅ Compliant | Verified URLs are required for data sources (NCBI SRA/Zenodo). Statistical methods (PERMANOVA, VIF) are standard library functions and do not require external URLs. |
| **III. Data Hygiene** | ✅ Compliant | Checksums recorded in `state/...yaml`; raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/stats trace to `data/processed` outputs; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | ✅ Compliant | Content hashes tracked; artifact updates trigger state timestamp updates. |
| **VI. Public Data Provenance** | ⚠️ Blocked | Compliance is conditional on finding a verified 16S wetland dataset. If none is found, the pipeline halts (see "Data Gap Protocol"). |
| **VII. Computational Resource Constraints** | ✅ Compliant | Subsampling logic (a limited number of reads) and library choices (`scikit-bio`, `scipy`) ensure <7GB RAM usage. |

## Project Structure

### Documentation (this feature)

```text
specs/001-microbial-succession/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-280-investigating-microbial-community-succes/
├── data/
│   ├── config/
│   │   └── dataset_ids.json       # Input: List of dataset IDs
│   ├── raw/                       # Downloaded feature tables & metadata
│   └── processed/                 # Filtered, subsampled, and analyzed data
├── code/
│   ├── 01_retrieve_data.py        # FR-001, FR-002, FR-011
│   ├── 02_preprocess.py           # FR-003, FR-015
│   ├── 03_diversity.py            # FR-004, FR-005, FR-009, FR-014
│   ├── 04_network.py              # FR-006, FR-007, FR-013
│   ├── 05_correlation.py          # FR-008, FR-010
│   ├── utils.py                   # Shared helpers (VIF, FDR, checksums)
│   └── requirements.txt           # Pinned dependencies
├── tests/
│   ├── unit/
│   └── contract/
└── state/
    └── projects/PROJ-280-investigating-microbial-community-succes.yaml
```

**Structure Decision**: Single project structure with modular scripts for each analysis phase. This minimizes overhead, ensures sequential data flow (download → preprocess → analyze), and fits within CI runner constraints.

## FR ↔ Schema Traceability

| Functional Requirement | Validating Schema Contract |
|------------------------|----------------------------|
| FR-001, FR-002, FR-011 | `contracts/dataset-config.schema.yaml` |
| FR-003, FR-015         | `contracts/feature-table.schema.yaml` |
| FR-004, FR-005, FR-009, FR-014 | `contracts/output-metrics.schema.yaml` (diversity/permanova section) |
| FR-006, FR-007, FR-013 | `contracts/network_output.schema.yaml` |
| FR-008, FR-010         | `contracts/output-metrics.schema.yaml` (correlation section) |
| Constitution Principle V | `contracts/state.schema.yaml` |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sensitivity Analysis (FR-013, FR-015)** | Required by spec to ensure robustness of network and diversity results. | Skipping sensitivity analysis would violate FR-013/FR-015 and compromise scientific validity. |
| **Under-determined Network Flag (FR-013)** | Necessary when samples < taxa. | Ignoring this would produce spurious network edges and invalid modularity comparisons. |
| **Power Analysis Gate (FR-014)** | Required to validate PERMANOVA results. | Running PERMANOVA without power check risks false positives/negatives. The pipeline halts if underpowered. |
| **Data Gap Protocol** | Ensures scientific validity by preventing analysis on non-existent data. | Using synthetic data would invalidate the research question. |

## Implementation Phases

### Phase 0: Data Validation & Retrieval
*   **Goal**: Verify existence of required data and download.
*   **Tasks**:
    1.  Load `data/config/dataset_ids.json`.
    2.  Check against verified sources list.
    3.  **Gate**: If no verified 16S wetland dataset is found, log "CRITICAL DATA GAP" and exit.
    4.  Download pre-processed 16S tables and metadata.
*   **FRs**: FR-001, FR-002, FR-011.

### Phase 1: Preprocessing & Subsampling
*   **Goal**: Filter samples and normalize read depth.
*   **Tasks**:
    1.  Filter for samples with N/P removal metrics.
    2.  Subsample to uniform depth (max a defined threshold).
    3.  **FR-015 Sensitivity**: Perform subsampling depth sweep (low, medium, high if available) to verify alpha diversity robustness.
*   **FRs**: FR-003, FR-015.

### Phase 2: Diversity & PERMANOVA
*   **Goal**: Calculate diversity and test community differences.
*   **Tasks**:
    1.  Calculate Alpha (Shannon, Simpson) and Beta (Bray-Curtis) diversity.
    2.  **FR-014 Power Analysis**: Estimate power for PERMANOVA (effect size R²=0.15).
        *   **Gate**: If power < 0.8 or n < 10/group, log "UNDERPOWERED" and halt.
    3.  Run PERMANOVA with restricted permutations.
    4.  Apply Benjamini-Hochberg FDR correction to pairwise comparisons.
*   **FRs**: FR-004, FR-005, FR-009, FR-014.

### Phase 3: Network Construction
*   **Goal**: Build co-occurrence networks and assess stability.
*   **Tasks**:
    1.  Calculate Spearman correlation matrix.
    2.  **FR-013 Under-determined Check**: If n_samples < n_taxa, flag as 'under-determined' and skip modularity calculation.
    3.  Apply threshold (|ρ|≥0.6, p≤0.01).
    4.  **FR-013 Sensitivity**: Sweep correlation thresholds to assess modularity stability.
    5.  Calculate modularity and delta (early vs. mature).
*   **FRs**: FR-006, FR-007, FR-013.

### Phase 4: Correlation & Reporting
*   **Goal**: Link taxa to nutrient removal.
*   **Tasks**:
    1.  Calculate Spearman correlation between taxa abundance and N/P removal.
    2.  Calculate VIF for predictor taxa (flag if >5).
    3.  **Note**: Correlation is treated as exploratory/descriptive only (no formal cross-validation due to n=30 constraints).
    4.  Generate final metrics report.
*   **FRs**: FR-008, FR-010.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified 16S dataset available** | Pipeline cannot run on real data. | **Data Gap Protocol**: Pipeline halts immediately. No synthetic data is generated. |
| **Sample size < 10 per stage** | PERMANOVA underpowered. | FR-014 ensures a hard stop; results are not generated. |
| **n < p (Samples < Taxa)** | Network construction invalid. | FR-013 flags as 'under-determined'; modularity comparison is skipped. |
| **Missing N/P metadata** | Cannot correlate taxa with function. | FR-002 filters out such samples; exclusion count logged. |