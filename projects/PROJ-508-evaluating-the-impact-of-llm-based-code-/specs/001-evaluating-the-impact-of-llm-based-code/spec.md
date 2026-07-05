# Specification: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

## Project Overview
This study investigates the association between LLM-based code completion adoption and developer cognitive load, using proxy metrics derived from version control and code review data.

## Functional Requirements

### FR-001: Data Ingestion
The system MUST ingest repository metadata, pull requests, commits, and code review threads from GitHub.

### FR-002: Iteration Counting
The system MUST count TOTAL push events between PR open and merge (no exclusions).
*Note: This requirement was updated in T007 to remove circular bias exclusions.*

### FR-003: Statistical Modeling
The system MUST use Mixed-Effects Models (GLMM) with random intercepts for repositories.
For zero-inflated outcomes (reverts/iterations), the system MUST use Zero-Inflated Negative Binomial (ZINB) or Hurdle models.
*Note: This requirement was updated in T006 to replace linear regression with appropriate GLMM/ZINB models.*

### FR-004: Multiple Comparison Correction
The system MUST apply Bonferroni correction for multiple hypothesis testing.

### FR-005: Data Validation
The system MUST scan for PII and validate schema compliance before analysis.

### FR-006: Reporting
The system MUST generate a final report with forest plots, sensitivity analysis, and explicit framing of findings as associational.

### FR-007: LLM Adoption Flagging
The system MUST flag repositories as "LLM Adopters" based on:
- Presence of `.cursorrules` or `copilot` config files
- Mentions of "Copilot"/"LLM" in README/CONTRIBUTING
- ≥5% frequency of "Copilot"/"LLM" in commit messages

### FR-008: Diff Complexity and AI Noise Detection
The system MUST calculate `diff_complexity_score` = (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0.
The system MUST flag 'AI Noise' if `diff_complexity_score` > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'.
*Rationale: This requirement was added in T004 to enable Signal Separation analysis (Phase 6) addressing Feynman's concern about distinguishing "fixing AI's mess" load from "solving the problem" load.*

### FR-009: Theoretical Grounding and Data Gap Disclosure
The final report MUST include a 'Theoretical Grounding' section citing Holland et al. on distributed cognition.
The final report MUST include a 'Data Gap' section explicitly stating the unavailability of self-report scales (e.g., NASA-TLX).
*Rationale: This requirement was added in T005 to ensure methodological transparency.*

## Success Criteria

### SC-001: Repository Filtering
Repositories with <10 PRs in the last 12 months MUST be excluded.

### SC-002: Data Quality
All metrics must be validated against schema before analysis.

### SC-003: Statistical Significance
Results must report coefficients, standard errors, p-values, adjusted p-values, and confidence intervals.

### SC-004: Visualization Quality
Forest plots must be publication-ready with proper labels and confidence intervals.

### SC-005: Sensitivity Analysis
The system MUST sweep `iteration_count` threshold over a range of low integer values and record effect estimates.

### SC-006: Reproducibility
All analysis must be reproducible via `code/analyze.py` with a single command.

### SC-007: API Documentation
The manifest must include all data sources, parameters, and timestamps.

### SC-008: Stratified Signal Separation Analysis
The analysis must produce a stratified result showing how the 'LLM Adoption' effect size changes when controlling for 'AI Noise' or when filtering for specific commit types.
*Rationale: This criterion was added in T004 to address Feynman's concern about the inability to separate "fixing AI's mess" load from "solving the problem" load. It authorizes the Signal Separation analysis in Phase 6.*

### SC-009: Explicit Proxy Metric Disclosure
The report must explicitly state: "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."
*Rationale: This criterion was added in T005 to ensure transparency about measurement limitations.*

## Data Model
- **Repository**: id, name, language, domain_complexity, llm_adoption_flag
- **PullRequest**: id, repo_id, created_at, merged_at, iteration_count, avg_comment_length, review_thread_depth
- **Commit**: id, pr_id, message, lines_added, lines_deleted, diff_complexity_score, is_ai_noise
- **AnalysisResult**: model_type, coefficient, se, p_value, adjusted_p_value, ci_lower, ci_upper

## Constraints
- CPU-only execution (no GPU)
- No fabricated data; all metrics must be derived from real GitHub API responses
- Observational study design (no causal claims)
- All code must be type-hinted and linted with ruff/black