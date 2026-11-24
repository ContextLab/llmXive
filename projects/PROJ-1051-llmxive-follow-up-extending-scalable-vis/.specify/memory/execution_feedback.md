# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/raw/docvqa/docvqa/000000.json, data/raw/docvqa/docvqa/000000.png, data/raw/docvqa/docvqa/000001.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/raw/docvqa/docvqa/000000.json, data/raw/docvqa/docvqa/000000.png, data/raw/docvqa/docvqa/000001.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 3 command(s) failed: python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml (rc=1); python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu (rc=1); python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa (rc=-1)

## Failing / missing run-book commands

- python -m src.data.preprocess  --input-dir data/raw/layout_corpus  --output-parquet data/processed/document_pairs.parquet  --schema contracts/documentpair.schema.yaml -> rc=1

2026-10-16 16:13:46,286 ERROR __main__: Preprocessing failed: [Errno 2] No such file or directory: 'contracts/documentpair.schema.yaml'

- python -m src.data.latent_generator  --input-parquet data/processed/document_pairs.parquet  --output-parquet data/processed/document_pairs_with_latent.parquet  --encoder-name resnet18  --device cpu -> rc=1

2026-10-16 16:13:47,963 ERROR __main__: Latent generation failed: Unable to read Parquet file 'data/processed/document_pairs.parquet': [Errno 2] No such file or directory: 'data/processed/document_pairs.parquet'

- python -m src.data.download  --dataset-name docvqa  --output-dir data/raw/docvqa -> rc=-1
    | 397/10537 [01:18<34:27,  4.90it/s]Saving DocVQA:   4%|▍         | 399/10537 [01:19<26:53,  6.28it/s]Saving DocVQA:   4%|▍         | 401/10537 [01:19<22:03,  7.66it/s]Saving DocVQA:   4%|▍         | 403/10537 [01:19<19:04,  8.85it/s]Saving DocVQA:   4%|▍         | 405/10537 [01:19<16:43, 10.09it/s]Saving DocVQA:   4%|▍         | 407/10537 [01:19<15:08, 11.15it/s]Saving DocVQA:   4%|▍         | 409/10537 [01:19<16:06, 10.48it/s]Saving DocVQA:   4%|▍         | 411/10537 [01:20<18:44,  9.01it/s]Saving DocVQA:   4%|▍         | 413/10537 [01:21<37:14,  4.53it/s]Saving DocVQA:   4%|▍         | 414/10537 [01:21<45:19,  3.72it/s]Saving DocVQA:   4%|▍         | 415/10537 [01:22<52:53,  3.19it/s]Saving DocVQA:   4%|▍         | 417/10537 [01:22<36:37,  4.60it/s]Saving DocVQA:   4%|▍         | 419/10537 [01:22<28:20,  5.95it/s]Saving DocVQA:   4%|▍         | 421/10537 [01:22<22:04,  7.64it/s]Saving DocVQA:   4%|▍         | 423/10537 [01:22<18:34,  9.07it/s]Saving DocVQA:   4%|▍         | 425/10537 [01:22<15:42, 10.73it/s]Saving DocVQA:   4%|▍         | 427/10537 [01:22<13:46, 12.24it/s]Saving DocVQA:   4%|▍         | 429/10537 [01:22<12:23, 13.60it/s]
[TIMEOUT after 120s]
