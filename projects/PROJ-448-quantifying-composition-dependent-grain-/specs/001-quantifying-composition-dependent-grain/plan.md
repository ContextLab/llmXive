# Implementation Plan: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Branch**: `001-quantifying-grain-boundary-segregation` | **Date**: 2026-07-26 | **Spec**: `specs/001-quantifying-grain-boundary-segregation/spec.md`
**Input**: Feature specification from `specs/001-quantifying-grain-boundary-segregation/spec.md`

## Summary

This feature implements a computational pipeline to quantify grain boundary (GB) segregation in BCC Fe-based alloys (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W). The approach integrates three distinct computational layers: (1) extraction of equilibrium phase compositions from an open CALPHAD parameter set (derived from literature), (2) calculation of segregation energies using pre-computed DFT values from cited literature sources and the McLean isotherm model, and (3) statistical analysis of multicomponent cooperative effects via linear regression with interaction terms.

The pipeline addresses the scientific gap regarding non-linear cooperative segregation by comparing multicomponent regression models against additive binary baselines, validated through cross-validation. The implementation explicitly separates **Pipeline Validation** (using synthetic data with injected ground truth to verify the regression engine) from **Scientific Discovery** (using literature-parameterized data).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen` (structure generation), `ase` (atomic simulation environment), `scikit-learn` (regression/CV), `pandas` (data manipulation), `numpy`, `matplotlib` (visualization), `requests` (data fetching), `pyyaml` (manifest).  
**Storage**: Local `data/` directory for downloaded CALPHAD parameters, pre-computed DFT values, generated supercells (CIF/XYZ), and computed results (CSV/Parquet).  
**Testing**: `pytest` with unit tests for thermodynamic calculations and integration tests for the full pipeline.  
**Target Platform**: GitHub Actions free-tier runner (CPU-only, limited cores, 7 GB RAM).  
**Project Type**: Scientific computing library/cli.  
**Performance Goals**: Complete pipeline execution within 6 hours; memory usage < 6 GB during DFT energy extraction (using pre-computed lookups).  
**Constraints**: No local GPU; strict adherence to open-source data availability; no fabrication of DFT results (pre-computed literature values used).  

> **Note on DFT and CALPHAD Feasibility**: Full Quantum ESPRESSO DFT calculations and proprietary TCFE9 database access are not feasible on the GitHub Actions free-tier CPU runner. The implementation plan for the CI environment utilizes **pre-computed DFT segregation energy datasets from cited literature sources** (e.g., Materials Project, Zenodo) and a **Reduced CALPHAD Parameter Set derived from open literature** to satisfy the *McLean isotherm* and *regression* requirements (FR-003, FR-004) without fabricating new DFT runs. The "DFT extraction" step (FR-002) in the CI context is implemented as a data loading and validation step against the pre-computed set, ensuring the pipeline logic is correct. A separate "Research" branch will handle actual DFT runs on HPC resources if required for new physics, but the *feature* as specified for CI testing relies on verified data sources.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Reference / Justification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All dependencies pinned in `requirements.txt`. Random seeds fixed in `code/`. Data sources (Open CALPHAD, Literature DFT) referenced by URL/DOI in `data_manifest.json`. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `plan.md` verified against the `# Verified datasets` block or specific literature sources. Synthetic data is clearly marked as "Controlled Injection" for validation only. |
| **III. Data Hygiene** | **PASS** | `data/` files will be checksummed. `data_manifest.json` tracks source types and DOIs. No PII expected. |
| **IV. Single Source of Truth** | **PASS** | All results (segregation energies, regression coefficients) derived from `data/` files via `code/` scripts. No hand-typed numbers. Synthetic data is the SSoT for validation; literature data is the SSoT for physics. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts recorded in state YAML. |
| **VI. Computational Thermodynamics** | **PASS** | McLean model inputs (T, E_seg) explicitly documented. Open CALPHAD parameters consistency enforced via data validation scripts. |
| **VII. Multicomponent Interaction** | **PASS** | Regression models include interaction terms. 5-fold CV and p<0.05 thresholds implemented. Synthetic injection validates the detection capability. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-grain-boundary-segregation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── segregation_profile.schema.yaml
    ├── seg_profile.schema.yaml
    ├── alloy_system.schema.yaml
    ├── data_manifest.schema.yaml
    └── regression_model.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-448-quantifying-composition-dependent-grain-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py                 # Paths, seeds, constants
