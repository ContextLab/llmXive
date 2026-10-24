# Data Model: Quantitative Analysis of Gene Expression Dynamics

## Conceptual ER Diagram
`DevelopmentalStage` → contains → `RegulatoryNetwork` → produces → `RewiringEvent` ← correlated with ← `DisorderRiskProfile`

## Entity Definitions

### DevelopmentalStage
| Field | Type | Description |
|-------|------|-------------|
| `stage_id` | string | Unique identifier, e.g., `"Fetal_12_16w"` |
| `start_age_days` | integer | Lower bound of age (days) |
| `end_age_days` | integer | Upper bound of age (days) |
| `cell_count` | integer | Number of cells/samples assigned to this window |
| `centroid_age` | float | Mean age (days) of samples in the window |

### RegulatoryNetwork
| Field | Type | Description |
|-------|------|-------------|
| `stage_id` | string (FK) | Links to `DevelopmentalStage` |
| `age_window` | string | Identifier of the observed age window (e.g., `"12_16w"`), aligns with `DevelopmentalStage.stage_id` |
| `window_id` | string | Identifier for the **pseudotime sliding window** within the age window (e.g., `window_01`) |
| `edges` | list of **Edge** objects | Each edge: `{tf, target, weight}` |
| `hubs` | list of strings | TFs with degree ≥ 10, or top‑20 TFs if fewer meet threshold |

**Edge** object  
- `tf`: string (TF gene symbol)  
- `target`: string (target gene symbol)  
- `weight`: float (GRNBoost2 importance score, motif‑validated)  

### RewiringEvent
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique identifier |
| `tf` | string | TF undergoing topological change |
| `stage_a` | string (FK) | Earlier developmental window |
| `stage_b` | string (FK) | Later developmental window |
| `weight_delta_z` | float | Z‑score‑normalized Δ(edge weight) between windows |
| `stability_score` | float | Consistency across sensitivity thresholds (0–1) |

### DisorderRiskProfile
| Field | Type | Description |
|-------|------|-------------|
| `disorder_name` | string | E.g., `"Schizophrenia"` |
| `risk_genes` | list of strings | Gene symbols from curated GWAS list |
| `source` | string | Citation (e.g., `"Curated GWAS Catalog"` ) |
| `evidence_level` | string | Qualitative confidence |

## Storage Schema
- **Processed AnnData**: `data/processed/integrated_atlas.h5ad`  
- **GRNs (raw)**: `data/processed/networks/{stage_id}_{window_id}.json` (list of Edge objects)  
- **GRNs (motif‑validated)**: `data/processed/networks_motif/{stage_id}_{window_id}.json`  
- **Rewiring Table**: `data/processed/rewiring_events.csv` (columns: `event_id, tf, stage_a, stage_b, weight_delta_z, stability_score`)  
- **Enrichment Results**: `data/processed/disorder_enrichment.csv` (columns: `disorder, vulnerability_window, odds_ratio, p_value, is_validated`)  

All files conform to schemas located in `contracts/`.

---


