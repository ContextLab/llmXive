# Feature Specification: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Feature Branch**: `001-evaluating-code-summarization-bug-localization`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "Evaluating the Efficacy of Code Summarization Techniques for Bug Localization"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Human Subject Study Data Collection (Priority: P1)

As a researcher, I need to collect participant interaction data (timestamps, line selections, participant IDs) across all three summary conditions (baseline, LLM-generated, rule-based) so that I can evaluate whether code summaries improve bug localization performance.

**Why this priority**: This is the foundational data collection layer. Without participant interaction logs, no statistical analysis or conclusions are possible. This is the MVP that delivers raw research data.

**Independent Test**: Can be fully tested by simulating a sufficient number of tasks per participant for a cohort of participants and verifying the CSV output contains valid timestamps, line selections, and participant IDs for all three conditions.

**Acceptance Scenarios**:

1. **Given** a participant has been assigned 10 tasks per condition via Latin-square design, **When** they complete all 30 tasks (clicking on suspected buggy lines), **Then** a CSV file records timestamps, selected line numbers, and participant IDs for each task.
2. **Given** the Defects4J v2.0 dataset has been downloaded and 60 buggy methods have been extracted, **When** a participant completes a task, **Then** the ground-truth buggy line from Defects4J is stored alongside the participant's selection for later accuracy comparison.
3. **Given** a participant session is in progress, **When** the participant clicks a line number, **Then** the system records the timestamp (in milliseconds) from task display to click.

---

### User Story 2 - Statistical Analysis Pipeline (Priority: P2)

As a researcher, I need to run McNemar's tests for accuracy and Linear Mixed-Effects (LME) models for speed, comparing baseline vs. LLM summary and baseline vs. rule-based summary, with effect sizes (Odds Ratio and Cohen's d) and 95% confidence intervals via bootstrapping (a sufficient number of resamples, fixed seed), so that I can determine statistical significance while accounting for repeated measures.

**Why this priority**: This transforms raw data into publishable results. Without statistical analysis, the collected data has no interpretive value. This is P2 because it depends on P1 data collection being complete.

**Independent Test**: Can be fully tested by feeding a synthetic CSV dataset and verifying the analysis outputs p-values, effect sizes (Odds Ratio, Cohen's d), and 95% confidence intervals for all four comparisons (accuracy baseline→LLM, speed baseline→LLM, accuracy baseline→rule, speed baseline→rule).

**Acceptance Scenarios**:

1. **Given** a complete CSV with 12 participants × 30 tasks each, **When** the statistical analysis pipeline runs, **Then** McNemar's tests produce p-values for accuracy comparisons and LME models produce p-values for speed comparisons.
2. **Given** the statistical test results, **When** effect sizes are computed, **Then** Odds Ratios (for accuracy) and Cohen's d (for speed) with 95% confidence intervals via bootstrapping (1,000 resamples, fixed seed) are generated for each comparison.
3. **Given** multiple hypothesis tests are performed, **When** the analysis completes, **Then** a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) is applied to control family-wise error rate at α=0.05.

---

### User Story 3 - Reproducibility Package Generation (Priority: P3)

As a researcher, I need to publish all analysis scripts (Python 3.11, pandas, scikit-learn, requests, statsmodels) and anonymized interaction logs on an OSF repository with a README detailing how to rerun the analysis within a GitHub Actions job (≤6h runtime, ≤7GB RAM), so that the study is reproducible and verifiable.

**Why this priority**: This ensures long-term research integrity and enables peer review. It depends on P1 and P2 being complete (data + analysis exist). This is P3 because the core research question can be answered without the reproducibility package, though it's required for publication.

**Independent Test**: Can be fully tested by cloning the OSF repository, running the analysis script in a GitHub Actions free-tier runner, and verifying the output matches the original results within a 5% numerical tolerance.

**Acceptance Scenarios**:

1. **Given** the analysis scripts and anonymized CSV logs are prepared, **When** a GitHub Actions job executes the analysis, **Then** the job completes within 6 hours on a free-tier runner (2 CPU cores, ~7GB RAM, ~14GB disk, NO GPU).
2. **Given** the reproducibility package is published, **When** a third party runs the analysis, **Then** the output matches the original results (p-values, effect sizes, confidence intervals) within a small numerical tolerance.
3. **Given** the README is complete, **When** a reader follows the instructions, **Then** they can rerun the full analysis pipeline without requiring additional data downloads or configuration beyond what is documented.

---

### Edge Cases

