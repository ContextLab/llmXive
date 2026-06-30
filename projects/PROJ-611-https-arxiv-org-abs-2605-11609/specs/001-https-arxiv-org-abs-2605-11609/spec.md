# Feature Specification: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information

**Feature Branch**: `611-antisd-reproduction`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Anti-Self-Distillation for Reasoning RL via Pointwise Mutual Information (arXiv:2605.11609) using vendored code at external/AntiSD."

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1)

The researcher MUST be able to initialize the project environment on a standard CPU-only CI runner (minimal core count, limited RAM) without requiring GPU drivers, CUDA, or large model downloads., ensuring the codebase is runnable for validation.

**Why this priority**: This is the absolute prerequisite. If the environment cannot be established without GPU hardware (which is unavailable in the free-tier runner), the project cannot proceed to execution. The paper's implementation relies on heavy deep learning frameworks (PyTorch, Megatron, vLLM) which typically default to GPU; the spec must enforce a CPU-tractable path.

**Independent Test**: A clean GitHub Actions runner executes the environment setup script and completes without crashing due to missing CUDA libraries or out-of-memory errors, producing a `requirements.txt` compatible with CPU-only execution.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner with 2 CPU cores and 7 GB RAM, **When** the user runs the environment initialization script (`scripts/install_vllm_sglang_mcore.sh` with CPU flags or a modified `requirements.txt`), **Then** the installation completes successfully without attempting to load CUDA kernels or downloading >10 GB of model weights.
2. **Given** the installed dependencies, **When** the user runs `python scripts/diagnose.py`, **Then** the script reports "CPU Mode Active" and confirms that PyTorch is available on CPU without raising `ImportError` for `torch.cuda`.

---

### User Story 2 - Data Preprocessing and Sample Execution (Priority: P2)

The researcher MUST be able to preprocess a small, representative subset of the math dataset (e.g., GSM8k) and execute a single training step or rollout loop to verify the AntiSD logic (divergence ascent) functions correctly without running the full multi-day training.

**Why this priority**: This validates the core algorithmic implementation (the "AntiSD" mechanism) without consuming the full 6-hour compute budget. It confirms that the "ascend divergence" logic and "entropy-triggered gate" are implemented as described in the paper.

**Independent Test**: The user runs the preprocessing script on a sample subset of GSM8k. and executes the `run/olmo3-instruct/antisd.sh` (or equivalent) with a `--max-steps 1` flag, observing the generation of a loss log that reflects the AntiSD objective.

**Acceptance Scenarios**:

1. **Given** the raw GSM8k dataset, **When** the user executes `data/preprocess_math_datasets.py` with a `--limit 50` flag, **Then** the script produces a processed JSONL file containing exactly 50 samples with the required fields (prompt, solution, reasoning trace) within 2 minutes.
2. **Given** the preprocessed 50-sample dataset, **When** the user launches the training script with `--max-steps 1` and `--use-cpu`, **Then** the script executes at least one forward/backward pass, outputs a log entry containing "AntiSD Loss" or "Divergence" metrics, and terminates without OOM errors.

---

### User Story 3 - Artifact Generation and Validation Report (Priority: P3)

The researcher MUST be able to generate the final validation artifacts (figures, logs, and a summary report) that compare the observed behavior against the paper's claims (e.g., "reaches GRPO baseline accuracy in 2-10x fewer steps" or "improves accuracy by up to 11.5 points") based on the limited run.

**Why this priority**: This delivers the final output of the reproduction project. Since full reproduction of the paper's large-scale results is impossible on free-tier CPU, the artifact must be a "validation report" confirming the code runs and produces *some* result, while explicitly stating the limitations of the partial run.

**Independent Test**: The pipeline finishes and generates a `validation_report.md` and `figures/validation_trace.png` in the `data/` directory, which are committed to the repository.

**Acceptance Scenarios**:

