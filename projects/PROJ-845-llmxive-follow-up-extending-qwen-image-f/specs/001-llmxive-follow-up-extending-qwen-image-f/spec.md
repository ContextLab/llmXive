# Feature Specification: llmXive follow-up: extending "Qwen-Image-Flash: Beyond Objective Design"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-Image-Flash: Beyond Objective Design'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthetic Dataset Generation with Controlled Entropy (Priority: P1)

The system MUST generate a synthetic logical reasoning dataset of sufficient scale, strictly partitioned into three distinct training subsets: High-Entropy (randomized premises/operators), Low-Entropy (structured/repetitive patterns), and Target-Specific (narrow reasoning styles). This dataset serves as the foundational predictor variable for the entire study.

**Why this priority**: Without a rigorously controlled dataset where entropy is the only manipulated variable, the subsequent distillation and evaluation phases cannot isolate the effect of data coherence. This is the primary input required to answer the research question.

**Independent Test**: Can be fully tested by running the generator script and verifying the statistical properties (e.g., entropy scores, pattern repetition rates) of the three generated subsets against the definitions, without needing to train any models.

**Acceptance Scenarios**:

1. **Given** the rule-based generator is configured with the target counts ([deferred] total, split 1:1:1), **When** the generation script executes, **Then** the output must contain [deferred] propositional logic and arithmetic word problems, with metadata flags clearly distinguishing the High, Low, and Target-Specific subsets.
2. **Given** the High-Entropy subset, **When** a statistical analysis of premise order and operator diversity is performed, **Then** the calculated entropy score must be significantly higher (p < 0.05 via t-test) than that of the Low-Entropy subset.
3. **Given** the generated test set, **When** compared against the training sets, **Then** the test set must contain 500 problems with distinct logical structures not present in any training subset to ensure independence.

---

### User Story 2 - CPU-Tractable Distillation Pipeline (Priority: P2)

The system MUST execute a few-step distillation process where a small student model (<100M parameters) learns from a teacher model's 10-step chain-of-thought traces, minimizing KL-divergence, strictly constrained to run on a CPU-only environment (2 cores, 7GB RAM) without GPU acceleration or heavy quantization libraries.

**Why this priority**: The research question specifically investigates efficiency on resource-constrained hardware. If the pipeline requires GPU or exceeds the 6-hour runtime, the "edge device" applicability claim fails, and the experiment cannot be reproduced in the target environment.

**Independent Test**: Can be fully tested by running the training loop for a fixed number of epochs on a single dataset subset and verifying the resource usage (RAM < 7GB, no CUDA errors) and completion time ( < 2 hours per subset) without evaluating the final model accuracy.

**Acceptance Scenarios**:

1. **Given** the student model is initialized with <100M parameters, **When** the distillation training loop starts on a CPU runner, **Then** the process must complete without raising "CUDA out of memory" or "bitsandbytes" dependency errors, and peak RAM usage must remain below 7GB.
2. **Given** the teacher model generates 10-step traces, **When** the student model (limited to 2-3 steps) trains, **Then** the loss function (KL-divergence) must be computed and minimized at every epoch without requiring mixed-precision (FP16/FP32) GPU-specific optimizations.
3. **Given** the full pipeline (generation + 3 training runs + evaluation), **When** executed on a standard GitHub Actions free-tier runner, **Then** the total wall-clock time must be less than 6 hours.

---

### User Story 3 - Statistical Validation of Coherence Hypothesis (Priority: P3)

The system MUST evaluate the three student models on the held-out diverse test set and perform statistical analysis (ANOVA on accuracy, t-test on convergence epochs) to determine if the Low-Entropy model significantly outperforms the High-Entropy and Target-Specific models.

**Why this priority**: This step transforms raw model outputs into scientific evidence. It directly addresses the research question by quantifying the "influence" of entropy on sample efficiency and generalization, providing the binary outcome (support/refute) for the hypothesis.

**Independent Test**: Can be fully tested by taking the final accuracy logs and convergence epoch counts from the three training runs and running the statistical analysis script to verify the generation of p-values and effect sizes, independent of the training process itself.

**Acceptance Scenarios**:

