# Research: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis  

## Dataset Strategy  

| Decision | Rationale |
|----------|-----------|
| **Dataset** | No verified URL for OpenNeuro **ds001734** (the dataset named in the specification) appears in the “# Verified datasets” block. Consequently, the pipeline cannot automatically download it on the CI runner. |
| **Alternative** | The verified list contains only generic EEG or non‑EEG OpenNeuro collections; none provide the required `condition_label` with **both** “simple” **and** “complex” auditory‑scene trials. Therefore, **no suitable open dataset is currently available**. |
| **Fallback** | The pipeline will execute **Phase 0 – Dataset‑Gap Check** (see `code/dataset_gap.py`). This check **requires the presence of BOTH** `simple` **and** `complex` condition labels. If a suitable dataset is later added to the verified list, the pipeline can resume from Phase 1. Otherwise, the project must be **re‑scoped** (e.g., focus on a single condition, or adopt a different open auditory ERP dataset). This avoids fabricating data and respects the data‑resource concern. |

### Acquisition Steps (if a suitable dataset is identified)  
1. `datasets.load_dataset("<verified‑dataset‑id>", streaming=False)` → `data/raw/`.  
2. Compute SHA‑256 for each file; store in `state/...yaml`.  
3. Parse each subject’s `events.tsv`; **verify that at least one row with `condition_label == "simple"` **and** one with `condition_label == "complex"`** exist. Abort with a clear error if either is missing (fulfills FR‑008).  

## Preprocessing Pipeline (MNE‑Python)  

| Step | Parameters | Purpose |
|------|------------|---------|
| Band‑pass filter | 1 Hz – 40 Hz, FIR, zero‑phase | Remove drift & high‑frequency noise while preserving MMN. |
| ICA | `n_components=0.99` variance, automatic EOG detection, `random_state=42` | Remove ocular artifacts. |
| Re‑reference | Average mastoids (`TP9`, `TP10`) | Standard reference for auditory ERP. |
| Baseline correction | Mean of –200 ms → 0 ms subtracted | Required for accurate amplitude measurement. |
| Epoching | –200 ms to 500 ms relative to stimulus onset | Matches spec window; enables baseline calculations. |
| Condition labeling | Use `condition_label` from `events.tsv` | Guarantees independent‑variable integrity. |
| Subject exclusion | Exclude if > 50 % epochs rejected post‑ICA | Implements edge‑case handling. |
| Channel interpolation | Spherical spline if < 10 % channels missing | Preserves topographic fidelity. |
| Trial‑balance check | Down‑sample larger condition if trial count > 10 % imbalance | Prevents bias from unequal trial numbers. |
| **NaN validation** | After epoch creation assert `np.isnan(epochs.get_data()).any() == False` (SC‑008) | Guarantees clean data for analysis. |

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
* Enforce `SNR ≥ 3.0`; otherwise flag `signal_validity = False` and exclude subject from group‑level stats (FR‑011 ↔ SC‑001).  

### Topographic Consistency & Validity (SC‑004) – Leave‑One‑Out  
* **LOO template**: For each subject, average the `deviant – standard` topography across *all other* subjects in the *simple* condition; save as `data/templates/canonical_mmn.npy` (FR‑009).  
* **Consistency**: Pearson‑r between each subject’s simple‑condition topography and its LOO template; require `r ≥ 0.8`.  
* **Validity**: Pearson‑r between each subject’s complex‑condition topography and the *same* LOO template; require `r ≥ 0.8`.  

### Hypothesis Testing (SC‑002)  
* Paired t‑test on per‑subject MMN amplitude (simple vs complex).  
* Benjamini‑Hochberg FDR correction across the electrode cluster.  
* Report `t`, raw `p`, `p_fdr`, and a boolean `significant` (`p_fdr < 0.05`).  

### Effect‑Size Benchmark (SC‑003)  
* Compute Cohen’s d for the paired difference.  
* Load benchmark JSON `data/benchmarks/mmn_effect_sizes.json` containing `{ "medium_effect_d": 0.5 }`.  
* Flag `practical_significance = True` if `d ≥ 0.5`.  

### Mixed‑Effects Robustness (optional) – Addresses methodology‑0f0359eb  
* If covariates (e.g., deviant probability, inter‑stimulus interval, acoustic feature metrics) are present in `events.tsv`, fit a linear mixed‑effects model (`statsmodels.MixedLM`) with condition as fixed effect, covariates as additional fixed effects, and subject as random intercept.  
* Report fixed‑effect estimate, SE, and p‑value as a supplementary robustness metric, ensuring that any observed complexity effect is not confounded by other stimulus attributes.  

### Power Analysis (FR‑016 ↔ SC‑006)  
* Prior to confirmatory testing, compute required N for detecting `d = 0.5` with 80 % power (α = 0.05) using `statsmodels.stats.power.TTestPower`.  
* If post‑QC subject count `N` < required, **abort confirmatory testing**, set `exploratory = true` in `results/stats.json`, and log a warning.  

All statistical calculations use `scipy.stats` (t‑test) and `statsmodels.stats.multitest` (FDR).  

## Compute Feasibility  
* **CPU‑first**: All heavy lifting runs on NumPy/SciPy/MNE; fully CPU‑compatible.  
* **Memory Management**: Process subjects sequentially; each `Epochs` object saved to disk (`.fif`) and loaded on demand, keeping RAM < 6 GB.  
* **Runtime Estimate**: [deferred] per subject; full cohort (< 20 subjects) comfortably fits within the 6 h CI limit.  

## Decision / Rationale Table  

| Decision | Rationale |
|----------|-----------|
| **Dataset‑Gap Check** | Guarantees we never attempt analysis on a dataset lacking required conditions (FR‑008). |
| **Band‑pass 1–40 Hz** | Preserves MMN while removing drift & muscle noise. |
| **ICA with fixed variance** | Guarantees removal of dominant ocular artifacts without over‑fitting. |
| **Baseline subtraction (–200 ms → 0 ms)** | Standard ERP practice; required for SNR computation. |
| **Paired t‑test + Benjamini‑Hochberg** | Controls Type I error across multiple electrodes (SC‑002). |
| **SNR ≥ 3.0** | Ensures the MMN is not a noise fluctuation (SC‑001). |
| **Cohen’s d benchmark ≥ 0.5** | Aligns with literature‑derived medium effect threshold (SC‑003). |
| **Topographic Pearson‑r ≥ 0.8 using LOO template** | Provides a stringent, non‑circular neurophysiological consistency check (SC‑004). |
| **Power analysis prior to confirmatory testing** | Guarantees sufficient sample size; if under‑powered, results are flagged as exploratory (FR‑016). |
| **Covariate mixed‑effects model** | Addresses potential confounds from stimulus attributes (methodology‑0f0359eb). |
| **Reference‑Validator before reporting** | Satisfies FR‑012‑3, ensuring all citations are verified at the final stage. |
| **Visualization file existence & size checks** | Satisfies SC‑005, guaranteeing usable figures for dissemination. |

---


