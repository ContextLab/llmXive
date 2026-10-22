# Quickstart

The following commands run the full benchmark on a fresh GitHub Actions runner (CPU‑only).

```bash
# 1️⃣ Clone the repository (already done in CI)
git checkout 001-semantic-decay-retrieval

# 2️⃣ Create a virtualenv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # contains exact versions

# 3️⃣ Download and verify datasets (checksums stored in data/checksums.txt)
python -m src.data.download

# 4️⃣ Preprocess raw Ego4D data, perform semantic coherence validation, and build FAISS index
python -m src.data.preprocess

# 5️⃣ Run the full evaluation (produces evaluation_report.json)
python -m src.cli.run

# 6️⃣ Validate output against the contract
pytest -q tests/contract/test_evaluation_report.py
```

**What you get**

* `evaluation_report.json` – machine‑readable results adhering to the contract, including optimal α, β, λ.  
* `report.md` – human‑readable summary (accuracy, latency, significance, optimal parameters).  
* `data/processed/faiss_hnsw_ego4d.index` – deterministically built FAISS index for reproducibility.  

All steps respect the CPU‑only constraint and stay under a reasonable RAM threshold.  

---