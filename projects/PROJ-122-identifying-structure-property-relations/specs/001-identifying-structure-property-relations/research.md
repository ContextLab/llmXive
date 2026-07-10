# Research: Identifying Structure-Property Relationships in Polymer Blends

## 1. Problem Statement

The goal is to identify structure-property relationships in polymer blends by leveraging public databases to train machine learning models that predict key macroscopic properties (Glass Transition Temperature, Tg, and Young's Modulus) from molecular descriptors. The challenge lies in aggregating heterogeneous data, generating meaningful features, and ensuring statistical rigor within the constraints of a CPU-only CI environment.

**Critical Constraint**: The primary hypothesis (predicting `Tg_residual` and `Modulus` for blends) is **contingent** on the existence of a verified dataset containing SMILES, Composition (weight fractions), Tg, and Modulus. If such a dataset is not found, the project switches to a "Monomer-Level Fallback" track (predicting monomer Tg/Modulus from descriptors only), which answers a different research question.

## 2. Dataset Strategy

### 2.1 Verified Datasets

Per the project's verified datasets list, the following sources are available. **Note**: The spec requires SMILES, Composition, Tg, and Modulus. The verified list contains SMILES and some descriptor data, but **NO verified source** for combined polymer blend data with all required fields (SMILES + Composition + Tg + Modulus) is found in the provided list.

| Dataset | Verified URL | Relevance to Spec | Gap Analysis |
|---------|--------------|-------------------|--------------|
| NIST (jsonl) | ` | General NIST data, not polymer-specific. | **No SMILES, Composition, Tg, Modulus.** Not suitable. |
| SMILES (csv) | ` | Contains SMILES. | **No Composition, Tg, Modulus.** Only monomer data, not blends. |
| RDKit (parquet) | ` | Contains SMILES and pre-computed descriptors. | **No Composition, Tg, Modulus.** Pure monomer data. |
| GPa | **NO verified source found** | Young's Modulus data. | **Critical Gap**: No verified source for GPa/Modulus data. |
| WebBook | **NO verified source found** | Potential polymer data. | **Critical Gap**: No verified source. |
| APIs | **NO verified source found** | Polymer Database, Materials Project APIs. | **Critical Gap**: No verified source for API endpoints. |

### 2.2 Dataset Mismatch & Mitigation

**Fatal Mismatch Identified**: The spec requires a dataset containing **SMILES, Composition (weight fractions), Tg, and Young's Modulus** for **polymer blends**. The verified datasets list contains only **monomer-level SMILES and descriptors** (e.g., `chembl-2025-randomized-smiles-cleaned-rdkit-descriptors`). **No verified source** exists for combined blend data with all required fields.

**Mitigation Strategy**:
1. **Halt on Missing Data**: Per FR-015, the system MUST verify the existence of a specific, accessible dataset URL containing all required fields before ingestion. Since no such URL is verified, the pipeline MUST halt the *main blend prediction* and trigger the **Monomer-Level Fallback** (FR-013).
2. **Fallback Logic (FR-013)**: If the "perfect join" fails for >50% of records (which it will, as no records exist), the system MUST switch to "component-level prediction mode". This involves:
 * Using available monomer SMILES and descriptors.
 * Attempting to predict monomer Tg/Modulus if any target data exists (currently none in verified list).
 * If no target data exists, the fallback track will report "No Target Data Available for Monomer Prediction" and halt the training phase.
3. **Assumption Check**: The spec's "Assumption about dataset-variable fit" states: "It is assumed that the available public datasets contain the necessary molecular descriptors... and that no critical predictor variables... are missing." **This assumption is invalid** given the verified dataset list. The analysis cannot proceed as specified without a verified data source.

**Decision**: The plan must explicitly state that **no verified dataset exists** for the required task. The implementation will:
- Attempt to load the verified SMILES/descriptor datasets (e.g., `chembl-2025...`) as a **proxy** for monomer-level analysis.
- **Exclude** blend-specific predictions (Tg_residual, Modulus) due to lack of blend data.
- **Focus** on monomer-level property prediction (e.g., predicting Tg for single polymers if Tg data were available, but it is not).
- **Report** this limitation clearly in `final_report.json` and halt the main pipeline if the "perfect join" threshold is not met.

**Alternative**: If the user can provide a verified URL for polymer blend data, the plan can be updated. Otherwise, the project scope must be reduced to monomer-level analysis (if Tg/Modulus data becomes available) or the spec must be revised.

## 3. Feature Engineering Strategy

### 3.1 Molecular Descriptors
- **Source**: RDKit (via `rdkit_chemical` or `chembl-2025` datasets).
- **Descriptors**: MW, TPSA, rotatable bonds, H-bonding capacity. **Note**: "Fractional Free Volume" (FFV) and "Hansen Solubility Parameters" are **not** standard RDKit outputs. They require external libraries (`hansen-solubility`, `polymer-properties`) or group contribution methods. The plan will implement these in `utils/descriptors.py` if data permits, otherwise, only standard RDKit descriptors will be used.
- **Target**: ≥15 distinct descriptors per monomer (FR-003, SC-007).
- **Validation**: Check for NaN values; exclude monomers with <15 valid descriptors.

### 3.2 Interaction Features (Blended)
- **Weighted Averages**: `avg_desc = Σ(w_i * desc_i)`
- **Absolute Differences**: `diff_desc = |desc_1 - desc_2|`
- **Non-linear Mixing Rules**:
 - **Fox Equation**: `1/Tg_mix = w_1/Tg_1 + w_2/Tg_2` → `Tg_residual = Tg_measured - Tg_Fox`
 - **Gordon-Taylor Equation**: `Tg_mix = (w_1*Tg_1 + k*w_2*Tg_2) / (w_1 + k*w_2)` (k is a fitting parameter).
- **Challenge**: These require **Tg_1, Tg_2** (monomer Tg) and **Tg_measured** (blend Tg). **No verified source** provides these. Thus, `Tg_residual` cannot be computed.

**Decision**: The interaction features **cannot be computed** without verified blend data. The plan will:
- Generate monomer descriptors only.
- **Skip** blend-specific interaction features (FR-004) due to data unavailability.
- **Report** this as a critical gap in `research.md` and `final_report.json`.

## 4. Statistical Rigor & Validation

### 4.1 Multiple Comparisons
- **Correction**: Bonferroni or False Discovery Rate (FDR) applied to p-values from paired t-tests (SC-002, Assumption about multiplicity).
- **Scope**: When comparing RF vs. Linear, XGBoost vs. Linear, and across different descriptors.

### 4.2 Sample Size & Power
- **Threshold**: N < 100 → "Data Insufficiency" error (FR-012, SC-010).
- **Power Analysis**: If N ≥ 100, a post-hoc power analysis will be reported. If N < 100, the limitation is explicitly stated.

### 4.3 Causal Inference
- **Framing**: All findings are **associational**, not causal (Assumption about inference framing). No randomization; observational data.
- **Claims**: Feature importance reflects *predictive contribution*, not causal mechanism.

### 4.4 Measurement Validity
- **Descriptors**: RDKit descriptors (MW, TPSA, etc.) are standard and validated in materials science (Assumption about measurement validity).
- **Limitation**: No experimental validation of descriptors for this specific dataset (due to data unavailability).

### 4.5 Predictor Collinearity
- **VIF Analysis**: Calculate VIF for all predictors. If VIF > 5.0, perform sensitivity analysis (FR-008).
- **Collinearity**: If predictors are definitionally related (e.g., MW and TPSA), report descriptive statistics and acknowledge collinearity. **Do not claim independent effects**.

### 4.6 Statistical Validity Gate
- **Condition**: If the primary dataset is missing, the plan explicitly states that t-tests, VIF, and SHAP cannot be performed for blend properties.
- **Action**: The report will reflect 'Data Insufficient' for these metrics rather than generating null results.

## 5. Compute Feasibility

- **Environment**: GitHub Actions `ubuntu-latest` (2 CPU, 7 GB RAM, no GPU).
- **Libraries**: `scikit-learn`, `xgboost` (CPU-only wheels), `rdkit`, `shap`.
- **Sampling**: If raw dataset > 7 GB RAM, implement stratified random sampling (FR-017) to target ≤ 6 GB.
- **Runtime**: Target ≤ 5 hours. Pipeline steps:
 1. Ingest (≤ 30 min)
 2. Feature Engineering (≤ 1 hour)
 3. Training (≤ 2 hours)
 4. Evaluation (≤ 1 hour)
 5. Reporting (≤ 30 min)
- **Fallback**: If runtime exceeds 5 hours, halt and report timeout.

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified blend data** | Fatal: Cannot compute Tg_residual or Modulus predictions. | Halt main pipeline; report gap; switch to monomer-level analysis (if possible). |
| **API rate limits** | Pipeline failure. | Exponential backoff (FR-010); max 5 retries. **SC-009**: Verify recovery within 30s. |
| **Small dataset (N < 100)** | Cannot train robust models. | Halt with "Data Insufficiency" error (FR-012). |
| **Collinearity** | Unstable feature importance. | VIF analysis + sensitivity analysis (FR-008). |
| **Memory overflow** | CI job failure. | Stratified sampling (FR-017); monitor RAM usage. |
| **Runtime > 5 hours** | CI job timeout. | Optimize code; sample data; report timeout. |
| **Missing Target Variables** | Cannot compute residuals. | Skip residual calculation; report gap. |

## 7. Conclusion

The proposed pipeline is methodologically sound but **blocked by the absence of a verified dataset** containing the required polymer blend data (SMILES, Composition, Tg, Modulus). The implementation will:
1. Verify data availability (FR-015).
2. Halt if no verified source is found.
3. Attempt monomer-level analysis using available SMILES/descriptor data (if applicable).
4. Report all gaps and limitations transparently.

**Recommendation**: Secure a verified URL for polymer blend data or revise the spec to focus on monomer-level property prediction (if Tg/Modulus data becomes available).