# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011b** — No download script, command log, or FASTQ files are present; the implementer provided no artifact demonstrating that raw FASTQ files were retrieved from NCBI SRA for the target study accession. The required output (downloaded FASTQ data or reproducible code to do so) is missing.
- **T011c** — No code, workflow, or resulting OTU table was presented. The claim that the 16S processing pipeline was run and an OTU table generated is unsupported by any artifact, so the required output is missing.
- **T011d** — No merge script, function, or resulting merged dataset was presented; there is no file or code that demonstrates merging the OTU table with serology metadata on `subject_id`. Consequently, the required artifact is missing, so the task is not satisfied.
- **T013b** — No code, data, analysis results, or documentation for “LOD Handling Sensitivity Analysis” were provided; the only evidence shown is the feature specification for microbiome‑influenza correlation, which does not address LOD handling. The required artifact (implementation and any output demonstrating sensitivity analysis) is missing.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/filtered_data.csv
- **T017** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T020a** — declared artifact(s) missing/empty/invalid: data/processed/cleared_default.csv
- **T020b** — The submission contains only the task description and project specifications; there are no code, data files, results tables, or figures showing CLR‑transformed data with pseudocounts 1e‑4, 1e‑6, 1e‑8, nor any calculated Jaccard Index values for the sensitivity analysis. These required artifacts are missing, so the task is not satisfied.
- **T020c** — The required input file `data/processed/filtered_no_zero_var.csv` does not exist, and the provided `code/02_preprocess.py` is truncated (ends abruptly with “l”) and contains no function that computes the Shannon diversity index. Both the data source and the necessary implementation are missing.
