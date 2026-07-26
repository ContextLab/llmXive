# Data Model: Investigating the Correlation Between Circadian Gene Expression and Metabolic Syndrome Risk

## 1. Entity Definitions

### 1.1 Donor
Represents a human subject from the GTEx dataset.
- `donor_id`: String (Unique identifier, e.g., "GTEx-XXX-XXXX")
- `age`: Integer (Years)
- `sex`: String ("Male", "Female")
- `tissue`: String (e.g., "Adipose - Subcutaneous", "Liver")
- `pmi`: Float (Post-Mortem Interval in hours)
- `time_of_death`: String (e.g., "Morning", "Afternoon", or ISO timestamp if available)
- `time_radians`: Float (Continuous circular representation of time for modeling)
- `bmi`: Float (kg/m²)
- `fasting_glucose`: Float (mg/dL)
- `systolic_bp`: Float (mmHg)
- `diastolic_bp`: Float (mmHg)
- `triglycerides`: Float (mg/dL)
- `hdl`: Float (mg/dL)
- `metabolic_status`: String ("MetS", "Control", "Excluded")
- `criteria_count`: Integer (0-5, number of ATP-III criteria met)
- `exclusion_reason`: String (Nullable, e.g., "Missing Glucose")
- `validation_status`: String ("Valid", "Probable", "Invalid") (Result of Phase 0.5)

### 1.2 GeneExpression
Represents the transcript abundance for a specific gene in a donor.
- `donor_id`: String (Foreign key to Donor)
- `gene_symbol`: String (e.g., "PER1", "BMAL1")
- `tpm`: Float (Transcripts Per Million)
- `log_tpm`: Float (Log10(TPM + 1))
- `phase_adjusted_tpm`: Float (Nullable, TPM adjusted for time of death)

### 1.3 AnalysisResult
Stores the output of statistical tests.
- `test_id`: String (Unique identifier)
- `tissue`: String
- `gene_symbol`: String
- `test_type`: String ("Wilcoxon", "Spearman", "LogisticRegression", "TraitOR")
- `p_value`: Float
- `adjusted_p_value`: Float (FDR corrected)
- `effect_size`: Float (e.g., Cohen's d, Correlation coefficient, Odds Ratio)
- `confidence_interval_lower`: Float
- `confidence_interval_upper`: Float
- `significant`: Boolean
- `model_type`: String ("BinaryMetS", "SeverityScore", "TraitSpecific")

## 2. File Formats

### 2.1 Raw Data
- **Format**: Parquet (preferred) or TSV.
- **Location**: `data/raw/`
- **Content**: Unmodified downloads from GTEx.

### 2.2 Processed Data
- **Format**: CSV or JSON.
- **Location**: `data/processed/`
- **Content**:
  - `baseline_labels.csv`: Donor ID, Metabolic Status, Criteria Count, Validation Status.
  - `expression_matrix.csv`: Donor ID, Gene Symbol, TPM, Log TPM, Phase Adjusted TPM.
  - `model_results.json`: Nested JSON containing AUC, Odds Ratios, and CI per gene, per tissue, per model type.

### 2.3 Intermediate Artifacts
- **Format**: Pickle or HDF5 (if necessary for large matrices).
- **Usage**: Temporary storage for stratified datasets before statistical testing.

## 3. Data Flow

1. **Ingestion**: `download_gtex.py` fetches raw data → `data/raw/`.
2. **Validation**: `validate_phenotype.py` checks variables → `data/processed/validation_report.json`.
3. **Classification**: `classify_metabolic.py` reads raw data, applies ATP-III logic, outputs `baseline_labels.csv` → `data/processed/`.
4. **Preprocessing**: `preprocess.py` merges labels with expression data, handles log-transform, calculates `time_radians` → `expression_matrix.csv`.
5. **Analysis**:
   - `differential_expression.py` (with phase adjustment) → `model_results.json` (DE results).
   - `correlation.py` (with partial correlation) → `model_results.json` (Correlation results).
   - `modeling.py` (Binary, Severity, Trait-Specific) → `model_results.json` (Regression results).
6. **Sensitivity**: `sensitivity_analysis.py` → `model_results.json` (Stability metrics).
7. **Visualization**: `plots.py` reads `model_results.json` and `expression_matrix.csv` to generate figures.

## 4. Constraints & Validation

- **Missing Values**: Any clinical variable with `NaN`, `null`, or `< -1` triggers exclusion.
- **Log Transformation**: `log_tpm = log10(tpm + 1)` to handle zero counts.
- **Tissue Filtering**: Tissues with < 20 samples per group are excluded before testing.
- **FDR**: All p-values must be corrected using Benjamini-Hochberg before reporting significance.
- **Time Modeling**: `time_radians` is calculated as `(hour / 24) * 2 * pi`.