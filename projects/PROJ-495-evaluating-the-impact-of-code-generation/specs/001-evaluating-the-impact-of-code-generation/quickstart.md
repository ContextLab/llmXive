# Quickstart: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Prerequisites
- Python 3.11 installed.
- Docker installed (required for SonarQube Community Edition).
- Sufficient free disk space for streaming datasets (no large pre‑download needed).
- No GPU required.

## Setup
```bash
cd code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Start SonarQube (required for FR‑002)
```bash
# Pull the official SonarQube image (a sizable Docker image) and run it in the background.
docker pull sonarqube:latest
docker run -d --name sonarqube -p 9000:9000 sonarqube:latest
# Wait a few seconds for the server to become healthy.
sleep 10
```

## Smoke Run (50‑file subset) – validates US‑1
```bash
python -m src.pipeline --smoke 50
```
What to check:
- `data/derived/file_manifest.csv` contains a substantial number of entries.
- `per_file_analysis.csv` has valid `vulnerability_count`, `corrected_vulnerability_count`, and CWE IDs for each file.
- No unhandled exceptions; runtime ≤ 5 min.

## Full Run
```bash
python -m src.pipeline
```
Executes all phases in order:
1. Downloads corpora (or aborts with a clear data‑availability error).  
2. Runs Bandit, **and SonarQube** (via Docker), writes `findings.csv` and `per_file_analysis.csv`.  
3. Computes raw and audit‑adjusted densities → `group_summary.csv`.  
4. Performs power analysis, over‑dispersion check, NB (or Poisson) regression & Mann‑Whitney U, applies Holm‑Bonferroni correction → `statistical_tests.csv`.  
5. Generates audit sample (`audit_sample.csv`).  
6. Produces figures (`results/figures/density_boxplot.*`, `cwe_distribution.*`).  

### Manual Audit (FR‑007)
1. Open `data/derived/audit_sample.csv` and fill the `verdict` column.  
2. Run:
```bash
python -m src.audit --compute-metrics
```
Outputs `results/tables/audit_metrics.csv` with precision, recall, and FPR per group.

## Tests
```bash
cd code && pytest
```
Includes:
- Unit tests for each module.  
- Contract validation against `specs/001-evaluating-the-impact-of-code-generation/contracts/*.schema.yaml`.  
- Synthetic data tests confirming that the NB regression returns a known p‑value within 0.001 (US‑3) and that density calculations (including audit correction) match expected values (US‑2).

## Expected Failure Mode
If **both** the CodeVulnBench LLM dataset **and** the human code subset cannot be downloaded **with verified URLs**, the pipeline exits with a non‑zero status and prints a concise error listing the attempted URLs. No synthetic data are created; the failure prompts a spec amendment to provide a verifiable open dataset.

---



