# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The required directories `data/raw/`, `data/processed/`, and `specs/contracts/` are missing from the project tree, even though `code/__init__.py` is present. The task demands all listed directories to exist, so the implementation is incomplete.
- **T001b** — The provided `requirements.txt` is missing the two required pinned packages `memory-profiler==0.61.0` and `llama-cpp-python==0.2.91`; thus the artifact does not meet the task’s specification.
- **T002** — No renderer script, event logger, text‑only agent loop, or memory‑gap metric code/data were provided; the claim contains only a description of desired behavior without any actual artifacts to verify deterministic ASCII output, JSON logs, inference results, or statistical analysis. Consequently the required deliverables are missing.
- **T004a** — declared artifact(s) missing/empty/invalid: data/processed/, state/checksums.yaml
- **T004b** — The required artifact `utils/checksum.py` with a functional command‑line interface is not present or not shown; no evidence of CLI arguments, help output, or error handling is provided. The implementer must supply the script containing the full CLI implementation and demonstrate it works (e.g., by showing the `--help` output).
- **T005a** — declared artifact(s) missing/empty/invalid: data/processed/, state/artifact_hashes.yaml
- **T039a-4** — declared artifact(s) missing/empty/invalid: state/checksums.yaml, state/artifact_hashes.yaml
- **T039c** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T043** — declared artifact(s) missing/empty/invalid: data/processed/, state/...yaml, state/checksums.yaml
