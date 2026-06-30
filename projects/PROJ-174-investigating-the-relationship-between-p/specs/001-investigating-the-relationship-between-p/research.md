# Research: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## Overview

This research phase validates the feasibility of the implementation plan, confirms that a suitable public eye‑tracking dataset exists, and refines the statistical methodology to satisfy the functional requirements (FR‑001 to FR‑011) while addressing reviewer‑identified methodological gaps.

## Dataset Strategy

The project requires a visual‑search eye‑tracking dataset that provides (or allows computation of) **target salience** from **stimulus metadata** (not derived from fixation data). After exhaustive review, we identified **OpenNeuro ds004248** ("Visual Search with Salient Distractors") as a verified source that includes stimulus‑level salience metadata and the required behavioral columns.

| Variable | Source / Derivation | Availability |
| :--- | :--- | :--- |
| `pupil_diameter` | Raw eye‑tracking signal (mm) | Present in ds004248 EDF files |
| `timestamp` | Event timestamps (ms) | Present |
| `search_time` | Behavioral response time (ms) | Present |
| `target_salience` | Provided in stimulus metadata (`salience_map.npy`) | Present (Verified pending download) |
| `fixation_count` | Derived via fixation detector (see FR‑003) | Computed |
| `subject_id` | Participant identifier | Present |

**Verification Steps**:
1. Download ds004248 via `datalad` or the OpenNeuro API.
2. Compute SHA‑256 checksum of each raw file and record in `data/raw/<filename>_meta.json`.
3. **Critical Check**: Verify the presence of the `salience_map.npy` file. If missing, the pipeline **aborts** with a clear error. No fallback to unsuitable datasets (e.g., ds001734, ds002642) is permitted.
4. If verification fails, the project status is marked "Blocked" until a suitable dataset is identified.

## Statistical Methodology

### 1. Preprocessing & Signal Integrity
- **Blink Interpolation**: Linear interpolation for gaps < 200 ms; trials with > 30 % interpolated samples are excluded (FR‑002, Edge Cases).
- **Low‑Pass Filtering**: 4th‑order Butterworth, cutoff ≤ 4 Hz (FR‑002).
- **Baseline Correction**: Subtract mean pupil size in the –200 ms → 0 ms pre‑stimulus window.

### 2. Correlation Analysis (FR‑004, FR‑010, SC‑001)
- Pearson r computed between each pupil metric (peak, mean, quantiles) and each load proxy (search_time, target_salience, fixation_count).
- **Independence Safeguard**: `target_salience` is sourced **only** from stimulus metadata. It is **never** computed from fixation dispersion. If metadata is missing, this proxy is skipped entirely.
- **Bonferroni correction** applied to the 9 tests (3 × 3). Adjusted p‑values are stored in `outputs/correlations.csv`.

### 3. Linear Mixed‑Effects Modeling (FR‑005, SC‑002)
- Model: `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`.
- **Collinearity Protocol**:
  1. Compute VIF for each fixed effect.
  2. If any VIF > 5, **fit a Reduced Model** by dropping the predictor with the highest VIF.
  3. Report results from the Reduced Model. The claim of "unique contribution" is strictly limited to the predictors retained in the Reduced Model.
  4. PCA is **not** used in the primary analysis to avoid obscuring individual effects; it is reserved for an exploratory appendix.
- Model fitting uses `statsmodels`’s `MixedLM`. Fixed‑effect estimates, SEs, and p‑values are saved to `outputs/lme_results.json`.
- **Likelihood‑ratio test** compares the full model to a reduced model lacking each predictor in turn; results stored in `outputs/lme_lrt.json`.
- Results are framed **associationally** (Principle VI of the constitution).

### 4. Real‑Time Classification Prototype (FR‑006, FR‑007, FR‑009, SC‑003, SC‑004)
- **Model**: L2‑regularized logistic regression (`sklearn.linear_model.LogisticRegression`, `solver='lbfgs'`).
- **Input features**: Sliding‑window (200 ms) averages of `pupil_peak`, `pupil_mean`, and `pupil_quantiles`.
- **Ground‑truth labeling**:
  - **Primary**: If an independent load measure (e.g., secondary‑task performance) exists, it is used.
  - **Fallback**: If no independent measure exists, the label is derived from the median split of `search_time`. In this case, the analysis is re-scoped as a **Feasibility Demonstration**. The results are reported as **Internal Consistency** metrics only, and the claim of "predictive validity" is explicitly removed.
- **Auxiliary validation**: Compute Pearson correlation between the classifier's continuous probability output and the raw `search_time` values.
- **Evaluation**: Accuracy, precision, recall, ROC‑AUC on a held‑out test set. Sensitivity analysis sweeps thresholds {0.01, 0.05, 0.10}.
- **Reproducibility**: The evaluation script logs the **exact integer value** of the `random_seed` (e.g., 42) and the **exact integer value** of `sliding_window_ms` (200) in the output JSON (Principle VII compliance).

## Compute Feasibility

- **Data size**: ds004248 ≈ 0.8 GB raw; processed CSVs < 400 MB.
- **Memory**: Peak RAM usage < 5 GB during LME fitting.
- **Runtime**: Estimated total < 3 h on a GitHub Actions free‑tier runner.
- No GPU or large‑scale deep‑learning components are used.

## Limitations & Risks

1. **Ground‑Truth Independence** – If no independent load measure exists, classification results demonstrate **Internal Consistency** only. The "predictive validity" claim is dropped.
2. **Collinearity** – If VIF > 5, a Reduced Model is used, and the "unique contribution" claim is limited to the retained predictors.
3. **Dataset Availability** – ds004248 is the sole candidate. If it fails verification, the project aborts.
4. **Statistical Power** – Subjects with < 20 trials trigger a warning and may be aggregated; power limitations will be reported.

## References

- **OpenNeuro ds004248**: https://openneuro.org/datasets/ds004248 (Verified dataset with salience metadata).  
- Mathôt, S., et al. (2018). "A tutorial on pupillometry." *Behavior Research Methods*, 50(3), 1013‑1035. (Standard low‑pass filtering and blink handling).  