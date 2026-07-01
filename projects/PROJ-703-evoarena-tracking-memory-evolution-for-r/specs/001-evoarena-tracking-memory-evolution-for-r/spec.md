# Feature Specification: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

**Feature Branch**: `703-evoarena-tracking-memory-evolution-for-r`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments (arXiv:2606.13681). The code is vendored at external/EvoArena."

## User Scenarios & Testing

### User Story 1 - Execute Baseline and EvoMem Evaluation on TerminalBench-Evo (Priority: P1)

**Journey**: The researcher runs the vendored `EvoMem-TerminalBench-Evo` evaluation suite to execute the baseline agent (`terminus2_baseline`) and the EvoMem agent (`terminus2_evomem`) on a subset of the TerminalBench-Evo dataset. The system must successfully capture memory patches, execute the agent chains, and output raw result logs.

**Why this priority**: This is the core reproduction task. Without successfully running the evaluation loop and generating output artifacts, no validation against the paper's claims ([deferred] baseline, [deferred] gain) is possible. It establishes the baseline functionality of the vendored code.

**Independent Test**: Can be fully tested by executing the `launch_terminus2_baseline.sh` and `launch_terminus2_evomem.sh` scripts (or their Python equivalents) on a small subset (e.g., 5 chains) and verifying the existence of JSON result files in the output directory.

**Acceptance Scenarios**:

1. **Given** the `EvoMem-TerminalBench-Evo` environment is activated and the dataset is present, **When** the baseline evaluation script is run for 5 chains, **Then** a JSON log file containing completion status and task results is created for each chain without runtime errors.
2. **Given** the baseline logs are generated, **When** the EvoMem evaluation script is run for the same 5 chains, **Then** a JSON log file containing the memory patch history and task results is created, and the memory patch files are stored in the designated `patch_store` directory.

---

### User Story 2 - Execute PersonaMem-Evo Evaluation and Chain Accuracy Analysis (Priority: P2)

**Journey**: The researcher runs the `EvoMem-PersonaMem-Evo` evaluation scripts to test the agents on the PersonaMem-Evo dataset. The system must process chat history updates, apply the patch-based memory paradigm, and calculate chain-level accuracy.

**Why this priority**: This validates the second domain (social/preference) claimed in the paper. It verifies the `patch_store` and `memory_layer_patch.py` logic in a different context than the terminal domain, ensuring the "dynamic environment" handling is generalizable across the benchmark suite.

**Independent Test**: Can be fully tested by running `evaluate_persona_chain_acc.py` on a subset of the `chat_history_32k` data and verifying that the script outputs a summary accuracy metric and per-chain JSON results.

**Acceptance Scenarios**:

1. **Given** the `EvoMem-PersonaMem-Evo` environment is configured, **When** the evaluation script is executed on 3 persona chains, **Then** the script completes without crashing and produces a summary report file.
2. **Given** the summary report is generated, **When** the raw chain logs are inspected, **Then** each log contains the sequence of memory updates (patches) applied during the chain execution.

---

### User Story 3 - Generate Performance Comparison and Mechanistic Analysis Reports (Priority: P3)

**Journey**: The researcher aggregates the raw logs from the Terminal and Persona evaluations to compute aggregate accuracy metrics (average accuracy, chain-level accuracy) and compares them against the paper's reported figures. The system must also generate a simple mechanism analysis report (e.g., evidence capture count) if the code supports it.

**Why this priority**: This fulfills the "validate" part of the task. It transforms raw execution data into the specific metrics mentioned in the abstract ([deferred] baseline, [deferred] gain, [deferred] chain-level gain) to confirm or refute the paper's claims.

**Independent Test**: Can be fully tested by running a post-processing script (or manual aggregation) on the generated JSON logs to produce a CSV or JSON summary table comparing Baseline vs. EvoMem accuracy.

**Acceptance Scenarios**:

1. **Given** the raw result logs from both Terminal and Persona evaluations, **When** the aggregation script is run, **Then** it outputs a summary table with average accuracy and chain-level accuracy for both Baseline and EvoMem configurations.
2. **Given** the summary table is generated, **When** the values are compared to the paper's abstract, **Then** the system flags if the reproduced values deviate by more than 5% from the reported values (triggering a manual review).

---

### Edge Cases

- **API Rate Limiting**: If the evaluation relies on external LLM APIs (e.g., via the `.env` configuration), the system must handle rate limits gracefully (e.g., exponential backoff) rather than crashing the entire batch run.
- **Missing Data Files**: If a specific chain ID in the dataset is missing or corrupted, the system must log the error and skip that specific chain without halting the entire evaluation suite.
- **Memory Overflow**: If a specific chain generates an excessively large memory patch history, the system must enforce a hard limit on patch size or history depth to prevent OOM errors on the CI runner.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `EvoMem-TerminalBench-Evo` evaluation scripts to run both baseline and EvoMem agents on the vendored dataset, producing raw JSON result logs for each chain (See US-1).
- **FR-002**: The system MUST execute the `EvoMem-PersonaMem-Evo` evaluation scripts to process chat history updates and generate chain-level accuracy results for the PersonaMem domain (See US-2).
- **FR-003**: The system MUST capture and store memory evolution patches (structured update histories) during agent execution to enable mechanistic analysis (See US-2).
- **FR-004**: The system MUST aggregate raw execution logs from both domains to compute average accuracy and chain-level accuracy metrics for Baseline vs. EvoMem configurations (See US-3).
- **FR-005**: The system MUST validate that all execution artifacts (JSON logs, patch files) are non-empty and contain valid JSON structure before considering the run successful (See US-1).

### Key Entities

- **Evaluation Run**: A single execution of an agent on a specific chain of tasks, resulting in a JSON log containing task outcomes and memory state.
- **Memory Patch**: A structured update record capturing the evolution of the agent's memory (e.g., new facts, corrected beliefs) generated during a task.
- **Chain Accuracy**: A boolean metric indicating whether an agent successfully completed a consecutive sequence of related subtasks within a specific chain.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The reproduction success rate is measured against the paper's reported average accuracy (baseline) and improvement ([deferred] gain) to determine if the code validates the claims (See FR-004).
- **SC-002**: The chain-level accuracy improvement is measured against the paper's reported gain on EvoArena to validate the effectiveness of the memory paradigm (See FR-004).
- **SC-003**: The artifact integrity is measured against the requirement that [deferred] of executed chains produce valid JSON logs and corresponding patch files (See FR-005).
- **SC-004**: The mechanistic analysis validity is measured by the presence of evidence capture metrics in the memory logs, confirming the claim of "better preservation of complete evolving environment states" (See FR-003).

## Assumptions

- The vendored code in `external/EvoArena` is functional and does not require code modifications to run, only environment configuration (e.g., API keys in `.env`).
- The evaluation scripts are designed to run on CPU-only environments; if the code internally attempts to load large models requiring GPU, the assumption is that the code will be run with a CPU-compatible model configuration or a small sampled subset of the dataset to fit the 7GB RAM constraint.
- The dataset files (e.g., `chat_history_32k`, TerminalBench-Evo chains) are fully present in the submodule and do not require external downloads during the CI run.
- API calls to external LLM providers (if used) are either mocked for local testing or use a provided key with sufficient quota for a small-scale reproduction run (e.g., 10-20 chains total).
- The "mechanistic analysis" mentioned in the paper (evidence capture) is implemented as a logging feature in the provided code and does not require a separate complex analysis pipeline to extract.
- The evaluation time for a small subset of chains (e.g., 10 total) will complete within the 6-hour CI limit on a CPU-only runner.
