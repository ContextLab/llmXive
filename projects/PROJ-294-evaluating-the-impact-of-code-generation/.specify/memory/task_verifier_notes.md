# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T051** — The repository contains `code/generate_code_gpu.py`, but the script is truncated, does not include logic to check the `USE_GPU=1` environment variable or fallback from CPU failures, and there is no evidence that it writes the required `data/generated/codegen_samples_gpu.json` (the file is missing). Consequently the task’s core requirements are not satisfied.
- **T052** — The required output file `data/generated/llama_samples.json` does not exist, and the provided `generate_code_llama.py` is truncated (the core generation and saving logic is not shown). Without the JSON artifact, the task’s primary deliverable is missing.
