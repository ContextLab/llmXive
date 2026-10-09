# Tasks: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction  

**Inputs**: `spec.md`, `plan.md`, existing repository structure, reviewer feedback.  

The following task list follows the platform’s canonical format.  Checked boxes denote work that has already been completed and verified; unchecked boxes are the remaining deliverables that must be implemented and verified.  Tasks are grouped by research phase and respect data‑flow dependencies.

---  

## Phase 0 – Spec & Plan Amendments (blocking prerequisites)  

These amendments are required before any scientific code is written.  

- [ ] T001 [P] [Spec] **Create provenance files for all constitutional deviations** – `code/provenance/deviation_constitution_principle_ii.md`, `deviation_JPEG2000_folding.md`, `deviation_LALInference_Bilby.md`, `deviation_Hierarchical_Fallback.md`, `constitution_amendment_principle_vii.md`.  
  **Verification:** assert each file exists and its SHA‑256 checksum matches the recorded value in `state/projects/...yaml`.  
- [ ] T002 [P] [Spec] **Draft amendment document** – `specs/001-compression-impact-gw-reconstruction/amendment_draft.md` containing the exact replacement text for FR‑001, FR‑003, FR‑005, FR‑007, FR‑009, FR‑010, SC‑003, SC‑005, SC‑006, and the three user‑story narratives.  
  **Verification:** file exists; diff against current `spec.md` shows exactly the intended replacements; checksum recorded.  
- [ ] T003 [P] [Spec] **Validate amendment draft** – manual review that the draft is consistent with `plan.md` and the Constitution.   <!-- FAILED-IN-EXECUTION: code/validate_amendment.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/validate_amendment.py exit=1 -->
- [ ] T004 [P] [Spec] **Apply amendments to `spec.md`** – replace the functional‑requirement and user‑story sections with the text from `amendment_draft.md`.   <!-- FAILED-IN-EXECUTION: code/apply_spec_amendments.py exit=1 -->
  **Verification:** `spec.md` diff matches `amendment_draft.md`; checksum recorded.  
- [ ] T005 [P] [Plan] **Apply amendments to `plan.md`** – update the Constitution‑check table, project‑structure diagram, and any references to the amended FRs/SCs.  
  **Verification:** file exists; checksum updated; Constitution‑check table reflects new FR/SC numbers.

---  

## Phase 1 – Project Setup & Documentation  

These tasks establish a reproducible environment and the minimal documentation required for the research pipeline.  

- [ ] T006 [P] [Setup] **Configure linting & formatting** – create `pyproject.toml` with Ruff and Black settings.  
  **Verification:** `pyproject.toml` exists and contains expected Ruff/Black sections.  
- [ ] T007 [P] [Setup] **Create data directories** – `data/raw/`, `data/interim/`, `data/processed/`, `data/external/`.  
  **Verification:** all four directories exist after task execution.  
- [ ] T008 [P] [Setup] **Create test directories** – `tests/unit/`, `tests/integration/`, `tests/contract/`.  
  **Verification:** directories exist.  
- [ ] T009 [P] [Setup] **Configure Pytest** – add `pytest.ini` (timeout = 300 s, coverage options).  
  **Verification:** `pytest --collect-only` runs without error and reads `pytest.ini`.  
- [ ] T010 [P] [Docs] **Write `quickstart.md`** – step‑by‑step usage guide placed in `specs/001-compression-impact-gw-reconstruction/quickstart.md`.  
  **Verification:** file exists and contains at least one fenced code block.  
- [ ] T011 [P] [Docs] **Create contracts placeholder** – `specs/contracts/README.md` describing the contract‑testing strategy.  
  **Verification:** file exists.  
- [ ] T012 [P] [Docs] **Create `data-model.md`** – schema definitions for `GWOSCEvent`, `CompressionArtifact`, and `ParameterPosterior`.  
  **Verification:** file exists and validates against JSON schema defined therein.

---  

## Phase 2 – Real Data Acquisition & Validation (User Story 1)  

