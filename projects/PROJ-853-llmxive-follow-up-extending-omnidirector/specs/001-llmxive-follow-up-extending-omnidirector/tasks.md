# Tasks: llmXive follow‑up: extending “OmniDirector: General Multi‑Shot Camera Cloning without Cross‑Paired D”

**Inputs**: `spec.md`, `plan.md`, data model, JSON schemas, and any reviewer feedback.  
All tasks follow the canonical checklist format. Unchecked boxes (`[ ]`) indicate work that still needs to be completed and verified. Checked boxes (`[X]`) would be used only after a task passes its verification step – none are currently checked because the previous implementation did not produce verifiable artifacts.

---

## Phase 1 – Project scaffolding & early end‑to‑end runnable example

- [ ] T001 [US1] Create the required directory hierarchy.  
  **Paths**: `code/`, `code/data/`, `code/geometry/`, `code/analysis/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`, `logs/`.  
  *Verification*: CI step runs `tree -L 3 .` and asserts that each listed directory exists and is non‑empty (contains at least an `__init__.py` placeholder where appropriate).  
  *Depends on*: none – must run before any task that writes into these directories.

- [ ] T002 [US1] Initialise a Python 3.11 package and create a fully version‑pinned `requirements.txt`.  
  **Paths**: `code/requirements.txt` (pinned exact versions of `opencv-python`, `numpy`, `pandas`, `scipy`, `pytest`, `pyyaml`), `code/__init__.py`.  
  *Verification*: `pip install -r code/requirements.txt` succeeds on the CI runner without warnings, and all version numbers are exact (e.g., `opencv-python==4.8.0.76`).  

- [ ] T003 [US1] Add linting and formatting configuration.   <!-- FAILED-IN-EXECUTION: code/lint.sh exit=1 -->
  **Paths**: `.ruff.toml`, `.flake8`, `pyproject.toml` (with Black settings), `code/lint.sh` (runs `ruff check . && black --check .`).  
  *Verification*: CI runs `code/lint.sh` and fails if any style violations are reported.

- [ ] T004 [US1] Implement a deterministic dataset‑download script that fetches the real OmniDirector zip archive (no synthetic fallback for primary pipeline).  
  **Paths**: `code/data/download.py`, resulting archive `data/raw/omnidirector.zip`.  
  *Verification*: After `python -m code.data.download`, the zip file exists, its size > 0 KB, and a SHA‑256 checksum is written to `code/data/download.log`.  
  *Depends on*: T001.

- [ ] T005 [US1] Provide a CLI entry point that runs the full pipeline on a minimal synthetic subset (≤ 5 sequences).  
  **Paths**: `code/main.py` (argument parser with `--run demo`), `quickstart.md` (command example).  
  *Verification*: CI executes `python -m code.main --run demo` and checks that `report.md` is created within 30 minutes and contains a non‑empty Pearson‑r value.  
  *Depends on*: T002, T004.

- [ ] T025 [US1] Set and document fixed random seeds for all stochastic components (e.g., synthetic fallback generation, line‑detection randomness).  
  **Path**: `code/config.py` (defines `SEED = 42` and applies it globally).  
  *Verification*: Unit tests import `code.config` and assert that `np.random.rand()` is deterministic across runs.

---

## Phase 2 – Dataset ingestion & geometric filtering (User Story 1)

- [ ] T006 [US1] Implement dataset loader that extracts video frames and metadata from the zip produced by T004.  
  **Path**: `code/data/ingestion.py` (`load_raw_dataset()` returns a generator of `GridFrame` objects).  
  *Verification*: Unit test `code/tests/unit/test_ingestion.py` loads the first two frames without raising exceptions and logs the discovered sequence count.  
  *Depends on*: T004.

- [ ] T007 [US1] Implement the geometric‑filtering heuristic (FR‑001) and write a curated CSV.  
  **Paths**: `code/data/ingestion.py` (`filter_sequences()`), output `data/processed/filtered_sequences.csv`.  
  *Verification*: CSV validates against `specs/001-llmxive-follow-up-extending-omnidirector/contracts/dataset.schema.yaml` (using `jsonschema`), and every retained row satisfies `radial_motion_deg > 15 or z_velocity_avg > 0.1`.  
  *Depends on*: T006.

- [ ] T008 [US1] Log excluded sequences with reasons.  
  **Path**: `logs/ingestion.log`.  
  *Verification*: CI checks that the log contains at least one entry with “excluded – insufficient spatial volume”.  
  *Depends on*: T007.

- [ ] T022 [US1] Compute and record the dataset‑filtering success rate (SC‑004).  
  **Path**: `code/analysis/filter_metrics.py` (generates `data/processed/filter_success_rate.txt`).  
  *Verification*: The text file contains a percentage value equal to `retained / total_raw * 100`.  
  *Depends on*: T007.

---

## Phase 3 – CPU‑based perspective inversion solver (User Story 2)

- [ ] T009 [US2] Define the canonical unit‑grid model and implement line‑detection / intersection extraction.  
  **Path**: `code/geometry/utils.py` (`WORLD_GRID_POINTS`, `detect_grid_lines()`, `compute_intersections()`).  
  *Verification*: Unit test `code/tests/unit/test_geometry_utils.py` runs on a synthetic grid image and asserts ≥ 4 intersection points are returned with pixel error ≤ 2 px.  
  *Depends on*: T007.

