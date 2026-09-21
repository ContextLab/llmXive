# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The repository contains `code/stimuli/metadata.py`, but the file is truncated and never writes any YAML files to `data/stimuli/`. No `data/stimuli/{id}_metadata.yaml` files are present (the only referenced `_metadata.yaml` is missing). Consequently the required output files and full metadata generation logic are not provided.
- **T035#1** — The repository contains `code/analysis/anova.py` with a gate check and ANOVA computation, but the script does not show any code that writes the results to `data/analysis/anova_results.json`, and that JSON file is missing. Consequently the required output artifact and schema verification are not satisfied.
- **T096** — No `plan.md` file or its contents were provided; consequently we cannot verify that it contains the required phrases “ladder of explanation” and “serotonin → cAMP → PKA → CREB”. The implementer must supply the updated `plan.md` with the specified subsection and verify the phrases are present.
