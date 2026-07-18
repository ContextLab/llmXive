# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013d** — The required output file `data/metadata/harmonized_matrix.csv` does not exist, and the provided `src/pipelines/ingest.py` snippet shows only ontology‑mapping utilities without any logic that merges, validates, cleans metadata, or writes the harmonized matrix CSV. Consequently the task’s core requirement is unmet.
- **T015** — The `src/pipelines/preprocess.py` file contains no import or usage of `miceforest`, nor any logic for MICE imputation, convergence checking, or row dropping. Additionally, the required `data/cleaned_metadata.csv` file is absent. Both the implementation and the verification artifact are missing.
- **T018** — The repository lacks the required `results/permanova_summary.csv` file, and the provided `src/pipelines/analysis.py` does not contain any implementation of PERMANOVA (adonis2) with the specified permutation logic or Benjamini‑Hochberg correction. The task’s core output and functionality are therefore missing.
- **T020** — declared artifact(s) missing/empty/invalid: src/pipelines/report.py
- **T022** — declared artifact(s) missing/empty/invalid: results/permanova_summary.csv, results/db_rda_variance.csv
- **T026** — The provided `analysis.py` does not show any logic that checks stratum sample counts and skips PERMANOVA/varpart, nor does it write to `results/skipped_strata.log`. Moreover, the required log file is absent from the repository. The power‑check implementation and the verification log entry for biome “FR-005” are missing.
- **T028** — No `results/db_rda_biome_<NAME>.csv` files are present; the claim provides only a description of the expected output without any actual CSV artifacts, so the required per‑biome R² results are missing. The next implementer must generate and commit the CSV files for each biome as specified.
- **T029** — declared artifact(s) missing/empty/invalid: results/biome_ranking_summary.csv
- **T030** — No summary report file (e.g., CSV, PDF, or markdown) showing the top predictor per biome was provided; the evidence consists only of the task description and specifications, with no actual output artifact to verify the required analysis.
- **T033** — declared artifact(s) missing/empty/invalid: src/pipelines/report.py
