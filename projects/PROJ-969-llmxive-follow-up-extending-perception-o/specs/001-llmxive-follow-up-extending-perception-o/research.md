# Research: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

## Overview
This document details the research‑ready design, data strategy, model selection, statistical methodology, and compute plan required to answer the primary hypothesis:

> **H₁**: Injecting explicit, text‑based social priors into MLLM prompts reduces the *Prejudice Rate* (PR) relative to the baseline prompting protocol.

A secondary hypothesis (**H₂**) asserts that a random‑noise control does **not** reduce PR, confirming that any observed effect is due to meaningful context rather than prompt length.

## Dataset Strategy
| Dataset | Access Method | Verified URL | Notes |
|---------|---------------|--------------|-------|
| **MM‑OCEAN validation subset** (≈ 200 videos) | Supposedly hosted with arXiv:2605.22109 | *No verified URL in the "# Verified datasets" block* | Not publicly downloadable; **FR‑001** cannot be satisfied directly. We will develop and validate the full pipeline on the open substitute and **re‑run** on the genuine MM‑OCEAN data once an official mirror is released. |
| **Open substitute** (`mmbench/ocean` on HuggingFace) | `datasets.load_dataset("mmbench/ocean", split="validation")` | https://huggingface.co/datasets/mmbench/ocean | Contains video references, transcripts, setting, culture, and behavior tags compatible with the required schema. Used for pipeline development, power analysis, and proof‑of‑concept. |

**Decision:** Build and test the entire pipeline on the open substitute. The final analysis must be reproduced on the authentic MM‑OCEAN subset when it becomes openly accessible; this limitation is explicitly flagged in the reporting.

## Model Selection & Inference Strategy
- **Model pool:** The 27 models listed in Table 2 of arXiv:2605.22109 (e.g., LLaVA‑1.5‑7B, Mini‑GPT‑4‑7B). All are open‑source and loadable via `transformers`.  
- **Quantization:** 4‑bit (`bitsandbytes`) on CPU; falls back to 8‑bit if 4‑bit fails. Keeps RAM ≤ 7 GB.  
- **Batching:** Process videos in batches of 20 per model; streaming video URLs avoids loading full files into memory.  
- **Runtime estimate:** ≈ 0.8 s per inference on a 7 B quantized model → ~3.6 h total wall‑clock for Multiple × 200 × 3 runs, well under the 6 h limit. Two models run concurrently to respect the 2‑core GitHub Actions runner.  
- **GPU escape hatch:** Not required for the main pipeline. If a model cannot load on CPU, the inference module catches the `RuntimeError` and automatically re‑runs that model on a free Kaggle GPU (`device="cuda"`). The off‑loaded run processes only the first 50 videos (sampled) to stay within the free‑GPU time budget.

## Prompt Templates (stored in `src/pipeline/prompts.py`)
- **Baseline:** `"You are shown a short video. Based on visual cues, rate the target's openness on a 1‑5 scale. Provide a brief reasoning and a grounding score (0–1) derived from the video metadata."`
- **Context‑Grounded:** `"Context: {context_profile}\n[Baseline prompt]"`  
- **Random‑Noise Control:** `"Context: {random_noise}\n[Baseline prompt]"` where `random_noise` is a 20‑word gibberish string.

All prompts are deterministic and version‑controlled.

## Metric Definitions (grounding assessed by a **blinded GPT‑4‑Turbo judge**)
| Metric | Formula | Required Fields |
|--------|---------|-----------------|
| **Prejudice Rate (PR)** | `#(correct rating ∧ grounding judged invalid) / #valid samples` | `rating_correct`, `grounding_valid` (from judge) |
| **Holistic‑Grounding Rate (HR)** | `#(correct rating ∧ grounding judged valid) / #valid samples` | same |
| **Integration‑failure Rate (IR)** | `#(output does NOT cite any phrase from the injected context) / #samples with context injected` | `context_cited` flag |

**Grounding validity** is computed by sending the model’s reasoning string and the ground‑truth behavioral evidence tags (from metadata) to a **blinded GPT‑4‑Turbo judge** (via the OpenAI API) which returns a binary judgment of “valid” vs. “invalid” grounding. This assessment is **independent of the injected context**, avoiding circularity.  

**Correct rating** is determined by matching the model’s trait rating to the ground‑truth trait label provided in the metadata.

Ambiguous samples (≥ 2 contradictory behavior tags) are flagged as *grounding‑uncertainty* (FR‑011) and excluded from primary PR/HR calculations to maintain measurement validity.

## Statistical Methodology (covers SC‑001, SC‑002, SC‑005)
1. **A priori power analysis** – Using `statsmodels.stats.power.TTestPower` with a presumed medium effect size (Cohen’s d ≈ 0.5), α = 0.05, paired n = 27 yields an estimated power of **≈ 0.65** (reported as `[deferred]` until the actual effect size is observed). We will report the observed power based on the realized effect size.  
2. **Primary test** – Paired comparison across models:  
   - If the distribution of PR differences is approximately normal → paired *t*-test.  
   - Otherwise → Wilcoxon signed‑rank test.  
   - **Multiple‑comparison correction:** Bonferroni across the three primary comparisons (baseline vs context, baseline vs noise, context vs noise).  
3. **Mixed‑effects secondary analysis** – Using `statsmodels` `MixedLM` with random intercepts for video ID and random slopes for model family (vision‑only vs. multimodal).  
4. **Confidence intervals** – 95 % CI via bootstrapping (10 000 resamples).  
5. **Sensitivity analysis (SC‑005)** – Sweep grounding‑judgment confidence threshold over {0.05, 0.10, 0.15}; recompute PR/HR and report false‑positive/false‑negative rates.  
6. **Quantization impact control** – Run a representative subset of 5 models at 8‑bit precision (and, for a tiny sample, full precision) to verify that quantization does not systematically bias the intervention effect; report any observed shift.  

All statistical code resides in `src/pipeline/analysis.py`.

## Resource‑Budget Monitoring (SC‑003, FR‑007)
- **Timer:** `time.perf_counter()` at start/end of each phase; aggregated in `data/derived/runtime_log.json`.  
- **Memory:** `psutil.Process().memory_info().rss` sampled every 5 s; peak recorded.  
- **Predefined fallback:** Before any inference runs, a **pre‑specified fallback configuration** (top‑15 models chosen a priori based on prior literature and a fixed 10‑frame‑per‑video sampling strategy) is logged. If total wall‑clock > 5.5 h **or** peak RAM > 6.5 GB, the orchestrator aborts and re‑runs with this configuration. The fallback is determined **before** any data are processed, eliminating selection bias.  
- **Fallback trigger:** If limits are exceeded, the pipeline automatically switches to the pre‑configured subset and sampling scheme; the chosen fallback is logged; the final results markdown includes a “Resource‑Constraint Note”.

## Condition Order Randomization (internal validity)
For each model‑video pair, the order of the three conditions (baseline, context, noise) is **randomly permuted** using a fixed random seed (`np.random.seed(42)`) to ensure reproducibility while counterbalancing potential order effects.

## Validation & Contracts
- **JSON schema** for each output artifact (see `contracts/metric_record.schema.yaml`).  
- **Contract tests** (`pytest -m contract`) enforce schema compliance and guarantee that every figure/table traces back to a single row in the metric CSVs (Principle IV).  

## Deliverables
- CSVs: `baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv`.  
- Figures: PR reduction bar plot, IR histogram, sensitivity‑analysis line chart.  
- `results.md` summarizing hypothesis‑test outcomes, effect sizes, observed power, and resource‑budget status.  

---



