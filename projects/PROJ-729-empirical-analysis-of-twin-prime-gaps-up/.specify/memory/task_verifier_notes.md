# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The file `tests/unit/test_gap_calc.py` exists and `test_normalized_gap_formula` does use p=3, delta=2, and the 1e-4 tolerance, but it computes `expected_normalized` and `actual_normalized` with the identical expression (`delta / math.log(p)`), making the assertion tautological rather than checking against an independently derived expected value. More critically, the module-level `from generate_primes import compute_hardy_littlewood_expected_count` will fail: the test inserts `tests/` (the parent of `tests/unit`) into `sys.path`, but `generate_primes.py` lives in `code/`, so the entire test mod
- **T013b-b** — Requested task execution failed; rerun successfully: code/compute_expected_count.py exit=1
- **T012** — Requested task execution failed; rerun successfully: code/generate_primes.py exit=1
