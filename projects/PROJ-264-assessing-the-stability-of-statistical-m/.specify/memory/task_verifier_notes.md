# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T050** — No execution logs, output files, or reports are provided showing a full pipeline run on three datasets (one <1k, one 1k‑10k, one >10k). Without concrete artifacts (e.g., console output, generated report, or saved results) the claim cannot be verified. The required evidence of the end‑to‑end smoke test is missing.
- **T051** — The required artifact `results/memory_profile.log` does not exist, so the memory profiling step was not performed or its output was not saved as specified. The task’s core requirement—logging peak RSS memory usage—is unmet.
- **T052** — No evidence of the smoke test being run twice, no recorded checksums of the output CSVs or final report, and no verification that they are identical. The required artifact (determinism verification results) is missing.
- **T053** — The required `.github/workflows/ci.yml` file does not exist in the repository, so no workflow configuration can be verified for the specified triggers, timeout, or signal handling. The implementer must add the file with the correct settings.
