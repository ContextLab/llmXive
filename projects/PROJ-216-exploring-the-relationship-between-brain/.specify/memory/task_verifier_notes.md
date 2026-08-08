# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No evidence was provided that a `data/raw` directory was actually created or that its existence was programmatically verified; the submission contains only the task description and specifications without any artifact (e.g., a file system listing, script output, or log) confirming the directory’s presence.
- **T001c** — No artifact showing that a `data/interim` directory was created or that its existence was verified is provided; the claim lacks any concrete file‑system evidence. The implementer must create the directory and include a proof (e.g., a screenshot, command output, or script that checks `os.path.isdir('data/interim')`).
- **T001d** — No evidence of a `data/processed` directory (or any script/file that creates and checks it) is provided; the artifact is missing, so the requirement is not satisfied.
- **T001f** — No evidence of the required `tests/unit` and `tests/integration` directories is provided, nor any script or test that checks their existence. The implementer must add these directories (with at least placeholder files) and include a verification step (e.g., a test or script that asserts the directories exist).
- **T001g** — No artifact showing a `reports` directory was provided, nor any script or log confirming its creation and existence. The implementer’s submission contains only the project specification without the required directory or verification evidence.
- **T003** — No linting/formatting configuration files (e.g., pyproject.toml entries for ruff and black, .ruff.toml, or related setup scripts) were provided or referenced, so there is no evidence that the required tools have been configured. The implementer must supply the actual configuration artifacts.
- **T005** — No script or code file that checks for the presence of FSL and AFNI is provided; the only artifacts described relate to data preprocessing, graph metrics, and analysis, not a system‑level dependency check. The required dependency‑check script is missing.
- **T008a** — The required file `specs/amendment-001-fluid-intelligence-n10.md` was not presented, and no content showing the three amendment clauses was provided. Without the artifact, the task cannot be considered fulfilled.
- **T013b** — No code, script, or documentation implementing the required fallback logic for ds000230 is present; the provided information contains only the original feature specification and no concrete artifact demonstrating that ds000230 is used when ds000224 fails or lacks data. The task therefore remains unfulfilled.
- **T014a** — declared artifact(s) missing/empty/invalid: data/processed/valid_subjects.json
- **T014c** — declared artifact(s) missing/empty/invalid: data/processed/pipeline_errors.log
- **T016a** — declared artifact(s) missing/empty/invalid: data/processed/motion_exclusion_log.csv
- **T016b** — declared artifact(s) missing/empty/invalid: data/processed/pipeline_errors.log
- **T017a** — declared artifact(s) missing/empty/invalid: data/processed/preprocessing_stats.json
- **T017b** — No `preprocessing_stats.json` file was presented, nor any code or output showing the calculation of `successful_subjects / total_downloaded_subjects`. Without this artifact, the required success‑rate metric has not been produced.
