# Feature Specification: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

**Feature Branch**: `001-llmxive-verifier-graph`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Leveraging Verifier-Based Reinforcement Learning in Image Editing'"

## User Scenarios & Testing

### User Story 1 - Baseline Verifier Evaluation on Conflicting Instructions (Priority: P1)

The researcher MUST be able to run the baseline distilled verifier (Edit-R1 1B) on a curated dataset of [deferred] image editing prompts (500 conflicting, 500 neutral) and generate a CSV report containing the verifier's alignment scores against human-annotated feasibility scores for each prompt.

**Why this priority**: This establishes the failure mode hypothesis. Without quantifying the baseline degradation on conflicting instructions, the proposed graph augmentation cannot be evaluated. It is the essential control condition for the entire study.

**Independent Test**: The researcher runs the baseline evaluation script on the dataset without the graph module enabled and verifies the output CSV contains non-null alignment scores for all [deferred] samples.

**Acceptance Scenarios**:

1. **Given** a dataset of [deferred] image editing prompts with ground-truth human feasibility scores, **When** the baseline evaluation script is executed, **Then** a CSV file is generated containing [deferred] rows with columns for prompt ID, instruction type (conflicting/neutral), verifier score, human score, and alignment delta.
2. **Given** the baseline evaluation script, **When** run on the 500 conflicting instruction subset, **Then** the average alignment delta (verifier - human) is statistically significantly lower (p < 0.05) than the average delta on the 500 neutral subset.

---

### User Story 2 - Symbolic Constraint Graph Construction (Priority: P2)

The system MUST parse natural language instructions into directed constraint graphs using CPU-only NLP libraries (spaCy, networkx), identifying nodes (principles) and edges (temporal dependencies or contradictions), and output these graphs as structured JSON context for the verifier.

**Why this priority**: This is the core innovation (the intervention). The graph module must function independently of the neural verifier to ensure it is a valid preprocessing layer. It provides the structural guidance hypothesized to mitigate reasoning degradation.

**Independent Test**: The researcher provides a set of 50 conflicting instructions to the parser module and verifies the output JSON contains valid graph structures with identified contradiction edges and temporal dependencies.

**Acceptance Scenarios**:

1. **Given** a natural language instruction containing explicit contradictions (e.g., "Make the sky blue and keep it dark"), **When** the symbolic parser processes it, **Then** the output JSON contains at least two nodes representing the conflicting principles and an edge labeled "contradiction" connecting them.
2. **Given** a natural language instruction with temporal dependencies (e.g., "First remove the car, then add a tree"), **When** the symbolic parser processes it, **Then** the output JSON contains nodes for each step and a directed edge labeled "temporal-precedes" indicating the correct order.
3. **Given** [deferred] instructions, **When** the parser processes them, **Then** the total CPU runtime is ≤ 30 minutes on a standard 2-core runner, and no GPU memory is allocated.

---

### User Story 3 - Graph-Augmented Verifier Evaluation and Statistical Comparison (Priority: P3)

The researcher MUST be able to execute the graph-augmented evaluation, feeding the generated constraint graphs into the verifier's prompt template, and perform a paired statistical test (t-test or Wilcoxon) to compare alignment scores between the baseline and graph-augmented conditions.

**Why this priority**: This validates the hypothesis that the symbolic preprocessing mitigates the degradation. It delivers the final scientific result of the project.

