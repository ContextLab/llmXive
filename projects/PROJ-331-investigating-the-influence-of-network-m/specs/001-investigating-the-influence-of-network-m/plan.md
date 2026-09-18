# Implementation Plan: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

**Branch**: `feature/motif-rsfc` | **Date**: 2026-06-27 | **Spec**: `specs/feature/motif-rsfc/spec.md`
**Input**: Feature specification from `specs/feature/motif-rsfc/spec.md`

## Summary

This project implements a reproducible pipeline to investigate whether specific 3-node network motif configurations in structural brain connectomes constrain individual variation in resting-state functional connectivity (rsFC). The approach involves downloading HCP diffusion and rs-fMRI data, constructing Schaefer-100 parcellated connectomes (treated as **undirected** binary matrices), enumerating 3-node motifs (4 non-isomorphic classes) against degree-preserving null models, and correlating motif z-scores with rsFC metrics.

To address methodological rigor:
1.  **Non-linear Controls**: The regression model includes polynomial terms for global degree to capture non-linear degree-motif coupling.
2.  **Regional Correspondence**: In addition to global metrics, the analysis tests edge-level and regional correspondence to avoid aggregate-vs-aggregate circularity.
3.  **Robust Null Models**: A secondary sensitivity analysis uses a null model preserving both degree and global motif counts.
4.  **Correct Motif Count**: The plan explicitly targets the **4** non-isomorphic 3-node motifs for undirected graphs (isolated, edge, path, triangle), correcting the previous error regarding directed counts.

**Technical Context**

**Language/Version**: Python 3.11  
**Primary Dependencies**: `huggingface_hub`, `numpy`, `scipy`, `networkx`, `pandas`, `matplotlib`, `seaborn`, `reportlab`, `statsmodels`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Scientific research pipeline / CLI  
**Performance Goals**: Motif enumeration ≤ 300s per subject (2-core CPU); PDF report generation ≤ 2 minutes  
**Constraints**: ≤ 7 GB RAM, ≤ 14 GB disk; no GPU required; deterministic seeds  
**Scale/Scope**: Cohort of HCP subjects; Small-node motifs only (undirected graph assumption)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | Seeds pinned (42); `requirements.txt` will pin versions; CI fetches HCP data on every run. |
| **II. Verified Accuracy** | ✅ | All citations (HCP, Schaefer) will be validated against primary sources; no Wikipedia stats used for power analysis. |
| **III. Data Hygiene** | ✅ | Raw HCP data stored unchanged in `data/raw/`; derived matrices in `data/processed/` with checksums. |
| **IV. Single Source of Truth** | ✅ | All figures/stats in PDF trace to `data/processed/` and `code/`. |
| **V. Versioning Discipline** | ✅ | Content hashes tracked in `state/`; `updated_at` timestamps managed by agent. |
| **VI. Structural Data Integrity** | ✅ | HCP structural matrices stored raw; binary parcellation derived with provenance metadata. |
| **VII. Statistical Transparency** | ✅ | Scripts record exact test params, seeds, and versions; p-values and plots in PDF. |

## FR/SC Traceability

| Requirement | Plan Element | Notes |
| :--- | :--- | :--- |
| **FR-001** (Download) | Task T002: Data Ingestion | Downloads HCP data for a subset of IDs. |
| **FR-002** (Structural) | Task T004: Parcellation | Generates binary adjacency matrices. |
| **FR-003** (rsFC) | Task T005: Functional Calc | Computes correlation matrices & efficiency. |
| **FR-004** (Motifs) | Task T006: Motif Quant | Enumerates 3-node motifs (4 types, undirected). |
| **FR-005** (Correlation) | Task T007: Stats | Multivariate regression (with polynomial terms), Bonferroni, VIF check. |
| **FR-006** (Permutation) | Task T007: Stats | Permutation test for significant motifs. |
| **FR-007** (Report) | Task T008: Reporting | Generates PDF with plots & disclaimer. |
| **FR-008** (Logging) | Task T017: Utils/Logging | `pipeline.log` with all steps/errors. |
| **FR-009** (Disclaimer) | Task T008 | "Associational only" string in PDF. |
| **FR-010** (Power) | Task T007 | Power analysis module in report. |
| **SC-001** (Success) | Task T002 (Skip Logic) | **Explicitly maps to SC-001**: Checks `actual >= 0.95 * target`; logs warning if missed but continues. |
| **SC-002** (Motif Time) | Task T006 | Timeout logic for >300s. |
| **SC-003** (Corr Calc) | Task T007 | Computes for all motifs regardless of sig. |
| **SC-004** (PDF Speed) | Task T008 | Report generation < 2 mins. |
| **SC-005** (Power Report) | Task T007 | Report includes detectable effect size. |

