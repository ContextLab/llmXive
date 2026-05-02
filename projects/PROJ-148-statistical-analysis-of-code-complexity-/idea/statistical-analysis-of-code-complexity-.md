---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Field**: statistics  

## Research question  

Which source‑code complexity metrics (e.g., cyclomatic complexity, lines of code, nesting depth) most strongly predict the presence of bugs in open‑source software, and how accurately can a statistical model built on these metrics identify bug‑prone code units?  

## Motivation  

Software defects dominate maintenance costs, yet developers lack quantitative guidance on which code characteristics signal higher defect risk. Prior defect‑prediction studies have used a variety of metrics, but a systematic comparison of classic complexity measures on large, modern repositories is missing. Identifying the most predictive metrics will enable lightweight, data‑driven prioritisation of code review and testing.  

## Related work  

- [Use of Source Code Similarity Metrics in Software Defect Prediction (2018)](http://arxiv.org/abs/1808.10033v1) — Shows that similarity‑based features improve defect prediction; provides a baseline for comparing traditional complexity metrics.  
- [Wildfire Prediction to Inform Fire Management: Statistical Science Challenges (2013)](http://arxiv.org/abs/1312.6481v1) — Illustrates statistical modelling of complex, spatiotemporal processes; useful for methodological inspiration (e.g., handling imbalanced outcomes).  
- [The Statistical Analysis of fMRI Data (2009)](http://arxiv.org/abs/0906.3662v1) — Discusses hierarchical modelling and multiple‑testing correction; relevant for rigorous inference on many code modules.  

## Expected results  

We anticipate that a subset of complexity metrics (particularly cyclomatic complexity and nesting depth) will exhibit statistically significant positive associations with bug occurrence (p < 0.05 after false‑discovery correction). A logistic‑regression or random‑forest model built on these metrics is expected to achieve an ROC‑AUC of ≈0.70–0.80 on held‑out repositories, demonstrating moderate predictive power while remaining interpretable.  

## Methodology sketch  

- **Data acquisition**  
  1. Download a curated set of open‑source Java projects from the GHTorrent dataset (URL: https://ghtorrent.org/).  
  2. For each project, retrieve the full commit history and issue tracker (GitHub API) to label code files/commits as “bug‑fix” (based on keywords in commit messages and linked issue labels).  

- **Metric computation**  
  3. Use the open‑source tool *lizard* (https://github.com/terryyin/lizard) to compute per‑file metrics: cyclomatic complexity, lines of code, token count, nesting depth, Halstead volume, etc.  
  4. Aggregate metrics at the file level (or function level) and align them with the bug‑fix labels from step 2.  

- **Data preprocessing**  
  5. Clean missing values, log‑transform highly skewed metrics, and encode the binary bug label.  
  6. Split the dataset into training (70 %) and test (30 %) sets stratified by project to avoid leakage.  

- **Statistical modelling**  
  7. Fit a logistic‑regression model with L1 regularisation (glmnet) to identify the most predictive metrics.  
  8. As a robustness check, train a random‑forest classifier (scikit‑learn) and compare variable importance.  

- **Evaluation**  
  9. Compute ROC‑AUC, precision‑recall curves, and calibration plots on the held‑out test set.  
  10. Perform k‑fold cross‑validation (k = 5) within the training set to assess variance of performance metrics.  

- **Interpretation & reporting**  
  11. Apply Benjamini–Hochberg correction to regression p‑values to control false discovery rate.  
  12. Visualise the top‑3 metrics with partial dependence plots; discuss practical thresholds for developers.  

All steps rely on publicly available data and Python/R libraries that run comfortably within a GitHub Actions runner (≤ 7 GB RAM, ≤ 6 h total runtime).  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(none identified)*.  
- Verdict: **NOT a duplicate**.
