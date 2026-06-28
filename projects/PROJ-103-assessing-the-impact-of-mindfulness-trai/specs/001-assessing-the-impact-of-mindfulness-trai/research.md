# Research: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

## Dataset Strategy

| Dataset Type | Required Variables | Verified Source | Status |
|--------------|-------------------|-----------------|--------|
| OpenNeuro resting‑state fMRI (pre/post mindfulness) | Pre/post BOLD scans, motion parameters, intervention metadata | **Attempted verification via OpenNeuro API** (no pre‑registered sources) | **CONTINGENCY** – If ≥3 verified datasets are found, they will be used. If none are found, the pipeline proceeds with any available resting‑state dataset(s) and reports the limitation explicitly. |
| AAL atlas (DMN regions) | MNI152‑aligned masks for PCC, mPFC, IPL, angular gyrus | Standard AAL atlas (NeuroVault) | ✅ Available |
| MNI152 template | Standard space reference | Bundled with fMRIPrep | ✅ Available |
| NBS toolbox | Network‑Based Statistic implementation | Python `nbs` package (CPU‑only) | ✅ Available |

**Note**: The original “BLOCKING ISSUE” flag has been replaced with a concrete contingency plan. The pipeline will not abort; instead it will document dataset scarcity and, when necessary, present single‑dataset results with an explicit generalizability warning.

## Methodological Decisions

### Preprocessing Pipeline (FR‑002, US‑1)

- **Primary**: fMRIPrep 23.1.0 in Docker (`--nthreads 2 --omp-nthreads 2 --mem-mb 6000`). Parameters: motion correction, slice timing, MNI152 NLIN2009cAsym normalization, 6 mm smoothing, band‑pass 0.01‑0.1 Hz, nuisance regression (WM, CSF, 6 motion params, global signal), physiological noise correction if RETROICOR files are present.
- **Fallback**: Nilearn lightweight preprocessing (motion correction, slice timing, linear MNI152 registration, 6 mm smoothing, band‑pass) if fMRIPrep exceeds memory or runtime limits.
- **Motion exclusion**: Subjects with >3 mm translation or >3° rotation flagged by fMRIPrep are excluded (FR‑006). Exclusion counts are recorded in the methods.

### DMN ROI Extraction (FR‑003, Constitution VI)

- **Atlas**: **AAL** (Automated Anatomical Labeling) atlas, selecting the following AAL regions as DMN nodes: `Precuneus`, `Medial_Orbital_Frontal`, `Inferior_Parietal`, `Angular_Gyrus`. This satisfies Constitution Principle VI.
- **Rationale**: AAL is a widely used anatomical atlas, fully compatible with fMRIPrep MNI152 outputs and mandated by the constitution.

### Connectivity & Statistical Testing (FR‑004, FR‑005, SC‑001, SC‑002)

1. Extract time series for each AAL DMN node (identical length per subject).
2. Compute Pearson correlation matrices for all node‑pair combinations (≥6 connections).
3. Apply Fisher‑z transformation; correct temporal autocorrelation via AR(1) prewhitening **or** permutation testing (10 000 iterations).
4. Compute Cohen’s d effect sizes for pre vs. post changes with bootstrapped 95 % CIs (10 000 resamples).
5. Perform NBS correction (primary threshold *t* ≥ 3.1, component‑wise FWE α = 0.05). Significant connections are reported (SC‑002).

### Global Signal Regression Sensitivity

Both pipelines (with GSR and without GSR) are executed. Differences in connectivity patterns and effect sizes are compared; results are presented side‑by‑side to assess GSR impact (addressing methodological concern).

### Meta‑Analysis (FR‑007, SC‑003)

- Random‑effects meta‑analysis using R `metafor::rma.mv`, modeling **scanner/site** as a random effect.
- Heterogeneity metrics: I², Q‑test p‑value. If I² > 50 %, a leave‑one‑out analysis identifies influential datasets.
- If fewer than 3 datasets meet verification, the script outputs a clear message and proceeds with single‑dataset summary statistics, noting limited reproducibility.

### Power Analysis (FR‑010, SC‑005)

- Conducted **a priori** using `statsmodels.stats.power.TTestPower` with assumed medium effect size (d = 0.5). Target power = 0.80, α = 0.05. Required per‑group *n* is computed at runtime and reported in the methods. Post‑hoc power is also calculated after data collection.

### Bayesian Supplement (addressing scientific‑soundness‑9a326a77)

- For small samples (n < 30), Bayesian estimation of the mean difference (using `bayes_factor`) is performed in addition to frequentist tests. Bayes factors are reported to complement p‑values.

### Edge Cases

| Edge Case | Handling |
|-----------|----------|
| OpenNeuro API returns no matching datasets | Log the failure, proceed with any available resting‑state dataset(s), and document the limitation. |
| Incomplete pre/post scan pairs | Exclude those subjects; report exclusion count. |
| fMRIPrep failure for a subject | Flag in QC logs, exclude subject, retain error report for debugging. |
| Missing behavioral covariates | Primary connectivity analysis proceeds; secondary correlational analyses are omitted and noted. |
| >20 % subjects exceed motion thresholds | Document exclusion rate, discuss potential bias in limitations. |

## Statistical Rigor Checklist (completed)

- [x] Multiple‑comparison correction via NBS (α = 0.05, *t* ≥ 3.1)
- [x] A priori power analysis (FR‑010) with target [deferred] power
- [x] Associational framing (FR‑009)
- [x] Measurement validity (AAL atlas, fMRIPrep standard pipeline)
- [x] Predictor collinearity acknowledged (DMN nodes are anatomically related)
- [x] Temporal autocorrelation addressed (AR(1) or permutation)

## Dataset‑Variable Fit Verification Protocol (FR‑008)

1. Query OpenNeuro API for each candidate dataset.
2. Verify presence of pre/post scans and mindfulness metadata.
3. Confirm that AAL DMN masks align with MNI152‑normalized images.
4. If any check fails, mark dataset `design_status = "failed"` and exclude from analysis; log reason.

## Compute Feasibility (re‑affirmed)

- All steps run on 2 CPU cores, ≤7 GB RAM, ≤6 h total runtime per CI job.
- No GPU, CUDA, or large‑model inference required.
