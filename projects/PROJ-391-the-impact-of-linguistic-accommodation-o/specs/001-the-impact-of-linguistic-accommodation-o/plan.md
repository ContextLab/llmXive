# Implementation Plan: Association between Linguistic Accommodation and Perceived Empathy

**Branch**: `001-linguistic-accommodation-empathy` | **Date**: 2024-05-21 | **Spec**: `specs/001-the-impact-of-linguistic-accommodation-o/spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-linguistic-accommodation-empathy/spec.md`

## Summary

The project investigates the **association** between linguistic accommodation (lexical overlap, syntactic similarity) and **perceived empathy** in AI‑assistant responses. Because no verified public dataset contains both AI‑assistant turns and explicit empathy ratings, we will **collect a small, ethically‑approved human‑rated validation dataset** (n ≥ 30) of AI‑assistant replies. DailyDialog will be used to compute accommodation metrics on a large corpus of human‑human dialogues, serving as a proxy for AI‑assistant style; the collected dataset will provide the required empathy scores for rigorous analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.2`, `numpy==1.26.4`, `scikit-learn==1.5.0`, `scipy==1.14.0`, `spacy==3.7.4`, `nltk==3.9.1`, `matplotlib==3.9.2`, `seaborn==0.13.2`, `datasets==2.19.1`, `pyyaml==6.0.2`, `gensim==4.3.2`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `outputs/reports`)  
**Testing**: `pytest` (unit tests for metrics, integration test for pipeline)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM) – **CPU‑only** execution.  
**Performance Goals**: Full pipeline ≤ 6 h, RAM < 6 GB, no GPU.  

## Constitution Check

| Principle | Status | Action / Verification |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` pins versions; random seeds (42) fixed; data checksums recorded. |
| **II. Verified Accuracy** | **PASS** | All citations verified; DailyDialog source cited (Yan et al., 2017). |
| **III. Data Hygiene** | **PASS** | Raw data immutable; all transformations produce new files; PII scan active. |
| **IV. Single Source of Truth** | **PASS** | Every statistic in `outputs/reports/` traces back to a row in `data/processed/final_dataset.csv`. |
| **V. Versioning** | **PASS** | Content hashes updated in `state/`. |
| **VI. Human Subject Ethics** | **PASS** | New human‑rated validation subset will be collected under IRB approval; informed consent obtained; data stored anonymously. |
| **VII. Statistical Validity** | **PASS** | Bonferroni correction for the four primary tests; power analysis documented; bootstrap convergence enforced. |

## Project Structure

```text
specs/001-the-impact-of-linguistic-accommodation-o/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── dataset_schema.schema.yaml
│   └── output.schema.yaml
```

```text
projects/PROJ-391-the-impact-of-linguistic-accommodation-o/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 00_collect_human_empathy.py          # FR‑010
│   ├── 01_ingest_and_preprocess.py         # FR‑008
│   ├── 02_map_emotion_score.py
│   ├── 03_compute_metrics.py               # FR‑001, FR‑002, FR‑008
│   ├── 04_define_sampling_strategy.py      # prepares sampling for sensitivity analysis
│   ├── 05_sensitivity_analysis.py          # FR‑009 (mandatory)
│   ├── 06_generate_topics.py                # FR‑007 (LDA)
│   ├── 07_analyze_correlations.py          # FR‑004, FR‑005, FR‑006, SC‑001‑005
│   ├── 08_regression_control.py            # FR‑007 (regression with covariates)
│   ├── 09_manual_validation.py              # FR‑010 (human rating protocol)
│   └── utils.py
├── data/
│   ├── raw/
│   │   ├── daily_dialog/
│   │   └── human_empathy/                  # collected AI‑assistant dialogues + ratings
│   └── processed/
│       └── final_dataset.csv
├── outputs/
│   ├── reports/
│   │   ├── bootstrap_results.json
│   │   ├── correlation_summary.json
│   │   ├── sensitivity_results.json
│   │   ├── regression_summary.json
│   │   └── validation_summary.json
│   └── figures/
│       └── scatter_plot.png
├── tests/
│   ├── unit/
│   │   ├── test_utils.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── contracts/
        └── dataset_schema.yaml
```

## Complexity Tracking

