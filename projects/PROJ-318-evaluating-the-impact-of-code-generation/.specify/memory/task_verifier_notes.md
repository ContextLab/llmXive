# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure or any files were provided; the claim that the required folders exist is unsupported by any tangible artifact in the submission. The implementer must create and show the listed directories (e.g., a printed tree or actual folder listings) to satisfy the task.
- **T009** — No configuration files, scripts, or documentation were presented that define environment variables for model paths or implement rate‑limit retry logic. The claim lacks any tangible artifact, so the requirement is not satisfied.
- **T010** — The `repo_loader.py` file is incomplete – it ends with a dangling line (`if not isinstance(entry["name"], str) or`) that makes the module syntactically invalid, so the validation logic is not fully implemented. Moreover, the required data file `data/raw/repo_list.json` is absent, meaning the loader cannot actually load and validate any repository list. Both the missing JSON file and the broken code prevent the task from being genuinely satisfied.
