---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Input**: Design documents from `/specs/001-network-efficiency-aging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

Include exact file paths in descriptions.

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md` structure)
- Paths shown below assume single project structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure per `plan.md`. **Explicitly create directories**: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, `state/`, `tests/`, `figures/`, `data/quality/`, `data/config/`. **Explicitly create placeholder files**: `code/__init__.py`, `data/.gitkeep`, `docs/.gitkeep`, `state/.gitkeep`, `tests/.gitkeep`, `figures/.gitkeep`, `data/quality/.gitkeep`, `data/config/.gitkeep`. **Dep**: None.
- [X] T002 [P] Initialize Python 3.11 project with virtualenv and `requirements.txt` (MNE, NetworkX, SciPy, Pandas, Statsmodels, PyWavelets).
- [ ] T003 [P] Configure linting and formatting tools. **Deliverables**: Create `.ruff.toml` (rules: E501, W291, F401; max-line-length=88) and `pyproject.toml` (black config: line-length=88, target-version=py311). **Verification**: Run `ruff check code/` and `black --check code/` with 0 errors. **Dep**: T001.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note on FR-003**: The plan implements 'Imaginary Coherence' per ratified Design Decision T014b, which overrides the generic 'Coherence' in FR-003. The spec amendment T014d formally updates `spec.md` to reflect this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `docs/decisions/epoch_length.md`. **Content**:
 - `# Epoch Length Decision`
 - `## Rationale`: "Longer epochs provide sufficient spectral resolution for coherence estimation in the low-to-moderate frequency band, reducing variance compared to shorter epochs. This aligns with the ratified specification which mandates a defined number of **signal processing epochs**."
 - `## Impact`: "Increased epoch duration improves signal‑to‑noise ratio for connectivity metrics but reduces the number of independent epochs per recording. This is acceptable for resting‑state analysis."
 - `## Spec Reference`: Explicitly references `spec.md` which already mandates the required number of epochs.
 - **Deliverable**: Verify file exists with this structure. **Verify consistency with spec.md v1.1** to ensure no divergence. **Dep**: T001.
- [X] T014b [P] Create `docs/decisions/connectivity_metric.md`. **Content**:
 - `# Connectivity Metric Decision`
 - `## Rationale`: "Imaginary Coherence is selected over standard Coherence to mitigate volume conduction effects (field spread) which artificially inflate connectivity estimates. This is a standard practice in EEG functional connectivity analysis to ensure valid graph metrics."
 - `## Impact`: "Overrides the generic 'Coherence' requirement in FR‑003 with 'Imaginary Coherence' for scientific validity. This decision is ratified here to close the traceability gap."
 - `## Spec Reference`: Explicitly overrides FR‑003 for this project.
 - **Deliverable**: Verify file exists with this structure. **Dep**: T001.
- [X] T014c [P] **Formal Ratification**: Update `docs/decisions/` and `spec.md` references to formally ratify the 'Imaginary Coherence' deviation as a Design Decision (T014b) to satisfy traceability requirements. **Dep**: T014b.
- [X] T014d [P] **Spec Amendment**: Update `spec.md` text to explicitly reflect the 'Imaginary Coherence' deviation in FR-003, removing the ambiguity between the spec and the ratified decision. **Dep**: T014c.
- [X] T004 [P] Implement `code/config.py` to manage paths (raw, processed, results) and configuration parameters (thresholds, epoch length). **Config Note**: Set `epoch_length_sec = 10` as per `spec.md` v1.1 and `docs/decisions/epoch_length.md`. **Deliverable**: Generate the 'initial version map of all source code and data artifacts with SHA‑256 hashes' required by FR‑006. **Action**: Create `state/version_map.yaml` with initial entries for all code files AND placeholder entries for data directories (`data/raw/`, `data/processed/`, `data/results/`) with status "pending_download". **Dep**: T014, T014b.
- [X] T042d [US1] [P] Create `contracts/dataset.schema.yaml` defining the schema for input data validation (columns: participant_id, age, cognitive_instrument, cognitive_score, signal_quality). **Dep**: T001.
- [X] T025a [US2] [P] Create `data/config/cognitive_instrument_registry.yaml` with hard‑coded list of valid instruments (MMSE, MoCA) and references as per FR‑007. **Dep**: T004.

