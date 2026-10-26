# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/ag_news.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/ag_news.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 2 command(s) failed: python src/data/download.py --output-dir data/raw/ (rc=1); python src/data/preprocess.py  --raw-dir data/raw/  --output data/processed/memory_nodes.parquet (rc=1); 11 declared deliverable(s) absent: data/processed/faiss_index_mapping.json; data/processed/memory_nodes.parquet; data/processed/validation_queries.json

## Failing / missing run-book commands

- python src/data/download.py --output-dir data/raw/ -> rc=1
**32 - 1\nTraceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/download.py", line 187, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/download.py", line 180, in main
    download_ego4d(Path(args.output_dir))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/download.py", line 133, in download_ego4d
    embedding = _deterministic_embedding(text)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/download.py", line 56, in _deterministic_embedding
    rng = np.random.RandomState(seed)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "numpy/random/mtrand.pyx", line 186, in numpy.random.mtrand.RandomState.__init__
  File "numpy/random/_mt19937.pyx", line 168, in numpy.random._mt19937.MT19937._legacy_seeding
  File "numpy/random/_mt19937.pyx", line 182, in numpy.random._mt19937.MT19937._legacy_seeding
ValueError: Seed must be between 0 and 2**32 - 1

- python src/data/preprocess.py  --raw-dir data/raw/  --output data/processed/memory_nodes.parquet -> rc=1
", line 114, in main
    build_memory_nodes_parquet(Path(args.raw_dir), Path(args.output))
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/preprocess.py", line 85, in build_memory_nodes_parquet
    embeddings = _load_embeddings(raw_dir)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/preprocess.py", line 43, in _load_embeddings
    raise RuntimeError(f"Embeddings file not found at {embeddings_path}")
RuntimeError: Embeddings file not found at data/raw/embeddings.npy

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/preprocess.py", line 120, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1064-llmxive-follow-up-extending-lightmem-ego/src/data/preprocess.py", line 116, in main
    raise RuntimeError(f"Preprocessing failed: {e}") from e
RuntimeError: Preprocessing failed: Embeddings file not found at data/raw/embeddings.npy


## Declared deliverables still missing

- data/processed/faiss_index_mapping.json
- data/processed/memory_nodes.parquet
- data/processed/validation_queries.json
- data/results/evaluation_metrics.json
- data/results/evaluation_queries.json
- data/results/evaluation_report.json
- data/results/mcnemar_test.json
- data/results/optimal_parameters.json
- data/results/validation_run.json
- figures/latency_vs_age.png
- figures/long_term_accuracy.png

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/faiss_index_mapping.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/processed/memory_nodes.parquet` is declared but was NOT written. Scripts referencing it:
    - `src/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/memory_nodes.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_metrics.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_queries.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/evaluation_report.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/mcnemar_test.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/optimal_parameters.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `data/results/validation_run.json` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/latency_vs_age.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
- `figures/long_term_accuracy.png` is declared but NOT written and NO script references it — create the script that produces it and add it to quickstart.md.
