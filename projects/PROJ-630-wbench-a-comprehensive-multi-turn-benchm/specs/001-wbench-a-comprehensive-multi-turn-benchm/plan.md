# Implementation Plan: Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

**Branch**: `PROJ-630-wbench-a-comprehensive-multi-turn-benchm/001-reproduce-validate-wbench` | **Date**: 2025-05-22 | **Spec**: `specs/PROJ-630/001-reproduce-validate-wbench/spec.md`
**Input**: Feature specification from `/specs/PROJ-630/001-reproduce-validate-wbench/spec.md`

## Summary

This feature aims to reproduce and validate the WBench benchmark implementation. The primary requirement is to execute the vendored WBench codebase on a standard CPU-only GitHub Actions runner, validating the installation, processing a sample of test cases, and aggregating results to match the paper's structure. 

**Critical Constraint**: To ensure scientific validity, **no mocking of video data or metric models is permitted for the evaluation phase**. The pipeline will strictly use real video assets provided in the verified WBench dataset. If a video asset is missing, the case is skipped. Model architectures must match the original paper; CPU feasibility is addressed via frame sampling and subset selection, not model substitution.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU wheel), `scikit-learn`, `opencv-python`, `pandas`, `numpy`, `requests`, `huggingface-hub`  
**Storage**: Local file system (temporary CI storage), Parquet files for data  
**Testing**: `pytest` (for unit tests), shell scripts for integration (install/verify)  
**Target Platform**: Linux (Ubuntu) GitHub Actions Runner (CPU-only)  
**Project Type**: Research Benchmark / CLI Tool  
**Performance Goals**: Complete subset evaluation (50 cases) within 6 hours; sample run (<5 mins). Full case run is flagged as 'Proxy Evaluation' if it exceeds time limits.  
**Constraints**: No GPU/CUDA; Memory < 7GB; Disk < 14GB; No external API keys required for core logic (unless specified by metric).  
**Scale/Scope**: A target set of test cases, metric dimensions, sub-metrics.

## Constitution Check

*Note: No specific `constitution.md` was supplied for this project. The plan adheres to 'Default Research Integrity' principles derived from standard scientific reproducibility standards:*

- **Principle I: Data Validity**: The plan mandates the use of real video data from the verified WBench dataset for all metric calculations. Mocking of video frames or generation is strictly forbidden in the evaluation phase (US-2, US-3).
- **Principle II: Resource Honesty**: The plan explicitly acknowledges CPU limitations. It does not invent new performance requirements but adapts the scope (subset sampling, frame skipping) to fit constrained computational resources without compromising metric definitions.
- **Principle III: Model Fidelity**: The plan commits to using the original model architectures specified in the WBench paper. No substitution with smaller models (e.g., DistilBERT) is permitted, as this would invalidate the metric construct.
- **Principle IV: Error Resilience**: The plan includes specific steps for skipping missing assets and handling network timeouts, ensuring partial results are preserved (FR-004, SC-005).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── metrics/
│   ├── consistency/     # Consistency metric logic
│   ├── physical/        # Physics compliance logic
│   └── quality/         # Video quality metrics
├── evaluation/
│   ├── runner.py        # Main evaluation orchestration
│   └── aggregator.py    # Result aggregation
├── utils/
│   ├── logger.py
│   └── retry.py
└── cli/
    └── main.py          # Entry point

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: The structure mirrors the spec's description of `src/metrics/` sub-modules and `src/evaluate.py` (mapped to `evaluation/runner.py`). The `cli` module handles the `main.py` entry point. This separation ensures modularity for testing individual metrics and the full pipeline.

## Phase Breakdown

### Phase 0: Environment & Dependency Validation (FR-001, FR-002, SC-001)
- **Goal**: Ensure the environment is set up without GPU requirements.
- **Steps**:
  1. Install Python 3.10+ and system dependencies (ffmpeg, etc.).
  2. Install `requirements.txt` with CPU-only constraints (e.g., `torch --index-url https://download.pytorch.org/whl/cpu`).
  3. Execute `tools/verify_install.py`.
  4. **Success Criterion**: Exit code 0, all dependencies "Ready".
  5. **Dataset Schema Verification**: Load the WBench Parquet file and verify the presence of required columns: `case_id`, `prompt`, `interaction_sequence`, `video_path`, `ground_truth`. 
     - **Critical Check**: If `interaction_sequence` or `ground_truth` columns are missing, the pipeline halts with a "Dataset Mismatch" error. We do not assume these fields exist.
     - If `video_path` points to missing files, the pipeline logs a warning but proceeds to check other cases.

### Phase 1: Sample Data Execution (FR-003, SC-002)
- **Goal**: Run the pipeline on a minimal subset (a small number of cases) using **real video data**.
- **Steps**:
  1. Download/Load the verified WBench parquet dataset.
  2. Select a small number of test cases that have valid `video_path` entries.
  3. **No Mocking**: If a video file is missing, skip the case. Do not generate dummy frames.
  4. Execute metric calculations (Quality, Adherence, Consistency, Physics) on the real video frames.
  5. **Success Criterion**: Valid JSON/CSV output with non-null values for all sub-metrics. No CUDA errors.

### Phase 2: Full Dataset Aggregation (FR-005, FR-006, SC-003, SC-004)
- **Goal**: Process a representative subset or full dataset if time permits.
- **Steps**:
  1. Iterate through the WBench dataset.
  2. **Frame Sampling**: To meet CPU time limits, process only a reduced number of frames per second (or a fixed subset) for heavy metrics (Optical Flow, VLM).
  3. **Retry Logic**: Implement retry only for network-dependent steps (e.g., model loading from HuggingFace). **No retry for local video processing**.
  4. Aggregate results into `final_results.csv`.
  5. Compute mean scores for the dimensions.
  6. **Success Criterion**: `final_results.csv` matches the schema of `assets/leaderboard_9models_full.csv`. Execution time ≤ 6 hours. If time limit is breached, the run is labeled 'Proxy Evaluation (Subset)'.

### Phase 3: Validation & Reporting (SC-005)
- **Goal**: Verify error resilience and structural reproducibility.
- **Steps**:
  1. Inject simulated network failures (for model loading) to test robustness.
  2. Compare the *structure* and *score ranges* of the generated `final_results.csv` against the paper's reported values.
  3. **Variance Analysis**: Any deviation is documented with its cause (e.g., "Frame sampling used", "CPU precision variance"). No fixed tolerance is set as a pass/fail criterion; the focus is on understanding the deviation.
  4. **Success Criterion**: ≥90% of cases (with valid video data) complete successfully; partial results preserved.

## Risk Management

- **Risk**: Video generation exceeds CPU time/memory.
  - **Mitigation**: The plan explicitly **skips** video generation. It uses pre-existing video assets from the dataset. If assets are missing, the case is skipped.
- **Risk**: Dataset variables missing.
  - **Mitigation**: Phase 0 includes a strict schema check. If `interaction_sequence` or `video_path` are missing, the pipeline halts with a clear error.
- **Risk**: External API dependencies.
  - **Mitigation**: Implement retry mechanisms for network calls. Fallback to 'skipped' status if retries fail.
- **Risk**: CPU Time Limit Exceeded.
  - **Mitigation**: Use frame sampling and subset selection (50 cases) as the default CI target. Full case run is optional and labeled 'Proxy Evaluation'.