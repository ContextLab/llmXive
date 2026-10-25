# Tasks: Symbolic backward‑step substitution in Bidirectional Evolutionary Search  

**Inputs**: `specs/001-symbolic-bes/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

---  

## Phase 0 – Design and documentation  

- [ ] T012 [P] [US1] Write **design_dataset.md** documenting puzzle‑type choices, complexity scaling, random‑seed handling, and provenance metadata.  
  • File: `specs/001-symbolic-bes/design_dataset.md`  
  • Verification: file exists, contains sections *Puzzle Types*, *Scaling Plan*, *Seed Management* and is syntactically valid Markdown.  

- [ ] T013 [P] [US2] Write **stat_analysis_plan.md** specifying TOST bounds, α = 0.0497, power = 0.8, and effect‑size targets.  
  • File: `specs/001-symbolic-bes/stat_analysis_plan.md`  
  • Verification: file exists and includes numeric values for Δ, α, power, and required sample size.  

- [ ] T014 [P] [US3] Record baseline LLM choice (e.g., `distilbert-base-uncased`) with exact HuggingFace commit hash and `device='cpu'`.  
  • File: `specs/001-symbolic-bes/baseline_architecture.md`  
  • Verification: file lists model identifier, commit SHA, and device configuration.  

- [ ] T015 [P] [US4] Validate JSON‑Schema contracts `dataset.schema.yaml` and `output.schema.yaml`.  
  • Files: `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`  
  • Verification: running `python -c "import yaml, sys; yaml.safe_load(open('contracts/dataset.schema.yaml'))"` and the same for `output.schema.yaml` exits without exception.  

- [ ] T016 [P] [US5] Create **quickstart.md** with a reproducible command chain (`python -m code.main --pilot`) and list expected output locations.  
  • File: `specs/001-symbolic-bes/quickstart.md`  
  • Verification: file exists; the command runs without error on a clean checkout, producing non‑empty `data/processed/pilot/` artifacts.  

- [ ] T020 [P] [US5] Compute SHA‑256 checksums for every file created under `data/` and write a manifest `data/checksums.json`.  
  • File: `data/checksums.json` (generated)  
  • Verification: after each data‑generation step a checksum entry is added; a test `tests/integration/test_checksums.py` validates that the manifest matches actual file hashes.  

- [ ] T021 [P] [US5] Pin all random seeds (`random`, `numpy`, `torch`) at program start and record them in `data/provenance/seeds.json`.  
  • File: `data/provenance/seeds.json` (generated)  
  • Verification: a test `tests/unit/test_seed_pin.py` checks that the seeds file exists and matches the values set in code.  

---  

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [P] [US1] Implement the **puzzle dataset generator** (`code/dataset/generator.py`) so that it writes a **single JSON object** containing a top‑level `"puzzles"` list (conforming to `contracts/dataset.schema.yaml`). Also implement the **deterministic verifier** (`code/dataset/verifier.py`).  
  • Paths: `code/dataset/generator.py`, `code/dataset/verifier.py`  
  • Requirements:  
    – `generator.py` creates `data/raw/puzzles.json` with structure `{ "puzzles": [ … ] }` (no JSONL).  
    – Each puzzle record includes all required fields (`puzzle_id`, `puzzle_type`, `constraints`, `initial_state`, `target_state`, `verifier_script`, `complexity_score`).  
    – `verifier.py` provides a function `verify(solution_text: str, puzzle_path: str) -> (bool, str)` that runs in ≤ 100 ms and returns a boolean plus an error code.  
  • Verification: `pytest code/tests/test_generator.py code/tests/test_verifier.py` passes; the generator test loads the file with `json.load` and validates against `dataset.schema.yaml`; the verifier benchmark asserts runtime < 0.1 s.  

- [ ] T002 [P] [US2] Implement the **symbolic planner** (`code/symbolic/planner.py`) and **parser** (`code/symbolic/parser.py`) with concrete exception classes `ParseFailure` and `ContradictionDetected`.  
  • Paths: `code/symbolic/planner.py`, `code/symbolic/parser.py`, `code/symbolic/exclusion_logger.py`  
  • Requirements: planner either returns an ordered list of sub‑goals **or** raises one of the two exception classes; exclusion logger writes `data/processed/exclusions.json` with puzzle IDs and reasons.  
  • Verification: `pytest code/tests/test_symbolic_planner.py` passes (exception handling uses the actual classes, not string literals).  

- [ ] T019 [P] [US1] Generate **evaluation logs** for each solution attempt, writing `data/processed/evaluation_log.jsonl` and validate each entry against a newly added `contracts/evaluation_log.schema.yaml`.  
  • Paths: `code/analysis/evaluation_logger.py`, `contracts/evaluation_log.schema.yaml` (new)  
  • Requirements: for every attempt the logger records `attempt_id`, `puzzle_id`, `method`, `is_valid`, `error_code`, `timestamp`; entries are validated on write.  
  • Verification: `pytest code/tests/test_evaluation_log.py` ensures schema compliance and that the file is non‑empty after a pilot run.  

- [ ] T003 [P] [US2] Implement the **BES evolutionary loop** (`code/bes/population.py`, `code/bes/forward_step.py`, `code/bes/backward_step.py`, `code/bes/main.py`) and ensure the top‑level entry point (`code/main.py`) runs end‑to‑end **and exits with status 0**.  
  • Paths: `code/bes/population.py`, `code/bes/forward_step.py`, `code/bes/backward_step.py`, `code/bes/main.py`, `code/main.py`  
  • Requirements:  
    – Forward step uses the CPU‑only LLM (`distilbert-base-uncased`) with `device='cpu'`.  
    – Backward step calls the symbolic planner from T002.  
    – Fitness evaluation invokes `code/dataset/verifier.py` with a timeout (≤ 2 s).  
    – The loop logs per‑generation statistics to `data/processed/run_log.jsonl`.  
    – The CLI `python -m code.main --pilot` completes without error and returns exit code 0.  
  • Verification: executing `python -m code.main --pilot` creates non‑empty `data/processed/pilot/attempts.jsonl` and `data/processed/pilot/evaluations.jsonl` with real `cost_time` values; `pytest code/tests/test_bes_loop.py` passes.  

---  

## Phase 2 – Complete the study and validate its evidence  

- [ ] T004 [P] [US1] Generate the **full scaled dataset** for three sizes (N = 10, 100, 500) and validate its distribution.  
  • Paths: `data/raw/puzzles_N10.json`, `data/raw/puzzles_N100.json`, `data/raw/puzzles_N500.json`, `code/dataset/validate_distribution.py`  
  • Verification: script writes `data/processed/distribution_report.json` and `data/processed/distribution_validation.json`; both exist, pass schema validation, and the report lists counts per puzzle type and complexity bucket.  

- [ ] T005 [P] [US2] Implement the **neural‑verifier baseline** (`code/bes/neural_verifier.py`, `code/bes/neural_baseline_runner.py`).  
  • Paths: as listed.  
  • Requirements: record wall‑clock time, estimated energy (`cpu_time * TDP_WATTS`), and a **GPU‑hours estimate** using a documented conversion factor; produce `data/processed/neural_baseline_results.json` that conforms to `contracts/output.schema.yaml` plus a supplemental `data/processed/gpu_hours_report.json`.  
  • Verification: `data/processed/neural_baseline_results.json` contains real numeric fields (`run_id`, `method="neural"`, `total_instances`, `success_count`, `mean_time`, `p_value_z`, `p_value_t`, `significance`, `logical_contradiction_rate`) and `gpu_hours_report.json` includes `gpu_hours_estimate` and a comparison against the symbolic method.  

- [ ] T006 [P] [US2] Execute the **symbolic‑guided BES** on all three puzzle sets and aggregate results.  
  • Paths: `code/bes/result_aggregator.py`, output `data/processed/symbolic_bes_results.json`.  
  • Verification: aggregated JSON validates against `contracts/output.schema.yaml` and includes non‑zero `success_count` and `excluded_instances`.  

- [ ] T007 [P] [US3] Run **statistical analysis** (`code/analysis/stats.py`, `code/analysis/cost_calculator.py`).  
  • Paths: as listed; output `data/processed/statistical_report.json`.  
  • Requirements: compute two‑proportion Z‑test, paired t‑test, TOST equivalence test (Δ = 0.05), and include `p_value_z`, `p_value_t`, `significance`.  
  • Verification: `code/tests/test_stats.py::test_z_test_significance` passes; report JSON contains all required keys with real numeric values.  

- [ ] T022 [P] [US3] Implement the **primary paired McNemar’s test** for success‑rate comparison and add its p‑value (`p_value_mcnemar`) to `data/processed/statistical_report.json`.  
  • Paths: `code/analysis/mcnemar_test.py` (new) integrated into `stats.py`.  
  • Verification: `code/tests/test_mcnemar.py` checks that the McNemar p‑value is computed correctly and appears in the final report.  

- [ ] T017 [P] [US4] Define JSON schema for `complexity_report.json` → `contracts/complexity_report.schema.yaml`.  
  • Schema fields: `run_id`, `method`, `complexity_class`, `empirical_R2`, `theoretical_class`, `discrepancy_flag`.  
  • Verification: `yaml.safe_load` on the newly created file succeeds; a test `code/tests/test_complexity_schema.py` validates a sample report against it.  

- [ ] T018 [P] [US4] Define JSON schema for `sc005_validation.json` → `contracts/sc005_validation.schema.yaml`.  
  • Schema fields: `passed` (bool), `complexity_class` (string), `notes` (string).  
  • Verification: schema loads without error; a test validates a sample validation file.  

- [ ] T008 [P] [US3] Perform **scalability analysis** (`code/analysis/complexity_empirical.py`, `code/analysis/complexity_theory.py`).  
  • Outputs: `data/processed/complexity_report.json` and `data/processed/sc005_validation.json`.  
  • Verification: both files exist and pass validation against the schemas created in T017 and T018.  

- [ ] T009 [P] [US3] Generate **result tables and figures** (`code/analysis/report.py`).  
  • Outputs: `data/results/table_summary.csv`, `figures/success_rate.png`, `figures/runtime_comparison.png`.  
  • Verification: `code/tests/test_report_links.py` asserts every table cell and figure datum originates from a source JSON file; test suite passes and files are non‑empty.  

- [ ] T010 [P] [US3] Write the **methods & results manuscript draft** (`specs/001-symbolic-bes/results.md`).  
  • File: `specs/001-symbolic-bes/results.md`  
  • Verification: all quantitative statements cite the exact JSON artifact (e.g., `data/processed/symbolic_bes_results.json`) via inline links; markdown renders without broken references.  

- [ ] T011 [P] [US3] **Re‑run the full workflow** from a clean `data/processed/` directory and produce the **paper‑stage handoff** (`specs/001-symbolic-bes/handoff.md`).  
  • File: `specs/001-symbolic-bes/handoff.md`  
  • Verification: after deleting `data/processed/*` the command `python -m code.main --full` completes without error and regenerates every result artifact; handoff file lists SHA‑256 checksums of all final JSON/CSV/PNG artifacts.  

---  

## Phase 3 – Additional contract creation (supporting Phase 2)  

*(Moved to Phase 2 to satisfy ordering constraints; retained for documentation.)*  

---  

## Dependencies & Requirement Coverage  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 | T001, T004 |
| FR‑002 | T002, T006 |
| FR‑003 | T003, T006 |
| FR‑004 | T005, T006 |
| FR‑005 | T007, T022 |
| FR‑006 | T002, T006 |
| SC‑001 | T007 |
| SC‑002 | T007 |
| SC‑003 | T002, T003 |
| SC‑004 | T007 |
| SC‑005 | T008 |
| US‑1 | T001, T004 |
| US‑2 | T002, T003, T006 |
| US‑3 | T007, T008, T009, T010, T011 |
| US‑4 | T017, T018 |
| Evaluation Log entity | T019 |
| SHA‑256 checksum generation | T020 |
| Random seed pinning | T021 |
| McNemar’s test | T022 |

All tasks respect data flow, use only project‑owned paths, and adhere to the specification and constitutional constraints.  

---  

*All checked tasks have been verified to meet their respective acceptance criteria; unchecked tasks are pending implementation or correction as noted.*  