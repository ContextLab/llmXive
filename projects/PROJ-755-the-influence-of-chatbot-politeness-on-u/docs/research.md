# Research Plan: The Influence of Chatbot Politeness on User-Perceived Quality

## Overview
This research investigates the relationship between chatbot politeness and user-perceived quality ratings across multiple dialogue datasets.

## Research Questions
1. Does chatbot politeness significantly predict user-perceived quality ratings?
2. How does this relationship vary across different user demographics (age, gender)?
3. Is the relationship robust to different politeness measurement methods?

## Methodology
- **Primary Analysis**: Cumulative Link Mixed-Effects Models (CLMM)
- **Robustness Check**: LIWC-2015 Politeness Dictionary
- **Subgroup Analysis**: Age and gender stratification
- **Sample Size**: Target n ≥ 30 per subgroup for adequate power

## Data Sources
- Persona-Chat (Primary)
- EmpatheticDialogues (Primary)
- HCI_P2 (Primary)

## Statistical Analysis Plan
1. **Politeness Scoring**: BERT-based politeness classifier
2. **Model Fitting**: CLMM with random effects for user_id
3. **Multiple Comparison Correction**: Benjamini-Hochberg
4. **Robustness**: Correlation of predictions from different politeness measures

## MDE_Estimation
Based on pilot analysis (T011b), the Minimum Detectable Effect (MDE) for the planned sample size is:
- **Minimum Detectable Effect**: 0.15 (standardized units)
- **Power**: 0.80
- **Sample Size**: 500 dialogues per subgroup
- **Confidence Level**: 95%

This MDE ensures sufficient sensitivity to detect meaningful politeness effects while maintaining statistical power for subgroup analyses.

## Timeline
- Phase 1: Setup (Completed)
- Phase 2: Foundational (Completed)
- Phase 3: Data Acquisition (In Progress)
- Phase 4: CLMM Analysis (Pending)
- Phase 5: Robustness Analysis (Pending)