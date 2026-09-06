# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-1071-llmxive-follow-up-extending-synthdocbenc/` directory or any files within it was provided; the claim lacks the required concrete project‑structure artifact.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a pre‑commit hook) are present in the provided evidence, so the requirement to set up ruff and black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly reference ruff and black.
- **T005** — No `code/models/` directory or any model definition files and schema validator implementations are present, and there is no evidence that they correspond to the YAML schemas in `contracts/`. The required artifacts are missing, so the task is not satisfied.
- **T006** — No logging configuration, code, or directory structure was provided; there is no evidence of a `logs/` folder or JSON‑structured logging setup, so the required artifact is missing.
- **T010** — The provided `code/baseline_eval.py` stops after a partially shown `load_pdf_image` function and contains no visible logic for running VLM inference, profiling latency/memory, or writing results to `data/derived/perf_metrics.json`. Moreover, the required `perf_metrics.json` file is missing entirely. The task’s core requirements are therefore not satisfied.
