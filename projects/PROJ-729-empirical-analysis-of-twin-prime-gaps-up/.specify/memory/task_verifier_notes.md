# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — I inspected the project root and found the large `data/raw/twin_primes.csv` and the JSON performance reports, but the `performance_gen.json` explicitly records `within_5_percent_of_expected: false`, violating US1’s row‑count criterion. Moreover, the required artifacts for US2 and US3 (`data/results/stats.json`, `data/figures/qq_plot.png`, `data/results/local_stats.json`, `data/figures/local_deviation.png`) and the final Markdown report are absent. The project therefore does not satisfy the specified acceptance criteria.
- **T002** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T003** — declared artifact(s) missing/empty/invalid: .pre-commit-config.yaml
- **T013b-b** — Requested task execution failed; rerun successfully: code/compute_expected_count.py exit=1
- **T012** — Requested task execution failed; rerun successfully: code/generate_primes.py exit=1
- **T021** — Requested task execution failed; rerun successfully: code/analyze_gaps.py exit=1
