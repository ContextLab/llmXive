# Data Model: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

This document defines the core data entities and their schemas for the molecular
fingerprint analysis pipeline. It is a hard gate for Phase 1 and a prerequisite
for T011 (dataset download) and T012 (organophosphate filtering).

## 1. Entity: Compound

Represents a chemical compound from the source dataset (Tox21).

**Schema:**
```json
{
  "smiles": "str",
  "mol_id": "str",
  "toxicity_labels": "dict"
}
```

| Field | Type | Description | Constraints |
|:---|:---|:---|:---|
| `smiles` | str | Canonical SMILES string of the molecular structure | Non-null, RDKit-parseable |
| `mol_id` | str | Unique identifier for the compound (e.g., DSSTox ID) | Primary Key, Non-null |
| `toxicity_labels` | dict | Dictionary of binary toxicity endpoint labels, e.g. `{"NR-AR": 0, "SR-p53": 1}` | Values in a binary set; keys are the 12 Tox21 endpoints |

**Source:** `data/raw/tox21_raw.csv` (via T011)
**Derived File:** `data/processed/organophosphates_filtered.csv` (via T012)

## 2. Entity: Fingerprint

Represents a binary vector encoding the structural features of a compound.

**Schema:**
```json
{
  "type": "str (morgan/maccs)",
  "bits": "int",
  "vector": "list"
}
```

| Field | Type | Description | Constraints |
|:---|:---|:---|:---|
| `type` | str | Fingerprint type | Enum: `morgan` or `maccs` |
| `bits` | int | Number of bits in the fingerprint | 2048 (Morgan), 166 (MACCS) |
| `vector` | list | The fingerprint bit vector (list of ints) | Length equals `bits`; values in {0, 1} |

**Constants (from `code/constants.py`):**
- Morgan: `radius=2` (`MORGAN_RADIUS`), `bits=2048` (`MORGAN_BITS`)
- MACCS: `bits=166` (`MACCS_BITS`)

**Derived Files:** `data/processed/fingerprints_morgan.pkl`, `data/processed/fingerprints_maccs.pkl` (via T017)

## 3. Entity: Model

Represents a trained Random Forest classifier for a specific fingerprint type and endpoint.

**Schema:**
```json
{
  "type": "str",
  "fingerprint_type": "str",
  "endpoint": "str",
  "metrics": "dict"
}
```

| Field | Type | Description | Constraints |
|:---|:---|:---|:---|
| `type` | str | Algorithm type (e.g., `RandomForestClassifier`) | Non-null |
| `fingerprint_type` | str | Fingerprint used for training | Enum: `morgan` or `maccs` |
| `endpoint` | str | Toxicity endpoint the model predicts (e.g., `NR-AR`) | Non-null |
| `metrics` | dict | Evaluation metrics for this model (e.g., `{"roc_auc": 0.82, "pr_auc": 0.41}`) | Values are floats in [0.0, 1.0] |

**Hyperparameters (fixed per FR-003):** `n_estimators=100`, `max_depth=15`, CPU-only.

**Derived File:** `data/processed/final_models.pkl` (via T020a)

## 4. Entity: PerformanceMetric

Represents a quantitative evaluation result of a model.

**Schema:**
```json
{
  "name": "str",
  "value": "float",
  "ci": "tuple"
}
```

| Field | Type | Description | Constraints |
|:---|:---|:---|:---|
| `name` | str | Metric name (e.g., `roc_auc`, `pr_auc`) | Non-null |
| `value` | float | Calculated metric value | Range: [0.0, 1.0] |
| `ci` | tuple | (lower, upper) confidence interval bounds, derived via bootstrap | Optional; floats |

**Derived Files:**
- `data/processed/final_test_metrics.json` (Single Split, via T020b)
- `data/processed/kfold_scores.json` (K-Fold CV, via T019)
- `data/processed/test_set_descriptive.json` (via T024b)
- `data/processed/sc003_analysis.json` (Feature Importance, via T025c3)

## Relationships

1. **Compound 1..* Fingerprint**: Each compound generates one Morgan and one MACCS fingerprint.
2. **Compound 1..* Model**: A compound's labels and fingerprints are used to train models.
3. **Model 1..* PerformanceMetric**: A model is evaluated on multiple splits (K-Fold) or a single held-out test set.
4. **PerformanceMetric *..1 Model**: Each metric record belongs to exactly one model instance.

## Data Flow

1. **Raw Data** -> `Compound` (T011: download)
2. **Compound** -> filtered `Compound` set (T012: SMARTS filter)
3. **Compound** -> `Fingerprint` (T017: Morgan + MACCS generation)
4. **Fingerprint + Compound labels** -> `Model` (T019, T020a: Random Forest training)
5. **Model + test data** -> `PerformanceMetric` (T019, T020b)
6. **PerformanceMetric aggregation** -> statistical reports (T025a2, T025b, T029a3)

## Notes

- Toxicity labels are treated as ground-truth binary values; no measurement
  uncertainty (standard deviation) is recalculated, per the Spec Assumptions
  ("Instrument Precision").
- RDKit default implementations of Morgan and MACCS fingerprints constitute the
  standard calibration; no external calibration is applied, per the Spec
  Assumptions ("Algorithm Calibration").
- The study is observational and correlational; no causal claims are made.