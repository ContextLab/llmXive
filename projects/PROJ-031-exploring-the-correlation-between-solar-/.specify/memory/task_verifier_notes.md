# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required output file `data/raw/dst_indices.csv` does not exist, and the provided `code/ingest.py` is truncated and contains obvious errors (e.g., `connect_to_swpc` returns an undefined variable `f`). Consequently the script does not demonstrably download Dst indices nor write them to the expected CSV. The task therefore remains unfinished.
- **T013b** — The required output file `data/raw/kp_indices.csv` does not exist, and the provided `code/ingest.py` excerpt shows no implementation for downloading Kp indices or writing/validating them against a schema. The task’s core requirement is therefore unmet.
- **T016b** — declared artifact(s) missing/empty/invalid: data/processed/analysis_subset.csv
- **T017** — The `code/validate.py` file is only partially shown (truncated) and does not contain a complete blocking validation routine, and the required schema file `contracts/aligned_event.schema.yaml` is absent from the repository, so the validation gate cannot actually be executed. The task therefore remains unfinished.
