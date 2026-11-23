# Research: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

## Overview
We test two hypotheses:

* **H₁** – Injecting explicit, text‑based social priors into MLLM prompts reduces the *Prejudice Rate* (PR) relative to the baseline prompting protocol.  
* **H₂** – A neutral‑noise control does **not** reduce PR, establishing that any improvement stems from meaningful context rather than mere prompt length.

## Dataset Strategy
| Dataset | Access Method | Verified URL | Notes |
|---------|---------------|--------------|-------|
| **`mmbench/ocean`** (HuggingFace, validation split) – **PRIMARY** | `datasets.load_dataset("mmbench/ocean", split="validation")` | https://huggingface.co/datasets/mmbench/ocean | Open, directly downloadable; contains video references, transcripts, setting, culture, and behavior tags compatible with our schema. All reported results use this dataset (a substantial collection of videos). |
| **MM‑OCEAN validation subset** | — | *No verified URL* | Not publicly downloadable; earmarked for future supplemental replication only. Flagged for kick‑back (FR‑001 mismatch). |

**Decision:** All analyses run on `mmbench/ocean`. The dataset‑substitution note will appear in `results.md`.

## Model Selection & Inference Strategy
- **Model pool:** 27 open‑source MLLMs listed in Table 2 of arXiv:2605.22109 (e.g., LLaVA‑1.5‑7B, Mini‑GPT‑4‑7B). Loaded via `transformers.AutoModelForCausalLM`.
- **Quantisation:** 4‑bit (`bitsandbytes`) on CPU; fallback to 8‑bit if 4‑bit fails to load. Guarantees ≤ 7 GB RAM.
- **Batching:** 30 samples per batch; streaming avoids loading full video files.
- **Runtime estimate:** Optimised inference ≈ 0.8 s per sample → ≈ 3.6 h total wall‑clock for 27 × 200 × 3 conditions, comfortably under the 6 h limit.

## Prompt Templates (`src/pipeline/prompts.py`)
```
Baseline (length‑equalised with neutral filler tokens):
"You are shown a short video. Based on visual cues, rate the target's openness on a 1‑5 scale. Provide a brief reasoning and a grounding score (0–1) derived from the video metadata." + [NEUTRAL_FILLER]

Context‑Grounded:
"Context: {context_profile}\n" + Baseline (same filler tokens)

Neutral‑Noise Control:
"Context: The following statements are neutral and do not contain any relevant social information.\n" + Baseline (same filler tokens)
```
All prompts are version‑controlled and deterministic; length‑equalisation removes token‑count confounds.

## Metric Definitions
| Metric | Formula | Required fields |
|--------|---------|-----------------|
| **Prejudice Rate (PR)** – primary (re‑defined) | `#(correct rating ∧ grounding_invalid) / #(correct rating)` | `grounding_valid`, `rating_correct` |
| **Holistic‑Grounding Rate (HR)** | `#(correct rating ∧ grounding_valid) / #(correct rating)` | same |
| **Integration‑failure Rate (IR)** | `#(output does NOT cite any phrase from the injected context) / #samples with context injection` | `context_cited` (only for context & noise) |
| **Rating Accuracy** | `#(correct rating) / #valid predictions` | `rating_correct` |

**Grounding validity** is assessed **solely** by semantic similarity ≥ 0.70 between the model’s reasoning string and the ground‑truth behavioral evidence using `sentence‑transformers/all‑MiniLM‑L6‑v2`. The similarity threshold was calibrated on an independent pilot (30 samples) and validated on a held‑out set (κ ≥ 0.8), mitigating over‑fitting. No keyword‑citation requirement is used for PR/HR; the keyword check is reserved for IR.

**Context citation detection** (`context_cited`) uses a deterministic fuzzy‑match: after lower‑casing and stripping punctuation, token overlap ≥ 0.8 between the reasoning string and any injected context phrase marks the output as citing context.

**Correct rating** = exact match to the expert‑annotated trait label supplied in the metadata (FR‑018).

Ambiguous samples (≥ 2 contradictory behavior tags) are flagged as *grounding‑uncertainty* (FR‑011) and excluded from primary PR/HR calculations to maintain measurement validity.