All downstream work depends on a vetted set of ≥ 15 **real** GWOSC CBC injection events with complete spin metadata (including tilt angle).  

- [ ] T013 [US1] **Implement data‑pipeline modules** – create:  
  - `src/data/fetch_injection.py` (function `fetch_injection_events` that queries the GWOSC injection‑campaign API, downloads LAL‑format files, and returns a list of local file paths).  
  - `src/data/validation_logic.py` (function `validate_injection_event` that checks each downloaded file for required fields: strain time series, detector names, timestamps, true parameters, and a `tilt_angle` field).  
  - `src/data/fetch_loop.py` (orchestration loop that calls `fetch_injection_events`, validates each with `validate_injection_event`, and repeats until **≥ 15** valid events are collected or a hard limit of 30 attempts is reached; raises `RuntimeError` if the quota cannot be met).  
  **Verification:** each module imports without error; `fetch_loop` can be imported and its main function runs without exception and produces at least 15 validated events.  
- [ ] T014 [US1] **Create data orchestrator** – `src/data/main.py` that invokes the fetch‑loop, writes the list of validated events (metadata only) to `data/interim/valid_events.json`, and logs provenance (including download URLs and SHA‑256 checksums).  
  **Verification:** running `src/data/main.py` produces a non‑empty `valid_events.json` containing ≥ 15 entries, each with a verified checksum.  
- [ ] T015 [US1] **Write tests for the data pipeline** –  
  - Unit tests in `tests/unit/test_fetch_injection.py` and `test_validation_logic.py` (e.g., assert that a downloaded file contains the `tilt_angle` field and that checksum verification passes).  
  - Integration test `tests/integration/test_data_pipeline.py` that runs the full pipeline on a limited subset (e.g., first 5 events) and then asserts that after the full run `valid_events.json` contains **≥ 15** validated events.  
  **Verification:** `pytest` passes all unit and integration tests.

---  

## Phase 3 – Compression & Reconstruction Error (User Story 2)  

Implement lossless and lossy compressors, compute error metrics, and flag unacceptable SNR degradation.  

- [ ] T016 [US2] **Lossless compression module** – `src/compression/lossless.py` with wrappers for gzip, LZ4, and bzip2 at levels 1, 5, 9.  
  **Verification:** each wrapper imports, compresses, and decompresses to exact original bytes (bitwise equality).  
- [ ] T017 [US2] **Lossy compression module** – `src/compression/lossy.py` implementing:  
  1. Quantized floating‑point (16‑bit, 8‑bit, 4‑bit).  
  2. JPEG2000 via 1‑D → 2‑D Hilbert‑curve folding (calls helper `src/compression/validation_jpeg2000.py`).  
  **Verification:** each method runs and returns a compressed file; quantization produces expected bit‑depth.  
- [ ] T018 [US2] **JPEG2000 validation helper** – `src/compression/validation_jpeg2000.py` exposing `validate_transformation_artifact(original, folded, compressed) → float` that returns the excess MSE after folding.  
  **Verification:** function returns a float; on a known sample the MSE matches pre‑computed value within 1e‑6.  
- [ ] T019 [US2] **Metrics module** – `src/compression/metrics.py` with functions `mse(original, recon)` and `snr_degradation(original, recon)` (precision ≥ 0.1 dB) **and** theoretical SNR computation based on injected parameters.  
  **Verification:** unit tests assert precision and that theoretical SNR is used in degradation calculation.  
- **Compression driver split into four granular tasks:**  
  - [ ] T020a [US2] **Compression input reader** – reads `valid_events.json` and streams each waveform.  
    **Verification:** succeeds and produces an in‑memory list of events.  
  - [ ] T020b [US2] **Apply compression methods** – iterates over each event and applies every lossless and lossy method, writing compressed files to `data/interim/compressed/`.  
    **Verification:** compressed files exist; naming follows `<event>_<method>_lvlX.bin`.  
  - [ ] T020c [US2] **Compute reconstruction metrics** – loads original and decompressed waveforms, computes MSE and SNR degradation (using T019), and records results in `data/interim/compression_results.json`.  
    **Verification:** JSON contains required fields (`mse`, `snr_degradation_db`, `theoretical_snr_db`).  
  - [ ] T020d [US2] **Flag unacceptable compression** – scans `compression_results.json` and adds a boolean `unacceptable` flag for any entry where SNR degradation > 5 %. Writes updated JSON.  
    **Verification:** at least one entry is flagged when degradation exceeds 5 %; flag field present for all entries.  
