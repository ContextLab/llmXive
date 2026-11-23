# Performance Optimization Guide

## T037: PCA Optimization for PGLS

### Problem Statement

When the number of genomic features (BGC counts, types) exceeds the number of
species samples, standard PGLS models are prone to overfitting and numerical
instability.

### Solution

The `train_pgls_with_pca_optimization()` function in `code/modeling/train.py`
automatically detects when feature count > sample count and applies PCA
dimensionality reduction before PGLS modeling.

### Configuration

- **Variance Threshold**: Default 0.95 (retain 95% of variance)
- **Max Components**: Optional cap on PCA components
- **Feature Threshold**: Can be configured via `pca_feature_threshold` in config

### Usage

```python
from code.modeling.train import train_pgls_with_pca_optimization

result = train_pgls_with_pca_optimization(
 X=feature_matrix,
 y=target_vector,
 species_names=species_list,
 tree_path="data/raw/phylogeny/tree.nwk",
 variance_threshold=0.95
)

if result['optimization_applied']:
 print(f"PCA reduced {result['pca_info']['original_features']} "
 f"to {result['pca_info']['reduced_features']} features")
```

### Testing

Run unit tests to verify optimization logic:

```bash
pytest tests/unit/test_pca_optimization.py -v
```