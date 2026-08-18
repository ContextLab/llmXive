# Feature Specification: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the 'reverse-perplexity' curriculum used to instill self-checking behaviors in Olympiad-level models inadvertently encode rigid, domain-specific heuristics that degrade performance on open-ended, ill-structured scientific problems lacking verifiable ground-truth answers?"

## User Scenarios & Testing

### User Story 1 - Benchmark Ingestion and Model Inference (Priority: P1)

The researcher MUST be able to load the deterministic Olympiad datasets (IMO/IPhO) and the novel "OpenSci-Reason" dataset, then run the SU-01 model (and baseline) to generate responses on a CPU-only environment without requiring GPU acceleration or proprietary data access.

**Why this priority**: Without the ability to generate the raw data (model responses) on both datasets, no analysis can occur. This is the foundational data acquisition step that enables all subsequent evaluation.

**Independent Test**: The system can be tested by executing the inference pipeline on a sample of 10 prompts from each dataset and verifying that the output files (JSONL) contain valid text responses within the 6-hour CI time limit and 7GB RAM constraint.

**Acceptance Scenarios**:

1. **Given** the SU-01 model weights and the IMO/IPhO dataset are available, **When** the inference script runs with `batch_size=1` and `temperature=0.7` on a CPU-only runner, **Then** the system generates valid text responses for all prompts without OOM errors or CUDA dependency failures.
2. **Given** the OpenSci-Reason dataset (500 ill-structured prompts), **When** the system runs the inference, **Then** it generates exactly 3 candidate responses per prompt, stored in a structured format, completing within the 6-hour job limit.

---

### User Story 2 - Automated Expert Simulation and Scoring (Priority: P2)

The researcher MUST be able to score the generated responses on the OpenSci-Reason dataset using a frozen, small-scale LLM (e.g., Llama-3-8B) acting as a proxy for an expert panel, evaluating "Novelty," "Feasibility," and "Logical Consistency" on a 1-5 scale.

**Why this priority**: Human evaluation is too costly and slow for CI. A reproducible, automated scoring mechanism is required to quantify "creativity" and "rigidity" to test the hypothesis.

**Independent Test**: The system can be tested by running the scoring module on a pre-defined set of 5 "gold standard" responses with known expert scores and verifying that the proxy model's scores correlate >0.6 with the gold standard.

**Acceptance Scenarios**:

1. **Given** a set of model responses and a frozen scoring model, **When** the scoring pipeline executes, **Then** it assigns a numeric score (1-5) for Novelty, Feasibility, and Consistency to every response, storing the results in a traceable log.
2. **Given** a response that is logically consistent but unoriginal, **When** the scoring model evaluates it, **Then** it assigns a high Consistency score and a low Novelty score, distinguishing between the two dimensions.

---

### User Story 3 - Statistical Correlation and Rigidity Analysis (Priority: P3)

The researcher MUST be able to compute the Pearson correlation between Olympiad performance and OpenSci-Reason scores, and perform a paired t-test to determine if the SU-01 model exhibits significantly lower creativity scores compared to the baseline backbone.

