# Tasks: llmXive follow‑up – extending “LatentSkill: From In‑Context Textual Skills to In‑Weight Latent Skills”

**Inputs**: `spec.md`, `plan.md`, existing code base, contracts, and reviewer feedback.  
All tasks are written as checklist items; checked boxes (`[X]`) indicate work that has already been completed and verified. Unchecked boxes (`[ ]`) indicate work that still needs to be done.  Parallelizable tasks are marked with `[P]`.  Story labels (`[US1]`, `[US2]`, `[US3]`) tie tasks to the user‑story requirements in the specification.

---

## Phase 0 – Project bootstrap & reproducibility (setup)

- [ ] T001 [P] **Create project skeleton** – add `code/`, `tests/`, `data/`, `reports/` directories, initialise empty `__init__.py` files where needed, and add them to `.gitignore`.  
  *Verification*: `git ls-files` shows the directories and files; `pytest -q` runs with no import errors.

- [ ] T002 [P] **Pin exact dependencies** – write `requirements.txt` with the versions listed in the plan (torch 2.1.0, numpy 1.24.3, …).  
  *Verification*: `pip install -r requirements.txt` succeeds without conflicts.

- [ ] T003 [P] **System‑level prerequisites** – install `cmake` and `build-essential` via apt.  
  *Verification*: `dpkg -l | grep cmake` and `gcc --version` report installed versions.

- [ ] T004 [P] **Configuration & seed handling** – add `code/utils/config.py` that (i) pins random seeds, (ii) defines project‑wide paths, and (iii) stores `OOD_THRESHOLD = 0.5`.  
  *Verification*: Importing `config` prints the seed values and path constants.

- [ ] T005 [P] **Version‑hash utility** – implement `code/utils/versioning.py` to compute SHA‑256 hashes for any artifact and write them to `state/artifact_hashes.yaml`.  
  *Verification*: Running the script on a sample file updates the YAML with a matching hash.

- [ ] T006 [P] **Define verified data sources** – create `data_sources.yaml` containing the two canonical sources:  
  ```yaml
  proxy_lora_dataset: mrm8488/peft-examples
  arxiv_supplementary: https://arxiv.org/src/2606.06087v1/ancillary.zip
  ```  
  *Verification*: `cat data_sources.yaml` shows the exact entries.

- [ ] T007 [P] **Citation‑check script** – add `code/validate/citation_check.py` that (i) HTTP‑GETs each URL in `data_sources.yaml`, (ii) validates a 200 response, and (iii) writes `data/processed/citation_verification.json`.  
  *Verification*: Running the script produces a JSON with `"status": "ok"` for each source.

---

## Phase 1 – Data ingestion & Skill‑Vector index (User Story 1)

- [ ] T010 [P] **Download LoRA adapters** – `code/ingestion/download_weights.py` streams the `proxy_lora_dataset` via `datasets.load_dataset(..., streaming=True)`, writes each `adapter_model.safetensors` to `data/raw/lora_weights/`, and aborts with a non‑zero exit code if any file is missing.  
  *Verification*: After execution, `ls data/raw/lora_weights/*.safetensors` lists > 0 files; `data/processed/data_fetch_status.json` contains `"status": "success"`.

- [ ] T011 [P] **Flatten & normalize LoRA weights** – `code/ingestion/flatten_lora.py` loads the A/B matrices, flattens each to a 1‑D `float32` vector, L2‑normalises it, checks that all adapters share the same dimensionality, and writes `data/processed/weights_flattened.npz`.  
  *Verification*: `np.load(...).files` includes `vectors`; all vectors have identical shape; a checksum is recorded in `state/artifact_hashes.yaml`.

- [ ] T012 [P] **Build Skill‑Vector database** – `code/retrieval/vector_db.py` reads `weights_flattened.npz`, attaches task IDs and descriptions from `data/raw/task_descriptions.json`, and writes the compressed index `data/processed/skill_index.npz`.  
  *Verification*: Loading the index yields arrays `vectors`, `task_ids`, `descriptions`; schema validation against `skill_vector.schema.yaml` passes.

- [ ] T013 [P] **Unit‑test ingestion pipeline** – `tests/unit/test_ingestion.py` checks that the flattening step produces vectors whose length equals `A_dim * B_dim` and that the index file contains the expected number of entries.  
  *Verification*: `pytest tests/unit/test_ingestion.py -q` reports all tests passed.

