---
description: "Task list template for feature implementation"
---

# Tasks: Solvent Effects on Photo‑Fries Rearrangement Kinetics

**Input**: Design documents from `/specs/001-solvent-effects/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 **Create project structure** – directories: `code/`, `data/`, `tests/`, `docs/`.
- [X] T002 **Initialize a Python project** – create `requirements.txt` with pinned versions (`numpy`, `scipy`, `pandas`, `scikit-learn`, `pymc`, `statsmodels`, `pyyaml`, `rdkit`).
- [X] T002b **Add RDKit for Molecular Proxy** – pin `rdkit==2023.9.1` (or latest) in `requirements.txt`.
- [X] T003 **Configure linting and formatting** – add `ruff` and `black` configuration to `pyproject.toml`.
- [X] T004 **Initialize random seed utility** – `code/utils/seeds.py` sets global seeds for reproducibility.
- [X] T005 **Setup structured logging** – `code/utils/logging.py` handles logging of environmental parameters.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.

- [X] T006a **Solvent Schema Definition** – `contracts/solvent.schema.yaml` (fields: name, dielectric_constant, source_id, citation_url).
- [X] T006b **Solvent Data Population** – `data/chemicals/solvents.yaml` with ≥5 solvents (cyclohexane, toluene, acetonitrile, methanol, water) and NIST dielectric constants.
- [ ] T006c **Solvent Schema Validation** – validate `solvents.yaml` against `solvent.schema.yaml`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T007 **Kinetic Trace Schema Definition** – `contracts/kinetic_trace.schema.yaml`.
- [ ] T008 **Implement Solvent Loader** – `code/data/loaders.py` reads `solvents.yaml` and returns validated records.
- [ ] T009a **Config Paths & CPU Constraints** – `code/config.py` defines paths, CPU‑only flag, and constants. Default substrate mass and integration time are set to `None` and must be overridden via a YAML config file `config.yaml` or CLI arguments.
- [~] T009b **Explicit Solvent List** – extend `code/config.py` with `EXPLICIT_SOLVENTS` list (e.g., `['water', 'methanol']`) to satisfy FR‑005 explicit‑model proportion.
- [~] T010 **Unit Test for Solvent Loader** – `tests/unit/test_loaders.py` validates dielectric constants against a versioned lookup table.
- [ ] T017c **Robust Hash Initialization** – `code/analysis/hash_manager.py` computes SHA‑256 of `solvents.yaml` and stores under `state/artifact_hashes.yaml` (key: `solvents_yaml_hash`); raises if file missing. <!-- FAILED-IN-EXECUTION: state/artifact_hashes.yaml exit=-1 -->
- [~] T014 **Environment Logging Infrastructure** – `code/analysis/environment.py` logs temperature, humidity, barometric pressure, substrate mass, and integration time per run to `data/processed/environment_logs.json`. **Dependency**: Runs after `T015f` (data capture) to obtain run IDs.
- [~] T015e **Instrument Capture Interface** – `code/data/instrument_interface.py` defines `capture_transient_data()` API; raises `NotImplementedError` if hardware absent. **Dependency**: Must be defined before `T015f`.
- [~] T015b **Real Data Ingestion (Optional)** – `code/data/ingest.py` reads transient‑absorption CSV/JSON from path `REAL_DATA_PATH` (set in `config.py`). aborts if `USE_REAL_DATA=True` and file missing.
- [~] T015c **Synthetic Data Generation (CI fallback)** – `code/data/generate_synthetic.py` creates deterministic synthetic kinetic traces (`data/raw/synthetic_traces.csv`) given a seed and output path.
- [ ] T015f **Actual Data Capture Implementation** – `code/data/capture.py` creates `Kinetic Trace` entities in `data/raw/kinetic_traces/`. Uses real data (`T015b`) when `USE_REAL_DATA=True`; otherwise calls `T015c`. Generates a unique `run_id` for each trace. **Dependency**: Depends on `T015e`, `T015b`/`T015c`, and `T013` (solvent configuration). <!-- FAILED: unspecified -->
- [~] T016 **Calibration Application** – `code/analysis/calibration.py` applies instrument calibration factors (detector response, wavelength stability) to raw traces; outputs `data/processed/calibration_record.json`.
- [~] T017a **Environmental Validation & SC‑010 Enforcement** – `code/analysis/validation.py` verifies dielectric constants against lookup table (≤2 % deviation), computes percentage of compliant runs, fails if <98 %, and flags temperature or humidity excursions beyond tolerances. Input: all entries in `data/processed/environment_logs.json`. Output: `data/processed/validation_flags.json`.
- [~] T017b **Compliance Reporting** – `code/analysis/compliance.py` aggregates validation results to produce `data/processed/compliance_report.json` (≥95 % runs within all tolerances). **Dependency**: Runs after `T017a`.

---

## Phase 3: User Story 1 – Configure and Execute Solvent Series (Priority P1)

**Goal**: Define a series of solvents spanning non‑polar to polar conditions and initiate the experimental protocol with full environmental logging.

- [~] T013 **CLI Solvent Series Configuration** – `code/main.py` CLI accepts a list of solvent names, validates that ≥5 distinct solvents are provided and that dielectric constants span a low‑to‑high range. Calls `environment.py` to generate logs for each run. **Depends on** `T006b`.

---

## Phase 4: User Story 2 – Extract Radical‑Pair Lifetime (Priority P2)

**Goal**: Process raw spectroscopic data to extract singlet‑radical‑pair intermediate lifetime via global kinetic analysis.

- [~] T021 **Joint NLME Model Definition** – `code/analysis/kinetic_fit.py` defines a Joint Non‑Linear Mixed‑Effects model (using `pymc`) for decay traces across replicates and solvents. Pre‑computes PCA‑derived Solvent Polarity Index for later correlation.
- [ ] T022 **NLME Model Execution & Lifetime Extraction** – runs the model defined in `T021`, extracts posterior means and standard deviations of lifetimes per solvent, flags outliers (> 2 σ). Outputs `data/processed/kinetic_metrics.csv`. <!-- FAILED: unspecified -->
- [ ] T025 **Threshold Sensitivity Analysis** – varies lifetime discrepancy thresholds `{0.05, 0.1}` ns, computes false‑positive and false‑negative rates against a synthetic ground truth (mean lifetime of replicates). Generates `data/processed/sensitivity_analysis.csv`.
- (T023 Outlier Flagging is now integrated into `T022` and therefore omitted.)

---

## Phase 5: User Story 3 – Correlate Solvation Energy with Kinetic Lifetimes (Priority P3)

**Goal**: Correlate computed solvation free energies with experimentally determined lifetimes using associational inference.

- [~] T059a **Study Design Definition** – `code/analysis/power.py` defines static design (`n ≥ 3` replicates per solvent, ≥5 solvents, placeholder effect size). Outputs `data/processed/study_design.yaml`.
- [ ] T059b **Run Power Analysis** – executes the design from `T059a` and writes `data/processed/study_power_analysis.json` (methodology, sample size, effect‑size status = 'deferred'). <!-- FAILED-IN-EXECUTION: code/run_power_analysis.py exit=1 -->
- [ ] T029a **DFT Data Fetching (Implicit)** – loads pre‑computed implicit‑solvent DFT results from `data/compute/dft_results.csv`. If absent, raises `ConfigurationError`.
- [ ] T029d **Explicit Solvent Model Computation (CPU Proxy)** – uses RDKit to generate a 3‑D geometry of phenyl benzoate from SMILES file `data/chemicals/phenyl_benzoate.smi`, optimizes with UFF, and computes solvation free energy via GBSA. Tags rows with `model_type='explicit'`. **Justification**: CPU‑tractable proxy required by plan's feasibility constraints.
- [~] T029b **Model Partitioning & Validation** – partitions solvent list so that ≥20 % are assigned to explicit modeling (based on `EXPLICIT_SOLVENTS`). Validates count; raises `ConfigurationError` if not satisfied.
- [ ] T029c **Write Combined Solvation Table** – merges implicit and explicit results into `data/compute/solvent_solvation.csv` (`solvent_id`, `solvation_energy`, `model_type`).
- [~] T030a **PCA‑Derived Solvent Polarity Index** – `code/analysis/correlation.py` standardizes dielectric constant and solvation energy, performs PCA, and stores the first component as `solvent_polarity_index` in `data/processed/pca_index.csv`.
- [ ] T031b **VIF on Raw Variables (Diagnostic Only)** – computes Variance Inflation Factors for dielectric constant and solvation energy (pre‑PCA) to assess collinearity. Outputs `data/processed/vif_raw_scores.json`. **Note**: Diagnostic only; not used for hypothesis testing.
- [~] T032 **Multiple‑Comparison Correction** – applies Bonferroni/Holm correction to any post‑hoc pairwise tests derived from the Bayesian model (e.g., comparing solvent groups). Records family‑wise error rate in `data/processed/correlation_results.json`.
- [ ] T030b **Bayesian Hierarchical Model Execution & Reporting** – implements the **correlation analysis** required by **US-3** and **SC-003** using a **Bayesian Hierarchical Model** (as mandated by the plan for low-N handling). Uses the PCA-derived index as predictor for lifetimes. Produces `data/processed/correlation_results.json` containing posterior slope, R², credible intervals, and p‑value equivalents. Ensures all findings are labeled `"associational"` in metadata.
- [~] T033 **Associational Framing Enforcement** – verifies that all JSON outputs contain a `"framing": "associational"` field; aborts if missing.
- [ ] T034 **Figure Generation & Artifact Copy** – creates regression plot `paper/figures/regression_plot.png` from Bayesian results and copies `correlation_results.json` into paper assets. Caption includes `"associational"` tag.

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [~] T035 **Instrument Registry** – `code/analysis/instrument_registry.py` loads instrument configuration from `data/chemicals/instrument_config.yaml` (or defaults) and writes `data/processed/instrument_config.json`.
- [ ] T045 **Calibration Protocol** – `code/analysis/calibration_protocol.py` loads standards from `data/chemicals/calibration_standards.yaml`, records detector response curves, calculates detection limits, and writes per‑run certificates to `data/processed/calibration_certificates/`. **Includes verification step** to ensure certificates meet FR-004 metadata requirements before writing.
- [ ] T039 **Full Pipeline Integration Test** – `tests/integration/test_full_pipeline.py` executes the entire workflow from solvent configuration to figure generation, asserting presence and integrity of `kinetic_metrics.csv`, `correlation_results.json`, and `regression_plot.png`.
- [~] T099 **Safety Monitor & Control Loop** – `code/analysis/safety_monitor.py` monitors `environment_logs.json`; if temperature deviates > 0.5 °C or RH deviates > 2 % from targets, raises `PauseExperiment` and logs the pause reason. Integrates with main driver to halt execution.