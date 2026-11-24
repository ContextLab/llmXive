# Tasks: llmXive follow‑up – extending “LatentSkill: From In‑Context Textual Skills to In‑Weight Latent Skills”

**Inputs**: `spec.md`, `plan.md`, existing code base, contracts, and reviewer feedback.  
All tasks are expressed as checklist items; a checked box (`[X]`) indicates completion.  
Unchecked boxes (`[ ]`) indicate work that still needs to be done.  Parallelizable tasks are marked with `[P]`.  Story labels (`[US1]`, `[US2]`, `[US3]`) tie tasks to the user‑story requirements in the specification.

---

## Phase 0 – Project bootstrap & reproducibility  

- [X] T001 [P] [US1] **Create project skeleton** – add `code/`, `tests/`, `data/`, `reports/` directories and minimal `__init__.py` files.  
  *Verification*: `git ls-files` lists the new directories; `pytest -q` runs with no import errors.

- [ ] T002 [P] [US1] **Pin exact dependencies** – write `requirements.txt` with the versions listed in the plan (e.g., `torch==2.1.0`, `numpy==1.24.3`, `sentence‑transformers==2.2.2`, `datasets==2.19.0`, `bitsandbytes==0.43.1`).   <!-- FAILED-IN-EXECUTION: code/verify_requirements.py exit=1 -->
  *Verification*: `pip install -r requirements.txt` succeeds without conflicts.

- [X] T003 [P] **Configure reproducibility utilities** – add `code/utils/config.py` that (i) sets a global random seed, (ii) defines project‑wide path constants (`paths.DATA_RAW`, `paths.DATA_PROCESSED`, …), and (iii) stores a small constant `OOD_THRESHOLD = 0.5`.  
  *Verification*: Importing `config` prints the seed and path values; a unit test confirms deterministic RNG output.

---

## Phase 1 – Data ingestion & Skill‑Vector index (User Story 1)

- [ ] T004 [P] [US1] **Download original LatentSkill LoRA adapters** – `code/ingest/download_weights.py` attempts to fetch the official LoRA adapters (A and B matrices) for ALFWorld and Search‑QA from the LatentSkill repository via a verified URL/repo. The script aborts with a non‑zero exit code if any file is missing.  
  *Verification*: After execution, `ls data/raw/lora_weights/*.safetensors` shows the expected files and a status file `data/processed/download_status.json` contains `"status": "success"`.

- [ ] T004a [P] **Proxy fallback download** – if the official adapters are unavailable, `code/ingest/download_proxy.py` streams the verified proxy dataset `mrm8488/peft-examples` via `datasets.load_dataset(..., streaming=True)`, writes each `adapter.safetensors` to `data/raw/lora_weights/`, and aborts with a non‑zero exit code if any file is missing.  
  *Verification*: Same as T004 but with a distinct log entry indicating proxy usage.

- [ ] T005 [P] [US1] **Flatten & L2‑normalize LoRA weights** – `code/ingest/flatten_lora.py` loads the A/B matrices from each safetensors file, flattens them to a 1‑D `float32` vector, applies L2 normalisation, checks that all adapters share the same dimensionality, and writes `data/processed/weights_flattened.npz`.  
  *Verification*: `np.load(...).files` includes `vectors`; all vectors have identical shape; a SHA‑256 hash is recorded in `state/artifact_hashes.yaml`.

- [ ] T006 [P] [US1] **Build Skill‑Vector database** – `code/ingest/build_index.py` reads `weights_flattened.npz`, merges it with task IDs and descriptions from `data/raw/task_descriptions.json`, and writes the compressed archive `data/processed/skill_index.npz`.  
  *Verification*: Loading the archive yields arrays `vectors`, `task_ids`, `descriptions`; validation against `skill_vector.schema.yaml` passes.

- [ ] T007 [P] **Unit‑test ingestion pipeline** – `tests/unit/test_ingestion.py` asserts that (i) each flattened vector length equals `A_dim * B_dim`, (ii) the index file contains the expected number of entries, and (iii) the SHA‑256 hash matches the recorded value.  
  *Verification*: `pytest tests/unit/test_ingestion.py -q` reports all tests passed.

---

## Phase 2 – Text encoding & Retrieval strategies (User Story 2)

- [ ] T008 [P] [US2] **Encode task descriptions** – `code/retrieval/text_encoder.py` loads the CPU‑friendly sentence‑transformer `all‑MiniLM‑L6‑v2`, encodes all task descriptions, and saves `data/processed/text_embeddings.npy`.  
  *Verification*: The NumPy file has shape `(N, 384)`; a checksum entry is added to `state/artifact_hashes.yaml`.

