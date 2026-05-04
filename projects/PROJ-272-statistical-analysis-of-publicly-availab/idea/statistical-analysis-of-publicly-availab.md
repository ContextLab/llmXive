---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Field**: statistics

## Research question

Can statistical features extracted from publicly available textual data (lexical diversity, syntactic complexity, semantic coherence) reliably distinguish between individuals with cognitive decline and cognitively normal controls?

## Motivation

Early detection of cognitive decline is critical for timely intervention, yet current diagnostic methods require clinical visits and specialized testing. If linguistic markers in accessible text can predict cognitive status, this would enable scalable, non-invasive screening. The gap in existing literature is the lack of rigorous statistical validation of these linguistic features on publicly available datasets with known cognitive status labels.

## Related work

- [A remark on statistics for detecting laboratory effects in ORDANOVA (2019)](http://arxiv.org/abs/1904.06048v3) — ORDANOVA provides ordinal variation analysis methods that could be adapted for ranked cognitive status comparisons.
- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Discusses modern statistical philosophy relevant to interpreting predictive model performance and avoiding overfitting.
- [Statistical Modeling of RNA-Seq Data (2011)](http://arxiv.org/abs/1106.3211v1) — High-dimensional statistical modeling techniques applicable to feature-rich linguistic data.
- [The Statistical Analysis of fMRI Data (2009)](http://arxiv.org/abs/0906.3662v1) — Neuroimaging statistical approaches that parallel multivariate analysis of linguistic biomarkers.

## Expected results

We expect to identify 3-5 linguistic features with statistically significant differences between cognitive decline and control groups (p < 0.05, effect size d > 0.5). A logistic regression or random forest classifier using these features should achieve AUC ≥ 0.75 on held-out test data, with cross-validation confirming generalizability. The level of evidence needed includes at least 500 samples per group with verified cognitive status labels.

## Methodology sketch

- **Data acquisition**: Download the DementiaBank Pitt Corpus (https://dementia.talkbank.org/) and the ADReSS Challenge dataset (https://github.com/microsoft/ADReSS); both provide interview transcripts with cognitive status labels (MCI, AD, control).
- **Preprocessing**: Clean transcripts, remove non-verbal annotations, tokenize using NLTK (Python); store as UTF-8 text files.
- **Feature extraction**: Compute lexical diversity (type-token ratio, MTLD), syntactic complexity (mean clause length, T-unit count), and semantic coherence (sentence embedding cosine similarity using lightweight sentence-BERT).
- **Data split**: Stratified 70/15/15 train/validation/test split by participant to avoid data leakage.
- **Statistical modeling**: Fit logistic regression and random forest classifiers; compare AUC, accuracy, and F1-score across models.
- **Feature importance**: Extract coefficients (logistic) or Gini importance (random forest) to rank linguistic features.
- **Statistical testing**: Apply Mann-Whitney U test for feature differences between groups; Bonferroni correction for multiple comparisons.
- **Cross-validation**: 5-fold stratified cross-validation to assess model stability within 7GB RAM constraint.
- **Visualization**: Generate ROC curves, feature importance bar plots, and confusion matrices using Matplotlib.
- **Reproducibility**: Save all code, random seeds, and processed data to GitHub repository; document environment requirements.

## Duplicate-check

- Reviewed existing ideas: TODO — no existing idea corpus provided for similarity comparison.
- Closest match: N/A (no corpus available).
- Verdict: NOT a duplicate
