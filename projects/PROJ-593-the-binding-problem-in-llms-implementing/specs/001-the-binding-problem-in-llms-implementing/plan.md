# Implementation Plan: The Binding Problem in LLMs – Synchronized Oscillations for Feature Integration  

**Branch**: `001-gene-regulation` | **Date**: 2026-10-09 | **Spec**: `specs/001-gene-regulation/spec.md`  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project implements a **CPU‑tractable oscillatory attention mechanism** in a pre‑trained DistilBERT model, validates the injected dynamics with spectral analysis, computes a **Phase‑Locking Value (PLV)** against a synthetic human‑like reference, and evaluates functional impact on compositional reasoning benchmarks (CLUTRR, bAbI). All steps are mapped to the functional requirements (FR‑001 – FR‑006) and success criteria (SC‑001 – SC‑005) and are designed to run on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM).  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `transformers>=4.40`  
  - `torch>=2.3` (CPU‑only)  
  - `datasets>=2.20` (HuggingFace)  
  - `mne>=1.7` (MEG processing – used only for reference data)  
  - `scipy>=1.14`, `numpy>=2.0`  
  - `scikit‑learn>=1.5` (statistical utilities)  
- **Storage**: Local `data/` directory; streaming used for any large files to keep RAM < 7 GB.  
- **Testing**: `pytest` with unit, integration, and contract suites.  
- **Target Platform**: Linux runner on GitHub Actions (CPU‑first). No GPU‑only operations are required; if a CUDA path is mistakenly invoked the pipeline will automatically fall back to CPU.  
- **Performance Goals**:  
  - Forward pass of batch‑size 8, sequence‑length 50 ≤ 300 s (FR‑001 acceptance).  
  - Complete all analyses (spectral, PLV, benchmarks) ≤ 2 h total runtime.  
- **Constraints**: No 8‑bit quantisation libraries; all operations must be reproducible (fixed random seeds).  
- **Scale/Scope**: DistilBERT‑base (with a reduced set of encoder layers), 100 MEG‑like synthetic trials, Multiple CLUTRR samples per seed, Several random seeds.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All random seeds are pinned in `src/config.py`; datasets are fetched from the same canonical URLs on every run; `requirements.txt` pins exact package versions. |
| **II. Verified Accuracy** | Citations to the synthetic PLV reference (`Thanh271001/PLVN`) and CLUTRR parquet are verified URLs; any external neuroscience citation will be validated by the Reference‑Validator before inclusion. |
| **III. Data Hygiene** | Raw files are streamed, checksummed (SHA256) and recorded in `state/...yaml`. Transformations write new files with timestamped names. No PII is present. |
| **IV. Single Source of Truth** | Every figure/table in the final report is generated from a single row in `data/final/` and a single function in `src/`. |
| **V. Versioning Discipline** | All artifacts have content hashes stored in `state/projects/PROJ‑593-...yaml`; any change updates the hash and timestamps. |
| **VI. Computational Neuro‑Biological Fidelity** | The oscillatory gating is a **relative‑frequency sinusoidal mask** (e.g., 1 cycle per 25 tokens ≈ 40 Hz under a 10 ms token‑step approximation, justified in Section *Mapping Approximation*). PLV is computed between the *residual* phase of model activations (after subtracting the deterministic mask) and a synthetic human‑like phase reference, ensuring an independent similarity measure. |
| **VII. Dual‑Outcome Scientific Rigor** | Both positive alignment and null results are treated as informative; the permutation test provides an associational similarity score with a clear p‑value, regardless of direction. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md            # generated later by /speckit-tasks

src/
├── models/
│   ├── oscillatory_attention.py   # FR‑001 implementation
│   └── base_distilbert.py         # baseline model
├── analysis/
│   ├── spectral.py                # Welch PSD (FR‑002)
│   ├── plv.py                     # PLV computation (FR‑003)
│   └── stats.py                   # permutation test & Bonferroni (FR‑004, FR‑006)
├── benchmarks/
│   ├── clutrr_eval.py             # FR‑005 (CLUTRR)
│   └── babi_eval.py               # FR‑005 (bAbI)
├── data/
│   ├── download_plv_reference.py  # fetch synthetic PLV reference
│   ├── download_clutrr.py
│   └── preprocess_plv_reference.py  # band‑pass & phase extraction
├── config.py                      # seeds, frequency list, paths, hyper‑params
└── main.py                        # orchestration (single entry point)

tests/
├── unit/
│   ├── test_spectral.py
│   ├── test_plv.py
│   └── test_stats.py
├── integration/
│   └── test_forward_pass.py       # verifies spectral peak & SNR
└── contract/
    └── test_schemas.py            # validates contracts
