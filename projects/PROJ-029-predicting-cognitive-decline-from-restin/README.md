# Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Project**: PROJ-029-predicting-cognitive-decline-from-restin
**Goal**: Train a Random Forest classifier to predict cognitive decline (MMSE/MOCA drop ≥ 3 points) using graph-theoretic metrics derived from resting-state fMRI connectivity matrices.

## Prerequisites

### System Requirements
- **RAM**: Minimum 7 GB (strict limit enforced during graph metric calculation)
- **CPU**: 2 cores recommended (parallelism limited to 2 jobs)
- **Storage**: ~20 GB for raw data, ~2 GB for processed artifacts
- **Software**: Python 3.11+, FSL (for `mcflirt` motion correction), Git

### Dataset
- **Source**: OpenNeuro Dataset `ds000246` (Constitution VI, FR-001)
- **Requirements**:
 - Resting-state fMRI (rs-fMRI) scans available
 - Longitudinal cognitive scores (MMSE or MOCA) at two timepoints
- **Download**: Automated via `code/01_download_and_filter.py` (requires internet connection)

### Dependencies
Install all Python dependencies from `code/requirements.txt`:
```bash
cd code
pip install -r requirements.txt
```

## Project Structure

```
.
├── code/
│ ├── 00_data_gate.py # Verify dataset availability
│ ├── 01_download_and_filter.py # Download & filter subjects
│ ├── 02_preprocess_and_parcellate.py # Preprocess & extract timeseries
│ ├── 03_compute_graph_metrics.py # Calculate graph metrics
│ ├── 04_train_model.py # Train Random Forest with Nested CV
│ ├── 05_evaluate_model.py # Evaluate model performance
│ ├── 06_runtime_verifier.py # Runtime estimation & verification
│ ├── 07_sensitivity_analysis.py # Threshold & label sensitivity
│ ├── 09_generate_report.py # Generate final report
│ ├── 10_verify_success_criteria.py # Check success criteria
│ ├── 11_external_outcome_check.py # Check MCI data availability
│ ├── config.py # Configuration management
│ ├── requirements.txt # Python dependencies
│ └── utils/ # Utility modules (io, graph, stats, etc.)
├── data/
│ ├── raw/ # Downloaded BIDS data
│ ├── processed/ # Intermediate & final processed data
│ └── artifacts/ # Final reports & logs
├── specs/ # Feature specifications & contracts
└── tests/ # Unit & integration tests
```

## Execution Order

Run the pipeline phases sequentially. Each phase produces artifacts required by the next.

### Phase 0: Dataset Gate
Verify the dataset is available and contains required modalities.
```bash
cd code
python 00_data_gate.py
```
**Output**: Exits with code 2 if data/labels missing; otherwise logs verification status.

### Phase 1: Data Ingestion & Filtering
Download data and filter for eligible subjects (non-null scores at both timepoints).
```bash
python 01_download_and_filter.py
```
**Outputs**:
- `data/processed/eligible_subjects.csv`
- `data/processed/excluded_subjects.log`

### Phase 2: Preprocessing & Parcellation
Motion correction, normalization, and atlas-based timeseries extraction.
```bash
python 02_preprocess_and_parcellate.py
```
**Outputs**: 90x90 connectivity matrices per subject in `data/processed/connectivity/`

### Phase 3: Graph Metric Calculation
Compute node degree, global efficiency, clustering coefficient, and path length.
```bash
python 03_compute_graph_metrics.py
```
**Outputs**:
- `data/processed/graph_metrics.csv`
- Memory profile logged to `data/artifacts/memory_profile.log`

### Phase 4: Model Training & Evaluation
Train Random Forest with nested cross-validation and evaluate performance.
```bash
# Train model
python 04_train_model.py

# Evaluate model
python 05_evaluate_model.py
```
**Outputs**:
- `data/processed/model.pkl`
- `data/processed/performance_report.json`

### Phase 5: Statistical Validation
Run permutation test and sensitivity analysis.
```bash
# Permutation test (500 permutations)
python 06_permutation_test.py

# Sensitivity analysis
python 07_sensitivity_analysis.py
```
**Outputs**:
- `data/processed/permutation_results.json`
- `data/processed/sensitivity_report.json`

### Phase 6: Reporting & Verification
Generate final report and verify success criteria.
```bash
# Check external outcome data
python 11_external_outcome_check.py

# Generate final report
python 09_generate_report.py

# Verify success criteria
python 10_verify_success_criteria.py
```
**Outputs**:
- `data/artifacts/final_report.md`
- `data/artifacts/limitations.txt`
- `data/artifacts/runtime_report.json`

## Reproducing Results

1. **Clean Start**: Remove `data/raw/`, `data/processed/`, and `data/artifacts/` to ensure a fresh run.
2. **Set Seed**: Ensure `random_seed=42` in `code/config.py` (default).
3. **Run Full Pipeline**: Execute scripts in the order listed above.
4. **Verify**: Check `data/artifacts/verification_status.txt` for success criteria compliance:
 - ROC-AUC > 0.50
 - p-value < 0.05
 - Total runtime < 6 hours

## Testing

Run the test suite to validate implementation:
```bash
cd tests
pytest unit/ -v
pytest integration/ -v
```

## Limitations & Notes

- **Associational Findings**: All results are associational (FR-007); no causal claims.
- **External Outcome**: MCI conversion data may be unavailable; check `data/artifacts/limitations.txt`.
- **Memory Constraints**: Graph metric calculation is strictly limited to 7 GB RAM.
- **Runtime Limits**: Permutation test aborts if estimated runtime > 2 hours.

## Troubleshooting

- **FSL not found**: Ensure FSL is installed and `fsl` command is in PATH.
- **Memory Error**: Reduce `N` (max subjects) in `01_download_and_filter.py` or increase RAM.
- **Download Failure**: Check internet connection; `01_download_and_filter.py` includes retry logic.
- **Runtime Exceeded**: Reduce permutations in `06_permutation_test.py` (not recommended for final run).