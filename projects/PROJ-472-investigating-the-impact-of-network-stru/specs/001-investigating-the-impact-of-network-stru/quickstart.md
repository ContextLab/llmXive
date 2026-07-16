# Quickstart Guide: Network Structure & Avalanche Dynamics

## 1. Prerequisites
- Python 3.9+
- MRtrix3 (for dMRI processing, installed separately)
- MNE-Python
- NetworkX, BCTpy, powerlaw, pandas, numpy, scipy

## 2. Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Set up environment variables (optional, defaults are in `code/config.py`):
 ```bash
 cp code/.env.example code/.env
 # Edit.env if custom paths are needed
 ```

## 3. Data Acquisition
The pipeline automatically downloads data from OpenNeuro `ds004231` upon first run.
- **Note**: Ensure sufficient disk space (~10GB+).
- **Constraint**: If `ds004231` is unreachable, the pipeline will halt with a clear error.

## 4. Running the Pipeline
Execute the main entry point:
```bash
python code/main.py
```
This will:
1. Download and verify data.
2. Preprocess dMRI and EEG.
3. Compute structural and avalanche metrics.
4. Run statistical analysis (if N >= 10).
5. Generate reports.

## 5. Output Location
- **Processed Data**: `data/processed/`
- **Results & Reports**: `data/results/`
- **Logs**: `data/logs/`

## 6. Validation
To verify the pipeline integrity:
```bash
python code/main.py --validate
```
This checks for:
- Presence of required files.
- Valid checksums.
- Correct routing state (`routing_state.json`).

## 7. Troubleshooting
- **Data Download Failed**: Check internet connection and OpenNeuro status. The pipeline does not support offline/fallback modes for the primary source.
- **Insufficient Subjects**: If fewer than 10 subjects pass QC, a `insufficient_sample_report.md` will be generated in `data/results/`.
- **Power-Law Convergence**: If fitting fails for a subject, they are excluded from the correlation matrix (logged in `fitting_report.json`).

## 8. Documentation Path
All project documentation resides in `specs/001-network-structure-avalanche-dynamics/`.
- `research.md`: Research protocol.
- `data-model.md`: Data structures.
- `quickstart.md`: This guide.
- **Deprecated**: The `docs/` directory is no longer used.