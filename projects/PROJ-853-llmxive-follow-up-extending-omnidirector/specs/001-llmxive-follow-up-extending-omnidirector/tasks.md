# Tasks: llmXive follow‑up: extending “OmniDirector: General Multi‑Shot Camera Cloning without Cross‑Paired D”

**Inputs**: `spec.md`, `plan.md`, existing data model, contracts, and any reviewer feedback.  
All tasks follow the canonical `- [ ] T### [P?] [USx?] description …` format. Checked boxes (`[X]`) indicate work that has already passed verification; unchecked boxes are pending and have been reopened where verification failed.

---

## Phase 1 – Project setup & early end‑to‑end run

| ID | Description |
|----|-------------|
- [ ] T001 **Create project directory hierarchy** – create the folders required by the plan: `code/`, `code/data/`, `code/geometry/`, `code/analysis/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`.  
  - *Verification*: `tree` output shows all directories; CI step `test_dir_structure.sh` asserts their existence.  
  - *Artifacts*: directory tree on disk.  

- [ ] T002 **Initialize Python 3.11 project** – add `code/requirements.txt` with pinned versions of `opencv-python`, `numpy`, `pandas`, `scipy`, `pytest`, `pyyaml`; create a minimal `code/__init__.py` to make the package importable.  
  - *Verification*: `pip install -r code/requirements.txt` succeeds in CI.  

- [ ] T003 **Configure linting & formatting** – add `.ruff.toml`, `.flake8`, and `pyproject.toml` (with Black settings) under `code/`; add a convenience script `code/lint.sh` that runs `ruff check . && black --check .`.  
  - *Verification*: CI step runs `code/lint.sh` and requires zero violations.  

---

## Phase 2 – Foundational infrastructure (must complete before any user‑story work)

- [ ] T004 **Setup basic logging** – add a logger configuration in `code/__init__.py` that writes to `logs/llmxive.log` with INFO level.  
- [ ] T005 **Implement configuration loader** – create `code/config.py` exposing paths (`RAW_DATA_DIR`, `PROCESSED_DATA_DIR`, etc.) and constants (e.g., motion thresholds).  
- [ ] T006 **Create base data models** – implement `GridFrame`, `CameraPose`, and `ReconstructedBox` dataclasses in `code/data/models.py`.  
- [ ] T006b **Design streaming/chunked loading strategy** – add helper functions in `code/config.py` (`load_dataset_streaming`) that guarantee < 6 GB RAM usage.  
- [ ] T007 **Download OmniDirector dataset or generate deterministic synthetic fallback** – write `code/data/download.py` that (1) attempts to fetch the real dataset from the canonical URL (`https://huggingface.co/datasets/omnidirector/full`) into `data/raw/omnidirector.zip`; (2) on failure, creates `data/raw/synthetic_omnidirector.zip` containing a small but schema‑compliant synthetic collection (10 sequences, each with 5 frames, random poses, and a `randomized_depth` flag). The script logs the source used.  
  - *Verification*: after execution, exactly one of the two zip files exists and is non‑empty; its checksum is recorded in `code/data/download.log`.  

---

## Phase 3 – User Story 1: Dataset ingestion & geometric filtering (P1)

- [ ] T008 **Implement dataset loader** – in `code/data/ingestion.py` write `load_raw_dataset()` that extracts video frames and metadata from the zip produced by T007, yielding a generator of `GridFrame` objects.  
  - *Verification*: unit test loads the first 2 frames without error; logs the number of sequences discovered.  

