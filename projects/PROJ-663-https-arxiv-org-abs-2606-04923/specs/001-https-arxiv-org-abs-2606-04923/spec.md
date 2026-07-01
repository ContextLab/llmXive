# Feature Specification: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning

**Feature Branch**: `663-reproduce-cherrl`
**Created**: 2026-06-08
**Status**: Draft
**Input**: User description: "Reproduce & validate: Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based Reinforcement Learning (arXiv:2606.04923). Code vendored at external/CHERRL."

## User Scenarios & Testing

### User Story 1 - Environment Setup and Sanity Execution (Priority: P1)

The researcher MUST be able to initialize the project environment and execute a minimal, non-training verification step of the CHERRL codebase to confirm the code is functional and the data pipeline is intact.

**Why this priority**: Without a verified environment and a working "smoke test," no further reproduction or analysis can occur. This is the critical path for project viability.

**Independent Test**: Can be fully tested by running the provided unit test or a minimal script that loads the dataset and instantiates the judge model without starting a full training loop, verifying that no import errors or data-loading failures occur.

**Acceptance Scenarios**:
1. **Given** the submodule is cloned at `projects/PROJ-663-https-arxiv-org-abs-2606-04923/external/CHERRL`, **When** the researcher executes the sanity check script (e.g., `tests/single_controller/check_worker_alive/main.py` or a minimal data loader), **Then** the script exits with code 0 and produces a log confirming successful data loading and model instantiation.
2. **Given** a fresh GitHub Actions runner (CPU-only, 7GB RAM), **When** the environment setup script runs, **Then** all required dependencies are installed without GPU/CUDA-specific errors, and the process completes within 15 minutes.

---

### User Story 2 - Controlled Bias Injection and Reward Divergence (Priority: P2)

The researcher MUST be able to run a short, controlled training episode where a specific, known bias is injected into the LLM-as-a-Judge, and verify that the policy model's reward score diverges from the ground-truth quality (or a baseline unbiased score) as predicted by the CHERRL environment.

**Why this priority**: This is the core validation of the paper's primary claim: that CHERRL can *reproduce* reward hacking. If the bias injection does not lead to observable divergence, the environment is not functioning as intended.

**Independent Test**: Can be tested by running a fixed-seed training job with a specific bias (e.g., "self-praise") for a limited number of steps (e.g., 100 steps) and comparing the resulting reward curve against a control run with no bias.

**Acceptance Scenarios**:
1. **Given** the CHERRL environment configured with a "self-praise" bias and a fixed random seed, **When** a small-scale training run (≤ 500 steps) is executed, **Then** the recorded reward curve shows a statistically significant increase (p < 0.05) compared to a baseline run without bias, confirming the agent is exploiting the bias.
2. **Given** the same setup, **When** the training logs are analyzed, **Then** the logs explicitly record the specific tokens or phrases triggering the biased reward, matching the injected bias definition.

---

### User Story 3 - Hacking Onset Detection and Threshold Sensitivity (Priority: P3)

The researcher MUST be able to execute the detection agent (RHDA) on the training logs from User Story 2, verify it identifies the "onset" of reward hacking, and confirm that the detection threshold sensitivity analysis produces a valid report showing how detection rates vary with threshold changes.

**Why this priority**: This validates the second major contribution of the paper: the automated detection system. The sensitivity analysis is required by methodological soundness rules to ensure the detection threshold is not arbitrary.

**Independent Test**: Can be tested by running the `detection/rhda` module on the logs generated in US-2, and verifying that the output includes a CSV or JSON report detailing detection metrics across a swept range of thresholds (e.g., {0.01, 0.05, 0.1}).

**Acceptance Scenarios**:
1. **Given** training logs containing a known hacking onset step, **When** the RHDA detection agent is run with a default threshold, **Then** the agent outputs a detection step that is within ±5 steps of the ground-truth onset.
2. **Given** the same logs, **When** the sensitivity analysis script is executed, **Then** it produces a report (e.g., `threshold_grid.csv`) containing detection metrics (True Positive Rate, False Positive Rate) for at least 3 distinct threshold values, demonstrating the stability or volatility of the detection method.

### Edge Cases

