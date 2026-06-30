# Feature Specification: Reproduce & Validate SU-01 Olympiad Reasoning

**Feature Branch**: `581-reproduce-su01-olympiad`  
**Created**: 2026-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified Scaling (arXiv:2605.13301). Code vendored at external/SU-01. Task: run, validate, reproduce end-to-end on CPU-only CI."

## User Scenarios & Testing

### User Story 1 - Validate Submodule Integrity and Environment Bootstrapping (Priority: P1)

**User Journey**: A researcher or CI runner clones the repository, initializes the git submodule to fetch the `SU-01` codebase, verifies file integrity, and bootstraps a CPU-only Python environment capable of importing the evaluation scripts without GPU dependencies.

**Why this priority**: Without a valid, reproducible codebase and a compatible runtime environment, no further execution or validation is possible. This is the foundational block for the entire reproduction effort.

**Independent Test**: The CI job initializes the submodule, installs dependencies (pinned to CPU-compatible versions), and successfully imports the `su01-eval` and `su01-train-slime` modules without throwing `ImportError` or CUDA-related exceptions.

**Acceptance Scenarios**:

1. **Given** the project root is clean, **When** the `git submodule update --init --recursive` command is executed, **Then** the `external/SU-01` directory contains the full file tree (including `su01-eval` and `su01-train-slime`) and the `.git` submodule configuration is valid.
2. **Given** the environment is a GitHub Actions free-tier runner (CPU-only, 7GB RAM), **When** the `build_conda.sh` or equivalent dependency installation script runs, **Then** the environment completes setup within 30 minutes and `python -c "import su01_eval"` executes without CUDA/GPU import errors.
3. **Given** the submodule is initialized, **When** the `su01-eval/decode/direct_gen.py` script is invoked with a `--help` flag, **Then** the script returns a valid help message indicating available arguments without crashing due to missing dependencies.

---

### User Story 2 - Execute Direct Inference on Verifiable Benchmarks (Priority: P2)

**User Journey**: The user runs the `SU-01` inference engine on a small, verifiable subset of the IMO/USAMO datasets (e.g., 1-2 problems) to confirm the model can generate output artifacts (text solutions) and that the verification pipeline (answer checking) executes successfully.

**Why this priority**: This proves the core "reasoning" capability exists and that the evaluation pipeline can ingest model outputs and produce a pass/fail result. It validates the "gold-medal" claim mechanism on a micro-scale.

**Independent Test**: The system runs `su01-eval/decode/direct_gen.py` against a 2-problem subset of `imo25.jsonl`, generates output files, and runs `eval_verifiable_answer.py` to produce a JSON result with a `score` or `pass` field.

**Acceptance Scenarios**:

1. **Given** a CPU-only environment with the `SU-01` code and a sample dataset of 2 problems, **When** `su01-eval/decode/direct_gen.py` is executed with a configuration to load a small checkpoint (or a dummy fallback if weights are missing), **Then** the script generates output text files (`.txt` or `.jsonl`) for each problem within 15 minutes.
2. **Given** the generated output files exist, **When** `su01-eval/verifiable_bench/answer_verifiable_bench/eval_verifiable_answer.py` is run against them, **Then** the script produces a summary JSON file containing at least one entry with a `status` field (e.g., "PASS", "FAIL", "TIMEOUT") and a `reason` string.
3. **Given** the inference run completes, **When** the logs are inspected, **Then** no errors related to missing CUDA devices, GPU memory allocation, or unsupported hardware accelerators appear.

---

### User Story 3 - Generate Reproduction Artifacts and Validation Report (Priority: P3)

**User Journey**: The user executes the full validation pipeline (or a representative subset) to produce the required artifacts (figures, logs, result summaries) and generates a `reproduction_report.md` that explicitly compares the observed behavior against the paper's claims.

**Why this priority**: This delivers the final deliverable of the project: a documented, evidence-backed confirmation (or refutation) of the paper's claims. It transforms raw execution into scientific validation.

**Independent Test**: The system produces a `reproduction_report.md` containing the execution logs, generated artifacts, and a structured summary stating whether the paper's claims (e.g., "stable reasoning on 100K tokens", "gold-medal performance") were observed, partially observed, or failed due to environmental constraints.

**Acceptance Scenarios**:

