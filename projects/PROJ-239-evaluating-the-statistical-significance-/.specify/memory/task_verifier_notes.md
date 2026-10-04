# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — The required `.github/workflows/ci.yml` file is missing from the repository, so the CI configuration deliverable is not present. Consequently the verification script cannot be run, and the task is not satisfied.
- **T025** — The required output file `data/derived/final_report.csv` does not exist, and the provided `merge_results.py` script (as shown) does not demonstrate that it writes a CSV with the exact schema `ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper` nor that it enforces the verification checks on input DataFrames. The missing final report file means the task’s primary deliverable is absent.
