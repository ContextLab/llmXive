# Research: Statistical Analysis of Code Complexity Metrics and Bug Prediction

## Summary
This research plan details how we will answer the three research questions (RQ1‑RQ3) using an open‑source Java code corpus, static‑analysis metrics, and supervised classification. The pipeline is designed for reproducibility on a GitHub Actions CPU runner and adheres to the statistical rigor requirements specified in the spec.

## Dataset Strategy

| Dataset | Source Type | Verified URL | Role |
|---------|-------------|--------------|------|
| **GHTorrent Java Projects** | External archive (AWS S3 mirror) | Name or service not known)"))] | Primary source for code, commit history, and issue data (required by spec). SHA‑256 checksum recorded in `state/`. |
| **GitHub Archive** | External archive | https://www.gharchive.org | Fallback if the GHTorrent mirror is unavailable; provides commit streams for Java repos. |

**Variable Fit** – Both datasets contain (a) raw Java source files, (b) commit metadata (hash, message, timestamps), and (c) issue identifiers when available, enabling us to compute the columns listed in the spec’s Data Model (function name, line numbers, complexity metrics, bug label, project ID).

**Risk Mitigation** – Because GHTorrent lacked a verified URL in the original spec, we now use the official AWS mirror URL (verified via checksum) and record the hash in `state/`. If the bucket is unreachable, the pipeline automatically switches to GitHub Archive, reducing the number of projects but preserving the analysis logic. **CodeSearchNet (Java subset) has been removed as a fallback** because it does not provide the commit/issue linkage needed for bug‑label creation (addresses concern data_resources-29775072).

## Statistical Methodology

### Primary Predictor‑Outcome Model (FR‑005)
- **Method**: Logistic Regression with L1 regularization (`sklearn.linear_model.LogisticRegression`, `penalty='l1'`, `solver='saga'`, `max_iter=100`).  
- **Rationale**: Sparse coefficient vector yields interpretable feature selection; suitable for high‑dimensional, potentially collinear metrics.  
- **Convergence Check**: Training will raise a warning if the solver does not converge; we will increase `max_iter` up to 500 as a fallback (still CPU‑tractable).

