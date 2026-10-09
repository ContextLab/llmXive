# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/requirements.txt` file exists but contains additional packages (`torch`, `joblib`, `matplotlib`) beyond the exact list required (pandas, scikit-learn, numpy, requests, pyyaml, memory-profiler, seaborn, pytest). This does not satisfy the task’s specification.
- **T007** — The file `state/projects/PROJ-386-predicting-the-impact-of-processing-temp.yaml` exists, but its contents are a project metadata document and do not include the required top‑level keys `artifact_hashes` (a map) and `updated_at` (a timestamp). The schema specified for task T007 is therefore not satisfied. The implementer must replace or augment the YAML so that it contains those two keys with appropriate values.
