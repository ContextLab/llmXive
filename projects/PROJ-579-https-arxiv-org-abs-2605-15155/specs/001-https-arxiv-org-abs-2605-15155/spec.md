# Feature Specification: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

**Feature Branch**: `579-https-arxiv-org-abs-2605-15155-repro`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Self-Distilled Agentic Reinforcement Learning (SDAR) paper (arXiv:2605.15155) using the vendored SDAR codebase on CPU-only CI."

## User Scenarios & Testing

### User Story 1 - Environment Sanity & Entry Point Execution (Priority: P1)

**Description**: As a researcher, I need to verify that the vendored SDAR repository is correctly cloned, dependencies are resolvable on a standard Linux CPU environment, and the minimal entry point (Ray worker health check) executes without GPU acceleration errors.

**Why this priority**: This is the "smoke test" for the entire project. If the environment cannot launch the Ray cluster or import the core modules without CUDA, the project cannot proceed to actual training or evaluation. It validates the "Compute Feasibility" constraint immediately.

**Independent Test**: Execute the Ray CPU test script `tests/ray_cpu/check_worker_alive/main.py` in a fresh virtual environment. The test must pass if the environment is correctly configured.

**Acceptance Scenarios**:

1. **Given** the submodule `external/SDAR` is cloned and `requirements.txt` is installed in a CPU-only Python environment, **When** the command `python tests/ray_cpu/check_worker_alive/main.py` is executed, **Then** the script must complete successfully with exit code 0 and log "Ray cluster healthy" without any "CUDA not found" or "device_map" errors.
2. **Given** the environment has no GPU drivers installed, **When** the script attempts to initialize Ray, **Then** it must bind exclusively to CPU resources and report the available CPU count (e.g., "2 CPUs detected") without raising an `ImportError` for `torch.cuda`.

---

### User Story 2 - Minimal Training Run on Subsampled Data (Priority: P2)

**Description**: As a researcher, I need to execute a truncated SDAR training loop on a single ALFWorld task with a small batch size to verify that the core algorithm (Self-Distillation gating + RL) runs end-to-end and produces loss logs and model checkpoints.

**Why this priority**: This validates the mathematical and architectural correctness of the SDAR implementation. It confirms that the "gated auxiliary objective" and "token-level guidance" mechanisms execute without crashing, even if the run is too short to produce statistically significant results. This is a **sanity check** only.

**Independent Test**: Run the SDAR training script with hardcoded parameters for a limited number of steps on a single ALFWorld environment instance. The run must produce a loss curve file and a checkpoint file.

**Acceptance Scenarios**:

1. **Given** the training script is configured for `num_steps=10`, `batch_size=1`, and `env=alfworld`, **When** the training loop starts, **Then** the system must log the "SDAR Gate Loss" and "RL Loss" values for at least 5 steps and save a checkpoint file (e.g., `step_5.pt`) to the output directory.
2. **Given** the training run is limited to 10 steps, **When** the process completes, **Then** the script must exit cleanly with a summary report showing the final average loss, and the output directory must contain at least one non-empty artifact file.

---

### User Story 3 - Evaluation & Metric Reporting (Priority: P3)

**Description**: As a researcher, I need to run the evaluation script on a tiny subset of the ALFWorld test set to confirm that the system can interact with the environment, parse rewards, and output success rate metrics.

**Why this priority**: This validates the "Reproduction" claim by ensuring the evaluation harness works. It confirms that the system can successfully complete a task and report a score, which is necessary to compare against the paper's claims (e.g., "+[deferred] on ALFWorld").

**Independent Test**: Execute the evaluation script on a representative subset of ALFWorld tasks. The system must output a JSON or text report with a "success_rate" metric.

**Acceptance Scenarios**:

1. **Given** a trained (or randomly initialized) model and the evaluation script configured for `num_tasks=5`, **When** the evaluation loop runs, **Then** the system must attempt to solve each task and output a final success rate (e.g., "Success Rate: 0.XX") to the console and a log file. Success is defined as the ALFWorld environment returning a `success=True` flag. If the environment times out (exceeds a predefined threshold), the task is recorded as a failure, and the system continues.
2. **Given** the evaluation encounters a task timeout, **When** the task fails, **Then** the system must record the failure reason (e.g., "Max steps exceeded") in the log and continue to the next task without crashing the entire evaluation suite.

---

### User Story 4 - Baseline Comparison & Statistical Analysis (Priority: P1)

**Description**: As a researcher, I need to execute a comparative training run using a standard PPO baseline (without self-distillation) on the same task and seeds, and perform a paired t-test to validate the hypothesis that self-distillation improves sample efficiency or stability.

**Why this priority**: The core research question is "Does self-distillation help?". A single SDAR run cannot answer this. This user story ensures the scientific validity of the reproduction by enforcing a controlled comparison and statistical testing, as mandated by the paper's methodology.

**Independent Test**: Run the SDAR training script and the PPO baseline script for multiple independent random seeds with aggressive downsampling (e.g., a reduced step count per seed) to fit within the CI time limit. Perform a paired t-test on the final success rates or cumulative rewards.

**Acceptance Scenarios**:

1. **Given** the configuration for 5 random seeds, **When** the pipeline executes both `external/SDAR/agent_system/train.py` (SDAR mode) and the baseline script (PPO mode), **Then** the system must generate separate log files for each seed and each method, containing loss and reward data.
2. **Given** the collected metrics from 5 seeds, **When** the analysis script runs, **Then** it must output a p-value from a paired t-test comparing SDAR vs. PPO, and report whether the difference is statistically significant (p < 0.05).

---

### Edge Cases

- **Ray Resource Contention**: What happens if the GitHub Actions runner has limited CPU availability (e.g., < 2 cores)? The system must detect available cores and adjust `ray init` parameters to avoid hanging.
- **Import Errors in Vendored Code**: What happens if the vendored `SDAR` repository has local dependencies (e.g., specific versions of `alfworld` or `verl`) that conflict with the runner's global packages? The system must isolate dependencies via a virtual environment or container.
- **Environment Stuck State**: What happens if the ALFWorld environment enters an infinite loop during evaluation? The system must enforce a hard timeout (e.g., a predefined duration per task) and abort the specific task, logging the timeout.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the Ray CPU worker health check (`tests/ray_cpu/check_worker_alive/main.py`) and confirm successful initialization on a CPU-only runner (See US-1).
- **FR-002**: System MUST run the SDAR training loop for a minimum of 10 steps on a single ALFWorld environment instance without raising CUDA-related errors. This run is a **sanity check** only; the primary research goal is the statistical comparison defined in FR-008 (See US-2).
- **FR-003**: System MUST generate and persist at least one model checkpoint file (e.g., `.pt` or `.safetensors`) and a training log file containing loss values for the SDAR gate and RL components (See US-2).
- **FR-004**: System MUST execute the evaluation script on a minimum of 5 ALFWorld tasks and output a structured success rate metric (See US-3).
- **FR-005**: System MUST enforce a maximum execution time per evaluation task of ≤ 60 seconds to ensure real-time responsiveness and prevent infinite loops (See US-3).
- **FR-006**: System MUST force CPU device assignment (e.g., `device_map="cpu"`) and ensure no GPU-related imports are executed. At runtime, the system MUST report 0 GPUs detected during initialization (See US-1).
- **FR-007**: System MUST parse actual execution logs from `external/SDAR/agent_system/train.py` and `external/SDAR/agent_system/eval.py` to generate data artifacts, prohibiting synthetic data generation (See US-2, US-3).
- **FR-008**: System MUST execute a baseline PPO training run for 5 independent random seeds with aggressive downsampling (e.g., 1000 steps per seed) to enable statistical comparison (See US-4).
- **FR-009**: System MUST perform a paired t-test (or non-parametric equivalent) on the results from 5 seeds to compare SDAR vs. PPO performance (See US-4).