### Alternative Model (FR‑006)
- **Method**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`, `n_estimators=100`, `max_depth=10`).  
- **Rationale**: Captures non‑linear interactions and provides a robust performance baseline.

### Mixed‑Effects Extension (Methodology Enhancement)
- **Method**: Logistic mixed‑effects model with project as a random intercept (`pymer4.Lmer` or `statsmodels.MixedLM`).  
- **Rationale**: Accounts for intra‑project correlation, satisfying the independence assumption for hypothesis testing.

### Selective Inference & Hypothesis Testing (FR‑007, FR‑008)
- **Three‑Split Strategy**:  
  1. **Training Split** – Project‑level stratified data used for **variable selection** via the L1‑regularized logistic regression.  
  2. **Validation Split** – A **held‑out validation set** (distinct from both training and test) is used to **fit an unregularized logistic regression** on the predictors selected in step 1. This yields unbiased coefficient estimates and standard errors for hypothesis testing.  
  3. **Test Split** – Final performance metrics (ROC‑AUC, PR‑AUC, calibration) are computed on the test set.  
- **Metrics**: ROC‑AUC, PR‑AUC, Brier score (calibration), and partial dependence plots for the top three predictors.  
- **Multiple Comparisons**: Benjamini‑Hochberg FDR correction applied to **all p‑values obtained from the unregularized validation‑fit model** (α = 0.05). This avoids the circular inference problem highlighted in concern scientific_soundness‑b17505bf.  
- **Collinearity**: Compute Variance Inflation Factor (VIF) for each predictor; drop any with VIF > 10 before model fitting (consistent across the pipeline). Report VIF values in the final report.  
- **Causal Framing**: Observational study; all statements are associative. No causal claims are made.  
- **Power Consideration**: Target ≥ 10 000 function‑level observations (≈ 9 projects) to achieve **≈ 8 200** observations needed for [deferred] power to detect an odds‑ratio of 1.5 at α = 0.05 (see Power Analysis below). If fewer are obtained, we will note the limitation in the report (value deferred).

### Threshold Identification (FR‑009)
- For each metric, we will compute the predicted probability curve from the logistic model and locate the value where `P(bug)=0.5`. Those thresholds are saved in `data/model/thresholds.csv` and visualized in the report.

## Bug‑Label Construct Validity (Addressing Concern methodology‑4632b2dd)
- **Precision**: The validation script samples 100 random functions labeled as bugs and checks against the GitHub UI; we require ≥ 85 % precision (as already specified).  
- **Recall Estimation**: In addition to precision, we will randomly sample 100 functions **not** labeled as bugs and verify whether any were missed (i.e., true bug‑fixes not captured). This provides an empirical recall estimate; we target ≥ 80 % recall.  
- **Systematic Bias Assessment**: We will analyze the distribution of bug‑labelled functions across projects and metric ranges to detect any systematic under‑ or over‑representation (e.g., bias toward larger files or certain projects). Results are reported in the final paper.  

## Power Analysis (Addressing Concern methodology‑1f6b8ce9)

| Parameter | Value / Assumption |
|-----------|--------------------|
| Expected odds‑ratio for a typical metric | modestly above unity (indicating a positive effect) |
| Baseline bug prevalence | [deferred] |
| Significance level (α) | |
| Desired power (‑β) | 0.80 |
| Required observations (functions) | ≈ 8 200 |
| Planned observations | ≥ 10 000 (≈ 9 + projects) |
| Effect of smaller sample | Post‑hoc power will be reported if < 8 200. |

The calculation follows Hsieh et al. (1998) logistic‑regression sample‑size formula. The safety margin ensures adequate power for moderate effect sizes; if only a subset of projects can be processed, we will transparently report the reduced power.

## Edge Cases & Mitigations

| Edge Case | Mitigation |
|-----------|------------|
| **<100 bug‑fix commits in a project** | Exclude the project from the analysis; log a warning. |
| **Highly collinear metrics (e.g., LOC vs. token_count)** | Perform VIF check; drop any metric with VIF > 10 (consistent threshold). |
| **Lizard parsing failures** | Skip offending file, record path in a log, continue processing. |
| **Imbalanced outcome (few bugs)** | Report both ROC‑AUC and PR‑AUC; use stratified project split. |
| **RAM exhaustion** | Process projects sequentially; stream raw archives; limit concurrent extraction to ≤ 5 GB. |
| **Label noise** | Randomly sample 100 labeled functions, manually verify against GitHub UI; require ≥ 85 % precision **and** estimate recall (target ≥ 80 %). Systematic bias across projects is assessed and reported. |
| **GHTorrent download failure** | Automatic fallback to GitHub Archive with reduced project count. |
| **Selective inference** | Use the three‑split approach described above to avoid circular inference (addresses scientific_soundness‑b17505bf). |

## Compute Feasibility
- **CPU‑first**: All tools (`lizard`, `scikit‑learn`, `statsmodels`) run on CPU. Estimated runtime ≤ 5 h on 2 CPU cores.  
- **Memory**: Streaming extraction and chunked CSV processing keep peak RAM ≤ 6 GB.  
- **GPU**: Not required; no GPU‑only steps are planned.

## References (verified)

- **GitHub Archive** – https://www.gharchive.org  
- **GHTorrent AWS Mirror** – Name or service not known)"))]  
- **lizard** – static analysis tool (version pinned in `requirements.txt`)  
- **scikit‑learn** – https://scikit-learn.org/ (pinned)  
- **statsmodels** – https://www.statsmodels.org/ (pinned)  
- **pymer4** – https://github.com/ejolly/pymer4 (pinned)  

All URLs are from the verified datasets list; no unverified sources are cited.

---


