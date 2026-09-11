# Data Model: Predicting Polymer Degradation Pathways

## Entities

*   **PolymerRecord**: Represents a single polymer instance with its chemical structure, environmental conditions, and observed degradation pathway.

    *   `smiles` (str): SMILES string representing the polymer's chemical structure.
    *   `temperature` (float): Temperature in Celsius during degradation.
    *   `ph` (float): pH value during degradation.
    *   `uv_exposure` (float): UV exposure level during degradation.
    *   `degradation_pathway` (str): Categorical label representing the observed degradation pathway (e.g., "hydrolysis", "oxidation").
*   **MolecularGraph**: The graph representation of a polymer record.

    *   `nodes` (list): List of node features (atom types, charges, etc.).
    *   `edges` (list): List of edge features (bond types, distances, etc.).
*   **DegradationPathway**: Categorical label representing the type of degradation.

    *   `pathway_name` (str):  The name of the degradation pathway (e.g. "hydrolysis", "photolysis", "oxidation").
*   **MotifImportance**:  Represents the importance of a specific structural motif in predicting degradation.

    *   `motif_id` (int): Unique identifier for the motif.
    *   `pathway` (str): The degradation pathway the motif is associated with.
    *   `importance_score` (float):  The score representing the importance of the motif.

## Relationships

*   A `PolymerRecord` is represented as a `MolecularGraph`.
*   A `PolymerRecord` has one `DegradationPathway`.
*   A `DegradationPathway` can be associated with multiple `MotifImportance` records.

## Schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  PolymerRecord:
    type: object
    properties:
      smiles:
        type: string
        description: "SMILES string representing the polymer."
      temperature:
        type: number
        format: float
        description: "Temperature in Celsius."
      ph:
        type: number
        format: float
        description: "pH value."
      uv_exposure:
        type: number
        format: float
        description: "UV exposure level."
      degradation_pathway:
        type: string
        description: "Degradation pathway."
    required:
      - smiles
      - temperature
      - ph
      - uv_exposure
      - degradation_pathway

  MolecularGraph:
    type: object
    properties:
      nodes:
        type: array
        items:
          type: array
          description: "Node features."
      edges:
        type: array
        items:
          type: array
          description: "Edge features."
    required:
      - nodes
      - edges

  DegradationPathway:
    type: object
    properties:
      pathway_name:
        type: string
        description: "Name of the degradation pathway."
    required:
      - pathway_name

  MotifImportance:
    type: object
    properties:
      motif_id:
        type: integer
        description: "Unique identifier for the motif."
      pathway:
        type: string
        description: "Degradation pathway."
      importance_score:
        type: number
        format: float
        description: "Importance score of the motif."
    required:
      - motif_id
      - pathway
      - importance_score
```