### Streaming & Data Integrity Implementation

- [X] T067a [P] Implement `code/data/download.py` streaming iterator using `mne.io.read_raw_edf` with `preload=False`. **Requirement**: Remove ALL synthetic fallback logic. If PhysioNet/TUH fetch fails, raise `RuntimeError`. Add `--verify-source` flag. **Dep**: T004.
- [X] T067b [P] Implement `code/data/validate_snr.py` to handle streamed data inputs. **Requirement**: Verify SNR calculation on chunks without full load. **Dep**: T067a.
- [X] T067c [P] Update `code/network/connectivity.py` to process epochs from streaming pipeline. **Requirement**: Handle variable-length epoch lists. **Dep**: T067a.
- [X] T067d [P] Update `code/stats/power.py` to dynamically read `actual_n` from `download_report.json`. **Dep**: T067a.
- [X] T014e [P] **Ratification**: Ratify 'Strict Real-Data Loader' and 'Streaming Iterator' as a Design Decision. **Dep**: T067a, T067b, T067c, T067d.
- [X] T014f [P] **Ratification**: Ratify 'Power Analysis Halt Threshold' (N<85 or Power<0.80) as a Design Decision. **Dep**: T004.

### Data Acquisition Prerequisites (Implementation Steps)

- [X] T005a [P] **Schema Validation**: Implement schema check in `code/data/download.py` using `contracts/dataset.schema.yaml`. **Dep**: T042d, T025a.
- [X] T005b [P] **Filtering Logic**: Implement age (>=18) and instrument validation (MMSE/MoCA) in `code/data/download.py`. **Exit Logic**: Exit 1 if `total_valid_eeg_count == 0` OR `missing_cognitive_count > 0`. **Dep**: T005a.
- [X] T005c [P] **Report Generation**: Generate `data/quality/download_report.json` with status "OK" or "BLOCKED". **Dep**: T005b.

### Data Acquisition & Validation (Orchestration)

- [X] T005 [P] **Orchestrate Download**: Depend on T005a, T005b, T005c, T067a, T014e. **Deliverable**: Execute download with strict failure policy. **Dep**: T005a, T005b, T005c, T067a, T014e.
- [X] T005_run [P] **Execute** `code/data/download.py` to generate `data/raw/` and `data/quality/download_report.json`. **Verification**: Ensure `download_report.json` exists, is non‑empty, and matches the schema. **Dep**: T005.
- [X] T005c [P] **Update Version Map**: After T005_run, update `state/version_map.yaml` with SHA‑256 hashes of all downloaded raw EDF files and `download_report.json`. **Dep**: T005_run.

### Preprocessing & Epoching

- [X] T006 [P] Implement `code/data/preprocess.py` for MNE‑Python pipeline. **Steps**:
 1. Band‑pass filter 1‑40 Hz (`mne.filter.filter_data`).
 2. ICA artifact removal (`mne.preprocessing.ICA`).
 3. Epoch into **10‑second** segments (per `code/config.py` & `docs/decisions/epoch_length.md`).
 4. Reject epochs with >50 % artifacts.
 5. Calculate SNR per epoch; flag SNR < 10 dB.
 **Dep**: T004, T067a.
- [X] T006_run [P] **Execute** `code/data/preprocess.py` to generate `data/processed/epochs/` (`*.fif`). **Verification**: Confirm epoch files exist, non‑NaN, and SNR flags are recorded in `data/quality/epoch_quality.json`. **Dep**: T006, T005_run.
- [X] T006c [P] **Update Version Map**: After T006_run, update `state/version_map.yaml` with SHA‑256 hashes of all processed epoch files. **Dep**: T006_run.

### Connectivity & Metrics

