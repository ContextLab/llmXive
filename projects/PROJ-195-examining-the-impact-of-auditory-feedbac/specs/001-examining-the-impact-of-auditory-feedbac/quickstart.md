# Quickstart: Examining the Impact of Auditory Feedback on Motor Sequence Learning

## Prerequisites

- Python 3.10+
- Docker (for `fmriprep`)
- Git
- Sufficient disk space for raw and processed data of a subset

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-195-examining-the-impact-of-auditory-feedbac
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

## Running the Pipeline

The pipeline is executed in stages. You can run the full pipeline or individual stages.

### 1. Download Data
```bash
python code/download_data.py --dataset ds000115 --output data/raw/
```
*Note: This may take time and requires internet access.*

### 2. Preprocess with fmriprep
```bash
# Ensure Docker is running
bash code/run_fmriprep.sh data/raw/ds000115 data/processed/
```
*Note: This step is computationally intensive. It will process a subset of subjects to fit the time limit.*

### 3. Fit GLMs
```bash
python code/preprocess_glms.py --input data/processed/ --output data/processed/
```

### 4. Group Analysis
```bash
python code/group_analysis.py --input data/processed/ --output data/processed/
```

### 5. Brain-Behavior Correlation & Visualization
```bash
python code/brain_behavior.py --input data/processed/ --output data/processed/
```

### 6. Power Analysis
```bash
python code/power_analysis.py --input data/processed/ --output data/processed/
```

## Output

- **Statistical Maps**: `data/processed/group_stats/`
- **Visualizations**: `data/processed/plots/` (PNG/PDF)
- **Reports**: `data/processed/report.md`

## Troubleshooting

- **Docker errors**: Ensure Docker daemon is running and user has permissions.
- **Out of Memory**: Reduce the number of subjects processed in `run_fmriprep.sh`.
- **Network errors**: Retry the download step; ensure firewall allows OpenNeuro access.
