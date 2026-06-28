# Feature Specification: Phenomenological AI: First-Person Experience Modeling in Language Models

**Feature Branch**: `592-phenomenological-ai-first-person-experie`  
**Created**: 2026-06-17  
**Status**: Draft  
**Input**: User description: "Phenomenological AI: First-Person Experience Modeling in Language Models"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Report Generation Pipeline (Priority: P1)

The system MUST generate first-person phenomenological reports using four distinct prompting strategies across two open-source LLM checkpoints. This forms the primary dataset for all downstream analysis.

**Why this priority**: Without the generated text corpus, no validity metrics can be computed, and no statistical comparison between prompting strategies is possible. This is the foundational data acquisition step.

**Independent Test**: Can be fully tested by executing the generation script and verifying that the output directory contains the expected number of text files (multiple samples per prompt per strategy) with valid JSON metadata.

**Acceptance Scenarios**:

1. **Given** the prompt templates (Multiple templates) and model checkpoints are available, **When** the generation script runs with temperature 0.7 and top-p 0.9, **Then** Multiple samples are produced without CUDA dependencies.
2. **Given** a specific prompting strategy (e.g., "Role-play"), **When** the system processes 20 prompts, **Then** Multiple samples are generated with unique seeds recorded for reproducibility.

---

### User Story 2 - Phenomenological Metric Computation (Priority: P2)

The system MUST compute three validity criteria (Internal Consistency, Semantic Stability, Marker Presence) for every generated report to produce a composite validity score.

**Why this priority**: This translates raw text into quantifiable data required for the ANOVA and Chi-square statistical tests described in the methodology.

**Independent Test**: Can be fully tested by running the analysis script on a small subset of 10 known reports and verifying the output CSV contains non-null consistency scores, stability scores, and marker counts.

**Acceptance Scenarios**:

1. **Given** a set of generated reports, **When** the NLI model processes pairwise sentences, **Then** a contradiction count is recorded for each report.
2. **Given** repeated generations for the same prompt, **When** embeddings are computed, **Then** cosine similarity scores are stored for stability analysis.
3. **Given** a report text, **When** the keyword dictionary is applied, **Then** counts for sensory, temporal, and intentional markers are logged.

---

### User Story 3 - Qualitative Validation & Reproducibility (Priority: P3)

The system MUST facilitate human evaluation by two philosophy graduate students and archive all artifacts for public reproducibility.

**Why this priority**: This provides the external validity check (inter-rater reliability) required to ground the automated metrics in human judgment and ensures the research can be audited.

**Independent Test**: Can be fully tested by verifying the GitHub repository contains the `run.sh`, `requirements.txt`, and the anonymized qualitative rating sheets with calculated Cohen's κ.

**Acceptance Scenarios**:

1. **Given** the generated reports, **When** the two annotators rate Multiple reports per condition, **Then** inter-rater reliability is computed and stored.
2. **Given** the analysis is complete, **When** the archive script runs, **Then** all prompts, seeds, and scripts are committed to the public repository.

---

### Edge Cases

- What happens when the NLI model fails on a specific sentence pair due to length limits? The system MUST skip the pair and log a warning without halting the batch.
- How does the system handle model generation timeouts on the free-tier runner? The system MUST retry the specific generation up to 3 times before marking the sample as missing.
- What happens if inter-rater reliability (Cohen's κ) falls below 0.5? The system MUST flag the condition for re-evaluation in the final report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate ≥ 80 samples per prompt per strategy using the 4 defined prompting strategies (See US-1); if generation fails, retry up to 3 times and mark as missing after 3 failures, maintaining ≥80 successful samples per condition.
- **FR-002**: System MUST execute inference on CPU-only environment without CUDA dependencies or GPU-specific quantization (See US-1).
- **FR-003**: System MUST compute internal consistency using a pretrained Natural Language Inference (NLI) model on pairwise sentences (See US-2).
- **FR-004**: System MUST compute semantic stability using cosine similarity between embeddings of repeated generations (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg FDR correction (α≤0.05) and Tukey HSD post-hoc tests for all ANOVA comparisons (See US-2).
- **FR-006**: System MUST perform sensitivity analysis on validity score weights over range {0.25, 0.5, 0.75} (See US-2).
- **FR-007**: System MUST archive all prompts, model checkpoints (via HuggingFace IDs), generation seeds, and analysis scripts (See US-3).
- **FR-008**: System MUST compute phenomenological marker presence using rule-based keyword dictionary for sensory, temporal, and intentional markers (See US-2).
- **FR-009**: System MUST provide construct validity justification for computational metrics: cite phenomenology literature establishing marker definitions, or perform sensitivity analysis across alternative metric definitions (e.g., absolute diff ∈ {0.01, 0.05, 0.1}) (See US-2).
- **FR-010**: System MUST use independent validation rubric for human raters (separate from automated metric definitions) and report correlation between human coherence ratings and automated validity scores (See US-3).
- **FR-011**: System MUST perform sensitivity analysis on Cohen's κ threshold across {0.5, 0.6, 0.7} to assess robustness of inter-rater reliability conclusions (See US-3).
- **FR-012**: System MUST test ANOVA assumptions (Shapiro-Wilk normality p≥0.05, Levene's homogeneity p≥0.05); if violated, use Kruskal-Wallis non-parametric alternative (See US-2).

### Key Entities

- **Phenomenological Report**: A text output generated by an LLM in response to a specific prompt strategy.
- **Validity Score**: A composite metric computed as the normalized weighted sum of three component scores: Internal Consistency (0.33 weight), Semantic Stability (0.33 weight), and Marker Presence (0.33 weight). Each component is normalized to [0,1] range before aggregation.
- **Prompt Strategy**: One of the four defined input manipulation styles (Direct, Hypothetical, Comparative, Role-play).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: All three validity metrics (Internal Consistency, Semantic Stability, Marker Presence) MUST be computed for ≥95% of generated reports (See US-2).
- **SC-002**: Inter-rater reliability (Cohen's κ) for qualitative validation MUST be ≥0.6 on stratified random sample of 10 reports per condition, justified against phenomenological qualitative research convention (Cohen 1960; Landis & Koch 1977) (See US-3).
- **SC-003**: Statistical significance threshold MUST be p < 0.05 with family-wise error rate controlled via Benjamini-Hochberg FDR (See US-2).

## Assumptions

- **Compute Constraints**: Medium-scale parameter models will be run in low-bit quantization (GGUF) or a smaller subset of generations (e.g., multiple samples per prompt) if the full sample plan exceeds the 6-hour CI time limit.
- **Performance Constraint**: Pipeline execution time MUST be ≤ 6 hours on standard free-tier runner (4 vCPU, 16GB RAM, Ubuntu 22.04) (See US-1).
- **Human Resources**: Two philosophy graduate students are available for the qualitative validation phase and can complete the 10-report rating task per condition within 2 weeks.
- **Model Access**: HuggingFace models (`meta-llama/Llama-7b-chat-hf`, `mistralai/Mistral-7B-Instruct-v0.2`) are accessible without rate limits that block CI execution.
- **Inference Framing**: Findings regarding prompting strategies and report coherence are treated as associational, not causal, due to the observational nature of the prompting manipulation.
- **Threshold Justification**: The weights for the composite validity score are treated as tunable hyperparameters; the sensitivity analysis (FR-006) serves as the justification mechanism rather than a fixed pre-registered value.