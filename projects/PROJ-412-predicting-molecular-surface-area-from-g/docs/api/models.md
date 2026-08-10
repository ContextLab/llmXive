# Models Module API Documentation

This document provides detailed API documentation for the `code/models/` module, covering the implementation of Functional Requirements FR-001 to FR-007 related to model training, baseline comparison, and evaluation.

## Overview

The models module implements:
- **FR-001**: GCN model training on graph data
- **FR-002**: Baseline model training (2D and 3D descriptors)
- **FR-003**: Model evaluation with multiple metrics
- **FR-004**: Statistical comparison between models
- **FR-005**: Early stopping and training optimization
- **FR-006**: Memory monitoring and OOM handling
- **FR-007**: Reproducible training with seed management

## Modules

### `code/models/gcn.py`

Implements the Graph Convolutional Network for SASA prediction.

#### Classes

**`GCNModel`**
PyTorch Geometric GCN model for molecular graph learning.

**Attributes**:
- `conv1: GCNConv`: First graph convolution layer
- `conv2: GCNConv`: Second graph convolution layer
- `fc: Linear`: Fully connected output layer
- `dropout: Dropout`: Dropout regularization

**Methods**:

**`forward(x: Tensor, edge_index: Tensor, batch: Tensor) -> Tensor`**
Forward pass through the GCN:
- Applies two GCN convolution layers with ReLU activation
- Applies global mean pooling over nodes
- Returns predicted SASA values
- Implements FR-001: Graph-based learning

**Constructor Parameters**:
- `input_dim: int`: Dimension of node features
- `hidden_dim: int`: Hidden layer dimension
- `output_dim: int`: Output dimension (1 for SASA)
- `dropout: float`: Dropout rate (default: 0.1)

**`create_model_from_processed_data(input_dim: int, hidden_dim: int = 64) -> GCNModel`**
Factory function to create GCNModel with appropriate dimensions.

---

### `code/models/baseline.py`

Implements baseline models using molecular descriptors.

#### Functions

**`extract_geometry_features(df: pd.DataFrame) -> np.ndarray`**
Extracts 3D geometric descriptors from dataframe:
- `radius_of_gyration`
- `principal_moment_1`, `principal_moment_2`, `principal_moment_3`
- `sasa_components`
- Implements FR-002: Geometry-based baseline (FR-004 requirement)

**`load_processed_data_for_baseline_3d(path: Path) -> pd.DataFrame`**
Loads processed dataset for 3D baseline training.

**`extract_topological_features_for_geometry(df: pd.DataFrame) -> np.ndarray`**
Extracts 2D topological descriptors:
- `NumHeteroatoms`
- `NumRings`
- `MolWt`
- `NumRotatableBonds`
- Implements FR-002: 2D descriptor baseline

**`train_baseline_model(X: np.ndarray, y: np.ndarray) -> LinearRegression`**
Trains a Linear Regression model on provided features.
- Implements FR-002: Baseline model training
- Returns fitted scikit-learn model

**`evaluate_model(model: LinearRegression, X: np.ndarray, y: np.ndarray) -> Dict[str, float]`**
Evaluates model performance:
- Calculates MAE, RMSE, R²
- Implements FR-003: Model evaluation metrics

**`save_predictions(smiles: List[str], y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None`**
Saves predictions to Parquet file with error column.

**`main() -> None`**
Entry point for baseline training pipeline.

---

### `code/models/train.py`

Implements the training loop with early stopping and memory monitoring.

#### Classes

**`EarlyStopping`**
Early stopping callback with patience and minimum delta.

**Attributes**:
- `patience: int`: Number of epochs to wait
- `min_delta: float`: Minimum improvement threshold
- `counter: int`: Current counter
- `best_loss: float`: Best validation loss seen
- `should_stop: bool`: Flag to stop training

**Methods**:
- `__call__(val_loss: float) -> bool`: Update and check if should stop

#### Functions

**`load_processed_graphs(path: Path) -> List[Data]`**
Loads processed graphs from Parquet file and converts to PyG Data objects.

**`train_epoch(model: GCNModel, loader: DataLoader, optimizer: Optimizer, device: str) -> float`**
Trains one epoch of the model:
- Implements FR-005: Training loop with gradient accumulation
- Returns average training loss

