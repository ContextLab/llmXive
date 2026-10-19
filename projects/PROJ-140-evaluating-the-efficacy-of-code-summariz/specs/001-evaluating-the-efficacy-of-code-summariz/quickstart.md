# Quickstart: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

## 1. Project Layout
```
<project-root>/
├─ code/
│   ├─ main.py                # CLI entry point
│   ├─ data_prep/
│   │   ├─ download_defects4j.py
│   │   └─ generate_summaries.py
│   ├─ simulation/
│   │   └─ simulate_study.py
│   ├─ analysis/
│   │   └─ run_statistics.py
│   └─ utils/
│       ├─ pii.py
│       └─ timing.py
├─ data/
│   ├─ raw/
│   ├─ processed/
│   ├─ interaction_logs/
│   ├─ analysis_results/
│   └─ defects4j_version.txt
├─ specs/…/quickstart.md
├─ contracts/
│   ├─ dataset.schema.yaml
│   ├─ interaction.schema.yaml
│   └─ analysis.schema.yaml
├─ tests/
├─ .github/workflows/
└─ requirements.txt
```

## 2. Provenance
- **Defects4J version**: `2.0` (recorded in `data/defects4j_version.txt`).  
- **Random seed**: All stochastic steps use seed `42`.  

## 3. Running the Full Pipeline (CI / Simulation)

```bash
# 1️⃣ Install exact dependencies (once)
pip install -r requirements.txt

# 2️⃣ Verify the CLI loads
python -m code.main --mode sim --help
```

### Typical workflow (simulated CI run)

```bash
# 2️⃣ Download the verified Defects4J dataset (streaming, checksum‑verified)
python code/data_prep/download_defects4j.py

# 3️⃣ Generate rule‑based summaries (baseline and rule)
python code/data_prep/generate_summaries.py --mode sim

# 4️⃣ Simulate participant interactions (12 participants, 10 tasks per condition)
python code/simulation/simulate_study.py --participants 12 --tasks-per-condition 10 --seed 42

# 5️⃣ Run the statistical analysis (CI‑mode disables heavy bootstrapping if needed)
python code/analysis/run_statistics.py --input data/interaction_logs/simulated_logs.csv --mode ci

# 6️⃣ Verify outputs against contracts
pytest -q tests/contract
```

All steps complete within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).  

## 4. Real‑Study Execution (requires GPU)

1. **Generate LLM summaries** on a Kaggle GPU (once per method):
   ```bash
   bash scripts/run_llm_gpu.sh   # writes data/processed/summaries_llm.csv
   ```
2. **Run the full pipeline** with real interaction logs:
   ```bash
   python -m code.main --mode real --log-file data/interaction_logs/anonymized_logs.csv
   ```

The pipeline will automatically detect the presence of `summaries_llm.csv`; if missing, it aborts with a clear message.

## 5. Reproducibility Guarantees
- All random seeds are fixed (`42`).  
- Defects4J version is pinned (`2.0`).  
- The same `requirements.txt` reproduces the environment on any machine with Python 3.11+.  
- Contract validation (`pytest -q tests/contract`) ensures every output file conforms to the declared schema.  

---
