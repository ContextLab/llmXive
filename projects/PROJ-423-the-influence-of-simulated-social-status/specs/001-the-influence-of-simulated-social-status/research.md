# Research: The Influence of Simulated Social Status on Risk-Taking Behavior

## I. Background & Motivation

Existing literature demonstrates a link between social status and risk-taking, but the directionality and underlying mechanisms remain unclear. This project aims to determine whether observing higher-status agents engaging in risky behavior *increases* subsequent individual risk-taking, while observing lower-status agents engaging in such behavior *decreases* it. A key challenge is the lack of readily available datasets with a fully crossed factorial design (status level x observed behavior).

## II. Data Strategy

Given the difficulty of finding pre-existing data, this project will leverage either:

1.  **Data Simulation:** Generate a synthetic dataset based on meta-analytic effect sizes derived from published studies on social status and risk-taking. This approach allows for precise control over experimental conditions and minimizes confounding variables.
2.  **Meta-Analysis:** Aggregate data from separate randomized trials examining the relationship between social status, observed behavior, and risk-taking.

**Verified Datasets**:

*   VIF (parquet): [https://huggingface.co/datasets/tranthaihoa/vifactcheck/resolve/main/data/dev-00000-of-00001.parquet](https://huggingface.co/datasets/tranthaihoa/vifactcheck/resolve/main/data/dev-00000-of-00001.parquet)
*   NOT (jsonl): [https://huggingface.co/datasets/QinyuanWu/ToCall_or_NotToCall/resolve/main/bfcl/bfcl.jsonl](https://huggingface.co/datasets/QinyuanWu/ToCall_or_NotToCall/resolve/main/bfcl/bfcl.jsonl), [https://huggingface.co/datasets/kalyannakka/Answerable-or-Not/resolve/main/answerability_data.csv](https://huggingface.co/datasets/kalyannakka/Answerable-or-Not/resolve/main/answerability_data.csv), [https://huggingface.co/datasets/vlmbook/notebooks/resolve/main/Chapter%203/chapter_3_batched_loss.json](https://huggingface.co/datasets/vlmbook/notebooks/resolve/main/Chapter%203/chapter_3_batched_loss.json)

## III. Decision/Rationale

The choice between simulation and meta-analysis will be guided by data availability and effect size consistency. If reliable meta-analytic parameters are available, simulation is preferred for its control. Otherwise, a rigorous meta-analysis will be conducted using established methods (e.g., random effects models).  All computational work will prioritize CPU execution due to resource constraints of the free tier runner. If GPU acceleration becomes essential (e.g., for complex model fitting), we will utilize Kaggle’s free GPU resources with scaled-down data and a quantized model (`device="cuda"` / `load_in_8bit`).

## IV. Statistical Approach

A mixed-effects regression model will be employed to assess the interaction between observed agent status and observed behavior on participant risk-taking, accounting for potential individual differences using random effects. Model assumptions (e.g., linearity, normality of residuals) will be verified through diagnostic plots. Family Wise Error correction (Bonferroni) will be applied for post-hoc comparisons.
