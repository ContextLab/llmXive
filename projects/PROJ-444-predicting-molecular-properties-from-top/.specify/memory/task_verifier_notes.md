# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The core artifacts exist and are consistent with the run log (checksum matches `data/raw/esol.csv`, power report shows `passes: true` with actual_n=4197, 3 large molecules logged, 2441 scaffolds, 5-fold split written), and the data is real. However, two explicit requirements are not met: (1) the script's default source is the `skfp` loader rather than downloading from the specified default URL `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv` (the `--url` path exists but is not the default behavior), and (2) the required "chunked sparse-matrix fallback" for processing
- **T002** — Requested task execution failed; rerun successfully: code/02_tda_computation.py exit=1
