# Models Module

This module contains the core data models used throughout the `llmXive` molecular surface area prediction pipeline.

## Entities

### `Molecule`
Represents a chemical entity.
- **Input**: SMILES string, metadata.
- **Output**: Enriched with 3D properties (SASA) after processing.
- **Location**: `code/models/molecule.py`

### `Graph`
Represents the graph structure derived from a `Molecule` for GNN input.
- **Fields**: `node_features`, `edge_index`, `edge_features`, `y` (target).
- **Format**: Compatible with PyTorch Geometric (NumPy arrays).
- **Location**: `code/models/graph.py`

### `EvaluationResult`
Aggregates performance metrics and predictions after model inference.
- **Metrics**: MAE, RMSE, R², p-values, Cohen's d.
- **Location**: `code/models/evaluation.py`

## Usage

```python
from code.models import Molecule, Graph, EvaluationResult
import numpy as np

# Create a molecule
mol = Molecule(smiles="CCO", molecule_id="test_001")

# Create a graph
graph = Graph(
 molecule_id="test_001",
 node_features=np.array([[1, 0], [0, 1]]),
 edge_index=np.array([[0, 1], [1, 0]]),
 y=50.5
)

# Create evaluation result
result = EvaluationResult(
 model_name="gcn",
 dataset_split="test",
 mae=0.05,
 rmse=0.07
)
```
