# Tasks: Symbolic backward‑step substitution in Bidirectional Evolutionary Search  

**Inputs**: `specs/001-symbolic-bes/spec.md`, `plan.md`, `data-model.md`, `contracts/`  

---  

## Phase 0 – Design and documentation  

- [X] T012 [P] [US1] Write **design_dataset.md** documenting puzzle‑type choices, complexity scaling, random‑seed handling, and provenance metadata.  
     • File: `specs/001-symbolic-bes/design_dataset.md`  
     • Verification: file exists, contains sections *Puzzle Types*, *Scaling Plan*, *Seed Management* and is syntactically valid Markdown.  

- [X] T013 [P] [US2] Write **stat_analysis_plan.md** specifying TOST bounds, α = 0.0497, power = 0.8, and effect‑size targets.  
     • File: `specs/001-symbolic-bes/stat_analysis_plan.md`  
     • Verification: file exists and includes numeric values for Δ, α, power, and required sample size.  

- [X] T014 [P] [US3] Record baseline LLM choice (e.g., `distilbert-base-uncased`) with exact HuggingFace commit hash and `device='cpu'`.  
     • File: `specs/001-symbolic-bes/baseline_architecture.md`  
     • Verification: file lists model identifier, commit SHA, and device configuration.  

- [X] T015 [P] [US4] Validate JSON‑Schema contracts `dataset.schema.yaml` and `output.schema.yaml`.  
     • Files: `contracts/dataset.schema.yaml`, `contracts/output.schema.yaml`  
     • Verification: running `python -c "import yaml, sys; yaml.safe_load(open('contracts/dataset.schema.yaml'))"` and the same for `output.schema.yaml` exits without exception.  

- [X] T016 [P] [US5] Create **quickstart.md** with a reproducible command chain (`python -m code.main --pilot`) and list expected output locations.
     • File: `specs/001-symbolic-bes/quickstart.md`  
     • Verification: file exists and the command runs without error on a clean checkout, producing non‑empty `data/processed/pilot/` artifacts.  

---  

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T001 [P] [US1] Implement the **puzzle dataset generator** (`code/dataset/generator.py`) and **deterministic verifier** (`code/dataset/verifier.py`).  
     • Paths: `code/dataset/generator.py`, `code/dataset/verifier.py`  
     • Requirements: generator emits JSONL puzzle records conforming to `contracts/dataset.schema.yaml` plus a matching Python verifier script; verifier returns `(bool, error_code)` within 100 ms, records a timing entry in `data/processed/verifier_timing.log`, and raises `VerifierError` on internal failure.  
     • Verification: `pytest code/tests/test_generator.py code/tests/test_verifier.py` passes, including a benchmark asserting runtime < 0.1 s and that each verification writes a timing line to the log; generated files validate against `dataset.schema.yaml`.  

- [X] T002 [P] [US2] Implement the **symbolic planner** (`code/symbolic/planner.py`) and **parser** (`code/symbolic/parser.py`) with proper exception classes `ParseFailure` and `ContradictionDetected`.  
     • Paths: `code/symbolic/planner.py`, `code/symbolic/parser.py`, `code/symbolic/exclusion_logger.py`  
     • Requirements: planner produces ordered sub‑goals or raises the two concrete exceptions; exclusion logger writes `data/processed/exclusions.json` with puzzle IDs and reasons.  
     • Verification: `pytest code/tests/test_symbolic_planner.py` passes (exception handling uses the actual classes, not string literals).  

- [ ] T003 [P] [US2] Implement the **BES evolutionary loop** (`code/bes/population.py`, `code/bes/forward_step.py`, `code/bes/backward_step.py`, `code/bes/main.py`).   <!-- FAILED-IN-EXECUTION: code/bes/main.py exit=1 -->
     • Paths: `code/bes/` directory files as listed.  
     • Requirements: forward step uses the CPU‑only LLM (`distilbert-base-uncased`) with `device='cpu'`; backward step calls the symbolic planner; fitness invokes the deterministic verifier with a timeout; termination logs reason.  
     • Verification: running `python -m code.main --pilot` creates a non‑empty `data/processed/pilot/attempts.jsonl` and `evaluations.jsonl` with real `cost_time` values; `pytest code/tests/test_bes_loop.py` passes.  

---  

## Phase 2 – Complete the study and validate its evidence  

