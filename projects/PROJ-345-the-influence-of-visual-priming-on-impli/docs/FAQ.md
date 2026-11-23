# Frequently Asked Questions

## Q: Why does the pipeline halt when human-rated ambiguity is missing?
A: Per Plan Critical Design Change #2, synthetic derivation of ambiguity is prohibited. The system halts to ensure scientific rigor.

## Q: Can I use synthetic data for testing?
A: No. All data must come from real sources (OSF/HF). Synthetic data is not allowed.

## Q: How do I handle large datasets (>7GB)?
A: Use the chunked processing modules (`code/data/chunked_processor.py`, `code/models/lmm_chunked.py`).

## Q: What does "Associational analysis only" mean?
A: It means the findings are correlational and do not imply causality. This is a requirement for all reports.

## Q: How do I fix a PII leak?
A: Run `python code/main.py --scan-pii` to identify the leak. Remove the PII from the source data and re-run the pipeline.

## Q: Can I change the random seed?
A: The seed is pinned in `code/config.py` for reproducibility. Do not change it unless you have a specific reason.

## Q: What if the LMM model fails to converge?
A: The system automatically retries with alternative optimizers. Check `state/model_convergence_metrics.json` for details.

## Q: How do I add a new dataset?
A: Update `code/data/ingest.py` with the new OSF/HF URL and re-run the ingestion script.