- [ ] T009 [P] [US2] **Implement retrieval & interpolation functions** – `code/retrieval/strategies.py` provides three callable utilities:  
    1. `nearest_neighbor(query_vec, k=1)` → writes `data/processed/synthesized/nn_{task_id}.npz`  
    2. `arithmetic_mean(query_vec, k)` → writes `data/processed/synthesized/mean_{task_id}.npz`  
    3. `cosine_weighted(query_vec, k)` → writes `data/processed/synthesized/weighted_{task_id}.npz`  
  All functions verify dimensionality, issue a warning if fewer than `k` neighbors exist, and respect the `OOD_THRESHOLD`.  
  *Verification*: `tests/unit/test_strategies.py` checks that the three outputs have identical shapes and that weighted averaging uses the correct similarity weights.

- [ ] T028 [P] **Top‑k sensitivity analysis** – `code/retrieval/sensitivity.py` runs the three strategies for `k ∈ {3,5,10}` on the held‑out composite tasks, records success rates and latency per `k`, and writes `data/metrics/sensitivity_k.json`.  
  *Verification*: The JSON file exists and contains entries for each `k` value; schema validation passes.

- [ ] T010 [P] **Schema validation for synthesized adapters** – `tests/contract/test_synthesized_schema.py` validates each generated `.npz` file against `skill_vector.schema.yaml`.  
  *Verification*: All schema checks pass for a sample of adapters.

---

## Phase 3 – Proxy ground‑truth & Linearity validation (User Story 2 continued)

- [ ] T011 [P] **Create held‑out composite task list** – `code/validation/generate_composites.py` randomly pairs two distinct task descriptions (fixed seed 42) and writes `data/processed/composite_tasks.yaml` containing at least 5 composite entries.  
  *Verification*: The YAML file lists ≥ 5 composites; each entry includes the IDs of its two components.

- [ ] T012 [P] **Generate proxy ground‑truth vectors** – `code/validation/proxy_ground_truth.py` reads the component vectors for each composite task, computes their arithmetic mean, and writes `data/processed/proxy_ground_truth.npz`.  
  *Verification*: The `.npz` file contains a `vectors` array whose shape matches the number of composite tasks.

- [ ] T013 [P] **Compute reconstruction error** – `code/validation/reconstruction_error.py` compares each synthesized adapter (from T009) against the corresponding proxy ground‑truth vector, writes `data/results/reconstruction_error.json` with `mean_cosine_error` and `max_cosine_error`, and flags failure if `max_cosine_error > 0.05`.  
  *Verification*: The JSON file exists; `max_cosine_error ≤ 0.05` for the test run.

- [ ] T014 [P] **Text‑Weight alignment correlation** – `code/validation/alignment_correlation.py` calculates the Pearson correlation between pairwise cosine distances in text‑embedding space and in weight‑vector space (using the proxy ground truth), writes `data/results/alignment_correlation.json` containing `pearson_r`, `p_value`, and a boolean `valid` (true if `p_value < 0.05`).  
  *Verification*: JSON includes numeric `pearson_r` (e.g., 0.71) and `valid: true`.

- [ ] T015 [P] **Aggregate linearly validation** – `code/validation/aggregate_linearity.py` merges the reconstruction‑error and alignment‑correlation results into a single file `data/results/linearity_validation.json` that conforms to the `linearity_validation` section of `stats_report.schema.yaml`.  
  *Verification*: Schema validation passes; the file contains keys `reconstruction_error`, `threshold`, `valid`, `pearson_correlation`, `p_value`, `valid`.

---

## Phase 4 – Evaluation pipeline (User Story 3)

- [ ] T016 [P] **Prepare quantized base LLM** – download the TinyLlama‑1B‑Chat GGUF (`Q4_K_M`) to `data/models/tinyllama.gguf`, verify file size < 7 GB, and run a dry‑run inference to confirm it fits in the runner’s RAM.  
  *Verification*: Existence of the file and a log entry showing < 7 GB RAM consumption.

- [ ] T017 [P] **Environment‑logic wrapper** – `code/evaluation/env_wrapper.py` implements `run_task(adapter_path: str, task_id: str) -> bool` for the proxy ALFWorld‑style simulation (deterministic success flags based on a lookup table).  
  *Verification*: Unit test confirms that a known adapter yields the expected Boolean outcome.

- [ ] T018 [P] **Run full evaluation (N = 5 runs per task)** – `code/evaluation/runner.py` loads the base model, applies each synthesized adapter (nearest‑neighbor, mean, weighted) to every composite task, calls `run_task` five independent times, records binary outcomes, and writes `data/results/stats_raw.json` with success rates per strategy and a baseline (zero‑shot).  
  *Verification*: After execution, `stats_raw.json` contains entries such as `"nearest_neighbor": 0.68` for every task.

- [ ] T019 [P] **Statistical testing & BH correction** – `code/evaluation/stats.py` reads `stats_raw.json`, performs a paired t‑test (or Wilcoxon signed‑rank when normality fails) comparing each strategy against the baseline, applies the Benjamini‑Hochberg correction, and writes the final report `data/results/stats_report.json` that conforms to `stats_report.schema.yaml`.  
  *Verification*: JSON validation succeeds; the file includes `summary`, `comparisons` (with `raw_p_value`, `bh_corrected_p_value`, `significant`), `alignment_check`, and `linearity_validation`.

