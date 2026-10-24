# Implementation Plan: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Branch**: `001-evaluating-code-summarization-bug-localization` | **Date**: 2026-10-23 | **Spec**: `spec.md`  
**Input**: Feature specification from `specs/001-evaluating-the-efficacy-of-code-summarization-bug-localization/spec.md`

## Summary
We will deliver a fully reproducible research pipeline that (1) streams the **open Defects4J v2.0** dataset from HuggingFace, verifies it with SHA‑256 checksums, and extracts a stratified sample of buggy methods; (2) produces three summary conditions (baseline, rule‑based via srcML, LLM‑generated via a CodeLlama model 8‑bit on a Kaggle GPU escape hatch); (3) records interaction logs (simulated for CI, real for the human study) with precise timestamps; (4) runs statistically rigorous analyses (McNemar’s test for accuracy, Linear Mixed‑Effects for speed) with Holm‑Bonferroni correction (α = 0.05) and cluster‑bootstrap confidence intervals. All random seeds are fixed (`42`), all files are validated against JSON‑Schema contracts, and the entire CPU‑only portion runs within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `statsmodels`, `linearmodels`, `datasets`, `srcml` (via subprocess), `torch` (8‑bit CodeLlama on GPU), `scipy`, `pyyaml`  
- **Storage**: CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit, integration, contract validation)  
- **Target Platform**: Linux GitHub Actions free‑tier runner (CPU‑only); optional Kaggle GPU for LLM inference  
- **Constraints**: ≤ 6 h runtime, ≤ 7 GB RAM, ≤ 14 GB disk, no GPU in CI, deterministic seeds, checksum‑verified dataset  
- **Scale/Scope**: A modest sample of participants. × 30 tasks = 360 total task observations; a sample of buggy methods sampled from Defects4J.  

## Constitution Check
| Principle | Verification |
|-----------|--------------|
| I. Reproducibility | Fixed seeds, `requirements.txt` pins exact versions, dataset loaded from verified HuggingFace URL, deterministic scripts. |
| II. Verified Accuracy | All citations (Defects4J URLs, Holm‑Bonferroni method) are verified. |
| III. Data Hygiene | Raw downloads checksum‑verified; derived files written to new filenames; PII removed before commit. |
| IV. Single Source of Truth | Every figure/table will be generated from `data/analysis_results/results.json`. |
| V. Versioning Discipline | Content hashes recorded in `state/projects/.../artifact_hashes.yaml`. |
| VI. Human‑Subject Data Protection | Interaction logs are hashed, original consent kept in `.gitignore`‑ed `data/consent/`. |
| VII. Benchmark Dataset Integrity | Defects4J version pinned in `data/defects4j_version.txt`; summaries stored separately, original source unchanged. |

All principles are satisfied; no violations.

