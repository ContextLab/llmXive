# Data Model: llmXive follow-up: extending "Intern-Atlas"

## Entities & Relationships

### MethodNode
- **Description**: A node representing a research method in the Intern-Atlas graph.
- **Attributes**:
  - `paper_id` (str): Unique identifier (DOI or internal ID).
  - `title` (str): Paper title.
  - `year` (int): Publication year.
  - `outgoing_edges` (list): List of edge objects.
  - `incoming_citations` (int): Total citation count.
  - `field_of_study` (str): Subject area.
  - `venue` (str): Journal/Conference name.

### RetractionLabel
- **Description**: External truth label mapped to a MethodNode.
- **Attributes**:
  - `paper_id` (str): Matched ID.
  - `status` (int): 0 (Robust), 1 (Fragile), 2 (Retraction-Only).
  - `source` (str): "Retraction Watch" or "Replication Index".
  - `retraction_reason` (str): Reason for retraction.

### TopologicalFeatures
- **Description**: Derived record for analysis.
- **Attributes**:
  - `paper_id` (str): Primary key.
  - `bottleneck_resolution_ratio` (float): Calculated BRR.
  - `branching_entropy` (float): Calculated BE.
  - `citation_count` (int): Total citations.
  - `publication_year` (int): Year.
  - `retraction_status` (int): Label (0, 1, 2).
  - `field_of_study` (str): Field.
  - `venue` (str): Venue.
  - **Note**: BRR and BE are mathematically coupled (derived from same edge distribution). High correlation is expected. **If VIF > 5, the model will be re-run using only 'branching_entropy' or a composite metric, and this will be reported as a sensitivity analysis.**

### ModelResult
- **Description**: Output of model training/evaluation.
- **Attributes**:
  - `model_type` (str): "Topological" or "Baseline".
  - `auc_roc` (float): Area Under ROC Curve.
  - `precision` (float).
  - `recall` (float).
  - `f1_score` (float).
  - `stability_flag` (bool): True if VIF > 5 or MI > 0.1.
  - `structural_coupling_handled` (bool): True if the model was re-run due to high VIF.

## Data Flow
1. **Raw Input**: `intern-atlas-snapshot.graphml`, `retraction-watch-dump.csv`.
2. **Intermediate**: `nodes_filtered.csv` (2010-2018).
3. **Derived**: `features_2010_2018.csv` (merged with labels, fuzzy matching applied).
4. **Output**: `model_results.json`, `plots/`.

## Constraints
- **Date Range**: 2010-01-01 to 2018-12-31.
- **Edge Types**: Only human-annotated `improves`/`replaces`/`extends` allowed for BRR calculation. **Exclude** any edge types linked to retraction outcomes (e.g., 'retracted').
- **Label Logic**: Strict mapping based on retraction reason.
- **Matching**: Exact DOI first, then Levenshtein >= 0.85.