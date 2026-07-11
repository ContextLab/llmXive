# Feature Specification: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

**Feature Branch**: `001-llmxive-appo-static-branching`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'APPO: Agentic Procedural Policy Optimization'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Static Branching Scores (Priority: P1)

The researcher needs to compute a "Static Branching Score" for every decision point in a sampled subset of the GSM8K and MATH datasets using a frozen pre-trained model (e.g., Phi-2 or Llama-3-8B) via CPU-only inference, without any online policy rollouts.

**Why this priority**: This is the core experimental variable. Without the static scores, the primary research question (correlation between static and dynamic scores) cannot be addressed. It establishes the baseline "structural" hypothesis. The study hypothesizes that high structural confidence (KL divergence) is a *necessary but not sufficient* predictor of high procedural value (APPO reward), and this metric validates that empirical link.

**Independent Test**: The system can be fully tested by loading a small batch of tasks, running the static inference pass, and verifying that a score vector is generated for each task without triggering any training loops or GPU operations.

**Acceptance Scenarios**:

1. **Given** a JSON file containing 10 GSM8K reasoning traces, **When** the system runs the static scoring module on a CPU-only environment, **Then** it outputs a JSON file mapping each token position to a Kullback-Leibler (KL) divergence score relative to a uniform top-k distribution.
2. **Given** a model loaded in default precision (float32/float16) on a CPU, **When** the system processes a trace with >500 tokens, **Then** it completes the scoring within 5 minutes per task and does not attempt to allocate CUDA memory. Note: "default precision" permits necessary numerical stabilization (e.g., probability clamping to 1e-9) to ensure stability.
3. **Given** a trace where the model's next-token probability distribution is uniform across all tokens, **When** the system calculates the divergence, **Then** it outputs a score of approximately 0.0 (or the defined minimum threshold).

---

### User Story 2 - Generate Dynamic APPO Branching Scores (Priority: P2)

The researcher needs to generate "Dynamic Branching Scores" for a matching subset of 500 tasks from the GSM8K and MATH datasets using the APPO algorithm with online rollouts, to serve as the ground truth for comparison.

**Why this priority**: This provides the "future-aware" dynamic variable. While the static score is the innovation, the dynamic score is the necessary reference point to validate the hypothesis. It is P2 because the static score can be computed independently, but the correlation analysis requires both.

**Independent Test**: The system can be tested by running the APPO rollout module on a fixed set of 5 tasks, verifying that the "future-aware likelihood gains" are calculated based on actual policy interactions and stored alongside the task ID.

**Acceptance Scenarios**:

1. **Given** a subset of 500 tasks from the MATH dataset selected via stratified random sampling by problem difficulty, **When** the APPO module executes online rollouts, **Then** it records a dynamic branching score for each decision point based on the observed policy likelihood gains.
2. **Given** a task where the policy fails to find a solution during rollouts, **When** the system calculates the dynamic score, **Then** it records a score reflecting the negative likelihood gain or failure state, distinct from the static score.
3. **Given** the dynamic scoring process, **When** it completes for the full subset, **Then** the output dataset contains aligned task IDs and decision points matching the static score dataset structure.
4. **Note on Reward Function**: The APPO reward function is explicitly defined as binary correctness of the final answer.

---

### User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

The researcher needs to align the static and dynamic score sequences by token position and task ID, compute Pearson and Spearman correlation coefficients, and perform a permutation test with a sufficient number of iterations to determine statistical significance.

**Why this priority**: This synthesizes the data to answer the research question. It is P3 because it depends on the successful completion of US-1 and US-2.

**Independent Test**: The system can be tested by feeding two dummy datasets with a known perfect correlation (r=1.0) and verifying that the output reports r≈1.0 and a p-value < 0.05.

**Acceptance Scenarios**:

1. **Given** two aligned datasets of static and dynamic scores, **When** the analysis module runs, **Then** it outputs the Pearson correlation coefficient, Spearman rank correlation, and the p-value from the permutation test.
2. **Given** a correlation coefficient of < 0.3, **When** the system generates the error analysis report, **Then** it visualizes the residuals to identify specific reasoning patterns (e.g., multi-step algebra vs. arithmetic) where the static approximation deviates most.
3. **Given** the permutation test results, **When** the p-value is > 0.05, **Then** the system flags the result as "not statistically significant" and outputs a summary stating that the static approximation is indistinguishable from random chance.
4. **Note on Repetition**: The correlation analysis MUST be executed three times (n=3) with different random seeds to ensure result stability.

---

### Edge Cases

