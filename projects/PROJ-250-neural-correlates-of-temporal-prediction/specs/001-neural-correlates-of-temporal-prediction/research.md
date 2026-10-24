# Research: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Dataset Strategy

| Decision | Rationale |
|----------|-----------|
| **Dataset**: `clane9/openneuro-fslr64k` (Hugging Face) | Publicly downloadable, verified URL, fits the CI runner. Contains BIDS‑style `events.tsv` that we will inspect for `condition_label` values `simple` and `complex`. |
| **Fallback**: If `complex` is absent, the pipeline aborts with the explicit message required by FR‑008. No synthetic data is generated. | Aligns with the specification’s “hard stop” policy. |

### Acquisition Steps
1. `datasets.load_dataset("clane9/openneuro-fslr64k", streaming=False)` – loads the full dataset into local `data/raw/`.
2. Compute SHA‑256 checksum of each downloaded file; store in `state/...yaml`.
3. Parse `events.tsv` for each subject; verify that both `simple` and `complex` appear at least once. If not, raise `DatasetConditionError`.

## Preprocessing Pipeline (MNE‑Python)

| Step | Parameters | Purpose |
|------|------------|---------|
| Band‑pass filter | 1 Hz – 40 Hz (FIR, zero‑phase) | Remove DC drift & high‑frequency noise while preserving MMN. |
| ICA | `n_components=0.99` variance explained, automatic EOG component detection | Eliminate blink & eye‑movement artifacts that overlap fronto‑central sites. |
| Re‑reference | Average of mastoid electrodes (`TP9`, `TP10`) | Standard reference for auditory ERP studies. |
| Baseline correction | Mean of –200 ms → 0 ms subtracted from each epoch | Removes slow drifts; required for accurate amplitude measurement. |
| Epoching | –200 ms to 500 ms relative to stimulus onset | Matches spec window; enables pre‑stimulus baseline calculation. |
| Condition labeling | Use `condition_label` column in `events.tsv` to assign “simple” or “complex”. | Guarantees the independent variable is not derived from stimulus type. |
| Subject exclusion | Exclude if > 50 % of epochs are rejected post‑ICA | Implements edge‑case handling. |
| Channel interpolation | Spherical spline interpolation if < 10 % of channels missing | Preserves topographic fidelity per spec. |

All steps are deterministic; random seeds for ICA are fixed (`random_state=42`).

## Statistical Methodology

### MMN Quantification
* **Window of Interest**: 150 ms – 250 ms post‑stimulus.  
* **Electrode Cluster**: `['Fz','FCz','Cz','F3','F4','FC3','FC4']`.  
* **Amplitude**: Mean voltage difference (deviant – standard) within the window.  
* **Latency**: Time of maximal difference within the window.  

### Signal‑Validity Check (SC‑001)
* Compute baseline SEM = `std(pre‑stimulus) / sqrt(N_trials)`.  
* SNR = `|amplitude| / SEM`.  
* Enforce `SNR ≥ 3.0`; otherwise flag `signal_validity = False` and exclude the subject from group statistics.

### Topographic Consistency & Validity (SC‑004)
* **Canonical Template**: Average `deviant – standard` topography across all subjects in the *simple* condition; saved as `data/templates/canonical_mmn.npy`.  
* **Consistency**: Pearson‑r between each subject’s simple‑condition topography and the canonical template; require `r ≥ 0.8`.  
* **Validity**: Pearson‑r between each subject’s complex‑condition topography and the same template; require `r ≥ 0.8`.  

### Hypothesis Testing (SC‑002)
* Paired t‑test on per‑subject MMN amplitude (simple vs complex).  
* Apply Benjamini‑Hochberg FDR across the electrode cluster.  
* Report `t`, raw `p`, `p_fdr`, and `significant` flag (`p_fdr < 0.05`).  

### Effect‑Size Benchmark (SC‑003)
* Compute Cohen’s d for the paired difference.  
* Load benchmark JSON `data/benchmarks/mmn_effect_sizes.json` which stores `{ "medium_effect_d": 0.5 }`.  
* Flag `practical_significance = True` if `d ≥ 0.5`.

All statistical calculations use `scipy.stats` (t‑test) and `statsmodels.stats.multitest` (FDR).

## Compute Feasibility

* **CPU‑first**: All heavy lifting (filtering, ICA, regression) runs on NumPy/SciPy which are fully CPU‑optimized.  
* **Memory Management**: Process subjects sequentially; `Epochs` are saved to disk (`.fif`) and loaded on demand.  
* **Runtime Estimate**: [deferred] per subject on the free runner; full cohort (< 20 subjects) fits comfortably within the 6 h limit.
* **No GPU required** – the pipeline does not contain any CUDA‑dependent code.

## Decision / Rationale Table

| Decision | Rationale |
|----------|-----------|
| Use 1‑40 Hz band‑pass | Preserves MMN while removing drift & muscle noise. |
| ICA with [deferred] variance | Guarantees removal of dominant ocular artifacts without over‑fitting. |
| Baseline subtraction (-200 ms → 0 ms) | Standard ERP practice; required for SNR computation. |
| Paired t‑test + Benjamini‑Hochberg | Controls Type I error across multiple electrodes (SC‑002). |
| SNR ≥ 3.0 (SEM denominator) | Ensures the MMN is not a noise fluctuation (SC‑001). |
| Cohen’s d benchmark ≥ 0.5 | Aligns with literature‑derived medium effect threshold (SC‑003). |
| Topographic Pearson‑r ≥ 0.8 | Provides a stringent neurophysiological consistency check (SC‑004). |
| Halt if “complex” condition missing | Enforces FR‑008 hard stop; prevents meaningless analysis. |
| Reference‑Validator at three stages | Satisfies FR‑012 and Constitution Principle II. |

---