## Project Structure

### Documentation (this feature)

```text
specs/feature/motif-rsfc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (generated in this response)
│   ├── dataset.schema.yaml
│   ├── output.schema.yaml
│   ├── motif_profile.schema.yaml
│   ├── analysis_results.schema.yaml
│   ├── results.schema.yaml
│   └── structural_connectome.schema.yaml
└── tasks.md             # (Content of Task List below)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configs, seeds, paths
├── data_loader.py       # HCP download & preprocessing
├── motif_analysis.py    # Subgraph enumeration & z-score calc
├── correlation_analysis.py # Multivariate regression, Bonferroni, permutation
├── report_generator.py  # PDF generation
├── utils.py             # Logging, validation helpers
└── main.py              # Orchestration script

tests/
├── unit/
│   ├── test_motif.py
│   └── test_correlation.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # HCP downloads (checksummed)
├── processed/           # .npy matrices, motif profiles
├── logs/
│   └── pipeline.log
└── manifest.json        # Cohort status

results/
└── results.pdf
```

**Structure Decision**: Single project structure (Option 1) chosen for scientific pipeline simplicity. Direct script execution preferred over complex CLI for this stage.

## Task List

| ID | Task | Description | Deliverable | FR/SC Link |
| :--- | :--- | :--- | :--- | :--- |
| **T001** | Directory Setup | **Active Task**. Create `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/logs/`, `results/`, `state/`. Create placeholder `__init__.py` and `.gitkeep` files. | Folders created | FR-001, FR-008 |
| **T002** | Data Ingestion & Validation | Download HCP data for IDs; skip missing subjects; write `manifest.json`. **Validation Logic**: Check `actual_count >= 0.95 * target` (SC-001). If met, success. If not, log warning but continue. | `data/processed/` files, `manifest.json` | FR-001, SC-001 |
| **T003** | Linting Config | **Active Task**. Add `.flake8` and `pyproject.toml` (Black settings). | Config files | FR-008 (Quality) |
| **T004** | Parcellation | Apply Schaefer-100 to diffusion; generate binary adjacency. | `structural.npy` | FR-002 |
| **T005** | Functional Calc | Compute rsFC matrices & global efficiency. | `rsfc.npy`, `efficiency.csv` | FR-003 |
| **T006** | Motif Quant | Enumerate 3-node motifs (undirected, **4 types**: isolated, edge, path, triangle); compute z-scores against degree-preserving null. | `motif_profile.json` | FR-004, SC-002 |
| **T006b** | Secondary Null Model | Run sensitivity analysis using a null model that preserves both degree and global motif counts to test robustness of z-scores. | `motif_sensitivity.json` | FR-004 |
| **T007** | Stats Analysis (Global) | **Multivariate regression** (GLM) with motif z-scores + **polynomial terms** for global degree. Control for structural global degree. **VIF Check**: If VIF > 5, switch to Ridge Regression. Bonferroni correction. Permutation test. Power analysis (N=50, Power=0.80). | `correlation_results.json` | FR-005, FR-006, FR-010 |
| **T007c** | Stats Analysis (Regional) | Compute regional correspondence: Correlate motif density in specific sub-networks (e.g., default mode) with local rsFC strength. Compute edge-level mapping. | `regional_results.json` | FR-005 |
| **T008** | Reporting | Generate PDF with plots, disclaimer, power analysis, and regional results. | `results/results.pdf` | FR-007, FR-009, SC-004, SC-005 |
| **T009** | Data Model | **Active Task**. Define entities, relationships, and file formats. Generate `data-model.md`. | `data-model.md` | FR-008 (Structure) |
| **T010** | Contract Tests | Write tests to validate schemas against generated data. | `tests/contract/` | FR-008 (Validation) |
| **T017** | Utils/Logging | **Active Task**. Implement `utils.py` with explicit validation: `seed=42`, `bonferroni_alpha` (calculated as 0.05/num_motifs), `vif_threshold=5`, `permutation_count=1000`. Log all steps to `data/logs/pipeline.log`. | `utils.py`, `pipeline.log` | FR-008, FR-010 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected. | N/A |

