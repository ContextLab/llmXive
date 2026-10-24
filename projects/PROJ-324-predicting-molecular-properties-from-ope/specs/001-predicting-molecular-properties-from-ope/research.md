# Research: Molecular Property Prediction Pipeline

## Research Question
*Which topological interaction signatures (fingerprint bit‑pairs) are most predictive of logP, aqueous solubility, and boiling point, and how does a non‑linear Random Forest model capture non‑additive deviations relative to property‑specific additive baselines?*  

The question is framed as a **statistical** investigation of 2‑D fingerprint correlations, respecting Constitution Principle VI (explicit baseline comparison) and acknowledging that correlations do not imply causation.

## Dataset Strategy

### Verified Datasets

| Dataset | Source URL | Access Method | Key Fields |
|---------|------------|---------------|------------|
| PubChem Compound | https://pubchem.ncbi.nlm.nih.gov/ | `pubchempy` (Python API) | `CID`, `IsomericSMILES`, `logP`, `solubility`, `boiling_point`, `property_type` (must be `"Experimental"`), `measurement_uncertainty`, `confidence` |
| Open Babel | https://openbabel.org/ | CLI `obabel` | Generation of MACCS and ECFP4 fingerprints (FP2 omitted) |

*Rationale*: PubChem provides open, programmatic access to **experimental** measurements, satisfying FR‑001 and the constitution’s verification requirement. Open Babel is the standard tool for the required fingerprints (FR‑003).

### Data Availability & Feasibility
- **Size**: The curated experimental subset contains a few thousand molecules (approximately a few megabytes in CSV format).  
- **Streaming**: `download.py` can stream additional PubChem records if needed, but the default set fits comfortably within the runner’s 14 GB disk.  
- **Checksum**: SHA‑256 recorded in `state/artifact_hashes.yaml` (III. Data Hygiene).  

## Methodological Rigor

### Modeling
- **Additive Baselines** (required by Constitution Principle VI):  
  - **logP** – Crippen fragments via RDKit (`MolLogP`).  
  - **Solubility & Boiling Point** – Linear regressions on molecular weight and polar surface area (trained on the experimental subset).  
- **Random Forest**: `sklearn.ensemble.RandomForestRegressor` with `n_estimators=300`, `max_depth=15`, `random_state=42`.  
- **Nested Cross‑Validation**: Outer 5‑fold CV for unbiased performance; inner 5‑fold CV tunes `max_features` and `min_samples_leaf`. Random seed fixed (42) for reproducibility (IV. Reproducibility).

### Evaluation Metrics
- **Primary**: MAE and RMSE on outer‑fold test sets (target thresholds MAE ≤ 0.5, RMSE ≤ 0.7 logP units).  
- **Statistical Comparison**: Three **property‑wise** paired Wilcoxon signed‑rank tests on absolute errors (RF vs. baseline) with **Holm‑Bonferroni** correction (α = 0.05). To guard against heteroscedasticity across properties, we also compute a **non‑parametric bootstrap test** of the combined error reduction (1 000 resamples) and report its confidence interval.  
- **Baseline generation**: Compute additive‑fragment XlogP3 values for all molecules; store residuals.  
- **SHAP interaction significance**: Compute SHAP interaction values; assess via **bootstrap‑of‑model** (200 resamples) rather than target permutation, retaining interactions where observed magnitude exceeds the 95th percentile of the bootstrap distribution.  
- **LNAI (Local Non‑Additivity Index)**:  
  1. **Top‑K selection** – rank MACCS bits by **mean absolute SHAP interaction strength** **computed only on inner‑validation folds**; select the top‑ranked bits (resulting in a large set of pairs). This split‑based selection eliminates leakage.  
  2. For each pair, require **marginal prevalence ≥ 5 %** for each bit and **joint prevalence ≥ 5 %**; **regress out each bit’s main effect** from `(RF_error − Baseline_error)`, then compute **rank‑biserial correlation** between the residuals and the joint‑presence indicator.  
  3. Assess significance with **2 000 permutations** (Numba‑accelerated) and apply Benjamini‑Hochberg FDR (α = 0.05).  
  4. **Power analysis** (Task T015c) estimates detectable effect size given N≈5 000 and ~4 950 tests; a warning is logged if power < 0.8.  
