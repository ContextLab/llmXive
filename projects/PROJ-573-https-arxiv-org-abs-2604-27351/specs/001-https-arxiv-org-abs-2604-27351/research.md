# Research: Heterogeneous Scientific Foundation Model Collaboration Benchmark

## Summary

This research validates dataset availability, model feasibility, and statistical methodology for comparing heterogeneous vs. unified scientific foundation model collaboration pipelines. **Results framed as exploratory associational comparison; causal claims NOT made.**

## Dataset Strategy

| Dataset Type | Required Variables | Verified Source | Status | Notes |
|--------------|-------------------|-----------------|--------|-------|
| Time-series (PhysioNet) | Clinical time-series measurements, ground-truth labels | NO verified source found | ⚠️ BLOCKING GAP | FR-001 references PhysioNet; no verified URL in block. Substitute UCI_HAR (see below). Document domain mismatch in paper. |
| Tabular (UCI) | Tabular features, ground-truth labels | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv | ✅ Available | Use UCI_HAR for time-series validation; additional UCI datasets may be needed for tabular tasks. |
| Tabular (UCI Shopper) | Tabular features, purchase labels | | ✅ Available | Use for tabular modality tasks. |
| Text (PubMed) | Abstracts, classification labels | NO verified source found | ⚠️ BLOCKING GAP | FR-001 references PubMed; no verified URL in block. Substitute DROP/MUST (see below). Document domain mismatch in paper. |
| Text (MUST) | Text data, tool-calling labels | | ✅ Available | Use for text modality tasks. |
| Text (MUSTC) | Text data, translation labels | | ✅ Available | Use for text modality tasks. |
| Text (DROP) | Text QA, answers | | ✅ Available | Use for text QA tasks. |
| Transaction Logs (US-100K) | Transaction features, labels | https://huggingface.co/datasets/AMLGentex/us_K_difficult/resolve/main/tx_log.csv<br>A transaction log dataset (tx_log.csv, AMLGentex, Hugging Face) | ✅ Available | Use for tabular transaction tasks. |

### Dataset Gap Analysis (Blocking)

| Required Dataset | Gap Description | Impact | Resolution Required |
|------------------|-----------------|--------|---------------------|
| PhysioNet time-series | NO verified source in block | Blocking for FR-001 | Substitute UCI_HAR; document clinical domain mismatch in paper limitations |
| PubMed abstracts | NO verified source in block | Blocking for FR-001 | Substitute DROP/MUST; document scientific abstract domain mismatch in paper limitations |
| FR-010 download retry target | NO verified source | Non-blocking | Retry logic applies to all downloads; no specific dataset required |

**DECISION**: Proceed with verified datasets (UCI_HAR, UCI Shopper, MUST, MUSTC, DROP, US-100K) for initial benchmark. Document PhysioNet and PubMed gaps in paper as "dataset availability limitations". Do NOT fabricate URLs. **Results framed as exploratory; domain mismatch acknowledged.**

### Task-to-Dataset Mapping

| Task Group | Datasets Used | Modalities | Count |
|------------|---------------|------------|-------|
| Time-series + Tabular | UCI_HAR, UCI Shopper | time-series, tabular | multiple |
| Time-series + Text | UCI_HAR, DROP | time-series, text | multiple classes |
| Tabular + Text | UCI Shopper, MUST | tabular, text | multiple |
| Time-series + Tabular + Text | UCI_HAR, UCI Shopper, DROP | all listed | 2 |
| **Total** | | | **20** |

**Task Construction Methodology**: Tasks are artificially constructed by combining independent datasets to create multi-modal prediction problems. This is documented as a limitation for external validity. Tasks do not necessarily reflect naturally-occurring scientific workflows but enable controlled comparison of architecture conditions.

## Model Inventory

| Model Type | Candidate | Size | CPU-Feasible | Status |
|------------|-----------|------|--------------|--------|
| TimeSeries-Transformer | TimeSeries-Transformer (HF) | <1 GB (assumed, Phase 0.5 verification required) | ✅ Yes (assumed) | Must verify weight size before Phase 2; fallback to smaller variant if >1 GB |
| TabPFN | TabPFN-small | <1 GB | ✅ Yes | Default choice for tabular; verified CPU-compatible |
| Distilled LLM | distilled-llm-7B (CPU) or smaller | <1 GB (Phase 0.5 verification required) | ✅ Yes (if <1 GB) | Must verify weight size; fallback to smaller model if needed |

**DECISION**: Use TabPFN-small for tabular (CPU-tractable, <1 GB). For time-series and text, verify HF model weights in Phase 0.5 before implementation. If any model >1 GB, substitute with smaller distilled variant and document in paper.

### Model Selection Justification

**Modality-Specific vs. Modality-Optimized Distinction**:
- **Modality-Specific**: Native architecture designed for specific data type (e.g., TimeSeries-Transformer with temporal attention, TabPFN with tabular-specific inductive biases)
- **Modality-Optimized**: General architecture adapted for modality (e.g., standard transformer fine-tuned on tabular data)

Selected models are **modality-specific** by design: TimeSeries-Transformer uses temporal positional encodings; TabPFN uses tabular-specific attention patterns; distilled LLM uses language-specific tokenization. This supports the scientific claim that modality-specific expertise improves collaboration.

## Statistical Methodology

