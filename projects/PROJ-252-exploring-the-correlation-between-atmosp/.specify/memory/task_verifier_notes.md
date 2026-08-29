# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The `tests/integration/test_download_pipeline.py` file is present but is truncated (e.g., the `missing = require` line is incomplete) and does not actually read the required `data/processed/config.yaml`. Moreover, the `data/processed/config.yaml` file itself is missing, so the test cannot verify the expected earthquake count of 12 as specified. The task’s core requirement is therefore not met.
- **T013a** — The repository lacks the required `data/interim/land_mask.geojson` file, and the provided excerpt of `code/preprocess.py` does not contain a `load_land_mask()` implementation (the file is truncated before any such function could appear). Without the function and/or the mask file, the task requirement is not satisfied.
