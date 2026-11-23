# Known Issues

## Data Fetching
- **Issue**: NIST API may be slow or rate-limited.
- **Workaround**: The system automatically falls back to simulation data if the fetch fails or returns insufficient records (< 500).

## Small Molecules
- **Issue**: Some polymer repeat units may have MW < 1000 Da.
- **Status**: Flagged in `logs/small_molecule_review.csv` for manual review. Not excluded by default.

## Memory Usage
- **Issue**: Large datasets may cause high memory usage during graph batching.
- **Mitigation**: Optimized data loading and batching implemented in `performance_optimizer.py`.

## Scaffold Split
- **Issue**: Strict scaffold splitting may result in very small test sets for certain datasets.
- **Status**: This is an intentional design choice to ensure true generalization.

## 3D Features
- **Issue**: Users may expect 3D structural features.
- **Status**: Explicitly excluded per FR-001. Only 2D features are used.
