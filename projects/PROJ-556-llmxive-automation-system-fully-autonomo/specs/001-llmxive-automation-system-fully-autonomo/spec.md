# Feature Specification: llmXive Automation System: Fully Autonomous Scientific Discovery Pipeline

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "What structural limitations of current large language models constrain their ability to generate novel, reproducible hypotheses in end-to-end scientific discovery workflows?"

## User Scenarios & Testing

### User Story 1 - Automated Hypothesis Generation and Novelty Scoring (Priority: P1)

The system must ingest standardized scientific datasets and execute the llmXive brainstorming agent to generate research hypotheses, then immediately compute a novelty score by comparing these hypotheses against a local literature corpus to detect rephrased training data artifacts.

**Why this priority**: This is the core value proposition of the project. Without the ability to generate hypotheses and quantitatively distinguish novelty from memorization, the system cannot address the primary research question regarding structural limitations in scientific reasoning.

**Independent Test**: The system can be tested by running the pipeline on a single, small UCI dataset with a fixed seed. The test passes if it outputs a CSV containing the generated hypotheses and their corresponding novelty scores (0.0–1.0) derived from semantic similarity, without requiring code execution or human intervention. This is a "smoke test" validating the pipeline mechanism; the volume is intentionally lower than the full production run (FR-002) to ensure rapid feedback.

**Acceptance Scenarios**:

1. **Given** a valid dataset file (e.g., `uci_breast_cancer.csv`) and a populated local literature index, **When** the brainstorming agent runs with temperature=0.7, **Then** the system outputs at least 10 unique hypothesis strings and a novelty score for each.
2. **Given** a hypothesis that is a near-verbatim copy of a sentence in the literature corpus, **When** the novelty scorer runs, **Then** the system assigns a novelty score ≤ 0.2.
3. **Given** a hypothesis proposing a novel relationship between variables not found in the corpus, **When** the novelty scorer runs, **Then** the system assigns a novelty score ≥ 0.6.

---

### User Story 2 - Reproducibility Validation via Code Execution (Priority: P2)

The system must automatically generate executable Python code for each generated hypothesis, attempt to run it in an isolated environment, and log the outcome (success, dependency error, logical error, or non-deterministic failure) to quantify reproducibility rates.

**Why this priority**: Reproducibility is identified in the literature gap as a primary bottleneck. Measuring the failure rate of generated code is essential to map architectural constraints to empirical failure modes.

**Independent Test**: The system can be tested by taking a single hypothesis, generating the corresponding code, and executing it in a sandboxed container. The test passes if the system correctly categorizes the result as "Pass" or "Fail" and logs the specific error type (e.g., `ModuleNotFoundError`, `AssertionError`, `Timeout`).

**Acceptance Scenarios**:

1. **Given** a hypothesis requiring a standard statistical test (e.g., t-test), **When** the code generator produces a script and the runner executes it, **Then** the system logs "Pass" if the script completes without error and produces deterministic output.
2. **Given** a hypothesis requiring a library not installed in the runner environment, **When** the code runner executes, **Then** the system logs "Fail" with the specific error code `ModuleNotFoundError` and captures the missing dependency name.
3. **Given** a hypothesis where the generated code produces non-deterministic results (e.g., varying outputs on repeated runs due to lack of seed setting), **When** the runner executes the script 3 times, **Then** the system logs "Fail" with the error type `NonDeterministicOutput`.

---

### User Story 3 - Structural Correlation and Statistical Analysis (Priority: P3)

The system must aggregate the results from hypothesis generation and code execution across multiple datasets and ArchConfig variations (e.g., model size, retrieval augmentation) to perform statistical regression and identify correlations between specific LLM configurations and failure rates.

**Why this priority**: This step synthesizes the raw data into the final research finding, directly answering the research question about which structural limitations constrain the system.

**Independent Test**: The system can be tested by providing a pre-generated CSV of results (100+ rows) containing columns for `model_config`, `novelty_score`, and `reproducibility_status`. The test passes if the system outputs a summary report containing p-values and correlation coefficients indicating the relationship between configuration and failure.

**Acceptance Scenarios**:

1. **Given** a dataset of 100+ hypothesis attempts with varied temperature settings, **When** the statistical analysis module runs, **Then** it outputs a p-value and a confidence interval, regardless of whether the result is significant or not.
2. **Given** data comparing models with and without retrieval augmentation, **When** the analysis runs, **Then** it generates a regression coefficient quantifying the improvement in novelty scores attributable to retrieval.
3. **Given** a null result where no ArchConfig variation significantly impacts novelty, **When** the analysis runs, **Then** it explicitly reports "No significant correlation found" with the corresponding confidence interval.

---

### Edge Cases

