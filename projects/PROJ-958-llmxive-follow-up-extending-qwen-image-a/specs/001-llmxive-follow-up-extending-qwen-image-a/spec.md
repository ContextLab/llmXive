# Feature Specification: llmXive follow-up: extending "Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-08-01  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Qwen-Image-Agent: Bridging the Context Gap in Real-World Image Generation'"

## User Scenarios & Testing

### User Story 1 - Ambiguity Scoring & Dataset Stratification (Priority: P1)

The system must ingest raw text prompts from the IA-Bench and WISE-Verified datasets and compute a deterministic "Ambiguity Score" (0.0–1.0) for each prompt based exclusively on syntactic complexity (parse tree depth, clause count) and lexical diversity (MTLD), explicitly excluding semantic embeddings.

**Why this priority**: This is the foundational data layer. Without a reproducible, non-circular ambiguity metric, the subsequent routing and fidelity analysis cannot be performed or validated. It establishes the independent variable for the study.

**Independent Test**: Can be fully tested by running the scoring script on a known subset of 100 prompts and verifying the output CSV contains scores, syntactic features, and lexical features, with no semantic embedding vectors present.

**Acceptance Scenarios**:

1. **Given** a list of 50 raw text prompts from IA-Bench, **When** the scoring module processes them, **Then** the output file contains a numeric ambiguity score (0.0–1.0) for each prompt and a log entry confirming no semantic embeddings were used.
2. **Given** a prompt with high syntactic complexity (deep parse tree) but simple vocabulary, **When** scored, **Then** the ambiguity score reflects the syntactic weight as defined by the weighted average formula, not the semantic content.
3. **Given** a prompt that fails to parse due to malformed syntax, **When** processed, **Then** the system assigns a default low score (0.0) and logs a warning, ensuring the pipeline does not crash.

---

### User Story 2 - Hybrid Routing & Execution Simulation (Priority: P2)

The system must implement a deterministic "Router" that classifies prompts into "low," "medium," or "high" ambiguity categories based strictly on the computed Ambiguity Score thresholds (low: < 0.2, medium: 0.2–0.6, high: > 0.6), routing them to either a rule-based context expansion module (for low and medium) or a simulated full agentic execution pipeline (for high).

**Why this priority**: This implements the core hypothesis: that simple prompts can bypass expensive reasoning. It defines the "hybrid" behavior being tested against the baseline.

**Independent Test**: Can be tested by feeding a mix of clearly simple and clearly complex prompts and verifying that simple prompts trigger the rule-based path (logging "Router: Low") while complex prompts trigger the agent path (logging "Router: High"), confirming the routing is a deterministic function of the score.

**Acceptance Scenarios**:

1. **Given** a prompt with an ambiguity score < 0.2, **When** processed by the Router, **Then** the system routes it to the rule-based context expansion module and logs the decision with the specific threshold used.
2. **Given** a prompt with an ambiguity score > 0.6, **When** processed, **Then** the system routes it to the full agentic execution simulation and logs the decision.
3. **Given** a prompt with an ambiguity score between 0.2 and 0.6, **When** processed, **Then** the system routes it to the rule-based context expansion module and logs the category "medium".

---

### User Story 3 - Fidelity Measurement & Threshold Detection (Priority: P3)

The system must compute the "Context Fidelity" delta between the baseline (full agent) and hybrid execution using a frozen CLIP model (ViT-B/32) against human-verified references, ensuring paired generation (identical seeds), and apply piecewise linear regression with model comparison to identify the "knee point" where agentic advantages vanish.

**Why this priority**: This delivers the final research output: the specific threshold value. It validates whether the routing strategy actually preserves fidelity while saving cost.

**Independent Test**: Can be tested by running the regression analysis on a pre-computed dataset of fidelity scores and ambiguity scores, verifying that the output includes a calculated knee point, a plot of the fidelity delta curve, and a statistical justification (F-test) that the piecewise model is superior to a linear model.

**Acceptance Scenarios**:

1. **Given** a set of generated images and their corresponding reference descriptions, **When** the fidelity module runs, **Then** it outputs a CLIP similarity score for each pair and calculates the delta between baseline and hybrid methods.
2. **Given** a series of ambiguity scores and their corresponding fidelity deltas, **When** the regression analysis runs, **Then** it identifies a specific knee point (e.g., score X) where the slope of the fidelity improvement curve drops below a defined threshold (e.g., < 0.01) and confirms the model fit via F-test.
3. **Given** the identified knee point, **When** the statistical validation runs, **Then** it performs a permutation test and reports whether the fidelity difference below the threshold is statistically distinguishable from zero (p-value < 0.05).

### Edge Cases