- [X] T007 [P] Implement `code/network/connectivity.py` for **Imaginary Coherence** calculation (Welch method on fixed‑duration epochs) to address volume conduction as per ratified Design Decision **T014b** (overrides FR-003). Enforce CPU‑only execution (`device='cpu'`). **Dep**: T014b, T014c, T014d, T067c.
- [X] T007_run [P] **Execute** `code/network/connectivity.py` to generate `data/processed/connectivity_matrices/` (`*.npy`). **Verification**: Confirm CPU‑only execution (SC‑001) and that adjacency matrices match the standard 10‑20 montage dimensions. **Dep**: T007, T006_run.
- [X] T008 [P] Implement `code/network/metrics.py` functions for Global Efficiency, Characteristic Path Length, Local Efficiency, Clustering Coefficient, Modularity. **Formula Constraints**:
 - Compute **Characteristic Path Length** explicitly.
 - `Global_Efficiency = 1.0 / Path_Length`.
 - `Local_Efficiency = 1.0 / mean_shortest_path(subgraph)` (subgraph‑based).
 **Dep**: T007.
- [X] T008_run [P] **Execute** `code/network/metrics.py` to generate `data/results/network_metrics.csv`. **Implementation Note**:
 - Inject `trace_id` as SHA‑256 of concatenated hashes of all input connectivity matrix files (`data/processed/connectivity_matrices/*.npy`) **plus** hashes of relevant code files (`code/network/metrics.py`, `code/network/connectivity.py`).
 - Update `state/version_map.yaml` with the new CSV hash.
 **Dep**: T008, T007_run.
- [X] T008_sweep [P] Implement `code/network/sweep_metrics.py` to re-run `code/network/metrics.py` with variable density thresholds and artifact rejection parameters for sensitivity analysis. **Dep**: T008.

### Cognitive Filtering & Validation

- [X] T025b [US2] [P] **Filter Cognitive Subset**: Create `code/stats/filter_cognitive.py` to read `data/quality/download_report.json` and `data/raw/metadata.csv` and generate `data/results/valid_cognitive_participants.csv`. **CRITICAL**: This step physically excludes invalid records. **Dep**: T005_run, T025a.
- [X] T025c [US2] [P] **Filter Network Metrics**: Create `code/stats/filter_metrics.py` to join `data/results/network_metrics.csv` (from T008_run) with `data/results/valid_cognitive_participants.csv` (from T025b) and output `data/results/network_metrics_cleaned.csv`. **CRITICAL**: Ensure NO records with invalid instruments remain. **Dep**: T008_run, T025b.
- [X] T025d [US2] [P] **Enforce Exclusion**: Create `code/stats/validate_exclusion.py` to verify that `data/results/network_metrics_cleaned.csv` contains NO records with `invalid_instrument` or `missing_cognitive` flags. **Dep**: T025c, T005_run.
- [X] T061_impl [P] **Handle Missing Scores**: Modify `code/stats/filter_cognitive.py` to log "Excluded participant {id}: Missing cognitive score" for each exclusion. **Dep**: T025b.

### Statistical Analysis

- [X] T027 [US2] [P] Implement `code/stats/power.py` to perform **Monte Carlo MDES analysis**. **Dep**: T005_run.
- [X] T027_run [US2] Execute `code/stats/power.py` → generate `power_analysis.json`. **Dep**: T027.
- [X] T027b [US2] Halt check: if `is_sufficient == false` **AND** `actual_n < 85`, log warning *“Study underpowered for cognitive analysis; skipping cognitive visualization tasks”* and skip downstream US2/US3 tasks. **Dep**: T027_run, T014f.
- [X] T009 [P] Implement `code/stats/correction.py` for Bonferroni/FDR multiple‑comparison correction.
- [X] T023 [US2] [FR-004] Implement Spearman correlation (metrics ↔ Age & Cognitive Score) with Bonferroni/FDR correction. **CRITICAL**: Consume `data/results/network_metrics_cleaned.csv`. **Dep**: T025d, T009, T027b.
- [X] T023_run [US2] Execute `code/stats/correlation.py` → generate `data/results/correlation_results.csv`. **Dep**: T023, T025d, T027b.
- [X] T028 [US2] Validate `trace_id` column exists in `correlation_results.csv`. **Dep**: T023_run.
- [X] T029 [US2] Validate output schema of `correlation_results.csv`. **Dep**: T028.
- [X] T053 [US2] Sensitivity analysis of multiple‑comparison correction methods. **Dep**: T023_run.
- [X] T031 [US3] [FR-004-SUPPLEMENT] Implement `code/stats/regression.py` (Cognition ~ Efficiency + Age + Sex + Education). **Dep**: T025d, T005_run, T027b.
- [X] T031_run [US3] Execute `code/stats/regression.py` → generate `data/results/regression_results.csv`. **Dep**: T031, T025d, T027b.
- [X] T032 [US3] Create `regression_summary.json` containing `warnings` array if power is insufficient. **Dep**: T027_run, T031_run.

