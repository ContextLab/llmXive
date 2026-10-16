# Quickstart: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Prerequisites
- Python 3.11 installed.
- Docker installed (required for SonarQube Community Edition).
- At least 10 GB of free disk space (datasets are streamed; no full download required).
- No GPU required.

## Setup
```bash
cd code
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Additional tool for complexity proxy
pip install radon
```

## Start SonarQube (required for FR‑002)
```bash
# Pull the official SonarQube image and run it in the background.
docker pull sonarqube:latest
docker run -d --name sonarqube -p 9000:9000 sonarqube:latest
# Wait a few seconds for the server to become healthy.
sleep 15
```

## Smoke Run (US‑1 validation) – processes a small subset
```bash
python -m src.pipeline --smoke 50
```
**What to check**
- `data/derived/file_manifest.csv` lists ≥ 45 entries (≥ 90 % of the subset).  
- `per_file_analysis.csv` contains non‑negative `vulnerability_count` and a defined `density` (or `"undefined"` for zero‑LOC files).  
- No unhandled exceptions; total runtime ≤ 5 min.

## Full Run
```bash
python -m src.pipeline
```
The pipeline executes all phases in order:
1. **Ingest** – attempts to download the **CodeVulnBench** (LLM‑generated) and **Juliet Test Suite** (human‑written) datasets. If either dataset is missing or its checksum cannot be verified, the pipeline aborts with a clear error message and stops. No proxy data are used.
2. **Static analysis** – runs Bandit, Semgrep, and SonarQube (Docker).  
3. **Deduplication**, **complexity**, **density**, **audit‑adjusted counts**.  
4. **Statistical tests** – power analysis, over‑dispersion check, NB regression (or Poisson fallback), Mann‑Whitney U, Benjamini‑Hochberg correction.  
5. **Audit sample** generation (`audit_sample.csv`). Findings in this sample are **excluded** from the regression dataset.  
6. **Figures** – boxplot and CWE bar chart saved under `results/figures/`.  

### Manual Audit (FR‑007)
1. Open `data/derived/audit_sample.csv` and fill the `verdict` column (`true_positive` / `false_positive`).  
2. Run:
```bash
python -m src.audit --compute-metrics
```
Outputs `results/tables/audit_metrics.csv` with precision, recall, and **tool‑specific** false‑positive rates, plus group‑level FPRs.

## Tests
```bash
cd code && pytest
```
Tests include:
- Unit tests for each module.  
- Contract validation against the three YAML schemas in `specs/001-evaluating-the-impact-of-code-generation/contracts/`.  
- Synthetic data checks confirming that the NB regression returns a known p‑value within 0.001 of the expected value (US‑3) and that density calculations (including audit correction) match expected values (US‑2).

## Expected Failure Mode
If **both** the CodeVulnBench and Juliet datasets remain unavailable (no verified URLs), the pipeline aborts early with a clear error message stating the missing sources. No synthetic data are generated; the failure indicates that a spec amendment is required to provide a verifiable open dataset before the primary hypothesis test can be performed.

---