- [ ] T014 [P] **Integration test for end‑to‑end ingestion** – `tests/integration/test_ingestion_pipeline.py` runs the download, flatten, and index steps on a small sample (first 10 adapters) and asserts the existence and integrity of `skill_index.npz`.  
  *Verification*: Test passes and prints “Ingestion pipeline OK”.

---

## Phase 2 – Retrieval & interpolation (User Story 2)

- [ ] T020 [P] **Sentence‑transformer encoder** – `code/retrieval/text_encoder.py` loads `all-MiniLM-L6-v2` on CPU, encodes all task descriptions, and saves `data/processed/text_embeddings.npy`.  
  *Verification*: Shape of the embeddings is `(N, 384)`; a checksum entry is added to `state/artifact_hashes.yaml`.

- [ ] T021 [P] **Query generation** – `code/retrieval/query.py` provides a CLI `--task-desc "<text>"` that (i) encodes the description, (ii) computes cosine similarity against `skill_index.npz`, (iii) logs `embedding_latency_ms`, `retrieval_latency_ms`, `total_skill_selection_latency_ms` to `data/results/latency_metrics.json`, and (iv) raises a `ValueError` if the nearest‑neighbor distance exceeds `OOD_THRESHOLD`.  
  *Verification*: Running the CLI on a sample description produces the JSON file with the three latency fields.

- [ ] T022 [P] **Retrieval strategies** – `code/retrieval/strategies.py` implements three functions:  
  1. `nearest_neighbor(task_id)` → writes `artifacts/synthesized_adapters/nn_{task_id}.npz`  
  2. `arithmetic_mean(task_id, k)` → writes `artifacts/synthesized_adapters/mean_{task_id}.npz`  
  3. `cosine_weighted(task_id, k)` → writes `artifacts/synthesized_adapters/weighted_{task_id}.npz`  
  All functions verify dimensionality, handle `<k` results with a warning, and respect the OOD check.  
  *Verification*: Unit tests in `tests/unit/test_strategies.py` confirm that the three outputs have identical shapes and that weighted averaging respects similarity weights.

- [ ] T023 [P] **Contract validation for retrieval output** – `tests/contract/test_schemas.py` validates that each generated adapter file conforms to `skill_vector.schema.yaml`.  
  *Verification*: All schema checks pass.

---

## Phase 3 – Proxy ground‑truth & linearity validation (User Story 2 continued)

- [ ] T030 [P] **Generate held‑out composite task list** – `code/validation/generate_eval_tasks.py` creates `data/processed/eval_tasks.yaml` by randomly pairing two distinct task descriptions (fixed seed 42).  
  *Verification*: The YAML file contains at least 5 composite entries.

- [ ] T031 [P] **Proxy ground‑truth synthesis** – `code/validation/generate_proxy_gt.py` reads the component vectors for each composite task, computes their arithmetic mean, and writes `data/processed/proxy_ground_truth.npz`.  
  *Verification*: The file contains a `vectors` array; its shape matches the number of composite tasks.

- [ ] T032 [P] **Reconstruction‑error computation** – `code/validation/reconstruction_error.py` compares each synthesized adapter (from T022) against the corresponding proxy ground truth, writes `data/results/reconstruction_error.json` with `mean` and `max` cosine distances, and flags a failure if `max > 0.05`.  
  *Verification*: JSON file exists; `max` ≤ 0.05 for the test run.

- [ ] T033 [P] **Text‑weight alignment check** – `code/validation/correlation_check.py` computes Pearson correlation between pairwise text‑embedding cosine distances and weight‑vector cosine distances (using the proxy ground truth), writes `data/results/correlation.json`.  
  *Verification*: The JSON contains `"pearson_correlation": 0.73` (example) and a p‑value.

- [ ] T034 [P] **Linearity validation aggregation** – `code/validation/linearity_check.py` merges the reconstruction‑error and correlation results, writes `data/results/linearity_validation.json` conforming to `linearity_schema.json`.  
  *Verification*: The file includes `"linearity_valid": true` when `max_error ≤ 0.05` and `"correlation_coefficient"` from T033.

