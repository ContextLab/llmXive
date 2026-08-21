# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011e** — declared artifact(s) missing/empty/invalid: data/consent/irb_approved.txt
- **T022b** — No code, configuration, or documentation was provided showing that the session is rejected when IP capture fails, nor any reference to the result of T022b_1. The required implementation artifact is missing.
- **T024a** — The provided `01_preprocess.py` does not contain an implemented `reshape_to_wide(df)` function (or the required assertion), and the expected output file `data/processed/cleaned_data.csv` is absent. Both the core transformation and the resulting CSV are missing, so the task is not satisfied.
- **T024b** — The required artifact `data/processed/cleaned_data.csv` does not exist, and there is no evidence that the script was executed to produce it or that its schema was validated against T024a. The task’s verification steps therefore fail.
- **T046a** — The script `code/analysis/06_power_analysis.py` exists but does not place `numpy.random.seed(42)` and `random.seed(42)` on the first two lines, and it lacks any implementation that computes the minimum detectable effect size for N=250 or writes a JSON file matching the required schema. Moreover, the required data files (`data/raw/submissions.csv` and `data/processed/mock_data.csv`) are absent, so the script cannot run as specified.
- **T046b** — The required output file `data/processed/power_analysis.json` is missing, so the verification step cannot be satisfied. The script exists, but there is no evidence it was run or that the JSON output was generated. The task therefore remains incomplete.
