# Feature Specification: Evaluating LLM Fidelity in Commit-to-Documentation Translation

**Feature Branch**: `001-evaluating-llm-fidelity`  
**Created**: 2026-08-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Use of LLMs for Automated Documentation Generation from Code Commits"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Pairing (Priority: P1)

As a researcher, I need to extract paired data (commit messages and corresponding documentation diffs) from 5 popular open-source repositories so that I have a ground-truth dataset to evaluate LLM performance against.

**Why this priority**: This is the foundational data layer. Without a valid, paired dataset of human-written documentation changes linked to specific commits, no model evaluation can occur. It is the prerequisite for all subsequent analysis.

**Independent Test**: Can be fully tested by running the data extraction script against the 5 target repositories and verifying that the output CSV contains at least 500 rows where each row has a non-empty commit message, a valid commit hash, and a corresponding documentation file diff.

**Acceptance Scenarios**:

1. **Given** a list of 5 target repositories (e.g., `pandas`, `requests`, `scikit-learn`, `flask`, `django`), **When** the extraction script runs, **Then** it outputs a CSV with ≥500 valid (commit_message, doc_diff) pairs filtered for commits that explicitly modified `.md` or `.rst` files.
2. **Given** a commit that modified both code and documentation, **When** the script processes it, **Then** the associated documentation diff is isolated and paired with the commit message, excluding unrelated code changes from the diff content.
3. **Given** a commit with no associated documentation change in the last 2 years, **When** the script processes it, **Then** that commit is excluded from the final dataset to ensure every entry has a ground-truth human reference.

---

### User Story 2 - LLM Inference and Generation (Priority: P2)

As a researcher, I need to generate documentation updates for the extracted commit messages using 3 distinct open-source LLM architectures so that I can compare their ability to capture technical intent versus surface-level details.

**Why this priority**: This implements the core experimental variable (model architecture). It produces the machine-generated outputs required for the fidelity scoring phase.

**Independent Test**: Can be fully tested by running the generation pipeline on a subset of 10 commits and verifying that each model produces a text output that is distinct from the input commit message and formatted as a documentation update.

**Acceptance Scenarios**:

1. **Given** a commit message and the pre-change documentation context, **When** the generation pipeline invokes one of the three specified models (Phi-3-mini, Gemma-2-2b, Llama-3.2-3B), **Then** the model outputs a proposed documentation update.
2. **Given** the same input pair, **When** three different models are invoked, **Then** the system generates three distinct output files, one per model, preserving the original commit ID for traceability.
3. **Given** a model that fails to generate text (e.g., timeout or error), **When** the pipeline encounters this, **Then** it logs the failure with the commit ID and retries the generation up to 2 times before marking the entry as "generation_failed" in the results log.

---

### User Story 3 - Fidelity Scoring and Statistical Analysis (Priority: P3)

As a researcher, I need to calculate precision and recall scores for "technical intent" and "surface-level" entities in the generated text compared to human changes, and perform statistical tests across models, so that I can quantify information loss.

**Why this priority**: This delivers the final research output. It transforms raw text into the quantitative metrics (fidelity scores) required to answer the research question.

**Independent Test**: Can be fully tested by running the analysis script on the generated outputs and verifying that it produces a summary table with mean precision/recall scores for "intent" and "surface" categories per model, and a p-value from a Friedman test.

**Acceptance Scenarios**:

1. **Given** the human documentation diff and the LLM-generated output, **When** the entity extraction parser runs, **Then** it outputs a structured JSON list of entities with text and type (intent or surface), and generates an audit log for manual verification of a 50-sample subset.
2. **Given** the entity counts for all 500 samples across 3 models, **When** the statistical analysis runs, **Then** it calculates precision and recall for each category and performs a Friedman test to test for significant differences between models, with bootstrapping if normality is violated.
3. **Given** the statistical results, **When** the visualization step runs, **Then** it generates a bar chart comparing the intent-to-surface preservation ratio for each model and a confusion matrix of information loss types.

### Edge Cases

- What happens when a commit message is extremely short (e.g., "fix typo") and lacks explicit technical intent? The system must classify this as a "low-intent" sample and exclude it from intent-specific scoring or flag it for separate analysis to avoid skewing the "intent preservation" metric.
- How does the system handle hallucinated entities in the LLM output that do not exist in the commit or the documentation? The scoring logic must treat these as False Positives for "surface" entities if they are valid technical terms found in the codebase, or as "Hallucination" errors if they are not found in the codebase, ensuring they penalize the precision score.
- What happens if a repository has no documentation changes in the last 2 years? The extraction script must skip that repository and log a warning, ensuring the final dataset is constructed from the remaining valid repositories without crashing.

## Requirements

### Non-Functional Requirements

- **NFR-001**: The generation pipeline MUST complete inference for a single commit within 60 seconds on a standard GitHub Actions free-tier runner (2 CPU, ~7GB RAM) (See US-2).

### Functional Requirements

