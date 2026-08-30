# Implementation Plan: Virtual Tactile Zero-Shot Adaptation

**Branch**: `001-virtual-tactile-adaptation` | **Date**: 2026-07-13 | **Spec**: `specs/001-virtual-tactile-adaptation/spec.md`
**Input**: Feature specification from `specs/001-virtual-tactile-adaptation/spec.md`

## Summary

This feature implements a "Virtual Tactile" estimator to enable zero-shot adaptation of a dexterous hand manipulation policy (PICA baseline) to unseen friction conditions. The system estimates contact stiffness ($k_{est}$) using the ratio of hand joint torque derivatives to object velocity derivatives, dynamically scaling reward weights without prior training on specific objects. The implementation is constrained to CPU-only execution (PyBullet) to ensure reproducibility on GitHub Actions free-tier runners. The statistical validation uses a Generalized Linear Mixed Model (GLMM) to rigorously test for a >15% improvement in success rates on high-friction novel objects (0.8–1.2) compared to a static baseline, while explicitly handling zero-success baselines via Odds Ratios.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pybullet` (CPU physics), `torch` (CPU-only policy), `numpy`, `pandas`, `pytest`, `scipy`, `statsmodels` (GLMM), `psutil` (memory monitoring)  
**Storage**: Local filesystem (`data/`), JSONL manifest from Hugging Face  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM)  
**Project Type**: research-simulation  
**Performance Goals**: Complete full experiment (100 trials, 50 objects) in ≤ 6 hours; Peak RAM < 7GB  
**Constraints**: NO CUDA operations; NO GPU acceleration; deterministic random seeds; strict memory limits  
**Scale/Scope**: Multiple randomized friction trials per object; A novel set of articulated object geometries (high-friction targeted and full-range)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Mapping |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and CPU-only execution to ensure identical results on fresh runners. |
| **II. Verified Accuracy** | PASS | Plan requires `validate_citations.py` execution (Task T008c) and generation of `citations_validation.log` as evidence. Validation against the DragMesh-2 manifest URL provided in the verified datasets block. |
| **III. Data Hygiene** | PASS | Plan includes `verify_manifest.py` (Task T005c) to compute SHA256 of the *populated* manifest and record it in `artifact_hashes.data_raw` (corrected path). |
| **IV. Single Source of Truth** | PASS | All metrics (success rates, $k_{est}$ values, system metrics) will be written to `data/results/` CSVs/JSONs; the paper will strictly reference these derived files. |
| **V. Versioning Discipline** | PASS | State YAML will be updated with content hashes of `data/` and `code/` artifacts upon completion. |
| **VI. CPU-Only Simulation Fidelity** | PASS | Plan explicitly forbids CUDA; uses PyBullet `Direct` (CPU) backend; policies run on `device="cpu"`. |
| **VII. Derivative-Based Stiffness Proxy Validation** | PASS | Plan includes GLMM validation (Task T015d) comparing adaptive vs. static success rates, specifically isolating the high-friction subset (0.8–1.2) for SC-001 and calculating Odds Ratios to handle zero-success baselines. |

## Resolved Tasks

*The following tasks were refined to address panel concerns regarding ambiguity and missing parameters.*

- **T001c (Revised)**: Compute SHA256 of the *populated* `requirements.txt` and `pytest.ini` created in T002/T003. Do NOT hash empty skeletons.
- **T005c (Revised)**: Execute `verify_manifest.py` to compute SHA256 of the *populated* `data/raw/dataset_manifest.jsonl`. Record the hash under `artifact_hashes.data_raw` in the state YAML. Include `FileNotFoundError` handling to abort if the manifest is missing.
- **T021a (Split)**: 
  . **Implement sweep generator**: Create `object_generator.py` to generate a set of objects (half with friction in a high range, half with friction in a low range).
  . **Execute sweep**: Run multiple trials per object for both static and adaptive policies. Output to `data/generated/sweep.csv` with columns: `trial_id`, `object_id`, `friction_coefficient`, `policy_type`, `success` (binary indicator), `k_est_mean`, `runtime_seconds`.

## Project Structure

### Documentation (this feature)

```text
specs/001-virtual-tactile-adaptation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/
├── code/
│   ├── __init__.py
│   ├── env/
│   │   ├── __init__.py
│   │   ├── dragmesh_wrapper.py      # Wraps PyBullet for DragMesh objects
│   │   └── virtual_tactile_estimator.py  # FR-001, FR-006, FR-007
│   ├── policy/
│   │   ├── __init__.py
│   │   ├── pica_baseline.py         # Static reward baseline
│   │   └── adaptive_reward_scheduler.py # FR-002
│   ├── data/
│   │   ├── __init__.py
│   │   ├── manifest_loader.py       # Loads DragMesh-2 manifest
│   │   └── object_generator.py      # FR-003: Generates novel geometries (stratified)
│   ├── experiments/
│   │   ├── __init__.py
│   │   ├── sweep_runner.py          # Executes multiple trials, range [0.0, 2.5]
│   │   ├── stats_analyzer.py        # FR-005: GLMM analysis (not t-test)
│   │   └── system_monitor.py        # Tracks RAM/CPU time for SC-003/004
│   └── utils/
│       ├── __init__.py
│       ├── validate_citations.py    # T008c: Validates DragMesh/PICA citations
│       └── verify_manifest.py       # T005c: Computes SHA256 of populated manifest
├── data/
│   ├── raw/
│   │   └── dataset_manifest.jsonl   # Downloaded from HF
│   ├── generated/
│   │   ├── sweep.csv                # T021a output: 100 trials, friction [0.0, 2.5]
│   │   └── novel_objects/           # Generated geometries
│   └── results/
│       ├── adaptive_success_rates.csv
│       ├── static_success_rates.csv
│       ├── system_metrics.json      # SC-003/004 verification
│       └── stat_test_results.json   # GLMM results (Odds Ratios)
├── tests/
│   ├── contract/
│   │   └── test_schemas.py          # Validates against contracts/*.yaml
│   ├── unit/
│   │   └── test_estimator.py        # Tests k_est calculation, epsilon handling
│   └── integration/
│       └── test_sweep.py            # Tests full pipeline on small subset
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize overhead for a research simulation. All simulation logic, data generation, and analysis reside in `code/` to ensure a single entry point for the CI runner. The `data/` directory is strictly for inputs (raw manifest) and outputs (generated sweeps, results), preserving the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is tightly bounded by the spec (CPU-only, a defined set of trials, specific friction ranges). The complexity of the estimator, scheduler, and GLMM analysis is intrinsic to the research hypothesis and cannot be simplified without invalidating the study. | N/A |