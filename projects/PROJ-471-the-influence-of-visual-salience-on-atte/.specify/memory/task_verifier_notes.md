# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/bootstrap.py` script parses `sys.argv` directly, causing a `SystemExit` when the test suite runs (pytest injects its own arguments). Consequently `tests/test_bootstrap.py` fails, so the required directories, `requirements.txt`, and `quickstart.md` are never created under the temporary root. The script must ignore or strip external arguments (e.g., use `parse_known_args()` or `parser.parse_args([])`) to let the test pass.
- **T002** — The `tests/test_verify_data.py` suite fails the `test_verify_missing_dir` case because the script raises `RuntimeError("DATA_MISSING_001: ds003123 incomplete")` but does not include the required substring “ds003123 not found” in its error output. This mismatch means the implementation does not meet the specified verification behavior.
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
