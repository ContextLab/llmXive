# Implementation Plan: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Branch**: `001-gene-regulation` | **Date**: 2026-06-25 | **Spec**: `specs/001-improving-accessibility-and-usability-of/spec.md`
**Input**: Feature specification from `/specs/001-improving-accessibility-and-usability-of/spec.md`

## Summary
This project implements a reproducible research pipeline to evaluate the impact of Explainable AI (XAI) interfaces on usability for people with disabilities. The system consists of a web-based task simulator (Traditional vs. Explainable variants), a data collection engine, and a statistical analysis module. The analysis pipeline will perform normality checks (Shapiro-Wilk), utilize **Repeated Measures ANOVA** as the primary test for superiority (per Constitution Principle VII), apply Holm-Bonferroni correction for multiple comparisons, and generate publication-quality visualizations via `matplotlib`. All artifacts will be reproducible on a CPU-only GitHub Actions runner.

**Scope Adjustment**: The primary research question is scoped to the **aggregate population** to align with the N=30 power constraint. Subgroup analysis (by disability type) is strictly exploratory and underpowered.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `scipy` (statistics), `matplotlib` (visualization), `pandas` (data manipulation), `jupyter` (reproducibility), `streamlit` (simulator interface - lightweight CPU option)
**Storage**: Local CSV/JSON files under `data/` (checksummed)
**Testing**: `pytest` (unit tests for statistical logic), manual verification of notebook execution
**Target Platform**: Linux (GitHub Actions Free Tier: CPU, 7GB RAM)
**Project Type**: Research Pipeline / Web-based Simulator
**Performance Goals**: Analysis of ~1000 rows in < 5 minutes; Simulator response < 200ms
**Constraints**: No GPU; No heavy LLM inference in the loop; Data must fit in < 7GB RAM; All random seeds pinned.
**Scale/Scope**: Single study dataset (N=30 target), single statistical pipeline.

## Constitution Check

*Gates determined based on `projects/PROJ-015-improving-accessibility-and-usability-of/.specify/memory/constitution.md`*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `requirements.txt` pins, random seed fixing, and a single executable Jupyter notebook (`code/analysis.ipynb`). |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` are restricted to the "Verified datasets" block provided in the prompt. No external URLs will be invented. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data, immutable raw storage, and separate derived files. PII exclusion logic is defined. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated dynamically from `data/` via the notebook; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded in the project state file upon artifact generation. |
| **VI. Participant Representation** | **PASS** | The plan explicitly logs `disability_type` and flags power limitations if N < 30 for subgroups, aligning with the recruitment assumption. |
| **VII. Standardized Metrics** | **PASS** | The plan implements SUS, completion time, and error rates. **Statistical analysis uses Repeated Measures ANOVA** to satisfy this principle, superseding the Spec's T-Test mandate for this specific design. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── session.schema.yaml
    └── analysis_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-015-improving-accessibility-and-usability-of/
├── data/
│   ├── raw/             # Raw session logs (immutable, checksummed)
│   └── processed/       # Cleaned CSVs for analysis
├── code/
│   ├── simulator/       # Streamlit app for UI rendering (Traditional/XAI)
│   ├── analysis/        # Statistical logic and visualization scripts
│   └── analysis.ipynb   # Reproducible end-to-end notebook
├── tests/
│   ├── unit/            # Statistical function tests
│   └── contract/        # Schema validation tests
└── requirements.txt     # Pinned dependencies
```

**Structure Decision**: Single-project structure is selected. The simulator and analysis are distinct modules within the same repository to ensure tight coupling between data generation and analysis, facilitating the reproducibility requirement (Constitution Principle I).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | The complexity is minimal. The statistical rigor (ANOVA, Holm-Bonferroni) is mandated by the Constitution and scientific best practice for this design, not an architectural over-engineering choice. |

## Implementation Phases

