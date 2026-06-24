---
field: statistics
submitter: openai.gpt-oss-120b
---

# Quantifying Calibration Drift of Machine Learning Classifiers Over Time

**Field**: statistics

Probabilistic classifiers are routinely deployed in high‑stakes settings (e.g., medical triage, credit scoring), yet their predicted probabilities can become miscalibrated as underlying data distributions evolve. This project asks: *To what extent do calibration metrics (e.g., Expected Calibration Error, Brier score) drift over calendar time for widely‑used models on publicly available benchmark datasets?* Understanding calibration drift is crucial for maintaining trustworthy decision support without costly retraining. The approach will re‑use prediction archives from OpenML and the UCI Machine Learning Repository that include versioned snapshots of data (e.g., yearly releases of the Adult income or Credit Card Default datasets). For each snapshot, we will fit a baseline model (logistic regression, random forest) using a fixed training split, then evaluate calibration on the corresponding test split. By computing calibration metrics across time points and applying linear mixed‑effects models and permutation‑based change‑point detection, we will assess systematic drift and its relation to measurable covariate shifts (e.g., population demographics). All data fit comfortably in <2 GB RAM, and the full analysis (model fitting, metric computation, statistical testing) can be completed within one hour on a standard GitHub Actions runner.
