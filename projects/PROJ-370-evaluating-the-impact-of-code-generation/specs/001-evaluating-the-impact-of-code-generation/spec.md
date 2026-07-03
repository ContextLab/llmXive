# Feature Specification: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Feature Branch**: `001-eval-llm-review-quality`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance"

## User Scenarios & Testing

### User Story 1 - Automated PR Data Extraction and Preprocessing (Priority: P1)

The system must automatically fetch pull request diffs, review comments, and linked issues from 3-5 specified open-source GitHub repositories, extracting the code changes and associated human annotations to create a structured dataset for analysis.

**Why this priority**: This is the foundational data ingestion step. Without a clean, structured dataset of code diffs and ground-truth bug labels, no subsequent analysis or comparison can occur. It delivers the raw material required for the entire research pipeline.

**Independent Test**: The system can be tested by running the extraction script against a single, known repository (e.g., `microsoft/vscode`) for a fixed set of 10 PRs and verifying that the output JSON contains valid diffs, review comments, and linked issue IDs with no parsing errors.

**Acceptance Scenarios**:

1. **Given** a list of target repositories and a PR range, **When** the extraction script runs, **Then** it outputs a JSON file containing 10 PR objects, each with `diff`, `human_review_comments`, and `linked_issue_ids` fields populated correctly.
2. **Given** a PR with no linked issues, **When** the extraction script processes it, **Then** the `linked_issue_ids` field is populated as an empty list rather than causing a crash or null error.

---

### User Story 2 - LLM-Assisted Bug Detection Simulation (Priority: P2)

The system must process the extracted code diffs using a CPU-tractable open-source LLM (e.g., StarCoder2-3B) with a standardized prompt to generate bug reports, including severity classifications (critical, major, minor, style), and output these findings in a structured format aligned with the human baseline.

**Why this priority**: This implements the core experimental condition (LLM-assisted review). It transforms the raw data into the "LLM review" signal required for the comparative analysis against human reviews.

**Independent Test**: The system can be tested by feeding a specific test fixture `test-fixtures/bug-synth-001.json` (containing a known bug at line 42) into the LLM inference pipeline and verifying that the output JSON contains a detected bug with a severity label and the correct file/line location.

**Acceptance Scenarios**:

1. **Given** a code diff containing a syntax error, **When** the LLM inference pipeline processes it, **Then** the output JSON includes a bug detection with severity "critical" or "major" and the correct file/line location.
2. **Given** a code diff with no obvious bugs, **When** the LLM inference pipeline processes it, **Then** the output JSON either contains no bug detections or flags the code as "no issues found" without hallucinating non-existent errors.

---

### User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