- **What happens when** the CLIP model fails to generate a score for a specific image (e.g., due to format mismatch)? **Then** the system must log the error, skip that specific data point, and proceed with the remaining valid data, ensuring the regression does not fail entirely.
- **How does the system handle** prompts that are syntactically simple but semantically ambiguous (e.g., "The thing")? **Then** the scoring module must assign a score based strictly on the syntactic metrics (low score), and the routing logic must treat it as "low ambiguity," potentially testing the hypothesis that heuristics fail here.
- **What happens when** the piecewise regression cannot find a clear "knee point"? **Then** the system must output a "No Threshold Found" flag if the R² of the best-fit 2-segment model is < 0.85 or if the slope change is < 0.01, and record the maximum observed fidelity delta across the entire range.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute an ambiguity score (0.0–1.0) for every input prompt using only syntactic complexity (parse tree depth, clause count) and lexical diversity (MTLD), explicitly excluding semantic embeddings (See US-1).
- **FR-002**: System MUST classify prompts into "low," "medium," or "high" ambiguity categories by applying deterministic thresholds (< 0.2, 0.2–0.6, > 0.6) to the computed Ambiguity Score (See US-2).
- **FR-003**: System MUST route "low" and "medium" ambiguity prompts to a rule-based context expansion module and "high" ambiguity prompts to a simulated full agentic execution pipeline (See US-2).
- **FR-004**: System MUST compute "Context Fidelity" scores for all generated images using a frozen CLIP model (ViT-B/32) against human-verified reference descriptions (See US-3).
- **FR-005**: System MUST perform piecewise linear regression on the "Fidelity Delta" vs. "Ambiguity Score" data to identify the specific "knee point" threshold where agentic advantage vanishes, requiring the piecewise model to be statistically superior to a linear model (F-test p < 0.05) (See US-3).
- **FR-006**: System MUST perform a permutation test (10,000 permutations, alpha = 0.05) to statistically validate whether the fidelity difference below the identified threshold is distinguishable from zero (See US-3).
- **FR-007**: System MUST log all routing decisions, including the input score, assigned category, and target execution path, for traceability (See US-2).
- **FR-008**: System MUST log simulated token counts and latency for both the rule-based and agent paths for every prompt to enable efficiency analysis (See SC-005).
- **FR-009**: System MUST simulate the full agentic execution pipeline using a deterministic mock logic: mock generation time = 15 ms/token + 500ms overhead (See US-2).
- **FR-010**: System MUST perform stratified regression analysis by visual domain (photorealistic, abstract, illustration) to identify domain-specific thresholds (See US-3).

### Key Entities

- **Prompt**: A text input string with associated metadata (source dataset, ambiguity score, routing category).
- **FidelityDelta**: A numeric value representing the difference in CLIP scores between the baseline (full agent) and hybrid execution for a specific prompt.
- **Threshold**: The specific ambiguity score value identified as the "knee point" where the marginal gain in fidelity becomes negligible.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The "Ambiguity Score" is measured against the syntactic and lexical feature vectors derived from the IA-Bench and WISE-Verified datasets (See FR-001).
- **SC-002**: The "Context Fidelity" is measured against the CLIP similarity scores generated from the frozen ViT-B/32 model and human-verified reference descriptions (See FR-004).
- **SC-003**: The "Knee Point Threshold" is measured against the piecewise linear regression curve fitted to the Fidelity Delta vs. Ambiguity Score scatter plot (See FR-005).
- **SC-004**: The statistical significance of the threshold is measured against the p-value derived from the permutation test (See FR-006).
- **SC-005**: The computational efficiency of the hybrid system is measured against the baseline full-agent execution in terms of simulated token count and latency (See FR-008).
- **SC-006**: Domain-specific thresholds are measured against the stratified regression curves for each visual domain (See FR-010).

## Assumptions

- The IA-Bench and WISE-Verified datasets contain a sufficient number of prompts (≥ 2,000) to support statistically valid regression analysis and permutation testing.
- The "simulated full agentic execution" can accurately approximate the latency and token consumption of the real Qwen-Image-Agent pipeline without requiring GPU resources, relying on token counting and mock generation times.
- It is hypothesized that the frozen CLIP model (ViT-B) is CPU-tractable and can process the entire dataset within the standard free-tier time limit of GitHub Actions, assuming the dataset is sampled or processed in batches.; this will be validated during implementation.
- The syntactic complexity metrics (parse tree depth, clause count) are sufficient proxies for "ambiguity" in the context of image generation, independent of semantic meaning.
- The "rule-based context expansion module" can generate plausible context for low-ambiguity prompts using fixed templates without degrading fidelity below the statistical noise floor.
- The "knee point" in the fidelity curve is a real, non-linear phenomenon and not an artifact of the specific dataset or regression method used.