## Project Structure
```text
specs/001-evaluating-code-summarization-bug-localization/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── interaction.schema.yaml
    ├── interaction_log.schema.yaml
    ├── analysis.schema.yaml
    └── analysis_result.schema.yaml

code/
├── __init__.py
├── main.py                # CLI orchestrator
├── config.py
├── data_prep/
│   ├── download_defectsj.py      # T-002 (see corrected path)
│   └── generate_summaries.py     # T-003 (includes rule‑based & LLM stubs)
├── simulation/
│   └── simulate_study.py
├── analysis/
│   └── run_statistics.py
├── utils/
│   ├── pii.py
│   └── timing.py
└── llm_gpu/
    └── run_llm_gpu.sh          # GPU escape hatch script
data/
├── raw/
│   └── defects4j.parquet
├── processed/
│   ├── methods.csv
│   ├── summaries_rule.csv
│   └── summaries_llm.csv       # populated only by GPU escape hatch
├── interaction_logs/
│   ├── simulated_logs.csv
│   └── anonymized_logs.csv
├── analysis_results/
│   └── results.json
└── defects4j_version.txt
tests/
├── unit/
│   ├── test_download.py
│   ├── test_generate_summaries.py
│   └── test_analysis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
.github/
└── workflows/
    ├── ci.yml
    ├── test_reproducibility.yml
    └── validate_citations.yml
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| GPU Escape Hatch for LLM | CodeLlama‑7B cannot meet the 30 s timeout on CPU; fabricating a CPU approximation would be a falsification. | Using a tiny toy model would not answer the research question. |
| Dual Data Path (sim vs. real) | CI cannot collect human data nor run GPU inference; we need a deterministic simulation for CI while preserving a real‑mode path for the actual study. | Running only the real path would break CI; running only simulation would make the study impossible. |
| Cluster Bootstrap (participants) | Required for correct CIs with a small number of clusters. | Parametric CIs would ignore within‑subject correlation. |
| **A‑priori Power Analysis** | Needed to justify sample size and avoid under‑powered conclusions. | Ignoring power analysis would threaten methodological rigor. |

## Implementation Tasks (mapped to FR/SC)

| Task ID | Description | FR(s) addressed | SC(s) addressed |
|---------|-------------|----------------|-----------------|
| **T-001** | Create `requirements.txt` with exact version pins. | — | I, II |
| **T-002** | `code/data_prep/download_defectsj.py` – stream the verified Parquet dataset from HuggingFace, compute SHA‑256 checksums, verify against `data/checksums.txt`, write combined Parquet to `data/raw/defects4j.parquet`, and write version tag to `data/defects4j_version.txt`. | FR‑001 | I, III, VII |
| **T-003** | `code/data_prep/generate_summaries.py` – (a) extract methods → `data/processed/methods.csv`; (b) rule‑based summaries via srcML → `data/processed/summaries_rule.csv`; (c) **GPU‑only stub** that raises an error if `--mode=real` without GPU. | FR‑002, FR‑003 | I, III |
| **T-004** | `code/utils/timing.py` – perform a loopback latency test, assert median ≤ 100 ms, abort pipeline if not met. | FR‑003 | I |
| **T-005** | `code/simulation/simulate_study.py` – generate Latin‑square design for several participants × 10 tasks/condition, simulate timestamps and random line selections, write `data/interaction_logs/simulated_logs.csv`. | FR‑003 | I |
| **T-006** | `code/utils/pii.py` – hash raw participant IDs with SHA‑256 + secret salt, drop PII columns, write `data/interaction_logs/anonymized_logs.csv`. | FR‑003, VI | III, VI |
| **T-007** | `code/analysis/run_statistics.py` – (a) **McNemar’s test** for accuracy (binary outcome) comparing each pair of conditions; (b) Linear Mixed‑Effects model for speed (log‑transformed time) with random intercept for participant; (c) compute Odds Ratio (McNemar) and Cohen’s d (LME); (d) cluster bootstrap (12 participants, 2000 resamples, seed = 42) for 95 % CI; (e) **Primary analysis MUST exclude trials where `fallback_status != none`**; (f) Holm‑Bonferroni correction across the four primary tests (α = 0.05). | FR‑004, FR‑005, FR‑006 | III, IV, V |
| **T-008** | `code/main.py` – orchestrates steps: download → method extraction → rule summaries → latency test → (simulated or real) interaction log → analysis → writes `data/analysis_results/results.json`. | FR‑001‑FR‑007 | I |
| **T-009** | `scripts/run_llm_gpu.sh` – runs CodeLlama‑7B (8‑bit) on a Kaggle GPU, writes `data/processed/summaries_llm.csv`; logs any generation failures for fallback handling. | FR‑002 (real mode) | VII |
| **T-010** | CI workflow `ci.yml` – executes `python -m code.main --mode sim`, runs unit & contract tests, enforces 6‑hour timeout. | FR‑007 | I, V |
| **T-011** | Reproducibility workflow `test_reproducibility.yml` – runs full pipeline on a fresh runner, hashes `results.json`, asserts equality with stored reference hash. | FR‑007 | I |
| **T-012** | **A‑priori Power Analysis** – using `statsmodels.stats.power` (McNemar and LME) to estimate required number of participants for detecting a moderate effect (OR = 2.0, Cohen’s d = 0.6) at α = 0.05, 80 % power; results stored in `data/power_analysis/report.txt`. If the required N exceeds 12, the design is automatically upgraded to 24 participants (720 observations) before simulation. | — (addresses methodology concern) | SC‑001, SC‑002, SC‑003 |
| **T-013** | Update `README.md` with OSF publishing instructions, license, and usage notes. | FR‑007 | I, VI |
| **T-014** | Citation validation workflow `validate_citations.yml` – runs Reference‑Validator on all markdown files. | — | II |

### Power & Limitations (updated)
- **A‑priori Power Analysis (T‑012)**: Using `statsmodels` we estimate that to detect a **moderate** effect (Odds Ratio ≈ 2.0 for accuracy, Cohen’s d ≈ 0.6 for speed) with α = 0.05 and 80 % power, **≈ 24 participants** (720 task observations) are needed. The original 12‑participant design is powered only for large effects (OR > 3, d > 1). The pipeline will automatically run the power‑analysis script; if the computed required N > 12, the simulation will generate data for 24 participants. This ensures the study is not under‑powered for realistic effect sizes while remaining feasible on the CI runner.
- **Post‑hoc Power**: After data collection, we will also report observed power given the actual effect sizes.
- **Bootstrap instability**: With 12 clusters CIs may be wide; the larger 24‑participant design mitigates this. Both bootstrap and parametric CIs will be provided.

All functional requirements FR‑001 – FR‑007 and success criteria SC‑001 – SC‑005 are covered by at least one task.

## Projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/specs/001-evaluating-the-efficacy-of-code-summariz/contracts/ (unchanged)
(The contract files remain valid and unchanged.)