- [ ] T009 **Implement geometric filtering logic** – extend `code/data/ingestion.py` with `filter_sequences()` applying FR‑001 heuristics (radial motion > 15° OR Z‑velocity > 0.1 units/frame).  
- [ ] T010 **Extract grid frames & pair with ground‑truth poses** – add `extract_grid_frames()` in `code/data/preprocessing.py` that writes each frame’s image to `data/raw/frames/<seq_id>_<frame_idx>.png` and records the associated `R_i`, `t_i`.  
- [ ] T011 **Write curated dataset CSV** – after filtering, `code/data/ingestion.py` writes `data/processed/filtered_sequences.csv` following the `dataset.schema.yaml` (columns: `sequence_id,frame_id,radial_motion_deg,z_velocity,grid_points_2d,R_matrix,t_vector,randomized_depth`). Include a SHA‑256 checksum column for each row.  
  - *Verification*: CI runs `csvkit` to validate the file against the JSON schema; the checksum column must be non‑empty.  

- [ ] T012 **Linear interpolation for missing/occluded grid lines** – add helper `interpolate_missing_lines()` in `code/data/ingestion.py` that fills gaps without raising exceptions.  

**Tests (already verified)**  
- [ ] T013 **Unit test for filtering heuristics** – `code/tests/unit/test_ingestion.py`.  
- [ ] T014 **Integration test for ingestion pipeline** – `code/tests/integration/test_ingestion_pipeline.py` runs on a subset of the synthetic zip and checks that `filtered_sequences.csv` contains only retained sequences.  

---

## Phase 4 – User Story 2: CPU‑based perspective inversion solver (P2)

- [ ] T015 **Define WorldGridModel** – constant `WORLD_GRID_POINTS` (4 corners of a unit square on Z = 0) in `code/geometry/utils.py`.  
- [ ] T016 **Implement orthogonal line detection & intersection** – functions `detect_grid_lines()` and `compute_intersections()` in `code/geometry/utils.py` using OpenCV Canny + HoughLinesP.  

- [ ] T017 **Implement solvePnP‑based geometric solver** – in `code/geometry/solver.py` write `solve_sequence_pose()` that (1) builds 3‑D object points from `WorldGridModel`; (2) feeds detected 2‑D points; (3) calls `cv2.solvePnP(..., flags=cv2.SOLVEPNP_ITERATIVE)`; (4) returns a `CameraPose` with a scale‑factor flag.  
  - *Verification*: unit test verifies that a synthetic sequence with known pose yields reprojection error ≤ 2 px.  

- [ ] T018 **Reconstruct bounding‑box dimensions** – `code/geometry/reconstruction.py` implements `reconstruct_box()` that aggregates per‑frame poses into relative height, width, depth (scale‑invariant).  

- [ ] T019 **Write pose estimates & reconstructed boxes** – after solving all retained sequences, `code/geometry/solver.py` writes `data/processed/poses_estimated.json` conforming to `output.schema.yaml` (one entry per sequence with `reconstructed_dimensions` and `ground_truth_dimensions`).  

- [ ] T020 **Handle missing data & flag high‑complexity sequences** – `solver.py` skips frames where `intersections` are insufficient and adds a `flag` field (`high_complexity: true`) when motion exceeds the solvable threshold defined in FR‑007.  

- [ ] T021 **Log sequences exceeding distortion thresholds** – append entries to `logs/solver_warnings.log` with sequence ID and reason.  

- [ ] T022 **Enforce CPU‑only implementation** – `solver.py` imports only `cv2` (CPU build) and asserts `cv2.cuda.getCudaEnabledDeviceCount() == 0` at runtime.  

**Tests (already verified)**  
- [ ] T023 **Unit test line‑intersection** – `code/tests/unit/test_solver.py`.  
- [ ] T024 **Unit test solvePnP scale‑ambiguity handling** – `code/tests/unit/test_solver.py`.  
- [ ] T025 **Integration test full sequence reconstruction** – `code/tests/integration/test_geometry_pipeline.py`.  

---

## Phase 5 – User Story 3: Statistical validation & correlation analysis (P3)

- [ ] T026 **Compute reconstruction error metrics** – in `code/analysis/metrics.py` add `compute_error_metrics()` that reads `poses_estimated.json` and produces per‑sequence absolute errors (height, width, depth) and `aspect_ratio_error`.  

