# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The script `code/generate_reference.py` correctly computes the partition counts and writes them to `tests/data/reference_values.csv`, and the CSV’s first 20 rows match the expected values. However, the provided pytest suite `tests/test_reference_validation.py` looks for the file at `data/reference_values.csv` (project root) and therefore all four tests fail, indicating the verification step is not satisfied. The reference file must be placed (or the test path adjusted) so that the test can locate it and pass.
- **T003** — Requested task execution failed; rerun successfully: code/generate_partitions.py exit=1
