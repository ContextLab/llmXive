# Tasks: Neuro‑Symbolic Learning Networks: Bridging Neural and Symbolic Reasoning in Education  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, and reviewer feedback.  

The following checklist implements the full end‑to‑end study while respecting all functional requirements (FR‑001 – FR‑022) and success criteria (SC‑001 – SC‑012). Tasks are ordered to respect data flow; tasks marked **[P]** can run in parallel because they operate on independent files.

---  

- [ ] **T001** [P] **Citation‑gate validation** – Run `tools/reference_validator.py` on all external URLs (ASSISTments, Khan Academy, BKT repo, etc.) using the Constitution‑mandated title‑overlap threshold 0.8.  
  - **Artifact**: `state/validation/citation_gate_passed.txt` (empty file indicates success).  
  - **Verification**: CI aborts with exit 1 and logs “ERROR: URL validation failed for <URL>” if any URL falls below the threshold.  

- [ ] **T002** **Dataset download, unification, checksum generation & validation** (covers FR‑001, FR‑007, FR‑008, FR‑012, FR‑021).  
  1. **Download** `ASSISTments` (`https://huggingface.co/datasets/assistments/2009-2010`) and `Khan Academy` (`https://huggingface.co/datasets/khanacademy/math`) with `datasets.load_dataset(..., streaming=True)`. Abort with exit 1 and log `ERROR: Failed to download ASSISTments after 300 seconds – aborting pipeline.` (or analogous for Khan) if the configurable timeout (default 300 s) is exceeded.  
  2. **Write** raw CSVs to `data/raw/assistments.csv` and `data/raw/khan_academy.csv`.  
  3. **Generate SHA‑256 checksum files** `data/raw/assistments.sha256` and `data/raw/khan_academy.sha256`.  
  4. **Unify** the two sources into `data/processed/unified_problems.csv`, preserving the original rows, adding a `dataset_source` column, and **recording** the actual source proportions in `results/dataset_balance.csv`. No hard minimum per source is enforced (FR‑021 is deferred).  
  5. **Validate** `unified_problems.csv` against `contracts/problem.schema.yaml`. On any violation, exit 1 and log `ERROR: Invalid unified schema: <details>`.  
  - **Artifacts**: `data/raw/assistments.csv`, `data/raw/assistments.sha256`, `data/raw/khan_academy.csv`, `data/raw/khan_academy.sha256`, `data/processed/unified_problems.csv`, `results/dataset_balance.csv`.  
  - **Verification**: CI checks that the files exist, checksums match, and schema validation passes.  

- [ ] **T003** **Explanation generation, distinctness, and problem‑record robustness** (covers FR‑002, FR‑017, FR‑018, SC‑001, SC‑010‑12).  
  1. **Neural**: For each `problem_id` in `unified_problems.csv`, run `code/generate/neural_explanation.py` using a 4‑bit quantized TinyLlama‑1.1B‑Chat (`load_in_8bit=True`, `device="cpu"`). Enforce per‑problem timeout (default 180 s). Output `data/traces/{problem_id}_neural.txt` and accompanying JSON metadata `data/traces/{problem_id}_neural.json` conforming to `contracts/explanation.schema.yaml`.  
  2. **Symbolic**: Run `code/generate/symbolic_explanation.py` (rule‑based engine) producing `*_symbolic.txt` + metadata.  
  3. **Neuro‑symbolic**: Run `code/generate/neuro_symbolic_explanation.py` which merges the neural narrative with the symbolic trace, producing `*_neuro_symbolic.txt` + metadata.  
  4. **Missing/Corrupt problem handling**: If a problem cannot be parsed, log a warning and skip it. After processing, compute the proportion of skipped records; abort with exit 1 if **> 1 %** (SC‑011).  
  5. **Distinctness verification**: `code/generate/verify_distinctness.py` computes cosine similarity between neural and symbolic texts (via sentence‑transformers). Fail the pipeline if similarity > 0.95 for **> 2 %** of problems (SC‑010).  
  6. **Success‑rate summary**: Produce `results/explanation_generation_summary.csv` containing counts of successful generations per condition and percentages of timeouts, missing/corrupt records, and non‑distinct pairs.  
  - **Artifacts**: Explanation `.txt` and `.json` files under `data/traces/`, plus the summary CSV.  
  - **Verification**: CI aborts if overall success < 95 % (SC‑001) or if distinctness or missing‑record thresholds are exceeded.  

- [ ] **T004** **Human pilot ingestion & BKT calibration** (covers FR‑010, SC‑007).  
  1. **Ingest** `data/pilot/real_pilot_data.csv` (provided by the research team) and validate against `contracts/pilot_data.schema.yaml`. Exit 1 with `ERROR: Human pilot data missing or <50 records` if validation fails.  
  2. **Compute calibration metrics** (`RMSE`, `RMSE diff`, and a TOST equivalence test) using `code/simulate/calibrate_bkt.py`.  
  3. **Pass/fail**: Abort with exit 1 and log `ERROR: Calibration thresholds not met (RMSE = …, diff = …)` if any of the three thresholds (RMSE ≤ 0.15, diff ≤ 0.02, TOST p ≥ 0.10) are violated (FR‑010).  
  4. **Write** calibrated parameters to `code/simulate/bkt_params.yaml` and a human‑readable report to `results/calibration_report.json`.  
  - **Artifacts**: `code/simulate/bkt_params.yaml`, `results/calibration_report.json`.  
  - **Verification**: CI checks that the report exists and that all thresholds are satisfied.  

