# Research: Molecular Property Prediction Pipeline

## Research Question
*Which topological interaction signatures (fingerprint bit‑pairs) are most predictive of logP, aqueous solubility, and boiling point, and how does a non‑linear Random Forest model capture non‑additive deviations relative to property‑specific additive baselines?*  

The question is framed as a **statistical** investigation of 2‑D fingerprint correlations, acknowledging that fingerprints are topological proxies for underlying 3‑D phenomena (see Constitution Principle VI).

## Dataset Strategy

### Verified Datasets

| Dataset | Source URL | Access Method | Key Fields |
|---------|------------|---------------|------------|
| PubChem Compound | https://pubchem.ncbi.nlm.nih.gov/ | `pubchempy` (Python API) | `CID`, `SMILES`, `logP`, `solubility`, `boiling_point`, `property_type` (must be `"Experimental"`), `measurement_uncertainty`, `logp_source` (must be `"Experimental"`), `confidence` |
| Open Babel | https://openbabel.org/ | CLI `obabel` | Fingerprint generation (MACCS, ECFP4, FP2) |

**Rationale** – PubChem provides open, programmatic access to real **experimental** measurements, satisfying FR‑001 and the constitution’s verification requirement. Open Babel is the de‑facto standard for generating the required fingerprints (FR‑003).

### Data Availability & Feasibility
- **Size**: A curated set of several thousand molecules (tens of megabytes in CSV format) fits comfortably within the runner’s disk quota.  
- **Streaming**: `download.py` can stream additional records if the set grows beyond 1 GB, preserving full‑dataset fidelity.  
- **Checksum**: Every file in `data/raw/` is SHA‑256 hashed and recorded in `state/artifact_hashes.yaml` (III. Data Hygiene).

## Methodological Rigor

### Modeling
- **Baseline** (required by Constitution Principle VI):  
  - **logP** – Crippen fragments via RDKit `Crippen` descriptors (experimental only).  
  - **Solubility & Boiling point** – Linear regressions on molecular weight & polar surface area (experimental only).  
- **Random Forest**: `sklearn.ensemble.RandomForestRegressor` with `n_estimators=300`, `max_depth=15`.  
- **Nested Cross‑Validation**: Outer 5‑fold CV for unbiased performance; inner 5‑fold CV inside each outer training split to tune `max_features` & `min_samples_leaf`. The inner loop never sees the outer hold‑out data, preventing leakage (fulfills FR‑004).

### Evaluation Metrics
- **Primary**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on outer‑fold test sets.  
- **Statistical Comparison**: Paired Wilcoxon signed‑rank test on absolute errors (RF vs. baseline) for each property.  
- **Multiple‑Comparison Correction**: Bonferroni adjustment (α = 0.05/3).  
- **Power Considerations**: With ≥ 5 000 molecules, power > 0.9 to detect a Cohen’s d = 0.2 effect (reported in `statistical_report.md`).  

### Explainability & Non‑Additivity
- **SHAP Values**: Computed with `shap.TreeExplainer` (CPU).  
- **SHAP Interaction Validation**: A permutation test (100 random shuffles of the target) recomputes interaction matrices; stability is assessed by the proportion of original interaction magnitudes exceeding the permutation distribution, reported in `shap_interaction_validation.txt`.  
- **Top‑K MACCS Selection**: Mean absolute SHAP values are averaged across molecules; the top K = 50 MACCS bits are retained for downstream interaction analysis.  
- **LNAI (Local Non‑Additivity Index)**: For each **pair among the top‑K bits** (≤1,225 pairs), compute **rank‑biserial correlation** between `(RF_error − Baseline_error)` and the **joint presence** of the two bits, applying a **prevalence filter** (each bit must appear in ≥5 % of molecules) and Benjamini‑Hochberg FDR (α = 0.05). Only pairs passing FDR < 0.05 are reported as significant interaction zones.  
- **MACCS‑SMARTS Mapping**: Use a curated `maccs_smart_lookup.json` to translate each selected MACCS bit into a SMARTS pattern; map back to molecules with RDKit substructure searches, producing `deviation_contexts.csv`.  

### Assumptions & Limitations
- **Observational Study**: All claims are correlational; no causal inference is attempted.  
- **Collinearity**: Fingerprint bits are inherently correlated; SHAP interaction values are interpreted with this in mind and validated via the permutation test.  
- **Construct Validity**: Only **experimental** property values are used; computed XLogP3 values are excluded, preserving the validity of the target variable.  

## Compute Feasibility
- **CPU‑first**: All heavy lifting (RF, SHAP, permutation tests, LNAI on ≤ 1,225 pairs) runs on the 2‑core CPU; estimated runtime ≤ 4 h.  
- **Memory**: Fingerprint matrices (~5 000 × 2 200 bits ≈ 1.4 MB) plus model objects fit well within 7 GB RAM.  
- **No GPU Needed**: The pipeline does not invoke CUDA; therefore no escape hatch is required.

## Decision / Rationale
- **Dataset**: PubChem is the only open, programmatic source meeting the variable requirements (SMILES + three target experimental properties).  
- **Model**: Random Forest balances interpretability (via SHAP) and computational tractability on CPU.  
- **Baseline**: Property‑specific additive baselines ensure scientific validity for each target property (Constitution Principle VI).  
- **Explainability**: SHAP interaction validation guards against over‑interpretation of noisy high‑dimensional interaction scores.  

## Deliverables (Generated by the pipeline)

| Artifact | Path | Description |
|----------|------|-------------|
| Raw PubChem CSV | `data/raw/pubchem.csv` | Immutable download (raw) |
| Data quality report | `data/derived/data_quality_report.csv` | Missing covariates, experimental‑data ratio |
| Verification log | `data/derived/verification_log.txt` | Reference‑Validator outcomes |
| Fingerprint arrays | `data/processed/*.npy` | MACCS (166 bits), ECFP4 (1024), FP2 (1024) |
| Baseline predictions | `data/derived/baseline_predictions.csv` |
| Baseline residual plot | `data/derived/baseline_residuals.png` |
| RF predictions | `data/derived/rf_predictions.csv` |
| RF residual plot | `data/derived/rf_residuals.png` |
| Test‑set split | `data/derived/test_set.csv` | CID, outer‑fold index, test‑set flag |
| Statistical report | `data/derived/statistical_report.md` |
| SHAP values (JSON) | `data/derived/predictions/*.json` | Conforms to `prediction.schema.yaml` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| SHAP interaction matrix (raw) | `data/derived/shap_interaction.npy` |
| SHAP interaction validation | `data/derived/shap_interaction_validation.txt` |
| Top‑K MACCS bits list | `data/derived/top_k_maccs.txt` |
| LNAI table | `data/derived/lna_index.csv` |
| Deviation contexts (MACCS‑SMARTS) | `data/derived/deviation_contexts.csv` |
| Validation summary | `data/derived/validation_summary.csv` |

All artifacts will be validated against the JSON/YAML contracts in `contracts/`.

---