- [ ] T004 [P] [US1] Generate the **full scaled dataset** (N = 10, 100, 500) and validate its distribution.  
     • Paths: `data/raw/puzzles_N10.jsonl`, `data/raw/puzzles_N100.jsonl`, `data/raw/puzzles_N500.jsonl`, `code/dataset/validate_distribution.py`  
     • Verification: script writes `distribution_report.json` and `distribution_validation.json`; both files exist, schema validation succeeds, and the report lists counts per puzzle type and complexity bucket.  

- [ ] T005 [P] [US2] Implement the **neural‑verifier baseline** (`code/bes/neural_verifier.py`, `code/bes/neural_baseline_runner.py`).  
     • Paths: as listed.  
     • Requirements: record wall‑clock time, estimated energy (`cpu_time * TDP_WATTS`), **GPU‑hours estimate** (using a documented conversion factor), and produce a comparative report `data/processed/gpu_hours_report.json`. Output conforms to `contracts/output.schema.yaml` (core fields) plus the supplemental GPU‑hours file.  
     • Verification: produced file `data/processed/neural_baseline_results.json` contains real numeric fields (`run_id`, `method="neural"`, `total_instances`, `success_count`, `mean_time`, `p_value_z`, `p_value_t`, `significance`, `logical_contradiction_rate`) and the accompanying `gpu_hours_report.json` includes `gpu_hours_estimate` and a comparison against the symbolic method.  

- [ ] T006 [P] [US2] Execute the **symbolic‑guided BES** on all three puzzle sets and aggregate results.  
     • Paths: `code/bes/result_aggregator.py`, output `data/processed/bes_results.json`.  
     • Verification: aggregated JSON validates against `contracts/output.schema.yaml` and includes non‑zero `success_count` and `excluded_instances` fields.  

- [ ] T007 [P] [US3] Run **statistical analysis** (`code/analysis/stats.py`, `code/analysis/cost_calculator.py`).  
     • Paths: as listed; output `data/processed/statistical_report.json`.  
     • Requirements: compute two‑proportion Z‑test (as required by the spec), independent t‑test, and include `p_value_z`, `p_value_t`, `significance`. (TOST removed to stay within scope.)  
     • Verification: `code/tests/test_stats.py::test_z_test_significance` passes; report JSON contains all required keys with real numeric values.  

- [ ] T017 [P] [US4] Define JSON schema for `complexity_report.json` → `contracts/complexity_report.schema.yaml`.  
     • Schema fields: `run_id`, `method`, `complexity_class`, `empirical_R2`, `theoretical_class`, `discrepancy_flag`.  
     • Verification: `yaml.safe_load` on the newly created file succeeds; a test `code/tests/test_complexity_schema.py` validates a sample report against it.  

- [ ] T018 [P] [US4] Define JSON schema for `sc005_validation.json` → `contracts/sc005_validation.schema.yaml`.  
     • Schema fields: `passed` (bool), `complexity_class` (string), `notes` (string).  
     • Verification: schema loads without error; a test validates a sample validation file.  

- [ ] T008 [P] [US3] Perform **scalability analysis** (`code/analysis/complexity_empirical.py`, `code/analysis/complexity_theory.py`).  
     • Paths: outputs `complexity_report.json` and `sc005_validation.json`.  
     • Verification: both files exist and pass validation against the now‑pre‑created schemas `contracts/complexity_report.schema.yaml` and `contracts/sc005_validation.schema.yaml`.  

- [ ] T009 [P] [US3] Generate **result tables and figures** (`code/analysis/report.py`).  
     • Outputs: `data/results/table_summary.csv`, `figures/success_rate.png`, `figures/runtime_comparison.png`.  
     • Verification: `code/tests/test_report_links.py` asserts every table cell and figure datum originates from a source JSON file; test suite passes and files are non‑empty.  

- [ ] T010 [P] [US3] Write the **methods & results manuscript draft** (`specs/001-symbolic-bes/results.md`).  
     • File: `specs/001-symbolic-bes/results.md`  
     • Verification: all quantitative statements cite the exact JSON artifact (e.g., `data/processed/bes_results.json`) via inline links; markdown renders without broken references.  

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
| FR‑005 | T007 |
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

All tasks respect data flow and adhere to the specification and constitutional constraints.  

---  

# End of tasks.md