**Independent Test**: The researcher runs the full graph-augmented pipeline on the conflicting subset and verifies the statistical test output shows a significant improvement in alignment scores compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the baseline alignment scores and the graph-augmented alignment scores for the 500 conflicting instructions, **When** the statistical analysis script is executed, **Then** a report is generated containing the p-value of the paired test and the effect size (Cohen's d).
2. **Given** the graph-augmented verifier, **When** evaluated on the conflicting subset, **Then** the average alignment score is at least 0.15 higher than the baseline average for the same subset.
3. **Given** the statistical analysis, **When** run, **Then** the analysis confirms that the improvement is not due to chance (p < 0.05) and reports the 95% confidence interval for the improvement.

### Edge Cases

- What happens when the symbolic parser fails to identify any contradictions in a prompt that is labeled as "conflicting" in the ground truth? (The system must log a warning and proceed with a null graph, ensuring the pipeline does not crash).
- How does the system handle instructions with ambiguous temporal dependencies where the order is not explicitly stated? (The parser must default to a "no-order" edge or a heuristic-based inference, documented in the output).
- What happens if the verifier times out or crashes on a specific prompt? (The system must skip the sample, log the error, and continue processing the remaining dataset without halting the entire job).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and curate a synthetic dataset of image editing prompts (including conflicting and neutral examples) paired with ground-truth edit outcomes and human-annotated feasibility scores from a public repository. (See US-1)
- **FR-002**: System MUST implement a CPU-only symbolic parser using standard NLP libraries (e.g., spaCy, networkx) to parse natural language instructions into directed constraint graphs, identifying nodes (principles) and edges (temporal dependencies or contradictions). (See US-2)
- **FR-003**: System MUST execute the baseline distilled 1B-parameter Edit-R1 verifier on raw prompts to measure the baseline failure rate and correlation with human feasibility scores. (See US-1)
- **FR-004**: System MUST feed the generated constraint graphs as structured context into the verifier's prompt template and re-run the evaluation to measure the change in alignment with human scores. (See US-3)
- **FR-005**: System MUST apply a paired t-test or Wilcoxon signed-rank test to compare the alignment scores between the baseline and graph-augmented conditions for the conflicting instruction subset, reporting p-values and effect sizes. (See US-3)
- **FR-006**: System MUST implement a robustness check by testing on a hold-out set of conflicts generated with different linguistic phrasings to verify the improvement is not driven by overfitting to specific prompt syntax. (See US-3)
- **FR-007**: System MUST perform a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if more than one hypothesis test is conducted on the alignment metrics to control the family-wise error rate. (See US-3)
- **FR-008**: System MUST ensure all analysis steps (parsing, inference, statistics) complete within a 6-hour runtime on a CPU-only runner with ≤ 7 GB RAM. (See US-2, US-3)

### Key Entities

- **Instruction**: A natural language prompt for image editing, classified as either "conflicting" or "neutral".
- **Constraint Graph**: A directed graph representation of an instruction, where nodes represent principles and edges represent temporal or contradictory relationships.
- **Alignment Score**: A quantitative metric (0.0 to 1.0) representing the correlation between the verifier's output and the human-annotated feasibility score for a given instruction.
- **Feasibility Score**: A ground-truth human-annotated score indicating the logical feasibility of the instruction's edit outcome.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The average alignment score difference (Graph-Augmented minus Baseline) on the conflicting instruction subset is measured against the null hypothesis of zero difference using a paired statistical test. (See US-3)
- **SC-002**: The runtime of the symbolic parser on [deferred] prompts is measured against the 30-minute CPU budget constraint. (See US-2)
- **SC-003**: The memory footprint of the entire analysis pipeline is measured against the 7 GB RAM limit of the GitHub Actions free-tier runner. (See US-2, US-3)
- **SC-004**: The statistical significance (p-value) of the improvement in alignment scores is measured against the 0.05 threshold for rejecting the null hypothesis. (See US-3)
- **SC-005**: The robustness of the graph-augmented verifier is measured against the performance drop on the hold-out set of linguistically varied conflicts compared to the primary test set. (See US-3)

## Assumptions

- **Dataset Availability**: The public repository (e.g., InstructPix2Pix subset) contains sufficient examples of multi-step conflicting instructions and neutral controls to construct the [deferred]-sample dataset with ground-truth human feasibility scores. If the source lacks explicit human feasibility scores, a proxy metric or synthetic labeling protocol will be used, and this limitation will be recorded as a `[NEEDS CLARIFICATION]` item if the gap is unresolvable.
- **Model Compatibility**: The distilled 1B-parameter Edit-R1 verifier can be loaded and executed on a CPU-only environment with 7 GB RAM without requiring CUDA or quantization libraries that force GPU usage.
- **NLP Library Reliability**: Standard Python NLP libraries (spaCy, networkx) are sufficient to parse the semantic structure of image editing instructions into valid constraint graphs without requiring specialized large-language-model-based parsers.
- **Statistical Power**: The sample size of 500 conflicting instructions provides sufficient statistical power (≥ 0.8) to detect a medium effect size (Cohen's d ≥ 0.5) in the paired comparison, assuming a significance level of 0.05. If the effect size is smaller, the study will report the power limitation.
- **Threshold Justification**: The significance threshold of p < 0.05 is used as a community-standard default for hypothesis testing in this domain; no additional sensitivity analysis on this threshold is required as it is a standard statistical convention.
- **Data Fit**: The dataset of image prompts and associated metadata fits within the 14 GB disk space and 7 GB RAM limits of the free-tier runner when processed in batches.
