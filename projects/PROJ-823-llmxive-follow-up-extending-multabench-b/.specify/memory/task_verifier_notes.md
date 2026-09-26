# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008b** — The script exists and logs the required error message, but it constructs the baseline file path relative to the `code` directory (`Path(__file__).resolve().parent.parent`) instead of the project root, so it will look for `code/data/raw/multabench_baselines.csv` and fail to detect the file even when it is correctly placed in `data/raw/`. The path logic must be corrected to point to the actual project‑root `data/raw/` location.
