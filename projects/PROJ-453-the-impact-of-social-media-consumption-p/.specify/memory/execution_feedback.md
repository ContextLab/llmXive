# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/01_ingest.py (rc=1); python code/02_engineer.py (rc=1); python code/03_model.py (rc=1)

## Failing / missing run-book commands

- python code/01_ingest.py -> rc=1
    requests/models.py", line 1167, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/llmXive/datasets/main/addhealth_wave4_sample.csv

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 249, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 220, in main
    raise e
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 217, in main
    download_data(DATA_URL, raw_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/01_ingest.py", line 106, in download_data
    raise RuntimeError(f"Data fetch failed: {e}") from e
RuntimeError: Data fetch failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/llmXive/datasets/main/addhealth_wave4_sample.csv
- python code/02_engineer.py -> rc=1
    453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 145, in main
    df = load_all_raw_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 56, in load_all_raw_data
    raise FileNotFoundError(f"No cleaned data found in {processed_dir}. Expected *_cleaned.csv")
FileNotFoundError: No cleaned data found in data/processed. Expected *_cleaned.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 179, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 145, in main
    df = load_all_raw_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/02_engineer.py", line 56, in load_all_raw_data
    raise FileNotFoundError(f"No cleaned data found in {processed_dir}. Expected *_cleaned.csv")
FileNotFoundError: No cleaned data found in data/processed. Expected *_cleaned.csv
- python code/03_model.py -> rc=1
    [2026-10-02 21:33:14,488] INFO: Starting Sensitivity Analysis & FDR (T026).
[2026-10-02 21:33:14,488] ERROR: Cleaned data not found at data/processed/participants_cleaned.csv.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/03_model.py", line 296, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-453-the-impact-of-social-media-consumption-p/code/03_model.py", line 247, in main
    raise FileNotFoundError(f"Cleaned data not found: {cleaned_path}")
FileNotFoundError: Cleaned data not found: data/processed/participants_cleaned.csv
- python code/04_visualize.py -> rc=1
    [2026-10-02 21:33:15,656] INFO: Starting visualization pipeline (T036-T039).
[2026-10-02 21:33:15,656] ERROR: File not found: Cleaned data not found at data/processed/participants_cleaned.csv

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `_cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_model.py`, `code/01_ingest.py`, `code/02_engineer.py`, `code/04_visualize.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `_cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_model.py`, `code/01_ingest.py`, `code/02_engineer.py`, `code/04_visualize.py`.

### `data/processed/participants_cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_model.py`, `code/02_engineer.py`, `code/04_visualize.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/participants_cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/03_model.py`, `code/02_engineer.py`, `code/04_visualize.py`.