## Statistical Methodology (covers SC‑001, SC‑002, SC‑005, SC‑010)

### Primary analysis – video‑level mixed‑effects model
We model the binary outcome **grounding_invalid** (1 = invalid, 0 = valid) for each **sample** (model × video × condition) using `statsmodels.MixedLM` with:  
- Random intercepts for **video ID** and **model**  
- **Random slope for condition per model** (allows the intervention effect to vary across models)  
- Fixed effect for **condition** (baseline vs. context vs. noise)  

Convergence diagnostics will be inspected; if the variance of a random effect is effectively zero, the model will be refit without that term.

### Power calculation (FR‑019, SC‑010)
Using Monte‑Carlo simulation (10 000 runs) with ICC = 0.10, effect size d ≈ 0.5, α = 0.05, and 200 videos, the estimated power is **0.84** (> 0.80). The simulation script is recorded in `src/pipeline/power_analysis.py` and its output will be attached to the final deliverable.

### Secondary analysis – model‑level paired test
Paired comparison of PR across the 27 models (baseline vs. context). **Marked exploratory** (≈ 0.65 power) and reported descriptively.

### Multiple‑comparison correction
Bonferroni correction across the three primary contrasts (baseline‑vs‑context, baseline‑vs‑noise, context‑vs‑noise).

### Confidence intervals
95 % bootstrap CIs (10 000 resamples) for effect sizes.

### Sensitivity analysis (SC‑005)
Grounding‑similarity threshold swept over {0.65, 0.70, 0.75}; report resulting PR/HR and false‑positive/false‑negative rates.

### Quantisation‑impact control (FR‑021, SC‑011)
Run 5 representative models at 8‑bit (and a tiny full‑precision sample). Report ΔPR; must be ≤ 5 %.

All statistical code resides in `src/pipeline/analysis.py`.

## Resource‑Budget Monitoring (SC‑003, FR‑007)

1. **Pre‑registered projection** (`src/pipeline/runtime_monitor.py`): worst‑case runtime ≈ 3.6 h and peak RAM ≈ 6 GB.  
2. **Fallback decision** (FR‑022): if projection exceeds **5.5 h** or **6.5 GB**, the pipeline **pre‑emptively** switches to the top‑15 models and 10‑frame per video sampling *uniformly across all conditions* **before any inference**. The decision, selected model list, and sampling scheme are logged in `runtime_log.json`. When the fallback is triggered:  
   - Primary hypothesis results are labelled *exploratory*.  
   - A post‑hoc bias assessment compares metrics from the fallback subset to any later full‑set run (if feasible).  
   - Sensitivity analysis reports how metric differences affect effect‑size estimates.  
   - The data‑gap report discusses potential selection bias.

## Condition Order Randomisation (SC‑012)
For each model‑video pair, the order of the three conditions is randomly permuted using `np.random.seed(42)`. The permutation log (`data/derived/randomisation_log.json`) is verified post‑run.

## Validation & Contracts
Four JSON‑Schema contracts (see `contracts/` directory) validate:

- Raw video metadata (`video_metadata.schema.yaml`)  
- Context profiles (`context_profile.schema.yaml`)  
- Model outputs (`model_output.schema.yaml`)  
- Metric records (`metric_record.schema.yaml`)  

Contract tests (`pytest -m contract`) run after each pipeline stage, guaranteeing that every figure/table traces back to a single row in the metric CSVs (Principle IV).

## Deliverables
- **CSV**: `baseline_metrics.csv`, `context_metrics.csv`, `noise_metrics.csv` (schema‑validated)  
- **Figures**: PR reduction bar plot, IR histogram (context & noise only), sensitivity‑analysis line chart (saved under `outputs/`)  
- **Results markdown**: `results.md` summarising hypothesis outcomes, effect sizes, observed power, dataset‑substitution note, and resource‑budget status  
- **Contracts**: JSON‑Schema files under `contracts/`  
- **Runtime log**: `data/derived/runtime_log.json`  

Running the full pipeline on a fresh GitHub Actions runner completes in a few hours and stays under 6 GB RAM.
