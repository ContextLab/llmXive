# Quickstart: Auditing Public A/B Test Summaries  

## Prerequisites
- Python 3.11 installed (or use the provided Docker image).  
- Git installed.  
- Internet access to download the target URLs.  

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/ab-audit.git
cd ab-audit
```

## 2. Set Up the Environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 3. Prepare the Input CSV
Create `data/raw_urls.csv` with a single column `url`:

```csv
url
https://example.com/blog/experiment-1
https://another.com/ab-test/2023
...
```

## 4. Run the Full Pipeline Locally
```bash
python -m audit.run \
    --url-csv data/raw_urls.csv \
    --output-dir outputs \
    --synthetic-size <chosen size>   # generates synthetic validation set with realistic quirks
```
The command performs all phases (ingest → dashboard).  

### Expected Outputs
| File | Description |
|------|-------------|
| `outputs/audit_report.json` | JSON array of `AuditRecord` objects. |
| `outputs/dashboard.html` | Interactive HTML dashboard (see SC‑010). |
| `outputs/checksums.txt` | MD5 checksums for reproducibility (SC‑004, SC‑009). |
| `outputs/manifest.json` | SHA‑256 hashes for **all** output artifacts (supports Principle V). |
| `data/synthetic_validation.csv` | Ground‑truth validation set (used for precision/recall). |

## 5. Verify Resource Limits (CI Check)
The script prints a summary:

```
Runtime: a few hours.
CPU cores used: a limited number of cores
Peak RAM: on the order of a few gigabytes.
Parsing error rate: low (to be quantified in the implementation phase)
Achieved power for overall inconsistency test: high (sufficient to detect the effect of interest)
```
All values must satisfy **SC‑008**, **SC‑005**, and the power threshold (≥ 0.80) for a well‑powered study.

## 6. Run the Reproducibility Package (Docker)
```bash
docker build -t ab-audit:latest .
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/outputs:/app/outputs ab-audit:latest \
    python -m audit.run --url-csv data/raw_urls.csv --output-dir outputs
```
After the run, compare MD5 checksums with `outputs/checksums.txt` **and** verify that the SHA‑256 hashes in `outputs/manifest.json` match the recorded values to confirm exact reproducibility (SC‑004, SC‑009).

## 7. CI Execution (GitHub Actions)
The repository includes `.github/workflows/ci.yml`. To trigger:

```bash
git add data/raw_urls.csv
git commit -m "Trigger CI audit"
git push
```

Watch the Actions tab; the job must finish within 6 h, stay under the CPU/RAM caps, and report the parsing‑error rate ≤ 5 % (SC‑005).  

---

