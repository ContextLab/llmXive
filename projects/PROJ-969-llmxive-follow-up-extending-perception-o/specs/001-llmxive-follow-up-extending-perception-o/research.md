# Research: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

## Overview
This document details the research‑ready design, data strategy, model selection, statistical methodology, and compute plan required to answer the primary hypothesis:

> **H₁**: Injecting explicit, text‑based social priors into MLLM prompts reduces the *Prejudice Rate* (PR) relative to the baseline prompting protocol.

A secondary hypothesis (**H₂**) asserts that a random‑noise control does **not** reduce PR, confirming that any observed effect is due to meaningful context rather than prompt length.

## Dataset Strategy
| Dataset | Access Method | Verified URL | Notes |
|---------|---------------|--------------|-------|
| **MM‑OCEAN validation subset** (≈ 200 videos) | Supposedly hosted with arXiv:2605.22109 | *No verified URL in the "# Verified datasets" block* | Not publicly downloadable; therefore **FR‑001** cannot be satisfied directly. |
| **Open substitute** (`mmbench/ocean` on HuggingFace) | `datasets.load_dataset("mmbench/ocean", split="validation")` | https://huggingface.co/datasets/mmbench/ocean | Contains video references, transcripts, setting, culture, and behavior tags compatible with the required schema. Used for pipeline development and proof‑of‑concept. |

**Decision:** Build and test the entire pipeline on the open substitute. The final analysis must be rerun on the genuine MM‑OCEAN data once an official public mirror is available. This satisfies the constitution’s requirement to flag missing data rather than fabricate it.

## Model Selection & Inference Strategy
- **Model pool:** The 27 models listed in Table 2 of arXiv:2605.22109 (e.g., LLaVA‑1.5‑7B, Mini‑GPT‑4‑7B). All are open‑source and loadable via `transformers`.  
- **Quantization:** 4‑bit (`bitsandbytes`) on CPU; falls back to 8‑bit if 4‑bit fails. Keeps RAM ≤ 7 GB.  
- **Batching:** Process videos in batches of 20 per model; streaming video URLs avoids loading full files into memory.  
- **Runtime estimate:** ≈ 0.8 s per inference on a 7 B quantized model → ~3.6 h total wall‑clock for 27 × 200 × 3 runs, well under the 6 h limit. Two models run concurrently to respect the 2‑core GitHub Actions runner.  
- **GPU escape hatch:** Not required for the main pipeline. If a model cannot load on CPU, the inference module catches the `RuntimeError` and automatically re‑runs that model on a free Kaggle GPU (`device="cuda"`). The off‑loaded run processes only the first 50 videos (sampled) to stay within the free‑GPU time budget.

## Prompt Templates (stored in `src/pipeline/prompts.py`)
- **Baseline:** `"You are shown a short video. Based on visual cues, rate the target's openness on a 1‑5 scale. Provide a brief reasoning and a grounding score (0–1) derived from the video metadata."`
- **Context‑Grounded:** `"Context: {context_profile}\n[Baseline prompt]"`  
- **Random‑Noise Control:** `"Context: {random_noise}\n[Baseline prompt]"` where `random_noise` is a 20‑word gibberish string.

All prompts are deterministic and version‑controlled.

## Metric Definitions
| Metric | Formula | Required Fields |
|--------|---------|-----------------|
| **Prejudice Rate (PR)** | `#(correct rating ∧ invalid grounding) / #valid samples` | `rating_correct`, `grounding_valid` |
| **Holistic‑Grounding Rate (HR)** | `#(correct rating ∧ valid grounding) / #valid samples` | same |
| **Integration‑failure Rate (IR)** | `#(output does NOT cite any context phrase) / #samples with context injected` | `context_cited` flag |

Grounding validity is computed via exact‑phrase overlap between the model’s reasoning string and the ground‑truth behavioral evidence tags. Ambiguous samples (≥ 2 contradictory behavior tags) are flagged as *grounding‑uncertainty* (FR‑011) and excluded from primary PR/HR calculations.

## Statistical Methodology (covers SC‑001, SC‑002, SC‑005)
1. **Primary test** – Paired comparison across models:  
   - If the distribution of PR differences is approximately normal → paired *t*-test.  
   - Otherwise → Wilcoxon signed‑rank test.  
   - **Multiple‑comparison correction:** Bonferroni across the three primary comparisons (baseline vs context, baseline vs noise, context vs noise).  
2. **Mixed‑effects secondary analysis** – Using `statsmodels` `MixedLM` with random intercepts for video ID and random slopes for model family (vision‑only vs. multimodal).  
3. **Confidence intervals** – 95 % CI via bootstrapping (10 000 resamples).  
4. **Sensitivity analysis (SC‑005)** – Sweep grounding‑overlap threshold ∈ {0.05, 0.10, 0.15}; recompute PR/HR and report false‑positive/false‑negative rates.  

All statistical code resides in `src/pipeline/analysis.py`.

## Resource‑Budget Monitoring (SC‑003, FR‑007)
- **Timer:** `time.perf_counter()` at start/end of each phase; aggregated in `data/derived/runtime_log.json`.  
- **Memory:** `psutil.Process().memory_info().rss` sampled every 5 s; peak recorded.  
- **Fallback trigger:** If total wall‑clock > 5.5 h **or** peak RAM > 6.5 GB, the orchestrator automatically:  
  1. Reduces the model list to the top‑15 (by baseline PR) **or**  
  2. Limits video frames per sample to 10 (instead of full video).  
  The chosen fallback is logged; the final results markdown includes a “Resource‑Constraint Note”.

## Validation & Contracts
- **JSON schema** for each output artifact (see `contracts/metric_record.schema.yaml`).  
- **Contract tests** (`pytest -m contract`) enforce schema compliance and guarantee that every figure/table traces back to a single row in the metric CSVs (Principle IV).  

## Deliverables
- CSVs: `baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv`.  
- Figures: PR reduction bar plot, IR histogram, sensitivity‑analysis line chart.  
- `results.md` summarizing hypothesis‑test outcomes, effect sizes, and resource‑budget status.  

---
