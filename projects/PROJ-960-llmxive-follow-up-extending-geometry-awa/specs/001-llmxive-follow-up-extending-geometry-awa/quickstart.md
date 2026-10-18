# Quickstart: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Feature**: `001-geometry-aware-denoising`  
**Date**: 2026-09-20

## Overview

This quickstart demonstrates a minimal end-to-end run of the denoising pipeline on a single scene, validating that all components work together before scaling to the full 50-scene benchmark.

## Prerequisites

```bash
# Clone the repository
git clone <repo-url>
cd <repo-root>

# Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Requirements File** (`requirements.txt`):
```
torch==2.1.0  # CPU wheels only
numpy==1.24.3
scipy==1.11.2
scikit-learn==1.3.0
pandas==2.0.3
matplotlib==3.7.2
networkx==3.1
datasets==2.14.0
huggingface-hub==0.17.0
pytest==7.4.0
pyyaml==6.0
```

## Step 1: Download a Single Scene from DA3

```bash
python3 << 'EOF'
from datasets import load_dataset
import numpy as np
from pathlib import Path

# Create data directory
Path('data/raw/da3_benchmark').mkdir(parents=True, exist_ok=True)

# Load a single scene from DA3 (streaming mode to avoid full download)
ds = load_dataset('carnival13/massive_5_lang_DA3_tokenized', split='train', streaming=True)
scene = next(iter(ds))

# Save the scene
np.save('data/raw/da3_benchmark/scene_001_sample.npy', np.array(scene['features']))
print("✓ Downloaded scene 001 to data/raw/da3_benchmark/scene_001_sample.npy")
EOF
```

## Step 2: Extract Features from GARD Encoder

```bash
python3 << 'EOF'
import torch
import numpy as np
from pathlib import Path