### Visualization & Reporting

- [X] T033 [US3] Implement `code/viz/plots.py` to generate age‑stratified bar plots. **Dep**: T008_run.
- [X] T054 [US2] Implement visualization for correlation coefficients. **Dep**: T023_run.
- [X] T056 [US3] Implement network‑topology visualizations. **Dep**: T008_run.
- [X] T066 [P] **Visualization Alternative Task**: Compare Matplotlib vs. Plotly for topology plots. Test multiple color palettes.

The research question, method, and references remain unchanged as no specific values, citations, or empirical claims were present in the original text to alter. Output `docs/visualization_alternatives.md` with schema: `{method, palette, recommendation, rationale}`. **Dep**: T033.
- [X] T034 [US3] Generate regression table. **Dep**: T031_run, T032.
- [X] T035 [US3] Validate regression table schema. **Dep**: T034.
- [X] T036 [US3] Generate final summary report. **Dep**: T052, T027_run, T053, T018d, T032.

### Sensitivity & Validation

- [X] T016 [US1] Validate derivation: verify `network_metrics.csv` respects formula constraints. **Dep**: T008_run.
- [X] T017 [US1] Update `network_metrics.csv` to include `signal_quality_flag`. **Dep**: T008_run.
- [X] T018a [US1] Sensitivity analysis – sweep network density thresholds. **Dep**: T008_sweep.
- [X] T018b [US1] Sensitivity analysis – vary artifact‑rejection thresholds. **Dep**: T008_sweep.
- [X] T018c [US1] Aggregate sensitivity results. **Dep**: T018a, T018b.
- [X] T018d [US1] Generate consolidated sensitivity documentation. **Dep**: T018c.
- [X] T019 [US1] Validate `trace_id` column in `network_metrics.csv`. **Dep**: T008_run.
- [X] T020 [US1] Validate output schema of `network_metrics.csv`. **Dep**: T019.
- [X] T064 [US1] [FR-002] **SNR Validation Task**: Implement `code/data/validate_snr.py` to re-validate SNR calculation. **Dep**: T006.
- [X] T065 [US2] [FR-004] **Correction Sensitivity Task**: Implement `code/stats/correction_sensitivity.py`. **Dep**: T023_run.

### Reproducibility & Cleanup

- [X] T010 [P] Implement `code/state/version_map.py`. **Dep**: T001.
- [X] T011 [P] Unit test for `code/network/metrics.py`. **Dep**: T008.
- [X] T012 [P] Integration test. **Dep**: T006_run, T008_run.
- [X] T013 [US1] Validate `download.py` output. **Dep**: T005_run.
- [X] T015 [US1] Validate `connectivity.py` output. **Dep**: T007_run.
- [X] T037 [P] Documentation updates. **Dep**: T001.
- [X] T038a [P] Refactor `code/data/preprocess.py` (filter_and_ica). **Dep**: T006.
- [X] T038b [P] Refactor `code/data/preprocess.py` (epoch_data). **Dep**: T006.
- [X] T038c [P] Refactor `code/network/connectivity.py`. **Dep**: T007.
- [X] T039 [P] Performance optimization: Profile `code/main.py` using `cProfile`; ensure wall-clock time < 6h on free-tier CI. **Dep**: T001.
- [X] T040d [US1] Add unit tests. **Dep**: T004, T005, T008.
- [X] T041 Run `quickstart.md` validation. **Dep**: T001.
- [X] T058 [P] Add GitHub Actions CI workflow. **Dep**: T001.
- [X] T059 [P] Add unit tests for visualizations. **Dep**: T033.
- [X] T060 [P] Document power‑analysis methodology. **Dep**: T027_run.
- [X] T062 [P] Update `state/version_map.yaml` after every artifact generation. **Dep**: T001.
- [X] T063 [P] Create Dockerfile. **Dep**: T001.