- [ ] T010 [US2] Implement the `solvePnP`‑based pose estimator for a single sequence, handling scale ambiguity.  
  **Path**: `code/geometry/solver.py` (`solve_sequence_pose()`).  
  *Verification*: Unit test `code/tests/unit/test_solver.py` feeds known synthetic 2‑D projections and checks that the reprojection error ≤ 2 px and that a `scale_factor` flag is present.  
  *Depends on*: T009.

- [ ] T011 [US2] Run the solver over all retained sequences, compute relative 3D bounding‑box dimensions (FR‑003), and write pose estimates plus bounding‑box results.  
  **Paths**: `code/geometry/solver.py` (pipeline driver), output `data/processed/poses_estimated.json` and `data/processed/reconstruction_results.csv` (includes `reconstructed_dimensions`).  
  *Verification*: The JSON file conforms to the `output.schema.yaml` “results” entry for each sequence and the CSV contains columns `height`, `width`, `depth`.  
  *Depends on*: T010.

- [ ] T023 [US2] Compute reconstruction‑error metrics (FR‑004) by comparing estimated dimensions against ground‑truth.  
  **Path**: `code/analysis/error_metrics.py` (produces updated `data/processed/reconstruction_results.csv` with `error_metrics` fields).  
  *Verification*: Each row now includes `height_error`, `width_error`, `depth_error`, `aspect_ratio_error`, `mean_absolute_error`.  
  *Depends on*: T011.

- [ ] T012 [US2] Detect and flag sequences that exceed the solvable distortion threshold (FR‑007).  
  **Path**: `logs/solver_warnings.log`.  
  *Verification*: CI asserts that any sequence with `radial_motion_deg > 120` is recorded with `high_complexity: true`.  
  *Depends on*: T011.

---

## Phase 4 – Statistical validation & correlation analysis (User Story 3)

- [ ] T013 [US3] Compute per‑sequence error metrics, complexity metrics, and aggregate summary statistics including Pearson correlation (FR‑005).  
  **Path**: `code/analysis/metrics.py` (`compute_error_metrics()`, `pearson_correlation()`, `filter_success_rate()`).  
  *Verification*: The generated `data/processed/reconstruction_results.csv` contains a row `summary_statistics` with non‑empty fields `pearson_correlation`, `mean_error_overall`, and `synthetic_control_error_rate`.  
  *Depends on*: T023, T012.

- [ ] T014 [US3] Implement aspect‑ratio validation against known synthetic room ratios (± 5 %) (FR‑006).  
  **Path**: `code/analysis/validation.py` (`validate_aspect_ratio()`).  
  *Verification*: Unit test `code/tests/unit/test_validation.py` confirms that a sequence with a ground‑truth aspect ratio of 1.33 passes, while one deviating by > 5 % fails.  
  *Depends on*: T023.

- [ ] T015 [US3] Perform the synthetic‑control experiment (FR‑008) and record failure rates.  
  **Path**: `code/analysis/validation.py` (`synthetic_control_check()`).  
  *Verification*: After pipeline run, rows where `randomized_depth == true` have `error_metrics.mean_absolute_error` > 0.5 × ground‑truth and `validation.scale_anchored == false`.  
  *Depends on*: T023.

- [ ] T016 [US3] Generate the final statistical report with tables, figures, Pearson r line, and discussion of limitations.  
  **Path**: `report.md`.  
  *Verification*: The markdown includes a non‑empty “Pearson r = …” line, an error‑distribution histogram (embedded as a base‑64 PNG data URI), and a concise discussion of scale ambiguity and synthetic‑control outcomes.  
  *Depends on*: T013, T014, T015.

---

## Phase 5 – Polish, reproducibility, and handoff

- [ ] T017 [US0] Add comprehensive documentation.  
  **Paths**: `code/README.md` (overview, installation, usage), `code/docs/architecture.md` (pipeline diagram, data‑flow), `quickstart.md` (step‑by‑step command).  
  *Verification*: CI runs `mdformat -c` on all markdown files; the command exits with status 0.  
  *Depends on*: T001‑T016.

- [ ] T018 [US0] Implement logging configuration and memory‑profiling hooks; verify peak RAM ≤ 6 GiB.  
  **Paths**: `code/logging.py` (central logger), `logs/memory_profile.log`.  
  *Verification*: After a full run, `memory_profile.log` contains a line “Peak RAM = X MiB” and the value is ≤ 6 GiB.  
  *Depends on*: T020.

- [ ] T019 [US0] Optimize line‑detection performance to meet the CI time budget.  
  **Path**: `code/geometry/utils.py` (replace Canny with Sobel, add optional multiprocessing pool).  
  *Verification*: Benchmark script `code/benchmark_line_detection.py` reports average per‑frame processing < 100 ms on the CI runner; CI fails if the average exceeds this threshold.  
  *Depends on*: T009.

- [ ] T020 [US0] Verify the entire end‑to‑end pipeline on the full filtered dataset fits within the 6‑hour CI budget and record execution time (SC‑005).  
  **Path**: CI workflow step `run_full_pipeline.sh` (records wall‑clock time to `logs/runtime.log`).  
  *Verification*: CI records total wall‑clock time; the step succeeds only if time ≤ 6 h and `report.md` is present with all required sections.  
  *Depends on*: T019.
