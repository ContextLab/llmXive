# Research: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Dataset Strategy

| Decision | Rationale |
|----------|-----------|
| **Dataset**: OpenNeuro **ds001734** (`https://openneuro.org/datasets/ds001734`) | Publicly downloadable, verified URL, contains BIDS‑style EEG recordings with an `events.tsv` that includes a `condition_label` field distinguishing **simple** oddball and **complex** auditory‑scene conditions. |
| **Complex Condition Availability** | The ds001734 dataset **does** include a distinct “complex” auditory‑scene condition, satisfying FR‑008. This enables the planned paired comparison of MMN metrics across complexity levels. |
| **Fallback** | If, for any unforeseen reason, the “complex” label were missing after verification, the pipeline would halt with a clear error (FR‑008). No alternative dataset is needed because the required conditions are present. |

### Acquisition Steps
1. `datasets.load_dataset("openneuro/ds001734", streaming=False)` → `data/raw/`.  
2. Compute SHA‑256 for every file; store in `state/...yaml`.  
3. Parse each subject’s `events.tsv`; verify presence of at least one row with `condition_label == "simple"` **and** at least one row with `condition_label == "complex"`.  
4. Set a Boolean flag `complex_available = True` (guaranteed by verification).  

## Preprocessing Pipeline (MNE‑Python)

| Step | Parameters | Purpose |
|------|------------|---------|
| Band‑pass filter | 1 Hz – 40 Hz, FIR, zero‑phase | Remove drift & high‑frequency noise while preserving MMN. |
| ICA | `n_components=0.99` variance, automatic EOG detection, `random_state=42` | Remove blink/eye‑movement artifacts. |
| Re‑reference | Average mastoids (`TP9`, `TP10`) | Standard reference for auditory ERP. |
| Baseline correction | Mean of –200 ms → 0 ms subtracted | Required for accurate amplitude. |
| Epoching | –200 ms to 500 ms relative to stimulus onset | Matches spec window; enables baseline calculations. |
| Condition labeling | Use `condition_label` from `events.tsv` | Guarantees independent‑variable integrity. |
| Subject exclusion | Exclude if > 50 % epochs rejected post‑ICA | Implements edge‑case handling. |
| Channel interpolation | Spherical spline if < 10 % channels missing | Preserves topographic fidelity. |
| Covariate extraction | Load `participants.tsv` (age, gender, hearing ability) when present | Allows mixed‑effects robustness check. |
| Trial‑balance check | If condition trial counts differ > 10 %, down‑sample larger condition | Prevents bias from unequal trial numbers. |

All steps are deterministic; random seeds are fixed.

## Statistical Methodology

### MMN Quantification
* **Window**: 150 ms – 250 ms post‑stimulus.  
* **Electrode cluster**: `['Fz','FCz','Cz','F3','F4','FC3','FC4']`.  
* **Amplitude**: Mean voltage difference (deviant – standard) within window.  
* **Latency**: Time of maximal difference within window.  

### Signal‑Validity (SC‑001)
* Compute baseline SEM = `std(pre‑stimulus) / sqrt(N_trials)`.  
* SNR = `|amplitude| / SEM`.  
* Enforce `SNR ≥ 3.0`; otherwise flag `signal_validity = False` and exclude subject from group‑level stats.

### Topographic Consistency & Validity (SC‑004) – Leave‑One‑Out
* **LOO template**: For each subject, average the `deviant – standard` topography across *all other* subjects in the *simple* condition; save as `data/templates/canonical_mmn_loo.npy`.  
* **Consistency**: Pearson‑r between each subject’s simple‑condition topography and its LOO template; require `r ≥ 0.8`.  
* **Validity**: Pearson‑r between each subject’s complex‑condition topography and the *same* LOO template; require `r ≥ 0.8`.  

### Hypothesis Testing (SC‑002)
* Perform a paired t‑test on per‑subject MMN amplitude (simple vs complex).  
* Apply Benjamini‑Hochberg FDR across the electrode cluster.  
* Report `t`, raw `p`, `p_fdr`, and `significant` flag (`p_fdr < 0.05`).  

### Effect‑Size Benchmark (SC‑003)
* Compute Cohen’s d for the paired difference.  
* Load benchmark JSON `data/benchmarks/mmn_effect_sizes.json` containing `{ "medium_effect_d": 0.5 }`.  
* Flag `practical_significance = True` if `d ≥ 0.5`.  

### Mixed‑Effects Robustness (methodology‑ba42f9db)
* If covariates are available, fit a linear mixed‑effects model (`statsmodels.MixedLM`) with condition as fixed effect, subject as random intercept, and covariates as additional fixed effects.  
* Report fixed‑effect estimate, SE, and p‑value as a supplementary robustness metric.

All statistical calculations use `scipy.stats` (t‑test) and `statsmodels.stats.multitest` (FDR). Power analysis is **not** a required FR/SC; the pipeline logs a warning if the final subject count falls below the 20‑subject heuristic and marks the results as exploratory.

## Compute Feasibility
* **CPU‑first**: All heavy lifting runs on NumPy/SciPy; fully CPU‑compatible.  
* **Memory Management**: Process subjects sequentially; `Epochs` objects are saved to disk (`.fif`) and loaded on demand, keeping RAM < 6 GB.  
* **Runtime Estimate**: [deferred] per subject; full cohort (< 20 subjects) fits comfortably within the 6 h limit.  

## Decision / Rationale Table

| Decision | Rationale |
|----------|-----------|
| Use 1‑40 Hz band‑pass | Preserves MMN while removing drift & muscle noise. |
| ICA with fixed variance | Guarantees removal of dominant ocular artifacts without over‑fitting. |
| Baseline subtraction (–200 ms → 0 ms) | Standard ERP practice; required for SNR computation. |
| Paired t‑test + Benjamini‑Hochberg | Controls Type I error across multiple electrodes (SC‑002). |
| SNR ≥ 3.0 (SEM denominator) | Ensures the MMN is not a noise fluctuation (SC‑001). |
| Cohen’s d benchmark ≥ 0.5 | Aligns with literature‑derived medium effect threshold (SC‑003). |
| Topographic Pearson‑r ≥ 0.8 using LOO template | Provides a stringent, non‑circular neurophysiological consistency check (SC‑004). |
| Verify both “simple” and “complex” conditions | Satisfies FR‑008; aborts with clear error if missing. |
| Power analysis prior to data collection | Guarantees sufficient sample size; if under‑powered, results are flagged as exploratory. |

---