| Complexity | Why Needed (FR/SC) | Simple Alternative Rejected Because |
| :--- | :--- | :--- |
| **Human‑rated Validation Subset** | FR‑010, SC‑003 (human benchmark) | Skipping human ratings would violate the explicit validation requirement. |
| **Bootstrap Convergence** | FR‑006, SC‑001, SC‑002 | Fixed iteration caps would break the strict CI‑width condition. |
| **Bonferroni Scope** | FR‑005, SC‑005 | Ambiguous correction scope would risk under‑correction. |
| **Sensitivity Analysis** | FR‑009 | Optional analysis would leave construct validity unchecked. |
| **Topic Modeling (LDA)** | FR‑007, SC‑002 | Using raw topic labels would not meet the specified k = 10 LDA requirement. |
| **Task Ordering** | All phases depend on prior data availability | Circular dependencies would cause runtime failures. |
| **Power Analysis** | SC‑001, SC‑002 | Assuming adequacy without calculation could render study under‑powered. |
| **VIF Checks** | FR‑007 | Ignoring multicollinearity would bias regression estimates. |

## Implementation Phases (Tasks)

| Phase | Script | FR/SC Addressed | Description |
| :--- | :--- | :--- | :--- |
| 0a | `00_collect_human_empathy.py` | FR‑010, Principle VI | Recruit ≥30 human raters, present AI‑assistant responses, collect 1‑5 empathy Likert ratings, store with consent metadata. |
| 0b | `01_ingest_and_preprocess.py` | FR‑008 | Download DailyDialog (verified URL), normalize text (Unicode NFKC), drop empty turns. |
| 1 | `02_map_emotion_score.py` | FR‑003 | Apply emotion‑to‑Likert mapping for DailyDialog; flag records lacking emotion. |
| 2 | `03_compute_metrics.py` | FR‑001, FR‑002, FR‑008 | Compute lexical Jaccard, POS Jaccard, sentence‑length variance; also compute dependency Jaccard for sensitivity. |
| 3 | `04_define_sampling_strategy.py` | – | If total runtime > 4 h, define deterministic [deferred] random sample; writes `sampling_config.json`. |
| 4 | `05_sensitivity_analysis.py` | FR‑009 | Compare POS‑based vs. dependency‑based similarity; mandatory, no opt‑out. |
| 5 | `06_generate_topics.py` | FR‑007 | Fit LDA (k = 10) on all processed dialogues, assign dominant `lda_topic_id`. |
| 6 | `07_analyze_correlations.py` | FR‑004, FR‑005, FR‑006, SC‑001‑005 | Pearson & Spearman tests; Bonferroni α = 0.0125 for four primary tests; adaptive bootstrap until CI < 0.01 (no early stop). |
| 7 | `08_regression_control.py` | FR‑007 | Linear regression of empathy rating on accommodation metrics controlling for `word_count` and `lda_topic_id`; residualize topics, check VIF (< 5). |
| 8 | `09_manual_validation.py` | FR‑010 (validation of proxy) | Sample random pairs from the collected human dataset, compute inter‑rater reliability (Cohen’s κ), store in `validation_summary.json`. |

All tasks are ordered so that data is downloaded before any processing, models are fitted before evaluation, and figures are generated before being referenced in any report.

## Compute Feasibility & Rationale

- **Memory**: All datasets (< 2 GB) fit in memory; LDA uses sparse matrices.
- **Bootstrap**: Adaptive loop stops once CI < 0.01; worst‑case safety guard at 50 000 iterations (still within 6 h on CI runner).
- **Risk Mitigation**: If any step exceeds 4 h, the sampling strategy (04) will down‑sample the dataset to keep total runtime ≤ 6 h.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Collect human empathy ratings** | No public dataset provides AI‑assistant empathy scores; ethical collection satisfies FR‑010 and Principle VI. |
| **Use DailyDialog for metric computation** | Large, verified corpus for linguistic accommodation; proxy for AI style after validation. |
| **Bonferroni α = 0.0125** | Four primary hypothesis tests (Pearson/Spearman × lexical/syntactic). |
| **Bootstrap convergence requirement** | FR‑006 mandates CI < 0.01; adaptive loop guarantees compliance. |
| **Mandatory sensitivity analysis** | FR‑009 requires construct validation; dependency metric defined to avoid optional skipping. |
| **LDA topic control** | Meets FR‑007 specification; residualization prevents collider bias. |
| **VIF check** | Ensures regression covariates are not collinear (VIF < 5). |