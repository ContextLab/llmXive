# Specification: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Version
1.0.0

## Overview
This document defines the functional and scientific requirements for a study analyzing the impact of Large Language Model (LLM) code completion tools on developer cognitive load. The study utilizes observational data from GitHub repositories to correlate LLM adoption signals with proxy metrics for cognitive load (e.g., iteration count, review depth).

## Functional Requirements

### FR-001: Data Ingestion
The system MUST ingest data from GitHub repositories, including commit history, pull request metadata, and configuration files.

### FR-002: Iteration Count Calculation [UPDATED by T007]
The system MUST calculate `iteration_count` as the total number of push events between PR open and merge.
**Constraint**: NO exclusions based on commit message content (e.g., "Copilot") or diff size.

### FR-003: Statistical Modeling [UPDATED by T006]
The system MUST utilize Mixed-Effects Models (GLMM) with random intercepts for repositories.
For zero-inflated outcomes (e.g., reverts, low iteration counts), the system MUST apply Zero-Inflated Negative Binomial (ZINB) or Hurdle models.
Linear regression is explicitly deprecated for these specific outcomes.

### FR-004: Multiple Comparison Correction
The system MUST apply Bonferroni correction to p-values to control for family-wise error rate when testing multiple cognitive load proxies.

### FR-005: LLM Adoption Flagging
The system MUST flag a repository as "LLM Adopter" if:
- It contains `.cursorrules` or `copilot` configuration files.
- OR commit messages contain "Copilot"/"LLM" keywords with frequency >= 5%.
- OR README/CONTRIBUTING files explicitly mention LLM usage.

### FR-006: Control Variables
The system MUST include project size (LOC), team size (contributors), and domain complexity as control variables in statistical models.

### FR-007: Sensitivity Analysis
The system MUST perform sensitivity analysis by sweeping the `iteration_count` threshold to test robustness of effect sizes.

### FR-008: Signal Separation & AI Noise Detection [NEW - Added per T004]
The system MUST calculate `diff_complexity_score` = (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0.
The system MUST flag a commit as "AI Noise" if `diff_complexity_score` > 0.3 AND the commit message contains "fix", "hotfix", or "patch".
This metric is used to distinguish between "solving a problem" and "fixing AI-generated mess".

## Scientific Constraints

### SC-001: Repository Filtering
Repositories with fewer than 10 Pull Requests in the last 12 months MUST be excluded from the analysis.

### SC-002: Data Privacy
All Personally Identifiable Information (PII) must be scanned and removed before storage in derived datasets.

### SC-003: Associational Framing
All findings MUST be framed as associational. The study design does not support causal claims.

### SC-004: Zero-Inflation Handling
Models must explicitly account for the high frequency of zero values in metrics like `revert_frequency`.

### SC-005: VIF Threshold
Variables with a Variance Inflation Factor (VIF) > 5.0 MUST be flagged for potential multicollinearity.

### SC-006: Report Transparency
The final report MUST include a "Limitations" section detailing the observational nature of the study and the use of proxy metrics.

### SC-007: Theoretical Grounding
The report MUST cite Holland et al. regarding distributed cognition to ground the interpretation of cognitive load proxies.

### SC-008: Signal Separation Analysis [NEW - Added per T004]
The analysis must produce a stratified result showing how the 'LLM Adoption' effect size changes when controlling for 'AI Noise' or when filtering for specific commit types.
This addresses the confounding variable of "fixing AI's mess" vs "solving the problem".

### SC-009: Data Gap Disclosure [Added per T005]
The report must explicitly state: "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."

## Data Model

The system operates on the following primary entities:
- `Repository`: Metadata, adoption flag, domain complexity.
- `PullRequest`: Iteration count, review depth, comment length.
- `Commit`: Diff complexity, AI noise flag, message content.

## Output Artifacts

1. `data/derived/master_dataset.csv`: Cleaned, aggregated dataset.
2. `data/derived/analysis_results.json`: Statistical model coefficients and p-values.
3. `docs/output/final_report.pdf`: Publication-ready report with visualizations.