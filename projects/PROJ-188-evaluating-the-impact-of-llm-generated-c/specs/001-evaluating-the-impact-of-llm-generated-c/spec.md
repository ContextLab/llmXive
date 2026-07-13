# Feature Specification: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

**Feature Branch**: `001-eval-llm-code-explanations`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of LLM-Generated Code Explanations on Comprehension"

## User Scenarios & Testing

### User Story 1 - Dataset Curation and Explanation Generation (Priority: P1)

The system MUST ingest a curated set of Python functions from the CodeSearchNet corpus, varying in cyclomatic complexity, and generate a single natural-language explanation for each function using the CodeLlama-7B model (4-bit quantized) via HuggingFace `transformers` on a CPU-only runner, limited to 150 tokens per explanation. The target dataset size will be determined by the research question, the method, and the references, ensuring sufficient scope for analysis without specifying an exact count at this planning stage.

**Why this priority**: This is the foundational data layer. Without a consistent dataset and the corresponding LLM-generated artifacts, the human study cannot be constructed or executed. This step establishes the independent variable (the explanation text).

**Independent Test**: The script can be run in isolation to produce a JSON file containing up to 30 code snippets and their corresponding explanations. The output can be validated by checking that every snippet has exactly one explanation under 150 tokens and that the complexity labels (low/medium/high) are correctly assigned. If generation fails for some snippets, the test passes if the final N is ≥ 20 and the failure is logged.

**Acceptance Scenarios**:

1. **Given** the CodeSearchNet corpus is accessible, **When** the curation script runs, **Then** up to 30 Python functions are extracted and labeled by cyclomatic complexity (low, medium, high).
2. **Given** a Python function and the CodeLlama-7B model loaded on a CPU runner, **When** the generation prompt is executed, **Then** a single explanation string is produced that does not exceed 150 tokens.
3. **Given** the generated dataset, **When** the validation check runs, **Then** no null values exist for code or explanation fields, and all complexity labels are within the defined set {low, medium, high}.

---

### User Story 2 - Study Survey Construction and Deployment (Priority: P2)

The system MUST construct a survey interface that presents participants with one of three conditions (Code Only, Code + LLM Explanation, Code + Official Docstring or Placeholder) for a specific code snippet and records both the multiple-choice answer and the time-to-submit (latency) for each question.

**Why this priority**: This enables the primary data collection phase. It operationalizes the experimental design by enforcing the random assignment and capturing the dependent variables (accuracy and speed).

**Independent Test**: A mock survey can be deployed to a test group where the logic flow is verified: a user receives a specific condition, answers a question, and the backend logs the response accuracy and timestamp difference.

**Acceptance Scenarios**:

1. **Given** a participant is assigned to Condition B (Code + LLM Explanation), **When** they view the interface, **Then** they see the code snippet and the corresponding LLM-generated explanation, but not the official docstring.
2. **Given** a participant submits an answer to a comprehension question, **When** the submission is processed, **Then** the system records the binary accuracy (correct/incorrect) and the precise time elapsed (in milliseconds) since the question load.
3. **Given** a participant completes the study, **When** the session ends, **Then** the system logs the participant ID, assigned condition, code snippet ID, and all response metrics in a structured CSV format.

---

### User Story 3 - Statistical Analysis and Robustness Reporting (Priority: P3)

The system MUST execute a linear mixed model analysis on the collected data with fixed effects for *condition* and *complexity* and random intercepts for participants only, followed by post-hoc Tukey tests, and perform a sensitivity analysis sweeping the explanation quality threshold (BLEU score) to report stability of results.

**Why this priority**: This delivers the research outcome. It transforms raw logs into statistical evidence, addressing the research question regarding the impact of explanations while validating the robustness of the findings against explanation quality. The use of a linear mixed model with only participant random effects is methodologically necessary due to the low number of snippets (N=30).

**Independent Test**: The analysis script can be run against a synthetic dataset with known parameters to verify that the LMM F-statistics, p-values, and Tukey confidence intervals are calculated correctly and that the sensitivity sweep produces a trend report.

**Acceptance Scenarios**:

1. **Given** the cleaned dataset (removing participants with <30s total time or >80% missing data), **When** the LMM is fitted, **Then** the output includes the F-statistic and p-value for the interaction effect between *condition* and *complexity*.
2. **Given** the primary analysis results, **When** the post-hoc Tukey test is executed, **Then** pairwise comparisons between the three conditions are reported with adjusted p-values.
3. **Given** the subset of data where BLEU similarity ≥ 0.70, **When** the analysis is re-run and compared to the full dataset, **Then** a sensitivity report is generated showing the variation in headline accuracy/speed rates across the specified BLEU thresholds {0.70, 0.80, 0.90}.

---

### Edge Cases

- **What happens when** the CodeLlama model fails to generate an explanation within the timeout limit or produces output >150 tokens?
  - *Handling*: The system MUST retry up to 3 times with a 5-second backoff. If it still fails, the specific code snippet is marked as "skipped" in the dataset, and the analysis script must handle a non-integer N (e.g., 29/30) without crashing, logging the skip reason. The target is 30, but N < 30 is acceptable.
- **How does the system handle** participants who attempt to submit the survey in less than 30 seconds total?
  - *Handling*: The system MUST flag these records as "invalid" in the preprocessing step and exclude them from the final statistical analysis, logging the count of excluded participants.
