# Research: Evaluating Automated Code Review Tools Effectiveness

## Overview

This research phase validates the feasibility of the data pipeline, identifies verified datasets/sources, and outlines the statistical methodology for evaluating automated code review tools. It explicitly addresses construct validity, statistical power, and metric limitations.

## Dataset Strategy

| Dataset/Source | Description | Verified URL | Usage |
|----------------|-------------|--------------|-------|
| GitHub API | Repository metadata, PR comments, merged PRs | ` Name or service not known)"))] | Primary source for repo selection and human annotation extraction |
| SonarQube Scanner | Static analysis tool | ` | Tool execution (Docker) |
| DeepSource CLI | Static analysis tool | ` | Tool execution (Docker) - **Verified** |
| CodeClimate Engine | Static analysis tool | `https://docs.codeclimate.com/` | Tool execution (Docker) |

**Note**: No external static datasets are used; all data is dynamically fetched from GitHub and tool outputs. DeepSource URL verified by Reference-Validator Agent.

## Methodology

### Data Acquisition (FR-001, FR-002)
- Stratify 30–40 repos by language (Java, Python, JavaScript, Go) and activity (commits <1 year).
- Apply PESTO criteria: license, CI status, issue tracker.
- Clone repos, execute tools via Docker (versions from `code/versions.yaml`).

### Human Baseline & Gold Standard (FR-004, FR-011, FR-012, FR-013)
- **Candidate Generation**:
 1. Keyword heuristics (bug, security, style) to retrieve PR comments (satisfies FR-004).
 2. **Semantic Search**: Use `sentence-transformers` (CPU) to find comments semantically similar to defect patterns.
- **Expert Validation**: Experts validate a stratified random sample of the *combined* candidate set to confirm **actual defects**. This forms the **Gold Standard**.
 - **Validity**: The heuristic is a retrieval filter; the expert defines the ground truth, breaking circularity.
- **Capture-Recapture**: Estimate total defect population size using overlap between tool findings and human comments to contextualize Recall.
- **Metrics**: Cohen's κ on validation. Sensitivity analysis on keyword thresholds.

### Alignment (FR-005)
- **Primary**: AST-based diff matching or Code Embedding similarity (issue description vs. comment text).
- **Threshold**: Match only if confidence > 0.85.
- **Failure Mode**: If confidence < 0.85, mark as **unmatched**. Line tolerance is **not** used for matching to avoid bias.
- **Goal**: Minimize false positives from mere line proximity.

### Metrics & Statistics (FR-006, FR-007, FR-008, FR-009)
- **Metrics**:
 - **Precision**: TP / (TP + FP)
 - **Recall**: **Estimated Recall** (via Capture-Recapture) / Total Estimated Defects.
 - **RCD**: Reported separately as a lower bound.
- **Statistical Tests**:
 - Wilcoxon signed-rank (paired by project).
 - Fixed-effects regression (`metric ~ tool + language + project_size`) with **Cluster-Robust Standard Errors (CRSE)** to handle hierarchical data.
 - **Collinearity Diagnostics**: VIF calculation; if VIF > 5, report with caution or use Ridge regression.
 - **Power Analysis**: Post-hoc power check; if insufficient, prioritize Wilcoxon over regression.
 - **Multiple Comparisons**: Bonferroni correction.

## Statistical Rigor

- **Multiple Comparisons**: Bonferroni correction applied (FR-009).
- **Power & Sample Size**:
 - A sample size of 30–40 repos may be underpowered for complex interactions in regression.
 - **Post-hoc power analysis** will be conducted. If power < 0.8 for interaction terms, regression is used for descriptive trends only; Wilcoxon tests are primary.
 - Primary inference relies on paired Wilcoxon tests to maximize power with limited clusters.
- **Causal Claims**: Observational study; results framed as associational.
- **Validity**:
 - **Construct Validity**: Gold Standard formed by expert validation of *actual defects* (not just keywords).
 - **Metric Validity**: Recall is explicitly defined as "Estimated Recall" via capture-recapture. RCD is reported as a lower bound.
- **Collinearity**: VIF diagnostics mandatory. Language and size may be correlated; results reported with caution if VIF > 5, or Ridge regression applied.
- **Hierarchy**: Cluster-Robust SEs used on Fixed Effects model to handle nested data (issues in repos) without switching to Random Effects.

## Compute Feasibility

- All tools run via Docker on CPU.
- Data subset to fit available RAM.
- Runtime ≤ 5.5 hours (SC-003).
- No GPU, no large model training.
- `sentence-transformers` model used is CPU-optimized (`all-MiniLM-L6-v2`).

## Metric Limitations

- **Recall of Commented Defects (RCD)**: The study cannot measure recall against *all* defects (as most are not commented). RCD measures the tool's ability to find *discussed* defects. Capture-recapture analysis provides an estimate of the total defect population to contextualize this limitation.
- **Power**: With 30–40 clusters, detecting small interaction effects in regression is difficult. The plan prioritizes robust paired tests (Wilcoxon) for primary inference.
