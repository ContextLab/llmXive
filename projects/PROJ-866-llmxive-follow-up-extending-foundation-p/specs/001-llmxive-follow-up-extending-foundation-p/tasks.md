# Tasks: llmXive follow‑up – extending “Foundation Protocol: A Coordination Layer for Agentic Society”

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, and the verifier feedback (re‑run of T101 and T111 failed).

The tasks are organized into research phases.  Each task follows the required format  
`- [ ] T### [USx] description … with file path`.  The indented lines list the concrete
requirement(s) it satisfies and the verification step(s).

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T101 [US1] **Repair the pipeline orchestrator** – implement a functional `code/main.py` that orchestrates generation → full‑context execution → compressed execution → analysis → reporting.  
  **File**: `code/main.py`  
  **Requirements**: FR‑001, FR‑002, FR‑003, FR‑007; must expose CLI flags `--generate`, `--compress`, `--analyze`, `--n‑workflows`, `--seed`.  
  **Verification**: `python code/main.py --help` exits 0; a smoke run `python code/main.py --generate --n‑workflows 20` exits 0; full pytest suite under `code/` passes.

- [ ] T111 [US1] **Run the full pipeline and produce core artifacts** – using the repaired orchestrator, execute the complete study with the deterministic seed and full workflow count (500).  
  **Files**: `data/raw/workflows.json`, `data/processed/full_context_logs.json`, `data/processed/compressed_context_logs.json`, `data/results/tradeoff_curve.csv`, `data/results/analysis_results.json`, `data/results/threshold_report.json`, `data/results/multiplicity_tests.json`  
  **Requirements**: FR‑001 – FR‑006, FR‑007; all artifacts must conform to their JSON/YAML schemas and be non‑empty.  
  **Verification**: command `python code/main.py --generate --compress --analyze` exits 0; each listed file exists, parses, and passes schema validation.

- [ ] T112 [US1] **Record run‑time metrics** – extend the orchestrator (or add a small helper) to create `data/results/run_metrics.json` containing wall‑clock time, start/end timestamps, total workflow count, total execution count, and `invalid_workflow_ratio`.  
  **File**: `data/results/run_metrics.json`  
  **Requirements**: SC‑005, FR‑007.  
  **Verification**: JSON file exists, fields are present, `total_wall_clock_time_seconds` > 0 and matches the actual runtime.

---

## Phase 2 – Validation, edge‑case handling, and statistical checks

- [ ] T102 [US1] **Invalid‑workflow exclusion verification** – implement `code/utils/verify_invalid_exclusion.py` that cross‑checks `is_valid:false` entries in `data/raw/workflows.json` against logs in `data/processed/*_logs.json`, ensuring no invalid workflow contributes to `tradeoff_curve.csv`.  The script writes `data/results/invalid_exclusion_report.json` with keys `invalid_workflow_count`, `excluded_count`, `status`.  
  **Files**: `code/utils/verify_invalid_exclusion.py`, `data/results/invalid_exclusion_report.json`  
  **Requirements**: FR‑008, edge‑case handling (US‑1).  
  **Verification**: script exits 0; report file exists and counts match the number of `is_valid:false` workflows.

- [ ] T103 [US3] **Trade‑off‑curve and analysis‑results schema validation** – add validation of `data/results/tradeoff_curve.csv` against a new `contracts/tradeoff_curve.schema.yaml` and of `data/results/analysis_results.json` against the existing `contracts/analysis_results.schema.yaml` inside the pipeline.  
  **Files**: `contracts/tradeoff_curve.schema.yaml`, validation code in `code/main.py` (or a helper).  
  **Requirements**: Constitution IV (single source of truth), FR‑005, FR‑006.  
  **Verification**: a deliberately corrupted CSV or JSON causes the pipeline to abort with a non‑zero exit code; correct files pass silently.

- [ ] T104 [US3] **Threshold enforcement, multiplicity tests, and tokenizer consistency** – augment `code/services/analyzer.py` to (a) abort the pipeline if the identified safe‑operating‑zone threshold yields an error rate > 1 % (SC‑004), (b) emit `data/results/multiplicity_tests.json` containing the Cochran‑Armitage trend‑test statistic, Bonferroni‑corrected pairwise p‑values, and a boolean `alpha_0_05_significant` flag for each, (c) ensure every token‑counting reference uses the exact model name `cl100k_base`.  
  **Files**: `code/services/analyzer.py`, `data/results/multiplicity_tests.json`  
  **Requirements**: FR‑005, FR‑006, FR‑009, SC‑003, SC‑004.  
  **Verification**: unit test feeding a synthetic analysis result with >1 % error triggers abort; another test confirms `multiplicity_tests.json` contains corrected p‑values; grep for `cl100k_base` returns only the correct spelling.

- [ ] T105 [US1] **Adaptive‑sampling extension (optional sensitivity check)** – add an `--adaptive` flag to `code/services/generator.py` that densifies workflow depth distribution around the threshold reported in `threshold_report.json` while preserving the deterministic seed and the guarantee of ≥ 25 workflows per depth for the base levels.  Document the rule in `docs/adaptive_sampling.md`.  
  **Files**: `code/services/generator.py`, `docs/adaptive_sampling.md`  
  **Requirements**: FR‑001 (adaptive variant), optional for sensitivity analysis.  
  **Verification**: running `python code/main.py --generate --adaptive` produces a depth histogram with a statistically higher count in the bin containing the threshold; a repeat run with the same seed yields identical output.