- **What happens when** a code snippet has no official docstring for Condition C?
  - *Handling*: The system MUST automatically assign a "dummy" or "no-doc" placeholder text for Condition C participants for that specific snippet, ensuring the experimental balance is maintained, and note this in the methodology report. Condition C is defined as "Code + Official Docstring (or Placeholder if missing)".

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a target of 30 Python function explanations using the CodeLlama-7B model (4-bit quantized) with a hard token limit of 150 tokens per explanation (See US-1).
- **FR-002**: System MUST randomize participants into three distinct experimental conditions (Code Only, Code + LLM, Code + Docstring) using stratified random sampling with a fixed seed (seed=42) to ensure equal probability (See US-2).
- **FR-003**: System MUST record response latency with millisecond precision for every question submitted by a participant (See US-2).
- **FR-004**: System MUST filter the dataset to exclude participants with total completion time < 30 seconds or missing data > 80% (where missing data is defined as missing any of: answer, latency, or condition assignment) prior to statistical analysis (See US-3).
- **FR-005**: System MUST execute a linear mixed model (using statsmodels MixedLM with Gaussian family) with fixed effects for *condition* and *complexity* and random intercepts for participants only (See US-3).
- **FR-006**: System MUST perform a sensitivity analysis sweeping the BLEU similarity threshold over a range of representative values. using the official docstring as the reference text to assess result stability (See US-3).
- **FR-007**: System MUST report p-values for the interaction term between *condition* and *complexity* to test the primary hypothesis (See US-3).
- **FR-008**: System MUST report the participant pass rate (percentage of recruited participants passing quality filters) in the final output (See US-3).
- **FR-009**: System MUST include a statement in the final analysis report acknowledging the limitation that BLEU similarity measures fidelity to the baseline (docstring) rather than intrinsic explanation quality (See US-3).

### Key Entities

- **CodeSnippet**: A Python function from CodeSearchNet, identified by ID, with attributes for source code, cyclomatic complexity label, and optional official docstring.
- **Explanation**: A natural-language text string generated by the LLM, linked to a CodeSnippet, with metadata for generation timestamp and token count.
- **ParticipantResponse**: A record of a user's interaction, containing ParticipantID, ConditionID, SnippetID, QuestionID, Answer (boolean), and Latency (ms).
- **AnalysisResult**: A structured output containing statistical metrics (F-stat, p-value, effect size) derived from the ParticipantResponse dataset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The primary hypothesis test (interaction effect of condition × complexity) is measured against a significance threshold of p < 0.05, with findings framed as associational due to the observational nature of the complexity variable (See US-3).
- **SC-002**: The robustness of the headline accuracy rates is measured against the sensitivity analysis sweep across BLEU thresholds {0.70, 0.80, 0.90}, reporting the percentage variance in outcomes (See US-3).
- **SC-003**: The data collection validity is measured against the observed pass rate, ensuring at least 90% of recruited participants pass the quality filters (>30s time, <80% missing) (See US-2).
- **SC-004**: The computational feasibility is measured against the GitHub Actions `ubuntu-latest` runner constraints, ensuring the entire analysis pipeline (including CodeLlama inference on CPU) completes within 6 hours on a 2-core, 7GB RAM runner (See US-1, US-3).
- **SC-005**: The multiplicity correction is measured by the application of Tukey's HSD adjustment for all pairwise comparisons between the three conditions to control the family-wise error rate (See US-3).

## Assumptions

- **Dataset Variable Fit**: The CodeSearchNet corpus contains sufficient Python functions with varying cyclomatic complexity and available docstrings to construct the three experimental conditions. If a snippet lacks a docstring, a placeholder is used, assuming this does not bias the "Code + Docstring" condition significantly.
- **Model Inference Feasibility**: The CodeLlama-7B model (4-bit quantized) can be loaded and executed on a CPU-only GitHub Actions runner (2 cores, ~7 GB RAM) within the 6-hour job limit by using `bitsandbytes` for CPU quantization, with a strict batch size of 1 and aggressive memory management.
- **Participant Recruitment**: The study will successfully recruit a minimum of 90 valid participants via Prolific or MTurk to achieve adequate statistical power for a 3x3 mixed design, assuming a medium effect size (f = 0.25) and alpha = 0.05.
- **Measurement Validity**: The multiple-choice questions designed for each snippet accurately measure comprehension and are not ambiguous, ensuring that accuracy is a valid proxy for understanding.
- **Inference Framing**: The analysis will treat code complexity as an observed covariate rather than a manipulated variable; therefore, all claims regarding the relationship between complexity and comprehension will be framed as associational, not causal.
- **Threshold Justification**: The 150-token limit for explanations is justified by the need to keep reading time comparable across conditions and the context window constraints of the CPU runner; the BLEU sweep {0.70, 0.80, 0.90} is justified as essential for robustness against the arbitrary 0.80 cutoff, citing community practice for sensitivity analysis in NLP evaluation.
- **BLEU Limitation**: The BLEU metric is used as a proxy for 'fidelity to the baseline' rather than 'intrinsic quality'. This circularity risk is acknowledged in FR-009 and will be reported in the final analysis to ensure transparency.