- **Per‑molecule LNAI**: Average significant pairwise LNAI scores for each molecule; output `lna_index_per_molecule.csv`.  
- **SMARTS mapping**: Use `reference/maccs_smart_lookup.json` to translate **all** selected MACCS bits to SMARTS; match against molecules via RDKit `GetSubstructMatches`.  
- **Precision/Recall Evaluation**: Compare mapped substructures to the curated reference set (`reference/substructures.yaml`); required thresholds: precision ≥ 0.8, recall ≥ 0.7 (recorded in `mapping_metrics.txt`).  

### Explainability & Non‑Additivity
- **SHAP Values**: Computed with `shap.TreeExplainer` (CPU).  
- **SHAP Interaction Validation**: **Bootstrap‑of‑model** (200 resamples) provides a proper null distribution for interaction magnitudes.  
- **Top‑K MACCS Selection**: Split‑based, interaction‑strength driven, avoiding main‑effect bias.  
- **LNAI**: Main‑effect regression, prevalence filters, permutation testing, FDR correction, and power analysis ensure statistical rigor.  
- **Expert Validation**: Two independent chemists review the Interaction‑Zone Report PDF; their acceptance statements compiled into `validation_report.pdf` (FR‑011).  

### Assumptions & Limitations
- **Observational**: All conclusions are correlational; no causal claims are made.  
- **Collinearity**: Fingerprint bits are not independent; SHAP interaction significance is tempered by the bootstrap approach and main‑effect adjustment.  
- **Construct Validity**: Only **experimental** property values are used; any computed estimates are filtered out during preprocessing.  

## Deliverables (Generated by the pipeline)

| Artifact | Path | Description |
|----------|------|-------------|
| Raw PubChem CSV | `data/raw/pubchem.csv` | Immutable download (raw) |
| Data quality report | `data/derived/data_quality_report.csv` | Missing covariates, experimental‑data ratio |
| Verification log | `data/derived/verification_log.txt` | URL verification outcomes |
| Fingerprint arrays | `data/processed/*.npy` | MACCS (166 bits) & ECFP4 (1024 bits) |
| Baseline predictions | `data/derived/baseline_predictions.csv` |
| Baseline residual plot | `data/derived/baseline_residuals.png` |
| RF predictions | `data/derived/rf_predictions.csv` |
| RF residual plot | `data/derived/rf_residuals.png` |
| Test‑set split | `data/derived/test_set.csv` |
| Statistical report | `data/derived/statistical_report.md` |
| SHAP values (JSON) | `data/derived/shap/*.json` |
| SHAP interaction heatmap | `data/derived/shap_interactions.png` |
| SHAP interaction matrix (raw) | `data/derived/shap_interaction.npy` |
| SHAP interaction validation | `data/derived/shap_interaction_validation.txt` |
| Top‑K MACCS bits (selection‑set) | `data/derived/top_k_maccs_selection.txt` |
| Top‑K MACCS bits (test‑set) | `data/derived/top_k_maccs_test.txt` |
| LNAI table | `data/derived/lna_index.csv` |
| Per‑molecule LNAI | `data/derived/lna_index_per_molecule.csv` |
| Deviation contexts (SMARTS) | `data/derived/deviation_contexts.csv` |
| Mapping metrics (precision/recall) | `data/derived/mapping_metrics.txt` |
| Interaction‑Zone Report | `data/derived/interaction_zone_report.pdf` |
| Expert Validation Report | `data/derived/validation_report.pdf` |
| Validation Audit | `data/derived/validation_audit.pdf` |
| Predictions schema‑compliant CSV | `data/derived/predictions_schema.csv` |
| Molecules schema‑compliant CSV | `data/derived/molecules_schema.csv` |
| Validation summary (checksums, QC, etc.) | `data/derived/validation_summary.csv` |

All artifacts are validated against the JSON/YAML contracts in `contracts/`.

---



