# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013a` (rejected 1x): No dataset, code, or output files were presented; the claim lacks any concrete artifact (e.g., a CSV/Parquet file with ≥1,000 rows containing the required columns) to demonstrate that the pre‑trained DanceOPD teacher model was run and ground‑truth routing labels and velocity vectors were generated. The required evidence is missing.
- `T013b` (rejected 1x): No cleaned dataset, validation log, or script was provided to show that undefined routing paths were identified and excluded from the extracted dataset, which is the core requirement of task T013b. The implementer’s claim lacks any tangible artifact demonstrating the final validation step.
- `T014` (rejected 1x): The provided `code/00_data_extraction.py` stops after a helper function and does not contain the extraction, transformation, and streaming logic nor any code that writes `teacher_routing_dataset.parquet`. Moreover, the required output file `data/processed/teacher_routing_dataset.parquet` is absent from the repository. The task’s core requirement is therefore unmet.
- `T020` (rejected 1x): The provided `code/01_train_trees.py` is truncated (ends mid‑print statement) and lacks the full implementation (e.g., saving the train/test splits, argument parsing, main entry). Additionally, the required input file `data/processed/teacher_routing_dataset.parquet` is absent, so the script cannot be exercised. The task’s data‑splitting logic is therefore not fully delivered.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

