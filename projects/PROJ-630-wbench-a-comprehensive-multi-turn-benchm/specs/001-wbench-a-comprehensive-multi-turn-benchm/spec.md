# Feature Specification: Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

**Feature Branch**: `PROJ-630-wbench-a-comprehensive-multi-turn-benchm/001-reproduce-validate-wbench`  
**Created**: 2025-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation. The code is vendored as a submodule. Task is to run, validate, and reproduce the shipped implementation end-to-end."

## User Scenarios & Testing

### User Story 1 - Validate Environment & Dependency Installation (Priority: P1)

**Journey**: The user (researcher/CI runner) verifies that the vendored WBench codebase can be installed and its dependencies resolved on a standard CPU-only GitHub Actions runner without GPU acceleration.

**Why this priority**: Without a successful installation and environment verification, no execution or validation can occur. This is the foundational step for reproducibility.

**Independent Test**: Execute the provided `tools/install.sh` and `tools/verify_install.py` scripts; the system must exit with code 0 and report all required tools (e.g., Python, specific libraries) as "Ready".

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner (Ubuntu, 2 CPU, 7GB RAM), **When** the user runs `tools/install.sh`, **Then** the script completes without error and `tools/verify_install.py` reports all dependencies as installed.
2. **Given** the environment is set up, **When** the user attempts to import the core `src` modules, **Then** no `ImportError` or `ModuleNotFoundError` occurs.

---

### User Story 2 - Execute Core Evaluation Pipeline on Sample Data (Priority: P1)

**Journey**: The user runs the main evaluation pipeline (`main.py` or `src/evaluate.py`) against a minimal, representative subset of the WBench dataset (e.g., 2-3 test cases) to confirm the end-to-end flow of video generation, metric calculation, and result aggregation works.

**Why this priority**: This validates the core logic of the benchmark. If the pipeline fails on a small scale, it will fail on the full dataset. It confirms the "reproduction" aspect.

**Independent Test**: Run the evaluation script with a `--subset` flag (or equivalent) targeting a representative subset of test cases; the system must produce a JSON/CSV result file containing non-null metric values for all sub-metrics.

**Acceptance Scenarios**:

1. **Given** the environment is valid and a sample of 2 test cases is selected, **When** the user executes `python main.py --subset 2`, **Then** the process completes within 60 minutes and outputs a results file with valid numerical scores for all dimensions (video quality, setting adherence, interaction adherence, consistency, physics compliance).
2. **Given** the pipeline runs, **When** the user inspects the output logs, **Then** no CUDA/GPU-related errors (e.g., "CUDA out of memory", "No GPU found") are raised, confirming CPU-only execution.

---

### User Story 3 - Aggregate Full Dataset Results & Generate Diagnostics (Priority: P2)

**Journey**: The user executes the evaluation against the full WBench dataset (289 cases, multiple turns) to reproduce the paper's aggregate statistics and generate the diagnostic insights/leaderboards.

**Why this priority**: This fulfills the primary research goal of "reproducing" the paper's findings at scale. It validates the benchmark's utility across its intended scope.

**Independent Test**: Run the full evaluation; the system must produce a final leaderboard CSV and a summary report that matches the structure of the paper's `assets/leaderboard_*.csv` files.

**Acceptance Scenarios**:

1. **Given** the full dataset is available and the pipeline is stable, **When** the user runs the full evaluation, **Then** the system completes within the CI time limit and generates a `final_results.csv` containing metrics for all test cases.
2. **Given** the results are generated, **When** the user compares the aggregated mean scores against the paper's reported values, **Then** the values are within a pre-defined tolerance (e.g., ±0.05) or the deviation is documented as a reproducibility variance.

---

### Edge Cases