- [ ] T027 **Calculate motion‑complexity metrics** – already implemented in `metrics.py` (`radial_motion_deg`, `z_velocity_avg`, `motion_type`).  

- [ ] T028 **Pearson correlation analysis** – `metrics.py` provides `pearson_correlation()` between `complexity_score` and `aspect_ratio_error`.  

- [ ] T029 **Aspect‑ratio validation** – `code/analysis/validation.py` implements `validate_aspect_ratio()` that checks each reconstructed aspect ratio against the known synthetic room aspect ratio (tolerance ± 5 %).  

- [ ] T030 **Synthetic control validation** – `validation.py` scans `filtered_sequences.csv` for rows where `randomized_depth == True`, attempts depth recovery via the solver, and flags sequences with reconstruction error > 50 % as proof of metric‑depth loss.  

- [ ] T031 **Calculate dataset‑filtering success rate** – `analysis/metrics.py` adds `filter_success_rate()` that reads `filtered_sequences.csv` and the original metadata (available in the zip) to compute retained / total percentage; result stored in `data/processed/reconstruction_results.csv`.  

- [ ] T032 **Instrument pipeline timing** – wrap the full end‑to‑end run (ingestion → solver → analysis) with `time.perf_counter()` and record total wall‑clock seconds in the `analysis_metadata.total_time_sec` field of `reconstruction_results.csv`.  

- [ ] T033 **Generate final results CSV (SSoT)** – consolidate all per‑sequence statistics, summary statistics (pearson, mean error, synthetic‑control error rate) into `data/processed/reconstruction_results.csv` abiding by `output.schema.yaml`.  

- [ ] T034 **Generate statistical report** – create `report.md` that (1) cites SC‑001 – SC‑005, (2) includes tables/figures produced from `reconstruction_results.csv` (e.g., error histograms, correlation scatter), and (3) discusses limitations (scale ambiguity, synthetic control outcome).  

**Tests**  
- [ ] T035 **Unit test Pearson calculation** – `code/tests/unit/test_metrics.py`.  
- [ ] T036 **Unit test aspect‑ratio validation** – `code/tests/unit/test_validation.py`.  
- [ ] T037 **Integration test full statistical report generation** – `code/tests/integration/test_analysis_pipeline.py` runs the entire pipeline on the synthetic subset and asserts that `report.md` contains a non‑empty Pearson r value.  

---

## Phase 6 – Polish, cross‑cutting concerns & handoff

- [ ] T038 **Documentation updates** – fill `code/README.md` and `code/docs/architecture.md` with high‑level pipeline description, usage examples, and references to the JSON schemas.  

- [ ] T039 **Chunked processing & memory profiling** – enhance `solver.py` to process sequences in configurable batches; add a profiling hook that writes peak RAM usage to `logs/memory_profile.log`.  

- [ ] T040 **Performance optimisation of line detection** – replace Canny with Sobel‑based edge detection, enable `multiprocessing.Pool` to parallelise frame‑wise detection; ensure average per‑frame runtime < 100 ms on the CI runner.  

- [ ] T041 **Validate quickstart end‑to‑end execution** – update `quickstart.md` with the exact CLI command (`python -m code.main --config config.yaml --run full`) and add a CI step that runs this command on the synthetic dataset, asserting total runtime ≤ 6 h and that `report.md` is generated.  

---

### Dependency & execution order summary

| Phase | Must‑complete before |
|-------|----------------------|
| Phase 1 | – |
| Phase 2 | Phase 1 |
| Phase 3 (US 1) | Phase 2 |
| Phase 4 (US 2) | Phase 2 **and** Phase 3 (needs `filtered_sequences.csv`) |
| Phase 5 (US 3) | Phase 2 **and** Phase 4 (needs `poses_estimated.json`) |
| Phase 6 | All prior phases |

All tasks are written as checklist items; unchecked items indicate work that still needs to be produced and verified. When a task is completed and passes its verification step, the checkbox should be changed to `[X]` in the next revision.
