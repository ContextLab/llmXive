# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The required `code/calibration.py` (containing `estimate_lambda`) does not exist, and the input raster `data/raw/nlcd_30m_colorado.tif` is missing, so no real MLE/GMM estimation could have been performed. The JSON output appears fabricated without evidence of a genuine data‑driven computation.
- **T014** — declared artifact(s) missing/empty/invalid: code/resampling.py
- **T015** — declared artifact(s) missing/empty/invalid: code/resampling.py
- **T017** — The required file `code/resampling.py` does not exist, so there is no implementation of windowed reads or the specified 2000×2000 pixel chunking. Without the file, the task cannot be satisfied.
- **T031** — No `sensitivity_report.md` file or any other evidence of a sensitivity analysis (resolution factor sweep, bilinear resampling, threshold verification) was provided. The required artifact is missing, so the task is not satisfied.
- **T035a** — No README.md content was provided, and there is no evidence that the file was created or updated with CLI usage examples. The required artifact is missing, so the task is not satisfied.
