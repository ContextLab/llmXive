# Feature Specification: Reproduce & Validate EffOPD On-Policy Distillation

**Feature Branch**: `597-reproduce-effopd-validation`  
**Created**: 2025-05-23  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Learning to Foresee: Unveiling the Unlocking Efficiency of On-Policy Distillation (arXiv:2605.11739) using vendored EffOPD code."

## User Scenarios & Testing

### User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1)

The research engineer MUST be able to initialize the reproduction environment within the free-tier GitHub Actions runner constraints (CPU-only, ≤7 GB RAM) by installing dependencies and verifying the submodule presence without triggering GPU-specific errors.

**Why this priority**: Without a runnable environment, no validation can occur. This is the gatekeeper step. The paper claims "no additional trainable modules," but the codebase includes heavy dependencies (e.g., `vllm`, `transformers`) that must be constrained to CPU-compatible versions to prevent CI failure.

**Independent Test**: Execute the environment setup script on a fresh runner; verify that `pip install` completes without CUDA-related errors and that the `EffOPD` submodule is present at the expected path.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner (2 vCPU, 7 GB RAM, no GPU), **When** the environment setup script runs `pip install -r requirements.txt` (filtered for CPU-only packages), **Then** the installation must complete successfully without `ImportError` related to `torch.cuda` or `bitsandbytes`, and the `projects/PROJ-597-.../external/EffOPD` directory must exist.
2. **Given** the environment is initialized, **When** the script attempts to import the primary `verl` or `EffOPD` modules, **Then** the import must succeed without raising `RuntimeError: Found no CUDA device`.

---

### User Story 2 - Execution of Lightweight Validation Scripts (Priority: P1)

The system MUST execute the lightweight analysis scripts (SVD, rank analysis, data loading) provided in the `Analysis/` directory to generate initial artifacts and confirm data integrity.

**Why this priority**: These scripts represent the core "validation" of the paper's methodological claims (update direction, low-rank concentration) without requiring full-scale training. They are the primary evidence of the code working as intended.

**Independent Test**: Run the `svd.py` and `upd_rank.py` scripts on a small subset of the provided dataset (e.g., `gsm8k`); verify that output files (CSV/JSON/Plot) are generated and contain numerical data.

**Acceptance Scenarios**:

1. **Given** the `Analysis/eval/svd.py` script and a sample dataset (e.g., `data/gsm8k/test.jsonl`), **When** the script is executed, **Then** it must complete within 30 minutes and produce an output file (e.g., `svd_results.csv`) containing at least 10 rows of singular value data.
2. **Given** the `Analysis/eval/upd_rank.py` script, **When** executed on the same dataset, **Then** it must generate a rank analysis artifact showing non-zero rank concentration metrics, confirming the script logic is functional.

---

### User Story 3 - Full Pipeline Execution and Artifact Generation (Priority: P2)

The system MUST execute the full reproduction pipeline (or a representative subset if full training exceeds 6 hours) to generate the final evaluation artifacts (e.g., `reasoning_eval` results) and confirm the "3x acceleration" claim structure.

**Why this priority**: This validates the end-to-end claim of the paper. While full training might be resource-intensive, a partial run or a pre-trained model inference pass must produce the specific metrics claimed (pass@k, accuracy) to validate the codebase's output format.

**Independent Test**: Run the `reasoning_eval.py` script or the `run_evalplus.sh` script on a minimal subset of problems; verify that the output includes the specific metric headers defined in the paper (e.g., `Pass@1`, `Pass@10`).

**Acceptance Scenarios**:

1. **Given** the `Analysis/eval/reasoning_eval.py` script and a subset of math problems, **When** the script runs, **Then** it must produce a result file containing the headers `Pass@1`, `Pass@5`, and `Pass@10` with numerical values (not NaN or null).
2. **Given** the `EffOPD/code_eval/scripts/run_evalplus.sh` script, **When** executed on the `HumanEvalPlus` dataset (subset), **Then** it must complete within 2 hours and output a summary JSON with at least one non-zero pass rate.

