# Feature Specification: llmXive Follow-up: Extending "Improved Large Language Diffusion Models"

**Feature Branch**: `001-llmxive-overfitting-trajectory`  
**Created**: 2026-08-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Improved Large Language Diffusion Models'"

## User Scenarios & Testing

### User Story 1 - Construct and Validate the Micro-Corpus (Priority: P1)

**User Journey**: The researcher prepares a constrained, balanced dataset of a substantial number of tokens from open-source sources (e.g., Project Gutenberg, The Stack) using the `gpt` tokenizer and verifies that the data fits within the resource constraints of the free-tier CI runner before any model training begins.

**Why this priority**: Without a valid, size-constrained dataset, the comparative analysis cannot run. This is the foundational data requirement that enables the subsequent training loops.

**Independent Test**: The system can be tested by successfully loading the constructed Micro-Corpus into memory on a standard CPU runner, verifying the token count is ≥ 10,000,000 and ≤ 10,100,000, and confirming the total disk footprint is <14GB.

**Acceptance Scenarios**:

1. **Given** a raw collection of text files from Project Gutenberg and The Stack, **When** the data curation script filters and concatenates them using the `gpt2` tokenizer, **Then** the resulting dataset contains between 10M and 10.1M tokens and is stored in a format loadable within 7GB RAM.
2. **Given** the constructed Micro-Corpus, **When** a held-out test set is split from it, **Then** the training set and test set share no overlapping text sequences.

---

### User Story 2 - Execute Comparative Training Loops (Priority: P2)

**User Journey**: The researcher trains two M-parameter models (one causal autoregressive, one bidirectional masked diffusion) on the Micro-Corpus for a sufficient number of epochs using a CPU-optimized loop, recording validation loss and training loss after every epoch.

**Why this priority**: This is the core experimental procedure. It generates the raw data (loss curves) required to answer the research question about overfitting trajectories.

**Independent Test**: The system can be tested by running a single epoch of training for both models on the Micro-Corpus, verifying that the training completes without OOM errors, and that validation and training loss metrics are logged for both models.

**Acceptance Scenarios**:

1. **Given** the Micro-Corpus and two initialized model architectures, **When** the training loop executes for a sufficient number of epochs to ensure model convergence, **Then** both models complete the full training schedule within the wall-clock time limit of the CI runner.
2. **Given** the training process, **When** the validation set is evaluated after each epoch, **Then** the system logs the perplexity and training loss for both the autoregressive and diffusion models for every epoch throughout the training process.

---

### User Story 3 - Analyze Overfitting Trajectories (Priority: P3)

**User Journey**: The researcher performs statistical analysis (Repeated-Measures ANOVA on the Generalization Gap) on the logged loss curves to determine if the diffusion model exhibits a significantly slower widening of the generalization gap compared to the autoregressive baseline, and validates this against benchmark performance.

**Why this priority**: This step transforms raw metrics into scientific findings, directly addressing the research question regarding the "overfitting-as-a-feature" phenomenon with a methodologically sound metric.

**Independent Test**: The system can be tested by feeding the logged loss curves into the analysis script and verifying that a statistical interaction term (model type × epoch) is calculated on the generalization gap, and a correlation with benchmark performance is reported.

**Acceptance Scenarios**:

1. **Given** the epoch-by-epoch training and validation loss logs for both models, **When** the statistical analysis script runs, **Then** it outputs a p-value for the interaction effect between model architecture and epoch count on the generalization gap.
2. **Given** the analysis results, **When** the system generates the final report, **Then** it explicitly states whether the diffusion model's generalization gap widening is statistically slower than the autoregressive model's and correlates with benchmark performance.

---

### Edge Cases

- **What happens when the Micro-Corpus construction fails to reach the 10M token lower bound?** The system must fail the test and halt, as the data regime is insufficient.
- **What happens when the Micro-Corpus construction exceeds 10.1M tokens?** The system must log a warning and truncate the dataset to a controlled token limit to maintain the controlled regime, recording the truncation in metadata.
- **How does the system handle a training run that exceeds a substantial duration?** The CI job must fail gracefully, logging the epoch at which the timeout occurred to distinguish between a methodological failure and a resource constraint violation.
- **What if the generalization gap curves are identical?** The statistical test must correctly report a non-significant interaction, and the final output must reflect the null hypothesis (no difference in overfitting trajectories).

## Requirements

### Functional Requirements

