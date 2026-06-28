# Feature Specification: AgentDoG 1.5 Training Data Ablation Study

**Feature Branch**: `251-agentdog-1-5-training-data-ablation`  
**Created**: 2026-06-04  
**Status**: Draft  
**Input**: User description: "How does training data size affect the adversarial robustness of lightweight guardrail models against prompt-injection attacks on autonomous agents?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Subsetting and Model Fine-tuning (Priority: P1)

The research system MUST extract configurable-size subsets (across varying scales) from the AgentDoG safety corpus and fine-tune a base model on each subset with identical hyperparameters across multiple random seeds.

**Why this priority**: This is the core experimental setup. Without reproducible data subsetting and consistent fine-tuning, no valid comparison of robustness across data sizes is possible. All downstream measurements depend on this foundation.

**Independent Test**: Can be fully tested by verifying that three distinct model checkpoints are produced from three distinct data subsets, each trained with logged hyperparameters and seed values, and that the subset sizes match the target counts within ±1 sample.

**Acceptance Scenarios**:

1. **Given** a full AgentDoG safety corpus of ≥100k samples, **When** the system extracts a 1k-sample subset, **Then** the resulting training file contains exactly 1000 samples with deterministic ordering based on the seed.
2. **Given** three training jobs for 1k, 10k, and 100k subsets, **When** each completes fine-tuning, **Then** all three checkpoints are stored with metadata recording their subset size, seed, and hyperparameter configuration.
3. **Given** the same seed and hyperparameters, **When** two independent training runs execute, **Then** they produce identical model checkpoints (byte-for-byte comparison).

---

### User Story 2 - Adversarial Robustness Evaluation (Priority: P2)

The research system MUST evaluate each fine-tuned model on held-out adversarial test sets from ATBench and R-Judge using standardized prompt-injection attack templates, computing robustness metrics (success rate, false-positive rate) with confidence intervals.

**Why this priority**: This directly measures the dependent variable (robustness). Without standardized adversarial evaluation, the relationship between data size and robustness cannot be quantified or compared.

**Independent Test**: Can be fully tested by running evaluation on one model checkpoint and verifying that the output includes robustness metrics computed across ≥3 independent seeds, with confidence intervals calculated using t-distribution.

**Acceptance Scenarios**:

1. **Given** a fine-tuned guardrail model checkpoint, **When** it is evaluated on the ATBench prompt-injection test set, **Then** the system outputs a robustness score (percentage of attacks successfully blocked) with ± standard deviation across seeds.
2. **Given** the same model evaluated on both ATBench and R-Judge, **When** results are aggregated, **Then** the system reports per-benchmark scores and a weighted aggregate score based on benchmark prevalence in production deployments.
3. **Given** a robustness score from one data-size condition, **When** compared to another condition via two-sample t-test, **Then** the system outputs the p-value and effect size (Cohen's d).

---

### User Story 3 - Statistical Validation and Plateau Detection (Priority: P3)

The research system MUST apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) when testing differences across ≥3 data-size conditions, and implement a plateau detection algorithm that identifies the data-size threshold where robustness improvement falls below a specified margin.

**Why this priority**: This addresses the research question's core goal (identifying the optimal training budget). Without statistical correction and plateau detection, findings risk false positives and lack actionable guidance.

**Independent Test**: Can be fully tested by running the full experiment pipeline and verifying that the output includes corrected p-values, a detected plateau point (or explicit "no plateau" finding), and a sensitivity analysis report showing how plateau detection varies across tolerance thresholds.

**Acceptance Scenarios**:

1. **Given** robustness measurements from 1k, 10k, and 100k conditions, **When** pairwise t-tests are computed, **Then** p-values are corrected for family-wise error using Bonferroni (α_corrected = 0.05 / 3 = 0.017).
2. **Given** a sequence of robustness scores across increasing data sizes, **When** the plateau detection algorithm runs, **Then** it identifies the smallest data size where the improvement from the previous size is ≤5% with 95% confidence.
3. **Given** a detected plateau at 10k samples, **When** sensitivity analysis sweeps the tolerance threshold ∈ {0.01, 0.05, 0.1}, **Then** the system reports how the plateau point shifts across thresholds and whether the finding is stable.

---

### Edge Cases

