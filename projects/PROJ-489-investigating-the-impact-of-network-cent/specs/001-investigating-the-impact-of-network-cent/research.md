# Research: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Research Question
Do waking‑state **inter‑hemispheric coherence** metrics (theta (4‑8 Hz) and alpha (8‑13 Hz) coherence between Fpz‑Cz and Pz‑Oz) predict the magnitude of neural synchrony (Phase‑Locking Value, PLV) observed during each sleep stage (N1, N2, N3, REM), after accounting for medication status, sleep‑quality score, and EEG‑noise level?

## Methodological Approach

### 1. Data Acquisition & Preprocessing
| Item | Details |
|------|---------|
| **Source** | PhysioNet Sleep‑EDF (Hugging  Face mirror) |
| **Verified URL** | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` |
| **Inclusion Criteria** | • ≥ 2 min continuous, artifact‑free waking segment.<br>• At least one annotated epoch for each sleep stage (N1, N2, N3, REM).<br>• Presence of the two EEG channels (Fpz‑Cz, Pz‑Oz) required for inter‑hemispheric coherence. |
| **Filtering** | Band‑pass 0.5–45 Hz (SciPy FIR, zero‑phase). |
| **Artifact Removal** | ICA (MNE); reject components with kurtosis > 5.0 **or** high‑frequency power > 3 × baseline (0.5–2 Hz median power). |
| **Epoching** | Non‑overlapping 30 s windows (epoch length = 30 s, source 1908.11463). |
| **Night‑ID Extraction** | EDF header date used to create `waking_night_id` and `sleep_night_id`. |

### 2. Waking Inter‑Hemisphere Coherence
- **Bands**: Theta (4–8 Hz) and Alpha (8–13 Hz).  
- **Connectivity**: Magnitude‑squared coherence computed **between the two channels** (Fpz‑Cz ↔ Pz‑Oz) for each band, yielding a single coherence value per band per subject (range 0–1).  

### 3. Coherence Stability Check
- **Metric**: Split‑half Intraclass Correlation (ICC) computed on the two halves of the waking segment for each band’s coherence value.  
- **Threshold**: ICC ≥ 0.6 required to proceed without a stability warning (FR‑015).

### 4. Sleep‑Stage Neural Synchrony
- **Metric**: Phase‑Locking Value (PLV) computed across all available channel pairs per epoch (MNE).  
- **Aggregation**: Mean global PLV per sleep stage per subject (float ∈ [0, 1]).

### 5. Aggregation & Validation
- Combine coherence values, ICCs, and stage‑wise PLVs into `SubjectMetrics.csv` (one row per subject per stage).  
- Validate against `contracts/dataset.schema.yaml`.

### 6. Sample‑Size Verification
- Require **N ≥ 50** subjects after filtering; if fewer, pipeline aborts with “Insufficient Sample Size” warning (FR‑010).  

### 7. Normality Testing & Correlation Selection
- Shapiro‑Wilk test on each predictor‑outcome pair (SciPy).  
- **Pearson** if both p ≥ 0.05; otherwise **Spearman** (internal to FR‑006).

### 8. Covariate Adjustment & Missing Data Policy
- Partial correlation controlling for **medication status, sleep‑quality score, EEG‑noise level** (FR‑014).  
- **Missing covariate handling**: subjects missing *any* of the three covariates are excluded from the covariate‑adjusted analysis (listwise deletion); the effective N is reported per test.

### 9. Correlation Analysis
- **Tests**: 2 coherence metrics × 4 sleep stages = **8** primary tests.  
- Compute coefficient, raw *p*, and store method used.

### 10. Multiple‑Comparison Control
- **Benjamini‑Hochberg FDR** correction across the 8 tests (α = 0.05) as required by FR‑007.

### 11. Power Assessment
- **A‑priori**: Using `statsmodels.stats.power`, α = 0.05/8 ≈ 0.00625, desired power = 0.80, effect size ≈ 0.30 → N ≈ 50 subjects. This justification is reported in the methods.  
- **Post‑hoc**: Compute achieved power for each observed effect size given the actual N (reported in the final Markdown).

### 12. Reporting
- **JSON** (`analysis_results.json`) with full statistics.  
- **Markdown** (`report.md`) containing:  
  - Dataset description & filtering summary.  
  - Table of correlation results (highlighting `q_corrected < 0.05`).  
  - **Confounding Limitation**: flag subjects where `waking_night_id == sleep_night_id`.  
  - **ICC Diagnostics**: split‑half ICC values for theta and alpha coherence, with flags for ICC < 0.6.  
  - **Power Discussion**: a‑priori justification, post‑hoc power estimates, and caveats.  
  - **Causal Disclaimer**: all findings are correlational.  

## Dataset Strategy

| Dataset | Description | Verified URL | Fit Verification |
|---------|-------------|--------------|------------------|
| **PhysioNet Sleep‑EDF** (Hugging  Face mirror) | Polysomnographic EEG (two channels) with sleep‑stage annotations and brief pre‑sleep wake. | `https://huggingface.co/datasets/ronaldvandenbroek/physionet-sleep-data/resolve/main/physionet-sleep-data-full.zip` | Contains required two EEG channels for inter‑hemispheric coherence, sleep‑stage labels, and wake segments. Wake ≥ 2 min enforced; if insufficient subjects remain, pipeline aborts (transparent limitation). |

**Decision/Rationale**: The mirror provides programmatic download, checksum verification, and all necessary signals. Using the two‑channel coherence predictor respects the dataset’s limitations while still testing the research hypothesis after spec revision.

## Statistical Rigor & Assumptions
- **Multiple Comparisons** – Benjamini‑Hochberg FDR (α = 0.05).  
- **Power** – Minimum N ≥ 50 enforced; a‑priori power analysis justifies this threshold; post‑hoc power reported per test.  
- **Observational Design** – No randomization; all statements are correlational.  
- **Missing Sleep Stages** – Excluded from that stage‑specific correlation; no imputation.  
- **Data Corruption** – Corrupted EDF files are logged, skipped, and do not stop the run.  
- **Temporal Confounding** – Same‑night waking/sleep flagged in report.  
- **Normality** – Shapiro‑Wilk determines Pearson vs. Spearman (internal to FR‑006).  
- **Covariate Handling** – Listwise deletion for any missing covariate; effective N reported.  
- **ICC Stability** – Split‑half ICC may be low for some subjects; flagged in the report.  

## Limitations
1. **Two‑Channel Constraint** – Only inter‑hemispheric coherence can be derived; graph‑theoretic centrality is not computable with this dataset.  
2. **Wake Duration** – The ≥ 2 min wake filter may reduce usable subjects, limiting statistical power.  
3. **Sample Size** – If fewer than 50 subjects survive filtering, the study is under‑powered; the pipeline aborts with a clear warning.  
4. **Stability** – Split‑half ICC may be low for some subjects; flagged in the report.  
5. **Observational Nature** – No causal inference; all findings are associational.  

---



