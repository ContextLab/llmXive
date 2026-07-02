# Quickstart: Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

## 1. Prerequisites

- **Python**: 3.11 or higher.
- **Dependencies**: `numpy`, `scipy`, `astropy`, `healpy`, `camb`, `nbodykit`, `fitsio`, `requests`, `pytest`.
- **Hardware**: CPU-only environment (+ cores, 7GB+ RAM).
- **Disk Space**: ≥ 14 GB available.

## 2. Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-036-exploring-the-impact-of-cosmic-microwave
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Running the Pipeline

The pipeline is executed in stages. Each stage can be run independently for testing.

### Step 1: Download and Validate CMB Data
```bash
python code/01_data_download.py
```
- Downloads Planck PR3 maps from the archive.
- Validates checksums.
- Outputs: `data/raw/planck_map.fits`

### Step 2: Generate Power Spectra
```bash
python code/02_power_spectrum.py
```
- Calculates standard and anomaly-modified power spectra (Phase-Injected).
- Outputs: `data/derived/power_spectrum.npy`, `data/derived/anomaly_spectrum.npy`

### Step 3: Generate Initial Conditions
```bash
python code/03_initial_conditions.py
```
- Creates IC files for both control and anomaly runs.
- Outputs: `data/derived/ic_control.ic`, `data/derived/ic_anomaly.ic`

### Step 4: Run Simulations
```bash
python code/04_simulation_runner.py
```
- Executes paired N-body simulations with high-resolution grids (high comoving volume).
- **Note**: This step may take up to 12 hours.
- Outputs: `data/derived/snapshot_control.0`, `data/derived/snapshot_anomaly.0`

### Step 5: Extract Statistics & Run Tests
```bash
python code/05_statistics.py
```
- Extracts matter power spectrum and void distributions.
- Performs KS and Chi-squared tests (Diagnostic).
- Outputs: `data/results/statistical_results.json`

### Step 6: Versioning & State Update
```bash
python code/utils/versioning.py --update-state
```
- Calculates SHA256 hashes for all artifacts.
- Writes hashes to `state/projects/.../artifact_hashes.yaml`.
- **Note**: This step is mandatory for CI compliance (Constitution Principle V).

### Step 7: Verification & Accuracy Gate
```bash
python code/utils/validate_citations.py
```
- Validates all URLs in `research.md` against the verified datasets block.
- **Note**: This step is mandatory for CI compliance (Constitution Principle II).

### Step 8: Visualization (Optional)
```bash
python code/06_visualization.py
```
- Generates plots of power spectra and void distributions.
- Outputs: `data/results/plots/`

## 4. Verification

To verify the pipeline:
```bash
pytest tests/
```
This runs unit tests for data validation, power spectrum generation, and statistical analysis.

## 5. Troubleshooting

- **Memory Error**: If the simulation runs out of memory, reduce the particle count in `config/anomaly.yaml` and re-run.
- **Checksum Mismatch**: If the download fails validation, check your network connection and retry.
- **Runtime Exceeded**: If the simulation exceeds 12 hours, the job will be terminated by GitHub Actions. Consider reducing the box size or particle count.
- **Versioning Error**: If the versioning step fails, check that `state/` directory exists and is writable.
- **Citation Error**: If the citation validation fails, check that all URLs in `research.md` are present in the "# Verified datasets" block.