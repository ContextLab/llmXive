# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The provided `.ruff.toml` only contains an `extend = "pyproject.toml"` line and does not specify the required rule selections (E, W, F) nor set `max-line-length = 88`. Consequently the artifact does not meet the task’s specification, and there is no evidence that `ruff check code/` passes with those settings. The file must be updated to include the rule list and line‑length configuration.
- **T004** — The repository contains no `.gitignore` file (or it is empty), and no evidence (e.g., `git status` output) that the required ignore patterns are in place. The task’s required artifact is missing.
- **T012b-CLI** — declared artifact(s) missing/empty/invalid: code/data/annotate_cli.py
- **T013** — declared artifact(s) missing/empty/invalid: code/data/validate_annotation.py
- **T015d** — declared artifact(s) missing/empty/invalid: code/data/annotate_cli.py, data/human_scores.json
- **T015d-Gen** — declared artifact(s) missing/empty/invalid: code/data/generate_placeholder_scores.py, data/human_scores.json
- **T015d-Load** — declared artifact(s) missing/empty/invalid: code/data/load_human_scores.py, data/human_scores.json
- **T015e** — declared artifact(s) missing/empty/invalid: code/data/generate_placeholder_scores.py, data/human_scores.json
- **T020** — declared artifact(s) missing/empty/invalid: code/models/router.py
- **T021** — declared artifact(s) missing/empty/invalid: code/models/fallback.py
- **T020#1** — declared artifact(s) missing/empty/invalid: code/models/router.py
- **T019b-Run** — declared artifact(s) missing/empty/invalid: code/models/router_model/
- **T034b** — declared artifact(s) missing/empty/invalid: code/analysis/threshold_finder.py
- **T045a** — declared artifact(s) missing/empty/invalid: code/models/router.py
- **T045b** — declared artifact(s) missing/empty/invalid: code/models/router.py
- **T047** — declared artifact(s) missing/empty/invalid: code/models/fallback.py
