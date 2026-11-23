# Quickstart: Neuro‑Symbolic Learning Networks

## Prerequisites
- Python 3.11+  
- R 4.3+ (optional, for `lme4` via `rpy2`)  
- Git  
- Internet access (to download ASSISTments dataset; Khan Academy dataset must be publicly reachable)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-559-neuro-symbolic-learning-networks-bridgin

# Set up virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration (`code/config.yaml`)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `random_seed` | Fixed seed for reproducibility | 42 |
| `dataset_urls.assistments` | Verified ASSISTments CSV URL | https://huggingface.co/datasets/OloriBern/assistments-dataset/resolve/main/skill_builder_data_corrected.csv |
| `dataset_urls.khan` | Optional Khan Academy URL (must be publicly reachable) | "" |
| `simulation_size_per_condition` | Number of simulated students per condition | 2000 |
| `download_timeout_seconds` | Dataset download timeout | 300 |
| `explanation_timeout_seconds` | Generation timeout per problem (seconds) | 180 |

## Running the Full Pipeline

### 0. Citation Validation (CI Gate)
```bash
python code/tools/reference_validator.py --threshold 0.8
```
Exits 1 if any external URL fails the 0.8 title‑overlap check.

### 1. Download & Prepare Data
```bash
python code/data/download_assistments.py
python code/data/download_khan.py   # **MANDATORY**: aborts if no verified URL or timeout
python code/data/unify_datasets.py
python code/data/validate_schema.py
```
*Outputs*: `data/raw/assistments.csv`, `data/raw/khan_academy.csv`, `data/processed/unified_problems.csv`.

### 2. Human Pilot Collection (Manual)
1. Run a short survey (e.g., Google Forms) collecting correctness, response time, and 1‑5 Likert rating for ≥ 50 participants across the three conditions.  
2. Save as `data/pilot/real_pilot_data.csv`.  
3. Validate the pilot CSV:
```bash
python code/tools/validate_pilot.py   # checks against contracts/pilot_data.schema.yaml
```
4. Calibrate the BKT simulator:
```bash
python code/simulation/pilot_calibrator.py
```
If calibration fails (RMSE > 0.15, diff > 0.02, or TOST p < 0.10) the pipeline aborts.

### 3. Generate Explanations
```bash
python code/generation/batch_generate.py \
  --conditions neural symbolic neuro_symbolic \
  --timeout $(python -c "import yaml,sys; print(yaml.safe_load(open('code/config.yaml'))['explanation_timeout_seconds'])")
```
*Key points*:
- Generates `explanation_<condition>_<problem_id>.txt` in `data/traces/`.  
- Writes accompanying JSON metadata and **validates each file against `contracts/explanation.schema.yaml`**.  
- Logs generation success rate; CI will **fail if < 95 %** of problems lack all three explanations (SC‑001).  
- Explanation‑generation timeouts are counted; must stay ≤ 2 % (SC‑010).

### 4. API Delivery to Simulator (FR‑003)
```bash
python code/simulation/present_to_simulator.py
```
Calls the deterministic `simulator.run_explanation()` for each explanation, ensuring a reproducible mapping between problem, condition, and simulator invocation.

### 5. Simulation Run
```bash
python code/simulation/run_simulation.py
```
*What happens*:
- For each problem‑explanation pair the script loads the explanation file and calls the deterministic API (Phase 4).  
- Simulates **≥ 2 000** students per condition (FR‑009).  
- Logs `correct`, `rt_seconds` (0.1 s precision), `comprehension_rating` (1‑5), `prior_knowledge_score`, and `difficulty`.  
- **Validates the resulting `interaction_logs_simulated.csv` against `contracts/interaction_log.schema.yaml` and `contracts/simulation_log.schema.yaml`; CI fails on violations** (plan‑consistency‑d2c59896).  
- **SC‑005 checks**: ≥ 99 % of logs contain all required fields; response‑time histogram has no > 5 s gaps (≤ 2 consecutive empty bins). Violations are reported in CI summary.  

### 6. Real‑Student Data Collection (Manual)
Collect ≥ 200 participants across the three explanation conditions; store as `data/processed/real_student_data.csv`.  
Validate the CSV:
```bash
python code/tools/validate_interactions.py   # checks against contracts/interaction_log.schema.yaml
```

### 7. Merge & Exploratory Diagnostics
```bash
python code/analysis/merge_data.py   # creates merged_interaction_logs.csv (adds data_source)
python code/analysis/exploratory_regression.py   # runs mixed‑effects model on combined data for diagnostics only
```
*Outputs*: diagnostics report (effect sizes, CI widths, `data_source` effect) — **not used for primary inference**.

### 8. Primary Mixed‑Effects Regression (Real‑Only)
```bash
python code/analysis/regression_analysis.py
```
*Features*:
- Fixed effects: `condition`, `prior_knowledge_score`, `difficulty`.  
- Random intercepts: `problem_id`, `student_id`.  
- **No `data_source` fixed effect** (avoids confounding).  
- Holm‑Bonferroni correction for three pairwise condition contrasts.  
- Cohen’s d with 95 % CI for each contrast (SC‑003).  
- **Aborts if total interaction records < 5 000** (SC‑002).  
- Outputs `results/analysis_output.yaml` (validated against `contracts/analysis_output.schema.yaml`) and a human‑readable `results/report.md`.

### 9. Reporting & CI Summary
`analysis/report_generator.py` produces `results/report.md` containing:
- Primary regression table and effect sizes (real‑only).  
- Exploratory diagnostics summary (combined).  
- Calibration statistics (RMSE, TOST).  
- SC‑001, SC‑005, SC‑009‑SC‑012 metric summaries; resource usage (peak CPU ≤ 2 cores, RAM ≤ 7 GB) (SC‑006).  
- Any **scope‑limitation note** if the Khan dataset could not be downloaded.

## Verification Checklist
- [ ] `data/raw/assistments.csv` and checksum exist.  
- [ ] `data/raw/khan_academy.csv` exists; otherwise pipeline aborts with clear error (FR‑001).  
- [ ] `data/processed/unified_problems.csv` passes schema validation.  
- [ ] Three explanation files per problem (`*_neural.txt`, `*_symbolic.txt`, `*_neuro_symbolic.txt`).  
- [ ] Explanation metadata validated against `contracts/explanation.schema.yaml`.  
- [ ] Generation success ≥ 95 % (SC‑001).  
- [ ] Pilot CSV validated (SC‑007).  
- [ ] Simulation logs validated and ≥ 99 % complete (SC‑005).  
- [ ] Real‑student CSV validated (SC‑007).  
- [ ] Primary regression runs on ≥ 200 real records; exploratory diagnostics run on ≥ 5 000 combined records (SC‑002).  
- [ ] `results/analysis_output.yaml` conforms to schema and includes CI‑reported metrics.  

## Troubleshooting
- **Dataset download timeout**: Increase `download_timeout_seconds` in `config.yaml` or verify network connectivity.  
- **LLM OOM**: Ensure `bitsandbytes` 4‑bit quantization is enabled; if still OOM, the script will automatically off‑load to a Kaggle GPU.  
- **Schema validation errors**: Review the corresponding log (e.g., `validate_schema.log`) for offending rows and correct the source CSV.  
- **Citation validation failure**: Verify that all external URLs match the verified‑datasets block exactly; correct any typos.  
- **Resource limit breach**: Reduce `simulation_size_per_condition` or enable streaming for larger CSVs.  

---