- [ ] T021 [US2] **Tests for compression pipeline** – unit tests in `tests/unit/test_compression.py` (bitwise equality for lossless, SNR > 0 for lossy) and integration test `tests/integration/test_compression_pipeline.py` that runs T020a‑d on a single synthetic event and checks that `compression_results.json` contains all required fields and correct `unacceptable` flags.  
  **Verification:** `pytest` passes all compression tests.

---  

## Phase 4 – Fast Parameter Estimation & Statistical Comparison (User Story 3)  

Run LALInference CPU‑mode parameter estimation on original and compressed data, compute bias, and perform the required statistical tests.  

- [ ] T022 [US3] **LALInference wrapper** – `src/pe/run_lalinference.py` that accepts a waveform file, runs LALInference in CPU mode (`--cpu`, appropriate runtime limits), and writes posterior samples to `data/processed/posteriors/<event>_<method>.h5`.  
  **Verification:** execution creates an `.h5` file containing `mass_samples`, `distance_samples`, `spin_samples`.  
- [ ] T023 [US3] **Failure‑detection module** – `src/pe/failure_detection.py` with `check_hierarchical_convergence(ess: float) -> bool` (returns *True* when `ess < 100`).  
  **Verification:** function returns expected boolean for sample ESS values.  
- [ ] T024 [US3] **Comparison & statistical‑test module** – `src/pe/compare_posteriors.py` that:  
  1. Loads `Bias_Original` baseline from `data/external/baseline_bias_original.json`.  
  2. Computes `Delta_Bias = Bias_Compressed – Bias_Original` for each parameter.  
  3. Attempts a **hierarchical Bayesian shift test** using KL‑divergence; if `check_hierarchical_convergence` is *True* **or** number of events < 5, falls back to paired t‑tests with Benjamini‑Hochberg correction.  
  4. Calculates **90 % credible‑interval overlap** for mass, distance, and spin.  
  5. Writes a consolidated results file `data/processed/statistical_test_results.json` containing KL values, p‑values, CI overlaps, and `Delta_Bias` with 95 % confidence intervals.  
  **Verification:** JSON contains keys `kl_divergence`, `ci_overlap`, `delta_bias`, `confidence_interval`; hierarchical test status recorded.  
- **PE orchestrator split into four tasks:**  
  - [ ] T025a [US3] **PE loop driver** – iterates over events and compression variants, invoking T022 for each.  
    **Verification:** driver completes without exception.  
  - [ ] T025b [US3] **Per‑event PE invocation** – wrapper that calls `run_lalinference.py` and logs runtime.  
    **Verification:** each call produces posterior file.  
  - [ ] T025c [US3] **Results aggregation** – collates all posterior files and calls `compare_posteriors.py`.  
    **Verification:** aggregation produces `statistical_test_results.json`.  
  - [ ] T025d [US3] **Report writing** – generates `reports/bias_report.md` summarizing tables of compression‑method vs. SNR degradation, `Delta_Bias` per parameter, and significance statements.  
    **Verification:** markdown file exists and contains required tables.  
- [ ] T026 [US3] **Tests for the PE pipeline** – unit tests for `run_lalinference.py` (mocked short run), `failure_detection.py`, and `compare_posteriors.py`; plus an integration test `tests/integration/test_pe_pipeline.py` that runs the full PE orchestrator on two events and verifies that `statistical_test_results.json` contains entries for mass, distance, spin and records hierarchical test convergence status.  
  **Verification:** `pytest` passes all PE tests.

---  

## Phase 5 – End‑to‑End Execution & Final Summary (Research Completion)  

