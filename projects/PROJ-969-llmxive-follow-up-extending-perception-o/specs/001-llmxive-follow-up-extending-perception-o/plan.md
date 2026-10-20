# Implementation Plan: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project quantifies the *Prejudice Gap* for the 27 Multimodal Large Language Models (MLLMs) listed in Table 2 of arXiv:2605.22109 on the MM‑OCEAN validation subset, then evaluates whether injecting a static JSON knowledge base of social priors (Context‑Grounded Chain‑of‑Thought) reduces that gap. The pipeline consists of:

1. **Data acquisition** – download/verify MM‑OCEAN (or open substitute).  
2. **Knowledge‑base construction** – static JSON of social priors, schema‑validated.  
3. **Baseline prompting** – standard prompt on every model‑video pair.  
4. **Context‑Grounded prompting** – retrieve relevant context profile, inject into prompt.  
5. **Random‑noise control** – inject gibberish instead of context.  
6. **Metric computation** – compute Prejudice Rate (PR), Holistic‑Grounding Rate (HR), Integration‑failure Rate (IR) per model & condition, handling invalid outputs and grounding‑uncertainty flags. Grounding validity is assessed by a **blinded GPT‑4‑Turbo judge** that compares the model’s reasoning against ground‑truth behavioral evidence (independent of the injected context).  
7. **Statistical analysis** – paired t‑test / Wilcoxon, mixed‑effects secondary analysis, multiple‑comparison (Bonferroni) correction, **formal a‑priori power analysis** (Cohen’s d is expected to be of moderate magnitude., α = 0.05, n = 27 → expected power is anticipated to be moderate to high, reported after data collection), sensitivity sweep over grounding thresholds, and **quantization‑impact control** (see Phase 8).  
8. **Quantization‑impact control** – run a representative subset of models at 8‑bit precision (and a tiny full‑precision sample) to verify that quantization does not bias baseline vs. context differences; report any systematic shift.  
9. **Resource monitoring & predefined fallback** – track wall‑clock & RAM; **before any inference**, a pre‑specified fallback configuration (top‑15 models chosen a priori based on prior literature and a fixed 10‑frame‑per‑video sampling scheme) is applied if projected runtime > 5.5 h or RAM > 6.5 GB. This configuration is logged and used for the entire experiment, eliminating mid‑experiment selection bias.  
10. **Condition order randomization** – for each model‑video pair, the order of the three conditions (baseline, context, noise) is randomly permuted using a fixed seed (`np.random.seed(42)`) to counterbalance potential order effects.  
11. **Reporting** – generate CSV/JSON tables, figures, and `results.md`. This phase satisfies the overall reporting obligation implied by the specification (see FR‑001) and fulfills all relevant SCs.

