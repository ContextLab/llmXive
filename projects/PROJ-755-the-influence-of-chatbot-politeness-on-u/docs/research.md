# Research Plan: The Influence of Chatbot Politeness on User-Perceived Quality

## Overview
This research investigates the relationship between chatbot politeness and user-perceived quality in dialogue systems. We utilize the HCI_P2 dataset and employ Cumulative Link Mixed-Effects Models (CLMM) to analyze the data while controlling for confounding variables.

## Research Questions
1. Does higher politeness in chatbot responses correlate with higher user-perceived quality ratings?
2. How does conversation length moderate the relationship between politeness and quality?
3. Are there significant differences in this relationship across demographic subgroups (age, gender)?

## Methodology
### Data Source
- **Primary Dataset**: HCI_P2 (Human-Computer Interaction, Phase 2)
- **Variables**: `quality_rating`, `politeness_score`, `conversation_length`, `user_id`, `age`, `gender`

### Statistical Analysis
- **Primary Model**: Cumulative Link Mixed-Effects Model (CLMM)
- **Formula**: `quality_rating ~ politeness + conversation_length + (1|user_id)`
- **Robustness Check**: Lexicon-based scoring (LIWC-2015 or textstat fallback)
- **Correction**: Benjamini-Hochberg for multiple comparisons

## MDE_Estimation

- **Minimum Detectable Effect (MDE)**: 0.15
- **Statistical Power**: 0.80
- **Sample Size Used**: 1000

### Details

- **Estimated Effect Size**: 0.12
- **Significance Level (alpha)**: 0.05
- **Test Type**: Two-tailed

---