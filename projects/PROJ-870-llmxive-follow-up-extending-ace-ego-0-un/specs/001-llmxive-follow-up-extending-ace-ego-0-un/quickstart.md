# Quickstart: llmXive static‑proxy analysis

**Feature**: `001-llmxive-static-proxy`  
**Date**: 2026-10-24  

Run the complete research pipeline on a fresh GitHub Actions runner (or locally) using **CPU only**.

## Prerequisites
```bash
# Clone the repository (run from project root)
git clone https://github.com/your-org/llmxive-project.git
cd llmxive-project

# Set up a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Pipeline Commands

| Step | Command | What it does |
|------|---------|--------------|
| 0️⃣ | `python src/cli/run_pipeline.py --stage download` | Streams VLA parquet, RoboCasa zip, and RoboTwin zip from the verified URLs; verifies SHA‑256 checksums; records metadata in the project manifest. |
| 1️⃣ | `python src/cli/run_pipeline.py --stage extract-static` | Extracts static features (entropy, hand confidence via MediaPipe Hands, lighting, metadata) at **0.5 fps** (adaptive down‑sampling to 0.25 fps if RAM > 5 GB) → `data/static_features.csv`. |
| 2️⃣ | `python src/cli/run_pipeline.py --stage train-static-model` | Trains Random Forest regressor, writes predictions (`data/static_predictions.csv`) and residuals (`data/static_residuals.csv`). |
| 3️⃣ | `python src/cli/run_pipeline.py --stage augment-temporal` | Computes optical‑flow features for 1 s, 3 s, 5 s, 10 s windows using OpenCV Farneback (CPU) → `data/temporal_features_{w}s.csv`. |
| 4️⃣ | `python src/cli/run_pipeline.py --stage filter-high-reliability` | Performs ROC‑based cutoff selection and sensitivity sweep; creates filtered training set. |
| 5️⃣ | `python src/cli/run_pipeline.py --stage train-vla` | Trains three VLA variants (dynamic baseline, uniform weighting, static‑proxy filtered) on the respective training sets (≤ 3 000 episodes). |
| 6️⃣ | `python src/cli/run_pipeline.py --stage evaluate-vla` | Evaluates each VLA model on RoboCasa & RoboTwin (≥ 100 episodes each) → `results/` CSV files. |
| 7️⃣ | `python src/cli/run_pipeline.py --stage equivalence-test` | Runs the TOST equivalence test (±2 % margin) on benchmark success‑rate differences and reports p‑values. |
| 8️⃣ | `python src/cli/run_pipeline.py --stage analyze` | Generates tables, plots (`figures/`), and a markdown summary (`report/summary.md`). |
| 9️⃣ | `python src/cli/run_pipeline.py --stage validate-contracts` | Validates **all** contract schemas against their corresponding CSVs. |

## Resource Usage
- **CPU**: ≤ 2 cores (default GitHub Actions runner).  
- **RAM**: Peaks at a modest amount of memory (on the order of gigabytes) during static extraction; adaptive down‑sampling keeps it < 6 GB.  
- **Runtime**: Full pipeline ≈ 4.5 h on the free tier (including VLA training on ≤ 3 000 episodes).  

## Troubleshooting
- **Download failures**: The `download` stage aborts if a checksum mismatch occurs; re‑run the stage to retry.  
- **Out‑of‑memory**: If RAM exceeds 5 GB the pipeline automatically reduces frame sampling to **0.25 fps** and logs the change.  
- **Contract validation errors**: All schemas under `contracts/` are validated; update the CSVs if a schema mismatch is reported.  

Happy research!

---


