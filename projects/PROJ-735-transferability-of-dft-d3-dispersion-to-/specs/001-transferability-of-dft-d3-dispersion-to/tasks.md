# Tasks: Transferability of DFT‑D3 Dispersion to Ionic Liquids  

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, reviewer feedback.  

The checklist implements the complete end‑to‑end workflow required by the specification, grouped into logical phases. All tasks use the canonical `- [ ] T### [P?] [USx?] description` format, include artifact paths, and respect data‑flow ordering.

---

## Phase 0 – Data acquisition & validation  

| Goal | Retrieve required external datasets, verify integrity, and perform mandatory validation before any computation. |
|------|---------------------------------------------------------------------------------------------------------------|

- [ ] **T022** [FR‑001] Download IL‑Benchmark dataset. <!-- FAILED-IN-EXECUTION: code/download_il_benchmark.py exit=1; code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=2 -->
  *Attempt to download the ZIP from the Zenodo DOI specified in the spec; on network failure or checksum mismatch, load the local fallback file `data/raw/IL‑Benchmark‑local.zip`. Verify SHA‑256 checksum, extract contents to `data/raw/`.*
  *Verification*: After execution, `data/raw/metadata.csv` exists and its checksum matches the recorded value in `state/projects/...yaml`.

- [X] **T023** [FR‑002] Validate benchmark records.  
  *Read `data/raw/metadata.csv` and ensure each row contains a non‑null `reference_energy` and a unique `pair_id`. Log any violations and omit those rows from downstream processing.*  
  *Verification*: A log file `code/validation.log` lists omitted records; the cleaned list is written to `data/processed/validated_metadata.csv`.

- [ ] **T024** [FR‑008] Retrieve experimental bulk‑property data.
  *Call the NIST IL Thermophysical Database API; if the request fails or returns incomplete data, fall back to the static CSV `data/raw/experimental_bulk_properties.csv`. Verify required columns (`pair_id`, `density`, `viscosity`).*  
  *Verification*: `data/processed/bulk_properties.csv` is created; its schema is validated against `contracts/raw_bulk_properties.schema.yaml`.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Prove that the code, data‑loading, and reporting infrastructure work on a tiny subset before scaling. |
|------|-----------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US1] Create a runnable quick‑start description.   <!-- FAILED-IN-EXECUTION: code/main.py exit=2 -->
  *Write `docs/quickstart.md` with the exact command `python -m code.main --subset 3` and environment activation steps.*  
  *Verification*: Running the command on a fresh runner produces `data/derived/raw_energies.csv` with ≥ 3 rows and exits with code 0.

- [ ] **T002** [US1] Implement the primary Psi4 computation and unit tests.  
  *Add `code/run_psi4.py` that reads the validated ion‑pair list, runs a B3LYP/def2‑TZVP + D3(BJ) single‑point with Counterpoise, retries SCF failures up to 3 times, and writes rows to `data/derived/raw_energies.csv` (schema `raw_energies.schema.yaml`).*  
  *Add `tests/test_run_psi4.py` asserting correct energy format and proper `"failed"` marking.*  
  *Verification*: `pytest -q tests/test_run_psi4.py` passes.

- [ ] **T003** [US1] Execute a tiny end‑to‑end run and produce a raw‑energies CSV.  
  *Run `python -m code.main --subset 5` (uses the subset flag added in T001).*  
  *Verification*: `data/derived/raw_energies.csv` exists, contains all required columns, and passes schema validation.

- [ ] **T004** [US1] Run the full benchmark (≤ 100 ion‑pairs) on the CI runner.  
  *Invoke `python -m code.main` (no `--subset`).*  
  *Verification*: `data/derived/raw_energies.csv` contains a row for every validated ion‑pair; `calculation_status` is `"success"` or `"failed"` as appropriate; schema validation succeeds.

---

## Phase 2 – Complete study and validation  

| Goal | Produce the scientific results required by FR‑001 – FR‑014, SC‑001 – SC‑005, and the three user stories. |
|------|-------------------------------------------------------------------------------------------------------------------|

- [ ] **T005** [US1] Compute raw error metrics and bootstrap MAE confidence interval.  
  *Add `code/analyze_energies.py` that reads `raw_energies.csv`, calculates MAE, RMSE, MSE, and performs 1 000 bootstrap resamples to obtain a 95 % CI for MAE (FR‑014).*  
  *Write the summary to `docs/benchmark_report.md`; validate the markdown against a newly added `benchmark_report.schema.yaml`.*  
  *Verification*: The markdown contains MAE, CI, RMSE, MSE, and passes schema validation.

