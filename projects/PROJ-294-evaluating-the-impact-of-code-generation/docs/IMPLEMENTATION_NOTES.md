# Implementation Notes

## Version History

- **v1.0 (Current)**: Full pipeline implementation including sensitivity analysis and statistical rigor.

## Key Implementation Decisions

### 1. Stratified Sampling (T011)
We use quartile-based stratification on human pass rates to ensure the dataset covers easy, medium, and hard tasks. This prevents bias towards simple tasks that all models can solve.

### 2. Sensitivity Analysis (T028-T029)
The pipeline attempts to load `CodeLlama-3B` locally first. If memory constraints prevent this, it falls back to the HuggingFace Inference API for `CodeLlama-7B`. If both fail, it proceeds with the primary `CodeGen-350M` model, logging a warning.

### 3. Metric Deferral (T042)
Coverage measurement is expensive and prone to timeouts. We record `[deferred]` if coverage fails but still record the binary pass rate. This ensures we maximize the dataset size for Wilcoxon tests on pass rate while having partial data for coverage.

### 4. Statistical Rigor (T020-T025)
We do not rely on a single test. Continuous metrics use Wilcoxon (paired) and Spearman (correlation). Binary metrics use McNemar. We also perform Permutation tests to validate the robustness of our coverage findings.

### 5. Integrity Verification (T005, T006)
Every downloaded file and generated artifact is hashed. The `state/artifact_hashes.yaml` file tracks these to ensure reproducibility and detect data corruption.

## Known Limitations

- **RAM Constraints**: Local generation of large models (7B) is not supported on standard CPU environments without quantization. The pipeline handles this via the API fallback.
- **Execution Time**: Full coverage analysis on 50+ tasks can take significant time. The `analyze_metrics.py` script includes a timeout mechanism.
- **API Rate Limits**: If the HuggingFace API is used for sensitivity analysis, rate limits may cause delays. The script includes retry logic.

## Troubleshooting

### "ModuleNotFoundError"
Ensure all dependencies in `code/requirements.txt` are installed:
```bash
pip install -r code/requirements.txt
```

### "SHA256 Mismatch"
The download script verifies file integrity. If a mismatch occurs, the script will delete the corrupted file and re-download.

### "CUDA Out of Memory"
The pipeline is designed for CPU execution. If running on GPU, ensure the model loading code in `generate_code.py` is configured to use the correct device.

### "Citation Validation Failed"
The `validate_citations.py` script checks all URLs in the final report. If a link is broken, the report generation will log a warning but proceed.