- **FR-001**: System MUST extract at least 500 valid (commit_message, documentation_diff) pairs from 5 specified open-source repositories within a 2-year time window, ensuring each pair has a ground-truth human reference (See US-1).
- **FR-002**: System MUST generate documentation updates for the extracted commit messages using exactly 3 distinct open-source LLM architectures: `Phi-3-mini` (Microsoft), `Gemma-2-2b` (Google), and `Llama-3.2-3B` (Meta), all capable of running on CPU-only hardware (See US-2).
- **FR-003**: System MUST parse both human documentation diffs and LLM-generated outputs to extract and categorize entities using a deterministic taxonomy:
  - **Surface Entities**: Must match regex patterns for file paths (`[a-zA-Z0-9_./-]+\.(py|md|rst)`), function signatures (`def [a-zA-Z_][a-zA-Z0-9_]*\(`), and version numbers (`\d+\.\d+\.\d+`).
  - **Technical Intent Entities**: Must be identified by a zero-shot classifier or rule-based heuristics looking for keywords indicating reasoning (e.g., "because", "fix", "improve", "handle", "prevent") followed by a noun phrase, validated against a human-annotated gold standard subset (See US-3).
- **FR-004**: System MUST calculate precision and recall scores for both "intent" and "surface" categories for every model-sample pair, explicitly distinguishing between information preservation and information loss, using the deterministic definitions in FR-003 as the ground truth (See US-3).
- **FR-005**: System MUST perform a non-parametric Friedman test to statistically compare the fidelity scores across the three model architectures, reporting p-values for differences in intent preservation; if data is normally distributed, a repeated-measures ANOVA MAY be used as a sensitivity check (See US-3).
- **FR-006**: System MUST verify the existence of any "technical term" generated by the LLM against the target repository's codebase (via GitHub API or local clone) to distinguish hallucinated entities (non-existent terms) from valid but unseen terms (See US-3).
- **FR-007**: System MUST exclude any sample from the statistical analysis if the ground-truth human documentation diff is missing for that specific commit, ensuring the "repeated-measures" design only applies to complete data points (See US-3).
- **FR-008**: System MUST create a human-annotated gold standard dataset of 50 samples to validate the accuracy of the "Technical Intent" classification method, requiring an inter-annotator agreement (Cohen's Kappa) of ≥0.6 (See US-3).

### Key Entities

- **CommitPair**: Represents a single data point containing the `commit_hash`, `commit_message`, `repository_name`, and `human_doc_diff`.
- **GeneratedOutput**: Represents the machine-generated documentation update, linked to a `CommitPair` and a specific `model_id`.
- **EntitySet**: A structured collection of extracted entities from a text, tagged as either `type: intent` or `type: surface`, used for calculating fidelity metrics.
- **FidelityMetric**: A record containing the `precision` and `recall` scores for `intent` and `surface` categories for a specific model and sample.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The dataset construction phase MUST yield ≥500 valid (commit_message, doc_diff) pairs from the 5 target repositories, measured against the raw git history of the repositories (See US-1).
- **SC-002**: The generation pipeline MUST successfully produce outputs for ≥90% of the dataset across all 3 models, measured against the total number of input pairs (See US-2).
- **SC-003**: The fidelity scoring module MUST produce distinct precision/recall values for "intent" and "surface" categories for every sample, measured against the ground-truth entity counts from human diffs (See US-3).
- **SC-004**: The statistical analysis MUST identify whether there is a significant difference (p < 0.05) in "intent preservation" scores between the three model architectures using the Friedman test (or ANOVA if assumptions met), measured against the calculated fidelity metrics (See US-3).
- **SC-005**: The analysis MUST quantify the rate of hallucinated entities (False Positives) in the LLM outputs by verifying terms against the codebase, measured against the ground-truth entity set to ensure no fabricated technical details are counted as preserved (See US-3).

## Assumptions

- **Assumption about data availability**: The 5 selected repositories (`pandas`, `requests`, `scikit-learn`, `flask`, `django`) contain sufficient documentation changes in the last 2 years to yield a minimum of 500 valid pairs; if not, the project fails the data acquisition gate.
- **Assumption about compute constraints**: The selected 3 LLMs (Phi-3-mini, Gemma-2-2b, Llama-3.2-3B) can be loaded and run in 4-bit quantization on a GitHub Actions free-tier runner (2 CPU, ~7GB RAM) without requiring GPU acceleration, as these models are optimized for edge/CPU inference.
- **Assumption about entity extraction**: A hybrid approach (rule-based for surface, classifier for intent) combined with a human-annotated gold standard (n=50) can reliably distinguish between "technical intent" and "surface" entities; the classifier's performance is validated against this gold standard.
- **Assumption about statistical validity**: The sample size of 500 pairs is sufficient to perform a Friedman test with adequate power to detect medium effect sizes between models; if power is low, the results will be framed as exploratory associations rather than definitive causal claims.
- **Assumption about model behavior**: The LLMs will not systematically hallucinate technical terms that perfectly mimic valid entities (e.g., inventing a function name that doesn't exist but looks real); such hallucinations will be detectable as False Positives during the entity matching phase via codebase verification.
- **Assumption about dataset-variable fit**: The commit messages in the selected repositories contain sufficient semantic information to distinguish "technical intent" from "surface changes"; if commit messages are purely "fix bug" without context, the "intent" category will be sparse, and the analysis will focus on the "surface" preservation metric.