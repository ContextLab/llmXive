# Quickstart: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Prerequisites

- Python 3.11 or higher
- Stable internet connection (for downloading Knot Atlas data)
- 2GB+ available disk space (for dataset storage and computation)

## Installation

1. **Clone the repository** (if using local copy):
```bash
git clone <repository-url>
cd projects/PROJ-552-quantifying-the-complexity-of-knot-diagr
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r code/config/requirements.txt
```

**Requirements File**: code/config/requirements.txt pins the following dependencies:
- pandas==2.1.4
- numpy==1.26.3
- scikit-learn==1.4.0
- scipy==1.12.0
- matplotlib==3.8.2
- pyyaml==6.0.1
- requests==2.31.0
- tqdm==4.66.1
- datasets==2.16.1
- pytest==7.4.3

## Running the Pipeline

### Step 1: Download Knot Data

```bash
python code/downloader/knot_atlas_client.py --output data/raw/knot_atlas_export.csv --max-crossing-number 13
```

**Expected Output**:
- data/raw/knot_atlas_export.csv (downloaded dataset)
- data/checksums.txt (SHA-256 checksum recorded)
- docs/reproducibility/logs/download.log (timestamped log)

**Retry Logic**: If Knot Atlas is unavailable, exponential backoff is applied (2s → [deferred] → [deferred] → [deferred] → [deferred]). Partial results cached after 3 consecutive failures.

**URL Stability Note**: Knot Atlas URL stability is not independently verified. If download fails persistently, consult docs/reproducibility/url_fallback.md for checksummed mirror options.

### Step 2: Compute Invariants

```bash
python code/invariant_computation/main.py --input data/raw/knot_atlas_export.csv --output data/derived/invariants_computed.csv
```

**Expected Output**:
- data/derived/invariants_computed.csv (dataset with computed invariants)
- docs/reproducibility/uncomputable_invariants.md (records with missing invariants)
- docs/reproducibility/algorithm_validation.md (validation results against KnotInfo)

### Step 3: Exploratory Analysis

```bash
python code/analysis/exploratory_analysis.py --input data/derived/invariants_computed.csv --output-dir data/plots/
```

**Expected Output**:
- data/plots/crossing_vs_braid_alternating.png (1200x900 pixels)
- data/plots/crossing_vs_braid_non_alternating.png (1200x900 pixels)
- docs/reproducibility/logs/analysis.log

### Step 4: Regression Modeling

```bash
python code/analysis/regression_models.py --input data/derived/invariants_computed.csv --output data/derived/regression_results.csv
```

**Expected Output**:
- data/derived/regression_results.csv (all model metrics)
- docs/reproducibility/logs/regression.log

### Step 5: Composite Score Validation

```bash
python code/analysis/composite_score.py --input data/derived/invariants_computed.csv --config code/config/complexity_weights.yaml --output data/derived/composite_score_results.csv
```

**Expected Output**:
- data/derived/composite_score_results.csv (correlation metrics)
- docs/reproducibility/logs/composite_score.log

**Sensitivity Analysis**: To run sensitivity analysis across weight configurations:
```bash
python code/analysis/composite_score.py --input data/derived/invariants_computed.csv --config code/config/complexity_weights.yaml --sensitivity-analysis --output data/derived/composite_score_sensitivity.csv
```

### Step 6: Run Full Pipeline

```bash
python code/main.py --config code/config/seeds.yaml
```

**This executes all steps in sequence with proper error handling and logging.**

## Configuration

### Random Seed Pinning

Edit code/config/seeds.yaml to set random seeds:

```yaml
random_seed: 42
numpy_seed: 42
tensorflow_seed: 42  # if applicable
```

### Composite Score Weights

Edit code/config/complexity_weights.yaml to configure weights:

```yaml
weight_crossing_number: 1.0
weight_braid_index: 1.0
```

**Note**: Equal weights (1:1 ratio) is the default with no theoretical basis; configurable for future iterations. Sensitivity analysis recommended to assess robustness across weight space (0-1 increments).

## Data Directory Structure

After running the pipeline, your data/ directory should contain:

```
data/
├── raw/
│   ├── knot_atlas_export.csv
│   └── knot_atlas_export.csv.sha256
├── derived/
│   ├── invariants_computed.csv
│   ├── regression_results.csv
│   └── composite_score_results.csv
├── plots/
│   ├── crossing_vs_braid_alternating.png
│   └── crossing_vs_braid_non_alternating.png
└── checksums.txt
```

## Reproducibility Verification

To verify reproducibility:

```bash
python code/reproducibility/validation.py --verify-all
```

**This checks**:
- All checksums match recorded values
- Random seeds are pinned correctly
- Derivation notes are complete
- Logs are properly formatted

## Testing

### Run Contract Tests

```bash
pytest tests/contract/ -v
```

**Contract Test Coverage**:
- test_knot_record.py: Validates KnotRecord outputs against knot_record.schema.yaml
- test_regression_output.py: Validates RegressionModel outputs against regression_output.schema.yaml
- test_composite_score.py: Validates CompositeComplexityScore outputs against composite_score_output.schema.yaml

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

## Troubleshooting

### Knot Atlas Unavailable

If download fails after 3 retries with exponential backoff:
1. Check network connectivity
2. Verify Knot Atlas URL is accessible
3. Partial results will be cached in data/raw/
4. Consult docs/reproducibility/url_fallback.md for checksummed mirror options
5. Logs available in docs/reproducibility/logs/download.log

### Missing Invariant Data

If invariants cannot be computed:
1. Check data/derived/invariants_computed.csv for missing_invariant_flags
2. Review docs/reproducibility/uncomputable_invariants.md for details
3. Records are flagged, not silently excluded

### Algorithm Validation Failure

If validation against KnotInfo fails:
1. Check docs/reproducibility/algorithm_validation.md for pass/fail status
2. If coverage is insufficient, validation is skipped per FR-003
3. Limitation documented in algorithm_validation.md

### Tie-Breaking Validation

To verify tie-breaking rules are applied consistently:

```bash
python code/reproducibility/validation.py --check-tie-breaking
```

**This verifies**:
- Braid word preferred over DT code when both available
- Lexicographically first DT code used when multiple exist
- Consistency across all invariant computations

### Selection Bias Awareness

Results are limited to hyperbolic knots only (torus/satellite knots excluded). See docs/reproducibility/selection_bias.md for impact analysis.

### Statistical Interpretation

For finite census (prime knots ≤13), p-values are exploratory only. Frame results as descriptive model fit (R², MAE) rather than statistical significance. See docs/reproducibility/statistical_framing.md.

## Next Steps

After completing the quickstart:

1. **Review Results**: Examine data/derived/regression_results.csv for model comparisons
2. **Check Validation**: Review docs/reproducibility/validation_scope.md for Phase 1 scope boundaries
3. **Explore Plots**: View data/plots/ for visual analysis of crossing number vs. braid index
4. **Read Documentation**: See docs/reproducibility/ for complete reproducibility artifacts
5. **Assess Sensitivity**: Run sensitivity analysis to verify composite score robustness

## Support

For issues or questions:
1. Check docs/reproducibility/logs/ for error logs
2. Review FR-003 for invariant computation requirements
3. Consult Constitution Principle I for reproducibility standards
4. See specs/004-quantifying-the-complexity-of-knot-diagr/spec.md for full specification