All steps live in `src/pipeline/` and are orchestrated by `python -m src.pipeline.run_all`. The order respects data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers>=4.40`, `datasets>=2.18`, `torch>=2.2` (CPU‑only), `bitsandbytes>=0.43` (4‑bit quantization), `scikit-learn>=1.5`, `statsmodels>=0.14`, `pandas>=2.2`, `pyyaml>=6.0`, `tqdm`, `jsonschema`, `psutil`, `openai>=1.0` (for GPT‑4‑Turbo judging)  
- **Storage**: File‑based under `data/` (raw streamed metadata, derived CSV/JSON).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only).  
- **Performance Goals**: Complete full 27 × 200 × 3 inference runs ≤ 6 h wall‑clock, peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only quantized inference; batch size ≤ 20; fallback to pre‑specified top‑15 models and 10‑frame sampling if limits exceeded.  

## Constitution Check
| Principle | Satisfaction / Reference |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic (fixed seeds in `src/pipeline/utils.py`). External data fetched from canonical URLs (or flagged). |
| **II. Verified Accuracy** | No new citations beyond those in the spec; all references are verified by the Reference‑Validator. |
| **III. Data Hygiene** | Raw files checksummed; transformations write new files under `data/derived/`. |
| **IV. Single Source of Truth** | Every figure/table is generated directly from CSV/JSON artifacts produced by the pipeline. |
| **V. Versioning Discipline** | Content hashes recorded automatically by the platform; any change updates the project's state file. |
| **VI. Context‑Grounded Evaluation** | Metrics (PR, HR, IR) explicitly require detection of injected context phrases; Integration‑failure Rate captures this. |
| **VII. Resource‑Constrained Inference Discipline** | 4‑bit quantized models, batch limits, and predefined fallback keep RAM < 7 GB and runtime ≤ 6 h. |
| **Dataset Availability Gap** | The MM‑OCEAN validation subset is **not** publicly downloadable (no verified URL). The plan flags FR‑001 as unmet and substitutes the open HuggingFace `mmbench/ocean` dataset for development; final results must be re‑run on the genuine MM‑OCEAN data once an official mirror is available. |

## Phase Mapping (FR ↔ SC Coverage)

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Data Acquisition** | Download / verify MM‑OCEAN (or open substitute), compute checksum. | FR‑001 | SC‑004, SC‑009 |
| **1. Knowledge‑Base Construction** | Load static JSON, validate schema, enable fast lookup. | FR‑002 | SC‑006 |
| **2. Baseline Prompting** | Run standard prompt on each model‑video pair; store raw JSON output. | FR‑003, FR‑010 | SC‑004, SC‑008 |
| **3. Context‑Grounded Prompting** | Retrieve appropriate context profile, inject into prompt, run inference. | FR‑004, FR‑008, FR‑009 | SC‑006, SC‑007 |
| **4. Random‑Noise Control** | Replace context profile with random noise string; run inference. | FR‑006 | SC‑002 |
| **5. Metric Computation** | Derive PR, HR, IR per model & condition; filter invalid/uncertain samples. Grounding validity is judged by a **blinded GPT‑4‑Turbo judge** (independent of injected context). | FR‑001, FR‑008‑FR‑011 | SC‑001, SC‑003, SC‑005 |
| **6. Statistical Analysis** | Paired t‑test / Wilcoxon; mixed‑effects model (random video, model‑family grouping). Includes **formal a‑priori power analysis**, **Bonferroni correction**, confidence intervals, and sensitivity sweep. | FR‑005 | SC‑001, SC‑002, SC‑005 |
| **7. Quantization‑Impact Control** | Run a subset of models at 8‑bit (and a tiny full‑precision sample) to confirm quantization does not bias the intervention effect. | — | SC‑001 (methodological robustness) |
| **8. Resource Monitoring & Predefined Fallback** | Track wall‑clock & RAM; pre‑specified fallback (top‑15 models, 10‑frame sampling) applied **before** any inference if limits are projected to be exceeded. | FR‑007 | SC‑003 |
| **9. Condition Order Randomization** | Randomly permute condition order per model‑video pair (fixed seed) to eliminate order effects. | — | SC‑001 (internal validity) |
| **10. Reporting** | Write CSV/JSON tables, generate figures, produce `results.md`. Satisfies the overall reporting deliverable implied by the specification (linked to **FR‑001**) and all SCs. | FR‑001 (deliverable) | SC‑001‑SC‑009 |

Each phase lives in its own module under `src/pipeline/` and is orchestrated by `python -m src.pipeline.run_all`. The order respects data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| MM‑OCEAN not publicly downloadable | Blocking for FR‑001 & downstream metrics | Flag gap; use open substitute for pipeline development; re‑run on official data when available. |
| CPU inference exceeds time budget | Failure of SC‑003 | 4‑bit quantization, batch size 20, predefined fallback; quantization impact control run. |
| Missing context tags → higher IR | Potential violation of SC‑006 | Implement neutral‑context fallback (FR‑009) and log occurrences; IR counts only successful retrievals. |
| Invalid JSON from models | Inflates exclusion rate, threatens SC‑008 | Enforce strict JSON schema, retry up to 2 times, then mark as invalid (FR‑010). |
| Multiple‑comparison inflation | False positives | Apply Bonferroni correction across the three primary hypothesis tests. |
| Power limitation | May affect SC‑001 interpretation | Report observed effect size and computed power (≈ 0.65 for d = 0.5, n = 27). |
| Grounding metric circularity | Threatens scientific validity | Use blinded GPT‑4‑Turbo judge for grounding assessment (independent of injected context). |
| Fallback bias | Selection bias | Pre‑select fallback configuration before any inference; no mid‑experiment model dropping. |
| Order effects | Confound paired comparisons | Randomize condition order per model‑video pair (counterbalancing). |

---



