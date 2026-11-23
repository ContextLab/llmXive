# Feature Specification: llmXive follow-up: extending "Leveraging Verifier-Based Reinforcement Learning in Image Editing"

**Feature Branch**: `001-llmxive-verifier-graph`  
**Created**: 2026-07-09  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Leveraging Verifier-Based Reinforcement Learning in Image Editing'"

## User Scenarios & Testing

### User Story 1 - Baseline Verifier Evaluation on Conflicting Instructions (Priority: P1) (US-1)

The researcher MUST be able to run the baseline distilled verifier (Edit-R1 1B) on a curated dataset of a sizable collection of image editing prompts (target balanced numbers of conflicting and neutral prompts) and generate a CSV report containing the verifier's alignment scores against human‑annotated feasibility scores for each prompt.

**Why this priority**: This establishes the failure mode hypothesis. Without quantifying the baseline degradation on conflicting instructions, the proposed graph augmentation cannot be evaluated. It is the essential control condition for the entire study.

**Independent Test**: The researcher runs the baseline evaluation script on the dataset without the graph module enabled and verifies the output CSV contains non‑null alignment scores for all input samples.

**Acceptance Scenarios**:

1. **Given** a dataset of image editing prompts with ground‑truth human feasibility scores, **When** the baseline evaluation script is executed, **Then** a CSV file is generated containing a substantial number of rows where each row includes prompt ID, instruction type (conflicting/neutral), verifier score, human score, and alignment delta.
2. **Given** the baseline evaluation script, **When** run on the conflicting instruction subset, **Then** the script calculates and reports the mean alignment delta (verifier − human) for the conflicting subset and the neutral subset, and outputs these values to the report.

### User Story 2 - Symbolic Constraint Graph Construction (Priority: P2) (US-2)

The system MUST parse natural language instructions into directed constraint graphs using CPU‑only NLP libraries (spaCy, networkx) and a rule‑based contradiction detection module (e.g., antonym matching), identifying nodes (principles) and edges (temporal dependencies or contradictions), and output these graphs as structured JSON context for the verifier. The conflicting‑instruction dataset is built by augmenting the single‑step InstructPix2Pix shards with algorithmically generated contradictory pairs (e.g., pairing “add a tree” with “remove the tree”) and manually verifying the presence of genuine conflicts.

**Why this priority**: This is the core innovation (the intervention). The graph module must function independently of the neural verifier to ensure it is a valid preprocessing layer. It provides the structural guidance hypothesized to mitigate reasoning degradation.

**Independent Test**: The researcher provides a set of multiple conflicting instructions to the parser module and verifies the output JSON contains valid graph structures with identified contradiction edges and temporal dependencies. The total CPU runtime for the curated dataset of instructions must be ≤ 30 minutes on a standard 2‑core runner, and no GPU memory is allocated.

**Acceptance Scenarios**:

1. **Given** a natural language instruction containing explicit contradictions (e.g., "Make the sky blue and keep it dark"), **When** the symbolic parser processes it, **Then** the output JSON contains at least two nodes representing the conflicting principles and an edge labeled "contradiction" connecting them.
2. **Given** a natural language instruction with temporal dependencies (e.g., "First remove the car, then add a tree"), **When** the symbolic parser processes it, **Then** the output JSON contains nodes for each step and a directed edge labeled "temporal-precedes" indicating the correct order.
3. **Given** the curated dataset of instructions, **When** the parser processes them, **Then** the total CPU runtime is ≤ 30 minutes on a standard 2‑core runner, and no GPU memory is allocated.

### User Story 3 - Graph‑Augmented Verifier Evaluation and Statistical Comparison (Priority: P3) (US-3)

The researcher MUST be able to execute the graph‑augmented evaluation, feeding the generated constraint graphs into the verifier's prompt template, and perform a paired statistical test (t‑test or Wilcoxon) to compare alignment scores between the baseline and graph‑augmented conditions.

**Why this priority**: This validates the hypothesis that the symbolic preprocessing mitigates the degradation. It delivers the final scientific result of the project.

**Independent Test**: The researcher runs the full graph‑augmented pipeline on the conflicting subset and verifies the statistical test output shows a significant improvement in alignment scores compared to the baseline.

**Acceptance Scenarios**:

