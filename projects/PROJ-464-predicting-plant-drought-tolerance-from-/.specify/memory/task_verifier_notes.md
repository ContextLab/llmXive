# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042#1** — The provided `code/download_images.py` defines helper functions for computing and saving checksums, but the truncated view does not show any logic that (a) generates `data/raw/nppn_checksums.json` when it is absent, (b) compares downloaded file hashes against the manifest, or (c) aborts with the exact error message “Data integrity check failed for NPPN images.” Moreover, the required `data/raw/nppn_checksums.json` file is missing, so there is no evidence that the script creates or uses it as specified. The task’s core verification behavior is not demonstrably implemented.
- **T045#1** — declared artifact(s) missing/empty/invalid: results/figures/vif_heatmap.png
- **T046** — declared artifact(s) missing/empty/invalid: results/figures/sensitivity_curve.png
