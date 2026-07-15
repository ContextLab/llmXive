# Feature Specification: llmXive Follow-up: Counterfactual Inspector Agent

**Feature Branch**: `001-counterfactual-inspector`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "How does the explicit generation and integration of counterfactual narrative angles by an auxiliary agent affect the detection of non-obvious causal insights and the reduction of confirmation bias in automated data journalism systems?"

## User Scenarios & Testing

### User Story 1 - Baseline Narrative Generation (Priority: P1)

The system must process a provided multi-variable public policy dataset and generate a primary narrative story using the existing `llmXive` pipeline, identifying the most statistically prominent causal angle without external intervention.

**Why this priority**: This is the foundational control condition. Without a valid baseline story, the comparative evaluation of the counterfactual agent cannot occur. It establishes the "standard" narrative that the system would produce without the proposed innovation.

**Independent Test**: Can be fully tested by running the existing pipeline on a single known dataset (e.g., a housing dataset with a known primary correlation) and verifying that a coherent story is generated containing the expected dominant trend.

**Acceptance Scenarios**:

1. **Given** a valid CSV dataset with at least 5 numeric variables and 100 rows, **When** the baseline pipeline is executed, **Then** the system outputs a JSON story object containing a "primary_narrative" field with a textual summary of the strongest statistical correlation.
2. **Given** a dataset where Variable A correlates strongly with Variable B, **When** the baseline pipeline runs, **Then** the generated story explicitly claims "A is the primary driver of B" with a supporting statistical metric (e.g., r-value or p-value).
3. **Given** a dataset with missing values, **When** the baseline pipeline runs, **Then** the system imputes or excludes missing data according to the standard `llmXive` protocol and proceeds to generate the story without crashing.

---

### User Story 2 - Counterfactual Angle Generation (Priority: P2)

The system must invoke a dedicated "Counterfactual Inspector Agent" that analyzes the baseline narrative and the raw dataset to generate at least one alternative causal explanation or contradictory correlation that challenges the primary narrative.

**Why this priority**: This implements the core research intervention. It transforms the system from a summarizer into an interrogator, directly addressing the research question regarding bias mitigation and depth.

**Independent Test**: Can be tested by providing a specific baseline narrative (e.g., "High income causes low crime") and a dataset where a counter-intuitive variable (e.g., "High population density") actually correlates with the outcome, verifying the agent identifies and reports this contradiction.

**Acceptance Scenarios**:

1. **Given** a baseline narrative claiming "A causes B" and a dataset containing a variable C inversely related to B, **When** the Counterfactual Inspector Agent is triggered, **Then** the system outputs a structured counterfactual claim identifying C as an alternative driver or a confounding factor.
2. **Given** a dataset with no obvious counter-intuitive correlations, **When** the Inspector Agent runs, **Then** the system explicitly reports "No significant counterfactuals found" rather than hallucinating a false correlation.
3. **Given** a baseline narrative, **When** the Inspector Agent generates a SQL or Python query to test a counterfactual, **Then** the query executes successfully against the dataset. If a statistically significant counterfactual exists within the swept thresholds, the system MUST report the p-value; otherwise, it MUST report "No significant counterfactuals found".

---

### User Story 3 - Integrated Story Synthesis (Priority: P3)

The system must merge the baseline narrative and the verified counterfactual insights into a single, cohesive story that explicitly cites the data queries supporting the alternative perspectives, ensuring the counterfactual is not just mentioned but traced to the data.

**Why this priority**: This delivers the final user-facing artifact. It ensures the counterfactual reasoning is not an internal process but is integrated into the deliverable, allowing for the evaluation of "Narrative Depth."

**Independent Test**: Can be tested by generating a final story and verifying that it contains at least two distinct causal claims (one primary, one counterfactual) and that the counterfactual claim includes a specific reference to the data query or metric used to validate it.

**Acceptance Scenarios**:

1. **Given** a baseline story and a verified counterfactual insight, **When** the narrative engine synthesizes the final output, **Then** the resulting text includes a section titled "Alternative Perspectives" or similar, detailing the counter-intuitive finding.
2. **Given** a counterfactual claim, **When** the final story is rendered, **Then** the claim includes a verifiable citation (e.g., "Data query: `SELECT corr(A, C) FROM table` returned r=-0.45") linking the text to the underlying evidence.
3. **Given** conflicting narratives (baseline vs. counterfactual), **When** the story is generated, **Then** the language used maintains neutrality (e.g., "While X suggests Y, data indicates Z") rather than dismissing the baseline entirely.

---

### Edge Cases

