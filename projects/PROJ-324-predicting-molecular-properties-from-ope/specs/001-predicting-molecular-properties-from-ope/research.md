# Research: Molecular Property Prediction Pipeline

## Research Question
*Which topological interaction signatures (fingerprint bit‑pairs) are most predictive of logP, aqueous solubility, and boiling point, and how does a non‑linear Random Forest model capture non‑additive deviations relative to property‑specific additive baselines?*

The question is framed as a **statistical** investigation of 2‑D fingerprint correlations, acknowledging that fingerprints are topological proxies for underlying 3‑D phenomena (see Constitution Principle VI).

## Dataset Strategy

### Verified Datasets

| Dataset | Source URL | Access Method | Key Fields |
|---------|------------|---------------|------------|
| PubChem Compound | https://pubchem.ncbi.nlm.nih.gov/ | `pubchempy` (Python API) | `CID`, `SMILES`, `logP`, `solubility`, `boiling_point`, `property_type` (Experimental/Computed) |
| Open Babel | https://openbabel.org/ | CLI `obabel` | Fingerprint generation (MACCS, ECFP4, FP2) |

**Rationale** – PubChem provides open, programmatic access to real experimental measurements (when available) and flags whether a property is experimental, satisfying FR‑001 and the [deferred] experimental‑data guard. Open Babel is the de‑facto standard for generating the required fingerprints (FR‑003).

### Data Availability & Feasibility
- **Size**: A curated set of several thousand molecules (~30 MB CSV) fits comfortably within the runner’s disk quota.  
- **Streaming**: `download.py` can stream additional records if the set grows beyond 1 GB, preserving full‑dataset fidelity.  
- **Checksum**: Every file in `data/raw/` is SHA‑256 hashed and recorded in `state/artifact_hashes.yaml` (III. Data Hygiene).

## Methodological Rigor

### Modeling
- **Baseline**: Property‑specific additive baselines:  
  - **logP** – Crippen fragments via RDKit `Crippen` descriptors.  
  - **Solubility** – Simple linear regression on molecular weight and polar surface area.  
  - **Boiling point** – Simple linear regression on molecular weight and polar surface area.  
- **Random Forest**: `sklearn.ensemble.RandomForestRegressor` with `n_estimators=300`, `max_depth=15`.  
- **Nested Cross‑Validation**: Outer 5‑fold CV for unbiased performance estimation; **inner 5‑fold CV inside each outer training split** for hyper‑parameter tuning (`max_features`, `min_samples_leaf`). The inner loop never sees the outer hold‑out data, preventing leakage (fulfills FR‑004).

### Evaluation Metrics
- **Primary**: Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on outer‑fold test sets.  
- **Statistical Comparison**: Paired Wilcoxon signed‑rank test on absolute errors (RF vs. baseline) for each property.  
- **Multiple‑Comparison Correction**: Bonferroni adjustment (α = 0.05/3).  
- **Power Considerations**: With ≥ 5 000 molecules, power > 0.9 to detect a Cohen’s d = 0.2 effect (reported in `statistical_report.md`).  

### Explainability & Non‑Additivity
- **SHAP Interaction Values**: Computed with `shap.TreeExplainer` (CPU).  
- **Bit‑to‑Substructure Mapping**: Only **MACCS** bits have deterministic substructure definitions; high‑importance MACCS bits are translated to SMARTS patterns via `code/data/rules.py`. Hashed bits from ECFP4/FP2 are reported as “uninterpretable” and excluded from substructure analysis.  
- **Local Non‑Additivity Index (LNAI)**: For each fingerprint bit‑pair (i, j), LNAI = *point‑biserial correlation* between `(RF_error − Baseline_error)` and the binary presence of both bits.  
- **Multiple‑Testing Correction for LNAI**: Benjamini‑Hochberg FDR correction (α = 0.05); only pairs with FDR < 0.05 are reported as significant interaction zones.  
- **Measurement Validity**: Only experimental measurements are used for model training and baseline fitting. Computed values are excluded from training but retained for optional consistency reporting.  

### Assumptions & Limitations
- **Observational Study**: All claims are correlational; no causal inference is attempted.  
- **Collinearity**: Fingerprint bits are inherently correlated; SHAP interaction values are interpreted with this in mind.  
- **Construct Validity**: 2‑D fingerprints capture topological, not full 3‑D steric/electronic effects; manuscript language will use “topological proxy” (see `contracts/interaction_context.schema.yaml`).  

## Compute Feasibility
- **CPU‑first**: All heavy lifting (RF, SHAP) runs on the 2‑core CPU; estimated runtime ≤ 4 h.  
- **Memory**: Fingerprint matrices (~5 000 × 2 200 bits ≈ 1.4 MB) plus model objects fit well within 7 GB RAM.  
- **No GPU Needed**: The pipeline does not invoke CUDA; therefore no escape hatch is required.

## Decision / Rationale
- **Dataset**: PubChem is the only open, programmatic source meeting the variable requirements (SMILES + three target properties + experimental flag).  
- **Model**: Random Forest balances interpretability (via SHAP) and computational tractability on CPU.  
- **Baseline**: Property‑specific additive baselines ensure scientific validity for each target property.  
- **Explainability**: MACCS mapping avoids unreliable interpretation of hashed bits; hashed bits are explicitly excluded.  

## Deliverables (Generated by the pipeline)
| Artifact | Path | Description |
|----------|------|-------------|
| Raw PubChem CSV | `data/raw/pubchem.csv` | Immutable download (raw) |
| Data quality report | `data/derived/data_quality_report.csv` | Missing covariates, experimental‑data ratio |
| Fingerprint arrays | `data/processed/*.npy` | MACCS (166 bits), ECFP4 (1024), FP2 (1024) |
| Baseline predictions | `data/derived/baseline_predictions.csv` |
| Baseline residual plot | `data/derived/baseline_residuals.png` |
| RF predictions | `data/derived/rf_predictions.csv` |
| RF residual plot | `data/derived/rf_residuals.png` |
| Statistical report | `data/derived/statistical_report.md` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| SHAP interaction matrix (raw) | `data/derived/shap_interaction.npy` |
| Prediction records (JSON) | `data/derived/predictions/*.json` | Conforms to `prediction.schema.yaml` |
| Deviation contexts (bit‑to‑substructure) | `data/derived/deviation_contexts.csv` |
| LNAI table | `data/derived/lna_index.csv` |
| Conformational limitations audit | `data/derived/conformational_limitations.csv` |
| Verification log | `data/derived/verification_log.txt` | Reference‑Validator outcomes |
| Comprehensive validation audit | `data/derived/validation_audit.pdf` |
| Experimental validation protocol | `data/derived/experimental_validation_protocol.md` |

All artifacts will be validated against the JSON/YAML contracts in `contracts/`.

---