---

### Edge Cases

- **What happens when** the dataset download fails or the file is corrupted? The system MUST detect the missing file, halt execution with a clear error code (non-zero), and log the specific missing file path.
- **How does the system handle** memory overflow during SVD on larger datasets? The system MUST implement a chunked processing strategy or sample size limit (e.g., A sample size sufficient to ensure statistical power will be used.) to ensure the process stays under 7 GB RAM, failing gracefully with a "Memory Limit Exceeded" warning if the limit is breached.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `Analysis/eval/svd.py` script on the `gsm8k` dataset subset (≤500 samples) to generate singular value decomposition artifacts, ensuring the process completes within 45 minutes on a -core CPU. (See US-1)
- **FR-002**: The system MUST execute the `Analysis/eval/upd_rank.py` script to compute update rank concentration metrics, outputting a CSV file with columns `layer_id`, `rank`, and `concentration_score`. (See US-2)
- **FR-003**: The system MUST run the `reasoning_eval.py` script on a subset of problems from `data/aime24/test.jsonl`. and produce a JSON report containing `Pass@1`, `Pass@5`, and `Pass@10` metrics. (See US-3)
- **FR-004**: The system MUST validate that no CUDA-specific dependencies (e.g., `bitsandbytes`, `load_in_8bit`) are invoked during execution, forcing all model inference and training steps to run on CPU. (See US-1)
- **FR-005**: The system MUST implement a memory guardrail that samples the dataset to ≤7 GB total memory usage (approx. a substantial corpus of tokens) before loading data into the analysis scripts. (See US-2)

### Success Criteria

- **SC-001**: The `svd.py` execution produces a CSV file with ≥10 rows of valid numerical singular values, measured against the script's expected output schema. (See FR-001)
- **SC-002**: The `upd_rank.py` execution generates a CSV file where the `concentration_score` column contains values in the range [0.0, 1.0], measured against the mathematical definition of rank concentration. (See FR-002)
- **SC-003**: The `reasoning_eval.py` output JSON contains non-null values for `Pass@1`, `Pass@5`, and `Pass@10`, measured against the paper's reported metric definitions. (See FR-003)
- **SC-004**: The total wall-clock time for the full validation pipeline (US-1 + US-2 + US-3) on the specified subsets is ≤4 hours, measured against the -hour GitHub Actions limit. (See FR-005)
- **SC-005**: The execution log contains zero occurrences of `RuntimeError: Found no CUDA device` or `ImportError: No module named 'bitsandbytes'`, measured against the runtime logs. (See FR-004)

## Assumptions

- **Assumption about data availability**: The `EffOPD` submodule at `projects/PROJ-597-https-arxiv-org-abs-2605-11739/external/EffOPD/` contains all necessary data files (e.g., `data/gsm8k/test.jsonl`) locally or can download them within the available disk limit without external network restrictions.
- **Assumption about compute constraints**: The "3x acceleration" claim in the paper is based on full-scale training; This reproduction will validate the *mechanism* (SVD, rank analysis) and *output format* on a CPU-only, sampled dataset, as full training exceeds the free-tier time limit.
- **Assumption about model weights**: The analysis scripts rely on pre-trained model weights (e.g., Qwen, Llama) that are available via Hugging Face Hub and can be loaded in 16-bit or 32-bit precision on CPU without requiring 8-bit quantization libraries.
- **Assumption about dataset-variable fit**: The provided datasets (`gsm8k`, `aime24`, etc.) contain the necessary problem statements and ground truths required by the `reasoning_eval.py` grader; no additional external variables are needed.
- **Assumption about inference**: The evaluation scripts use a small, CPU-tractable model (e.g., `Qwen/Qwen2.5-0.5B-Instruct`) for inference during the validation phase to ensure feasibility on free-tier hardware.
