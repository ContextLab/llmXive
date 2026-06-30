# Feature Specification: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

**Feature Branch**: `001-measuring-epistemic-resilience`  
**Created**: 2026-06-18  
**Status**: Draft  
**Input**: User description: "Measuring Epistemic Resilience of LLMs Under Misleading Medical Context"

## User Scenarios & Testing

### User Story 1 - Generate Misleading Medical Contexts (Priority: P1)

The system must be able to ingest a standard medical multiple-choice question (USMLE-style) and automatically inject a single, plausible but false medical claim into the question stem using the EvalPrompt methodology, producing a "mislead" variant while preserving the original ground truth.

**Why this priority**: This is the foundational data preparation step. Without the ability to reliably generate the misleading context, the subsequent resilience measurements cannot occur. It is the primary transformation of the input dataset.

**Independent Test**: Can be fully tested by running `generate_mislead.py` on a sample of 50 questions from the `medqa` dataset and verifying that the output JSON contains the original question, the injected false claim, and the unchanged correct answer key.

**Acceptance Scenarios**:
1. **Given** a clean USMLE-style question from the `medqa` dataset, **When** the script injects a false claim regarding a drug interaction, **Then** the output question stem contains the false claim, and the gold-standard answer remains identical to the original.
2. **Given** a question with multiple potential false claims, **When** the script selects a claim, **Then** exactly one false claim is injected, and no other part of the question stem is altered.
3. **Given** a malformed input file, **When** the script attempts to parse it, **Then** the script logs the error and skips the malformed entry without crashing the entire batch.

---

### User Story 2 - Execute Inference with Multiple Strategies (Priority: P2)

The system must run inference on both the clean and mislead datasets using three distinct prompting strategies (Baseline, Chain-of-Thought, Self-Critique) across three open-weight Llama-2 models (7B, 13B, 70B), ensuring deterministic outputs via fixed seeds and temperature settings. Execution of the 70B model is conditional on GPU availability; if no GPU is available, the 70B model is skipped, and the run proceeds with 7B and 13B only.

**Why this priority**: This executes the core experimental design. It generates the raw data (model answers) required to calculate accuracy and resilience. It is dependent on US-1 but is a distinct operational phase.

**Independent Test**: Can be fully tested by running `run_inference.py` on a subset of 10 questions and verifying that the output logs contain the expected number of distinct model responses (3 models × 3 strategies × 10 questions if GPU available; 2 models × 3 strategies × 10 questions if CPU only), all with `temperature=0.0` and `seed=42`.

**Acceptance Scenarios**:
1. **Given** a mislead question and the Llama-2-7B model, **When** the Chain-of-Thought strategy is applied, **Then** the model output includes a reasoning trace followed by the final answer choice.
2. **Given** the same input and model, **When** the Self-Critique strategy is applied, **Then** the model output includes an initial answer, a critique of that answer, and a revised final answer.
3. **Given** a batch of 100 questions, **When** the inference job completes on a GitHub Actions `ubuntu-latest` runner (2 CPU cores, 7GB RAM, 6-hour timeout), **Then** the job finishes within the 6-hour time limit and produces a JSONL file with exactly 100 entries per model/strategy combination (or skips 70B if CPU-only).

---

### User Story 3 - Compute Resilience and Statistical Significance (Priority: P3)

The system must calculate the epistemic resilience score for each model/strategy combination using the defined formula (1 - (clean - mislead)/clean) with a fallback for zero clean accuracy, and perform statistical tests (Wilcoxon signed-rank on per-item correctness, Kruskal-Wallis on per-item resilience distributions) to determine if observed differences in resilience are statistically significant.

**Why this priority**: This delivers the final scientific insight. It transforms raw accuracy data into the "epistemic resilience" metric and validates the hypothesis regarding model scale and prompting strategies.

**Independent Test**: Can be fully tested by running the analysis script on a pre-computed dataset of model answers and verifying that the output report contains the resilience scores for all combinations and the p-values for the statistical comparisons.

**Acceptance Scenarios**:
1. **Given** clean accuracy of [deferred] and mislead accuracy of [deferred] for a specific model, **When** the resilience formula is applied, **Then** the calculated resilience score equals 1 - (clean - mislead)/clean.
2. **Given** resilience scores for three model sizes (7B, 13B, 70B), **When** the Kruskal-Wallis test is performed, **Then** the output includes the H-statistic and the p-value (format: float, 0-1 range) indicating whether the difference in resilience across scales was tested.
3. **Given** a set of resilience scores, **When** the multiple-comparison correction is applied, **Then** the final reported p-values are adjusted (e.g., Bonferroni or Tukey HSD) to control the family-wise error rate.

