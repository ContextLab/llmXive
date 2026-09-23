# Tasks: llmXive follow-up: extending TriSplat for CPU-only edge robotics

**Input**: Design documents from `/specs/001-llmxive-trisplat-ext/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure per `plan.md` - `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` in `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` including `torch`, `numpy`, `scipy`, `trimesh`, `pygltflib`, `datasets`, `scikit-learn`, `tqdm`, `pandas`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/cli.py` entry point with arguments: `--views`, `--timeout`, `--seed`, `--update-state`
- [X] T023 [P] Implement dynamic view count configuration in `code/cli.py` (FR-002) to support 2, 3, 4, 5 views as a prerequisite for batch orchestration
- [X] T005 [P] Create `code/data/loader.py` implementing RealEstate10K streaming via `datasets.load_dataset(..., streaming=True)` with explicit 320x240 downscaling logic (FR-003)
- [X] T006 [P] Implement `code/utils/mesh_utils.py` for mesh generation, validation (manifold check), and cleanup
- [X] T007 [P] Implement `code/utils/stats.py` for Shapiro-Wilk, paired t-test, and Wilcoxon signed-rank test logic (FR-005)
- [X] T008 [P] Create `code/models/trisplat_base.py` to load frozen TriSplat backbone weights in CPU-compatible mode
- [X] T009 [P] Create `code/models/geometry_only.py` stub (empty file) for the differentiable ray-surface intersection layer (FR-001)
- [X] T010 [P] Implement `code/data/metrics.py` for Chamfer Distance and PSNR calculation against ground truth
- [X] T011 [P] Setup `code/experiments/run_batch.py` orchestrator skeleton with N=20 scene limit. **Note**: Must implement a wall-clock timeout. using `signal.alarm` (Unix) or a `time.time()` loop with a hard exit and logging before CI termination to satisfy FR-006. T011a will implement the specific mechanism.
- [X] T011a [P] Implement a configurable batch timeout mechanism in `code/experiments/run_batch.py`: Add a wrapper using `signal.alarm` (or `time.time()` loop) that triggers a graceful exit and logs "BATCH_TIMEOUT_EXCEEDED" if the process runs longer than a predefined duration., satisfying FR-006. **Note**: This task must be completed before T024 can run the batch.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Geometry-Only Reconstruction (Priority: P1) 🎯 MVP

**Goal**: Run 3D scene reconstruction on a standard 2-core CPU using only explicit geometric constraints, producing a valid mesh within 30 minutes. [UNRESOLVED-CLAIM: c_c21951c9 — status=not_enough_info]

