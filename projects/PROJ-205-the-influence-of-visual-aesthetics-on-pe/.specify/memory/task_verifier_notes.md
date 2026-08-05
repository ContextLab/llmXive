# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No `plan.md` file or any directory structure under `projects/PROJ-205-.../` is present; the required project scaffold was not provided. The task’s core deliverable is missing.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or setup instructions were provided, so the requirement to configure ruff/flake8 and black is not satisfied.
- **T004** — The required source file `docs/NEUTRAL_TEXT_V1.txt` is missing, so the content in `code/stimuli/text_content.txt` cannot be verified as the correct neutral text. Moreover, the existing text appears unrelated to the expected neutral source, indicating the task was not fulfilled.
- **T009** — No evidence was provided that the `data/raw/` and `data/processed/` directories actually exist in the repository (or that they contain any placeholder files). The implementer’s claim lacks the required filesystem artifacts, so the directory structure setup cannot be confirmed.
- **T011b** — declared artifact(s) missing/empty/invalid: data/consent/irb_approved.txt, docs/IRB_PROTO_V1.txt
- **T011c** — No code, configuration file, or log examples were provided showing an `IRB_PROTOCOL_ID` environment variable defined or its inclusion in consent log entries. The required artifact (environment variable definition and logging implementation) is missing.
- **T011** — declared artifact(s) missing/empty/invalid: data/consent/irb_approved.txt
- **T011a** — declared artifact(s) missing/empty/invalid: docs/IRB_PROTO_V1.txt
- **T012** — The `code/survey/app.py` contains a consent form that attempts to read the consent text, but the required source file `data/consent/irb_approved.txt` does not exist, so the app falls back to a placeholder message instead of displaying the actual IRB‑approved text. Consequently the task’s core requirement (displaying the IRB text from that file) is not satisfied. The missing consent file must be added (and the path verified) for the implementation to be complete.
- **T022** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
- **T023c** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
- **T023d** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
- **T023e** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
