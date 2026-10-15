# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…pipeline:      1. Ensure simulated AMT data exists.     2. Load the…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…-------------     # 1‑2. Simulated AMT data (still required for birt…”
- code/simulate_amt.py: synthetic/fake INPUT data not authorized by the spec — “…out_path)     log.info(f"Simulated AMT data written to {out_path}")…”

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/simulated_amt.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…pipeline:      1. Ensure simulated AMT data exists.     2. Load the…”; code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…-------------     # 1‑2. Simulated AMT data (still required for birt…”; code/simulate_amt.py: synthetic/fake INPUT data not authorized by the spec — “…out_path)     log.info(f"Simulated AMT data written to {out_path}")…”; every produced artifact is gitignored (data/raw/simulated_amt.parquet) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 5 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step ingest (rc=1); python code/main.py --step analyze (rc=1); 2 declared deliverable(s) absent: data/final/permutation_results.csv; data/final/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1
"
2026-10-15 16:20:13,905 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/datasets/matthewfranglen/lastfm-1k/tree/8613d9f34c914629843ad4ac9fa02bee93815b1a?recursive=false&expand=false "HTTP/1.1 200 OK"
2026-10-15 16:20:13,953 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/matthewfranglen/lastfm-1k/resolve/8613d9f34c914629843ad4ac9fa02bee93815b1a/dataset_infos.json "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 28, in main
    run_thin_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 16, in run_thin_pipeline
    data_ingestion.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 137, in main
    "user_id": rec["user_id"],
               ~~~^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'

- python code/main.py --step ingest -> rc=1
"
2026-10-15 16:20:15,668 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/datasets/matthewfranglen/lastfm-1k/tree/8613d9f34c914629843ad4ac9fa02bee93815b1a?recursive=false&expand=false "HTTP/1.1 200 OK"
2026-10-15 16:20:15,713 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/matthewfranglen/lastfm-1k/resolve/8613d9f34c914629843ad4ac9fa02bee93815b1a/dataset_infos.json "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 28, in main
    run_thin_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 16, in run_thin_pipeline
    data_ingestion.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 137, in main
    "user_id": rec["user_id"],
               ~~~^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'

- python code/main.py --step analyze -> rc=1
"
2026-10-15 16:20:17,351 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/datasets/matthewfranglen/lastfm-1k/tree/8613d9f34c914629843ad4ac9fa02bee93815b1a?recursive=false&expand=false "HTTP/1.1 200 OK"
2026-10-15 16:20:17,404 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/matthewfranglen/lastfm-1k/resolve/8613d9f34c914629843ad4ac9fa02bee93815b1a/dataset_infos.json "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 28, in main
    run_thin_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 16, in run_thin_pipeline
    data_ingestion.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 137, in main
    "user_id": rec["user_id"],
               ~~~^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'

- python code/main.py --step verify -> rc=1
"
2026-10-15 16:20:18,969 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/datasets/matthewfranglen/lastfm-1k/tree/8613d9f34c914629843ad4ac9fa02bee93815b1a?recursive=false&expand=false "HTTP/1.1 200 OK"
2026-10-15 16:20:19,016 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/matthewfranglen/lastfm-1k/resolve/8613d9f34c914629843ad4ac9fa02bee93815b1a/dataset_infos.json "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 28, in main
    run_thin_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 16, in run_thin_pipeline
    data_ingestion.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 137, in main
    "user_id": rec["user_id"],
               ~~~^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'

- python code/main.py --full-run -> rc=1
"
2026-10-15 16:20:20,785 - httpx2 - INFO - HTTP Request: GET https://huggingface.co/api/datasets/matthewfranglen/lastfm-1k/tree/8613d9f34c914629843ad4ac9fa02bee93815b1a?recursive=false&expand=false "HTTP/1.1 200 OK"
2026-10-15 16:20:20,827 - httpx2 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/matthewfranglen/lastfm-1k/resolve/8613d9f34c914629843ad4ac9fa02bee93815b1a/dataset_infos.json "HTTP/1.1 404 Not Found"
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 28, in main
    run_thin_pipeline()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 16, in run_thin_pipeline
    data_ingestion.main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 137, in main
    "user_id": rec["user_id"],
               ~~~^^^^^^^^^^^
TypeError: string indices must be integers, not 'str'


## Declared deliverables still missing

- data/final/permutation_results.csv
- data/final/sensitivity_analysis.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
