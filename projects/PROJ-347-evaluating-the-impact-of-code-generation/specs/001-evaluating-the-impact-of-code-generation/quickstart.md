# Quickstart: Running the Code‑Generation Security Study

## Prerequisites
1. **GitHub Actions runner** (or local Linux environment with ≥ 2 CPU cores, ~7 GB RAM).  
2. **Python 3.11**.  
3. **Docker** (required for Semgrep & SonarQube).  
4. **Hugging Face token** (optional; set `HF_TOKEN` if you encounter rate limits).

## Setup
```bash
# Clone the repository
git clone <repo-url>
cd PROJ-347-evaluating-the-impact-of-code-generation

# Create a virtual environment and install exact dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins all versions
# Pull required Docker images (first run will download them)
docker pull returntocorp/semgrep:1.46.0
docker pull sonarqube:9.9-community
```

## Run the Full Pipeline
```bash
python -m src.run_pipeline \
    --seed 42 \
    --max-pairs 300 \
    --confidence-thresholds 0.0 0.5 0.9
```
- `--seed` fixes all randomness for reproducibility.  
- `--max-pairs` caps the number of paired samples (default aligns with the power analysis).  
- `--confidence-thresholds` triggers the sensitivity sweep.

The orchestrator performs the following phases automatically:
1. **Data download & LLM generation** (Phase 0).  
2. **Syntax & functional equivalence checks**.  
3. **Static analysis** with Semgrep & SonarQube (Phase 1).  
4. **Aggregation, bias‑correction, and paired statistical testing** (Phase 2).  
5. **Sensitivity analysis** across confidence cutoffs.  
6. **Random audit of ≥ 20 % flagged findings** (Phase 3).  
7. **Report generation** (`reports/report.md`) and figure export (`reports/figures/`).  

All logs are written to `logs/`; intermediate artefacts follow the schema contracts under `contracts/`.

## Inspect Results
- **Aggregated counts**: `data/outputs/vuln_counts.csv`  
- **Statistical table**: `data/outputs/analysis_results.csv`  
- **Sensitivity sweep**: `data/outputs/sensitivity.csv`  
- **Audit log**: `data/outputs/audit_log.csv`  
- **Final report**: `reports/report.md` (open with any markdown viewer).  

## CI Integration
Add the following workflow file (`.github/workflows/research.yml`):
```yaml
name: Research Pipeline
on: [push, pull_request]
jobs:
  run-study:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt
      - name: Pull Docker images
        run: |
          docker pull returntocorp/semgrep:1.46.0
          docker pull sonarqube:9.9-community
      - name: Run pipeline
        run: |
          source .venv/bin/activate
          python -m src.run_pipeline --seed 42 --max-pairs 300 --confidence-thresholds 0.0 0.5 0.9
      - name: Verify RAM & Time limits
        run: python -m src.check_limits   # asserts ≤6 GB RAM, ≤6 h total
```
The CI will fail if any of the Constitution checks or Success Criteria are violated.

---
