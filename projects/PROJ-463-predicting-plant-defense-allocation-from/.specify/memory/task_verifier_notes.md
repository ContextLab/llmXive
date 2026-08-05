# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011a** — The repository contains a non‑empty `src/data/verify_metadata.py`, but the required output file `data/processed/metadata_verification_report.json` is absent, and the shown code is truncated before any logic that writes such a report. Without the JSON report the task’s output requirement is not satisfied.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/post_qc_species_list.json, data/processed/metadata_verification_report.json
- **T025a** — The repository lacks the required `data/processed/post_qc_species_list.json` file, causing `load_target_species_list` to raise a `FileNotFoundError`, and no `data/processed/trait_fallback_summary.json` is present or generated. Consequently the script cannot read the species list nor produce the mandated summary output.
- **T025b** — The repository contains `src/data/traits_fallback.py`, but the required input file `data/processed/post_qc_species_list.json` and the output file `data/processed/trait_fallback_summary.json` are absent, so the script cannot be exercised and does not demonstrate that it appends a `fallback_results` key or updates `missing_from_try`. The implementer must supply the missing JSON files (or generate them) and ensure the script writes the expected summary structure.
- **T038** — declared artifact(s) missing/empty/invalid: data/processed/trait_fallback_summary.json, data/processed/final_aggregated_traits.json
- **T040** — declared artifact(s) missing/empty/invalid: src/analysis/reproducibility.py, data/manifests/real_data_manifest.json
- **T028a** — declared artifact(s) missing/empty/invalid: src/data/phylogeny_fetcher.py, data/processed/post_qc_species_list.json, data/processed/phylogenetic_tree.tre
