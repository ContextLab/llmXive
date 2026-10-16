# Research: Investigating Neural Signatures of Predictive Processing in Visual Illusions

## Overview
This research pipeline tests whether individual precision‑weighting parameters inferred from a hierarchical predictive‑coding model on a Müller‑Lyer illusion predict susceptibility to a distinct Ponzo illusion. The analysis proceeds in four logical stages: (1) data ingestion, (2) model fitting, (3) susceptibility scoring, and (4) cross‑illusion prediction with robust resampling.

## Dataset Strategy
| Role | Dataset | Source (verified) | Loader | Key Variables Required |
|------|---------|-------------------|--------|------------------------|
| Training (Müller‑Lyer) | OpenNeuro Shard 0 | ` | `datasets.load_dataset(..., streaming=False)` | `subject_id`, `trial_id`, `stimulus_length`, `response_length`, `stimulus_parameters` |
| Test (Ponzo) | OpenNeuro Shard 1 | ` | same as above | `subject_id`, `trial_id`, `arrow_angle`, `depth_cue`, `perceived_length` |
| SusceptibilityScore | **Computed internally** (see Methodology). | – | – | – |

*If either parquet file lacks any of the required columns, the ingestion script aborts with a clear error message (see Edge Cases).*

## Methodology

### 1. Data Ingestion & Cleaning
- Load parquet with `datasets.load_dataset`.
- Verify SHA‑256 checksum against values recorded in the project SSoT state file.
- Drop rows with missing `response` or `perceived_length`; log counts.
- Compute per‑subject summary statistics (mean, SD) for sanity checks.
- Export clean CSVs (`clean_muller_lyer.csv`, `clean_ponzo.csv`).

### 2. Hierarchical Predictive‑Coding Model (Training)
- Model: Bayesian observer with precision parameter $\lambda$ governing the weighting of sensory evidence vs. prior.  
- Likelihood defined by Gaussian noise on perceived length.  
- Hierarchical: $\lambda$ drawn from a group‑level log‑normal prior (estimated jointly).  
- Optimization: `scipy.optimize.minimize` (L‑BFGS‑B) with bounds `[0.01, 10.0]`.  
- Convergence criteria: gradient norm < 1e‑6, log‑likelihood improvement > 1e‑4, no NaN/Inf.  
- Output per‑subject $\lambda$ (`precision_parameters.csv`) and per‑subject AIC/BIC.

### 3. Ponzo Susceptibility Scoring
- Generative model: perceived length = true length $\times$ (1 + $\beta\cdot$cue\_effect) + $\epsilon$, where $\beta$ captures susceptibility.  
- Fit $\beta$ per subject via ordinary least squares (closed‑form).  
- Store $\beta$ as `ponzo_susceptibility.csv`.

### 4. Cross‑Illusion Prediction & Validation
- **Power Analysis**: An *a priori* power analysis is conducted using `statsmodels` to determine if the available sample size of matched subjects is sufficient to detect a moderate effect (r $\approx$ 0.30) at $\alpha=0.05$, $\text{power}=0.80$.
- **Confound Control**: To account for systematic differences, subject-level covariates (age, gender) are regressed out of both $\lambda$ and $\beta$. The primary analysis is performed on the resulting residuals.
- **Primary analysis**: Pearson correlation `r` between $\lambda$ (training) and $\beta$ (test). Compute two‑tailed p‑value.  
- **Bootstrap**: 1000 resamples of matched subject pairs; derive 95 % CI for `r`.  
- **Control (shuffled IDs)**: Randomly permute subject IDs in the Ponzo table 1000 times; recompute `r` each time $\rightarrow$ null distribution centered at 0.  
- **Null model validation**: Fit a Ponzo‑specific predictive‑coding model (independent $\lambda'$) and compare its predictive performance ($\Delta$AIC, $\Delta$BIC) to the domain‑general $\lambda$.  
- **Multiple‑comparison handling**: Only one primary correlation is pre‑registered; we will explicitly note the single‑test nature (SC-005).  
- **Causal framing**: The design is observational; results will be described as associational (Principle VI).  

### Edge‑Case Handling
| Situation | Response |
|-----------|----------|
| Dataset download fails (HTTP error) | Abort with informative message; suggest manual download and placement in `data/raw/`. |
| Subject present in training but absent in test (or vice‑versa) | Exclude that subject from the merged analysis; log exclusion count. |
| Model fails to converge for a subject | Mark subject as “non‑convergent”; exclude from correlation; record reason in `fit_diagnostics.csv`. |

## Compute Rationale
All numerical work (optimization, bootstrapping, permutation) is performed with NumPy/SciPy on CPU. The worst‑case runtime is estimated at ~3-5 h on the GitHub Actions 2‑core runner, well within the 6 h limit. No GPU is required.

## Expected Deliverables
- Cleaned CSVs (`clean_muller_lyer.csv`, `clean_ponzo.csv`).  
- Parameter table (`precision_parameters.csv`).  
- Susceptibility table (`ponzo_susceptibility.csv`).  
- Correlation results JSON (`correlation_results.json`).  
- Diagnostic plots (`scatter.png`, `bootstrap_hist.png`, `fit_residuals.png`).  
- Checksums recorded in the SSoT state file.  