- **What happens when** the literature corpus is empty or too small to compute meaningful semantic similarity? The system must default novelty scores to 0.5 (neutral) and log a warning that novelty measurement is inconclusive.
- **How does the system handle** a generated hypothesis that requires computational resources exceeding the 7GB RAM limit (e.g., loading a massive dataset into memory)? The system must catch the `MemoryError`, log it as a "ResourceExceeded" failure, and attempt to retry with a random [deferred] sample of the original data rows. This retry is subject to a fixed timeout per attempt, with a maximum total wall-clock time for the hypothesis.
- **What happens when** the LLM generates a hypothesis that is syntactically valid Python but logically impossible (e.g., "correlate variable X with itself to prove Y")? The system must flag this as a `LogicalError` during the static analysis phase before execution.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest standardized datasets (CSV/Parquet) from UCI, OpenML, or HuggingFace and validate schema consistency before processing (See US-1).
- **FR-002**: System MUST generate at least 20 unique valid hypotheses per dataset using configurable LLM parameters (temperature, model size, retrieval toggle), or stop after 15 minutes of generation time, whichever comes first (See US-1).
- **FR-003**: System MUST compute semantic similarity scores between generated hypotheses and a local literature corpus using a CPU-tractable embedding model (e.g., `all-MiniLM-L6-v2`), ensuring the corpus contains only literature published after the LLM's training cutoff date to avoid circular validation (See US-1).
- **FR-004**: System MUST generate executable Python code for each hypothesis and execute it in an isolated, CPU-only sandbox with a 60-second timeout per execution attempt, allowing exactly one retry for `MemoryError` (total max 120s wall-clock) (See US-2).
- **FR-005**: System MUST log execution outcomes with specific error categorization (e.g., `DependencyError`, `RuntimeError`, `NonDeterministic`, `Pass`) (See US-2).
- **FR-006**: System MUST perform statistical regression (paired t-tests or Wilcoxon signed-rank) to correlate ArchConfig variations with novelty and reproducibility metrics (See US-3).
- **FR-007**: System MUST enforce a multiple-comparison correction (e.g., Bonferroni) when testing more than 3 ArchConfig variations to control family-wise error rate (See US-3).
- **FR-008**: System MUST generate and score 5 human-authored hypotheses per dataset (via a separate prompt or manual input) using the same novelty metric to provide a comparative baseline (See US-3).
- **FR-009**: System MUST perform a sensitivity analysis on the novelty metric by varying the embedding model or similarity threshold and report how the correlation between ArchConfig and novelty changes (See US-3).
- **FR-010**: System MUST perform a static analysis check for "plausible but false" claims (e.g., verifying variable existence in the dataset and test appropriateness) before code execution (See US-2).

### Key Entities

- **Hypothesis**: A textual research claim generated by the agent, containing variables, expected relationships, and a unique ID.
- **NoveltyScore**: A float (0.0–1.0) representing the semantic distance between a hypothesis and the literature corpus.
- **ExecutionLog**: A record containing the hypothesis ID, generated code, execution status, error type, and runtime duration.
- **ArchConfig**: A set of parameters defining the LLM run (e.g., `{"model": "llama-3-8b", "temp": 0.7, "rag": true}`).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The rate of hallucinated citations (false references) is measured against the ground-truth literature corpus, defined as a citation not found within a Levenshtein distance of 0.9, to verify the novelty scorer's ability to detect rephrased data (See US-1).
- **SC-002**: The reproducibility failure rate (percentage of generated scripts failing execution) is measured against the total number of generated hypotheses to quantify the primary bottleneck (See US-2).
- **SC-003**: The statistical significance (p-value) of the correlation between model scale and novelty is measured against a standard significance threshold (α=0.05) to validate structural constraints (See US-3).
- **SC-004**: The false-positive rate of the novelty scorer is measured against a manually annotated subset of 50 hypotheses, where a "false positive" is defined as a novelty score ≥ 0.6 where at least one of two independent annotators identifies the hypothesis as a known concept, with inter-rater reliability ≥ 0.8 (Cohen's Kappa), to ensure the metric is not trivially biased (See US-1).
- **SC-005**: The computational cost per hypothesis (CPU seconds) is measured against the 6-hour GitHub Actions limit to ensure the full pipeline of 5 datasets × 20 hypotheses is feasible (See US-3).

## Assumptions

- **Assumption about compute resources**: The analysis will strictly use CPU-only methods (scikit-learn, standard transformers in default precision) and will not require GPU acceleration, low-bit quantization, or mixed-precision training, as the GitHub Actions free tier (2 CPU, 7GB RAM) does not support CUDA.
- **Assumption about dataset availability**: A set of standardized datasets (UCI, OpenML) will be accessible via public APIs without authentication and will fit within the 14GB disk limit of the runner when sampled or subsetted.
- **Assumption about literature corpus**: A local vector index of scientific literature (derived from `lit_search` results) will be pre-populated or generated on-the-fly using small, CPU-efficient embedding models, and will not exceed 2GB in size.
- **Assumption about code generation**: The LLM will be prompted to generate only standard Python code using libraries available in the runner's base environment (e.g., `pandas`, `scipy`, `scikit-learn`), avoiding obscure or proprietary dependencies.
- **Assumption about novelty metric**: Semantic similarity (cosine distance) is assumed to be a valid proxy for "novelty" in this context, acknowledging that it may not capture deep conceptual novelty but serves as a measurable, reproducible metric for this study, provided the corpus is disjoint from the model's training data.
- **Assumption about statistical power**: Given the constraints of the free-tier runner, the sample size (number of hypotheses per dataset) is limited to 20; power analysis will be acknowledged as a limitation if the effect size is small.