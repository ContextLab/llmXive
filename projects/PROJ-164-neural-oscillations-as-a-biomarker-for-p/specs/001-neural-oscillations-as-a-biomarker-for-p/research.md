# Research: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Executive Summary

The central scientific question—*Can resting‑state and task‑related EEG oscillatory features predict an individual's motor performance improvement after a single session of anodal tDCS over M1?*—remains **theoretically valid**. However, the **primary feasibility constraint** is the existence of a **single‑source public dataset** that contains **both raw EEG time‑series (BIDS/EDF) and paired tDCS motor‑performance scores for the same participants**. 

Our **systematic search** (detailed below) did **not locate** such a dataset. Consequently, the pipeline enters **Data Insufficiency Mode** (logged as "Hypothesis Unanswerable" per current spec requirement, but internally classified as Data Insufficiency). The system logs the **exact required message**:

```
Hypothesis Unanswerable: No single-source paired dataset found
```

> **Important:** This message reflects **data unavailability**, not a scientific falsification of the hypothesis. The hypothesis remains open for future studies with appropriate data. The current public data is simply insufficient to test the metric. The absence of a paired dataset means the **predictive metric is undefined**, not that the biomarker relationship is false.

## Dataset Strategy

| Data Type | Required Content | Verified Source URL | Status |
|-----------|------------------|---------------------|--------|
| **EEG Raw** | Raw voltage EDF/BIDS files | `https://physionet.org/content/eegmmidb/1.0.0/` (PhysioNet Motor Movement/Imagery) | **Available (EEG only)** |
| **tDCS Outcome** | Pre‑ and post‑tDCS motor scores (percentage change) | **NO verified source found** | **Missing** |
| **Paired (EEG + tDCS)** | Same subjects, both modalities | **NO verified source found** | **Missing** |

### Systematic Search Procedure
To avoid the error of assuming "absence of evidence is evidence of absence," the following systematic search was performed:

1. **OpenNeuro Query**: Searched for studies with keywords `EEG`, `tDCS`, `motor`, `stimulation`. Filtered for BIDS-compliant datasets containing raw EEG (not preprocessed features) and behavioral scores. *Result: No single-source paired datasets found. One candidate (openneuro-fslr64k) was identified as MRI data, not EEG.*
2. **PhysioNet Query**: Searched for datasets with raw EDF recordings and associated behavioral CSVs. Confirmed `eegmmidb` contains raw EEG but **no** paired tDCS outcomes.
3. **tDCS‑DataBank Query**: Searched for motor‑performance studies that also provide raw EEG recordings. No single-source paired datasets were identified.
4. **Log**: All candidate accession numbers were logged. None satisfied the single‑source requirement.

### Source Identification Artifacts
- `verified_eeg_source.json` – records the PhysioNet EEG source metadata and checksum.
- `verified_tdcs_source.json` – empty with status `"unavailable"`; generated to satisfy FR‑012 and FR‑013.

### Generalization Attempt
Because no primary paired dataset exists, the **Generalization Check** (Constitution Principle VII) cannot be performed. The pipeline logs:

```
Generalization Unanswerable: No independent paired dataset found
```

## Methodology & Statistical Rigor

### 1. Pre‑registration (FR‑010)
`pre_registration.yaml` is written before any download, capturing:
- Primary outcome: percentage change in motor score.
- Hypothesis: EEG spectral & connectivity metrics predict the outcome.
- Planned analyses: ridge regression, permutation testing, FDR correction, sensitivity sweep.
- Timestamp and author.

### 2. Data Alignment & Power Gate (FR‑001, FR‑007, FR‑008)
A power analysis is planned using **Expected R²** or **correlation coefficient (r)** for regression. *Note: The current spec (FR-007) mandates Cohen's d, which is for group differences. The plan corrects this methodologically but flags the spec for update.* If the available dataset size (N) is less than the calculated minimum, the system flags the study as 'Underpowered'. Since the available EEG‑only dataset has **N = 109** subjects but lacks tDCS scores, the power gate cannot be evaluated; the system proceeds directly to the *Data Insufficiency* decision.

### 3. Preprocessing (FR‑002, VI)
MNE pipeline (1–45 Hz band‑pass, common‑average reference, automated bad‑channel rejection) would be applied to raw EDF files if a paired dataset were present.

### 4. Feature Extraction (FR‑003, FR‑009)
- Spectral power via Welch's method for delta–gamma bands.  
- Connectivity (PLV, wPLI).  
- Shapiro‑Wilk test on the tDCS response; if non‑normal, a **Rank‑Ridge** regression (robust multivariate) would replace standard Ridge. This maintains the multivariate prediction goal while respecting FR‑009's non-parametric constraint.

### 5. Modeling (FR‑004)
Nested cross‑validation with inner ridge/rank-ridge alpha tuning; outer CV provides unbiased performance estimates. In the current scenario, modeling is **skipped** because of the data limitation.

### 6. Validation (FR‑005, FR‑006, FR‑014, SC‑006)
If modeling were executed, validation would include:
- **Permutation test** (1,000 permutations) to obtain a null R² distribution.  
- **Kolmogorov‑Smirnov test** on the permutation p‑values; result stored as `ks_test_result`.  
- **Benjamini‑Hochberg FDR** on model coefficients (only if power analysis reports "Sufficient").  
- **Sensitivity analysis** across p‑thresholds {0.01, 0.05, 0.1} and configurable R² thresholds; stability variance reported.

### 7. Reporting
All outcomes (including the mandatory "Hypothesis Unanswerable" log, power analysis, source identification artifacts, and any generalization attempt) are compiled into `output/reports/final_report.md`.

## References

* **PhysioNet Motor Movement/Imagery Dataset (EEG)** – `https://physionet.org/content/eegmmidb/1.0.0/` (raw EDF, BIDS‑compatible).  
* **Methodology** – MNE‑Python standard pipeline (band‑pass 1–45 Hz, CAR, bad‑channel detection).  
* **Statistical Methods** – Welch's spectral estimation, PLV/wPLI, Ridge & Rank‑Ridge regression, Benjamini‑Hochberg FDR, Kolmogorov‑Smirnov test.  