- **What happens when** the dataset is too small (e.g., < 30 rows) to support statistically significant counterfactual testing? The system must flag the result as "Low Power - Interpret with Caution" rather than generating a definitive counterfactual claim.
- **How does the system handle** datasets where *no* counter-intuitive correlations exist (i.e., the data is entirely consistent with the primary narrative)? The system must explicitly state that no alternative angles were found, rather than forcing a weak correlation to meet a quota.
- **What happens when** the LLM generates a query that results in a syntax error or a timeout? The system must retry the query generation up to 2 times, then log the error and proceed with the baseline narrative only, marking the counterfactual step as "Failed."

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a baseline narrative identifying the strongest statistical correlation in the input dataset. (See US-1)
- **FR-002**: System MUST execute a dedicated "Counterfactual Inspector Agent" that queries the dataset for correlations contradicting the baseline narrative. (See US-2)
- **FR-003**: System MUST perform a sensitivity analysis using partial correlation control. For each candidate counterfactual claim, the system MUST compute the partial correlation coefficient controlling for the top-2 baseline drivers. The system MUST report findings in a JSON array where each object contains: `threshold_config` (string), `claim` (string or the literal string "NO_SIGNIFICANT_COUNTERFACTUAL"), `p_value` (float), and `partial_r` (float). A claim is considered valid ONLY if `p_value` < 0.05 AND `|partial_r|` > 0.15. (See US-2, US-3)
- **FR-004**: If at least one verified counterfactual insight exists, the system MUST integrate it into the final story output with a direct citation to the supporting data query. (See US-3)
- **FR-005**: System MUST perform all data processing and LLM inference within a 6-hour execution window on a deterministic environment (2 vCPU, 7GB RAM, ubuntu-latest runner). If the primary Llama-8B inference exceeds 15 minutes per dataset, the system MUST switch to a pre-approved fallback: Phi-3-mini (local) or batched API calls (capped at 5 minutes per dataset). (See US-1, US-2, US-3)
- **FR-006**: System MUST detect and report if the input dataset lacks sufficient sample size (n < 30) for reliable counterfactual inference. (See US-2, US-3)
- **FR-007**: System MUST frame all counterfactual findings as associational observations rather than causal proofs, avoiding causal language unless randomization is present. (See US-2, US-3)

### Key Entities

- **Dataset**: A structured table of public policy data (e.g., CSV) containing numeric variables.
- **Baseline Narrative**: The primary story generated by the standard pipeline, representing the most obvious trend.
- **Counterfactual Inspector Agent**: A dedicated software component that analyzes baseline narratives and datasets to generate and validate alternative causal explanations using partial correlation control.
- **Counterfactual Insight**: A structured object containing an alternative causal claim, the specific query used, and the resulting statistical metrics (including partial correlation).
- **Integrated Story**: The final multimodal output combining baseline and counterfactual elements with verifiable citations.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Narrative Depth is measured against a blinded expert rubric score (5-point Likert scale: 1=Superficial, 5=Deep) evaluating four criteria: (1) Novelty (involves variables outside top 3 correlations), (2) Evidence (cites specific data queries), (3) Nuance (acknowledges limitations), and (4) Clarity. Measurement requires multiple blinded experts. Inter-rater reliability (Cohen's Kappa) must be ≥ 0.6. If Kappa < 0.6, the run is FAILED and must be re-executed with a 4th expert until Kappa ≥ 0.6 is achieved. The final score is the arithmetic mean of the valid experts' scores. (See US-3)
- **SC-002**: Confirmation Bias is measured as the "Counterfactual Validity Score": the proportion of generated counterfactual claims that pass the statistical validity test defined in FR-003 (partial correlation p < 0.05 AND |partial_r| > 0.15). (See US-2, US-3)
- **SC-003**: Computational feasibility is measured against the 6-hour runtime and 7 GB RAM constraints (or API cost/time limits) on a standard GitHub Actions free-tier runner (2 vCPU, 7GB RAM, ubuntu-latest). (See US-1, US-2, US-3)
- **SC-004**: Verification Traceability is measured as the percentage of counterfactual claims in the final story that include a valid, executable data query citation. (See US-3)

## Assumptions

- The public policy datasets (e.g., from UCI or Kaggle) contain sufficient numeric variables and row counts (n ≥ 30) to perform meaningful correlation analysis without requiring data augmentation.
- The LLM used for query generation and narrative synthesis is a lightweight model (e.g., Llama-3-8B or similar) that can run on CPU within the 6-hour time limit, OR the system relies on batched API calls that do not exceed the time budget.
- If the primary Llama inference on CPU exceeds a feasible per-dataset threshold, the fallback to a smaller model or batched API calls is feasible and will preserve the total runtime budget.
- The "Counterfactual Inspector Agent" relies on standard statistical libraries (e.g., `scipy`, `pandas`) that are compatible with the CPU-only environment and do not require GPU acceleration.
- The expert evaluation rubric for "Narrative Depth" and "Confirmation Bias" is pre-defined and stable, allowing for blinded scoring without ambiguity.
- The baseline `llmXive` pipeline is already functional and capable of processing the target datasets without modification, serving as a reliable control.
- The partial correlation thresholds (p < 0.05, |r| > 0.15) are used as community-standard defaults for the sensitivity analysis to ensure robustness across varying data distributions.
- The datasets provided do not require complex feature engineering or external data joining to identify counter-intuitive correlations; the necessary variables are present in the raw input.