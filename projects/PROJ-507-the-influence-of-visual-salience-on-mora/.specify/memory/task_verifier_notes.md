# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — No `.gitignore` file content or `git check-ignore` output is provided; without the actual file and verification evidence, we cannot confirm the required patterns are excluded. The task remains undone.
- **T003** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T003a** — The required `.ruff.toml` file is missing from the repository, so the existence check fails and no validation of required keys can be performed. The task therefore is not satisfied.
- **T008** — No `.env.example` file was presented in the provided evidence, and therefore the required variables `VISUAL_GENOME_URL` and `SURVEY_API_KEY` cannot be verified as present. The implementer must add a non‑empty `.env.example` file containing at least the two specified environment variables.
- **T008a** — No `.env.example` file or its contents were provided; therefore we cannot verify that the file exists nor that it contains the required `VISUAL_GENOME_URL` and `SURVEY_API_KEY` keys. The implementer must supply the actual file with those entries.
