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
| `cell_count` | integer | Number of cells assigned to this window |
| `centroid_pseudotime` | float | Mean pseudotime of cells in the window |

### RegulatoryNetwork
| Field | Type | Description |
|-------|------|-------------|
| `stage_id` | string (FK) | Links to `DevelopmentalStage` |
| `edges` | list of **Edge** objects | Each edge: `{tf, target, weight}` |
| `hubs` | list of strings | TFs with degree ≥ 10, or top 20 TFs if fewer than 20 meet threshold |

**Edge** object  
- `tf`: string (TF gene symbol)  
- `target`: string (target gene symbol)  
- `weight`: float (GRNBoost2 importance score, motif-validated)  

### RewiringEvent
| Field | Type | Description |
|-------|------|-------------|
| `event_id` | string | Unique identifier |
| `tf` | string | TF undergoing topological change |
| `stage_a` | string (FK) | Earlier developmental window |
| `stage_b` | string (FK) | Later developmental window |
| `weight_delta` | float | Δ(edge weight) between windows (z‑score normalized) |
| `stability_score` | float | Consistency across sensitivity thresholds |

### DisorderRiskProfile
| Field | Type | Description |
|-------|------|-------------|
| `disorder_name` | string | E.g., `"Schizophrenia"` |
| `risk_genes` | list of strings | Gene symbols from GWAS |
| `source` | string | Citation (e.g., `"GWAS Catalog"` ) |
| `evidence_level` | string | Qualitative confidence |

## Storage Schema
- **Processed AnnData**: `data/processed/integrated_atlas.h5ad`  
- **Networks (GRNBoost2)**: `data/processed/networks/{stage_id}.json` (Adjacency list)  
- **Networks (Motif-Validated)**: `data/processed/networks_motif/{stage_id}.json` (Adjacency list, filtered for motif evidence)  
- **Rewiring Table**: `data/processed/rewiring_events.csv`  
- **Enrichment Results**: `data/processed/disorder_enrichment.csv`  

Each file conforms to a JSON or CSV schema located in `contracts/`.

---