**Why this priority**: This is the final analytical step that directly answers the research question regarding the trade-off between rigor and adaptability.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset with a known negative correlation and verifying that the script correctly reports a significant negative correlation coefficient (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the Olympiad scores and OpenSci-Reason scores for the SU-01 model, **When** the statistical analysis runs, **Then** it outputs a Pearson correlation coefficient and a p-value indicating the strength and significance of the relationship.
2. **Given** the mean creativity scores for SU-01 and the baseline model, **When** the paired t-test is performed, **Then** the system outputs the t-statistic and p-value to determine if the difference in adaptability is statistically significant.

---

### Edge Cases

- What happens when the "OpenSci-Reason" dataset contains prompts that are too ambiguous for the scoring model to evaluate (e.g., scoring all 1s or 5s)? The system MUST flag these as "low-confidence" and exclude them from the final correlation calculation.
- How does the system handle inference timeouts on the GitHub Actions free tier if a specific prompt generates an excessively long reasoning chain? The system MUST enforce a hard token limit (e.g., 2048 output tokens) and record the truncation as a "generation failure" rather than crashing.
- What if the frozen scoring model (Llama-3-8B) fails to fit in 7GB RAM due to OS overhead? The system MUST fallback to a smaller quantized model (e.g., Llama-3-8B-INT4) or a distilled 3B model, recording the model change in the assumptions log.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse the IMO/IPhO datasets and the curated "OpenSci-Reason" prompts (500 items) into a unified JSONL format for inference. (See US-1)
- **FR-002**: System MUST execute the SU-01 model and a baseline backbone on both datasets using CPU-only inference with `batch_size=1` and `temperature=0.7`, ensuring no CUDA dependencies. (See US-1)
- **FR-003**: System MUST generate exactly 3 distinct candidate responses per prompt for the OpenSci-Reason dataset using a temperature of 0.7. (See US-1)
- **FR-004**: System MUST utilize a frozen, small-scale LLM (e.g., Llama-3-8B or smaller) to score responses on Novelty, Feasibility, and Logical Consistency (1-5 scale) without fine-tuning. (See US-2)
- **FR-005**: System MUST compute the Pearson correlation coefficient between Olympiad scores and OpenSci-Reason scores, and perform a paired t-test comparing SU-01 vs. baseline creativity. (See US-3)
- **FR-006**: System MUST enforce a maximum output token limit of 2048 tokens per generation to prevent CI job timeouts on the free tier. (See US-1)
- **FR-007**: System MUST record all generation failures, truncations, and scoring ambiguities in a separate audit log for exclusion from statistical analysis. (See US-2)

### Key Entities

- **Prompt**: A text-based problem statement, either from a deterministic Olympiad source or an ill-structured scientific domain.
- **Response**: The text generated by the model in reaction to a Prompt, potentially containing reasoning steps and a final answer.
- **Score**: A tuple of three numeric values (Novelty, Feasibility, Consistency) assigned to a Response by the proxy expert model.
- **BenchmarkResult**: The aggregated performance metric (e.g., accuracy for Olympiad, mean creativity score for OpenSci-Reason) for a specific model on a specific dataset.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The correlation between Olympiad accuracy and OpenSci-Reason creativity is measured against the hypothesis of a negative relationship (See US-3).
- **SC-002**: The difference in mean creativity scores between the SU-01 model and the baseline backbone is measured against the null hypothesis of no difference using a paired t-test (See US-3).
- **SC-003**: The computational feasibility of the full pipeline is measured against the GitHub Actions free-tier constraints (≤6 hours, 7GB RAM, CPU-only) (See US-1).
- **SC-004**: The validity of the proxy scoring model is measured against a small set of manually verified "gold standard" responses to ensure correlation >0.6 (See US-2).
- **SC-005**: The robustness of the analysis is measured by the sensitivity of the correlation coefficient to the exclusion of low-confidence (ambiguous) prompts (See US-2).

## Assumptions

- The "OpenSci-Reason" dataset can be constructed entirely from text-only sources (NSF/ERC abstracts, open physics challenges) without requiring proprietary data or complex formatting.
- The frozen scoring model (e.g., Llama-3-8B) can run within the 7GB RAM limit on the GitHub Actions free tier using default 16-bit precision or INT4 quantization if necessary.
- The SU-01 model weights are available via HuggingFace or the original repository in a format compatible with `transformers` on CPU.
- The "reverse-perplexity" curriculum is the primary differentiator between the SU-01 model and the baseline backbone, with no other significant architectural changes.
- The proxy expert model (Llama-3-8B) is sufficiently calibrated to distinguish between "rigid" and "creative" responses without requiring domain-specific fine-tuning on scientific literature.
- The 500 prompts in the OpenSci-Reason dataset are representative enough of "ill-structured scientific problems" to yield statistically significant results with the available sample size.