- What happens when the full AgentDoG corpus contains fewer than 100k samples? → The system MUST log a warning and cap the largest subset at the available sample count, adjusting the experiment to 1k, 10k, and available-max.
- How does the system handle benchmark datasets that are unavailable or rate-limited? → The system MUST retry up to 3 times with exponential backoff (1s, 2s, 4s), then fail gracefully with an explicit error message naming the unavailable dataset.
- What happens when GPU hardware is detected but CUDA is not configured? → The system MUST abort with an explicit error message and not attempt any GPU-accelerated operations, ensuring CPU-only execution.
- How does the system handle random seed collisions between training runs? → The system MUST validate that all seeds are unique before starting parallel jobs and reject duplicate seeds with an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract configurable-size subsets (1k, 10k, 100k samples) from the AgentDoG safety corpus using deterministic shuffling based on seed values (See US-1)
- **FR-002**: System MUST fine-tune a 0.8B parameter base model (Qwen-0.5B or equivalent) on each subset with identical hyperparameters (learning rate, batch size, epochs) across all conditions (See US-1)
- **FR-003**: System MUST evaluate each model checkpoint on ATBench and R-Judge adversarial test sets using standardized prompt-injection attack templates (See US-2)
- **FR-004**: System MUST compute robustness metrics (attack success rate, false-positive rate) with 95% confidence intervals across ≥3 random seeds per condition (See US-2)
- **FR-005**: System MUST apply Bonferroni correction for family-wise error when conducting ≥3 pairwise t-tests across data-size conditions (See US-3)
- **FR-006**: System MUST implement plateau detection that identifies the smallest data size where robustness improvement from the previous size is ≤5% (See US-3)
- **FR-007**: System MUST perform sensitivity analysis sweeping the plateau tolerance threshold over {0.01, 0.05, 0.1} and report how the detected plateau point shifts (See US-3)
- **FR-008**: System MUST log all experiments with deterministic seeds, version-controlled data snapshots, and hyperparameter configurations for reproducibility (See US-1)
- **FR-009**: System MUST verify that the ATBench and R-Judge datasets contain all required variables (prompt templates, ground-truth labels, attack type annotations) before proceeding (See US-2)
- **FR-010**: System MUST frame all findings as ASSOCIATIONAL rather than causal, given the observational nature of the data-size manipulation (See US-3)

### Key Entities *(include if feature involves data)*

- **TrainingSubset**: A data partition of the AgentDoG safety corpus with size attribute (1000, 10000, or 100000 samples) and seed attribute for deterministic ordering
- **ModelCheckpoint**: A fine-tuned guardrail model with attributes for training subset size, seed, hyperparameters, and evaluation metrics
- **RobustnessMetric**: A performance measure with attributes for benchmark source (ATBench or R-Judge), metric type (success rate or false-positive rate), value, and confidence interval

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Robustness improvement rate between consecutive data sizes is measured against the 5% plateau detection threshold (See US-3)
- **SC-002**: Family-wise error rate across ≥3 pairwise comparisons is measured against the Bonferroni-corrected α = 0.017 threshold (See US-3)
- **SC-003**: Confidence interval width for robustness scores is measured against the [deferred] coverage requirement (See US-2)
- **SC-004**: Dataset variable completeness is measured against the required predictor/outcome/covariate list (See US-2)
- **SC-005**: Reproducibility is measured by byte-for-byte checkpoint identity across independent runs with identical seeds (See US-1)

## Assumptions

- The AgentDoG safety corpus available on HuggingFace contains ≥100k samples for the 100k subset condition; if fewer samples exist, the largest subset will be capped at the available count.
- The ATBench and R-Judge benchmark datasets contain all required variables: prompt-injection attack templates, ground-truth safety labels, and attack-type annotations for stratified evaluation.
- A 0.8B parameter model (Qwen-0.5B or equivalent) can be fine-tuned and evaluated within the GitHub Actions free-tier constraints (2 CPU cores, ~7 GB RAM, ≤6 hours) without GPU acceleration.
- Human evaluator noise in alignment judgments (as raised by the Daniel-Kahneman-simulated reviewer) is not within scope for this study; the research uses automated benchmark metrics as the ground truth for robustness measurement.
- The relationship between training data size and robustness is non-monotonic (plateau behavior), consistent with the expected results in the idea; a monotonic improvement finding would still be valid but would not identify an optimal budget.
- All benchmark datasets are publicly accessible without rate limits that would prevent completing ≥3 evaluation runs per condition within the 6-hour CI job budget.
- The fine-tuning process uses default precision (FP32) rather than 8-bit/4-bit quantization to ensure CPU compatibility and avoid CUDA dependency.