---

## Phase 4 – Performance evaluation (User Story 3)

- [ ] T040 [P] **Base LLM preparation** – download TinyLlama‑1B‑Chat GGUF (`Q4_K_M`) to `data/models/tinyllama.gguf`, verify size < 7 GB, run a dry‑run inference to confirm memory fits.  
  *Verification*: `data/models/tinyllama.gguf` exists; a log file records < 7 GB RAM usage.

- [ ] T041 [P] **Environment‑logic wrapper** – `code/evaluation/init_env_logic.py` provides `run_task(adapter_path, task_id) → bool` for the ALFWorld‑style simulation (stubbed with deterministic success flags for the proxy tasks).  
  *Verification*: Unit test confirms that a known adapter yields the expected Boolean.

- [ ] T042 [P] **Evaluation runner** – `code/evaluation/runner.py` loads the base model, applies a given adapter, calls `run_task`, repeats **N = 5** independent runs per composite task, records binary outcomes, and writes `data/results/stats_raw.json` with success rates for each strategy and the baseline.  
  *Verification*: After a full run, `stats_raw.json` contains entries like `"nearest_neighbor": 0.68` for every task.

- [ ] T043 [P] **Statistical testing (primary comparisons)** – `code/evaluation/stats.py` reads `stats_raw.json`, performs a paired t‑test (or Wilcoxon when normality fails) comparing each strategy against the baseline, writes raw p‑values to `data/results/stats_raw_pvalues.json`, and logs any zero‑variance warnings.  
  *Verification*: JSON file contains `"nearest_neighbor": {"raw_p_value": 0.12, "significant": false}` etc.

- [ ] T044 [P] **Sensitivity sweep over *k*** – `code/evaluation/run_sensitivity_sweep.py` varies `k ∈ {3,5,10}`, repeats the evaluation (using the same N = 5 runs), and writes `data/results/sensitivity_raw.json` with raw p‑values per *k*.  
  *Verification*: The file lists three entries keyed by `k`.

- [ ] T045 [P] **Benjamini‑Hochberg correction** – `code/evaluation/bh_correction.py` consumes both `stats_raw_pvalues.json` and `sensitivity_raw.json`, applies BH correction separately, and writes `data/results/stats_bh_corrected.json` and `data/results/sensitivity_bh_corrected.json`.  
  *Verification*: Each corrected file contains `"bh_corrected_p_value"` fields ≤ 1.

- [ ] T046 [P] **Report generation** – `code/evaluation/report_generator.py` aggregates:  
  * summary (total tasks, runs per task, baseline success rate)  
  * comparisons (raw & BH‑corrected p‑values)  
  * alignment_check (pearson correlation, validity)  
  * linearity_validation (reconstruction error, validity)  
  * latency metrics (from `latency_metrics.json`)  
  * power estimate (via `statsmodels.stats.power.TTestIndPower`)  
  and writes the final `data/results/stats_report.json` conforming to `stats_report.schema.yaml`.  
  *Verification*: JSON validates against the schema; `power_estimate` is ≥ 0.8 or a warning is logged.

---

## Phase 5 – Documentation & final artefacts

- [ ] T050 **Generate final markdown report** – `code/evaluation/final_report.py` reads `stats_report.json`, `latency_metrics.json`, `linearity_validation.json`, and the generated plots (see T058) to produce `reports/final_report.md`. The markdown must contain the mandatory sections:  
  1. **Methodology** (data sources, base model)  
  2. **Results** (table of success rates)  
  3. **Latency** (breakdown table)  
  4. **Linearity Validation** (PASS/FAIL, max error)  
  5. **Statistical Significance** (BH‑corrected primary & sensitivity p‑values)  
  6. **Statistical Power** (numeric estimate, note if < 0.8)  
  7. **Zero‑Variance Incidents** (list any skipped tests)  
  8. **Data Integrity** (confirmation that all inputs are real)  
  *Verification*: The file exists and includes the eight headings.

- [ ] T051 **Create README** – populate `README.md` with installation steps, usage example (`python -m code.main --task "my composite task"`), and links to `reports/final_report.md` and the generated PNG plots in `reports/plots/`.  
  *Verification*: `README.md` renders correctly on GitHub preview.