| Component | Method | Rationale | FR/SC Mapping |
|-----------|--------|-----------|---------------|
| Primary test | Paired t-test across 20 tasks | Standard for comparing two conditions with paired observations | FR-007, FR-011, SC-005 |
| Significance threshold | α ≤ 0.05 | Convention in scientific field | FR-011 |
| Effect size | Cohen's d (paired) | Quantifies magnitude of difference; PRIMARY outcome | FR-014 |
| Confidence interval | 95% bootstrap CI (1000 resamples) | Non-parametric, accounts for task dependency | FR-007, FR-014, Constitution VII |
| Alternative test | Wilcoxon signed-rank test | Non-parametric alternative for normality violations | FR-014 |
| Multiple comparison | Not applicable (single paired comparison) | Only one primary comparison (heterogeneous vs. unified) | N/A |
| Sample size | 20 tasks | Spec-defined; power limitation acknowledged | SC-004 (5 seeds) |

### Observational Comparison (NOT Causal)

**Important**: This study compares two experimental conditions (heterogeneous vs. unified) but does NOT randomize tasks or control confounders. Claims are framed as **associational** only. The observed difference measures the association between architecture condition and performance, not causal effect.

### Power & Limitations

| Consideration | Status |
|---------------|--------|
| Sample size justification | 20 tasks defined in spec; power analysis deferred (no pilot data) |
| Power limitation | Acknowledged in paper; results are **exploratory**; effect size primary outcome |
| Causal inference | Observational comparison; claims framed as associational only |
| Measurement validity | Use ground-truth labels from original datasets (Constitution II) |
| Predictor collinearity | N/A (comparing conditions, not predictor effects) |
| Task selection bias | Stratify tasks by difficulty; blocking analysis in statistical tests |

### Power Analysis

With a set of tasks and multiple seeds, statistical power is limited. Without pilot data, cannot estimate effect size variance. **Primary outcome is effect size with 95% CI; p-value threshold secondary.** Paper will report:
- Cohen's d effect size
- 95% bootstrap CI for effect size
- Paired t-test p-value (exploratory)
- Acknowledgment of power limitation

## Translation Fidelity Validation

The unified condition converts time-series/tabular to text before LLM inference. This introduces potential information loss confound. **Validation approach**:

1. **Reconstruction correlation**: For a sample of inputs, compute correlation between original numeric features and statistics extracted from translated text representation
2. **Threshold**: Correlation ≥ 0.95 required for acceptable fidelity (documented in translation.py)
3. **Reporting**: If correlation < 0.95, document in paper as "translation fidelity limitation"

This ensures observed performance differences reflect architecture (not translation artifacts).

## Computational Feasibility

| Component | Requirement | Feasible Method |
|-----------|-------------|-----------------|
| Model inference | CPU-only, ≤5 min/task | Distilled models; no fine-tuning; zero-shot/few-shot |
| Dataset size | ≤5 GB total | Use subset of verified datasets; sample if needed |
| Runtime | ≤4 hours total | 20 tasks × 5 min max = 100 min; overhead for download/reporting |
| RAM | ≤7 GB | Load one model at a time; stream data |
| Disk | ≤14 GB | Dataset + processed data + logs |

**DECISION**: If any component exceeds limits, document in paper as "compute-constrained approximation" and report actual runtime/memory measurements.

## Compute Feasibility Decision/Rationale

| Constraint | Decision | Rationale |
|------------|----------|-----------|
| GPU requirement | None | Spec explicitly states GPU out of scope for baseline |
| Model training | Zero-shot only | No fine-tuning; pre-trained models only |
| Quantization | None | No 8-bit/4-bit; use default precision for CPU compatibility |
| Dataset sampling | As needed | If full dataset >5 GB, sample to fit RAM/disk limits |
| Parallelization | Limited | 2 CPU cores; sequential task execution or 2-task parallel |

**Risk**: If models exceed 1 GB or inference exceeds 5 minutes, fallback to smaller variants or sampled data. Document all deviations in paper.

## Constitution Compliance Notes

| Principle | Compliance Action |
|-----------|-------------------|
| I. Reproducibility | Pin all seeds, versions; requirements.txt at Phase 3.5 |
| II. Verified Accuracy | Use ONLY verified dataset URLs; Reference-Validator gate |
| III. Data Hygiene | Checksum all data; no in-place modification |
| IV. Single Source of Truth | All statistics trace to `data/` rows; StatisticalSummary persisted to `data/statistical_summary.yaml` |
| V. Versioning Discipline | Content hashes in `state/` |
| VI. Modality-Specific Processing | Log text conversion; retain quantitative info; validate translation fidelity |
| VII. Rigorous Comparative Evaluation | Paired t-test + bootstrap CI + Wilcoxon |

## References (Verified Only)

| Dataset | URL | Verified |
|---------|-----|----------|
| UCI_HAR | https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv | ✅ |
| UCI Shopper | https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet | ✅ |
| MUST (qwen3.5) | https://huggingface.co/datasets/Mustafaege/qwen3.5-toolcalling-v2/resolve/main/data/test-00000-of-00001.parquet | ✅ |
| MUSTC | https://huggingface.co/datasets/kudo-research/mustc-en-es-text-only/resolve/main/data/dev-00000-of-00001.parquet | ✅ |
| DROP | https://huggingface.co/datasets/ucinlp/drop/resolve/main/data/train-00000-of-00001.parquet | ✅ |
| US-100K (difficult) | https://huggingface.co/datasets/AMLGentex/us_100K_difficult/resolve/main/tx_log.csv | ✅ |
| US-100K (easy) | https://huggingface.co/datasets/AMLGentex/us_100K_easy/resolve/main/tx_log.csv | ✅ |

**Note**: PhysioNet and PubMed have NO verified sources in the provided block. These gaps are documented and will be addressed in paper limitations as domain mismatch.