# Quickstart: Running the Code‑Generation Security Study

## Prerequisites
1. **GitHub Actions runner** (or local Linux env with at least 2 CPU cores, ~7 GB RAM).  
2. **Python 3.11** (installed via `pyenv` or system).  
3. **Docker** (required for Semgrep & SonarQube).  
4. **Hugging Face token** (optional, only needed if you hit rate limits on the StarCoder model). Set as environment variable `HF_TOKEN`.

## Setup
```bash
# Clone the repository (assumes you are in the project root)
git clone 
cd PROJ-347-evaluating-the-impact-of-code-generation

# Create a virtualenv and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions, including transformers

# Verify Docker images are available (will be pulled automatically on first run)
docker pull returntocorp/semgrep:1.46.0
docker pull sonarqube:9.9-community
```

## Execute the Full Pipeline
```bash
# Run the orchestrator script (all steps are logged under logs/)
python -m src.run_pipeline \
    --seed 42 \
    --max-pairs 200 \
    --confidence-thresholds 0.0 0.5 0.9
```
- `--seed` fixes all randomness.  
- `--max-pairs` caps the number of paired samples (default set according to the power analysis).  
- `--confidence-thresholds` triggers the sensitivity sweep.

The script performs:
1. Data download & LLM generation (Phase 0) using the **StarCoder** model.  
2. Syntax & functional checks.  
3. Static analysis with Semgrep & SonarQube (Phase 1).  
4. Aggregation, paired statistical testing, and sensitivity analysis (Phase 2).  
5. Random audit of **[deferred]** flagged findings (Phase 3).
6. Report generation (`reports/report.md`) and figure export (`reports/figures/`).

## Inspect Results
- **Aggregated counts**: `data/outputs/vuln_counts.csv`  
- **Statistical table**: `data/outputs/analysis_results.csv`  
- **Sensitivity sweep**: `data/outputs/sensitivity.csv`  
- **Final report**: `reports/report.md` (open in any markdown viewer).  

## Re‑running / CI Integration
The same command can be placed in a GitHub Actions workflow (`.github/workflows/research.yml`). The workflow automatically enforces the A timeout of appropriate duration (e.g., on the order of hours) and a RAM limit.; failures will be reported as CI errors.

---

