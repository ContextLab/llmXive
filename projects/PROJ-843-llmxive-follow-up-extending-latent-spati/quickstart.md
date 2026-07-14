# Quickstart – end‑to‑end run‑book

The following commands reproduce the full research pipeline on a CPU‑only
environment. They must be executed **in order** and each command must
exit with status 0.

```bash
# 1️⃣ Download the RealEstate10K dataset (handled by T007)
python code/data/download.py

# 2️⃣ Stratify the dataset (T008)
python code/data/stratify.py

# 3️⃣ Extract sparse features (T009)
python code/data/extract_features.py

# 4️⃣ Solve geometry & warp (T010‑T012)
python code/geometry/run_pipeline.py # produces data/results/sparse_warped_frames.npy

# 5️⃣ Download dense baseline (T016b)
python code/eval/download_dense_baseline.py

# 6️⃣ Compute evaluation metrics (T017)
python code/eval/metrics.py

# 7️⃣ Perform ANOVA (T018)
python code/eval/anova.py

# 8️⃣ Sensitivity analysis (T019)
python code/eval/sensitivity.py

# 9️⃣ Generate final report (T021)
python code/eval/report.py
```