1. **Given** the baseline alignment scores and the graph‑augmented alignment scores for the conflicting instructions, **When** the statistical analysis script is executed, **Then** a report is generated containing the p‑value of the paired test, the effect size (Cohen's d), and a 95 % confidence interval for the improvement.
2. **Given** the graph‑augmented verifier, **When** evaluated on the conflicting subset, **Then** the system calculates and reports the difference in average alignment scores between the graph‑augmented and baseline conditions.
3. **Given** the statistical analysis, **When** run, **Then** the analysis confirms that the improvement is not due to chance (p < 0.05) and reports the 95 % confidence interval for the improvement.

### Edge Cases

- What happens when the symbolic parser fails to identify any contradictions in a prompt that is labeled as "conflicting" in the ground truth? (The system must log a warning and proceed with a null graph, ensuring the pipeline does not crash).
- How does the system handle instructions with ambiguous temporal dependencies where the order is not explicitly stated? (The parser must default to a "no-order" edge or a heuristic‑based inference, documented in the output).
- What happens if the verifier times out or crashes on a specific prompt? (The system must skip the sample, log the error, and continue processing the remaining dataset without halting the entire job).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and curate a balanced collection of a sizable number of prompts (approximately equal numbers of conflicting and neutral) **and collect human‑annotated feasibility scores for at least 200 prompts** via crowd‑sourcing, storing the results in `data/results/human_validation.csv`. (See US-1)
- **FR-002**: System MUST implement a CPU‑only symbolic parser using standard NLP libraries (e.g., spaCy, networkx) and a rule‑based contradiction detection module (e.g., antonym matching) to parse natural language instructions into directed constraint graphs, identifying nodes (principles) and edges (temporal dependencies or contradictions). The conflicting‑instruction dataset is created by augmenting InstructPix2Pix shards with algorithmically generated contradictory pairs and manually verifying conflicts. (See US-2)
- **FR-003**: System MUST execute the baseline distilled 1B‑parameter Edit‑R1 verifier on raw prompts and measure alignment against the *human‑annotated* feasibility scores collected per FR‑009. (See US-1)
- **FR-004**: System MUST feed the generated constraint graphs as structured context into the verifier's prompt template and re‑run the evaluation to measure the change in alignment with human scores. (See US-3)
- **FR-005**: System MUST apply a paired t‑test or Wilcoxon signed‑rank test to compare the alignment scores between the baseline and graph‑augmented conditions for the conflicting instruction subset, reporting p‑values, effect sizes, and 95 % confidence intervals. (See US-3)
- **FR-006**: System MUST implement a robustness check by testing on a hold‑out set of conflicts generated with different linguistic phrasings to verify the improvement is not driven by overfitting to specific prompt syntax. (See US-3)
- **FR-009**: System MUST collect human feasibility scores for **at least 200 prompts** by presenting each prompt to crowd‑workers and recording a plausibility rating on a 0‑1 scale; the aggregated rating constitutes the independent ground‑truth feasibility score and is saved to `data/results/human_validation.csv`. (See US-1)
- **FR-010**: System MUST ensure that any synthetic feasibility scores generated for exploratory analysis are **not** used for evaluation or statistical comparison; evaluation must rely exclusively on the human‑annotated scores from FR‑009/FR‑001. (See US-1, US-3)

### Key Entities

- **Instruction**: A natural language prompt for image editing, classified as either "conflicting" or "neutral".
- **Constraint Graph**: A directed graph representation of an instruction, where nodes represent principles and edges represent temporal or contradictory relationships.
- **Alignment Score**: The absolute difference between the verifier’s plausibility output (scaled 0‑1) and the human‑annotated feasibility score (0‑1) for a given instruction; lower values indicate better alignment.
- **Feasibility Score**: A ground‑truth human‑annotated score indicating the logical feasibility of the instruction's edit outcome. For conflicting instructions, this is defined as the degree of partial compliance or plausibility of the non‑conflicting component.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The average alignment score difference (Graph‑Augmented minus Baseline) on the conflicting instruction subset is measured against the null hypothesis of zero difference using a paired statistical test. (See US-3)
- **SC-002**: The runtime of the symbolic parser on the curated dataset is measured against the 30‑minute CPU budget constraint defined in User Story 2. (See US-2)
- **SC-003**: The memory footprint of the entire analysis pipeline is measured against the 7 GB RAM limit of the GitHub Actions free‑tier runner. (See US-2, US-3)
- **SC-004**: The statistical significance (p‑value) of the improvement in alignment scores is measured against the 0.05 threshold for rejecting the null hypothesis. (See US-3)
- **SC-005**: The robustness of the graph‑augmented verifier is measured against the difference in Cohen's d effect sizes between the primary test set and the hold‑out set, requiring no statistically significant drop (p ≥ 0.05) in the effect size. (See US-3)
- **SC-006**: Baseline verifier average alignment score on the conflicting subset (against human scores) is reported with mean ± SD. (See US-1)
- **SC-009**: Baseline verifier runtime on the full 1 000‑prompt dataset must be ≤ 2 hours on a CPU‑only runner with ≤ 7 GB RAM. (See US-1)
- **SC-010**: Baseline verifier average alignment score on the conflicting subset must be reported (mean ± SD) and used as the reference point for improvement calculations. (See US-1)

## Assumptions

- **Dataset Availability & Construction**: The public InstructPix2Pix shards provide a large pool of single‑step editing instructions. We will algorithmically pair or modify these instructions to create multi‑step and contradictory prompts, then manually verify a subset to ensure genuine conflict. This curated process yields the required set of conflicting and neutral prompts in equal quantities.
- **Model Compatibility**: The distilled 1B‑parameter Edit‑R1 verifier can be loaded and executed on a CPU‑only environment with 7 GB RAM without requiring CUDA or quantization libraries that force GPU usage.
- **NLP Library Reliability**: Standard Python NLP libraries (spaCy, networkx) combined with a rule‑based contradiction detection module are sufficient to parse the semantic structure of image editing instructions into valid constraint graphs without requiring specialized large‑language‑model‑based parsers.
- **Statistical Power**: With **at least 200** human‑annotated prompts (≈ 100 conflicting, 100 neutral), the paired test may have limited power to detect a medium effect size (Cohen's d ≈ 0.5). Observed power will be reported alongside results; the study is primarily exploratory.
- **Threshold Justification**: The significance threshold of p < 0.05 is used as a community‑standard default for hypothesis testing in this domain; no additional sensitivity analysis on this threshold is required.
- **Data Fit**: The dataset of image prompts and associated metadata fits within the disk space limits of the free‑tier runner when processed in batches, and remains within the 7 GB RAM limits.
