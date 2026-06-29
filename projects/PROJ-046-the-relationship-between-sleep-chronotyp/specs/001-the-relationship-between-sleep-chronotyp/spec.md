# Feature Specification: The Relationship Between Sleep Chronotype and Moral Judgement

**Feature Branch**: `feature/chronotype-moral-judgement`  
**Created**: 2026-06-29  
**Status**: Draft  
**Input**: User description:  
*Do individuals with later sleep chronotypes (evening types) exhibit systematically different patterns of moral judgement compared to earlier chronotypes (morning types), independent of acute sleep deprivation?*  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Chronotype Classification (Priority: P1)

*As a researcher, I need to import raw questionnaire data and obtain a reliable chronotype label for each participant so that I can compare moral foundation scores across chronotype groups.*

**Why this priority**: Accurate group assignment is the foundation for any downstream statistical comparison; without it the analysis is invalid.

**Independent Test**: Run the ingestion‑and‑classification script on a sample CSV and verify that the output table contains a `chronotype` column with values “morning”, “intermediate”, or “evening”.

**Acceptance Scenarios**:

1. **Given** a CSV file containing a valid `MEQ_score` column, **When** the script is executed, **Then** each row receives a `chronotype` label according to the predefined thresholds (≥ 59 → morning, ≤ 41 → evening, otherwise intermediate).  
2. **Given** rows with missing or non‑numeric `MEQ_score`, **When** the script is executed, **Then** those rows are flagged with `chronotype = NA` and logged for review.

---

### User Story 2 – Controlled ANOVA with Multiplicity Control (Priority: P2)

*As a researcher, I want to run an ANOVA for each Moral Foundations Questionnaire (MFQ) subscale, controlling for sleep quality and demographics, and apply a family‑wise error correction so that I can test the chronotype effect rigorously.*

**Why this priority**: This analysis directly addresses the research question and must be statistically sound.

**Independent Test**: Execute the analysis module on a pre‑validated dataset and compare the generated ANOVA table to a reference R script; all p‑values must match within 0.01.

**Acceptance Scenarios**:

1. **Given** a cleaned dataset with `chronotype`, `MFQ_*` subscale scores, `PSQI`, `age`, and `sex`, **When** the ANOVA function is called, **Then** it returns an ANOVA table for each subscale, includes covariates, and reports Bonferroni‑adjusted p‑values (α = 0.05/5 = 0.01).  

---

### User Story 3 – Reproducible Reporting & Sensitivity Analysis (Priority: P3)

*As a researcher, I need an automatically generated report that summarises descriptive statistics, effect sizes, confidence intervals, power analysis, and a sensitivity sweep of the Bonferroni threshold, so that results can be communicated and inspected transparently.*

**Why this priority**: Stakeholders (e.g., journal reviewers) require a complete, reproducible artefact; the sensitivity sweep demonstrates robustness to threshold choices.

**Independent Test**: Render the R‑Markdown report on the CI runner and run the validation script; it must confirm presence of all required sections and that the sensitivity table lists results for at least three α‑values.

**Acceptance Scenarios**:

1. **Given** successful execution of the analysis pipeline, **When** the report rendering step finishes, **Then** a PDF (or HTML) file is produced containing: descriptive tables, ANOVA results, Cohen’s d with 95 % CI, a G*Power summary, and a sensitivity table for α ∈ {0.01, 0.0125, 0.015}.

---

### Edge Cases

- **Missing MEQ scores** – rows are marked `chronotype = NA` and excluded from group‑based analyses, with a warning logged.  
- **Intermediate chronotype dominance** – if > 70 % of participants fall into the intermediate category, the pipeline issues a “low‐group‑balance” alert and suggests recruiting additional extreme‑type participants.  
- **Invalid MFQ subscale values** (e.g., out‑of‑range integers) – such rows are removed after a data‑validation step; the report lists the number of exclusions.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest a CSV file containing at least the columns `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `age`, and `sex` (See US-1).  
- **FR-002**: The system MUST compute a `chronotype` label using the thresholds: **morning** if `MEQ_score ≥ 59`, **evening** if `MEQ_score ≤ 41`, otherwise **intermediate** (See US-1).  
- **FR-003**: The system MUST perform a separate one‑way ANOVA for each MFQ subscale with `chronotype` as the factor and `PSQI`, `age`, and `sex` as covariates, applying Bonferroni correction for the five subscales (α = 0.01) (See US-2).  
- **FR-004**: The system MUST calculate Cohen’s d effect sizes and 95 % confidence intervals for any significant chronotype contrast identified after correction (See US-2).  
- **FR-005**: The system MUST generate an R‑Markdown report that includes descriptive statistics, adjusted ANOVA tables, effect‑size tables, a G*Power‑based post‑hoc power estimate, and a sensitivity analysis sweeping the family‑wise α across {0.01, 0.0125, 0.015} (See US-3).  
- **FR-006**: The system MUST log all data‑validation warnings (missing MEQ, out‑of‑range MFQ scores, low group balance) and abort analysis only if > 20 % of rows are unusable (See US-1).  

### Key Entities

- **ParticipantRecord**: represents a single respondent; key attributes are `MEQ_score`, `chronotype`, `MFQ_*` subscale scores, `PSQI`, `age`, `sex`.  
- **AnalysisResult**: encapsulates ANOVA tables, effect‑size summaries, power calculations, and sensitivity sweep outcomes.

## Success Criteria *(mandatory)*

- **SC-001**: Chronotype classification accuracy is ≥ 95 % when compared to a manually coded benchmark dataset (See US-1).  
- **SC-002**: Adjusted p‑values produced by the pipeline differ by ≤ 0.01 from those generated by a reference R script for each of the five MFQ subscales (See US-2).  
- **SC-003**: The generated report passes an automated validation script that checks for presence of (a) descriptive tables, (b) Bonferroni‑adjusted ANOVA output, (c) Cohen’s d with 95 % CI, (d) a power analysis summary, and (e) a sensitivity table covering at least three α values (See US-3).  
- **SC-004**: The sensitivity analysis demonstrates that the set of significant chronotype effects remains unchanged across low α thresholds. (i.e., no reversal of significance) (See US-2).  

## Assumptions

- Participants are recruited in a well‑rested state; PSQI ≤ 5 is used as an inclusion criterion.  
- The Open Science Framework MFQ collection contains the required MFQ subscale scores **[NEEDS CLARIFICATION: does the OSF MFQ dataset also include Morningness‑Eveningness Questionnaire (MEQ) scores?]**. If not, data will be collected via Prolific as described.  
- All analyses are observational; therefore, findings will be framed as **associational** rather than causal.  
- The Bonferroni correction (α = 0.05/5 = 0.01) is the community‑standard method for controlling family‑wise error across the five moral foundations.  
- The analysis runs on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤ 6 h runtime) using base R and the tidyverse/lme4 packages; no GPU or large‑model inference is required.  
- Sample‑size estimation (minimum n = 159) is based on an a‑priori power analysis with effect size f = 0.25, α = 0.05, power = 0.80 (G*Power). The final dataset will meet or exceed this threshold.  
- Predictor collinearity is low because MEQ (chronotype) and MFQ subscales assess distinct constructs; nevertheless, variance inflation factors (VIF) will be reported and must be < 2.
