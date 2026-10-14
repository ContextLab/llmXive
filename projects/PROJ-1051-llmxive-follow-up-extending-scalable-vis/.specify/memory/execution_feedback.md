# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.data.download  --dataset-name publaynet  --output-dir data/raw`
  - script usage: `download.py [-h] --primary-name PRIMARY_NAME --fallback-name`
  - argparse error: `download.py: error: the following arguments are required: --primary-name, --fallback-name`
- run-book command: `python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa`
  - script usage: `download.py [-h] --primary-name PRIMARY_NAME --fallback-name`
  - argparse error: `download.py: error: the following arguments are required: --primary-name, --fallback-name`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.data.download  --dataset-name publaynet  --output-dir data/raw (rc=2); python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu (rc=1)

## Failing / missing run-book commands

- python -m src.data.download  --dataset-name publaynet  --output-dir data/raw -> rc=2

usage: download.py [-h] --primary-name PRIMARY_NAME --fallback-name
                   FALLBACK_NAME
download.py: error: the following arguments are required: --primary-name, --fallback-name

- python -m src.data.preprocess  --input-dir data/raw/publaynet  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/preprocess.py", line 277, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/preprocess.py", line 274, in main
    preprocess_dataset(args.input_dir, args.output_parquet, args.schema_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/preprocess.py", line 201, in preprocess_dataset
    raise RuntimeError(f"Input directory does not exist: {input_dir}")
RuntimeError: Input directory does not exist: /home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/data/raw/publaynet

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name layoutlmv3-base  --device cpu -> rc=1
ne 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 161, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/src/data/latent_generator.py", line 103, in main
    df = pd.read_parquet(args.input_parquet)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 651, in read_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 67, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=2

usage: download.py [-h] --primary-name PRIMARY_NAME --fallback-name
                   FALLBACK_NAME
download.py: error: the following arguments are required: --primary-name, --fallback-name