- [ ] **T006** [US2] Derive and apply the D3 scaling factor (self‑contained).  
  *If `data/derived/raw_energies.csv` is missing, invoke the benchmark task (T004) automatically.*  
  *Run `code/derive_scaling.py` which (a) splits the successful records (80 % train / 20 % test, fixed seed), (b) fits a constrained scalar `s>0` minimizing MAE on the training set, (c) evaluates test‑set MAE, (d) bootstraps 1 000 replicates to obtain a 95 % CI for `s`, and (e) performs a hypothesis test `H₀: s=1` (p‑value).*  
  *Write `data/derived/scaling_factor.txt` as a JSON block conforming to `scaling_factor.schema.yaml` and update `raw_energies.csv` with columns `scaled_d3_energy` and `error_corrected`.*  
  *Verification*: The file contains all required keys, `scaling_factor>0`, and the CI is recorded; unit test `tests/test_derive_scaling.py` passes.

- [ ] **T008** [US3] Compute bulk‑property correlations and generate report (self‑contained).  
  *If `scaling_factor.txt` is absent, invoke T006 automatically.*  
  *Merge `raw_energies.csv` with `data/processed/bulk_properties.csv`, exclude pairs missing bulk data, and compute (a) raw D3 vs density, (b) scaled D3 vs density, (c) interaction‑energy error vs viscosity. For each metric compute Pearson and Spearman coefficients, R², raw p‑values, and 95 % bootstrap CIs (1 000 replicates) while controlling for electrostatic energy and ion‑pair size via partial correlation. Apply a Bonferroni correction across the six tests.*  
  *Write results to `data/derived/correlation_results.csv` (schema `correlation_results.schema.yaml`) **without** a minimum‑sample‑size guard; if data are insufficient the CSV contains rows with `NA` values.*  
  *Generate `docs/correlation_report.md` from the CSV, ensuring compliance with `correlation_report.schema.yaml`.*  
  *Verification*: The CSV has six rows, all fields non‑null (or `NA`), and passes schema validation; the markdown report passes its schema check.

---

## Phase 3 – Reproducibility, linting, and handoff  

| Goal | Ensure the pipeline runs cleanly on CI, passes static checks, and provides a complete handoff for the downstream paper stage. |
|------|-------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T010** [US1] Run flake8 linting, fix all violations, and record a clean report.  
  *Execute `flake8 code/ tests/ > code/lint_report.txt` and ensure the exit code is 0. The file must end with the line `Exit code: 0`.*  
  *Verification*: `cat code/lint_report.txt` ends with `Exit code: 0`; re‑running flake8 produces no output.

- [ ] **T011** [US1] Document Black formatting configuration.  
  *Create `code/black_config.md` describing the Black version and line‑length settings used across the project.*  
  *Verification*: File exists and is listed in the repository; no test required.

- [ ] **T014** [US1 & US2 & US3] Execute the full pipeline and assert zero exit status.  
  *Run `python -m code.main` on a clean runner, capture stdout/stderr to `runtime_report.txt`, and assert the process exits with status 0.*  
  *Verification*: `runtime_report.txt` contains “Exit code: 0”.

- [ ] **T025** [SC‑005] Capture runtime statistics and enforce resource limits.  
  *Wrap the full pipeline call with `/usr/bin/time -v` and write the output to `runtime_report.txt`. After execution, parse the file to confirm wall‑clock time ≤ 6 h and maximum RSS ≤ 7 GB.*  
  *Verification*: A test script `tests/test_runtime_limits.py` asserts the limits are met.

- [ ] **T015** [US1 & US2 & US3] Write the paper‑stage handoff in `docs/quickstart.md`.  
  *Add a “Paper‑stage handoff” section that (a) lists the canonical artifact paths, (b) notes limitations (benchmark size, synthetic fallback, functional assumptions), and (c) provides the reproducibility command ` /usr/bin/time -v python -m code.main`. No hand‑typed numerical results are included.*  
  *Verification*: Section exists, uses only listed paths, passes a spell‑check test.

- [ ] **T026** [Principle V] Record SHA‑256 hashes of all derived artefacts.  
  *Compute hashes for `data/derived/raw_energies.csv`, `data/derived/scaling_factor.txt`, `data/derived/correlation_results.csv`, `docs/benchmark_report.md`, and `docs/correlation_report.md`; write them into `state/projects/PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml` under `artifact_hashes`.*  
  *Verification*: A validation script `scripts/verify_hashes.py` confirms that the recorded hashes match the current file contents.
