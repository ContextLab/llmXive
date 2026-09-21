# Data Model: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Entity-Relationship Overview

The data model consists of three primary entities: `Participant`, `Trial`, and `Stimulus`.
- **Participant**: Unique ID, demographic metadata (if available).
- **Trial**: Link between Participant and Stimulus, containing response time and condition.
- **Stimulus**: Image/Text content, valence score, ambiguity score.

**Stimulus Separation**: `data/primes/` and `data/targets/` are populated and processed independently before the final `linked_trials.csv` is generated, satisfying Constitution Principle VI.

## 2. Schema Definitions

### 2.1. Raw Input Schema (IAT Dataset)
Derived from `davanstrien/ia_test_embeddings`.
- `trial_id`: String (Unique identifier)
- `participant_id`: String (Unique identifier)
- `response_time`: Float (ms)
- `stimulus_id`: String (Link to stimulus metadata)
- `condition`: String (Prime/Target condition)
- `age`: Float (Optional)
- `gender`: String (Optional)
- `education`: String (Optional)

### 2.2. Processed Trial Schema (`data/processed/linked_trials.csv`)
- `trial_id`: String
- `participant_id`: String
- `response_time`: Float
- `prime_valence`: Float (Derived or Human-rated, -1 to 1)
- `stimulus_ambiguity`: Float (Derived or Human-rated, 0 to 1)
- `stimulus_id`: String
- `linkage_status`: String ("linked", "missing_image", "missing_metadata")
- `demographics_status`: String ("complete", "missing_age", "missing_gender", "missing_education", "missing_all")

### 2.3. Linkage Status Artifact (`state/linkage_status.json`)
- `status`: String ("PASS", "WARN", "HALT")
- `percentage`: Float (0.0 to 100.0)
- `threshold`: Float (Default 95.0)
- `message`: String

### 2.4. Model Output Schema (`state/model_convergence_metrics.json`)
- `convergence_rate`: Float (0.0 to 1.0)
- `total_attempts`: Integer
- `successful_runs`: Integer
- `failed_runs`: Integer
- `optimizer_settings`: Array of Strings

### 2.5. VIF Flag Artifact (`state/vif_flag.json`)
- `flagged`: Boolean
- `vif_values`: Object (predictor: value)
- `claim_suppressed`: Boolean
- `message`: String

### 2.6. Sensitivity Analysis Schema (`reports/sensitivity_analysis.csv`)
- `alpha_level`: Float (0.01, 0.05, 0.10)
- `significant_interactions`: Integer
- `total_tests`: Integer
- `fdr_corrected_p_values`: Array of Floats
- `conclusion`: String ("Significant", "Non-Significant", "Borderline")

## 3. Data Flow

1.  **Ingestion**: Raw Parquet/CSV -> `data/raw/`.
2.  **Stimulus Separation**: Primes and Targets extracted to `data/primes/` and `data/targets/` respectively.
3.  **Linkage**: Join `trial_id` with `stimulus_id` -> `data/processed/linked_trials.csv`.
4.  **Derivation**: If `stimulus_ambiguity` missing, derive using independent method (Lexical Ambiguity / Texture Variance).
5.  **Filtering**: Remove trials with `linkage_status` = "missing_image" if >10% (halt) or <10% (warn).
6.  **Demographics Check**: Map `age`, `gender`, `education`. Write status to `state/demographics_status.json`.
7.  **Modeling**: `linked_trials.csv` -> LME Model (with Robust SE if derived) -> `state/model_results.pkl`.
    - *Note*: Covariate term omitted if demographics missing.
8.  **Sensitivity Analysis**: Sweep alpha -> `reports/sensitivity_analysis.csv`.
9.  **Reporting**: Model results + `sensitivity_analysis.csv` (parsed) -> `reports/final_report.pdf`.

## 4. Constraints & Validations

- **Linkage Threshold**: System halts if >10% of trials lack image linkage (US-1). Default threshold 95% (configurable).
- **Valence Range**: `prime_valence` must be in [-1.0, 1.0].
- **Ambiguity Range**: `stimulus_ambiguity` must be in [0.0, 1.0].
- **PII Scan**: No `participant_id` can match known PII patterns (email, phone, SSN, name).
- **Collinearity**: If VIF > 5.0, claim suppression is enforced and reported.
- **Demographics**: If `demographics_status` indicates missing data, the model equation must exclude the covariate term.