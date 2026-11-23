# Data Model: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Function in Aging Using UK Biobank Data

## Overview
All data objects are stored as Parquet files to preserve schema and enable efficient columnar access. The synthetic dataset mirrors the UK Biobank schema required by the specification.

## Entity Definitions

### 1. Participant
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | `str` | Unique identifier (deterministic UUID) | Primary key |
| `age` | `float` | Age in years | 40 ≤ age ≤ 85 |
| `sex` | `int` | 0 = Female, 1 = Male | {0,1} |
| `bmi` | `float` | Body Mass Index | 15 ≤ bmi ≤ 45 |
| `diet_quality` | `float` | Score 0‑100 | 0 ≤ score ≤ 100 |
| `physical_activity` | `float` | MET‑min/week | > 0 |
| `medication_use` | `int` | 0 = No, 1 = Yes | {0,1} |
| `antibiotic_use` | `int` | 0 = No, 1 = Yes (recent) | {0,1} |

### 2. MicrobiomeProfile
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | `str` | FK → Participant | |
| `ilr_coords` | `dict[str, float]` | ILR‑transformed genus‑level coordinates | Sum = 0 (orthonormal) |
| `sequencing_depth` | `int` | Total reads after filtering | > 0 |
| `quality_score` | `float` | 0‑1 quality metric | 0 ≤ score ≤ 1 |

### 3. CognitiveScore
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `participant_id` | `str` | FK → Participant | |
| `reaction_time` | `float` | Mean reaction time (ms) | > 0 |
| `numeric_memory` | `int` | 0‑100 score | 0 ≤ score ≤ 100 |
| `reasoning` | `int` | 0‑100 score | 0 ≤ score ≤ 100 |
| `test_date` | `str` | ISO‑8601 date (YYYY‑MM‑DD) | Valid date |

### 4. AssociationResult
| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `taxon` | `string` | Name of the bacterial genus/taxon. |
| `cognitive_metric` | `string` | `"reaction_time"`, `"numeric_memory"` or `"reasoning"` |
| `beta` | `number` | Effect size (beta coefficient) from the linear model. |
| `p_value` | `number` | Unadjusted p‑value (0 < p ≤ 1). |
| `p_adj` | `number` | Benjamini‑Hochberg adjusted p‑value (0 < p_adj ≤ 1). |
| `interaction_p` | `number` | Interaction term p‑value (optional, 0 < p ≤ 1). |
| `causality_claim` | `boolean` | Always `false`. |

## Transformation Pipeline

1. **Raw Data Generation** (`code/pipelines/download.py`)  
   - Input: seed = 42.  
   - Output: `data/raw/synthetic_ukb.parquet` (fallback) **or** `data/raw/ukb_microbiome.parquet` + `data/raw/ukb_cognitive.parquet` when credentials succeed.  
   - Process: sample participant demographics, generate Dirichlet‑Multinomial counts for a representative set of genera, synthesize cognitive scores with age‑dependent noise, add antibiotic flag.

2. **Preprocessing** (`code/pipelines/preprocess.py`)  
   - Load raw Parquet (streamed).  
   - Filter out rows with `antibiotic_use == 1` or any missing core variable.  
   - Add pseudocount `1e-6` to zero counts.  
   - Apply ILR using a binary balance tree (implemented in `models/microbiome_transform.py`).  
   - Write `data/processed/ilr_transformed.parquet`.  
   - **Validate** the output against `contracts/dataset.schema.yaml` (task T018‑validate).

3. **Statistical Analysis** (`code/pipelines/analyze.py`)  
   - Input: processed Parquet.  
   - Fit OLS, Lasso, Ridge models for each taxon‑cognitive pair, controlling for all confounders.  
   - Apply BH correction to main and interaction p‑values.  
   - Fit reduced models (excluding diet & medication) for over‑control sensitivity.  
   - Save results to `results/associations/` as Parquet files conforming to `contracts/association_result.schema.yaml`.

4. **Visualization** (`code/paper/plots.py`)  
   - Generate Manhattan‑style plots per cognitive metric with effect‑size annotation.  
   - Save PNG/SVG to `results/plots/`.

## File Formats
- **Parquet** – all intermediate and final datasets (schema‑preserving, columnar).  
- **YAML** – configuration files and schema definitions (`contracts/`).  
- **JSON** – optional metadata payloads.  

---

