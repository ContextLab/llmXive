# Quickstart: Neural Correlates of Temporal Prediction Errors in Auditory Scene Analysis

## Prerequisites

- Python 3.x (recent versions)
- Git
- GitHub Actions Runner or Linux environment with $\ge 7$ GB RAM.

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-250-neural-correlates-of-temporal-prediction
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed in sequence via the `code/` directory.

### 0. Reference verification gates (FR-012)
```bash
python code/verify_references.py --stage dataset
python code/verify_references.py --stage citations
```
- Verifies the dataset ID/URL against the canonical OpenNeuro source before any download.
- Verifies all citations against their named primary sources and writes
  `data/results/citation_verification.json` before any report is written.

### 1. Data Acquisition
```bash
python code/download.py --subjects 2
```
- Downloads the OpenNeuro ds004510 dataset (2 subjects for the first
  end-to-end pass; `--subjects 0` for the full cohort).
- Verifies checksums (`data/raw/checksums.json`) and metadata
  (`data/results/dataset_metadata.json`), and runs the condition gate.
- **Halt Condition**: Stops if the "complex" condition is missing from the dataset.

### 2. Preprocessing
```bash
python code/preprocess.py
```
- Applies the 1–40 Hz bandpass filter.
- Performs ICA artifact rejection.
- Re-references to average mastoids.
- Subtracts baseline (mean of −200 to 0 ms).
- Segments data into epochs (−200 to 500 ms).

### 3. Analysis
```bash
python code/analysis.py
```
- Computes MMN amplitude/latency.
- Validates SNR ≥ 3.0 using the pre-stimulus baseline standard deviation.
- Generates canonical MMN topography template from 'simple' condition.
- Performs topographic consistency check (simple vs. template).
- Performs topographic validity check (complex vs. template).
- Performs paired t-tests with FDR correction.
- Calculates Cohen's $d$ and topographic correlations.

### 4. Visualization
```bash
python code/visualize.py
```
- Generates ERP waveforms, scalp maps, and significance plots in `data/results/figures/`.

## Validation

Run the contract tests to ensure data integrity and statistical validity:
```bash
pytest code/tests/
```
This verifies:
- `data/results/metrics.csv` matches `contracts/output.schema.yaml`.
- `data/results/stats.json` matches `contracts/output.schema.yaml`.
- Per-subject rows in `data/results/metrics_per_subject.csv` match
  `contracts/metrics_per_subject.schema.yaml`.
- Signal validity logic (SNR ≥ 3.0 using the baseline SD) is correctly applied.
- FDR-corrected p-values are used for significance flags.
- Topographic consistency and validity checks are properly distinguished.