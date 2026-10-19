# Quickstart: Neuro‑Symbolic Learning Networks

## Prerequisites
- Python 3.11+
- R 4.3+ (optional, for `lme4` via `rpy2`)
- Git
- Internet access (to download ASSISTments dataset)

## Installation
```bash
# Clone repository
git clone <repo-url>
cd projects/PROJ-559-neuro-symbolic-learning-networks-bridgin

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r code/requirements.txt
```

## Configuration (`code/config.yaml`)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `random_seed` | Fixed seed for reproducibility | 42 |
| `dataset_urls.assistments` | Verified ASSISTments CSV URL | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv |
| `dataset_urls.khan` | Optional Khan Academy URL (may be empty) | "" |
| `simulation_size_per_condition` | Number of simulated students | 2000 |
| `download_timeout_seconds` | Dataset download timeout | 300 |
| `explanation_timeout_seconds` | Generation timeout per problem | 180 |

## Running the Full Pipeline

### 0. Citation Validation (CI Gate)
```bash
python code/tools/reference_validator.py --threshold 0.8
```
Fails with exit 1 if any external URL does not meet the `CITATION_TITLE_OVERLAP_THRESHOLD`.

### 1. Download & Prepare Data
```bash
python code/data/download_assistments.py
python code/data/download_khan.py   # optional; will log and continue if fails
python code/data/unify_datasets.py
python code/data/validate_schema.py
```
*Outputs*: `data/raw/assistments.csv`, optional `khan_academy.csv`, `data/processed/unified_problems.csv`.

### 2. Human Pilot Collection (Manual)
1. Deploy a short survey (Google Forms / Qualtrics) collecting correctness, response time, and 1‑5 comprehension rating for ≥ 50 participants across the three conditions.  
2. Save as `data/pilot/real_pilot_data.csv` and run:
```bash
python code/simulation/pilot_calibrator.py
```
If the file is missing after 48 h, the pipeline will automatically switch to **Feasibility Mode** (no calibration, simulation only).

### 3. Generate Explanations
```bash
python code/generation/batch_generate.py \
  --conditions neural,symbolic,neuro_symbolic \
  --timeout ${explanation_timeout_seconds}
```
Creates `data/traces/explanation_<condition>_<problem_id>.txt` and corresponding JSON metadata.

### 4. Run Simulation
```bash
python code/simulation/run_simulation.py
```
Produces `data/processed/interaction_logs_simulated.csv`.

### 5. Real‑Student Data Collection (Manual)
Collect ≥ 200 participants, store as `data/processed/real_student_data.csv`.

### 6. Merge & Analyze
```bash
bash code/analysis/run_analysis.sh
```
The script merges simulated + real logs, fits the mixed‑effects model, applies Holm‑Bonferroni correction, computes Cohen’s d, and writes:
- `results/analysis_output.yaml` (validated against `contracts/analysis_output.schema.yaml`)
- `results/report.md` (human‑readable summary)

### 7. CI Resource Summary
During execution, `code/tools/resource_monitor.py` logs peak CPU and RAM. The CI job will fail if limits exceed 2 cores or 7 GB (SC‑006).

## Verification Checklist
- **[ ]** `data/raw/assistments.csv` & checksum exist.  
- **[ ]** `data/raw/khan_academy.csv` optional; if missing, log appears.  
- **[ ]** `data/processed/unified_problems.csv` passes schema validation.  
- **[ ]** Three explanation files per problem (`*_neural.txt`, `*_symbolic.txt`, `*_neuro_symbolic.txt`).  
- **[ ]** `data/pilot/real_pilot_data.csv` present (or pipeline in Feasibility Mode).  
- **[ ]** `data/processed/interaction_logs_simulated.csv` contains ≥ 2 000 rows per condition.  
- **[ ]** `data/processed/real_student_data.csv` ≥ 200 rows.  
- **[ ]** `results/analysis_output.yaml` conforms to schema and includes CI‑reported metrics.  

## Troubleshooting
- **Download timeout**: Increase `download_timeout_seconds` in `config.yaml` or check network.  
- **Out‑of‑memory**: Reduce `simulation_size_per_condition` or enable streaming (`datasets.load_dataset(..., streaming=True)`).  
- **LLM OOM**: Ensure `bitsandbytes` 4‑bit quantization is enabled; if still fails, the pipeline will automatically re‑run on Kaggle GPU.  
- **Schema validation errors**: Inspect `logs/validate_schema.log` for offending rows.  
- **Citation validation failure**: Verify URLs in `spec.md` match the verified block; correct any typos.  

---
