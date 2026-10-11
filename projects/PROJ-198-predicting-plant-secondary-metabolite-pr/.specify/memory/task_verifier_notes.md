# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=2
- **T003** — The required `.env.example` template is absent from the evidence (no such file was resolved), and the env loading in `code/config_env.py` uses `pydantic-settings` plus a hand-rolled parser rather than `python-dotenv` as specified. Additionally, the verification criterion would fail: `config.get("PMDB_API_TOKEN")` returns `None` because the code only defines/reads `PMDB_TOKEN` (the `EnvManager.get` falls back to `getattr(self._config, key, None)`, and no `PMDB_API_TOKEN` field exists), and there is no execution evidence that either key returns a non-empty string after sourcing the template.
- **T005** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=2
