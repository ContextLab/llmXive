# Quickstart: Auditing Public A/B Test Summaries

This guide walks you through a fresh clone of the repository to run the full audit pipeline on a sample corpus of URLs.

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/ab-test-audit.git
cd ab-test-audit
```

## 2. Build the Docker Image (CPU‑only)
```bash
docker build -t ab-audit:latest .
```
*The Dockerfile pins Python 3.11 and all library versions (see `requirements.txt`).*

## 3. Prepare Input URLs
Create a CSV file `input/urls.csv` with a header `url` and at least 300 reachable URLs:

```csv
url
https://example.com/blog/ab-test-1
https://example.org/engineering/experiment-42
...
```

## 4. Run the Audit Pipeline
```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/data:/app/data" \
  ab-audit:latest \
  python -m src.audit.cli input/urls.csv output/
```
The CLI performs the following steps automatically:

1. **Deduplication** (FR‑017)  
2. **HTML download & extraction** (FR‑001, FR‑002, FR‑007)  
3. **Statistical reconstruction** (FR‑003)  
4. **Consistency checks** (FR‑004) & **sensitivity analysis** (FR‑004a)  
5. **Synthetic validation dataset generation** (FR‑008) – saved under `data/synthetic/`  
6. **Dashboard generation** (`output/dashboard.html`, FR‑010)  
7. **Manifest creation** (`output/manifest.json`, FR‑014)  

## 5. Verify Resource Usage (SC‑008)
After the run finishes, inspect `output/resource_log.json` which contains:

```json
{
  "cpu_time_seconds": 11234,
  "max_memory_gb": 6.3,
  "wall_time_seconds": 11500
}
```
All values must respect the limits (≤ 2 CPU cores, ≤ 7 GB RAM, ≤ 6 h).

## 6. Check Reproducibility (SC‑004, SC‑009)
```bash
md5sum output/audit_report.json output/dashboard.html
cat output/manifest.json   # contains SHA‑256 hashes of the above files
```
The MD5 sums should match the values recorded in `manifest.json`.

## 7. View the Dashboard
Open `output/dashboard.html` in any browser. It displays:

- Overall inconsistency rate  
- Source‑wise bar chart  
- Monthly trend line chart  
- Binomial test p‑value and Wilson 95 % CI (FR‑005a)  

## 8. Run Contract Tests (optional)
```bash
docker run --rm -v "$(pwd):/app" ab-audit:latest pytest -m contract
```
All schema validations must pass (SC‑015).

## 9. CI Execution (for developers)
Push a branch to GitHub; the workflow `.github/workflows/audit.yml` will automatically run the pipeline on the GitHub Actions free‑tier runner and enforce the resource caps.

---
