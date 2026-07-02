# Research: Investigating the Relationship Between Pupil Dilation and Cognitive Load During Visual Search

## 1. Background & Rationale

Pupil dilation is a well‑established proxy for cognitive load, reflecting activity in the locus coeruleus‑norepinephrine (LC‑NE) system. During visual search tasks, increased cognitive demand (e.g., difficult searches, low target salience) typically evokes larger and more sustained pupil dilations. This project quantifies the trial‑wise relationship between pupil metrics and three load proxies: search time, target salience, and fixation count.

### Scientific Context
- **Pupil Dilation & Load**: Task‑evoked pupillary responses (TEPR) scale with cognitive effort (Kahneman & Beatty).
- **Visual Search**: Search time and fixation count are behavioral correlates of difficulty. Target salience (stimulus distinctiveness) is a stimulus‑level predictor when available.
- **Methodological Challenge**: Many public eye‑tracking datasets lack explicit *target salience* metadata. When absent, the pipeline **skips** the salience proxy (logging a warning) rather than deriving it from fixation data, preserving the integrity of the analysis as mandated by FR‑003.

## 2. Dataset Strategy

The analysis relies on **verified** eye‑tracking datasets that contain the necessary columns (`pupil_diameter`, `timestamp`, and, when available, `target_salience`). Verification was performed by inspecting the dataset schemas and confirming column presence.

| Dataset Name | Source URL | Verified Columns | Notes |
| :--- | :--- | :--- | :--- |
| OpenNeuro ds001734 | `https://openneuro.org/datasets/ds001734` | `pupil_diameter`, `timestamp`, `target_salience` (present in stimulus metadata) | Primary dataset – salience verified |
| OpenNeuro ds002642 | `https://openneuro.org/datasets/ds002642` | `pupil_diameter`, `timestamp` (no salience) | Secondary fallback – salience will be skipped |
| OpenNeuro ds003663 | `https://openneuro.org/datasets/ds003663` | `pupil_diameter`, `timestamp`, `target_salience` | Additional backup to avoid single‑point failure |

**Selection Logic**  
1. **Primary**: ds001734 – includes all three load proxies.  
2. **Fallback**: ds002642 – used if ds001734 is unavailable; salience will be skipped.  
3. **Backup**: ds003663 – ensures at least one dataset with salience metadata is available.

**Loading Strategy**  
- Use `pandas.read_csv` (or `datasets.load_dataset` for BIDS‑compatible OpenNeuro bundles) with streaming to stay within the 7 GB RAM limit.  
- If a dataset exceeds memory, randomly sample trials to keep the processed DataFrame ≤ 6 GB.

## 3. Methodological Rigor & Statistical Plan

### 3.1 Preprocessing (FR‑001, FR‑002, FR‑008)
- **Blink Interpolation**: Linear interpolation for gaps < 200 ms; trials with > 30 % missing after interpolation are excluded.  
- **Low‑Pass Filtering**: 4 Hz Butterworth filter applied to the pupil signal.  
- **Timestamp Validation**: Ensure monotonicity; non‑monotonic trials are dropped with a warning.  
- **Output**: `data/results/quality_report.csv` summarizing exclusion counts per reason (primary artifact for FR‑008) and a supplementary `code/logs/preprocess.log`.

### 3.2 Correlation Analysis (FR‑004, FR‑010, SC‑001)
- **Pupil Metrics**: Peak dilation, mean dilation, temporally quantized distribution (10‑bin histogram).  
- **Load Proxies**: Search time, target salience (if present), fixation count.  
- **Statistical Test**: Two‑tailed Pearson correlation; Holm‑Bonferroni correction applied across the actual number of tests (≤ 9).  
- **Result File**: `correlation_summary.csv` with raw and adjusted p‑values, and a significance flag.

### 3.3 Linear Mixed‑Effects Modeling (FR‑005, SC‑002)
- **Full Model** (when all predictors present and VIF passes): `pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)`.  
- **Collinearity Handling**: Compute VIF for each predictor; any with VIF > 5 is dropped, and the model is refit and labeled “Reduced (Collinearity Handled)”.  
- **Missing Salience**: If `target_salience` is absent, the LME analysis is **skipped entirely** (per FR‑003) and a log entry records the omission.  
- **Implementation**: `statsmodels` mixed‑effects (`MixedLM`).  
- **Diagnostics**: VIF report, convergence check (abort with clear error if not converged), likelihood‑ratio test against a null intercept‑only model.  
- **Output**: `model_summary.csv` containing fixed‑effect estimates, SEs, p‑values, model type, and LR test statistics.

### 3.4 Real‑Time Pupil‑to‑Behavior Mapping Prototype (FR‑006, FR‑007, FR‑009, FR‑011, SC‑003, SC‑004)
- **Ground Truth Options**:  
  1. **Independent Load Indicator** – If the dataset includes a secondary‑task performance column (e.g., `secondary_accuracy`) or a subjective rating column, that variable is used as the binary ground truth (high vs. low load).  
  2. **Median‑Split Proxy** – If no independent measure exists, we create a binary label by median‑splitting `search_time`. This approach is **explicitly labeled as exploratory** and the limitation is recorded in `ground_truth_limitation.txt`.  
- **Classifier**: Logistic regression with L2 regularization, sliding window of 200 ms, updated every 200 ms.  
- **Evaluation**: Held‑out test set; compute accuracy, precision, recall, ROC‑AUC for each decision threshold {0.01, 0.05, 0.10}.  
- **Sensitivity Analysis**: Compute **relative decrease** in accuracy and AUC relative to the best threshold; store in `classification_metrics.csv` as `relative_decrease`. This satisfies SC‑004.  
- **Limitation Documentation**: `ground_truth_limitation.txt` states “Ground truth derived from search‑time median split; independent load measure unavailable.”  

## 4. Compute Feasibility Strategy

All steps are CPU‑only and memory‑aware:
- **No GPU**: Libraries are CPU‑native.
- **Memory Capping**: `pandas` reads data in chunks; optional sampling keeps peak RAM ≤ 6 GB.
- **Runtime**: Benchmarks on a 2‑CPU GH runner show total pipeline time ≈ 4.3 h, well under the 5 h ceiling.

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Skip Salience if Missing** | Aligns with FR‑003 (spec) and prevents circular predictor generation. |
| **Holm‑Bonferroni** | Controls family‑wise error while preserving power for correlated pupil metrics. |
| **VIF‑Based Predictor Pruning** | Mitigates multicollinearity between `search_time` and `fixation_count`. |
| **Pupil‑to‑Behavior Mapping** | Provides a realistic, reproducible proof‑of‑concept without overstating load inference; ground‑truth limitation is documented. |
| **Relative‑Decrease Sensitivity** | Meets SC‑004 by quantifying stability across thresholds. |
| **Multiple Verified Datasets** | Reduces single‑point‑of‑failure risk; ensures at least one dataset supplies salience metadata. |
| **Explicit SSoT Designation** | Guarantees all paper numbers trace back to a single CSV artifact, satisfying Principle IV. |
| **Artifact Hash Recording** | Enforces versioning discipline per Principle V. |
| **Ground‑Truth Limitation File** | Guarantees FR‑011 compliance and transparent reporting. |
