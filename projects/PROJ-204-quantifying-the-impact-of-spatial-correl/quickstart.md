# Quickstart: Quantifying Spatial Correlations in Perovskite Solar Cell Efficiency

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with ~7GB RAM.

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-204-quantifying-the-impact-of-spatial-correl
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` pins versions for CPU-only compatibility.*

## Data Setup

1. **Check data feasibility** (Task T100):
 Before any download attempt, verify that a real source with linked EDS
 maps exists.

 ```bash
 python -m code.data.feasibility
 ```

 The script probes the NREL Perovskite Database, the Zenodo REST API
 (`https://zenodo.org/api/records/?q=perovskite+EDS`), and the Materials
 Project API, and writes `data/results/data_feasibility_report.json`
 containing, per source: the probed URL, reachability, HTTP status,
 record count, whether EDS image files are programmatically linked to
 performance metrics, and evidence sample IDs.

 If the report contains `"verdict": "halt"` the script exits non-zero
 (no substitute data is produced) and the pipeline cannot proceed; the
 plan's Data Availability Report path applies.

2. **Download Raw Data**:
 Run the ingestion script to fetch verified JSONs and attempt EDS downloads.
 ```bash
 python code/data/download.py
 ```
 *This script reads the verified URLs from the spec and populates `data/raw/`.*

3. **Verify Data**:
 Check that `data/raw/` contains the JSON files and any available EDS maps.
 ```bash
 ls -lh data/raw/
 ```
 *If EDS maps are missing, the pipeline will halt with a "Data Availability Report".*

## Running the Pipeline

Execute the full analysis pipeline:

```bash
python code/main_pipeline.py --config <path-to-config.yaml>
```

This script performs the following steps in order:
1. **Data Feasibility Check**: Verify EDS link programmatic access.
2. **Align & Mask**: Preprocesses EDS maps (FR-001).
3. **Co-location Validation**: Checks ID matching (FR-007).
4. **Depth Resolution Validation**: Checks EDS vs PCE depth (FR-008).
5. **Extract Metrics**: Computes autocorrelation and spectral power (FR-002, FR-003).
6. **Model**: Runs correlations, BH correction, and GAMs (FR-004).
7. **Robustness**: Performs LOO-CV (FR-005).
8. **Sensitivity Analysis**: Performs conditional exclusion (FR-008).
9. **Report**: Generates `results/summary_report.csv`, `results/summary_report.pdf`, and `results/ingestion_metrics.json` (SC-004).

## Testing

Run the unit tests to verify metric extraction accuracy (SC-001):

```bash
pytest tests/unit/test_spatial_metrics.py -v
```

Run integration tests:

```bash
pytest tests/integration/test_pipeline.py -v
```

## Output

- **Feasibility Report**: `data/results/data_feasibility_report.json`.
- **Processed Data**: `data/processed/` (Aligned maps, derived metrics).
- **Results**: `results/summary_report.csv` (Correlation coefficients, p-values, robustness metrics).
- **Ingestion Metrics**: `results/ingestion_metrics.json` (Global ingestion success rate as per SC-004).
- **Logs**: `logs/` (Detailed logs of masking, fitting, and exclusions).