- [ ] T106 [US3] **Measurement‑vs‑construction limitation analysis** – create `code/utils/construct_validity.py` that fits a scikit‑learn `LogisticRegression` (random_state = 42) on per‑step outcomes (features: `delegation_depth`, `policy_complexity`, `compression_depth`, chain‑length) to quantify how much of the observed error rate is explained by the underlying graph topology.  Output `data/results/construct_validity_report.json` with fields `structural_r2`, `residual_variance_fraction`, and a brief interpretation.  
  **Files**: `code/utils/construct_validity.py`, `data/results/construct_validity_report.json`  
  **Requirements**: address reviewer concern about deductive error generation; FR‑005, SC‑001.  
  **Verification**: script runs without error; JSON contains numeric values in [0, 1] and a non‑empty `interpretation` string.

- [ ] T113 [US3] **Simulation‑based power analysis** – implement `code/utils/power_analysis.py` that simulates 1 000 datasets matching the study design (effect size: ≥ 1 % error jump at the threshold), fits the same binomial GEE model on each, and records the proportion that detects the jump at α = 0.05 (Bonferroni‑adjusted).  Write `data/results/power_analysis.json` with `n_simulations`, `effect_size`, `estimated_power`, `power_ci_lower`, `power_ci_upper`, `method`.  
  **Files**: `code/utils/power_analysis.py`, `data/results/power_analysis.json`  
  **Requirements**: FR‑005, SC‑004, reproducibility (fixed seeds).  
  **Verification**: script exits 0; JSON fields are present and `estimated_power` lies in [0, 1]; two runs with identical seed produce identical files.

---

## Phase 3 – Reporting, reproducibility, and handoff

- [ ] T107 [US1] **README reproducibility section** – add a “Reproducibility and Verification” section to `README.md` that (1) documents the full pipeline command, (2) explains checksum generation via `code/utils/checksum_utils.py`, (3) describes how to run the invalid‑exclusion check, and (4) points to the `data/results/reproducibility_report.json`.  
  **File**: `README.md`  
  **Requirements**: FR‑007, SC‑005, Constitution V.  
  **Verification**: the section exists, contains the four items, and all commands run successfully on a fresh checkout.

- [ ] T108 [US3] **Results documentation** – author `specs/001-policy-compression-tradeoff/results.md` summarizing (a) methods (binomial GEE, trend test, Bonferroni correction), (b) outcomes (trade‑off curve, threshold with 95 % CI, multiplicity‑test results), (c) edge‑case handling (`[deferred]` cases, invalid‑workflow exclusion), (d) power estimate, (e) adaptive‑sampling sensitivity note, and (f) construct‑validity limitation.  All numbers must be traceable to cells in `data/results/*.json` or rows in `data/results/tradeoff_curve.csv`.  Include the figure `figures/tradeoff_curve.png` generated by `code/utils/make_figure.py`.  
  **Files**: `specs/001-policy-compression-tradeoff/results.md`, `figures/tradeoff_curve.png`  
  **Requirements**: SC‑001 – SC‑004, Constitution IV.  
  **Verification**: each numeric claim is cross‑checked (e.g., via a script that parses the CSV/JSON and asserts equality); the figure file exists and is regenerated by the script.

- [ ] T109 [US1] **Reproducibility re‑run & published hash** – on a clean clone, re‑execute the documented workflow (`python code/main.py --generate --compress --analyze`) and generate `data/results/reproducibility_report.json` containing (a) the exact command line used, (b) SHA‑256 checksums for every deterministic artifact under `data/`, and (c) an aggregate `reproducibility_hash` over the entire `data/` directory.  Two consecutive runs must yield identical checksums.  Do **not** write anything to `state/`.  
  **File**: `data/results/reproducibility_report.json`  
  **Requirements**: FR‑007, Constitution V, SC‑005.  
  **Verification**: after two runs, a diff of the two JSON files shows no differences in the checksum fields; the file parses and includes all required keys.

- [ ] T110 [US3] **Paper‑stage handoff note** – create `specs/001-policy-compression-tradeoff/paper_handoff.md` that lists (with relative paths) all artifacts required for the paper: `figures/tradeoff_curve.png`, `data/results/tradeoff_curve.csv`, `data/results/threshold_report.json`, `data/results/multiplicity_tests.json`, `data/results/power_analysis.json`, and the `reproducibility_hash` from T109.  State that these satisfy Constitution IV (single source of truth) and V (hash verification).  
  **File**: `specs/001-policy-compression-tradeoff/paper_handoff.md`  
  **Requirements**: FR‑006, Constitution IV & V.  
  **Verification**: each listed path exists; the hash matches the one recorded in `reproducibility_report.json`.

---

### Dependency ordering (implicit)

1. **T101** → 2. **T111** → 3. **T112** → 4. **T102**, **T103**, **T104**, **T105**, **T106**, **T113** → 5. **T107** → 6. **T108** → 7. **T109** → 8. **T110**  

All tasks write only to project‑owned locations (`code/`, `data/`, `figures/`, `docs/`, `specs/`).  No task touches platform‑owned `state/` directories.  The pipeline remains CPU‑only and conforms to the resource constraints of the free‑tier CI runner.