│   ├── data/
│   │   ├── download_calphad.py   # Open CALPHAD fetcher
│   │   ├── load_dft_energies.py  # Literature DFT loader
│   │   ├── fetch_apt_data.py     # APT data fetcher (T045d)
│   │   ├── manifest.py           # Data manifest generator (FR-007)
│   │   └── sources.md            # Data sources document (T006a, T045a, T045c)
│   ├── models/
│   │   ├── mclean.py             # McLean isotherm implementation
│   │   └── regression.py         # Linear regression with interactions
│   ├── services/
│   │   ├── segregation_engine.py # Orchestration of FR-001 to FR-003
│   │   ├── analysis_engine.py    # FR-004 to FR-005
│   │   └── synthetic_gen.py      # Controlled parameter injection (T047a, T047b)
│   └── cli/
│       └── run_pipeline.py       # Entry point
├── data/
│   ├── raw/                      # Downloaded CALPHAD, DFT sets, APT data
│   ├── processed/                # Segregation profiles, regression results
│   └── data_manifest.json        # FR-007 artifact
├── tests/
│   ├── unit/
│   │   ├── test_mclean.py
│   │   └── test_regression.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── quickstart.md
```

**Structure Decision**: Single project structure with modular `code/` subdirectories (`data`, `models`, `services`, `cli`) to separate I/O, physics, statistics, and orchestration. This supports the `Reproducibility` principle by isolating dependencies and the `Single Source of Truth` by centralizing data paths.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Separate `models` and `services`** | Physics (McLean) and Statistics (Regression) require distinct logic and validation. | Merging them would obscure the separation between thermodynamic calculation and empirical model fitting, violating the `Single Source of Truth` for derived metrics. |
| **Pre-computed DFT Data** | CI runner lacks GPU and time for full DFT. | Running full DFT on CI would fail the `Compute feasibility` constraint (6h limit, no GPU). Using a literature-parameterized surrogate allows testing the *pipeline logic* (FR-003, FR-004) without fabricating physics. |
| **Synthetic Injection** | To validate the regression engine's ability to detect non-linearity. | Without injected ground truth, the pipeline cannot be proven to work before applying it to extrapolated physics. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation (FR-001, FR-002, FR-007, T006a, T045a, T045c, T045d)

1.  **Download Open CALPHAD Parameters**: Fetch the Reduced CALPHAD Parameter Set from the cited open literature source (e.g., specific Zenodo record or NIST database) and store in `data/raw/calphad_params.json`.
2.  **Load Pre-computed DFT Energies**: Load DFT segregation energies for binary systems (Fe-Cr, Fe-Mo, etc.) from the cited literature source (e.g., Materials Project ID or Zenodo dataset) and store in `data/raw/dft_energies.json`.
3.  **Fetch APT Data**: Implement `fetch_apt_data.py` to download APT datasets from HuggingFace/Zenodo (T045d). Log success/failure.
4.  **Generate Data Manifest**: Create `data_manifest.json` (FR-007) and `research/data_sources.md` (T006a) with `source_id`, `doi`, `url`, `status` for all sources.
5.  **Verify APT Accession IDs**: Record NIST APT accession IDs for Fe-Cr, Fe-Mo, Fe-V, Fe-W in `research/data_sources.md` (T045a).
6.  **List Ternary APT Sources**: List peer-reviewed literature sources (DOIs) for ternary APT datasets in `research/data_sources.md` (T045c). If none exist, explicitly state "No verified ternary APT data found".

### Phase 0.5: Synthetic Data Generation (Controlled Injection)

1.  **Generate Synthetic Dataset**: Create a dataset where `segregation_energy_eV` is calculated using a known non-linear function (injected ground truth) for ternary systems.
2.  **Inject Interaction Terms**: Explicitly set `interaction_coefficient_truth` in the synthetic data.
3.  **Validate Engine**: Run the regression engine on this synthetic data to verify it recovers the injected coefficients (T047a, T047b).

### Phase 1: Segregation Calculation (FR-001, FR-002, FR-003)

1.  **Extract Bulk Compositions**: Use the Open CALPHAD parameters to extract equilibrium phase compositions for multiple ternary systems at elevated temperatures (FR-001). Handle missing parameters with linear extrapolation and warnings (T047a).
2.  **Compute Segregation Energies**: Use the pre-computed DFT values for binaries and extrapolate for ternaries using the Reduced CALPHAD set. Handle missing ternary parameters with linear interpolation and `NO_TERNARY_DATA` flag (T047b).
3.  **Calculate Equilibrium Concentrations**: Apply the McLean isotherm model to compute GB concentrations (FR-003).

### Phase 2: Analysis & Regression (FR-004, FR-005, SC-001, SC-002)

1.  **Fit Regression Model**: Fit a linear model with interaction terms to the calculated data (FR-004).
2.  **Perform Cross-Validation**: Run k-fold CV on the combined dataset (FR-005).
3.  **Validate Cooperative Effects**: Compare MSE of full model vs. additive model. Check for significant interaction terms (SC-001).
4.  **Report Generalizability**: Report R² and standard deviation across folds (SC-002).

### Phase 3: Validation & Visualization (SC-003, FR-006)

1.  **Align APT Data**: Extract binary segregation data from APT datasets and compare with model predictions (SC-003). Explicitly report the inability to validate ternary interactions experimentally.
2.  **Generate Heatmaps**: Create heatmaps of segregation energy vs. composition (FR-006).

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Missing CALPHAD parameters** | Use linear interpolation/extrapolation with a warning flag (T047a). |
| **Missing ternary APT data** | Report explicitly in `research/data_sources.md` and limit SC-003 validation to binary systems. |
| **Surrogate bias** | Clearly document the surrogate's source in `data_manifest.json`. The research focuses on the *methodology* of detecting non-linearity, which is robust to the specific energy values as long as they are physically plausible. |
| **Circular validation** | Separate synthetic validation (injected ground truth) from scientific results (literature data). |

## Decision Rationale

The choice to use literature-parameterized DFT and Open CALPHAD data for CI is driven by the **Compute Feasibility** constraint (no GPU, 6h limit) and the **Verified Accuracy** principle (using cited sources). The surrogate is derived from literature values (e.g., *Acta Materialia* papers on Fe-Cr segregation) and is deterministic. The **Synthetic Injection** phase ensures the pipeline can detect non-linearity, while the **Scientific Results** phase applies the pipeline to the literature-parameterized data, acknowledging the extrapolation uncertainty for ternary systems. This balances the need for a runnable CI pipeline with the requirement for real data validation.