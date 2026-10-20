# Implementation Plan: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-20 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project quantifies the *Prejudice Gap* for 27 Multimodal Large Language Models (MLLMs) on the MM‑OCEAN validation subset, then evaluates whether injecting a static JSON knowledge base of social priors (context‑grounded chain‑of‑thought) reduces that gap. The pipeline consists of:

1. **Data acquisition** (download/verify MM‑OCEAN or open substitute).  
2. **Knowledge‑base construction** (static JSON of social priors).  
3. **Baseline prompting** (standard prompt).  
4. **Context‑grounded prompting** (inject retrieved context).  
5. **Random‑noise control** (inject gibberish).  
6. **Metric computation** (Prejudice Rate PR, Holistic‑Grounding Rate HR, Integration‑failure Rate IR).  
7. **Statistical analysis** (paired test, mixed‑effects model, multiple‑comparison correction, sensitivity sweep).  
8. **Resource‑budget monitoring & fallback** (runtime & RAM tracking, automatic reduction to top‑15 models or 10‑frame sampling).  

All steps are CPU‑first, using 4‑bit quantized open‑source MLLMs that fit the GitHub Actions free‑tier limits. If a model cannot load on CPU, the pipeline will automatically off‑load that single model to a free Kaggle GPU (real GPU escape hatch) while processing a sampled subset.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `transformers>=4.40`, `datasets>=2.18`, `torch>=2.2` (CPU‑only), `bitsandbytes>=0.43` (4‑bit quantization), `scikit-learn>=1.5`, `statsmodels>=0.14`, `pandas>=2.2`, `pyyaml>=6.0`, `tqdm`, `jsonschema`, `psutil`  
- **Storage**: File‑based under `data/` (raw metadata streamed, derived CSV/JSON).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions runner (CPU‑only).  
- **Project Type**: Research library / CLI tool.  
- **Performance Goals**: Complete full 27 × 200 × 3 inference runs ≤ 6 h wall‑clock, peak RAM ≤ 7 GB.  
- **Constraints**: CPU‑only quantized inference; batch size ≤ 20; fallback to top‑15 models or 10‑frame sampling if limits exceeded.  
- **Scale/Scope**: 27 models, ~200 video samples, three conditions (baseline, context‑grounded, random‑noise).

## Constitution Check
| Principle | Satisfaction / Reference |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic (seeded). External data fetched from canonical URLs (or flagged). |
| **II. Verified Accuracy** | No new citations beyond those already in the spec; all references are verified. |
| **III. Data Hygiene** | Raw files checksummed; transformations write new files under `data/derived/`. |
| **IV. Single Source of Truth** | Every figure/table is generated directly from CSV/JSON artifacts produced by the pipeline. |
| **V. Versioning Discipline** | Content hashes recorded automatically by the platform. |
| **VI. Context‑Grounded Evaluation** | Metrics (PR, HR, IR) explicitly require detection of injected context phrases (principle‑specific). |
| **VII. Resource‑Constrained Inference Discipline** | Quantized 4‑bit models, batch limits, and fallback strategy keep RAM < 7 GB and runtime ≤ 6 h. |
| **Dataset Availability Gap** | The MM‑OCEAN validation subset is **not** publicly downloadable (no verified URL). The plan flags FR‑001 as unmet and proposes the open HuggingFace `mmbench/ocean` dataset as a proof‑of‑concept substitute, with a clear note that final results require the genuine MM‑OCEAN data. |

## Project Structure
```text
specs/001-gene-regulation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── metric_record.schema.yaml
└── tasks.md   # generated later by /speckit-tasks
```

```text
src/
├── data/
│   ├── raw/                # streamed video refs, raw metadata (read‑only)
│   ├── derived/            # processed metadata, context profiles, metric CSVs
│   └── knowledge_base.json # static JSON of social priors
├── pipeline/
│   ├── acquire.py          # download / verify data
│   ├── knowledge.py        # load / query knowledge base
│   ├── inference.py        # baseline / context / noise runs
│   ├── metrics.py          # compute PR, HR, IR
│   ├── analysis.py         # statistical tests, mixed‑effects model
│   └── utils.py            # logging, seeding, resource monitor
└── tests/
    └── contract/
        └── test_metrics.py # contract validation
```

## Phase Mapping (FR ↔ SC Coverage)

| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Data Acquisition** | Download / verify MM‑OCEAN (or open substitute), compute checksum. | FR‑001 | SC‑004, SC‑009 |
| **1. Knowledge‑Base Construction** | Load static JSON, validate schema, enable fast lookup. | FR‑002 | SC‑006 |
| **2. Baseline Prompting** | Run standard prompt on each model‑video pair; store raw JSON output. | FR‑003, FR‑010 | SC‑004, SC‑008 |
| **3. Context‑Grounded Prompting** | Retrieve appropriate context profile, inject into prompt, run inference. | FR‑004, FR‑008, FR‑009 | SC‑006, SC‑007 |
| **4. Random‑Noise Control** | Replace context profile with random noise string; run inference. | FR‑006 | SC‑002 |
| **5. Metric Computation** | Derive PR, HR, IR per model & condition; filter invalid/uncertain samples. | FR‑001, FR‑008‑FR‑011 | SC‑001, SC‑003, SC‑005 |
| **6. Statistical Analysis** | Paired t‑test / Wilcoxon; mixed‑effects model (random video, model‑family grouping). | FR‑005 | SC‑001, SC‑002, SC‑005 |
| **7. Resource Monitoring & Fallback** | Track wall‑clock & RAM; if > 6 h or > 7 GB, apply fallback (top‑15 models or 10‑frame sampling). | FR‑007 | SC‑003 |
| **8. Reporting** | Write CSV/JSON tables, generate figures (PR reduction plot, IR histogram, sensitivity sweep), produce `results.md`. | — | All SCs (final reporting) |

Each phase is a separate Python module under `src/pipeline/` and orchestrated by `python -m src.pipeline.run_all`. The order respects data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| MM‑OCEAN not publicly downloadable | Blocking for FR‑001 & downstream metrics | Flag gap; use open substitute for pipeline validation; document limitation; request official mirror before final analysis. |
| CPU inference exceeds time budget | Failure of SC‑003 | Quantize to 4‑bit, limit batch size, enable fallback to top‑15 models. |
| Missing context tags → higher IR | Potential violation of SC‑006 | Implement neutral‑context fallback (FR‑009) and log occurrences; IR calculation counts only successful retrievals. |
| Invalid JSON from models | Inflates exclusion rate, threatens SC‑008 | Enforce strict JSON schema, retry up to 2 times, then mark as invalid (FR‑010). |
| Multiple‑comparison inflation | False positives | Apply Bonferroni correction across the three primary hypothesis tests. |
| Power limitation | May affect SC‑001 interpretation | Report observed effect size and note that the sample size provides ≈ 80 % power for a moderate effect (Cohen’s d ≈ 0.5). |

---
