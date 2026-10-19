# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart.md and the run log show the command executes without error and produces `data/processed/descriptors_subset.csv`. However, the task requires the existence of `data/processed/descriptors.csv` (the renamed version of the subset file), which is listed as MISSING. The expected file name does not match the provided artifact, so the verification condition is not satisfied. The implementer must generate and commit `data/processed/descriptors.csv` (or rename the existing subset file accordingly).
- **T003** — Requested task execution failed; rerun successfully: scripts/run_minimal.sh exit=1