- [ ] T026 [P] **Verify ≤ 10 % degradation (SC‑001)** – `code/evaluation/verify_degradation.py` reads `stats_report.json`, computes the relative drop of each strategy versus the baseline, asserts the drop ≤ 0.10, and writes `data/metrics/degradation_check.json`.  
  *Verification*: Script exits with code 0 and the JSON file records all degradations ≤ 10 %.

- [ ] T027 [P] **Measure skill‑selection latency (SC‑003, Constitution VII)** – `code/retrieval/measure_latency.py` times each call to the three strategies on a representative query set, records per‑strategy wall‑clock times in `data/metrics/latency_metrics.json`, and asserts that the file exists.  
  *Verification*: JSON file present with keys `nearest_neighbor_ms`, `arithmetic_mean_ms`, `cosine_weighted_ms`.

- [ ] T020 [P] **Generate final markdown report** – `code/evaluation/report_generator.py` reads `stats_report.json`, `data/metrics/latency_metrics.json`, `data/results/linearity_validation.json`, and the sensitivity results, then creates `reports/final_report.md` containing the mandatory sections:  
    1. Methodology  
    2. Results (tables of success rates)  
    3. Latency analysis  
    4. Linearity validation (PASS/FAIL)  
    5. Statistical significance (BH‑corrected p‑values)  
    6. Statistical power estimate (≥ 0.8 or a warning)  
    7. Zero‑variance incidents (if any)  
    8. Data integrity statement  
  *Verification*: The markdown file exists and includes all eight headings.

- [ ] T021 [P] **Create concise summary markdown** – `reports/summary.md` lists: research question, key quantitative findings (baseline vs. each strategy), whether SC‑001 – SC‑005 are satisfied, and any limitations.  
  *Verification*: File contains a bullet list with the required items.

---

## Phase 5 – Archiving & hand‑off

- [ ] T022 [P] **Archive reproducibility bundle** – create an `archive/` directory and copy the following preserving relative paths:  
    * `data/raw/` (original LoRA files)  
    * `data/processed/` (skill index, embeddings, proxy ground truth)  
    * `data/results/` (all JSON result files)  
    * `reports/` (final report, summary, any plots)  
    * `state/` (artifact hashes, pipeline state)  
    * `logs/` (stdout/stderr captures from the pipeline)  
  Add `archive/README.txt` describing the contents and generate `archive/manifest.sha256` listing SHA‑256 hashes for every archived file.  
  *Verification*: `tree archive/` shows the expected hierarchy; `sha256sum -c archive/manifest.sha256` reports all files OK.

- [ ] T023 [P] **Verify final deliverables** – `code/utils/verify_final_outputs.py` loads `stats_report.json` and asserts the presence of all top‑level keys (`summary`, `comparisons`, `alignment_check`, `linearity_validation`, `power_estimate`, `warnings`). It also checks that `reports/final_report.md` contains the three mandatory sections (Statistical Power, Zero‑Variance Incidents, Data Integrity). The script exits with code 0 and prints “All final outputs verified”.  
  *Verification*: Running the script yields exit code 0 and the success message.

- [ ] T024 [P] **Human‑readable hand‑off document** – write `docs/handoff.md` summarising the entire pipeline, exact software versions, locations of archived artefacts, and an explicit “Limitations” subsection for downstream paper authors.  
  *Verification*: File exists and includes the required sections.

---

## Phase 6 – End‑to‑end execution checkpoint

- [ ] T025 [P] **Run the complete pipeline end‑to‑end** – execute the top‑level CLI `python -m code.main --runs-per-task 5`. This command should internally trigger tasks T004 → T018 in order, then T019 → T027, finally producing all artefacts listed above. After completion, re‑run `T023` to confirm that the final outputs are valid.  
  *Verification*: The CI log contains “Pipeline completed successfully”, and `T023` reports success.

---

### Dependency‑to‑requirement mapping (summary)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (LoRA ingestion & index) | T004, T004a, T005, T006 |
| FR‑002 (sentence‑transformer) | T008 |
| FR‑003 (retrieval & interpolation) | T009 |
| FR‑004 (apply adapters & evaluate) | T017, T018 |
| FR‑005 (statistical testing) | T019 |
| FR‑006 (Benjamini‑Hochberg) | T019 |
| FR‑007 (text‑weight alignment) | T014 |
| FR‑008 (multiple runs) | T018 |
| SC‑001 (≤ 10 % degradation) | T026 |
| SC‑002 (p < 0.05 after BH) | T019 |
| SC‑003 (skill‑selection latency) | T027 |
| SC‑004 (top‑k sensitivity) | T028 |
| SC‑005 (reconstruction error ≤ 0.05) | T013, T015 |

---

*All tasks above follow the canonical checklist format, reference concrete file paths, and include deterministic verification steps, enabling the execution stage to produce verifiable artefacts and pass the independent reviewer.*  