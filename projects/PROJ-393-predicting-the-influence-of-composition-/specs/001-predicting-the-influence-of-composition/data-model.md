# Data Model: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## 1. Entity Definitions

### AlloyEntry
| Field | Type | Description |
|-------|------|-------------|
| `alloy_id` | string (UUID) | Unique identifier |
| `composition` | object (element → atomic fraction) | Must sum to 1.0 ± 0.0001 |
| `coercivity` | object (`value`: float ≥ 0, `unit`: `"Oe"` ) | Experimental coercivity |
| `saturation` | object (`value`: float ≥ 0, `unit`: `"emu/g"` ) | Experimental saturation magnetization |
| `source_type` | enum `["NIST","Journal","Manual"]` | Origin of the record |
| `synthesis_method` | string (nullable) | e.g., `"Arc‑melting"` |
| `crystal_structure` | string (nullable) | e.g., `"L2_1"` |
| `is_dft` | boolean | Must be `False` for training targets |
| `raw_source` | string | URL or citation key |
| `reference` | string (nullable) | DOI or bibliographic reference |

### CompositionDescriptor
| Field | Type | Description |
|-------|------|-------------|
| `alloy_id` | string (FK to AlloyEntry) | |
| `avg_electronegativity` | float | Weighted average (Pauling) |
| `vec` | float | Valence electron concentration |
| `atomic_radii_variance` | float | Weighted variance of metallic radii |
| `avg_d_electrons` | float | Weighted average d‑electron count |
| `atomic_size_mismatch` | float | Size‑mismatch metric $\delta$ |

### ModelResult
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | enum `["Linear","RandomForest"]` | |
| `target_variable` | enum `["coercivity","saturation"]` | |
| `r2_cv` | float | Mean CV $R^2$ |
| `mae_cv` | float | Mean CV MAE |
| `f_statistic` | float | From F‑test vs. null |
| `p_value` | float | Must be `< 0.05` (Bonferroni‑adjusted) |
| `feature_importance` | object (feature → importance) | Top 3 by permutation importance |
| `bootstrap_ci_lower` | float | 95 % CI lower bound for $R^2$ |
| `bootstrap_ci_upper` | float | 95 % CI upper bound for $R^2$ |
| `sc006_status` | string (`"Exploratory Benchmark Met"` / `"Not Met"`) | Reflects SC‑006 |
| `data_scarcity_warning` | boolean | True if $N < 50$ |
| `interpretation_disclaimer` | string | Mandatory text (FR‑009) |
| `microstructure_note` | string | Mandatory text (FR‑010) |
| `residual_confounding_check` | string | Summary of stratified analysis |

## 2. Data Flow Diagram
1. **Ingestion** → `data/raw/` (raw CSV/JSON)  
2. **Preprocessing** (unit conversion, DFT filter, mean imputation) → `data/processed/alloys_clean.csv`  
3. **Feature Engineering** → `data/processed/alloys_features.csv`  
4. **Model Training** → `models/` (pickles) + `reports/metrics.json`  
5. **Validation** (F‑test, bootstrap, PDP) → `docs/reports/` (figures & markdown)  
6. **Report Assembly** → `docs/reports/final_report.md`

## 3. Data Integrity Rules
- **Composition Sum**: $\sum c_i = 1.0 \pm 0.0001$  
- **Units**: coercivity → Oe; saturation → emu/g  
- **Missing Data**: Column‑wise **mean imputation**; imputation rate must be **< 15 %** (recorded in `imputation_report.json`). Rows with > 50 % missing are dropped (listwise deletion).  
- **DFT Exclusion**: `is_dft == True` rows are removed before model training.  
- **Completeness Metric**: Verified distinct experimental entries = **54** (source Q39304236).  
- **Bootstrapping**: Exactly **1000** resamples (source: Bootstrapping (statistics)).  

---