- **What happens when** the frozen model fails to generate a valid next-token distribution (e.g., all probabilities are 0 due to numerical instability)? -> The system MUST clamp probabilities to a minimum floor (e.g., 1e-9) before calculating KL divergence to prevent NaN errors.
- **How does the system handle** tasks where the static and dynamic traces diverge significantly in length or tokenization? -> The system MUST truncate the longer trace to the length of the shorter one for alignment, or exclude the task from the correlation calculation if the overlap is < 80%.
- **What happens when** the permutation test takes longer than the 6-hour CI limit? -> The system MUST implement a progress bar and a hard timeout at a predefined duration. If the timeout triggers before n=3 runs complete, the system MUST report the actual calculated p-value from completed runs but flag the result as "inconclusive due to time truncation" rather than forcing a "fail to reject" outcome.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST compute the Static Branching Score as the Kullback-Leibler divergence between the model's actual next-token distribution and a uniform distribution over the top-k most probable alternatives for every token in the reasoning trace (See US-1).
- **FR-002**: The system MUST run all inference passes using a frozen pre-trained model (e.g., Phi or Llama-3-8B) in default precision on CPU-only hardware, explicitly avoiding CUDA, 8-bit quantization, or mixed-precision GPU training. Note: "default precision" permits necessary numerical stabilization (e.g., probability clamping to 1e-9) to ensure stability (See US-1).
- **FR-003**: The system MUST generate Dynamic Branching Scores by executing the APPO algorithm with online rollouts on a random subset of 500 tasks from GSM8K and MATH, recording future-aware likelihood gains (See US-2).
- **FR-004**: The system MUST align static and dynamic score sequences by task ID and token position, handling length mismatches by truncation or exclusion (See US-3).
- **FR-005**: The system MUST perform a permutation test targeting a sufficient number of iterations, with a hard timeout of a pre-specified duration. The test MUST run three times with different random seeds (n=3). The test MUST stop early if the p-value stabilizes (change < 0.001 iterations) or if the timeout triggers. If the timeout triggers, the system MUST report the actual calculated p-value but flag the result as "inconclusive" (See US-3).
- **FR-006**: The system MUST output a residual analysis report visualizing where static scores deviate from dynamic scores, categorized by reasoning pattern (e.g., arithmetic vs. algebra). The categorization MUST be performed by a pre-trained, domain-specific classifier model (e.g., fine-tuned BERT on GSM8K labels) to ensure verifiable ground truth (See US-3).

### Key Entities

- **Reasoning Trace**: A sequence of tokens representing a solution path for a math problem, containing the static score vector and the dynamic score vector.
- **Branching Score**: A numeric value representing the "decision value" at a specific token position, derived either statically (KL divergence) or dynamically (APPO likelihood gain).
- **Correlation Result**: A dataset containing the Pearson coefficient, Spearman coefficient, and p-value derived from the alignment of static and dynamic scores.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation coefficient (Pearson and Spearman) between static and dynamic scores is measured against the null hypothesis of zero correlation (r=0) using the permutation test p-value (See US-3).
- **SC-002**: The computational feasibility of the static score generation is measured against the constraint of running on a GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, no GPU) within 6 hours for the full dataset, AND producing a valid correlation result (non-NaN, non-timeout) (See US-1).
- **SC-003**: The statistical significance of the observed correlation is measured against the threshold of p < 0.05 to determine if the static approximation is distinguishable from random noise (See US-3).
- **SC-004**: The accuracy of the static approximation is measured against the magnitude of the residuals in the error analysis report to identify specific reasoning patterns where the static model fails (See US-3).
- **SC-005**: The robustness of the results is measured by repeating the permutation test with different random seeds (n=3) to ensure the p-value is stable (See US-3).

## Assumptions

- **Assumption about data availability**: The GSMK and MATH datasets are fully accessible via HuggingFace Datasets and contain sufficient reasoning traces for the 500-task subset without requiring additional preprocessing beyond standard tokenization.
- **Assumption about model behavior**: The frozen pre-trained models (Phi-2 or Llama-3-8B) will not crash or hang when running inference on a CPU-only environment with default precision, and their tokenizers are compatible with the dataset formatting.
- **Assumption about computational limits**: A sufficient iteration permutation test can complete within the 6-hour CI time limit on a 2-core runner; if not, the system will fall back to a partial test or early stopping as defined in the edge cases.
- **Assumption about variable fit**: The GSM8K and MATH datasets contain the necessary token-level information to compute "next-token distributions" and "reasoning traces" as required by the methodology; no external variables (e.g., user demographics) are needed.
- **Assumption about inference framing**: The correlation between static and dynamic scores is interpreted as an associational relationship; the study does not claim that static scores *cause* dynamic performance, only that they predict it.
- **Assumption about collinearity**: The static and dynamic scores are derived from the same underlying model architecture (or a fine-tuned version thereof). The dynamic APPO run uses a *fine-tuned* policy. The study interprets the correlation as "initial structural confidence predicting final policy value," acknowledging the training process as a confounding variable.