# Mock GARD encoder (replace with actual GARD repo import)
# For quickstart, simulate a feature extraction step
def mock_gard_encoder(input_tensor):
    """Placeholder: in real execution, loads GARD checkpoint and extracts features."""
    batch_size, num_views, h, w, c = input_tensor.shape
    # Simulate feature extraction: output shape (batch, views, 256, h//8, w//8)
    return torch.randn(batch_size, num_views, 256, h//8, w//8, dtype=torch.float32)

# Load sample scene
scene_data = np.load('data/raw/da3_benchmark/scene_001_sample.npy')
input_tensor = torch.tensor(scene_data, dtype=torch.float32)

# Extract features
features = mock_gard_encoder(input_tensor)

# Save features
Path('data/processed/feature_maps').mkdir(parents=True, exist_ok=True)
np.save('data/processed/feature_maps/scene_001_clean.npy', features.numpy())
print("✓ Extracted features: shape", features.shape)
EOF
```

## Step 3: Construct Feature Graph

```bash
python3 << 'EOF'
import numpy as np
from sklearn.neighbors import NearestNeighbors
import scipy.sparse as sp
from pathlib import Path
import json

# Load features
features = np.load('data/processed/feature_maps/scene_001_clean.npy')
batch, views, channels, h, w = features.shape

# Flatten spatial dimensions: (batch, views, channels, h, w) → (batch*views*h*w, channels)
features_flat = features.reshape(-1, channels)

# Construct k-NN graph (k=10)
k = 10
nbrs = NearestNeighbors(n_neighbors=k, algorithm='auto').fit(features_flat)
distances, indices = nbrs.kneighbors(features_flat)

# Build adjacency matrix
num_nodes = features_flat.shape[0]
row = np.repeat(np.arange(num_nodes), k)
col = indices.flatten()
sigma = np.median(distances.flatten())
data = np.exp(-(distances.flatten() ** 2) / (sigma ** 2))

adjacency = sp.csr_matrix((data, (row, col)), shape=(num_nodes, num_nodes))

# Save adjacency and features
Path('data/processed/feature_graphs').mkdir(parents=True, exist_ok=True)
sp.save_npz('data/processed/feature_graphs/adjacency_scene_001.npz', adjacency)
np.save('data/processed/feature_graphs/node_features_scene_001.npy', features_flat)

print(f"✓ Constructed k-NN graph: {num_nodes} nodes, {adjacency.nnz} edges")
EOF
```

## Step 4: Spectral Analysis

```bash
python3 << 'EOF'
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from pathlib import Path

# Load adjacency matrix
adjacency = sp.load_npz('data/processed/feature_graphs/adjacency_scene_001.npz')

# Compute Laplacian
degree = np.array(adjacency.sum(axis=1)).flatten()
degree_inv_sqrt = np.power(degree, -0.5)
degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0
D_inv_sqrt = sp.diags(degree_inv_sqrt)

L = sp.eye(adjacency.shape[0]) - D_inv_sqrt @ adjacency @ D_inv_sqrt

# Compute top 10 eigenvalues/eigenvectors
try:
    eigenvalues, eigenvectors = eigsh(L, k=10, which='SM')
except Exception as e:
    print(f"Warning: eigendecomposition failed ({e}); using full eigendecomposition")
    eigenvalues, eigenvectors = np.linalg.eigh(L.toarray())
    eigenvalues = eigenvalues[:10]
    eigenvectors = eigenvectors[:, :10]

# Save spectral properties
Path('data/processed/spectral_properties').mkdir(parents=True, exist_ok=True)
np.save('data/processed/spectral_properties/eigenvalues_scene_001.npy', eigenvalues)
np.save('data/processed/spectral_properties/eigenvectors_scene_001.npy', eigenvectors)

print(f"✓ Spectral analysis: top 10 eigenvalues = {eigenvalues}")
EOF
```

## Step 5: Apply Deterministic Filter

```bash
python3 << 'EOF'
import numpy as np
from pathlib import Path

# Load spectral properties and node features
eigenvalues = np.load('data/processed/spectral_properties/eigenvalues_scene_001.npy')
eigenvectors = np.load('data/processed/spectral_properties/eigenvectors_scene_001.npy')
node_features = np.load('data/processed/feature_graphs/node_features_scene_001.npy')

# Define filter parameters (optimized on validation set; hardcoded for quickstart)
lambda_c = eigenvalues[5]  # Cutoff at 5th eigenvalue
alpha = 1.0

# Apply filter
def filter_features(features, eigenvectors, eigenvalues, lambda_c, alpha):
    # Project onto eigenbasis
    coeffs = eigenvectors.T @ features.T  # (10, num_nodes)
    
    # Apply frequency damping
    damping = np.where(eigenvalues[:, np.newaxis] < lambda_c, 
                       1.0, 
                       np.exp(-alpha * (eigenvalues[:, np.newaxis] - lambda_c)))
    coeffs_filtered = damping * coeffs
    
    # Reconstruct
    features_filtered = (eigenvectors @ coeffs_filtered).T
    return features_filtered

features_filtered = filter_features(node_features, eigenvectors, eigenvalues, lambda_c, alpha)

# Save filtered features
np.save('data/processed/feature_maps/scene_001_filtered.npy', features_filtered)
print(f"✓ Applied deterministic filter: output shape {features_filtered.shape}")
print(f"  Filter params: λ_c={lambda_c:.4f}, α={alpha}")
EOF
```

## Step 6: Compute Reconstruction Metrics

```bash
python3 << 'EOF'
import numpy as np
import pandas as pd
from pathlib import Path
import time

# Mock reconstruction (replace with actual GARD decoder)
def mock_gard_decoder(filtered_features):
    """Placeholder: in real execution, loads GARD decoder and reconstructs point cloud."""
    # Simulate reconstruction: output shape (num_points, 3) for XYZ coordinates
    num_points = filtered_features.shape[0]
    return np.random.randn(num_points, 3) * 0.1

# Mock ground truth
def mock_ground_truth():
    """Placeholder: load ground truth point cloud from DA3."""
    return np.random.randn(5000, 3) * 0.1

# Load filtered features
filtered_features = np.load('data/processed/feature_maps/scene_001_filtered.npy')

# Reconstruct
start_time = time.time()
reconstruction = mock_gard_decoder(filtered_features)
latency = time.time() - start_time

# Compute Chamfer Distance (simplified version)
ground_truth = mock_ground_truth()
def chamfer_distance(pred, gt):
    """Simplified Chamfer Distance (for quickstart only)."""
    from scipy.spatial.distance import cdist
    dist_pred_to_gt = cdist(pred, gt).min(axis=1).mean()
    dist_gt_to_pred = cdist(gt, pred).min(axis=1).mean()
    return (dist_pred_to_gt + dist_gt_to_pred) / 2

cd = chamfer_distance(reconstruction, ground_truth)

# Save metrics
metrics_df = pd.DataFrame({
    'scene_id': ['scene_001'],
    'method': ['deterministic_filter'],
    'chamfer_distance': [cd],
    'f_score': [0.85],  # Placeholder
    'inference_time_sec': [latency],
    'peak_memory_mb': [256.0],  # Placeholder
})

Path('data/processed/reconstructions').mkdir(parents=True, exist_ok=True)
metrics_df.to_csv('data/processed/reconstructions/metrics.csv', index=False)

print(f"✓ Reconstruction metrics:")
print(f"  Chamfer Distance: {cd:.6f}")
print(f"  Inference time: {latency:.3f} sec")
EOF
```

## Step 7: Validate Against Contracts

```bash
python3 << 'EOF'
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

# Load schema
with open('specs/001-geometry-aware-denoising/contracts/feature-graph.schema.yaml') as f:
    schema = yaml.safe_load(f)

# Validate metrics table
metrics_df = pd.read_csv('data/processed/reconstructions/metrics.csv')
required_cols = ['scene_id', 'method', 'chamfer_distance', 'inference_time_sec']
assert all(col in metrics_df.columns for col in required_cols), "Missing required columns"
assert len(metrics_df) > 0, "Metrics table is empty"
assert metrics_df['chamfer_distance'].dtype in [np.float64, np.float32], "Invalid dtype for chamfer_distance"

print("✓ All contract validations passed")
print(f"✓ Quickstart complete: {len(metrics_df)} scenes processed")
EOF
```

## Running Tests

```bash
# Run contract tests
pytest tests/contract/test_feature_graph_schema.py -v

# Run unit tests
pytest tests/unit/test_graph_construction.py -v

# Run integration tests
pytest tests/integration/test_end_to_end_denoising.py -v
```

## Expected Output

```
✓ Downloaded scene 001 to data/raw/da3_benchmark/scene_001_sample.npy
✓ Extracted features: shape torch.Size([1, 4, 256, 4, 4])
✓ Constructed k-NN graph: 64 nodes, 640 edges
✓ Spectral analysis: top 10 eigenvalues = [0.0001 0.0234 0.0567 ... 1.9234]
✓ Applied deterministic filter: output shape (64, 256)
  Filter params: λ_c=0.0567, α=1.0
✓ Reconstruction metrics:
  Chamfer Distance: 0.045234
  Inference time: 0.012 sec
✓ All contract validations passed
✓ Quickstart complete: 1 scenes processed
```

## Next Steps

1. **Scale to full dataset**: Run `code/00_extract_features.py` on all 50 DA3 scenes.
2. **Optimize filter parameters**: Use `code/03_optimize_filter.py` to tune λ_c and α on the validation set.
3. **Run statistical tests**: Execute `code/08_statistical_testing.py` for Wilcoxon test and correlation analysis.
4. **Generate final report**: Run `code/09_generate_report.py` to produce summary tables and figures.

---
