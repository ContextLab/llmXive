# Implementation Plan: llmXive cross‑lingual edge‑spectrum analysis

**Branch**: `001-llmxive-crosslingual` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-llmxive-crosslingual/spec.md`

## Summary
This project investigates whether the "edge spectrum" subspace (top-100 singular vectors of the unembedding matrix $W_U$) encodes a universal, language-agnostic prior or language-specific noise. The technical approach involves extracting these subspaces from Llama models, Mistral, and BLOOM, aligning both the vocabulary-side bases ($U$) and the hidden-side bases ($V$) to shared spaces, and quantifying alignment via rotation-invariant subspace similarity. Validation is performed by correlating subspace shifts with WALS typological features and XTREME benchmark performance.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `torch` (CPU), `numpy`, `scipy`, `datasets`, `scikit-learn`, `jsonschema`
- **Storage**: All artifacts under `data/derived/` (raw inputs under `data/raw/`)
- **Testing**: `pytest` for contract validation
- **Target Platform**: GitHub Actions `ubuntu-latest` (CPU-first)
- **Constraints**: $\le$ 7 GB RAM, $\le$ 14 GB disk, $\le$ 6 h total runtime (per FR-004)
- **Scale/Scope**: 3 models, Multiple languages, top-100 singular vectors, $\ge$ 1M tokens per language guard.

## Constitution Check
| Principle | Status | Implementation Detail |
|-----------|--------|------------------------|
| I. Reproducibility | PASS | Fixed random seeds; deterministic HF dataset loaders. |
| II. Verified Accuracy | PASS | External URLs are restricted to the "Verified datasets" block; timestamps recorded. |
| III. Data Hygiene | PASS | Checksums recorded; derived files never overwrite raw data. |
| IV. Single Source of Truth | PASS | All metrics derived from JSON artifacts in `data/derived/`. |
| V. Versioning Discipline | PASS | Artifacts carry content hashes. |
| VI. Cross-Lingual Subspace Isolation | PASS | Separate pipelines for $W_U$ operations per language/model pair (FR-028). |
| VII. Typological Shift Quantification Rigor | PASS | Strict separation between geometric similarity (FR-002) and validation metrics (FR-007). |

## Project Structure

### Documentation (this feature)
```text
specs/001-llmxive-crosslingual/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
```

### Source Code (repository root)
```text
src/
├── pipeline/
│   ├── orchestrator.py     # Main execution flow
│   ├── extraction.py       # SVD, Hidden-Space Alignment, and Vocab Alignment (FR-001, FR-040)
│   ├── frequency.py        # Token streaming and guards (FR-006, FR-034)
│   ├── projection.py       # Pseudo-inverse and mean embeddings (FR-005, FR-036, FR-037)
│   └── stats.py            # Permutation, bootstrap, and correlation (FR-004, FR-015, FR-016)
└── lib/
    └── utils.py            # Hashing, logging, and checksums