Run the complete pipeline on the minimal viable dataset and produce the hand‑off artifacts.  

- [ ] T027a [Research] **Execute end‑to‑end pipeline** – invoke the top‑level script `src/main.py` (or `src/pe/main.py` after data and compression steps) on a *pilot* set of 2 synthetic events, generating:  
  - `data/interim/compression_results.json` (with SNR flags).  
  - `data/processed/statistical_test_results.json`.  
  - `reports/final_summary.md` containing:  
    * Table of compression‑method vs. SNR degradation.  
    * Table of `Delta_Bias` for mass, distance, spin with 95 % CI.  
    * Indication of which compression levels are “acceptable” (SNR ≤ 5 %).  
  **Verification:** script exits zero; all three artifacts exist and validate against their schemas.  
- [ ] T027b [Research] **Validate end‑to‑end artifacts** – run schema checks on the three artifacts and assert they meet the specifications.  
  **Verification:** schema validation passes; any deviation raises error.  
- [ ] T028 [Research] **Tilt‑angle exclusion verification** – after validation step, filter out any events lacking `tilt_angle` posteriors; assert that the final analysis set contains **≥ 12** events; log warnings for excluded events.  
  **Verification:** task fails if < 12 events remain; logs list of excluded IDs.  
- [ ] T029 [Research] **External Bias_Original baseline generation** – run a high‑iteration LALInference run on the original (uncompressed) synthetic dataset on an external compute resource (or use a pre‑computed public baseline) and store `baseline_bias_original.json` in `data/external/`.  
  **Verification:** baseline file exists and contains bias entries for each parameter.  
- [ ] T030 [Research] **Per‑method bias report** – compute for each compression method the bias (posterior mean − true value) with 95 % confidence intervals and write `reports/bias_report_per_method.md`.  
  **Verification:** markdown contains a table with columns `method`, `level`, `mass_bias (CI)`, `distance_bias (CI)`, `spin_bias (CI)`.  
- [ ] T031 [Research] **SNR theoretical baseline comparison** – using the theoretical SNR from injected parameters, compute the absolute deviation for each compression level and record in `reports/snr_theoretical_comparison.md`.  
  **Verification:** report exists and lists deviation in dB for each method/level.  

---  

## Phase 6 – Polish & Cross‑Cutting Concerns  

Final quality‑of‑life improvements.  

- [ ] T032 [Docs] **Update top‑level README** – installation steps, usage examples, and a diagram of the data flow.  
  **Verification:** README exists and includes sections “Installation”, “Usage”, and “Data Flow Diagram”.  
- [ ] T033 [Docs] **Add API documentation** – `docs/api.md` with signatures for all public functions in `src/data`, `src/compression`, and `src/pe`.  
  **Verification:** file exists and lists function signatures.  
- [ ] T034 [Perf] **Performance sanity check** – add a CI job that measures total pipeline runtime on the pilot set; if > 6 h, log a warning and suggest parameter tweaks (e.g., reduce `nlive`).  
  **Verification:** CI job records runtime; fails (or warns) if threshold exceeded.

---  

### Dependency & Execution Order Summary  

| Phase | Must complete before | Key output artifact |
|------|----------------------|---------------------|
| 0 (Amendments) | – | Updated `spec.md` & `plan.md` |
| 1 (Setup) | 0 | Lint config, directories, docs |
| 2 (Data) | 1 | `data/interim/valid_events.json` |
| 3 (Compression) | 2 | `data/interim/compression_results.json` |
| 4 (PE) | 3 | `data/processed/statistical_test_results.json` |
| 5 (E2E) | 4 | `reports/final_summary.md` |
| 6 (Polish) | 5 | Documentation & CI checks |

All tasks are written in the canonical `- [ ] T### [P?] [USx?] description with file path` format, include explicit file paths, and respect the data‑flow dependencies required by the specification.  Once every unchecked task is completed and its associated test passes, the analysis can be run end‑to‑end and the research hand‑off will be ready for the subsequent paper pipeline.  