### Key Entities

- **SDAR Model**: The LLM agent implementation including the self-distillation gating mechanism and RL backbone.
- **ALFWorld Environment**: The simulated household task environment used for training and evaluation.
- **Training Log**: A text or JSON file recording loss values, step counts, and gate activation statistics.
- **Evaluation Report**: A structured output containing success rates, task completion times, and failure modes.
- **Statistical Report**: A JSON or text file containing the p-value and conclusion of the paired t-test.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Ray health check script MUST complete successfully and report CPU-only resource allocation, measured against the script's expected success output (See US-1).
- **SC-002**: The training run MUST produce a log file containing at least 5 recorded loss values for both "SDAR Gate Loss" and "RL Loss", measured against the training script's logging interval (See US-2).
- **SC-003**: The evaluation run MUST produce a report with a calculated "success_rate" value (0.0 to 1.0) based on the tasks attempted. A rate of 0.0 or a partial calculation (denominator < 5) is a valid pipeline success, measured against the evaluation script's output format (See US-3).
- **SC-004**: The total wall-clock time for the entire reproduction pipeline (sanity check + training + evaluation + baseline comparison) MUST be ≤ 6 hours, measured against the GitHub Actions job timer (See US-2, US-3, US-4).
- **SC-005**: No runtime errors related to CUDA, GPU memory, or missing accelerators MUST occur during execution, measured against the standard error log (See US-1, FR-006).
- **SC-006**: Data artifacts (CSV/JSON) MUST be derived from parsing actual log files generated by `external/SDAR/agent_system/train.py` and `eval.py`, verified by the presence of a unique session ID generated at runtime and file modification time within the execution window (See FR-007).
- **SC-007**: The baseline comparison MUST produce a statistical report containing a p-value from a paired t-test comparing SDAR and PPO across 5 seeds, measured against the analysis script's output (See US-4).
- **SC-008**: The statistical report MUST explicitly state whether the difference in performance is statistically significant (p < 0.05) or not (See US-4).

## Assumptions

- **Assumption about Compute Environment**: The GitHub Actions runner provides at least 2 CPU cores and 7 GB of RAM, which is sufficient for running a small-scale SDAR training loop and ALFWorld evaluation without GPU acceleration.
- **Assumption about Data Availability**: The ALFWorld environment dependencies and pre-compiled assets (e.g., PDDL files, Thor binaries) are included in the vendored `external/SDAR` submodule or can be downloaded automatically during the first run without requiring external network access beyond the repository.
- **Assumption about Code Stability**: The vendored `external/SDAR` codebase is in a stable state where the entry points (`tests/ray_cpu/check_worker_alive/main.py`, `external/SDAR/agent_system/train.py`, `external/SDAR/agent_system/eval.py`) are functional and do not require immediate patching of syntax errors or missing imports.
- **Assumption about Training Scope**: The reproduction aims to validate the *mechanism's effect* via comparative analysis (US-4). The 10-step run (US-2) is a sanity check; the primary research goal is the statistical comparison of SDAR vs. PPO.
- **Assumption about Dependencies**: The Python environment can be isolated using a virtual environment or `conda` to resolve version conflicts between the SDAR dependencies and the runner's base system packages.
- **Assumption about Timeout Configuration**: The ALFWorld environment's default timeout settings are compatible with the 60-second hard limit enforced by the evaluation script; if the environment requires longer for complex tasks, the timeout will trigger a recorded failure rather than a hang.
- **Assumption about CI Time Limit**: The GitHub Actions CI job time limit is defined as a duration sufficient to accommodate the sanity check and the statistically valid baseline comparison with aggressive downsampling (e.g., 1000 steps per seed).
- **Assumption about Statistical Power**: Due to the 6-hour constraint, the number of steps per seed in the baseline comparison (US-4) will be aggressively downscaled (e.g., to 1000 steps) to ensure the 5-seed experiment completes, acknowledging that this may limit the magnitude of detectable effects but preserves the methodological requirement for a paired test.