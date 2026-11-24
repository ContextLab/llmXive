# Tasks: Does augmenting terminal‑use agents with a retrievable “procedural memory” of verified command sequences significantly improve their success rates on complex, multi‑step scientific workflow tasks compared to standard in‑context prompting alone?

**Inputs**: `spec.md`, `plan.md`, existing project structure, reviewer feedback (none at this stage).  
All tasks are written as unchecked checkboxes; completed tasks will be checked by the CI verifier.

---  

## Phase 0 – Data preparation (addresses FR‑001, FR‑003, FR‑010)

- [ ] T001 [US1] Download the official **TUA‑Bench** dataset via `datasets.load_dataset("tua_bench", streaming=True)`, stream‑select a balanced set of 24 tasks (12 complex, 12 routine), and write the subset to `data/synthetic_tasks.json`.   <!-- FAILED-IN-EXECUTION: code/generate_synthetic_tasks.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/generate_synthetic_tasks.py exit=1 -->
  *Verification*: `len(json.load(open("data/synthetic_tasks.json"))) == 24` and each entry contains `task_id`, `description`, `validation_script`, `task_type`.  

- [ ] T002 [US2] Construct the **Procedural Memory Bank** (`data/memory_bank.json`) with exactly 50 hand‑curated `MemoryEntry` objects. For each entry compute a MiniLM‑L6‑v2 embedding and store it under the `embedding` key.  
  *Verification*: JSON schema validation against `contracts/memory_entry.schema.json`; count of entries equals 50.  

- [ ] T003 [US2] Create the **ground‑truth relevance mapping** (`data/relevance_map.json`) that maps every `task_id` to a list of `entry_id`s deemed relevant. Resolve annotator disagreements and record Cohen’s κ ≥ 0.8.  
  *Verification*: Schema validation (`task_id` → list of strings) and printed κ value ≥ 0.8.  

---  

## Phase 1 – Baseline execution (addresses FR‑001, FR‑002, FR‑005, FR‑008, FR‑009, SC‑004)

- [ ] T004 [US1] Implement `code/run_baseline.py` that loads **Llama 3.1 8B** on CPU with 4‑bit quantisation (`bitsandbytes`), sets a deterministic seed, reads `data/synthetic_tasks.json`, and executes each task with only in‑context prompting. Enforce a 15‑minute per‑task timeout and a 6‑hour per‑batch timeout.  
  *Verification*: Unit test `pytest tests/test_run_baseline.py` checks model loads, timeout logic, and produces a single‑seed JSON stub.  

- [ ] T005 [US1] Execute the baseline script for **five independent seeds (0‑4)**, storing per‑seed results in `data/baseline_results/seed_{i}.json`. Each JSON entry must conform to `contracts/execution_result.schema.yaml` (with `condition="baseline"` and `k=null`).  
  *Verification*: After each run, `jq length` equals 24 and schema validation passes; total wall‑clock time for a seed ≤ 6 h (checked via log).  

- [ ] T006 [US1] Aggregate the five seed files into `data/baseline_results/aggregated.json` containing: overall success rate, failure‑mode counts, and total batch runtime. The file must satisfy `contracts/aggregated_result.schema.json` (`condition="baseline"`, `k=null`).  
  *Verification*: Script `code/aggregate_baseline.py` produces the file; CI test asserts schema compliance and that `overall_success_rate` ∈ [0,1].  

---  

## Phase 2 – Retrieval‑augmented execution (addresses FR‑004, FR‑006, FR‑007, FR‑008, FR‑009, FR‑011, FR‑012, SC‑004)

- [ ] T007 [US2] Implement `code/retrieval.py` exposing `retrieve(task_description: str, k: int) → List[MemoryEntry]`. The function encodes the description with the same MiniLM model, computes cosine similarity against all `embedding`s in `data/memory_bank.json`, and returns the top‑k entries (or an empty list on miss).  
  *Verification*: Unit test verifies that for a known task the returned IDs match the relevance map and that `k=0` yields an empty list.  

- [ ] T008 [US2] Implement `code/run_augmented.py` which (a) loads the baseline model as in T004, (b) for each task calls `retrieve` with a configurable `k`, (c) appends the retrieved command strings to the prompt, (d) records retrieval metadata (`retrieved_ids`, `false_positive` flag) and respects the same timeouts as baseline.  
  *Verification*: Integration test runs a single task with `k=3` and checks that the resulting JSON entry contains non‑empty `retrieved_ids` and correct `false_positive` value.  

- [ ] T009 [US2] For **each top‑k value {1, 3, 5}** and **each seed (0‑4)**, run `run_augmented.py` and store results in `data/augmented_results/k_{k}/seed_{i}.json`. All entries must conform to `execution_result.schema.yaml` with `condition="augmented"` and the appropriate `k`.  
  *Verification*: After the full sweep, each directory contains five JSON files; a CI loop validates schema and that total runtime per seed ≤ 6 h.  

- [ ] T010 [US2] Aggregate the augmented results per `k` into `data/augmented_results/k_{k}/aggregated.json` (schema `aggregated_result.schema.json`). Each file must report overall success rate, **false‑positive rate (< 0.2)**, retrieval‑miss rate, and failure‑mode counts.  
  *Verification*: CI validates schema and asserts `false_positive_rate < 0.2` and that `retrieval_miss_rate` matches the proportion of empty `retrieved_ids`.  

---  