- **What happens when a specific video generation model API times out?** The system MUST implement a retry mechanism (with a configurable maximum number of attempts) and log the failure without crashing the entire batch; the specific case is marked as "Failed" in the results.
- **How does the system handle missing ground-truth data for a specific test case?** The system MUST skip the specific metric calculation for that case and log a warning, ensuring the rest of the evaluation proceeds.
- **What happens if a metric calculation (e.g., physics compliance) requires more memory than available?** The system MUST detect the memory pressure, gracefully degrade (e.g., process in smaller chunks), or fail the specific metric while preserving the partial results of other metrics.

## Requirements

### Functional Requirements

- **FR-001**: System MUST successfully install all Python dependencies listed in `tools/requirements.txt` and `src/requirements.txt` on a CPU-only environment without requiring CUDA or GPU drivers. (See US-1)
- **FR-002**: System MUST execute the `tools/verify_install.py` script and return a "PASS" status only if all critical components (video processing libraries, metric evaluators) are functional. (See US-1)
- **FR-003**: System MUST process a minimum of 2 test cases from the WBench dataset and output a valid JSON/CSV result file containing values for all 22 sub-metrics. (See US-2)
- **FR-004**: System MUST handle API timeouts or generation failures for individual test cases by logging the error and marking the case as "failed" without terminating the entire pipeline. (See US-2)
- **FR-005**: System MUST aggregate results from all test cases into a single leaderboard CSV file that includes mean scores for the five dimensions: video quality, setting adherence, interaction adherence, consistency, and physics compliance. (See US-3)
- **FR-006**: System MUST compute and report the "consistency" and "physics compliance" metrics using the specific sub-modules (`src/metrics/consistency/`, `src/metrics/physical/`) defined in the codebase. (See US-3)

### Key Entities

- **Test Case**: A single entry in the WBench dataset defining a world setting, interaction sequence, and expected outcome.
- **Metric Score**: A numerical value (0.0–1.0 or similar) representing the performance of a model on a specific sub-metric (e.g., "motion_smoothness").
- **Leaderboard**: An aggregated dataset containing performance scores across all models and dimensions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Installation success rate is measured against the requirement that `tools/verify_install.py` exits with code 0 and reports [deferred] dependency readiness. (See FR-001, US-1)
- **SC-002**: Pipeline execution success is measured by the generation of a results file containing non-null values for ≥95% of the 22 sub-metrics across the sample test cases. (See FR-003, US-2)
- **SC-003**: Reproducibility fidelity is measured by the structural match of the generated `final_results.csv` to the paper's `assets/leaderboard_9models_full.csv` schema (columns and data types). (See FR-005, US-3)
- **SC-004**: Resource compliance is measured by the total execution time of the full dataset evaluation remaining ≤6 hours on a 2-core CPU runner. (See FR-005, US-3)
- **SC-005**: Error resilience is measured by the system's ability to process 289 test cases where ≥90% of cases complete successfully even if individual API calls fail. (See FR-004, US-2)

## Assumptions

- **Assumption about hardware**: The GitHub Actions free-tier runner (standard CPU allocation, ~7GB RAM) is sufficient to run the evaluation scripts, provided that heavy video generation models are either mocked, replaced with smaller CPU-compatible alternatives, or the evaluation focuses on the *metric calculation* logic rather than generating new high-fidelity videos from scratch (as generating a substantial volume of video turns may exceed CPU time limits).
- **Assumption about data availability**: The vendored submodule `external/WBench` contains the complete dataset (289 cases) or a mechanism to download it that does not require external authentication.
- **Assumption about model access**: The evaluation of "interactive world models" in the paper may rely on external APIs or pre-trained models; this spec assumes that for the purpose of *reproducing the benchmark logic*, we can either use a small subset of open models or mock the model generation step to focus on the metric evaluation pipeline.
- **Assumption about metric validity**: The automatic sub-metrics defined in the codebase are mathematically sound and do not require GPU acceleration for their calculation. (e.g., they rely on lightweight vision models or statistical comparisons).
- **Assumption about time limits**: The full evaluation of all cases can be completed within the 6-hour CI window. if the video generation step is optimized or if the benchmark is run in a "dry-run" mode that skips heavy generation and focuses on metric computation.