- What happens when a participant drops out mid-study (incomplete task set)? The system must mark the participant's data as partial and exclude them from paired analyses requiring complete data, logging the dropout count.
- How does the system handle missing ground-truth buggy line information from Defects4J? The task must be flagged and excluded from accuracy calculations, with a count of excluded tasks logged.
- What happens when the LLM summary generation fails for a method (e.g., API timeout, empty output)? The task must fall back to the rule-based summary for that participant, with a flag indicating the fallback occurred.
- How does the system handle participants who complete tasks outside the expected time window (e.g., >30 minutes per task)? Those tasks must be flagged as potential outliers and included in sensitivity analysis (excluding participants with ≥2 outliers).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download Defects4J v2.0 dataset and extract a stratified sample of buggy methods across Java projects (Chart, Time, Math), storing the ground-truth buggy line for each method (See US-1).
- **FR-002**: System MUST generate three summary variants per buggy method: (a) no summary (baseline), (b) LLM-generated summary via HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization, (c) rule-based summary via srcML comment extractor. If LLM generation fails (timeout >30 seconds, empty output, or non-text), the system MUST log the error and automatically fall back to the rule-based summary for that task (See US-1).
- **FR-003**: System MUST record participant interaction data in a CSV file with columns: participant_id, task_id, condition (baseline/LLM/rule), timestamp_ms, selected_line, ground_truth_line. The system MUST perform a local loopback latency test at startup to verify the timestamp recording mechanism achieves ≤100ms precision (See US-1).
- **FR-004**: System MUST perform McNemar's tests for accuracy (binary outcome) and Linear Mixed-Effects (LME) models with random intercepts for participants for speed (time-to-decision), comparing baseline vs. LLM and baseline vs. rule-based, with significance threshold α=0.05 (See US-2).
- **FR-005**: System MUST compute effect sizes (Odds Ratio for McNemar's, Cohen's d for LME) and 95% confidence intervals via bootstrapping with a sufficient number of resamples and a fixed random seed for all four comparison pairs (See US-2).
- **FR-006**: System MUST apply multiple-comparison correction (Bonferroni or Holm-Bonferroni) to control family-wise error rate at α=0.05 when >1 hypothesis test is performed (See US-2).
- **FR-007**: System MUST generate a reproducibility package containing all Python 3.11 scripts (pandas, scikit-learn, requests, statsmodels), anonymized interaction logs, and a README. The analysis script MUST complete within 6 hours on a standard GitHub Actions free-tier runner (≤7GB RAM, NO GPU) and include a CI test procedure to verify this constraint (See US-3).

### Key Entities *(include if feature involves data)*

- **Participant**: Represents a graduate-level software engineering student; key attributes: participant_id (anonymized), condition_assignments (Latin-square balanced), dropout_status.
- **Task**: Represents a bug localization instance; key attributes: task_id, buggy_method_id, condition (baseline/LLM/rule), ground_truth_line, participant_selection, timestamp_ms.
- **Summary**: Represents a code summary variant; key attributes: summary_id, method_id, summary_type (none/LLM/rule-based), summary_text.
- **AnalysisResult**: Represents statistical output; key attributes: comparison_pair (e.g., baseline_vs_LLM_accuracy), p_value, effect_size_odds_ratio, effect_size_cohens_d, confidence_interval_95%, correction_applied.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Median time-to-decision is measured against the baseline (no summary) condition to evaluate speed improvement (See US-2).
- **SC-002**: Correct-first-line identification rate is measured against the baseline (no summary) condition to evaluate accuracy improvement (See US-2).
- **SC-003**: Statistical significance (p<0.05) is measured against the McNemar's test and LME model results for each comparison pair to evaluate hypothesis support (See US-2).
- **SC-004**: Reproducibility is measured against the original analysis output by verifying that rerun results (p-values, effect sizes, confidence intervals) match within a 5% numerical tolerance using a fixed random seed (See US-3).
- **SC-005**: Compute feasibility is measured against the GitHub Actions free-tier constraint (≤6h runtime, ≤7GB RAM, NO GPU) to validate analysis runs in CI (See US-3).

---

## Assumptions

- Participants are graduate-level software engineering students with ≥2 years of Java development experience, recruited remotely via secure web form.
- The DefectsJ dataset contains all required variables: buggy method source code, ground-truth buggy line numbers, and official bug report text for all sampled methods.
- LLM summary generation via HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization completes within 30 seconds per method on CPU; if exceeded, the task falls back to rule-based summary.
- The study uses a Latin-square design to control order effects; 12 participants × 30 tasks each = 360 total task observations.
- Statistical analysis runs on CPU-only GitHub Actions free-tier (limited core allocation, ~7GB RAM, ~14GB disk); no GPU, CUDA, or 8-bit quantization is used for the *analysis* (only for LLM inference).
- Multiple-comparison correction uses Holm-Bonferroni method (family-wise error rate controlled at α=0.05 across 4 tests).
- Sensitivity analysis sweeps the statistical significance threshold over a range of standard cutoffs and reports how the headline p-values vary across these levels.
- Participant dropout rate is assumed ≤15% (≤2 participants); partial data from dropouts is excluded from paired analyses.
- All code and anonymized logs will be published on OSF repository with a permissive license (CC-BY 4.0).
- The system records timestamps with a precision of ≤100ms as verified by the local loopback calibration test at startup.