1. **Given** a completed (or time-broken) training run, **When** the user executes the post-processing script (`scripts/rollout_viewer.py` or a custom validation script), **Then** the script generates a `validation_report.md` containing a table of "Observed Steps" vs "Paper Claimed Steps" and a status of "Partial Reproduction" or "Algorithm Validated".
2. **Given** the run logs, **When** the user checks the `data/` directory, **Then** a `figures/validation_trace.png` exists showing the loss curve for the limited run, and the file size is < 10 MB.

### Edge Cases

- **What happens when** the dataset preprocessing script attempts to download a model checkpoint that is >7 GB? **How does the system handle it?** The system MUST detect the size constraint and either abort with a clear "Model too large for CPU-only runner" error or automatically switch to a smaller, quantized (CPU-safe) model if available in the config.
- **How does the system handle** a CUDA device detection failure? The system MUST fall back to CPU execution mode immediately without crashing, logging a warning that GPU acceleration is disabled.
- **What happens when** the "entropy-triggered gate" logic receives a NaN entropy value? The system MUST clamp the value to a safe range to prevent training divergence and log the event.

## Requirements

### Functional Requirements

- **FR-001**: System MUST initialize the Python environment with PyTorch and dependencies in CPU-only mode, explicitly disabling CUDA detection, to ensure execution on free-tier runners (See US-1).
- **FR-002**: System MUST preprocess the GSMk dataset into a sample subset of exactly 50 entries to enable rapid validation without exceeding RAM limits (See US-2).
- **FR-003**: System MUST execute the AntiSD training loop for a minimum of 1 step and a maximum of 100 steps (configurable), logging the divergence metric at every step (See US-2).
- **FR-004**: System MUST implement the "entropy-triggered gate" logic where the AntiSD term is disabled if teacher entropy collapses below a threshold of 0.01, as described in the paper (See US-2).
- **FR-005**: System MUST generate a `validation_report.md` artifact that explicitly compares the observed step count to the paper's claim of "2-10x fewer steps" and notes if the full benchmark was not reached due to compute constraints (See US-3).

### Key Entities

- **Dataset Subset**: A JSONL file containing a bounded number (50) of math reasoning problems with prompts and solutions, derived from GSM8k.
- **AntiSD Log**: A structured log file recording the "Divergence" loss, "Teacher Entropy", and "Gate Status" (Enabled/Disabled) for each training step.
- **Validation Report**: A Markdown document summarizing the execution status, artifacts generated, and the validity of the code against the paper's theoretical claims.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The environment setup duration is measured against a predefined timeout threshold. to ensure CI feasibility (See US-1).
- **SC-002**: The memory usage during the single-step training is measured against the available RAM limit. to confirm CPU tractability (See US-2).
- **SC-003**: The "AntiSD Loss" metric is measured against a non-NaN, non-infinite value to confirm the divergence ascent logic is active (See US-2).
- **SC-004**: The `validation_report.md` completeness is measured against a checklist of 5 required fields (Run ID, Steps Executed, Loss Value, Gate Status, Conclusion) (See US-3).

## Assumptions

- **Assumption about compute constraints**: The project assumes that a full reproduction of the paper's results (training large-scale models on full datasets) is impossible on the free-tier runner.; therefore, the scope is limited to "algorithmic validation" via small-scale sampling and single-step execution.
- **Assumption about model availability**: The project assumes that a small, CPU-tractable model (e.g., a model with a reduced parameter count or a quantized version) can be used for the validation run if the default large-scale models are too large for the available RAM limit.., and that the `run/` scripts can be modified to point to this smaller model.
- **Assumption about dataset access**: The project assumes that the GSM8k dataset is accessible via the Hugging Face `datasets` library without requiring a private token or large download, or that a local cached version is available.
- **Assumption about paper claims**: The project assumes that the "entropy-triggered gate" threshold of 0.01 (or similar small value) is a standard parameter derived from the paper's methodology and does not require further tuning for the validation run.
