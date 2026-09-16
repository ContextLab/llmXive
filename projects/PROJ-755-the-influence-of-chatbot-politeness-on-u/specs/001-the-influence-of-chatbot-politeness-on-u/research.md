# Research: Chatbot Politeness and User Trust

## Research Questions

1.  Is there a statistically significant association between chatbot politeness and user-perceived quality/trust?
2.  Does the relationship between politeness and trust vary by user age and gender?
3.  Are the findings consistent across different politeness classifiers (BERT vs. LIWC)?

## Dataset Strategy

| Dataset Name | Source URL | Variables Needed |
|---|---|---|
| Persona-Chat | [https://huggingface.co/datasets/pixelsandpointers/empathetic_dialogues_for_lm/resolve/main/data/test-00000-of-00001.parquet](https://huggingface.co/datasets/pixelsandpointers/empathetic_dialogues_for_lm/resolve/main/data/test-00000-of-00001.parquet) | Dialogue text, quality ratings, user ID |
| EmpatheticDialogues | [https://huggingface.co/datasets/ia-bentebib/empathetic_dialogues_fr/resolve/main/data/test-00000-of-00001.parquet](https://huggingface.co/datasets/ia-bentebib/empathetic_dialogues_fr/resolve/main/data/test-00000-of-00001.parquet) | Dialogue text, quality ratings, user ID |

## Decision/Rationale

*   **CPU-first**: All analysis will be performed on the CPU-tier GitHub Actions runner. The `jfiedler/politeness-bert` model is available for CPU execution. The CLMM will be fit using `lme4` in R, which is CPU-compatible.
*   **Data Availability**: Both datasets are directly downloadable from Hugging Face Datasets, ensuring accessibility.
*   **Statistical Methods**: CLMM is appropriate for ordinal quality ratings. Multiple comparison correction (Bonferroni or Benjamini-Hochberg) will be used to control for Type I error.

## Politeness Measurement

Politeness will be measured using the `jfiedler/politeness-bert` model. Utterances will be scored, and the mean score will be calculated for each conversation. Z-scoring will be applied to standardize politeness scores. A secondary analysis will use the LIWC-2015 Politeness Dictionary for comparison.

## Statistical Analysis Plan

1.  **Data Preparation**: Download, validate, and filter the datasets. Compute politeness scores and standardize them.
2.  **CLMM Fitting**: Fit a CLMM with quality rating as the outcome, politeness score, and conversation length as predictors, and user ID as a random effect.
3.  **Robustness Check**: Repeat the analysis using LIWC politeness scores.
4.  **Subgroup Analysis**: Conduct subgroup analyses by age and gender, testing for interaction effects.
5.  **Multiple Comparison Correction**: Apply Bonferroni or Benjamini-Hochberg correction to control for family-wise error rate.