1. **Given** the successful execution of the inference and evaluation scripts, **When** the `run_mo_eval.sh` (or equivalent) pipeline completes, **Then** the output directory contains at least one figure (e.g., `tts_action_length_distribution_1.png`) and a `results.json` file with aggregated metrics.
2. **Given** the results exist, **When** the `reproduction_report.md` is generated, **Then** it includes a section explicitly stating the observed token length distribution and a section comparing the observed pass rates against the paper's reported "gold-medal" thresholds.
3. **Given** the report is generated, **When** the report is reviewed, **Then** it contains a clear "Verdict" field (e.g., "Reproduced", "Partially Reproduced", "Failed") with a justification citing specific log lines or metric values.

---

### Edge Cases

- **Missing Model Weights**: If the `SU-01` repository does not include the actual 30B model weights (common for large models), the system MUST gracefully degrade to a "validation of pipeline" mode, using a smaller placeholder model or skipping the inference step while still validating the code structure and evaluation logic.
- **Memory Overflow**: If the dataset or model configuration exceeds the 7GB RAM limit of the free-tier runner, the system MUST fail fast with a clear `MemoryError` and a recommendation to reduce batch size or sample size, rather than hanging or crashing silently.
- **Network Timeouts**: If the submodule fetch or dependency download times out, the system MUST retry up to 3 times with exponential backoff before failing the job.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST initialize the git submodule `external/SU-01` and verify the presence of the `su01-eval` and `su01-train-slime` directories before proceeding. (See US-1)
- **FR-002**: The system MUST install Python dependencies strictly in CPU-only mode, ensuring no CUDA/GPU-specific libraries (e.g., `torch` with CUDA support) are required or installed. (See US-1)
- **FR-003**: The system MUST execute the `direct_gen.py` script on a configurable subset of the `imo25.jsonl` or `usamo2026.jsonl` datasets to generate output artifacts. (See US-2)
- **FR-004**: The system MUST run the `eval_verifiable_answer.py` script to process generated outputs and produce a structured JSON result with pass/fail status. (See US-2)
- **FR-005**: The system MUST generate a `reproduction_report.md` containing the execution logs, observed metrics, and a comparative analysis against the paper's claims. (See US-3)
- **FR-006**: The system MUST detect and report if the model weights are missing, and if so, skip the inference step and log a warning instead of failing the entire pipeline. (See US-3)
- **FR-007**: The system MUST enforce a timeout of 30 minutes for any single script execution to prevent hanging on resource-constrained runners. (See US-2)

### Key Entities

- **Dataset**: The JSONL files (`imo25.jsonl`, `usamo2026.jsonl`) containing Olympiad problems and ground-truth answers.
- **Model**: The `SU-01` reasoning model (potentially a placeholder or smaller version if weights are missing).
- **Artifact**: The generated output files (text solutions, JSON results, figures) produced by the evaluation pipeline.
- **Report**: The `reproduction_report.md` summarizing the validation results.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The success rate of the pipeline (number of successfully executed scripts / total scripts) is measured against the requirement that all core scripts (submodule init, install, inference, eval, report) must complete without error. (See FR-001, FR-002, FR-003, FR-004, FR-005)
- **SC-002**: The presence of at least one valid artifact (e.g., `results.json` or a figure) is measured against the paper's claim of generating "real artifacts" for validation. (See FR-005, US-3)
- **SC-003**: The `reproduction_report.md` must contain a "Verdict" field with a value of "Reproduced", "Partially Reproduced", or "Failed", measured against the requirement for a clear conclusion. (See FR-005, US-3)
- **SC-004**: The execution time of the inference step (for the subset) is measured against the 30-minute timeout constraint to ensure feasibility on free-tier CI. (See FR-007, US-2)
- **SC-005**: The absence of CUDA/GPU errors in the logs is measured against the requirement for CPU-only compatibility. (See FR-002, US-1)

## Assumptions

- **Assumption about Model Weights**: The `SU-01` repository may not contain the full 30B model weights due to size constraints; the pipeline assumes it can run with a placeholder model or skip inference if weights are missing, focusing on pipeline validation.
- **Assumption about Dataset Availability**: The `imo25.jsonl` and `usamo2026.jsonl` files are present in the `su01-eval/unverifiable_bench/mo/metadata/` directory and contain valid JSONL data.
- **Assumption about Compute Resources**: The GitHub Actions free-tier runner (CPU, standard memory) is sufficient to run the evaluation scripts on a small subset (e.g., a few problems) of the dataset, but not the full dataset.
- **Assumption about Dependencies**: The `su01-train-slime` and `su01-eval` dependencies can be resolved to CPU-compatible versions without requiring proprietary or GPU-specific drivers.
- **Assumption about Paper Claims**: The paper's claims regarding "gold-medal-level performance" are based on specific benchmarks that can be approximated or validated on a small subset for the purpose of this reproduction project.