tests/
├── contract/               # JSON-Schema validation
└── unit/                   # Math/Logic tests
```

## Implementation Phases & FR/SC Coverage

| Phase | Description | Primary Artifacts (`data/derived/`) | FRs | SCs | Contracts Exercised |
|-------|-------------|--------------------------------------|-----|-----|-------------------|
| **1** | **Subspace Extraction & Alignment**: Load $W_U$; apply language masks (FR-028); perform SVD (FR-001). Align $U$ bases to 11,200-dim shared space (FR-040). Compute Procrustes alignment for $V$ bases across models. | `edge_spectrum.json` | FR-001, FR-014, FR-028, FR-030, FR-033, FR-040 | - | `edge_spectrum.schema.yaml`, `vocab_alignment_warning.schema.yaml` |
| **2** | **Frequency Acquisition**: Stream RedPajama (EN) and Common Crawl (others) (FR-006, FR-009). Enforce $\ge$ 1M token guard (FR-034). Record verification timestamps (FR-012). | `frequency_list_{lang}.json` | FR-006, FR-009, FR-012, FR-034 | - | `frequency_list.schema.yaml` |
| **3** | **Vocab Mapping & Attribution**: Implement shared subword mapping (FR-008). Rank tokens by logit weights (FR-003). Generate geometric baseline (FR-031). | `token_attribution_{model}.json` | FR-003, FR-008, FR-031 | SC-002 | `token_attribution.schema.yaml` |
| **4** | **Mean Embedding Projection**: Compute $W_U^+$ with Tikhonov regularization if condition number $> 10^8$ (FR-037). Compute language mean embeddings $\hat{\mathbf{h}}$ (FR-005) and project $\hat{\mathbf{h}}$ onto the $V$-basis (FR-036). Generate uniform baseline (FR-029). | `mean_embedding_{lang}.json`, `cross_projection.json`, `baseline_report.json` | FR-005, FR-029, FR-036, FR-037 | SC-010 | `mean_embedding.schema.yaml`, `token_shift.schema.yaml` |
| **5** | **Subspace Similarity**: Compute rotation-invariant similarity (principal angles) in aligned $V$-space (FR-002). Compute $\Delta$ similarity vs architecture controls (FR-010). | `similarity_matrix.json`, `similarity_metric.json` | FR-002, FR-010 | SC-001 | `similarity_matrix.schema.yaml`, `similarity_metric.schema.yaml` |
| **6** | **Bootstrap Validation**: Perform $\ge$ 1,000 replicates by resampling $W_U$ rows to generate 95% CIs (FR-015). | `bootstrap_test.json`, `similarity_report.json` | FR-015 | SC-006 | `bootstrap_test.schema.yaml`, `similarity_report.schema.yaml` |
| **7** | **Permutation Testing**: $\ge$ 10,000 iterations. Combined null (within-lang, across-model). Bonferroni $\alpha=0.05/3$ (FR-004). Abort if $> 6$h. | `permutation_test.json`, `control_analysis.json` | FR-004 | SC-003 | `permutation_test.schema.yaml` |
| **8** | **Typological Correlation**: Correlate $\Delta$ similarity and shift vectors with WALS features and XTREME results (FR-007, FR-016). Perform ablation (FR-032). | `validation.json`, `ablation_report.json` | FR-007, FR-016, FR-032 | SC-004, SC-007, SC-009 | `validation.schema.yaml`, `wals_correlation.schema.yaml`, `wals_validation.schema.yaml` |
| **9** | **Feasibility & Integrity**: Run power analysis (FR-035). Record all checksums (FR-038) and runtime metrics. | `feasibility_report.json` | FR-035, FR-038 | SC-005, SC-008 | `feasibility_report.schema.yaml` |
| **10** | **Sensitivity Analysis**: Repeat pipeline without language masks (FR-042) to check for mask-induced bias. | `sensitivity_analysis.json` | FR-042 | - | (Uses existing schemas) |

## Success-Criteria Alignment
- **SC-001**: Subspace similarity reported with bootstrap CI (Phase 5, 6).
- **SC-002**: Token-overlap deviation from geometric baseline (Phase 3).
- **SC-003**: Permutation p-values with Bonferroni flags (Phase 7).
- **SC-004**: Pearson $r$ for WALS/XTREME with 95% CI (Phase 8).
- **SC-005**: Pipeline completes $\le$ 6h on GitHub Actions (Phase 9).
- **SC-006**: 95% CIs via bootstrap sampling of $W_U$ (Phase 6).
- **SC-007**: Correlation analysis on $\ge$ 10 languages (Phase 8).
- **SC-008**: All external URLs checksummed and timestamped (Phase 2, 9).
- **SC-009**: Ablation yields $p > 0.05$ for WALS correlation (Phase 8).
- **SC-010**: Uniform baseline shift is significant $p < 0.05$ (Phase 4, 8).
- **FR-036**: Mean embedding $\hat{\mathbf{h}}$ successfully projected onto $V$-basis across languages (Phase 4).
