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

## A‑priori Power Planning (optional, runs automatically)
The pipeline will automatically compute the required sample size for a target rate ratio of 1.10, power = 0.80, α = 0.05. If the downloaded datasets cannot meet this requirement, the run aborts with a clear message.

## Smoke Run (US‑1 validation) – processes a small subset
```bash
python -m src.pipeline --smoke <representative count>
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
1. **A‑priori Power Planning** – ensures sufficient sample size before any download.  
2. **Data Ingestion** – streams the **VulnCodeRepo** (LLM‑generated) and **Juliet JavaScript** (human‑written) datasets, verifies checksums, and aborts if they do not match the verified values. No proxy data are used beyond the documented substitute.  
3. **Static analysis** – runs Bandit, Semgrep, and SonarQube (Docker).  
4. **Deduplication**, **complexity**, **density**, **audit‑adjusted counts** (both FP and FN corrections, rounding to integer).  
5. **Statistical tests** – power analysis, over‑dispersion check, NB regression (or Poisson fallback), Mann‑Whitney U, Benjamini‑Hochberg correction.  
6. **Audit sample** generation (`audit_sample.csv`). Findings in this sample are **excluded** from the regression dataset.  
7. **Bias Assessment** – compares detection rates per language and reports any systematic differences; also computes the FPR disparity between LLM and human groups (SC‑008).  
8. **Figures** – boxplot and CWE bar chart saved under `results/figures/`.  
9. **Aggregate results** – merges `group_summary.csv` and `statistical_tests.csv` into `aggregate_results.yaml` (validated against the schema).  

### Manual Audit (FR‑007)
1. Open `data/derived/audit_sample.csv` and fill the `verdict` column (`true_positive` / `false_positive`).  
2. Run:
```bash
python -m src.audit --compute-metrics
```
Outputs `results/tables/audit_metrics.csv` with precision, recall, **tool‑specific** false‑positive rates, **false‑negative** rates (recall), and adjusted vulnerability counts.

## Tests
```bash
cd code && pytest
```
Tests include:
- Unit tests for each module.  
- Contract validation against the three YAML schemas in `specs/001-evaluating-the-impact-of-code-generation/contracts/`.  
- Synthetic data checks confirming that the NB regression returns a known p‑value within 0.001 of the expected value (US‑3) and that density calculations (including audit correction and rounding) match expected values (US‑2).

## Expected Failure Mode
If **either** the VulnCodeRepo or the Juliet JavaScript dataset cannot be downloaded or fails checksum verification, the pipeline aborts early with a clear error message stating the missing or mismatched source. No synthetic data are generated; the failure indicates that a spec amendment is required to provide a verifiable open dataset before the primary hypothesis test can be performed.

---