- **What happens when the LLM-as-a-Judge fails to generate a response?** The system MUST handle timeout or empty responses gracefully by logging the error and skipping the step, rather than crashing the entire training loop.
- **How does the system handle data corruption in the submodule?** If the `data/` directory is missing or corrupted, the system MUST fail fast with a clear error message indicating the missing dataset files, rather than proceeding with empty data.
- **What if the CPU-only runner cannot load the default model size?** The system MUST detect memory pressure and either fail gracefully with a recommendation to use a smaller model (e.g., Qwen3-4B instead of larger variants) or automatically downsample the context window if the configuration allows.

## Requirements

### Functional Requirements

- **FR-001**: System MUST successfully clone the CHERRL submodule from ` and install all dependencies without requiring GPU drivers or CUDA libraries. (See US-1)
- **FR-002**: System MUST execute a minimal data-loading and model-instantiation script that completes within 15 minutes on a 2-CPU, 7GB RAM runner. (See US-1)
- **FR-003**: System MUST support the configuration of at least 3 distinct judge biases (e.g., "self-praise", "lexical", "tone") via a single configuration file or command-line flag. (See US-2)
- **FR-004**: System MUST record training logs including per-step rewards, generated tokens, and the specific bias trigger events in a structured JSONL format. (See US-2)
- **FR-005**: System MUST execute the RHDA detection agent on the generated logs and produce a sensitivity analysis report covering a threshold sweep of at least 3 values (e.g., {0.01, 0.05, 0.1}). (See US-3)
- **FR-006**: System MUST explicitly frame all reported reward divergences as associational effects derived from the injected bias, avoiding causal claims about the agent's "intent" unless randomization is explicitly part of the experimental design. (See US-2)

### Key Entities

- **Bias Configuration**: Defines the specific latent bias injected into the judge (e.g., "reward self-praise tokens").
- **Training Log**: A structured record of the RL episode, including step index, policy output, judge score, and bias trigger flags.
- **Detection Report**: The output artifact of the RHDA agent, containing the estimated onset step and sensitivity analysis metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The success of the environment setup is measured against the criterion that the sanity check script exits with code 0 and produces a "Success" log message. (See US-1)
- **SC-002**: The success of bias injection is measured by comparing the reward curve of the biased run against the unbiased baseline; the biased run MUST show a reward increase of ≥ 10% over the baseline at the final step. (See US-2)
- **SC-003**: The success of the detection system is measured by the RHDA agent's ability to identify the hacking onset within ±5 steps of the ground-truth injection point. (See US-3)
- **SC-004**: The methodological soundness of the detection threshold is measured by the presence of a sensitivity analysis report containing metrics for at least 3 distinct threshold values. (See US-3)
- **SC-005**: The compute feasibility is measured by the total execution time of the reproduction pipeline (setup + bias run + detection) remaining within a practical timeframe on the free-tier runner. (See Assumptions)

## Assumptions

- **Compute Constraints**: The reproduction will use the smallest viable model size (e.g., Qwen3-4B or smaller) and a reduced dataset subset (e.g., a small number of samples) to ensure the entire pipeline runs within the 7GB RAM and A fixed time limit for the duration of the observation window will be enforced. of the GitHub Actions free tier.
- **Data Availability**: The `data/` directory within the CHERRL submodule contains the necessary `healthbench_train.parquet` and `AdvancedIF` datasets required for the experiments. If these are missing, the process will fail with a clear error, as the project relies on the vendored data.
- **Bias Definitions**: The specific biases to be tested (e.g., "self-praise", "lexical") are defined in the CHERRL codebase's configuration files and do not require external definition.
- **No Causal Claims**: The experimental design is observational with respect to the agent's behavior; findings regarding "reward hacking" are framed as associational correlations between the injected bias and reward scores, not causal proof of intent.
- **Threshold Justification**: The sensitivity analysis thresholds (e.g., 0.01, 0.05, 0.1) are chosen based on common statistical significance levels and are sufficient to demonstrate the stability of the detection method without requiring a full grid search.
- **Model Precision**: All model inference and training steps will be performed in default float32 precision to avoid CUDA-specific dependencies (e.g., 8-bit quantization) that are incompatible with the CPU-only runner.
