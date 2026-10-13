# Data Model: Quantitative Analysis of Gene Expression Dynamics

## Entity Relationship Diagram (Conceptual)
`DevelopmentalStage` $\rightarrow$ contains $\rightarrow$ `RegulatoryNetwork` $\rightarrow$ produces $\rightarrow$ `RewiringEvent` $\leftarrow$ correlated with $\leftarrow$ `DisorderRiskProfile`

## Entity Definitions

### 1. DevelopmentalStage
Represents a discrete or windowed time point in brain development.
- `stage_id`: String (e.g., "Fetal_12_16w")
- `start_age_days`: Integer
- `end_age_days`: Integer
- `cell_count`: Integer
- `centroid_pseudotime`: Float

### 2. RegulatoryNetwork
A directed graph of TF-target interactions for a specific stage.
- `stage_id`: String (FK to DevelopmentalStage)
- `edges`: List of `Edge` objects:
    - `tf`: String (Gene Symbol)
    - `target`: String (Gene Symbol)
    - `weight`: Float (Importance score from GRNBoost2)
- `hubs`: List of Strings (TFs with degree $\ge$ [deferred] threshold)

### 3. RewiringEvent
A quantified change in network topology between two adjacent stages.
- `event_id`: String
- `tf`: String
- `stage_a`: String (FK)
- `stage_b`: String (FK)
- `weight_delta`: Float ($\Delta$ edge weight)
- `stability_score`: Float (Consistency across sensitivity sweep)

### 4. DisorderRiskProfile
A curated list of genes associated with a neurological condition.
- `disorder_name`: String (e.g., "Schizophrenia")
- `risk_genes`: List of Strings (Gene Symbols)
- `source`: String (e.g., "GWAS Catalog")
- `evidence_level`: String

## Storage Schema

- **Processed Data**: `data/processed/integrated_atlas.h5ad` (AnnData format)
- **Networks**: `data/processed/networks/{stage_id}.json` (Adjacency list)
- **Rewiring**: `data/processed/rewiring_events.csv`
- **Enrichment**: `data/processed/disorder_enrichment.csv`
