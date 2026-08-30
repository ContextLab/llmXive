# Quickstart: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

## Prerequisites

*   Python 3.11+
*   Access to the verified datasets (download links provided below).
*   No manual data entry required (thermal conductivity values are generated programmatically).

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
cd projects/PROJ-260-investigating-the-influence-of-network-s
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Data Acquisition

### Download Verified Datasets
Run the following script to download the amorphous silicon trajectories:

```bash
# Download THZ-Alencar
wget https://huggingface.co/datasets/THZERAOFC/thalysalencar/resolve/main/thalysalencar.zip -O data/raw/thalysalencar.zip
unzip data/raw/thalysalencar.zip -d data/raw/thalysalencar/

# Download THZ-Alencar021
wget https://huggingface.co/datasets/THZERAOFC/alencar021/resolve/main/alencar021.zip -O data/raw/alencar021.zip
unzip data/raw/alencar021.zip -d data/raw/alencar021/
```

### Automatic Reference Generation
**No manual CSV required.** The pipeline will automatically generate thermal conductivity reference values using the `reference_generator.py` service, which applies a validated physical model (Cahill-Pohl limit) to ensure independence and reproducibility.

## 3. Running the Pipeline

Execute the full analysis pipeline:

```bash
python -m src.cli.main run --config config/default.yaml
```

### Pipeline Steps
1.  **Topology Extraction**: Parses trajectories, computes RDF, constructs bond networks, and outputs `data/derived/topology/`.
2.  **VDOS Calculation**: Computes VACF, Fourier transforms to VDOS, and calculates participation ratios. Outputs `data/derived/vdos/`.
3.  **Reference Generation**: Programmatically generates independent $\kappa$ values with independence checks. Outputs `data/derived/reference/`.
4.  **Sensitivity Analysis**: Sweeps threshold for bottleneck density. Outputs `data/derived/sensitivity/`.
5.  **Statistical Analysis**: Aggregates metrics (N≥30 per system size), performs bootstrap correlation, and applies multiple-comparison correction. Outputs `data/derived/correlation/`.
6.  **Runtime Validation**: Measures and asserts the ≤30 minute runtime constraint (SC-005).
7.  **Versioning**: Updates project state with content hashes.

## 4. Validation & Testing

Run the test suite to ensure data integrity and statistical accuracy:

```bash
pytest tests/ -v --cov=src
```

**Key Tests**:
*   `test_topology_schema`: Validates that coordination numbers are within physical bounds.
*   `test_vdos_spectrum`: Checks for the presence of the high-frequency peak.
*   `test_correlation_accuracy`: Verifies bootstrap correlation against a manual calculation (tolerance $\le 1e-6$).
*   `test_runtime_threshold`: Asserts the full pipeline completes in ≤ 30 minutes for a 4000-atom system (SC-005).
*   `test_independence_check`: Verifies that $\kappa$ values are not derived from the same trajectory as topological metrics (FR-008).
*   `test_sensitivity_analysis`: Validates the threshold sweep logic and stability reporting.

## 5. Interpreting Results

The final report is generated in `outputs/reports/summary.html`.

*   **Correlation Coefficient**: Look for the Spearman $r$ value across N≥30 snapshots.
*   **Significance**: Check the Bonferroni-corrected p-value.
*   **Power**: If the "Low Power" warning is present, interpret results with caution.
*   **Finite-Size Effects**: Compare $r$ across system sizes (1000, 2000, 4000 atoms).

## Troubleshooting

*   **Error: "Invalid File Format"**: Check that trajectory files are valid LAMMPS dump or XYZ formats.
*   **Error: "Missing Independence"**: The system detected that the $\kappa$ source is not independent. Check logs.
*   **Warning: "Ambiguous RDF Minimum"**: The system logged a decision. Check `logs/topology.log` for the fallback cutoff used.