The system must align LLM-detected bugs with human-annotated bugs using code location and description similarity, then compute precision, recall, F1-scores, and perform statistical tests (McNemar's, chi-square) to compare detection rates and severity distributions, outputting a final research report.

**Why this priority**: This delivers the research answer. It synthesizes the data from the previous steps into the quantitative metrics and statistical evidence required to answer the research question.

**Independent Test**: The system can be tested by running the analysis script on a small, manually constructed dataset of 5 PRs with known LLM and human bug labels, verifying that the output report correctly calculates precision/recall and reports the statistical test p-values.

**Acceptance Scenarios**:

1. **Given** two datasets of bug detections (LLM and Human) for the same 10 PRs, **When** the analysis script runs, **Then** the output report includes a table with Precision, Recall, and F1-score for the LLM model compared to the human baseline.
2. **Given** a comparison of severity distributions between LLM and Human reviews, **When** the analysis script runs, **Then** the output report includes the result of a chi-square test with a p-value indicating whether the distributions are significantly different.

---

### Edge Cases

- **What happens when** a PR diff is too large for the LLM context window? **How does system handle**: The system MUST truncate the diff to the most recently changed lines and log a warning that the analysis is partial.
- **How does system handle** missing or inaccessible GitHub issue data for a linked issue? **How does system handle**: The system MUST mark the specific bug label as "unverified" in the human baseline and exclude it from the ground-truth calculation, logging the issue ID.
- **What happens when** the LLM fails to generate a valid JSON response due to formatting errors? **How does system handle**: The system MUST retry the inference up to 2 times with a 1-second delay; if it still fails, it MUST record the PR as "LLM error" and skip it for the final metric calculation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract PR diffs, review comments, and linked issue IDs from 3-5 specified GitHub repositories, limiting the total dataset to ≤ 500 PRs to fit within memory constraints. Linked issues MUST be explicitly labeled as "reported" but not assumed as ground truth without further validation (See US-1).
- **FR-002**: System MUST run a CPU-tractable LLM (e.g., StarCoder2-3B) on each PR diff using a standardized prompt to generate bug reports with severity labels (critical, major, minor, style) (See US-2).
- **FR-003**: System MUST align LLM-detected bugs with human-annotated bugs using a combination of exact file/line range matching and cosine similarity on bug descriptions. The default threshold for primary reporting is ≥ 0.85, but the system MUST support variable thresholds for sensitivity analysis (See US-3).
- **FR-004**: System MUST compute Precision, Recall, and F1-scores for bug detection by comparing LLM outputs against the triangulated ground truth (See US-3).
- **FR-005**: System MUST perform McNemar's test to compare detection rates and chi-square tests for severity distribution differences, reporting p-values (See US-3).
- **FR-006**: System MUST implement a sensitivity analysis that sweeps the description similarity threshold over {0.80, 0.85, 0.90} and reports how the F1-score varies across these values (See US-3).
- **FR-007**: System MUST frame all findings as associational, avoiding causal claims, as the study design is observational without random assignment (See US-3).
- **FR-011**: System MUST define "ground truth" via a triangulated standard: a bug is considered ground truth if it is (a) linked to a GitHub issue AND (b) confirmed by at least two independent human reviewers (or a senior maintainer) in the review comments (See US-1).
- **FR-012**: System MUST enforce a strict binary decision rule for alignment before statistical testing: a match is valid ONLY if (similarity ≥ threshold AND location overlap ≥ 0.5). Location overlap MUST be calculated as the Jaccard index of the line sets (lines in LLM bug ∩ lines in Human bug) / (lines in LLM bug ∪ lines in Human bug) (See US-3).
- **FR-013**: System MUST enforce a maximum runtime of 6 hours per execution. If the runtime exceeds this limit, the system MUST log a timeout warning and gracefully skip remaining PRs (See US-1).
- **FR-014**: System MUST explicitly state in the final report that the term "affect" in the research question is interpreted as "correlate with" due to the observational design (See US-3).
- **FR-015**: System MUST define "CPU-tractable" as: max memory usage ≤ 7GB and max latency per PR ≤ 5 minutes (See US-2).
- **FR-016**: System MUST detect and flag code generated by LLMs (using heuristic detection or metadata) within PR diffs to distinguish between reviewing human-written vs. LLM-generated code (See US-2).
- **FR-017**: System MUST report "Recall relative to the triangulated ground truth" (defined in FR-011), ensuring the LLM can be credited for finding bugs humans missed (See US-3).

### Key Entities

- **PullRequest**: Represents a GitHub PR, containing attributes: `pr_id`, `repo_name`, `diff_text`, `human_review_comments`, `linked_issue_ids`.
- **BugDetection**: Represents a detected bug, containing attributes: `source` (LLM or Human), `file_path`, `line_start`, `line_end`, `severity`, `description`.
- **AlignmentResult**: Represents the match between an LLM and Human bug, containing attributes: `llm_bug_id`, `human_bug_id`, `match_score`, `match_type` (exact or fuzzy).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The bug detection rate (Precision/Recall) of the LLM-assisted review is measured against the human-only review baseline (See US-3).
- **SC-002**: The distribution of severity classifications (critical, major, minor, style) between LLM and human reviews is measured using a chi-square test to determine statistical significance (See US-3).
- **SC-003**: The stability of the alignment results is measured by sweeping the similarity threshold over {0.80, 0.85, 0.90} and reporting the variance in F1-scores (See FR-006).
- **SC-004**: The computational feasibility is measured by recording the total runtime for 500 PRs on a 2-CPU runner and comparing it against a target threshold (to be determined during analysis) (See Methodology Sketch).

## Assumptions

- **Assumption about data**: The selected open-source repositories (e.g., `microsoft/vscode`, `pytorch/pytorch`) contain sufficient PRs with linked issues and explicit review comments to support a sample size of 200-500 PRs.
- **Assumption about LLM capability**: The chosen open-source LLM (e.g., StarCoder2-3B) can be loaded and run in default precision on a 2-CPU, 7GB RAM runner without requiring GPU acceleration or 8-bit quantization.
- **Assumption about alignment**: Code location (file + line range) is a reliable primary key for matching bugs between LLM and human reviews, with description similarity serving as a secondary validation step.
- **Assumption about ground truth**: The study uses a "triangulated" approach: linked issues are the primary proxy for ground truth, but human review comments are also used to validate bugs when linked issues are absent, ensuring a more robust ground truth.
- **Assumption about network**: The GitHub Actions runner has stable internet connectivity to fetch data from the GitHub API and HuggingFace model hub within a standard job duration.