# Quickstart: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Prerequisites

- Python 3.11+
- Git
- ≥ 7 GB RAM (for full dataset processing)
- Internet access (to download verified datasets)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline automatically detects data availability and switches modes.

### 1. Run Source Verification & Analysis
```bash
python code/main.py
```

**Expected Behavior**:

- **If a single‑source paired dataset is found**:  
  - Logs “Primary Mode: Data verified. Proceeding to preprocessing.”  
  - Generates `output/verified_source_manifest.json` (`paired_found: true`).  
  - Runs Power Analysis (Phase 1) with **21 predictors**.  
  - If `N` ≥ required minimum, proceeds through preprocessing, feature extraction, **dimensionality reduction (Phase 6)**, modeling, validation, and attempts the Independent Dataset Check (Phase 10).  
  - **Note**: If `N < 30`, permutation testing is skipped. If no independent dataset is found, the pipeline logs "Skipped: No independent dataset found" and flags generalizability as "Unverified".  
  - Outputs `output/results.json`, `output/pre-registration.json`, and associated logs.  

- **If NO single‑source paired dataset is found** (current state):  
  - Logs “Data Insufficient Mode: No single‑source paired dataset found.”  
  - Generates `output/verified_source_manifest.json` with `paired_found: false` and a reason field.  
  - **Halts** all statistical modeling steps.  
  - Exit code 0 (validation succeeded, no analysis performed).

- **If the dataset is found but underpowered**:  
  - Logs “Underpowered: Minimum N required = X, actual N = Y.”  
  - Skips modeling, still produces `pre-registration.json` and `verified_source_manifest.json`.

- **If the dataset is sufficient but N < 30**:  
  - Logs “Insufficient subjects for reliable permutation testing; skipping permutation and KS validation.”  
  - Modeling proceeds, but validation reports the limitation.

### 2. Verify Outputs
```bash
cat output/verified_source_manifest.json
cat output/pre-registration.json
```

### 3. (Optional) Provide a Custom Paired Dataset
1. Place raw EEG and tDCS files under `data/raw/`.  
2. Update `code/config.py` to point to the local paths.  
3. Re‑run `python code/main.py`.

## Troubleshooting

- **Memory Error**: The system automatically downsamples epochs or reduces the number of retained PCA components. If the error persists, lower `MAX_EPOCHS` in `config.py`.  
- **Missing Independent Dataset**: If Phase 10 cannot locate a second paired dataset, the pipeline logs “Skipped: No independent dataset found” and flags the result as "Generalizability: Unverified" (satisfying Constitution Principle VII).  
- **Permutation Skipped**: For datasets with `N < 30`, permutation testing is omitted; the final report will note this limitation.