### Edge Cases

- What happens when the model fails to generate a valid multiple-choice option (e.g., outputs "Answer: A, B, C") instead of a single letter? The system must treat this as a non-match against the gold standard (accuracy = 0) and log the anomaly.
- How does the system handle the 70B model exceeding the 7 GB RAM limit on the free CI runner? The system must detect the OOM error or Time Limit Exceeded (TLE) and automatically skip the 70B model for that specific run, recording the limitation in the final report.
- What if the injected false claim makes the question unanswerable even for a human expert? The system must flag these items during the generation phase (US-1) and exclude them from the resilience calculation to avoid skewing results with ambiguous ground truth.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a misleading context by injecting exactly one false medical claim into the question stem of the `medqa` dataset using the EvalPrompt template logic. (See US-1)
- **FR-002**: System MUST execute inference for Llama-2-7B and 13B models using Baseline, Chain-of-Thought, and Self-Critique prompts with `temperature=0.0` and `seed=42`. If GPU resources are available, System MUST also execute inference for Llama-2-70B. (See US-2)
- **FR-003**: System MUST calculate the epistemic resilience score for every model/strategy pair using the formula: $1 - \frac{\text{clean accuracy} - \text{mislead accuracy}}{\text{clean accuracy}}$. If clean accuracy is 0, the resilience score MUST be defined as 0, and the item MUST be excluded from aggregate metrics. (See US-3)
- **FR-004**: System MUST perform a Wilcoxon signed-rank test on the *per-item correctness vectors* (0/1 for each question) to compare clean vs. mislead accuracy within each model/strategy pair. System MUST perform a Kruskal-Wallis test on the *distribution of per-item resilience scores* (or bootstrap replicates) to compare resilience across model scales. (See US-3)
- **FR-005**: System MUST apply a multiple-comparison correction (Bonferroni for pairwise, Tukey HSD or Dunn's test with Bonferroni for post-hoc following Kruskal-Wallis) to all statistical p-values to control the family-wise error rate when reporting significance. (See US-3)
- **FR-006**: System MUST validate that the injected false claim does not alter the original correct answer key, preserving the gold standard for evaluation. (See US-1)
- **FR-007**: System MUST detect Time Limit Exceeded (TLE) or Out-of-Memory (OOM) errors for the 70B model on CPU-only runners and skip the 70B inference for that batch, logging the limitation in the final report. (See US-2)

### Key Entities

- **QuestionItem**: Represents a single medical question, containing the original stem, the injected false claim (if any), the gold-standard answer, and the model's generated response.
- **ResilienceMetric**: A computed record linking a specific model, prompting strategy, and the calculated resilience score (float) along with associated statistical significance values.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The drop in accuracy (clean vs. mislead) is measured against the baseline performance of the Llama-2 models on the clean `medqa` dataset to determine the magnitude of epistemic fragility. (See US-3)
- **SC-002**: The difference in resilience scores between model scales (7B vs. 13B vs. 70B) is measured against the null hypothesis of no difference using the Kruskal-Wallis test statistic. (See US-3)
- **SC-003**: The effectiveness of prompting strategies (CoT, Self-Critique) is measured against the Baseline strategy to quantify the mitigation of misleading context impact. (See US-3)
- **SC-004**: The family-wise error rate for all hypothesis tests is measured against the standard alpha threshold (0.05) after applying the specified multiple-comparison correction. (See US-3)

## Assumptions

- The `medqa` dataset on HuggingFace contains sufficient USMLE-style multiple-choice questions where a single false claim can be injected without rendering the question logically impossible for a human expert.
- The 70B Llama-2 model requires >7 GB RAM and cannot be run on CPU-only GitHub Actions runners (7GB RAM limit) without destroying model capabilities; therefore, 70B inference is conditional on GPU availability. If no GPU is available, the 70B condition is skipped, and results are reported for 7B and 13B only.
- The "clinician-annotated gold standard" referenced in the idea is available as a static file accompanying the `medqa` dataset and does not require real-time external API calls to verify.
- The false claims generated by the `EvalPrompt` template are semantically plausible enough to confuse the model but distinct enough that a human expert would still identify the correct answer.
- The statistical power of the study is sufficient with the available dataset size (a substantial corpus in MedQA) to detect medium effect sizes., though a formal power analysis is deferred to the analysis phase if the initial sample is too small.
- The CI environment is GitHub Actions `ubuntu-latest` with 2 CPU cores, 7GB RAM, and a 6-hour job timeout.