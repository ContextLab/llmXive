# Implementation Plan: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Branch**: `001-gene-regulation` | **Date**: 2026-10-13 | **Spec**: [spec.md](../specs/001-gene-regulation/spec.md)  
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary
The project quantifies the *Prejudice Gap* in 27 Multimodal Large Language Models (MLLMs) on the MM‑OCEAN validation subset, then tests whether injecting a static JSON knowledge base of social priors reduces this gap. The pipeline consists of (1) data acquisition, (2) knowledge‑base preparation, (3) baseline prompting, (4) context‑grounded prompting, (5) random‑noise control, (6) metric computation (Prejudice Rate PR, Holistic‑Grounding Rate HR, Integration‑failure Rate IR), (7) paired statistical testing (paired t‑test or Wilcoxon signed‑rank) plus a mixed‑effects secondary analysis, and (8) resource‑budget monitoring with a fallback strategy.

All steps are designed to run on the GitHub Actions free‑tier (≤ 6 h, ≤ 7 GB RAM) using CPU‑quantized open‑source MLLMs (e.g., LLaVA‑1.5‑7B‑q4). Where a required dataset is not publicly downloadable, the plan explicitly flags the gap (see Constitution Check) and proposes an open substitute for proof‑of‑concept.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `transformers>=4.40`, `datasets>=2.18`, `torch>=2.2` (CPU‑only), `scikit‑learn>=1.5`, `statsmodels>=0.14`, `pandas>=2.2`, `pyyaml>=6.0`, `tqdm`, `jsonschema`
- **Storage**: File‑based (`data/` directory) – raw videos are streamed; all metadata and derived tables are CSV/JSON.
- **Testing**: `pytest` with contract validation (`jsonschema`); unit tests for each pipeline stage.
- **Target Platform**: Linux runner on GitHub Actions (CPU‑only). No GPU required.
- **Project Type**: Research library / CLI tool.
- **Performance Goals**: Complete full 27 × 200 × 3 inference runs within 6 h, peak RAM ≤ 7 GB.
- **Constraints**: CPU‑only quantized inference; batch size ≤ 20; fallback to top‑15 models or 10‑frame sampling if budget exceeded.
- **Scale/Scope**: 27 models, ~200 video samples, three conditions (baseline, context‑grounded, random‑noise).

## Constitution Check
| Principle | How the plan satisfies / references it |
|-----------|----------------------------------------|
| **I. Reproducibility** | All scripts are deterministic (random seeds pinned). External datasets are fetched from canonical URLs (or flagged as unavailable). |
| **II. Verified Accuracy** | No new citations are introduced beyond those already in the spec. |
| **III. Data Hygiene** | Raw MM‑OCEAN files (if obtainable) will be checksummed; all transformations write new files under `data/derived/`. |
| **IV. Single Source of Truth** | Every figure/table will be generated directly from CSV/JSON artifacts produced by the pipeline. |
| **V. Versioning Discipline** | All artifacts are content‑hashed; `state/projects/...yaml` will be updated automatically by the platform. |
| **VI. Context‑Grounded Evaluation** | Metric definitions (PR, HR, IR) explicitly require detection of injected context phrases in the reasoning string. |
| **VII. Resource‑Constrained Inference Discipline** | Inference uses quantized 7‑B models; batch processing limits keep RAM < 7 GB; fallback strategy defined. |
| **Dataset Availability Gap** | The required MM‑OCEAN validation subset is **not** available via a verified public URL (no entry in the “# Verified datasets” block). The plan therefore **flags** FR‑001 as unmet and proposes an open substitute (e.g., the HuggingFace `mmbench-ocean` dataset) for proof‑of‑concept, while noting that final results require the genuine MM‑OCEAN data. |

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
│   ├── acquire.py          # data download / verification
│   ├── knowledge.py        # build / query knowledge base
│   ├── inference.py        # baseline / context / control runs
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
| **0. Data Acquisition** | Download / verify MM‑OCEAN (or open substitute). Compute checksum. | FR‑001 | SC‑004 (valid reasoning), SC‑009 (grounding‑uncertainty) |
| **1. Knowledge‑Base Construction** | Load static JSON, validate schema, enable fast lookup. | FR‑002 | SC‑006 (IR ≤ 10 %) |
| **2. Baseline Prompting** | Run standard prompt on each model‑video pair; store raw JSON output. | FR‑003, FR‑010 | SC‑004, SC‑008 |
| **3. Context‑Grounded Prompting** | Retrieve appropriate context profile, inject into prompt, run inference. | FR‑004, FR‑008, FR‑009 | SC‑006, SC‑007 |
| **4. Random‑Noise Control** | Replace context profile with random noise string; run inference. | FR‑006 | SC‑002 |
| **5. Metric Computation** | Derive PR, HR, IR per model & condition; filter invalid/uncertain samples. | FR‑001, FR‑008‑FR‑011 | SC‑001, SC‑003, SC‑005 |
| **6. Statistical Analysis** | Paired t‑test / Wilcoxon; mixed‑effects model (random video, grouping by model family). | FR‑005 | SC‑001, SC‑002, SC‑005 |
| **7. Resource Monitoring & Fallback** | Track wall‑clock & RAM; if > 6 h or > 7 GB, apply fallback (top‑15 models or 10‑frame sampling). | FR‑007 | SC‑003 |
| **8. Reporting** | Write CSV/JSON tables, generate figures (PR reduction plot, IR histogram), produce a concise results markdown. | — | All SCs (final reporting) |

Each phase will be implemented as a separate Python module under `src/pipeline/` and orchestrated by a top‑level CLI (`python -m src.pipeline.run_all`). Tasks are ordered to respect data dependencies (download → knowledge base → inference → metrics → analysis → reporting).

## Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| MM‑OCEAN not publicly downloadable | Blocking for FR‑001 & downstream metrics | Flag gap; use open substitute for prototype; document limitation; request dataset access before final analysis. |
| CPU inference exceeds time budget | Failure of SC‑003 | Quantize models to 4‑bit, limit batch size, enable fallback to top‑15 models. |
| Context retrieval fails for missing tags | Potential rise in IR | Implement neutral‑context fallback (FR‑009) and log occurrences; ensure IR calculation counts only successful retrievals. |
| Invalid JSON output from models | Inflates exclusion rate | Enforce strict JSON schema, retry up to 2 times, then mark as invalid (FR‑010). |
| Multiple‑comparison inflation | False positives | Apply Bonferroni correction across the three primary hypothesis tests. |

---
