# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `data/` directory at the repository root is provided, nor any verification of its permissions (755). The implementer must create the directory and show its existence and correct mode.
- **T002** — No evidence was presented showing that the `data/raw/`, `data/processed/`, and `data/logs/` directories exist, nor that they have 755 permissions. The implementer must provide filesystem verification (e.g., a `tree` listing or `ls -ld` output) confirming the creation and correct permissions of these subdirectories.
- **T003** — No evidence was provided showing that the `tests/`, `tests/unit/`, and `tests/contract/` directories exist, nor any information about their permissions being set to 755. Without concrete artifacts or permission details, the requirement is not satisfied.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/perturbation_candidates.json
- **T023** — No code, configuration, or documentation for a sandbox executor with a fixed per‑test‑case timeout was provided; the claim lacks any artifact demonstrating that such an executor has been integrated or that it enforces the required timeout. The required implementation and evidence are missing.