**Independent Test**: Execute pipeline on a single RealEstate10K scene (320x240) on CPU-only runner; verify valid `.obj`/`.ply` output within 30 mins.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/models/geometry_only.py` differentiable ray-surface intersection layer using local triangle connectivity and depth gradients (FR-001)
- [X] T016 [US1] Implement convergence detection in `code/models/geometry_only.py` with a configurable hard limit on the maximum number of iterations, set via `--max-iterations` CLI arg. and non-convergence logging (FR-007). **Note**: This task depends on T015 completion; [P] tag removed. Must log the current `view_count` (sparsity threshold) alongside the failure flag to satisfy Constitution Principle VI.
- [X] T017 [US1] Integrate `code/utils/mesh_utils.py` (from T006) into `code/experiments/run_batch.py` to produce valid `.obj`/`.ply` files (FR-004). **Note**: Consumes T006 logic, does not re-implement.
- [X] T018 [US1] Integrate `code/models/geometry_only.py` into `code/experiments/run_batch.py` to replace the learned refinement head
- [X] T019b [US1] **Handle monocular input gracefully**: In `code/cli.py` and `run_batch.py`, if input views < 2, log a WARNING "Monocular input detected. Skipping scene." and continue to the next scene (do NOT exit with code 1). (FR-002, US1). **Note**: Replaces T019 to satisfy graceful handling requirement.
- [X] T020 [US1] Implement corrupted/missing ground truth handling in `code/data/loader.py`: If ground truth is missing *after* a successful fetch, skip scene, log WARNING, and continue (Edge Case). **Note**: Distinguish from fetch errors (T049); this handles data integrity issues *after* a successful fetch.
- [X] T040 [US1] Implement low-texture/non-convergence detection in `code/models/geometry_only.py`: detect via gradient variance, output a placeholder mesh, and log a distinct error flag "LOW_TEXTURE_CONVERGENCE_FAILED" (Edge Case)
- [X] T043 [US1] Implement general non-convergence handling in `code/models/geometry_only.py`: if the 100-iteration limit (T016) is hit for ANY reason (not just low-texture), generate a placeholder mesh and log an error flag "TIMEOUT_CONVERGENCE_FAILED" to satisfy FR-007 (Edge Case). **Note**: Must include the current `view_count` in the log entry to attribute failure to sparsity.

### Tests for User Story 1

> **NOTE**: Write these tests AFTER implementation to ensure they pass

- [X] T012 [P] [US1] Unit test for a bounded iteration limit in `code/models/geometry_only.py` (FR-007) in `tests/unit/test_geometry.py`. **Note**: Test function `test_iteration_limit_enforcement` must assert that the process raises a `TimeoutError` or sets a specific status flag when iterations > limit, and verify the log contains 'TIMEOUT_CONVERGENCE_FAILED'.
- [X] T013 [P] [US1] Integration test for single scene reconstruction pipeline in `tests/integration/test_single_scene.py`
- [X] T014 [P] [US1] Memory usage test verifying < 6 GB peak RAM in `tests/integration/test_memory_limits.py`

**Checkpoint**: User Story 1 is fully functional and testable independently on CPU

---

## Phase 4: User Story 2 - Sparsity Threshold Identification (Priority: P2)

**Goal**: Systematically vary input views (2, 3, 4, 5) to identify the sparsity threshold where geometric constraints fail.

**Independent Test**: Run pipeline on 20 scenes (or 50 if T042 triggers) with varying view counts; output structured log of Chamfer Distance/PSNR; perform statistical test to identify threshold.

### Implementation for User Story 2

- [X] T024 [US2] Implement batch orchestration in `code/experiments/run_batch.py` to process N=20 scenes (or N=50 if T042 triggers) across 2, 3, 4, and 5 view configurations (depends on T023)
- [X] T025 [US2] Implement metric logging in `code/experiments/run_batch.py` to output JSON logs with Chamfer Distance and PSNR per scene/view-count (FR-004)
- [X] T026 [US2] Implement statistical test logic in `code/utils/stats.py`: orchestrate normality check (T027) and conditional selection of t-test/Wilcoxon (FR-005)
- [X] T027 [US2] **Implement Shapiro-Wilk test**: Explicitly implement and log the Shapiro-Wilk normality test results in `code/utils/stats.py` as a distinct, verifiable unit of work to satisfy FR-005 requirement to perform all three tests.
- [X] T028 [US2] Integrate statistical results (T027, T026) into the final batch report JSON (FR-004)
- [X] T041 [US2] Implement threshold identification logic in `code/utils/stats.py`: Define a CLI argument `--tolerance` (default configurable) for the tolerance threshold. Calculate relative error increase as `(error_N - error_baseline) / error_baseline` where error_N is Chamfer Distance at view count N. Identify the specific view count where this exceeds the threshold; output result to `data/processed/threshold_result.json` (FR-005). **Note**: Document derivation of [deferred] default in code comments.

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for statistical significance logic (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/unit/test_stats.py`. **Note**: Must include test functions `test_shapiro_wilk_normality`, `test_conditional_ttest_wilcoxon`, and `test_threshold_calculation`.
- [X] T022 [P] [US2] Integration test for batch processing with varying view counts in `tests/integration/test_sparsity_batch.py`

**Checkpoint**: User Story 2 is complete; sparsity threshold is identified and logged

---

## Phase 5: User Story 3 - Quantitative Fidelity and Latency Benchmarking (Priority: P3)

**Goal**: Compare inference latency and geometric fidelity of the geometry-only module against the baseline.