**`train_epoch_corrected(model: GCNModel, loader: DataLoader, optimizer: Optimizer, device: str, accumulation_steps: int = 4) -> float`**
Trains one epoch with gradient accumulation for memory efficiency.
- Implements FR-005: Memory-optimized training

**`evaluate(model: GCNModel, loader: DataLoader, device: str) -> Tuple[float, np.ndarray, np.ndarray]`**
Evaluates model on validation/test set:
- Returns (average loss, predictions, targets)
- Implements FR-003: Evaluation metrics calculation

**`train_model(model: GCNModel, train_loader: DataLoader, val_loader: DataLoader, epochs: int, device: str) -> EarlyStopping`**
Trains model with early stopping:
- Implements FR-005: Early stopping with patience=5, max 50 epochs
- Uses MemoryMonitor for OOM detection (FR-006)
- Implements dynamic batch size fallback (FR-006)
- Returns EarlyStopping instance with final state

**`generate_predictions(model: GCNModel, loader: DataLoader, device: str) -> Tuple[np.ndarray, np.ndarray]`**
Generates predictions for all samples in loader.

**`main() -> None`**
Entry point for GCN training pipeline.

---

### `code/models/evaluation.py`

Implements evaluation metrics and statistical comparison.

#### Classes

**`EvaluationResult`**
Dataclass for storing evaluation results.

**Attributes**:
- `model_type: str`: Type of model evaluated
- `mae: float`: Mean Absolute Error
- `rmse: float`: Root Mean Squared Error
- `r2: float`: R-squared coefficient
- `predictions: List[float]`: Predicted values
- `errors: List[float]`: Prediction errors

**Methods**:
- `to_json() -> str`: Serialize to JSON
- `summary() -> str`: Generate human-readable summary

#### Functions

**`compare_models(y_true: np.ndarray, y_pred_gcn: np.ndarray, y_pred_baseline: np.ndarray) -> Dict[str, Any]`**
Compares two models using statistical tests:
- Paired t-test on prediction errors
- Cohen's d effect size
- Implements FR-004: Model comparison with statistical significance

---

## Traceability to Functional Requirements

| FR-ID | Description | Implemented In |
|-------|-------------|----------------|
| FR-001 | GCN model training | `gcn.py` - `GCNModel.forward()`, `train.py` - `train_model()` |
| FR-002 | Baseline model training | `baseline.py` - `train_baseline_model()` |
| FR-003 | Model evaluation metrics | `evaluation.py` - `EvaluationResult`, `train.py` - `evaluate()` |
| FR-004 | Statistical model comparison | `evaluation.py` - `compare_models()` |
| FR-005 | Early stopping and optimization | `train.py` - `EarlyStopping`, `train_epoch()` |
| FR-006 | Memory monitoring and OOM handling | `train.py` - MemoryMonitor integration |
| FR-007 | Reproducible training | `train.py` - Seed management via `utils.seed` |

## Usage Examples

### Training GCN Model
```python
from code.models.gcn import GCNModel, create_model_from_processed_data
from code.models.train import train_model, load_processed_graphs
from code.utils.seed import set_seed

set_seed(42)
graphs = load_processed_graphs('data/processed/paired_dataset.parquet')
model = create_model_from_processed_data(input_dim=6, hidden_dim=64)
early_stopper = train_model(model, train_loader, val_loader, epochs=50, device='cpu')
```

### Training Baseline Models
```python
from code.models.baseline import extract_geometry_features, train_baseline_model, evaluate_model

df = pd.read_parquet('data/processed/paired_dataset.parquet')
X = extract_geometry_features(df)
y = df['surface_area'].values
model = train_baseline_model(X, y)
metrics = evaluate_model(model, X, y)
```

### Comparing Models
```python
from code.models.evaluation import compare_models

results = compare_models(y_true, y_pred_gcn, y_pred_baseline)
print(f"p-value: {results['p_value']}, Cohen's d: {results['cohen_d']}")
```

## Error Handling

All training functions implement robust error handling:
- OOM errors trigger batch size reduction (FR-006)
- Invalid gradients trigger early stopping
- MemoryMonitor logs peak usage per epoch
- All errors are logged with full stack traces

## Dependencies

- `torch`: Deep learning framework
- `torch_geometric`: Graph neural networks
- `scikit-learn`: Baseline models and metrics
- `numpy`: Numerical operations
- `pandas`: Data loading
