# Implementation Plan: Qwen‑VLA Cross‑Embodiment Transfer Study  

**Branch**: `[feature‑branch]` | **Date**: 2026‑06‑29 | **Spec**: [link]  
**Input**: Feature specification from `/specs/[feature‑branch]/spec.md`

## Summary
The project will (1) ingest a filtered subset of the Open X‑Embodiment dataset (or a verified fallback BridgeData v2 subset) (~50 k demonstrations spanning ≥3 robot platforms), (2) fine‑tune a frozen Qwen2‑VL‑2B vision encoder with a diffusion‑transformer (DiT) action head on CPU‑only hardware, (3) evaluate the resulting checkpoint zero‑shot on the LIBERO‑Spatial and LIBERO‑Object benchmarks for held‑out platforms, (4) compare performance against a single‑embodiment baseline using a **Wilcoxon signed‑rank test with Holm‑Bonferroni correction** on paired success-rate vectors (same seeds, different data splits), and (5) run a data‑composition ablation (ratios 0.0, 0.5, 1.0) and report means with 95 % confidence intervals. All steps are orchestrated to respect the CI limits (2 CPU cores, ≈7 GB RAM, ≤6 h wall‑time) and the project constitution.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0+cpu`, `transformers==4.44.0`, `datasets==2.20.0`, `numpy`, `pandas`, `scipy`, `matplotlib`, `psutil`, `click`, `pyyaml`  
- **Storage**: File‑system storage under `data/` (parquet/CSV).  
- **Testing**: `pytest`, `hypothesis` for contract validation.  
- **Target Platform**: Linux x86_64 GitHub Actions runner (CPU‑only).  
- **Project Type**: Research CLI library.  
- **Performance Goals**: Peak RAM ≤ 7 GB; training wall‑time ≤ 6 h per CI job; checkpoint size ≤ 2 GB.  
- **Constraints**: No GPU, no CUDA, no large‑scale model training beyond the frozen backbone; batch size limited to fit RAM; streaming dataset loading.  
- **Scale/Scope**: 5 random seeds, ~50 k demos, 2 robot platforms for evaluation.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds, hyper‑parameters, and software versions are recorded in `manifest.yaml` and rendered by `render_manifest.py`. |
| II. Verified Accuracy | No external citation is introduced beyond those already present in the spec. |
| III. Data Hygiene | Dataset checksum and exact version identifier will be stored in `data/metadata.yaml`; transformations produce new files with provenance metadata. |
| IV. Single Source of Truth | Every figure/table in the paper will be generated from files under `data/` and code under `code/`. |
| V. Versioning Discipline | All artifacts are content‑hashed; `state/projects/...yaml` will be updated on change. |
| VI. Statistical Rigor | 95 % confidence intervals (bootstrapped) for each seed set; **paired Wilcoxon signed-rank test with Holm-Bonferroni correction** (justified by the paired design of same seeds, different data splits); significance threshold p < 0.05. |
| VII. Cross‑Embodiment Data Provenance | The Open X‑Embodiment subset (or verified fallback BridgeData v2) will be fetched via HuggingFace Datasets API (version recorded in `data/metadata.yaml`) and filtered deterministically. |

## Mapping of Functional & Success Criteria to Plan Phases
| Phase | FR(s) addressed | SC(s) addressed | Description |
|-------|----------------|----------------|-------------|
| **0 – Dataset Acquisition & Verification** | FR‑001, FR‑006 | (none directly) | Download Open X‑Embodiment (or verified fallback BridgeData v), compute checksum, record exact version ID in `data/metadata.yaml`, filter to ~50 k demos, store manifest. |
| **1 – Model Assembly** | FR‑002, FR‑003 | (none directly) | Load Qwen2‑VL‑2B weights (CPU‑only, frozen vision encoder), instantiate DiT action head, verify memory footprint ≤ 7 GB. |
| **2 – Pre‑training (Cross‑Embodiment)** | FR‑001, FR‑003, FR‑008 | SC‑004 | Train on filtered subset (ratio=1.0) for up to 6 h, log wall‑time and peak RAM (active monitoring), checkpoint ≤ 2 GB. |
| **3 – Baseline Pre‑training (Single‑Embodiment)** | FR‑001 (BridgeData‑only) | SC‑004 | Same pipeline but with `ratio=0.0` (single platform data) for the SAME 5 seeds as Phase 2 to enable paired testing. |
| **4 – Evaluation on LIBERO Benchmarks** | FR‑004 | SC‑001, SC‑004 | Zero‑shot evaluation on LIBERO‑Spatial & LIBERO‑Object for held‑out platforms; record per‑seed success‑rate, trajectory length, variance. |
| **5 – Statistical Comparison** | FR‑005 | SC‑001, SC‑002, SC‑004 | Compute paired Wilcoxon signed-rank test on the 5 seed vectors (Cross vs. Baseline), apply Holm‑Bonferroni correction, output p‑value and decision. |
| **6 – Data‑Composition Ablation** | FR‑006 | SC‑003, SC‑004 | Run three ratio settings (0.0, 0.5, 1.0), evaluate, compute mean ± 95 % CI, generate CSV + plot. |
| **7 – Reproducibility Manifest** | FR‑007 | SC‑005 | Generate `manifest.yaml` & `manifest.md` via `render_manifest.py`. |
| **8 – CI Guardrails** | FR‑008 | (none) | Enforce a configurable timeout warning; continue job after warning. |

## Edge‑Case Handling
- **Missing Action Token Format** – preprocessing step (`preprocess_actions.py`) will map raw joint vectors to DiT token space; if mapping fails for a demo, the demo is dropped and logged.
- **RAM Overrun** – dataset is streamed; batch size automatically reduced in real-time if `psutil` reports > 6.5 GB RSS.
- **Statistical Test Failure** – if any seed run crashes, the run is marked as 'INVALID' and the entire experiment for that condition is aborted/retried to ensure exactly 5 seeds are available, satisfying Constitution Principle VI.
- **Dataset Unavailability** – if the primary Open X‑Embodiment source is unreachable, the system automatically switches to the verified BridgeData v2 fallback (HuggingFace ID: `bridge-v2`) and logs the switch in `manifest.md`.

## Compute Feasibility
All commands are CPU‑only and limited to ≤ 2 GB model checkpoint size. Training uses `torch.set_num_threads(2)` to respect the 2‑core limit. Data is streamed from disk; peak RAM is monitored and capped. Expected total runtime: moderate duration on the CI runner (worst-case). No GPU or heavy external services are required.

---
