# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/bootstrap.py` script still calls `parser.parse_args()`, causing a `SystemExit` when pytest injects its own command‑line arguments (see the test failure log). Because of this the unit test `tests/test_bootstrap.py` aborts before any directories, `requirements.txt`, or `quickstart.md` are created, so the required behavior is not verified. The script must be changed to use `parse_known_args()` (or otherwise ignore unknown arguments) so that it returns 0 and the test can pass.
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
