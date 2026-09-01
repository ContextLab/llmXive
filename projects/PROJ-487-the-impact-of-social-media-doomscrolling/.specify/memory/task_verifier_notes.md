# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004a** — No evidence of a `venv` directory or the required `venv/bin/activate` script was provided; the implementer did not supply any artifact confirming the virtual environment was created. The missing `venv/bin/activate` file must be shown to satisfy the task.
- **T004b** — No evidence was presented showing that `projects/PROJ-487-the-impact-of-social-media-doomscrolling/venv/bin/activate` exists; the implementer did not provide a directory listing, screenshot, or any file verification output. The required artifact is missing.
- **T007a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010a** — The claim that a `test_fetch_gdelt.py` file exists in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/` cannot be verified because no such file or its contents were provided. The required test file is missing from the evidence, so the task is not satisfied.
- **T010b** — No `test_fetch_gdelt.py` file or its contents were presented, and there is no evidence that mock logic using the `responses` library was added to simulate two 500‑error requests followed by a successful one. The required test artifact is missing.
- **T010c** — No test file `test_fetch_gdelt.py` with a `test_retry_logic_on_failure` function containing the required assertion is present; the claim provides no artifact or code to verify the retry‑count check or the final successful response. The required test implementation is missing.
- **T011a** — No evidence of a `test_fetch_google_trends.py` file in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/` was provided; without the actual test file, the task requirement is not satisfied. The implementer must add the requested test file containing appropriate unit tests for the Google Trends data‑fetching functionality.
- **T011b** — No `test_fetch_google_trends.py` file or any test code was presented, and there is no evidence of mock logic that supplies an invalid keyword list and asserts a `ValueError`. The required test artifact is missing.
- **T011c** — No test file `test_fetch_google_trends.py` with a `test_invalid_keyword_validation` function containing the required ValueError assertion is present; the claim provides no artifact or code to verify. The required test implementation is missing.
- **T012a** — The `fetch_gdelt.py` script contains only a placeholder implementation and never writes any data to `data/raw/gdelt_events.csv`, which is also missing. Consequently the required fetch logic, CSV output, and full retry‑backoff behavior are not present. The task must be completed by implementing real GDELT queries, aggregating `EventCount` for negative sentiment, and saving the results to the specified CSV file.
- **T012b** — declared artifact(s) missing/empty/invalid: data/raw/gdelt_events.csv, data/raw/.checksums.json
- **T012c** — declared artifact(s) missing/empty/invalid: data/raw/gdelt_events.csv
- **T013a** — The repository contains `fetch_google_trends.py` with retry logic, but the script never creates the required `data/raw/google_trends.csv` (the file is missing) and the shown code does not include any CSV‑writing step. Hence the primary output artifact demanded by the task is absent.
- **T013b** — declared artifact(s) missing/empty/invalid: data/raw/google_trends.csv, data/raw/.checksums.json
- **T013c** — declared artifact(s) missing/empty/invalid: data/raw/google_trends.csv
- **T014a** — No `test_fetch_error_handling.py` file (or the specific `test_500_exit_code` test) was found in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/`, nor any code showing the required `responses` mock, log verification, and non‑zero exit assertion. The required test artifact is missing.
- **T020a** — declared artifact(s) missing/empty/invalid: data/processed/stationarity_check.csv
- **T020b** — declared artifact(s) missing/empty/invalid: data/processed/stationarity_check.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/aligned_timeseries.csv, data/processed/stationarity_check.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/aligned_timeseries.csv
