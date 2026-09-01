# Feature Specification: llmXive follow-up: extending "ResearchStudio-Idea: An Evidence-Grounded Research-Ideation Skill Suit"

**Feature Branch**: `001-llmxive-extension`  
**Created**: 2026-07-23  
**Status**: Draft  
**Input**: User description: "Do the 15 'ideation patterns' derived from top-tier machine learning conferences generalize to improve the quality of research proposals in resource-constrained, non-ML domains (e.g., public health policy, climate adaptation), or are these patterns specific artifacts of ML research culture?"

## User Scenarios & Testing

### User Story 1 - Corpus Acquisition and Pre-processing (Priority: P1)

The system must successfully ingest and prepare abstracts from both ML and non-ML domains to establish the baseline dataset for comparison. Without this data, no pattern mapping or evaluation can occur.

**Why this priority**: This is the foundational data layer. If the system cannot retrieve or process a sufficient quantity of ML and non-ML abstracts, the entire research question regarding pattern universality cannot be tested.

**Independent Test**: The system can be tested by verifying that the dataset directory contains a representative set of processed JSON files (including accepted and rejected cases) with valid metadata fields (title, abstract, venue, acceptance_status) and that the data fits within the 7 GB RAM constraint.

**Acceptance Scenarios**:

1. **Given** the system is configured with URLs for *Nature Climate Change*, *Health Affairs*, and the ML corpus, **When** the data acquisition script runs, **Then** it must download a substantial set of abstracts (approximately equal proportions of ML, non-ML accepted, and non-ML rejected) and store them in a structured format without data loss.
2. **Given** the downloaded raw text, **When** the pre-processing pipeline executes, **Then** it must normalize the text (remove headers/footers) and validate that every entry has a non-empty abstract field, rejecting any malformed entries with a clear error log.
3. **Given** the dataset is fully loaded into memory, **When** the memory usage is monitored, **Then** it must not exceed a size compatible with the available memory to ensure headroom for the embedding model on the constrained RAM runner.

### User Story 2 - Pattern Mapping and Proposal Generation (Priority: P2)

The system must map non-ML problem statements to a curated set of ML-derived ideation patterns using a CPU-tractable embedding model and generate two sets of proposals: one guided by these patterns and one baseline.

**Why this priority**: This is the core experimental manipulation. It tests the hypothesis by applying the specific intervention (ML patterns) against a control (generic prompts) to see if the patterns transfer.

**Independent Test**: The system can be tested by running the generation pipeline on a small subset (e.g., 5 problems) to verify the *logic* of pattern injection and baseline generation; however, the full functional requirement (FR-003) mandates the generation of 50 pairs for the complete study. The test verifies the code path is correct before scaling to the full dataset.

**Acceptance Scenarios**:

1. **Given** a non-ML problem statement and the 15 ML pattern cards, **When** the semantic similarity engine runs (using `all-MiniLM-L6-v2` quantized on CPU), **Then** it must identify and inject the top-3 matching patterns into the LLM prompt for the experimental group.
2. **Given** the same non-ML problem statement, **When** the baseline prompt is executed (generic "be creative" instruction), **Then** the resulting proposal must lack any structural constraints derived from the ML pattern cards.
3. **Given** the generation process, **When** the system executes on the GitHub Actions runner, **Then** it must complete the generation of 50 experimental and 50 baseline proposals (100 total) within 4 hours, utilizing batch processing to stay within 7 GB RAM limits.

### User Story 3 - Expert Evaluation and Statistical Analysis (Priority: P3)

The system must aggregate expert ratings for feasibility, bottleneck identification, and contextual alignment, then perform a statistical test to determine if the pattern-guided proposals differ significantly from the baseline.

**Why this priority**: This delivers the final answer to the research question. It transforms raw human feedback into a statistically valid conclusion about pattern universality.

**Independent Test**: The system can be tested by feeding it a pre-defined set of dummy ratings (e.g., 50 pairs of scores) to verify the statistical logic, AND by verifying the recruitment pipeline successfully ingests real expert ratings with blinded metadata.

**Acceptance Scenarios**:

1. **Given** a CSV of expert ratings for 50 pairs of proposals (each rated by ≥3 experts), **When** the analysis script runs, **Then** it must perform a normality check and automatically select either a paired t-test or Wilcoxon signed-rank test based on the distribution of mean scores.
2. **Given** the test results, **When** the report is generated, **Then** it must explicitly state the p-value, the effect size, and the conclusion regarding the null hypothesis (that there is no difference in quality).
3. **Given** multiple hypothesis tests (e.g., testing feasibility, bottleneck, and alignment separately), **When** the analysis completes, **Then** it must apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to the reported p-values to control the family-wise error rate.

