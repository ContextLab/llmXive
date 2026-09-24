# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T007b** — declared artifact(s) missing/empty/invalid: src/utils/stats.py
- **T008** — No code, configuration file, or documentation for a global logger with both file and console handlers was provided; the evidence consists only of the task description and project spec, which do not demonstrate that the required logging infrastructure has been implemented. The implementer must supply the actual logger setup (e.g., a Python module configuring `logging`, a config file, or similar) to satisfy T008.
- **T009** — No artifact (e.g., a script, notebook, Dockerfile, or documentation) was provided that actually sets `os.environ["CUDA_VISIBLE_DEVICES"] = ""` or otherwise enforces CPU‑only execution. Without such evidence the requirement is not demonstrated. The implementer must add a concrete file or code snippet showing the environment variable being set.
- **T011b** — declared artifact(s) missing/empty/invalid: src/data/verify_labels.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/download.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/embed.py, data/embeddings.parquet
- **T015** — No code, test, or documentation showing that dimensionality validation logic was added to the encoder output pipeline is present. The required artifact—a change that checks the shape of the `AudioEmbedding` before saving and raises an error or handles mismatches—is missing, so the task is not satisfied.
- **T016** — No code, script, or log files were presented that record per‑batch execution time or peak RAM usage during the embedding extraction phase. Consequently, the required resource‑logging functionality is not demonstrated. The implementer must add and provide the logging implementation (e.g., timestamps, batch‑level timing, memory‑usage metrics) and show the resulting logs or code excerpts.
- **T020** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T021** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T022** — declared artifact(s) missing/empty/invalid: src/models/train.py
- **T022b** — declared artifact(s) missing/empty/invalid: src/models/train.py, data/anomaly_scores.parquet
- **T023** — The submission provides no code, data file, or computed result showing a Gaussian‑distributed synthetic noise vector of the same dimensionality as the embeddings, nor any reported distance between that noise and the benign mean μ₍benign₎. Without these artifacts, the task requirement is not satisfied.
- **T024** — declared artifact(s) missing/empty/invalid: results/predictions.csv
- **T027b** — The required input `data/anomaly_scores.parquet` does not exist, and the expected output `results/correlation.json` was never created. Moreover, the provided `src/models/eval.py` snippet shows only loading functions and no implementation of Pearson correlation, hypothesis testing, threshold verification, or JSON saving. The task therefore remains unfinished.
- **T029** — The `results/report.md` file exists and contains the required metrics, but the required `results/resource_log.json` file is missing from the repository. The task is not fully satisfied until the JSON resource log is present.
- **T032** — The submission provides only the task description and no code, script, or documentation showing that a CLI argument parser for sampling size and batch size was added. There is no artifact (e.g., a Python file using argparse or click) to verify the required functionality. The missing implementation must be supplied for the claim to be valid.
- **T033** — No `quickstart.md` file or its contents are present in the provided evidence, so the required documentation with step‑by‑step instructions for running the full pipeline on a free‑tier runner is missing. The implementer must add a non‑empty `quickstart.md` that covers setup, dependencies, CPU‑only execution, and how to invoke each pipeline stage.
