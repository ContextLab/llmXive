# Feature Specification: llmXive follow-up: extending "ArcANE"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'ArcANE: Do Role-Playing Language Agents Stay in Character at the Right'"

## User Scenarios & Testing

### User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1)

**Description**: The system MUST allow a researcher to define and store two distinct sets of psychological axes for a given character: (1) Coarse Axes (broad traits) and (2) Fine Axes (nuanced shifts). These axes must be derived from independent narrative observations to ensure the validation target is not tautological.

**Why this priority**: Without valid, independently defined ground-truth axes, the comparison between prompting strategies (Coarse, Fine, Hybrid) cannot be conducted. This is the foundational data layer.

**Independent Test**: A researcher can input a character name and receive two distinct, non-overlapping JSON objects representing the Coarse and Fine axes, which can be verified against the manual definitions in the idea markdown.

**Acceptance Scenarios**:
1. **Given** a character name (e.g., "Harry Potter"), **When** the system requests axis definitions, **Then** the system outputs a "Coarse" specification (e.g., "Innocence to Experience") and a "Fine" specification (e.g., "Naive Trust to Calculated Skepticism") as distinct entities.
2. **Given** the defined axes, **When** the system validates them against the source text, **Then** it confirms that the Fine axes are derived from independent narrative observations (not subsets of Coarse) and satisfies a semantic overlap constraint: lexical overlap > 0.4 and embedding cosine distance < 0.3 between Coarse and Fine definitions.

---

### User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Description**: The system MUST generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text (e.g., applying character traits to modern ethical dilemmas or sci-fi scenarios) to test transferability.

**Why this priority**: The core hypothesis concerns "transferability to novel scenarios." If the probes are not out-of-world, the experiment fails to test generalization.

**Independent Test**: The system can generate a batch of probes for a character, and a sample check confirms that none of the prompts contain direct quotes or plot points from the original source text, and the average cosine similarity is relatively low.

**Acceptance Scenarios**:
1. **Given** a character and their defined axes, **When** the system generates probes, **Then** it produces at least 50 distinct prompts that apply the character's psychological profile to scenarios not present in the original training corpus.
2. **Given** the generated probes, **When** a semantic similarity check is run against the source text, **Then** the average cosine similarity is below 0.3, confirming semantic distance.

---

### User Story 3 - Execute Hybrid Prompting and Consistency Evaluation (Priority: P3)

**Description**: The system MUST run the target model (e.g., Phi-3-mini) under three conditions (Coarse, Fine, Hybrid) for each probe, and use a secondary "Judge" model AND a rule-based metric to rate consistency on a 1-5 Likert scale. The system MUST also perform a Judge Calibration step prior to main execution.

**Why this priority**: This is the experimental execution engine. It produces the raw data (consistency scores) required for the statistical analysis (ANOVA).

**Independent Test**: The system can process a single probe through all three conditions, output a structured result containing the model's response, the rule-based score, and the Judge's consistency score for each condition.

**Acceptance Scenarios**:
1. **Given** a probe and a character, **When** the system runs the "Hybrid" condition, **Then** the model receives both the broad summary and specific phase details in the prompt.
2. **Given** a model response, **When** the Judge model evaluates it, **Then** it outputs a numeric score (1-5) and a binary flag indicating if the response adhered to the target phase. Adherence is defined as: the response contains at least 2 phase-specific keywords from the prompt's defined phase list.
3. **Given** a model response, **When** the rule-based metric calculates a score, **Then** it outputs a numeric score (1-5) based on keyword presence and sentiment alignment, distinct from the Judge's score.
4. **Given** a set of human-annotated gold samples (n=20), **When** the system calibrates the Judge, **Then** it computes inter-rater reliability (Kappa > 0.6) before proceeding to the main experiment.

---

### Edge Cases