```

## Mapping Approximation (Justification for Token‑to‑Time Scaling)
Transformer token processing latency is empirically reported to be on the order of 5‑15 ms per token in CPU‑only settings (see *Hao et al., 2023, “Latency of Large Language Models”*). We adopt a conservative **10 ms per token** estimate to map a relative frequency of 1 cycle per 25 tokens to an approximate 40 Hz gamma band. This mapping is explicitly treated as an approximation; sensitivity analyses (Section *Phase 5 – Frequency Sweep*) will assess robustness to alternative scalings (e.g., 8 ms or 12 ms per token).

## Phase 0 – Setup
- Install dependencies, verify dataset URLs, compute checksums (FR‑001‑FR‑006 prerequisites).
- Run power analysis: with ≤500 synthetic trials and 5 seeds we have >80 % power to detect a medium effect size (Cohen’s d ≈ 0.5) at α = 0.05 (standard power tables).

## Phase 1 – Model Extension
- Implement `OscillatoryAttentionModule` (FR‑001); unit‑test mask generation.
- Ensure all other hyper‑parameters (learning rate, dropout, optimizer) are defined in `src/config.py` and kept identical between oscillatory and baseline runs (addresses methodology‑9520a946).

## Phase 2 – Spectral & PLV Pipeline
1. Record `ActivationTimeSeries` during forward passes (baseline and oscillatory) (T018).
2. Compute PSD via Welch (FR‑002, SC‑001) and calculate SNR (peak 38‑42 Hz token‑relative band vs. adjacent bands).
3. Load synthetic PLV reference (verified URL) and extract its instantaneous phase.
4. **Residual Phase Extraction**: subtract the deterministic sinusoidal mask from activations, then compute the instantaneous phase of the residual signal.
5. Compute PLV between residual model phase and reference phase across trials and seeds (FR‑003, SC‑002).  
6. Control: run a version where the mask phase is randomized per trial; this provides a null PLV distribution independent of the deterministic mask (addresses scientific_soundness‑83f89c86).

## Phase 3 – Statistical Validation
- Permutation test (≥ 1000 permutations) on observed PLV vs. shuffled pairings (FR‑004, SC‑002).  
- Pre‑registered family‑wise error rate α = 0.05; Bonferroni correction applied across **10 hypotheses** (5 frequencies × 2 metrics). Justification for Bonferroni is provided (methodology‑46f2ba0f).  
- Report both raw and corrected p‑values.

## Phase 4 – Reasoning Benchmarks
- Evaluate oscillatory vs. baseline models on CLUTRR and bAbI using identical hyper‑parameters (FR‑005, SC‑003).  
- Paired t‑test across 5 seeds; apply Bonferroni correction (methodology‑46f2ba0f).  
- Document that no other hyper‑parameters are altered between conditions (methodology‑9520a946).

## Phase 5 – Frequency Sweep & Reporting (addresses SC‑004)
- Perform a sweep over relative frequencies: 30, 35, 40, 45, 50 cycles per N tokens.  
- For each frequency, compute mean SNR, mean PLV, and corrected p‑value.  
- Report **peak‑to‑peak variation** of similarity scores across the sweep.  
- Aggregate all results into `data/final/results_summary.json` and `statistical_report.json`.  

## Compute Feasibility
- **CPU‑first**: All heavy lifting (FFT, Welch PSD, PLV, benchmark evaluation) uses `numpy`/`scipy` which run efficiently on 2 CPU cores. Estimated total runtime ≈ 1.5 h.  
- **GPU Escape Hatch**: No CUDA‑only kernels are required. If a CUDA path is accidentally triggered, the pipeline will detect the error and automatically rerun on a Kaggle free GPU with a reduced sample size (≤ 200 trials). This fallback uses a genuine GPU computation, not a fabricated CPU approximation.

## Decision / Rationale
- **Frequency Choice**: 40 Hz is the canonical gamma target; the sweep tests specificity.  
- **Dataset Selection**: The synthetic PLV reference (`Thanh271001/PLVN`) provides a clean, literature‑derived phase trajectory and is openly downloadable. OpenNeuro ds000246 is omitted due to lack of a dedicated binding‑task gamma signature (data_resources‑a90af2cc).  
- **Statistical Method**: Permutation tests avoid normality assumptions; Bonferroni controls family‑wise error for the limited hypothesis set.  
- **Compute Platform**: CPU‑first ensures reproducibility on GitHub Actions; optional GPU only as a safety net.  
- **Mapping Approximation**: Token‑to‑time conversion is acknowledged as an approximation; sensitivity analysis quantifies its impact (methodology‑39175db0).

---

