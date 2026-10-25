# Quickstart

The following commands run the full benchmark on a fresh GitHub Actions runner (CPU‑only).

```bash
# 1️⃣ Clone the repository (already done in CI)
git checkout 001-semantic-decay-retrieval

# 2️⃣ Create a virtualenv and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # contains exact versions

# 3️⃣ Download and verify datasets (checksums stored in data/raw/CHECKSUMS.txt)
python -m src.data.download

# 4️⃣ Preprocess raw data, perform semantic coherence validation, and build FAISS index
# (to be implemented in later tasks)
# python -m src.data.preprocess

# 5️⃣ Run the full evaluation (produces evaluation_report.json)
# (to be implemented in later tasks)
# python -m src.cli.run

# 6️⃣ Validate output against the contract (once the contract test is added)
# pytest -q tests/contract/test_evaluation_report.py
```

**What you get**

* `data/raw/squad_train.jsonl` – the raw SQuAD training set in JSONL format.  
* `data/raw/CHECKSUMS.txt` – SHA‑256 checksum for the downloaded file.  
* Subsequent steps will generate processed data, indexes, and evaluation reports.  

All steps respect the CPU‑only constraint and stay under a reasonable RAM threshold.