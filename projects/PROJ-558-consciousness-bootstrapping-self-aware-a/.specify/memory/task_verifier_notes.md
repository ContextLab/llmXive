# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — The required `data/raw/gsm8k.json` and `data/raw/mmlu.json` files are absent, and there is no evidence that `data_loader.py` contains a function that actually downloads the datasets and writes those files (only a manifest entry exists). The task’s core output – the saved evaluation datasets – is missing.
- **T014** — No evidence of a modified `train.py` was presented—no code showing recursion‑depth checks, OOM handling, error logging, or a non‑zero exit on violation. The required validation and hard‑fail behavior are therefore missing.
- **T037** — No `docs/` files containing the new statistical report format or metric definitions are present in the provided evidence; the required documentation updates are missing.
- **T038** — No CI configuration, workflow file, or script output showing that `ruff check` and `black --check` are executed on the `code/` directory, nor evidence that the CI pipeline fails on lint/format errors, is present. The required artifact (CI setup enforcing these checks) is missing.
- **T039** — declared artifact(s) missing/empty/invalid: results/memory_profile.log
- **T041** — No validation output, logs, or confirmation that `quickstart.md` was executed and all required artifacts were checked; the provided information contains only the task description and no concrete evidence of the validation being performed.
