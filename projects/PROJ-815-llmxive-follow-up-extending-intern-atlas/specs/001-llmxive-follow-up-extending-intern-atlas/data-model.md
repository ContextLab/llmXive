# Data Model: llmXive Follow-up (Extending Intern-Atlas)

This document defines the schema for the core entities used in the analysis of the Intern-Atlas graph and retraction databases. It serves as the source of truth for data extraction, feature engineering, and model training pipelines.

## 1. MethodNode

Represents a specific research method or technique within the scientific graph. Nodes are derived from the Intern-Atlas dataset and filtered by publication year.

### Attributes

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Unique identifier for the node (e.g., hash of DOI + title). | Primary Key, Not Null |
| `doi` | `str` | Digital Object Identifier of the paper. | Unique, Nullable |
| `title` | `str` | Full title of the publication. | Not Null |
| `authors` | `List[str]` | List of author names. | Not Null |
| `publication_year` | `int` | Year of publication. | Range: 2010–2018 (for this study) |
| `field_of_study` | `str` | Broad academic field (e.g., "Computer Science", "Biology"). | Not Null |
| `publication_venue` | `str` | Name of the journal or conference. | Not Null |
| `citation_count` | `int` | Total number of citations at time of extraction. | >= 0 |

## 2. RetractionLabel

Represents the ground-truth status of a method node, derived by matching against retraction databases (e.g., Retraction Watch). This label is the target variable for the predictive models.

### Enumerated Values

The `retraction_status` field uses the following integer mapping:

| Value | Label | Description |
|:--- |:--- |:--- |
| `0` | **Robust** | No retraction found; method is considered robust within the study window. |
| `1` | **Fragile** | Retraction found due to methodological error, irreproducibility, or honest mistake. |
| `2` | **Retraction-Only** | Retraction found due to fraud, plagiarism, or data fabrication (no methodological learning). |

### Attributes

| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Foreign key referencing `MethodNode.node_id`. | Foreign Key |
| `retraction_status` | `int` | The status code (0, 1, or 2). | Enum(0, 1, 2) |
| `retraction_reason` | `str` | The original reason string from the retraction database. | Nullable |
| `retraction_date` | `str` | Date of retraction (ISO 8601). | Nullable |
| `match_method` | `str` | How the link was established: `exact_doi` or `fuzzy_title`. | Enum |

## 3. TopologicalFeatures

Represents the computed graph-derived features for a `MethodNode`. These features quantify the node's position and role within the scientific evolution graph.

### Attributes

| Field Name | Type | Description | Formula / Logic |
|:--- |:--- |:--- |:--- |
| `node_id` | `str` | Foreign key referencing `MethodNode.node_id`. | Foreign Key |
| `bottleneck_resolution_ratio` | `float` | Ratio of resolving edges to total outgoing edges. | `count(edges where type in ['improves', 'replaces']) / count(outgoing_edges)` |
| `branching_entropy` | `float` | Shannon entropy of the downstream method types. | `- Σ (p_i * log2(p_i))` where `p_i` is the proportion of outgoing edges of type `i`. |
| `total_out_degree` | `int` | Total number of outgoing edges from the node. | Sum of all outgoing edges |
| `human_annotated_edges` | `bool` | Flag indicating if all outgoing edges are human-annotated. | `True` if no `LLM_INFERRRED` edges exist; otherwise pipeline aborts. |

## 4. Derived Records (Processed Dataset)

The final output of the extraction pipeline (`data/processed/features_2010_2018.csv`) merges the above entities into a single row per node.

### Schema

| Field Name | Source | Type | Description |
|:--- |:--- |:--- |:--- |
| `node_id` | MethodNode | `str` | Unique ID |
| `publication_year` | MethodNode | `int` | Year of publication |
| `field_of_study` | MethodNode | `str` | Academic field |
| `publication_venue` | MethodNode | `str` | Venue name |
| `citation_count` | MethodNode | `int` | Citation count |
| `bottleneck_resolution_ratio` | TopologicalFeatures | `float` | Feature 1 |
| `branching_entropy` | TopologicalFeatures | `float` | Feature 2 |
| `retraction_status` | RetractionLabel | `int` | Target (0, 1, 2) |
| `retraction_status_binary` | RetractionLabel | `int` | Binary target (1=1, 0=0 or 2) |

## 5. Constraints & Validation Rules

1. **Edge Type Integrity**: The pipeline must abort if any edge of type `LLM_INFERRRED` is detected in the input graph for the selected time window. Only `improves`, `replaces`, and `extends` (human-annotated) are valid.
2. **Time Window**: All nodes must satisfy `2010 <= publication_year <= 2018`.
3. **Label Completeness**: If no ground truth labels (RetractionLabel) are found for the selected time window, the pipeline must abort with the message: "No ground truth labels found for the specified time window; analysis cannot proceed."
4. **Binary Conversion**:
 - Input `0` (Robust) → Binary `0`
 - Input `1` (Fragile) → Binary `1`
 - Input `2` (Retraction-Only) → Binary `0`
5. **Missing Edge Handling**: Nodes with 0 outgoing edges must have `bottleneck_resolution_ratio` set to `0.0` and `branching_entropy` set to `0.0`.