**Independent Test**: Run both methods on same hardware; compare latency and fidelity metrics.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement latency measurement wrapper in `code/experiments/run_batch.py` to record inference time per scene-config
- [X] T031b [US3] **Implement CPU affinity enforcement for geometry-only module**: Explicitly implement `os.sched_setaffinity` or `taskset` logic in `code/experiments/run_batch.py` to enforce a limited multi-core CPU affinity (selecting a small subset of available cores, e.g., 0 and 1) for the geometry-only module (T015/T018) as required by SC-001, ensuring the primary hypothesis runs under strict CPU constraints. **Note**: Must be executed before T030 to ensure measurement is valid.
- [X] T031 [US3] Implement baseline TriSplat execution logic in `code/experiments/run_batch.py`: **Explicitly enforce** limited CPU affinity (e.g., `os.sched_setaffinity` selecting a restricted set of cores) for **both** the baseline and the geometry-only module (T015/T018) to strictly match SC-001 requirements. **Note**: If baseline fails on CPU, log a CRITICAL error and exit the batch process immediately; do NOT skip. A skipped baseline invalidates the research question (Constitution Principle VII).
- [X] T032 [US3] Implement comparative metric aggregation in `code/utils/stats.py` to calculate speedup ratio and PSNR delta (FR-004)
- [X] T033 [US3] Generate benchmark report CSV at `data/processed/benchmark_tradeoff.csv` with columns: `view_count,latency,chamfer_distance,psnr,baseline_latency` (US-3 Acceptance 1). **Note**: Explicitly list these headers in the code.
- [X] T039 [US3] Generate visualization of trade-off curve: Create a plot (PNG/SVG) showing latency vs. Chamfer Distance for different view counts, saved to `data/processed/benchmark_tradeoff_plot.png` (US-3 Acceptance 3)

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for latency measurement wrapper in `tests/unit/test_latency.py`. **Note**: Test function `test_latency_measurement_wrapper` must assert that the wrapper uses `time.perf_counter()`, returns a float > 0, and correctly logs exceptions during the timed block.
- [X] T029 [P] [US3] Integration test for comparative benchmarking in `tests/integration/test_benchmark.py`

**Checkpoint**: All user stories are independently functional and benchmarked

---

## Phase 6: Stretch Goal & Polish

**Purpose**: Handling N=50 scenes and final validation

- [X] T042 [P] Implement N=50 stretch goal logic in `code/experiments/run_batch.py`: If N=20 scenes complete within 70% of the time budget, dynamically expand the scene list to 50 random scenes and continue processing (Plan: Stretch Goal). **Note**: Must implement timeout using `signal.alarm` or `threading.Timer` to enforce the 6-hour wall-clock limit.
- [X] T035 [P] Add checksumming logic for downloaded dataset shards in `code/data/loader.py` (Plan: Data Hygiene)
- [X] T044 [P] Implement data flow for checksums: Ensure `code/data/loader.py` (T035) writes computed checksums to a temporary JSON file (`data/processed/checksums_temp.json`) that `code/cli.py --update-state` (T034) ingests to satisfy Constitution Principle III (Plan: Data Hygiene). **Note**: Explicitly defines the producer-consumer chain for checksums to state file.
- [X] T034 [P] Implement `code/cli.py --update-state` command to compute SHA-256 hashes and update `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` (Plan: Post-Execution State Update). **Note**: Must read `checksums_temp.json` if present (from T044) instead of recomputing hashes.
- [X] T036 [P] Write comprehensive `README.md` and `quickstart.md` in `specs/001-llmxive-trisplat-ext/`
- [X] T037 [P] Validate all contracts (`contracts/*.schema.yaml`) against generated JSON outputs
- [X] T046 [P] Final CI validation: Run full batch (N=20) on simulated GitHub Actions free-tier environment and archive logs to `data/processed/ci_validation_logs/` to satisfy Reproducibility principle

---

## Phase 7: Data Integrity & Reproducibility Hardening (Revision)

**Purpose**: Addressing specific reviewer concerns regarding data source verification, deterministic sampling, and stream handling to prevent fabrication.

### Implementation for Data Integrity

- [ ] T047 [US1] **Explicit Dataset Sampling Rule**: In `code/experiments/run_batch.py`, explicitly define the RealEstate10K validation split ID ('validation') and implement a deterministic sampling strategy using `itertools.islice` to select the *first* N=20 (or N=50) scenes from the streamed dataset using seed 42. Document the exact seed and slice logic in the code comments to satisfy the "Real data + real results" rule. **Note**: [P] tag removed due to file conflict risk with T024.
- [ ] T048 [US1] **Stream Verification**: In `code/data/loader.py`, add a pre-flight check that attempts to stream a small sample of frames from the dataset to verify connectivity and schema validity before starting the main batch. If this fails, raise a loud error (no fallback) to satisfy Constitution Principle III. **Note**: [P] tag removed due to file conflict risk with T005.
- [ ] T049 [US1] **Real Data Source Lock-in**: Ensure `code/data/loader.py` contains NO `try/except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` functions. If `datasets.load_dataset` fails, the script MUST crash immediately with a clear error message pointing to the real source URL. **Note**: [P] tag removed due to file conflict risk with T005.
- [ ] T050 [US1] **Artifact Hashing Logic**: In `code/cli.py --update-state`, implement the logic to recursively hash all files in `data/processed/` (including the `threshold_result.json` and `benchmark_tradeoff.csv`) and write the resulting map to `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` to ensure the "Single Source of Truth" is updated. **Note**: Must filter files by size < 100MB using `os.path.getsize` BEFORE hashing to avoid long runtimes on large mesh files. [P] tag removed due to file conflict risk with T034.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be completed first to validate feasibility
 - US2 (P2) depends on US1's geometry layer implementation
 - US3 (P3) depends on US1 and US2 for comparative data
