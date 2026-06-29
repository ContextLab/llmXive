# Data Model Specification

**Project**: PROJ-675-comparing-born-model-predictions-with-ex
**Spec Location**: specs/001-born-model-solvation-comparison/
**Constitution Principle IV Compliance**: Single Source of Truth for all data entities

---

## Overview

This document defines the canonical entity-to-file mappings for the Born Model Solvation Comparison project. Each entity has exactly one authoritative file location (Single Source of Truth), ensuring data consistency and reproducibility.

---

## Entity Definitions

### 1. IonSolventPair

**Purpose**: Experimental solvation free energy measurements with full metadata.

**Authoritative File**: `data/experimental_solvation.csv`

**Schema Fields**:
| Field | Type | Description | Precision/Constraints |
|-------|------|-------------|----------------------|
| ion_identifier | str | Ion chemical formula (e.g., "Na+", "Cl-") | Required |
| solvent_identifier | str | Solvent name (e.g., "water", "ethanol") | Required |
| experimental_deltaG | float | Experimental solvation free energy | Units: kcal/mol |
| experimental_deltaG_uncertainty | float | Measurement uncertainty | Required per Constitution Principle VII |
| charge | int | Ionic charge | Required |
| radius | float | Ionic radius | Precision ≥ 0.01 Å (per reviewer feedback) |
| radius_type | str | "crystal" or "hydrated" | Required per FR-002 |
| dielectric_constant | float | Solvent dielectric constant | Required |
| dielectric_constant_uncertainty | float | ε measurement uncertainty | Required per FR-008 |
| temperature | float | Measurement temperature | Units: Kelvin, ±0.5°C precision |
| instrument_metadata | str | Source/citation for measurement | Required per Constitution Principle II |

**Source Citations**:
- NIST Chemistry WebBook: https://webbook.nist.gov/chemistry/
- CRC Handbook of Chemistry and Physics
- Shannon Radii Database

**Validation**: ≥30 complete ion-solvent pairs required (T018)

---

### 2. BornPrediction

**Purpose**: Theoretical Born model predictions for comparison with experiment.

**Authoritative File**: `data/born_predictions.csv`

**Schema Fields**:
| Field | Type | Description | Precision/Constraints |
|-------|------|-------------|----------------------|
| ion_identifier | str | Ion chemical formula | Required |
| solvent_identifier | str | Solvent name | Required |
| predicted_deltaG | float | Born model prediction | Units: kcal/mol |
| ionic_radius | float | Radius used in calculation | Precision ≥ 0.01 Å |
| dielectric_constant | float | Solvent ε value | Required |
| radius_type | str | "crystal" or "hydrated" | Required per FR-002 |
| coordination_correction | bool | Whether coordination correction applied | Optional |
| calculation_timestamp | str | ISO 8601 timestamp | Required for reproducibility |
| random_seed | int | Reproducibility seed | Required per Constitution Principle I |

**Formula**: Born equation implemented in `code/born_calculator.py`

**Validation**: ≤1% relative error vs reference cases (T026)

---

### 3. ResidualAnalysis

**Purpose**: Statistical analysis of model residuals and breakdown detection.

**Authoritative File**: `data/residual_analysis.csv`

**Schema Fields**:
| Field | Type | Description | Precision/Constraints |
|-------|------|-------------|----------------------|
| ion_identifier | str | Ion chemical formula | Required |
| solvent_identifier | str | Solvent name | Required |
| residual | float | experimental_deltaG - predicted_deltaG | Units: kcal/mol |
| residual_uncertainty | float | Combined uncertainty | Required per FR-008 |
| ion_size_class | str | Size category (small/medium/large) | For stratification |
| solvent_class | str | "water", "alcohols", or "aprotic" | For stratification |
| statistical_significance | bool | Whether residual exceeds uncertainty | Required |
| p_value | float | Hypothesis test p-value | Benjamini-Hochberg corrected |
| confidence_interval_lower | float | 95% CI lower bound | Required |
| confidence_interval_upper | float | 95% CI upper bound | Required |
| rmse_per_class | float | Stratified RMSE | Per solvent class |
| correlation_per_class | float | Correlation coefficient | Per solvent class |
| review_required | bool | Flag for manual review | If RMSE > 20 kcal/mol |

**Metrics**:
- RMSE < 5 kcal/mol target (SC-003)
- Correlation > 0.8 target (SC-003)
- Benjamini-Hochberg correction applied (T033)

---

## Supporting Files

### data/metadata.json

**Purpose**: Data dictionary with source citations and documentation.

**Contents**:
- Source citations for every value (T019b)
- Uncertainty coverage percentage (T019a)
- Breakdown threshold documentation (T037b)
- FR-002 traceability (T014, T015, T016, T017)

### data/parameters.csv

**Purpose**: Physical constants and parameters with citations.

**Contents**:
- Elementary charge (e)
- Vacuum permittivity (ε₀)
- Ionic radii (Shannon)
- Dielectric constants
- Temperature conditions (T005c)

### data/plots/

**Diagnostic Plots** (T035a):
- `predicted_vs_experimental.png`
- `residual_vs_radius.png`
- `residual_vs_dielectric.png`

---

## Data Flow Dependencies

```
data/experimental_solvation.csv (T018 validated)
 ↓
data/born_predictions.csv (T027 computed)
 ↓
data/residual_analysis.csv (T031 computed)
```

**Critical Path**: T018 must complete before T027, which must complete before T031.

---

## Constitution Principle Compliance

| Principle | Compliance Action |
|-----------|-------------------|
| I (Reproducibility) | Random seeds pinned in all computation scripts |
| II (Verified Accuracy) | All citations validated via reference_validator.py |
| IV (Single Source of Truth) | Each entity maps to exactly one file |
| V (Versioning Discipline) | Checksums in state/projects/PROJ-675.yaml |
| VI (Thermodynamic Consistency) | Temperature conditions documented in parameters.csv |
| VII (Statistical Significance) | Benjamini-Hochberg correction applied |

---

## Precision Requirements (Per Reviewer Feedback)

1. **Ionic Radii**: ≥0.01 Å precision (Rosaleind-Franklin reviewer)
2. **Solvation Energy Uncertainty**: Must be stated for all values (Marie-Curie reviewer)
3. **Instrument Metadata**: Source and precision documented (Marie-Curie reviewer)
4. **Temperature Control**: ±0.5°C precision recorded

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-28 | llmXive | Initial data model specification |