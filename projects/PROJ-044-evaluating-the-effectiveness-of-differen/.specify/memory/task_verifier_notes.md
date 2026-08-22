# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — No content of `specs/001-evaluating-dp-federated-learning/spec.md` is provided, nor any grep output showing that the word “Shakespeare” is absent. Without the actual file or verification result, we cannot confirm that all Shakespeare references have been removed and that FR‑001 lists only “FEMNIST”. The required artifact is missing.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T011** — The `code/data/download.py` script is present, but the required output files `data/raw/femnist.parquet` and `data/raw/femnist.sha256` are missing, which is a mandatory completion criterion. Without these files the task is not considered done.
- **T013** — No JSON partition files matching the pattern `partition_femnist_{seed}_{alpha}.json` are present in `data/partitions/`, and the claim provides no evidence of such files, their schema, or any explicit reference to T000 as required. Consequently the required output artifact is missing.