- **Stretch Goal & Polish (Phase 6)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Can be implemented in parallel with Phase 6, but MUST be completed before final CI validation (T046).

### User Story Dependencies

- **User Story 1 (P1)**: Core feasibility. Must pass before US2/US3 are meaningful.
- **User Story 2 (P2)**: Requires US1's geometry-only implementation to run the batch.
- **User Story 3 (P3)**: Requires US1 and US2 to generate comparative metrics.

### Within Each User Story

- Implementation MUST be completed before Tests for that story can run (Producer -> Consumer flow)
- Models/Utils before Orchestrators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004-T011) can run in parallel
- Once Foundational phase completes:
 - Developer A can work on US1 (P1) Implementation
 - Developer B can work on US2 (P2) logic (batch orchestration)
 - Developer C can work on US3 (P3) logic (benchmarking)
- All tests for a user story marked [P] can run in parallel (after implementation)
- Phase 7 tasks (T047-T050) can run in parallel with Phase 6 tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together (excluding dependent tasks):
Task: "Implement differentiable ray-surface layer in code/models/geometry_only.py"
Task: "Integrate mesh generation from code/utils/mesh_utils.py"
Task: "Implement low-texture detection in code/models/geometry_only.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for a configurable maximum iteration limit in code/models/geometry_only.py"
Task: "Integration test for single scene in tests/integration/test_single_scene.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Geometry-only pipeline on CPU)
4. **STOP and VALIDATE**: Test US1 on a single scene. If it fails to produce a mesh or OOMs, the project is blocked.
5. Deploy/demo if ready (MVP: CPU-feasible geometry-only reconstruction)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Run batch of 20 scenes → Identify threshold → Deploy/Demo
4. Add User Story 3 → Run benchmark comparison → Generate trade-off curve → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Geometry Layer)
 - Developer B: User Story 2 (Batch Orchestrator & Stats)
 - Developer C: User Story 3 (Benchmarking & Latency)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (write tests after implementation skeleton exists)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/data/loader.py` uses `streaming=True` and never falls back to synthetic data (Constitution Principle III & IV).
- **Critical**: Ensure `code/models/geometry_only.py` runs on CPU only for the primary hypothesis (US-1).
- **Critical**: T042 ensures the N=50 spec requirement is met if runtime permits.
- **Critical**: T044 ensures checksums are recorded in the state file as per Constitution Principle III.
- **Critical**: T031 and T031b enforce 2-core CPU affinity for both baseline and geometry-only modules to satisfy SC-001.
- **Critical**: T043 ensures placeholder mesh is generated for general 100-iteration timeouts.
- **Critical**: T041 enforces the 15% tolerance constant (now CLI configurable).
- **Critical**: T019b explicitly handles monocular input with a warning and skip.
- **Critical**: T027 explicitly implements Shapiro-Wilk test as a distinct unit.
- **Critical**: T046 ensures final CI validation logs are archived.
- **Critical**: Ensure `code/experiments/run_batch.py` explicitly defines the RealEstate10K validation split ID and uses `itertools.islice` for the first N=20 (or N=50) scenes to guarantee a deterministic, reproducible sample as per the "Real data + real results" rule (T047).
- **Critical**: Ensure `code/data/loader.py` raises a loud error on fetch failure and contains NO synthetic fallback logic (T049).
- **Critical**: Ensure `code/cli.py --update-state` correctly hashes all processed artifacts (excluding large files >100MB) to update the state file (T050).
- **Critical**: Ensure T011a implements the 6-hour timeout mechanism explicitly.
- **Critical**: Ensure T016 and T043 log the specific `view_count` on failure.
- **Critical**: Ensure T031 does not skip the baseline on CPU failure.
- **Critical**: Ensure T044 is executed before T034.

# next task line

- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

# completed task ids
['T001', 'T002', 'T004', 'T023', 'T005', 'T006', 'T007', 'T008', 'T009', 'T010', 'T011', 'T011a', 'T015', 'T016', 'T017', 'T018', 'T019b', 'T020', 'T040', 'T043', 'T012', 'T013', 'T014', 'T024', 'T025', 'T026', 'T027', 'T028', 'T041', 'T021', 'T022', 'T030', 'T031b', 'T031', 'T032', 'T033', 'T039', 'T028', 'T029', 'T042', 'T035', 'T044', 'T034', 'T036', 'T037', 'T046']

# wall_clock_budget_seconds
300

# Existing project API surface (READ THIS — every name you import or call MUST come from this list, not invented)

### code/cli.py
import as: `from cli import compute_sha256, update_state_file, run_pipeline, main`
public names: compute_sha256, update_state_file, run_pipeline, main
imports:
 import argparse
 import json
 import os
 import sys
 import hashlib
 from pathlib import Path

### code/data/loader.py
import as: `from data.loader import compute_sha256, save_checksums, load_real_estate_10k_streaming, get_scene_batch, compute_sha256_file`
public names: compute_sha256, save_checksums, load_real_estate_10k_streaming, get_scene_batch, compute_sha256_file
imports:
 import logging
 import hashlib
 import json
 import os
 from typing import Iterator, Dict, Any, Optional, Tuple
 from pathlib import Path

### code/data/metrics.py
import as: `from data.metrics import calculate_chamfer_distance, calculate_psnr, calculate_metrics_batch`
public names: calculate_chamfer_distance, calculate_psnr, calculate_metrics_batch
imports:
 import numpy as np
 import torch
 from scipy.spatial import cKDTree
 from typing import Tuple, Union, Optional, List
 import logging

### code/experiments/generate_benchmark_csv.py
import as: `from experiments.generate_benchmark_csv import load_batch_results, aggregate_results, write_csv, main`
public names: load_batch_results, aggregate_results, write_csv, main
imports:
 import json
 import csv
 import logging
 import os
 from pathlib import Path
 from typing import List, Dict, Any

### code/experiments/generate_final_report.py
import as: `from experiments.generate_final_report import load_batch_results, aggregate_threshold_data, generate_final_batch_report, main`
public names: load_batch_results, aggregate_threshold_data, generate_final_batch_report, main
imports:
 import json
 import logging
 import os
 from pathlib import Path
 from typing import Dict, Any, List
 from utils.stats import identify_sparsity_threshold, save_threshold_results, aggregate_benchmark_results

### code/experiments/generate_tradeoff_plot.py
import as: `from experiments.generate_tradeoff_plot import load_benchmark_data, plot_tradeoff, main`
public names: load_benchmark_data, plot_tradeoff, main
imports:
 import os
 import csv
 import logging
 import matplotlib
 import matplotlib.pyplot as plt
 from pathlib import Path

### code/experiments/run_batch.py
import as: `from experiments.run_batch import setup_logging, TimeoutError, TimeoutHandler, SceneResult, run_baseline_trisplat_cpu, run_single_scene, generate_summary_report, run_batch_orchestration`
public names: setup_logging, TimeoutError, TimeoutHandler, SceneResult, run_baseline_trisplat_cpu, run_single_scene, generate_summary_report, run_batch_orchestration, main
imports:
 import argparse
 import json
 import logging
 import os
 import signal
 import sys

### code/models/geometry_only.py
import as: `from models.geometry_only import DifferentiableRaySurfaceLayer, GeometryOnlyModel, create_geometry_only_model, run_geometry_optimization, generate_placeholder_mesh_from_failure, run_geometry_optimization_with_fallback`
public names: DifferentiableRaySurfaceLayer, GeometryOnlyModel, create_geometry_only_model, run_geometry_optimization, generate_placeholder_mesh_from_failure, run_geometry_optimization_with_fallback
imports:
 import torch
 import torch.nn as nn
 import torch.nn.functional as F
 import numpy as np
 from typing import Optional, Tuple, Dict, Any, List
 from pathlib import Path

### code/models/trisplat_base.py
import as: `from models.trisplat_base import TriSplatBackbone, load_trisplat_base, is_cpu_compatible`
public names: TriSplatBackbone, load_trisplat_base, is_cpu_compatible
imports:
 import torch
 import torch.nn as nn
 from typing import Optional, Dict, Any, Tuple
 from pathlib import Path
 import logging

### code/utils/mesh_utils.py
import as: `from utils.mesh_utils import generate_mesh_from_points, validate_manifold, cleanup_mesh, export_mesh, create_placeholder_mesh`
public names: generate_mesh_from_points, validate_manifold, cleanup_mesh, export_mesh, create_placeholder_mesh
imports:
 import numpy as np
 import trimesh
 from typing import Optional, Tuple, List
 from pathlib import Path

### code/utils/stats.py
import as: `from utils.stats import check_normality, paired_comparison, identify_sparsity_threshold, save_threshold_results, run_statistical_analysis_batch, calculate_comparative_metrics, aggregate_benchmark_results`
public names: check_normality, paired_comparison, identify_sparsity_threshold, save_threshold_results, run_statistical_analysis_batch, calculate_comparative_metrics, aggregate_benchmark_results
imports:
 import numpy as np
 from scipy import stats
 from typing import List, Tuple, Dict, Any, Optional
 import json
 from pathlib import Path
 import logging

### code/utils/validate_contracts.py
import as: `from utils.validate_contracts import load_yaml_schema, load_json_output, validate_against_schema, find_json_outputs, find_schemas, validate_all_contracts, main`
public names: load_yaml_schema, load_json_output, validate_against_schema, find_json_outputs, find_schemas, validate_all_contracts, main
imports:
 import json
 import yaml
 import logging
 import sys
 from pathlib import Path
 from typing import Dict, Any, List, Tuple

# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files or directory tree were presented for `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/`; without any visible `plan.md` copy, source code, README, or folder hierarchy, we cannot confirm that the required structure was created. The implementer must supply the actual filesystem contents showing the project layout.
- **T003** — The implementer supplied only a high‑level feature specification and no actual files or configuration changes in the `code/` directory. There are no `pyproject.toml`, `.ruff.toml`, `black.toml`, or any other linting/formatting setup files present, nor any evidence that ruff or black were installed or integrated into the project. The required linting/formatting configuration is missing.
- **T014** — The required artifact `tests/integration/test_memory_limits.py` does not exist in the repository, so there is no test verifying that peak RAM stays below 6 GB. The task’s core deliverable is missing.
- **T041** — The `stats.py` file defines `TOLERANCE_THRESHOLD` but the `identify_sparsity_threshold` function is truncated and does not show the required calculation or JSON writing logic. Moreover, the expected output file `data/processed/threshold_result.json` is missing. The task’s core requirement—computing the relative error increase and persisting the result—is not fulfilled.
- **T027** — No JSON report or any file containing the integrated statistical results is provided; the evidence lacks the required final batch report artifact, so the task’s deliverable cannot be confirmed as completed.
- **T033** — declared artifact(s) missing/empty/invalid: data/processed/benchmark_tradeoff.csv
- **T039** — declared artifact(s) missing/empty/invalid: data/processed/benchmark_tradeoff_plot.png
- **T044** — The loader defines `save_checksums` but never calls it, and the required `data/processed/checksums_temp.json` file is absent. Moreover, `cli.py --update-state` recomputes checksums from files in `data/processed` instead of reading the temporary JSON, so the intended data flow is not realized. The task’s requirement is therefore not satisfied.
- **T034** — The `code/cli.py` contains an `update_state_file` function that would write the required YAML, but the repository lacks the `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` file, and the provided snippet does not show argument parsing that actually invokes `--update-state`. Without the state file present (or evidence that running the command creates it), the task’s requirement is not satisfied.
- **T036** — No `README.md` or `quickstart.md` files were presented in `specs/001-llmxive-trisplat-ext/`; the implementer provided no content to verify that the required documentation exists or meets the specification.
- **T037** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T038** — No artifacts (e.g., CI logs, batch output files, JSON/CSV results, or visualizations) were provided to demonstrate that a full batch of 20 or 50 scenes was actually run on a simulated GitHub Actions free‑tier environment. Consequently the requirement cannot be verified.


# Real data only — NEVER fabricate results

This code must run on REAL data and produce REAL measured results. NEVER generate synthetic/fake INPUT data, hard-code fake 'sample' rows, ship a placeholder dataset, or compute a result from random/simulated values standing in for a real measurement — the execution gate's fabrication guard will reject the run and the project cannot advance. When a task needs external data, load it from the REAL source named in the spec/plan (or data the project already downloaded under `data/`). If no real source is reachable, do NOT fake it — implement the loader against the real source and let it fail loudly (a clear error the fix loop can act on).

# Task

Return the YAML implementation report. If your script imports from sibling modules, the imported names MUST match the API surface above. If a name does not exist there, either add it to the appropriate file in this task's `artifacts` list or use a different name that does.