- [ ] **T005** **Full simulation run** (covers FR‑009, FR‑004, FR‑005, FR‑019, SC‑005‑6, SC‑012).  
  1. Using the calibrated BKT (`bkt_params.yaml`), simulate **≥ 2 000** students per explanation condition (`neural`, `symbolic`, `neuro_symbolic`).  
  2. For each simulated interaction, record fields required by `contracts/interaction_log.schema.yaml` (including `prior_knowledge_score` and `difficulty` drawn from the problem metadata). Store rows in `data/processed/simulation_logs.csv`.  
  3. **Validate** the CSV against the schema; abort on any schema violation.  
  4. **Response‑time distribution check** (`code/simulate/validate_rt_distribution.py`): bin `rt_seconds` into 1‑second bins, ensure no more than two consecutive empty bins (i.e., no gaps > 5 s). Abort with `ERROR: Response time distribution invalid` if violated (SC‑005).  
  5. **Comprehension‑rating validation**: compute the proportion of out‑of‑range or non‑numeric ratings; abort with `ERROR: Excess invalid comprehension ratings` if **> 0.5 %** (SC‑012).  
  6. **Summary**: `results/simulation_summary.yaml` reports total rows (must be ≥ 6 000), percentage of valid records (≥ 99 % required by SC‑005), and any rows dropped.  
  - **Artifacts**: `data/processed/simulation_logs.csv`, `results/simulation_summary.yaml`.  
  - **Verification**: CI enforces the thresholds above.  

- [ ] **T006** **Real‑student data ingestion** (covers FR‑011, SC‑004, SC‑007).  
  1. Ingest `data/real/real_student_data.csv` (≥ 200 participants) and validate against `contracts/interaction_log.schema.yaml` with `data_source = "real"`.  
  2. Produce a checksum file `data/real/real_student_data.sha256`.  
  3. On missing file, insufficient rows, or schema failure, abort with `ERROR: Real student data missing or <200 records`.  
  - **Artifacts**: `data/real/real_student_data.csv`, checksum, validation log.  

- [ ] **T007** **Merge datasets** (covers FR‑006, FR‑011, SC‑002).  
  1. Merge `simulation_logs.csv` (data_source = “simulated”) with `real_student_data.csv` (data_source = “real”) into `data/processed/combined_logs.csv`.  
  2. **Verify combined row count** ≥ 5 000; abort with `ERROR: Combined dataset below required size` if not (SC‑002).  
  - **Artifacts**: `data/processed/combined_logs.csv`.  
  - **Verification**: CI checks row count.  

- [ ] **T008** **Exploratory mixed‑effects regression on combined data** (covers FR‑020, SC‑009‑12, SC‑004).  
  1. Run `code/analyze/mixed_effects_exploratory.py` on `combined_logs.csv` including the `data_source` fixed effect.  
  2. Produce `results/exploratory_output.yaml` validated against `contracts/analysis_output.schema.yaml`. This file must contain **p‑values** and **Cohen's d effect sizes with 95 % confidence intervals** for each pairwise condition comparison (fulfilling SC‑004).  
  3. Include diagnostics for timeout counts, missing‑record percentages, and invalid‑rating rates (must be ≤ 2 %, ≤ 1 %, ≤ 0.5 % respectively).  
  - **Artifacts**: `results/exploratory_output.yaml`.  
  - **Verification**: CI validates schema and that the diagnostic thresholds are met.  

- [ ] **T009** **Primary mixed‑effects regression on real‑only data** (covers FR‑006, FR‑011, SC‑003).  
  1. Run `code/analyze/mixed_effects_primary.py` on `real_student_data.csv` (real‑only) with fixed effects `condition`, `prior_knowledge_score`, `difficulty`; random intercepts for `problem_id` and `student_id`.  
  2. Compute Cohen's d effect sizes with 95 % CI; enforce CI width for neuro‑symbolic vs neural ≤ 0.20 (SC‑003).  
  3. Output `results/analysis_output.yaml` validated against `contracts/analysis_output.schema.yaml`.  
  - **Artifacts**: `results/analysis_output.yaml`.  
  - **Verification**: CI checks CI‑width constraint.  

- [ ] **T010** **Deterministic API delivery of explanations to BKT simulator** (covers FR‑003).  
  1. For each explanation file produced in T003, invoke the deterministic API `simulator.present_explanation(explanation_path)` and log success.  
  2. Verify that the API call returns a success code for every explanation; abort if any call fails.  
  - **Artifacts**: log file `results/api_delivery_log.txt`.  
  - **Verification**: CI parses the log to ensure all calls succeeded.  

- [ ] **T011** **Reporting & CI resource monitoring** (covers FR‑008, SC‑006, SC‑009‑12).  
  1. `tools/resource_monitor.py` wraps the entire pipeline, records peak CPU cores and RAM usage, writes `results/resource_usage.json`. Abort with exit 1 and log `ERROR: Resource limits exceeded (CPU > 2 cores or RAM > 7 GB)` if limits are breached (FR‑008).  
  2. `code/report/generate_report.py` compiles a human‑readable markdown `results/report.md` containing:  
     - Explanation‑generation success rates and distinctness metrics (SC‑001, SC‑010‑12).  
     - Simulation validation summary (SC‑005, SC‑006).  
     - Calibration statistics (RMSE, TOST).  
     - Primary regression table and effect sizes (including CI widths).  
     - Exploratory diagnostics (data‑source effect, timeout/invalid‑rating percentages).  
     - Resource usage summary.  
  - **Artifacts**: `results/resource_usage.json`, `results/report.md`.  
  - **Verification**: CI checks resource usage limits and that the report file exists.  

---  

### Dependency Summary

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T002 |
| T004 | T003 |
| T005 | T004, T003 |
| T006 | – |
| T007 | T005, T006 |
| T008 | T007 |
| T009 | T007 |
| T010 | T003 |
| T011 | T008, T009, T010 |
