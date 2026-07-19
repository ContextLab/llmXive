# Specification: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## Overview
This document defines the functional and non-functional requirements for the research pipeline designed to evaluate the usability of computer systems for people with disabilities, specifically focusing on gene regulation interfaces.

## Functional Requirements

### FR-001: Data Collection and Logging
The system MUST collect interaction data including completion time, error counts, and explanation engagement time for both Traditional and Explainable interface variants.

### FR-002: Statistical Analysis Engine
**Ratified Amendment (Approved via Task T035a):**
The system MUST implement a statistical analysis engine using `scipy.stats`. For each metric (Completion Time, Error Count, SUS), the system MUST perform a **Repeated Measures ANOVA** to test for significant differences between interface types. The system MUST apply the **Holm-Bonferroni correction** method to the resulting p-values to control the family-wise error rate. Normality checks (Shapiro-Wilk) may be logged for audit purposes but do not alter the choice of test; ANOVA is the mandated primary method per Constitution Principle VII and Plan, superseding the original Spec text.

*Note: The previous requirement for Levene's test and the T-Test/Wilcoxon decision tree is hereby removed.*

### FR-003: User Interface Rendering
The system MUST render two distinct interface variants: a Traditional interface without overlays and an Explainable interface with XAI overlays (heatmaps, feature importance).

### FR-004: Counterbalancing
The system MUST implement Latin Square counterbalancing to assign the order of interface presentation (Traditional->Explainable or Explainable->Traditional) to mitigate order effects.

### FR-005: Data Cleaning and Validation
The system MUST validate all incoming session data against the schema defined in `contracts/session.schema.yaml`. Incomplete sessions (status='incomplete') MUST be excluded from statistical analysis. SUS scores with missing items MUST be imputed using the participant mean if only one item is missing; otherwise, the session is marked incomplete.

### FR-006: Power Analysis
The system MUST compute statistical power for the observed effect sizes to determine if the sample size was sufficient.

### FR-007: Web-Based Simulator for Human Participants
The system MUST provide a web-based simulator (Streamlit) for human participants to interact with the interfaces and generate real data. Synthetic data is strictly forbidden for final research claims.

## Non-Functional Requirements

### NFR-001: Reproducibility
All analysis must be reproducible. The pipeline must use pinned dependencies and deterministic seeds where applicable.

### NFR-002: Data Integrity
No synthetic data shall be used for final statistical claims. The pipeline must fail loudly if real data is missing in production mode.

## Appendix: Statistical Methodology
- Primary Test: Repeated Measures ANOVA
- Correction: Holm-Bonferroni
- Normality Check: Shapiro-Wilk (Audit only)
- Exclusion: Sessions with status='incomplete'
- Imputation: Participant mean for single missing SUS items