- [ ] T052 **Generate summary markdown** – `reports/summary.md` must succinctly list: research question, key quantitative findings (baseline vs. each strategy), whether SC‑001–SC‑005 were satisfied, and any limitations.  
  *Verification*: The file contains a bullet list with the required items.

- [ ] T053 **Archive all artefacts** – create an `archive/` directory and copy the following into it (preserving relative paths):  
  * `data/raw/` (original LoRA files)  
  * `data/processed/skill_index.npz`  
  * `data/processed/text_embeddings.npy`  
  * `data/results/` (all JSON/YAML result files)  
  * `reports/` (final report, summary, plots)  
  * `state/` (hashes and any pipeline state)  
  * `logs/` (any stdout/stderr captures).  
  Add a short `archive/README.txt` describing the archive contents.  
  *Verification*: `tree archive/` shows the expected hierarchy; a checksum manifest (`archive/manifest.sha256`) lists SHA‑256 hashes for every archived file.

- [ ] T054 **Run full end‑to‑end pipeline** – execute the top‑level CLI (`python -m code.main --runs-per-task 5`) which internally triggers all previous steps (download → index → query → synthesis → evaluation → stats → report).  
  *Verification*: After completion, the following artefacts exist and pass schema validation:  
    * `data/results/stats_report.json`  
    * `reports/final_report.md`  
    * `reports/summary.md`  
    * `archive/` populated as above.  
  Additionally, the CI log contains “Pipeline completed successfully”.

- [ ] T055 **Verify final deliverables** – run a sanity‑check script (`code/utils/verify_final_outputs.py`) that loads `stats_report.json` and asserts the presence of all required top‑level keys (`summary`, `comparisons`, `alignment_check`, `linearity_validation`, `power_estimate`, `warnings`). It also checks that `reports/final_report.md` contains the three mandatory sections (Statistical Power, Zero‑Variance Incidents, Data Integrity).  
  *Verification*: Script exits with code 0 and prints “All final outputs verified”.

- [ ] T056 **Human‑readable hand‑off** – create `docs/handoff.md` summarising the pipeline, the exact versions of all software, the location of the archived artefacts, and any open limitations. This document will be used by the downstream paper‑writing stage.  
  *Verification*: File exists and includes a “Limitations” subsection.

---

## Phase 6 – Outstanding reviewer‑driven revisions (re‑plan)

The following tasks were previously flagged as incomplete or malformed; they have been re‑specified above with clear artefacts and verification steps.

- [ ] T078 **Execute full pipeline with N = 5 runs per task** – see T054.  
- [ ] T079 **Validate `stats_report.json` contains all required fields** – see T055.  
- [ ] T080 **Produce `final_report.md` with the three mandated sections** – see T050.  
- [ ] T083 **Update `README.md` with results and plot links** – see T051.  
- [ ] T084 **Final review of `spec.md` and `plan.md` against the completed artefacts** – run `code/utils/compare_spec_plan.py` which diffs the assumptions and constraints in the spec/plan with the actual values recorded in `state/artifact_hashes.yaml` and `data/results/`.  
- [ ] T085 **Create `reports/summary.md`** – see T052.  
- [ ] T086 **Archive the full reproducibility bundle** – see T053.

---

### Dependency‑to‑requirement mapping (summary)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (LoRA ingestion & index) | T010, T011, T012 |
| FR‑002 (sentence‑transformer) | T020 |
| FR‑003 (retrieval & interpolation) | T021, T022 |
| FR‑004 (apply adapters & evaluate) | T041, T042 |
| FR‑005 (statistical testing) | T043, T045 |
| FR‑006 (BH correction) | T045 |
| FR‑007 (text‑weight alignment) | T033 |
| FR‑008 (multiple runs) | T042 |
| SC‑001 (success‑rate degradation ≤ 10 %) | T042 → T046 |
| SC‑002 (p < 0.05 after BH) | T045 → T046 |
| SC‑003 (skill‑selection latency) | T021 → T046 |
| SC‑004 (top‑k sensitivity) | T044 → T045 |
| SC‑005 (reconstruction error ≤ 0.05) | T032 → T034 |

--- 

*All tasks above are expressed in the canonical checklist format and reference concrete file paths, enabling deterministic verification by the execution stage.*
