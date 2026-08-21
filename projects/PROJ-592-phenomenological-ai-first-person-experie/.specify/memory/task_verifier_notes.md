# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T030a** — No `quickstart.md` content was provided, so we cannot confirm that the required CLI usage examples (`python main.py --mode generation`, `... analysis`, `... validate`) were added. The verification command cannot be run because the file (or its relevant lines) is absent. The implementer must supply a non‑empty `quickstart.md` containing at least one occurrence of the specified example command.
- **T033** — The repository lacks a `config.yaml` file required for the command, and there is no evidence (logs, timing output, or execution results) that `python code/main.py --mode generation --limit 100 --config config.yaml` was run successfully within the 6‑hour limit. Without these artifacts the validation task is not satisfied.
