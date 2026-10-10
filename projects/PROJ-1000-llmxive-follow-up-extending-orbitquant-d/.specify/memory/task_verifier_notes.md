# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires that `python code/main.py --phase init` runs without error and prints exactly "Initialization complete". However, `code/main.py` has a critical bug: it imports `json` at line 1 (implicitly via the validation module) but never imports it explicitly, and more critically, it calls `json.load()` in the `run_validation_gate()` function without the `json` module being imported in the file. When `--phase init` is executed, the `run_init_phase()` function will succeed and print "Initialization complete", but the module-level imports will fail because `code/main.py` does not contain `
- **T002** — Requested task execution failed; rerun successfully: code/data/download_coco.py exit=1; code/data/download_diverse_prompts.py exit=1; code/data/preprocess.py exit=1
