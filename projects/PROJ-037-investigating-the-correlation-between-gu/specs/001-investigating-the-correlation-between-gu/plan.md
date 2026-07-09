# Implementation Plan: Investigating the Correlation Between Gut Microbiome Composition and Circadian Rhythm Disruption

**Branch**: `001-gene-regulation` | **Date**: 2026-06-30 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project investigates the associational relationship between gut microbiome composition (alpha/beta diversity) and circadian rhythm disruption (sleep duration, quality, chronotype) using publicly available datasets. The technical approach involves downloading and merging American Gut Project (AGP) 16S rRNA data with Open Humans sleep metadata, calculating diversity metrics, performing FDR-corrected correlation tests and distance-based redundancy analysis (dbRDA), and validating findings via bootstrap resampling. All analysis is constrained to CPU-only execution on GitHub Actions (limited core count and memory) to ensure reproducibility and feasibility.

**Critical Methodological Note**: This plan explicitly addresses contradictions between the specification and scientific best practices identified by the methodology panel. Specifically:
1.  **FR-003 (Alpha-Beta Correlation)**: The spec mandates reporting the correlation between alpha and beta diversity. The plan identifies this as tautological (invalid validation) and will report it as a methodological limitation rather than a success metric.
2.  **SC-002 (Bootstrap CIs)**: The spec requires CIs to *exclude* zero for success. The plan corrects this to accept CIs including zero as valid negative results.
3.  **FR-004 (Diet Timing)**: The spec mandates adjusting for "diet timing," which is unavailable in AGP. The plan substitutes "diet type" and flags the spec for correction.
4.  **FR-004 (PERMANOVA)**: The spec mandates PERMANOVA for all beta diversity. The plan restricts PERMANOVA to categorical sleep variables and uses dbRDA for continuous ones.
5.  **ID Bridging**: The plan acknowledges that direct ID merging between AGP and Open Humans is often impossible without a specific bridging key. The pipeline will halt with N=0 if IDs do not match, preventing false progression.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn`, `scipy`, `statsmodels`, `biom-format`, `skbio`, `numpy`, `matplotlib`, `seaborn`
**Storage**: Local file system (CSV/TSV intermediate files); no external database.
**Testing**: `pytest` (unit tests for data ingestion, statistical assertions).
**Target Platform**: Linux (GitHub Actions runner).
**Project Type**: Computational biology research pipeline.
**Performance Goals**: Complete full pipeline (ingestion, analysis, validation) within 6 hours on N=200 sample. *Note: If N > 200, the pipeline will automatically sample to 200 to meet the 6-hour constraint unless overridden.*
**Constraints**: No GPU; no large language model inference; memory footprint < 7 GB; strict associational framing (no causal claims).
**Scale/Scope**: Single cohort analysis (Target N ~; Realistic expectation N < 200 due to merge constraints).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`; external datasets fetched from canonical sources (AGP/Open Humans) on every run. |
| **II. Verified Accuracy** | **Conditional** | All dataset citations restricted to the "Verified datasets" block. *Note: The block is currently empty for AGP/Open Humans. The implementation must manually verify URLs before execution.* |
| **III. Data Hygiene** | **Compliant** | Checksums recorded in state file; raw data preserved; transformations produce new files. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **Compliant** | Artifacts carry content hashes; state file updated on changes. |
| **VI. Cohort Matching** | **Conditional** | Pipeline explicitly filters for participants with BOTH microbiome and sleep data (N ≥ 200 target). *Note: Success is conditional on ID bridging; if IDs do not match, N=0 and the study halts.* |
| **VII. Confounder Control** | **Conditional** | GLM/dbRDA models adjust for age, BMI, diet *type*, medication, antibiotic history. *Note: "Diet timing" from spec is unavailable; plan uses "diet type" and flags this spec error.* |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-037-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/                  # Downloaded raw data (AGP, Open Humans)
│   ├── processed/            # Merged, cleaned cohort
│   └── outputs/              # Analysis results, figures
├── code/
│   ├── __init__.py
│   ├── ingestion.py          # Data download, merge, filter (FR-001)
│   ├── diversity.py          # Alpha/Beta diversity calc (FR-002)
│   ├── analysis.py           # Correlation, dbRDA, GLM (FR-003, FR-004)
│   ├── viz.py                # Heatmaps, PCoA (FR-005)
│   ├── validation.py         # Bootstrap, sensitivity (FR-006, FR-007)
│   └── report.py             # Final report generation (FR-008)
├── tests/
│   ├── test_ingestion.py
│   ├── test_analysis.py
│   └── test_validation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure selected. The pipeline is linear (Ingestion → Analysis → Validation → Report) and fits within a single Python package. No backend/frontend split is required as the output is a static report and data files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope is well-bounded by the spec and constitution. | N/A |

## Power Analysis & Feasibility (Methodology Panel Response)

**Concern Addressed**: Methodology panel noted N=200 is underpowered for multivariate adjustment with 5+ confounders.

**Plan Adjustment**:
1.  **Baseline**: The pipeline targets N=200.
2.  **Power Flag**: If N < 200, the report will explicitly state "Power Limitation: Sample size N < 200 reduces ability to detect small effect sizes after adjustment."
3.  **Bootstrap**: If N < 40, bootstrap resampling is skipped (as per FR-006), and the report flags "Insufficient sample size for resampling."
4.  **Result Interpretation**: Non-significant results (CI includes zero) are reported as valid negative findings, not study failures.

## Spec Contradictions & Mitigations

| Spec Item | Issue | Plan Mitigation | Status |
| :--- | :--- | :--- | :--- |
| **FR-003** | Mandates correlation between Alpha and Beta diversity (tautological). | Plan removes this as a validation step. Reports it as a "Methodological Limitation" in the final report. | **Spec Error (Flagged)** |
| **SC-002** | Requires CIs to *exclude* zero for success. | Plan updates success logic: CIs including zero are valid negative results. | **Spec Error (Flagged)** |
| **FR-004** | Mandates adjustment for "diet timing" (unavailable in AGP). | Plan uses "diet type" (available) and flags "diet timing" as missing. | **Spec Error (Flagged)** |
| **FR-004** | Mandates PERMANOVA for all sleep variables (invalid for continuous). | Plan uses dbRDA for continuous variables, PERMANOVA only for categorical groups. | **Spec Error (Flagged)** |
| **Assumptions** | Assumes "chronotype" variable exists in Open Humans dataset. | Plan explicitly states this is unverified. If missing, the pipeline halts with "Variable Missing" error. | **Conditional** |
| **ID Bridging** | Assumes direct ID merge is feasible. | Plan halts with N=0 if IDs do not match. Requires explicit bridging key or manual reconciliation. | **Critical Risk** |