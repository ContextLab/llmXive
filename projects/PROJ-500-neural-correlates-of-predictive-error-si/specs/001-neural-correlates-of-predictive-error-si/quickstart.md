# Quickstart: Neural Correlates of Predictive Error Signals During Tactile Discrimination Learning

## Prerequisites

- Python 3.11+
- GitHub Actions runner (2-core CPU, 7 GB RAM)
- Access to HuggingFace/OpenNeuro (no API key required for public datasets)

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Verify environment:
   ```bash
   python -c "import mne; import statsmodels; print('Dependencies OK')"
   ```

## Running the Pipeline

### 1. Data Ingestion
```bash
python src/main.py --task ingest --dataset openneuro-fslr64k
```
*Downloads and validates the dataset.*

### 2. Preprocessing
```bash
python src/main.py --task preprocess --subject 001
```
*Applies 1–40 Hz filter, ICA, and epoching.*

### 3. Alignment
```bash
python src/main.py --task align --subject 001
```
*Computes MMN amplitudes and aligns with behavioral blocks.*

### 4. Statistical Analysis
```bash
python src/main.py --task model --all
```
*Fits GLMM, runs permutation test, and applies corrections.*

### 5. Robustness Check
```bash
python src/main.py --task robustness --windows "140-240,160-260"
```
*Sweeps time windows and reports coefficient variation.*

## Output Locations

- **Preprocessed Data**: `data/preprocessed/`
- **Aligned Data**: `data/aligned/`
- **Statistical Results**: `analysis/results/`
- **Logs**: `logs/pipeline.log`

## Troubleshooting

- **OOM Error**: Reduce `--chunk-size` in `ingest.py`.
- **Convergence Warning**: Check `data/aligned/` for subjects with [deferred] accuracy; they are excluded automatically.
- **Missing Metadata**: The script will log a warning and skip the dataset. Check `logs/pipeline.log` for details.
