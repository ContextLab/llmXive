# Quickstart: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face datasets (no token required for public datasets)
- Sufficient disk space for temporary files and processed data

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-1030-llmxive-follow-up-extending-scaling-mixt
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Download and Prepare Data
```bash
python code/cli/run_pipeline.py --step download
```
This step downloads the RoboNet/Ego4D dataset subsets and stores them in `data/raw`.

### 2. Visual Fidelity Check
```bash
python code/cli/run_pipeline.py --step fidelity
```
This step filters clips based on texture score to ensure depth estimation feasibility.

### 3. Extract Features
```bash
python code/cli/run_pipeline.py --step extract
```
This step extracts latent vectors and expert masks from the LingBot-Video model and saves them to `data/processed/features.npy`.

### 4. Generate Labels
```bash
python code/cli/run_pipeline.py --step label
```
This step reconstructs 3D states, applies synthetic perturbations, and generates labels in `data/processed/labels.csv`.

### 5. Prior Audit
```bash
python code/cli/run_pipeline.py --step audit
```
This step runs `prior_audit.py` to verify label independence and saves the report to `data/processed/audit_report.json`.

### 6. Train and Evaluate Classifier
```bash
python code/cli/run_pipeline.py --step train
```
This step trains a lightweight classifier and evaluates it on a held-out test set, outputting metrics to `data/processed/metrics.json`.

### 7. Verify Results
```bash
python code/cli/run_pipeline.py --step verify
```
This step runs the `prior_audit.py` script to verify label independence and checks data hygiene.

## Troubleshooting

- **Memory Error**: If you encounter OOM errors, reduce the batch size or increase frame subsampling in `code/config.py`.
- **Depth Estimation Failure**: Check `data/processed/excluded_samples.log` for samples with low confidence.
- **Physics Simulation Crash**: Ensure the PyBullet environment is correctly configured and check logs for specific error messages.
- **Visual Fidelity Failure**: Check `data/processed/fidelity_log.json` for clips that failed the texture score check.

## Output

- **features.npy**: Extracted activation patterns.
- **labels.csv**: Ground-truth physical validity labels.
- **metrics.json**: Evaluation metrics (F1, precision, recall).
- **excluded_samples.log**: Log of filtered samples.
- **audit_report.json**: Prior audit results.
- **memory_log.json**: Peak RAM usage log.
- **filtering_report.json**: Count of filtered vs. retained samples.