### Edge Cases

- What happens if the non-ML abstracts from the target venues are not publicly accessible via direct URL (e.g., paywalled)? The system must fail gracefully with a clear error message indicating which venue failed, rather than proceeding with incomplete data.
- How does the system handle a scenario where the embedding model fails to load due to memory constraints on the specific runner instance? The system must implement a fallback to a smaller, lighter model (e.g., `all-MiniLM-L6-v2`) and log the switch.
- What if the expert raters provide inconsistent or extreme outliers in their Likert scores? The analysis must include a sensitivity analysis that re-runs the statistical test with outliers removed to ensure the conclusion is robust.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse a balanced set of accepted and rejected abstracts from specified non-ML venues and an equivalent set from the ML corpus., ensuring all entries contain valid title and abstract fields (See US-1).
- **FR-002**: System MUST compute semantic similarity between non-ML problem statements and the 15 ML-derived pattern cards using a CPU-only quantized embedding model (e.g., `all-MiniLM-L6-v2`) to retrieve top-3 candidates for prompting (See US-2).
- **FR-003**: System MUST generate a set of research proposals using ML patterns as structural constraints and a corresponding set of control proposals using generic prompts. For each of the unique non-ML problem statements, the system MUST generate exactly one pattern-guided proposal and one baseline proposal to ensure valid pairing (See US-2).
- **FR-004**: System MUST aggregate expert ratings on a Likert scale for feasibility, bottleneck identification, and contextual alignment. Experts MUST be verified via ORCID and have ≥5 years of domain experience. Ratings MUST be collected via blind evaluation (proposals stripped of generation metadata), with a minimum of 3 independent experts per proposal (See US-3).
- **FR-005**: System MUST perform a statistical comparison (paired t-test or Wilcoxon signed-rank) between pattern-guided and baseline proposals (using mean scores), including a multiple-comparison correction for the three evaluation metrics (See US-3).
- **FR-006**: System MUST explicitly include the phrase "associational, not causal" in the final conclusion section of the generated report to satisfy the rhetorical constraint (See US-3).

### Key Entities

- **Abstract**: Represents a research proposal text with metadata (title, venue, acceptance status, domain).
- **PatternCard**: Represents one of the 15 ML-derived ideation patterns with a description and structural constraints.
- **Proposal**: Represents a generated research idea, tagged with its source (pattern-guided or baseline) and associated problem statement.
- **Rating**: Represents an expert's score for a specific proposal on a specific metric (feasibility, bottleneck, alignment).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in mean expert ratings for "contextual alignment" between pattern-guided and baseline proposals is measured against the null hypothesis of no difference (See FR-005).
- **SC-002**: The false-positive rate due to multiple hypothesis testing is measured against the standard alpha level after applying family-wise error correction (See FR-005).
- **SC-003**: The computational feasibility of the entire pipeline is measured against the constraint of ≤6 hours runtime on a 2-core, 7 GB RAM GitHub Actions runner (See FR-003).
- **SC-004**: The validity of the pattern mapping is measured by the downstream expert "contextual alignment" scores (not the retrieval score), ensuring that pattern-guided proposals achieve a statistically significant improvement over baseline (See FR-004, FR-005). Note: The retrieval step uses cosine similarity with a threshold of ≥ 0.6 to select patterns, but this is a retrieval mechanism, not a validity metric.

## Assumptions

- The 15 ML-derived ideation patterns are sufficiently abstract to be applicable to non-ML domains like public health and climate adaptation, or their inapplicability will be detectable as a significant drop in "contextual alignment" scores.
- The dataset of abstracts (ML and non-ML) is representative of the broader research landscape in their respective fields and contains no systematic bias that would invalidate the comparison.
- The `all-MiniLM-L6-v2` (quantized) model can operate within the 7 GB RAM limit of the GitHub Actions runner when processing the dataset in batches.
- The expert raters recruited for the evaluation will have sufficient domain expertise in public health or climate adaptation to provide valid assessments of "feasibility" and "contextual alignment."
- The LLM used for proposal generation (via API or local quantized model) will not introduce hallucinations that systematically bias the "bottleneck identification" metric in favor of either the pattern-guided or baseline group.
- The 6-hour time limit on the GitHub Actions runner is sufficient to complete the embedding, generation, and statistical analysis steps, assuming efficient batching and no network latency spikes.
- The statistical power of the test (n=50 pairs, 3 raters per proposal) is sufficient to detect a medium effect size (Cohen's d ≈ 0.5) at α=0.05, accounting for expected inter-rater variance in creative evaluation.