## Phase 3 – Statistical analysis (addresses FR‑006, FR‑007, SC‑001, SC‑002, SC‑003, SC‑005)

- [ ] T011 [US3] Implement `code/stats.py` to (a) load `baseline_results/aggregated.json` and each `augmented_results/k_{k}/aggregated.json`, (b) construct paired binary outcome tables (majority‑vote per task across seeds), (c) perform **McNemar’s exact test** for the primary `k=3` condition, (d) run a secondary **paired t‑test** (as allowed by the spec), and (e) output `results/stats/mcnemar_k3.json` and `results/stats/ttest_k3.json`.  
  *Verification*: Scripts print test statistic and p‑value; CI asserts that `p_value` field exists, is a float, **and `p_value < 0.05`**.  

- [ ] T012 [US3] Extend `stats.py` to apply **Holm‑Bonferroni correction** across the three k‑conditions (k = 1, 3, 5) for the McNemar tests, producing `results/stats/holm_corrected.json`.  
  *Verification*: Corrected p‑values are ≤ 1 and the file contains an `adjusted_p_values` mapping.  

- [ ] T013 [US3] Compute **task‑type specific gains** (complex vs. routine) for each k, store in `results/stats/gain_complex.json` and `results/stats/gain_routine.json`. Also compute the overall **false‑positive retrieval rate** (`results/stats/false_positive.json`).  
  *Verification*: Each file contains the fields `gain`, `baseline_rate`, `augmented_rate`; CI checks that the fields exist and that `false_positive_rate` (from the stats file) is reported (the numeric threshold is enforced in T010). No numeric gain thresholds are asserted here because SC‑002 currently lacks concrete values.  

---  

## Phase 4 – Figures, manifest, final validation, and summary (covers SC‑001‑SC‑005)

- [ ] T015 [US3] Generate publication‑ready figures (bar plot of success rates per condition/k, heatmap of p‑values, false‑positive rate chart) using `matplotlib` in `code/plot_results.py`. Save PNGs to `figures/` (e.g., `figures/success_rates.png`).  
  *Verification*: Running the script produces at least three PNG files; each file size > 5 KB and a CI test confirms they open without error.  

- [ ] T014 [US3] Summarize all statistics, effect sizes, and compliance statements in `results/summary.md`, linking to figures (generated in the previous step) and citing the JSON files.  
  *Verification*: Markdown contains sections “Statistical Tests”, “Gain per Task Type”, and “Compliance Checks”; CI verifies that all referenced paths exist (figures are now generated before this task).  

- [ ] T016 [US3] Create a **manifest** `data/manifest.json` that lists SHA‑256 checksums for every file under `data/`, `results/`, and `figures/`.  
  *Verification*: Script `code/create_manifest.py` outputs the JSON; CI checks that each listed file exists and that the checksum matches the actual file.  

- [ ] T017 [US3] Run a full **schema validation suite** (`pytest tests/test_schema_validation.py`) that loads every JSON result/aggregated file and validates it against the corresponding schema in `contracts/`.  
  *Verification*: All tests pass (exit code 0).  

- [ ] T018 [US3] Write a concise **methods & results hand‑off note** `paper/handoff.md` that enumerates the paths to all data, result JSONs, figures, and the summary markdown, and explains how to regenerate the entire pipeline from a clean checkout.  
  *Verification*: The file contains a bullet list with relative paths and a reproducibility checklist; CI test parses the file and ensures each path exists.  

- [ ] T019 [SC‑004] Verify that the **aggregate compute time** across all seeds, conditions, and k‑values does not exceed **30 hours**. The script `code/check_total_runtime.py` sums the `batch_runtime_sec` fields from all aggregated JSONs and asserts the total ≤ 108 000 seconds.  
  *Verification*: CI runs the script after all aggregation steps; it fails if the total runtime exceeds the limit.  

---  

### Dependency mapping (spec → tasks)

| Spec ID | Requirement | Implemented by |
|--------|-------------|----------------|
| FR‑001 | Load 24 tasks | T001 |
| FR‑002 | CPU‑only model, timeouts | T004, T005, T009 |
| FR‑003 | Procedural Memory Bank | T002 |
| FR‑004 | Retrieval & context augmentation | T007, T008 |
| FR‑005 | Record binary outcomes & failure modes | T005, T009 |
| FR‑006 | McNemar & paired t‑test | T011 |
| FR‑007 | Holm‑Bonferroni correction | T012 |
| FR‑008 | Five seeds per condition | T005, T009 |
| FR‑009 | Graceful batch termination | T004, T009 (timeout handling) |
| FR‑010 | Ground‑truth relevance mapping | T003 |
| FR‑011 | False‑positive retrieval rate | T010, T013 |
| FR‑012 | Configurable top‑k (1,3,5) | T008, T009 |
| SC‑001 | Significance p < 0.05 | T011, T014 |
| SC‑002 | Domain‑specific gain thresholds (to be defined) | T013 (fields only) |
| SC‑003 | False‑positive rate < 20 % | T010 |
| SC‑004 | Batch compute ≤ 6 h, overall ≤ 30 h | T005, T009, T019 |
| SC‑005 | Sensitivity to k & Holm‑Bonferroni | T012, T013 |

---  

*All tasks respect the data‑flow ordering: data preparation → baseline → augmentation → analysis → reporting.*  

*All tasks remain unchecked; CI will mark them as completed when their verification steps pass.*  
