# Implementation evidence context (2026-10-09)

The fresh canary's `docs/research.md` claimed N=10000, p=5 unconditional TV=0.018 and conditional TV=0.021. Its actual JSON contained 0.1452 and 0.057269395235186316. The report also invented near-uniform residue counts. These claims had not passed acceptance.

The implementation prompt supplied source interfaces and referenced source files but no data files for the summary task. A task naming only `docs/research.md` could not inspect its own outputs. Prompts now include bounded literal CSV/JSON/TSV contents under data/results/outputs, prioritizing smaller summaries, plus paths and content hashes. Omitted files are explicitly identified, links outside the project are excluded, and reads/prompt length are bounded. The instructions prohibit invented example measurements and distinguish current file contents from successful execution or accepted results.

This is evidence delivery, not scientific acceptance: files can be stale, incorrect, or produced by failed execution. Execution, independent task verification, and claim gates remain necessary.

Validation: 34 focused tests pass, including a real production prompt assembled from temporary project data, bounded large-file handling, and exclusion of external file/directory symlinks. Related to #1139.