## Addressing Unresolved Panel Concerns

**Concern**: Task T008_validate raises an error if the manifest count does not match `config.EXPECTED_COHORT_SIZE`.
**Resolution**: **Task T002** explicitly implements the "skip-on-missing" strategy. It validates the *presence* of files for requested IDs, logs warnings for missing subjects, and proceeds with the available subset. The `EXPECTED_COHORT_SIZE` (50) is a target. The `manifest.json` records the *actual* processed count. The validation step checks `actual_count >= 0.95 * target` (SC-001) as a *success criterion* for the pipeline, not a hard error. If the threshold is not met, the pipeline logs a warning but continues to generate the report. This directly satisfies SC-001.

**Concern**: Methodology risks residual confounding (degree vs. motifs) and multicollinearity.
**Resolution**: **Task T007** mandates **multivariate regression** (GLM) with **polynomial terms** for global degree (e.g., degree^2) to capture non-linear coupling. If VIF > 5, the model switches to **Ridge Regression** (L2 regularization). Additionally, **Task T006b** runs a sensitivity analysis with a more constrained null model. The report includes a "Limitations" section acknowledging that non-linear degree-motif coupling may not be fully removed by linear controls, but the methodology now actively attempts to mitigate it.

**Concern**: Power analysis limitation (N=50, Bonferroni).
**Resolution**: **Task T007** explicitly calculates the minimum detectable effect size (r > 0.45) and includes this in the PDF report. The report interprets non-significant results as "insufficient power to detect effects smaller than r=0.45" rather than "no effect".

**Concern**: Undirected vs. Directed graph ambiguity.
**Resolution**: Committed to **undirected** binary matrices for this iteration. The null model is explicitly the **undirected degree-preserving Maslov-Sneppen** rewiring algorithm. The plan now correctly identifies **4** non-isomorphic 3-node motifs for undirected graphs (isolated, edge, path, triangle), correcting the previous error of citing 13 (which applies to directed graphs).

**Concern**: Task List missing explicit mapping to FRs.
**Resolution**: The Task List above explicitly maps every T001-T017 to the corresponding FR/SC. T001, T003, T009, and T017 are active tasks (not rejected) to satisfy FR-001, FR-008, etc.

**Concern**: Temporal inconsistency of `contracts/`.
**Resolution**: The `contracts/` directory is generated **in this response** (Phase 1 output) and is part of the current plan artifact.

**Concern**: Validation parameters deferred to `utils.py`.
**Resolution**: **Task T017** explicitly lists the validation parameters (`seed=42`, `bonferroni_alpha`, `vif_threshold=5`, `permutation_count=1000`) in the plan text.

**Concern**: Circular dependency in outcome variable (global efficiency).
**Resolution**: **Task T007c** adds "Regional Correspondence" and "Edge-Level Mapping" to test the hypothesis at the resolution required to claim "constraint on variation," avoiding the aggregate-vs-aggregate circularity. The global degree control variable is explicitly defined as the **structural** graph's degree, not the functional graph's, to avoid tautology.