### Phase 1: Data Collection & Simulation Setup
- **Objective**: Deploy the simulator and collect data with proper counterbalancing.
- **Action**:
  1.  **Counterbalancing**: Implement a **Latin Square** design. Participants are assigned to one of two sequences: `Traditional -> Explainable` or `Explainable -> Traditional`. This explicitly controls for order effects (learning/fatigue) as required by methodological rigor.
  2.  **Simulator**: Build the `code/simulator/` Streamlit app.
      - **Traditional Interface**: Standard HCI task interface.
      - **Explainable Interface**: Renders the same task but overlays XAI visualizations.
      - **XAI Rendering Mechanism**: The "explanation" is generated via a **deterministic, rule-based simulation** (not a learned surrogate model). Task difficulty is mapped to visual intensity (e.g., heatmap opacity) to ensure the "explanation" is a synthetic signal tied to the task, eliminating construct validity threats from inaccurate surrogate models.
  3.  **Data Logging**: Log `participant_id`, `disability_type`, `interface_type`, `sequence`, `start_time`, `end_time`, `error_count`, `explanation_engagement_time_seconds`, `sus_score`, and `status`.
  4.  **Dropout Handling**: Log `dropout_reason` for any `incomplete` sessions. This logging is a **measured output** for SC-005 validation.

### Phase 2: Data Cleaning & Validation
- **Objective**: Prepare data for analysis.
- **Action**:
  1.  **Filter**: Exclude sessions with `status != 'complete'`.
  2.  **Imputation**: If SUS has ≤1 missing item, impute with participant mean. If >1, reject session.
  3.  **Verification**: Verify the presence of `dropout_reason` logs for all excluded sessions to satisfy SC-005.

### Phase 3: Statistical Analysis
- **Objective**: Test hypotheses with scientific rigor.
- **Action**:
  1.  **Normality Check**: Perform **Shapiro-Wilk test** ($\alpha=0.05$) on the **difference scores** (Explainable - Traditional) for each metric.
      - *Note on Spec Conflict*: The Spec (FR-002) mentions Levene's test. However, Levene's test is methodologically inappropriate for paired designs (assumes independent groups). The Plan follows scientific best practice (Shapiro-Wilk on differences) and the Constitution's rigor requirement, flagging the Spec's Levene's mandate as a conflict to be resolved via kickback.
  2.  **Primary Test**: Perform **Repeated Measures ANOVA** for each metric (Completion Time, Error Count, SUS Score).
      - *Note on Spec/Constitution Conflict*: The Spec (FR-002) mandates T-Test/Wilcoxon. However, Constitution Principle VII explicitly mandates "ANOVA analysis". For a within-subjects design with multiple dependent variables, ANOVA is the standard method. The Plan implements ANOVA to satisfy the Constitution, noting this supersedes the Spec's specific test selection logic for this context.
  3.  **Post-Hoc**: If ANOVA is significant, perform pairwise comparisons with **Holm-Bonferroni correction**.
  4.  **Exclusion**: **Exclude `explanation_engagement_time` from inferential testing**. Comparing this metric against a constant zero (Traditional) is tautological. It will be reported descriptively only. This corrects the scientific validity issue in the Spec's FR-002 list.
  5.  **Output**: Generate `data/processed/metrics_summary.csv` with ANOVA F-statistic, p-value, adjusted p-value, and effect size.

### Phase 4: Visualization & Reporting
- **Objective**: Generate reproducible figures and reports.
- **Action**:
  1.  **Visualization**: Use `matplotlib` to generate box plots comparing metrics (Traditional vs. Explainable) with error bars.
  2.  **Notebook**: Compile `code/analysis.ipynb` to document the entire pipeline from raw data to figures.
  3.  **Validation**: Ensure the notebook runs end-to-end on the free-tier runner.

## Risk Management

- **Power Limitation**: If N < 30, the report will explicitly state that subgroup analysis is exploratory and underpowered. The primary claim is limited to the aggregate population.
- **Spec-Plan Conflict**: The Spec (FR-002) mandates T-Test/Wilcoxon and Levene's test, while the Constitution (Principle VII) mandates ANOVA. The Plan follows the Constitution (ANOVA) and scientific best practice (Shapiro-Wilk only, no Levene's). This discrepancy is flagged for a Spec kickback to align FR-002 with the Constitution and scientific rigor.