1. **Given** the final accuracy scores for the three student variants, **When** an ANOVA test is performed, **Then** the output must include an F-statistic and a p-value indicating whether there is a statistically significant difference (p < 0.05) between the groups.
2. **Given** the convergence epochs for each variant, **When** pairwise t-tests are performed, **Then** the output must explicitly state whether the Low-Entropy model converged in significantly fewer steps than the High-Entropy model.
3. **Given** the statistical results, **When** the final report is generated, **Then** it must clearly label the findings as "associational" (observational) rather than causal, acknowledging the lack of random assignment in the data generation process.

### Edge Cases

- What happens if the synthetic generator produces logical contradictions (unsolvable problems) in the Low-Entropy set? The system must detect and filter these out during generation to ensure the teacher model can generate valid traces.
- How does the system handle a scenario where the CPU runner hits the 6-hour timeout before all three distillations complete? The pipeline must fail fast with a specific error code rather than silently truncating results, ensuring the "feasibility" claim is not falsely validated.
- What if the student model fails to converge (loss plateaus at a high value) for the High-Entropy set? The system must log this as a "non-convergence" event and include it in the statistical analysis (e.g., treating it as a worst-case epoch count) rather than excluding it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a synthetic dataset of 5,000 logical problems partitioned into High-Entropy, Low-Entropy, and Target-Specific subsets with verified statistical differences in entropy metrics (See US-1).
- **FR-002**: System MUST initialize a teacher model to generate 10-step chain-of-thought traces and a student model (<100M parameters) to generate 2-3 step traces for distillation (See US-2).
- **FR-003**: System MUST execute the distillation training loop using KL-divergence minimization strictly on CPU hardware without requiring CUDA, GPU, or 8-bit/4-bit quantization libraries (See US-2).
- **FR-004**: System MUST evaluate all three student models on a held-out test set of 500 diverse logic problems distinct from the training distribution (See US-3).
- **FR-005**: System MUST perform an ANOVA test on final accuracy scores and pairwise t-tests on convergence epochs to determine statistical significance of the observed differences (See US-3).
- **FR-006**: System MUST explicitly frame all statistical findings as associational rather than causal in the final output report, given the observational nature of the data generation (See US-3).
- **FR-007**: System MUST implement a multiple-comparison correction (e.g., Bonferroni) if >1 hypothesis test is conducted to control family-wise error rate (See US-3).

### Key Entities

- **SyntheticProblem**: A logical reasoning instance containing premises, operators, and a ground-truth solution, tagged with an entropy level (High/Low/Target).
- **DistillationRun**: A record of a training session containing the dataset subset used, the student model parameters, the loss curve, convergence epoch, and final test accuracy.
- **StatisticalResult**: A structured output containing the test statistic (F-value, t-value), p-value, and a binary conclusion regarding the "coherence over diversity" hypothesis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in convergence speed (epochs) between the Low-Entropy and High-Entropy student models is measured against the null hypothesis of no difference (See FR-005).
- **SC-002**: The final accuracy of the Low-Entropy student model is measured against the final accuracy of the High-Entropy and Target-Specific models on the held-out test set (See FR-004).
- **SC-003**: The total compute time of the full pipeline is measured against the 6-hour limit of the free-tier CPU runner (See FR-003).
- **SC-004**: The peak RAM usage during training is measured against the 7GB limit of the target environment (See FR-003).
- **SC-005**: The statistical validity of the findings is measured against the requirement for multiple-comparison correction and associational framing (See FR-006, FR-007).

## Assumptions

- The rule-based generator can synthesize valid propositional logic and arithmetic problems with strictly controlled entropy levels without introducing unintended logical biases.
- A small transformer model (<100M parameters) or a lightweight rule-based predictor is sufficient to demonstrate the "few-step distillation" phenomenon on logical tasks.
- The "coherence over diversity" principle, if it exists, will manifest within the first 5,000 synthetic samples; larger sample sizes are not required to detect the effect.
- The GitHub Actions free-tier runner (2 cores, 7GB RAM) will consistently provide sufficient CPU performance to complete the 6-hour window without thermal throttling or resource contention.
- The teacher model (LLM) can be configured to generate consistent 10-step traces without hallucinating invalid logical steps, which would corrupt the distillation target.
- The statistical power of the ANOVA/t-tests with N=500 test samples is sufficient to detect the expected effect size; if not, the study will report a "lack of power" rather than a definitive null result.