- **FR-001**: System MUST construct a "Micro-Corpus" of between [deferred] and [deferred] tokens using the Hugging Face `gpt2` tokenizer (v4.0) from open-source datasets, ensuring a balanced mix of logical and code-heavy text, to serve as the training data for both models (See US-1).
- **FR-002**: System MUST implement two large-scale models

The research question remains: What is the impact of model scale on performance?
The method remains: Comparative analysis using controlled experiments.
References: Smith et al. (2023); arXiv:2301.12345. with identical embedding dimensions and attention heads: one standard causal autoregressive transformer and one bidirectional masked diffusion model, to isolate architectural differences (See US-2).
- **FR-003**: System MUST execute a repeated-epoch training loop for a sufficient number of epochs to ensure model convergence. on the Micro-Corpus for both models using a CPU-optimized loop (e.g., `torch.compile` on CPU) with identical batch sizes and learning rate schedules (See US-2).
- **FR-004**: System MUST record and log validation loss (perplexity), training loss, and accuracy on a held-out test set after every single epoch to explicitly map the overfitting trajectory (See US-2).
- **FR-005**: System MUST perform a repeated-measures ANOVA on the Generalization Gap (Training Loss - Validation Loss) curves across epochs to test for a significant interaction between model type and epoch count (See US-3).
- **FR-006**: System MUST evaluate final checkpoint performance on the HumanEval (full suite) benchmark, explicitly verifying that the benchmark data is excluded from the Micro-Corpus to ensure external validity (See US-3).
- **FR-007**: System MUST log CPU RAM usage, disk usage, and wall-clock time per epoch to verify feasibility within the RAM and disk constraints (See US-2).
- **FR-008**: System MUST calculate the Generalization Gap (Training Loss - Validation Loss) at every epoch and use this metric as the primary dependent variable for the overfitting trajectory analysis (See US-3).
- **FR-009**: System MUST perform an a priori power analysis to confirm the 10M token / 100 epoch regime provides statistical power ≥ 0.8 for detecting the expected interaction effect (See US-3).
- **FR-010**: System MUST calculate the Pearson correlation coefficient between the slope of the Generalization Gap and the final HumanEval score to validate the link between overfitting resistance and generalization (See US-3).

### Key Entities

- **Micro-Corpus**: A curated dataset of between 10M and 10.1M tokens derived from open-source text using the `gpt2` tokenizer, split into training and held-out test sets.
- **Model Configuration**: The hyperparameters and architecture definitions for the two M-parameter models (diffusion and autoregressive).
- **Training Log**: A time-series record of training loss, validation loss, generalization gap, and resource usage metrics for every epoch of training.
- **Statistical Result**: The output of the ANOVA test on the generalization gap, including interaction p-values and effect sizes.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in generalization gap widening rates between the diffusion and autoregressive models is measured against the null hypothesis of no interaction (See FR-005).
- **SC-002**: The final perplexity of the diffusion model on the HumanEval benchmark is measured against the final perplexity of the autoregressive model, and the correlation with the generalization gap slope is measured against a threshold of |r| ≥ 0.5 (See FR-006, FR-010).
- **SC-003**: The total wall-clock time for the multi-epoch training loop is measured against the CI runner time limit (See FR-007).
- **SC-004**: The peak RAM usage during training is measured against the CI runner limit. (See FR-007).
- **SC-005**: The statistical significance of the overfitting trajectory divergence is measured against a standard alpha level. (See FR-005).
- **SC-006**: The peak disk usage during training is measured against the CI runner limit. (See FR-007).

## Assumptions

- The open-source datasets selected (Project Gutenberg, The Stack) contain sufficient variety to construct a balanced M token corpus without introducing severe domain bias that would invalidate the "general language" premise.
- The "overfitting-as-a-feature" phenomenon, if it exists, will manifest within the -epoch training window on a M token dataset; if the effect requires more data or epochs to emerge, the study will yield a null result (no divergence) rather than a false positive.
- The `torch.compile` optimization on CPU provides sufficient speedup to complete epochs of training for two large-parameter models within a fixed time limit; if not, the study will be constrained by the available time, potentially truncating the epoch count.
- The HumanEval benchmark suite is sufficiently distinct from the Micro-Corpus to serve as a valid out-of-distribution test, ensuring the measured performance is not an artifact of data leakage, as verified by FR-006.
- The model size is small enough to fit entirely within the GB RAM limit of the free-tier CI runner when using default precision (FP/FP16) without requiring quantization or model parallelism.
- The 10M token / 100 epoch regime provides sufficient statistical power (≥ 0.8) to detect the expected interaction effect, as justified by the a priori power analysis mandated in FR-009.