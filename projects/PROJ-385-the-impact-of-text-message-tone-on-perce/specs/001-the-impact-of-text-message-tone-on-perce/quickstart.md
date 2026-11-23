# Quickstart: Running the Text‑Tone Emotional Support Pipeline

These instructions assume a fresh GitHub Actions runner (or a local Linux environment with ≥ 2 CPU cores and ≤ 7 GB RAM).

## 1. Clone the repository & navigate
```bash
git clone
cd text-tone-emotional-support
```

## 2. Set up the Python environment
```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
```

## 3. Verify data availability
```bash
# 1) Stimuli (generated automatically)
python code/01_generate_stimuli.py # produces data/raw/stimuli.csv

# 2) Real human ratings (must be placed here before proceeding)
if [ ! -f data/raw/real_ratings.csv ]; then
 echo "ERROR: data/raw/real_ratings.csv not found. Obtain the Prolific export and place it here."
 exit 1
fi
python code/02_collect_real_data.py --mode verify
```

## 4. Run the full analysis pipeline
```bash
# The script orchestrates all phases in the correct order.
python code/run_pipeline.py
```
`run_pipeline.py` internally executes:
1. `03_preprocess.py`
2. `04_fit_lmm.py`
3. (conditionally) `05_posthoc.py`
4. `06_sensitivity.py`
5. `07_generate_report.py`

All intermediate and final results appear under `data/results/`.

## 5. Manifest verification (new)
```bash
# Verify that the SHA‑256 hashes of all generated artifacts match the manifest.
python utils/validate_manifest.py
```

## 6. Inspect the report
```bash
less data/results/report.md
```
The report contains:
- Fixed‑effect table (interaction β, Wald‑based p‑value) – SC‑001
- Tukey‑adjusted pairwise comparisons – SC‑003
- Sensitivity report --- the ... (continued)

## 7. Run contract‑based tests (CI‑style)
```bash
pytest -q tests/contract/
```
All tests must pass before committing any changes.

## 8. (Optional) Benchmark runtime
```bash
python code/benchmark_runtime.py
```
The benchmark should stay within the allocated time limit; if it exceeds, consider reducing the number of **benchmark** iterations (the pipeline already uses a modest default).

---

**Note**: The pipeline **​**  ​   ​ ​  ​  ​  ​  **  **  the  ?  ?  ?  ** </ ? ? </ </ ? ... ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** (?? ?? ??) 