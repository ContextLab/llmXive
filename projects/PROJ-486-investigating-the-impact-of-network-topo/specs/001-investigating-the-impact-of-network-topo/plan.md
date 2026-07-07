# Implementation Plan: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Branch**: `001-network-topology-entrainment` | **Date**: 2026-06-28 | **Spec**: `specs/001-investigating-the-impact-of-network-topo/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-impact-of-network-topo/spec.md`

## Summary

This feature implements a computational pipeline to investigate the association between resting-state brain network topology (Clustering Coefficient, Characteristic Path Length) and neural entrainment strength (Phase-Locking Values) using Human Connectome Project (HCP) data. The system downloads fMRI data, constructs weighted correlation networks, computes topological metrics, correlates them with external entrainment metrics, and applies Bonferroni correction for multiple comparisons.

**Critical Data Constraint**: The pipeline **MUST** halt with a "Data Gap" error if the verified datasets do not contain the specific variables required for the hypothesis (i.e., fMRI time-series/matrix AND entrainment metrics derived from *rhythmic stimuli*). **Synthetic data is strictly for unit testing logic and code validity; it CANNOT be used to generate scientific results or claim hypothesis validation.**

The pipeline includes robustness checks via alternative parcellation schemes (AAL, Power 264) and strictly adheres to CPU-only, free-tier CI constraints (limited cores, constrained RAM, 6h runtime).

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `networkx`, `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `huggingface_hub`, `nibabel`, `requests`.  
**Storage**: Local ephemeral storage on GitHub Actions runner (data downloaded, processed, and discarded; no persistent DB).  
**Testing**: `pytest` with unit tests for metric calculation and integration tests for the full pipeline on a small subset.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational research pipeline (CLI/Script).  
**Performance Goals**: Complete full pipeline (download, process 100+ subjects, analyze, plot) within 6 hours; memory usage < 7GB.  
**Constraints**: No GPU; no large model training; dataset must be sampled or processed in chunks to fit RAM; strict adherence to FR-007/FR-008 validation.  
**Scale/Scope**: A subset of HCP participants will be recruited for the study. with matching entrainment data. If the full HCP S1200 (N=1200) is attempted, chunking is required, but the primary analysis targets the smaller matched subset to ensure RAM safety.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan mandates pinned `requirements.txt`, random seed setting in all stochastic steps (e.g., data sampling, if any), and deterministic processing of external datasets.
- **II. Verified Accuracy**: All dataset URLs in `research.md` are sourced strictly from the "Verified datasets" block. **Crucially**, if the verified datasets do not contain the required variables, the pipeline halts. Synthetic data is used **only** for logic validation (unit tests) and does not produce scientific results, thus not violating the requirement for verified sources for claims.
- **III. Data Hygiene**: The plan includes a checksum step for downloaded files and enforces "read-only" raw data handling. Derived metrics are written to new files.
- **IV. Single Source of Truth**: All statistics in the final report are generated programmatically from the `data/` artifacts. No manual entry.
- **V. Versioning Discipline**: The plan includes content hashing for `code/` and `data/` artifacts. **Hashes are recorded in `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml`** to trigger state updates, and a local `checksums.json` is maintained as a cache.
- **VI. Statistical Rigor & Correction**: The plan explicitly includes Bonferroni correction for N=2 tests (FR-004) and VIF calculation for collinearity (FR-004). It also acknowledges the mathematical coupling of metrics and restricts interpretation accordingly.
- **VII. Multimodal Data Alignment**: The plan includes a strict inner-join step on Subject ID with logging for mismatches (Edge Case: Data Mismatch) and validation of column presence (FR-007/FR-008), including a specific check for "rhythmic stimulus" metadata.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-topology-entrainment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-486-investigating-the-impact-of-network-topo/
├── code/
│   ├── __init__.py
│   ├── config.py              # Configuration (atlas selection, paths)
│   ├── data_loader.py         # HCP & Entrainment data ingestion
│   ├── network_metrics.py     # Clustering Coeff, Path Length, VIF
│   ├── analysis.py            # Correlation, Bonferroni, Visualization
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded raw files (parquet/csv)
│   ├── processed/             # Derived metrics (CSV)
│   └── checksums.json         # File integrity records
├── tests/
│   ├── unit/
│   │   ├── test_network_metrics.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── ...
└── requirements.txt
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) is selected to minimize overhead for a computational research pipeline. This aligns with the "library/cli" pattern suitable for scientific scripting.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The project scope is narrow (correlation of two metrics). | A complex microservice or multi-repo structure would add unnecessary CI/CD overhead for a single-run analysis. |

## Data Gap Handling Protocol

If the "Verified Datasets" do not contain the required variables (HCP S1200 connectivity, Entrainment PLV from rhythmic stimuli):
1.  **Log**: "Data Gap: Required variables not found in verified datasets."
2.  **Halt**: The pipeline exits with code 1. **No correlation analysis is performed.**
3.  **No Synthetic Results**: The system does not generate a "scientific result" using synthetic data. Synthetic data is only used in unit tests (`tests/unit/`) to verify the *logic* of the correlation and plotting code, not the *hypothesis*.

## Success Criteria for Data Availability

- **SC-001 (Conditional)**: If verified data is present, measure association. If not, report "Data Gap" and halt.
- **SC-004**: The pipeline (including download and validation) completes within 6 hours. If data is missing, the pipeline halts immediately (<5 mins), satisfying the constraint.
- **SC-005 (Fallback)**: If data is missing, the system **MUST** halt with the error "Invalid Entrainment Data" or "Data Gap" as defined in FR-007/FR-008. This state is considered a **Pipeline Success** (valid execution path) even though it does not yield a scientific association (SC-001).

## Fallback Success Criteria (Addressing SC-001 Data Gap)

In the event that the verified datasets lack the specific variables required for SC-001 (real-world association):
1.  **System Behavior**: The pipeline executes the validation logic, detects the missing variables, and halts with a structured error message and a `data_gap_report.json` artifact.
2.  **Success Definition**: This outcome is defined as a **Pipeline Success** because it fulfills FR-007 (validation) and FR-008 (input validation) and SC-005 (input data validity).
3.  **Scientific Outcome**: The study reports that SC-001 (scientific association) is **unmeasurable** due to data unavailability, rather than failing to execute. This distinguishes between "system failure" and "scientific null due to data absence."
4.  **Documentation**: The final report will explicitly state: "Hypothesis SC-001 untestable: Verified datasets lack 'rhythmic stimulus' entrainment metrics. Pipeline executed successfully with Data Gap protocol."

This fallback ensures the system meets its functional requirements (FR-007, FR-008) and success criteria for pipeline execution (SC-004, SC-005) even when the scientific hypothesis (SC-001) cannot be tested.