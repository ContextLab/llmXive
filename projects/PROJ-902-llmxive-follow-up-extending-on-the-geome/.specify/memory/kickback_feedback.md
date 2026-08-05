# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T003 expects a `.ruff.toml` linting configuration file, but the file is absent from the repository, violating Constitution Principle I (reproducibility) and the plan’s requirement for linting enforcement.
- Task T004 references a GitHub Actions workflow file `.github/workflows/ci.yml` that does not exist, breaking Constitution Principle VII (extreme resource constraints verification) and preventing CI‑based resource‑limit validation.
- Task T005 calls for a top‑level `README.md` with quick‑start instructions, yet the file is missing, undermining reproducibility and the plan’s documentation deliverable.
- Task T041 specifies generation of `data/checksums.txt` for GSM8K files, but the checksum file is not present, leaving Constitution Principle III (data hygiene) unenforced.
- Task T044 requires the dataset‑download script to validate SHA‑256 checksums before returning data, but the validation logic and associated test (`tests/integration/test_checksum_validation.py`) are absent, violating data‑hygiene constraints.