- **What happens when the target model (e.g., Phi-3-mini) fails to generate a response within the 60-second timeout?** The system MUST log the failure, assign a default consistency score of zero for that trial, and proceed to the next probe to ensure the experiment completes within the CI time limit.
- **How does the system handle a Judge model that outputs a score outside the 1-5 range?** The system MUST validate the output and clamp any out-of-bounds scores to the nearest valid integer within the defined scale range or discard the trial if the format is unparseable, logging the incident.
- **What happens if the semantic distance check for a generated probe fails (i.e., it is too similar to the source)?** The system MUST discard that specific probe and regenerate a replacement until a sufficient number of valid probes are collected (at least 50).
- **What happens if the regeneration loop exceeds 150 attempts?** The system MUST stop generating probes for that character, log a "Generation Limit Exceeded" error, and proceed with the available valid probes (if >= 50) or mark the character as invalid for the experiment.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate two distinct psychological axis definitions (Coarse and Fine) for each selected character based on manual input. Fine axes MUST be derived from independent narrative observations, not as subsets of Coarse axes (See US-1).
- **FR-002**: System MUST generate at least 50 "Out-of-World" probes per character that are semantically distant from the source text, verified by a similarity check (cosine similarity < 0.3). If a probe fails the check, it is discarded and regenerated up to a maximum of 150 attempts (See US-2).
- **FR-003**: System MUST execute the target model in zero-shot mode under three specific prompting conditions: Coarse Context, Fine Context, and Hybrid Context (See US-3).
- **FR-004**: System MUST invoke a secondary, quantized "Judge" model to rate each generated response on a 1-5 Likert scale for consistency, AND calculate a rule-based score based on keyword presence and sentiment alignment. The Judge must not see ground-truth labels (See US-3).
- **FR-005**: System MUST aggregate the consistency scores (both Judge and rule-based) across the three conditions. If the residuals of the Judge scores fail the Shapiro-Wilk normality test (p < 0.05), the system MUST default to the non-parametric Friedman test; otherwise, it MUST perform a repeated-measures ANOVA (See US-3).
- **FR-006**: System MUST validate the generated Consistency Scores against an external "Gold Standard" dataset of character behaviors (n=20) to ensure the evaluation is not circular (See US-3).
- **FR-007**: System MUST perform a Judge Calibration step prior to the main experiment, validating the LLM Judge against human-annotated samples to achieve a Kappa coefficient > 0.6 (See US-3).

### Key Entities

- **Character Axis**: A structured definition of a character's psychological state, containing a "Coarse" descriptor and a "Fine" descriptor (derived independently).
- **Probe**: A generated text prompt representing an out-of-world scenario designed to elicit a character-specific response.
- **Consistency Score**: A numeric rating (1-5) assigned by the Judge model or rule-based metric indicating the degree of adherence to the target character arc phase.
- **Gold Standard**: A small, manually annotated dataset of character behaviors used to validate the Consistency Score and prevent instruction-following confounds.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The mean consistency score for the "Hybrid" condition is measured against the mean scores of the "Coarse" and "Fine" conditions to determine statistical significance (ANOVA or Friedman test) (See FR-005, US-3).
- **SC-002**: The mean cosine similarity of generated probes against the source text corpus must be < 0.3 to ensure they meet the "Out-of-World" criteria (See FR-002, US-2).
- **SC-003**: The total execution time of the full experiment (multiple conditions × multiple characters × 50 probes) is measured against the CI job time limit to ensure feasibility (See FR-003, US-3).
- **SC-004**: The variance in consistency scores across the three conditions is measured to assess the stability of the Hybrid strategy (See FR-005, US-3).
- **SC-005**: The rate of "Judge Model" output validation failures (scores outside 1-5) is measured to ensure the evaluation pipeline is robust (See FR-004, US-3).
- **SC-006**: The inter-rater reliability (Kappa) between the Judge and human annotations during calibration must be > 0.6 (See FR-007, US-3).

## Assumptions

- **Assumption about data source**: The "ArcANE" corpus contains sufficient source text for at least 3 distinct characters (e.g., Harry Potter, Elizabeth Bennet) to allow for manual axis definition.
- **Assumption about hardware constraints**: The target model (e.g., Phi-mini or TinyLlama-1.1B) can be loaded and run on a standard GitHub Actions free-tier runner (multiple CPU cores, ~7 GB RAM) using low-bit quantization via `llama.cpp` or `transformers` without exceeding the 6-hour time limit.
- **Assumption about model capacity**: Small language models (≤2B parameters) possess sufficient in-context learning capability to track psychological arcs when provided with the "Hybrid" prompt structure, even without fine-tuning.
- **Assumption about evaluation validity**: A secondary, smaller quantized model is capable of acting as a reliable "Judge" for consistency on a 1-5 Likert scale, provided the prompt explicitly forbids access to ground-truth labels AND a rule-based metric is used as a primary validation check.
- **Assumption about statistical power**: A sample size of a sufficient number of total trials (characters × multiple probes) is sufficient to detect a medium effect size. in a repeated-measures ANOVA with 3 conditions, acknowledging that a formal power analysis is deferred due to resource constraints.
- **Assumption about variable fit**: The manually defined "Coarse" and "Fine" axes are the only variables required to test the hypothesis; no external psychological data (e.g., trait anxiety scores) is needed from the dataset, as the axes are derived from narrative text.
- **Assumption about Judge Calibration**: A small set of human-annotated samples is sufficient to establish the reliability of the LLM Judge before the main experiment.