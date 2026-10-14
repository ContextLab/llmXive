# Research: Energy Profiling of Quantized LLM Inference on Edge CPUs

## Overview
We will empirically evaluate how three quantization schemes—FP16, INT8, and 4‑bit—affect **energy‑per‑token** during inference of three GPT‑Neo model sizes (a small‑scale model, 350 M, 1.3 B) on a CPU‑only environment that mimics an edge device (GitHub Actions free‑tier runner). An optional validation run on a Raspberry Pi 4 will confirm proxy fidelity. The study integrates a scaling analysis (log‑log OLS with quantization covariate) and rigorous hypothesis testing (Bonferroni‑corrected t‑tests or non‑parametric alternatives).

## Dataset Strategy
| Role | Dataset | Source (verified URL) | Loader | Notes |
|------|---------|------------------------|--------|-------|
| Prompt corpus | WikiText‑2 (test split) | https://huggingface.co/datasets/EleutherAI/wikitext_document_level/resolve/main/wikitext-103-raw-v1/wikitext-103-raw-v1-test.parquet | `datasets.load_dataset("EleutherAI/wikitext_document_level", split="test", streaming=False)` | Parquet; checksum recorded; sampled to a **fixed‑length 500‑token** prompt after tokenization. |
| Model checkpoints | GPT‑Neo 125M / 350M / 1.3B | https://huggingface.co/EleutherAI/gpt-neo-125M (similarly for 350M & 1.3B) | `transformers.AutoModelForCausalLM.from_pretrained` | Open‑source, CPU‑compatible. |
| Optional LLaMA‑7B | LLaMA‑7B (public HF mirror) | *No verified open URL* → Attempted load only; if OOM, skip and log. | — | Not required for primary analysis. |

All data are fetched programmatically; no manual steps.

## Measurement Methodology
1. **Baseline idle power** – run a short no‑op loop (`for _ in range(10_000_000): pass`) while `pyRAPL` records power; subtract this from the inference measurement.  
2. **Primary energy capture** – use `pyRAPL.Measurement` to record Joules during the forward pass. If `pyRAPL` raises `RuntimeError`, fall back to `powerstat -d 1 -c 1`; if both fail, log *Energy measurement unavailable* and omit energy from aggregation (FR‑002 fallback).  
3. **Validation of energy readings** – run a known synthetic workload (e.g., matrix multiplication) and compare `pyRAPL` readings to `powerstat` (or an external calibrated wattmeter if available). Record the absolute difference; if it exceeds **[deferred]**, report measurement uncertainty in the final log.  
4. **CPU frequency handling** – after each run we read `/proc/cpuinfo` to capture the current frequency, wait up to 5 s for the frequency to stabilize (no change > 50 MHz), and record the average frequency. The observed frequency is later included as a covariate in the regression to control for residual scaling/throttling.  
5. **Latency** – measured with `time.perf_counter()` around the inference call.  
6. **Token count & normalization** – tokenized prompt is truncated/padded to exactly **500 tokens** for every model, ensuring a constant denominator.  
7. **Perplexity** – computed from model logits on the same prompt; stored for completeness.  
8. **Repetitions** – **ten** runs per configuration with hard‑coded seeds `[42, 123, 999, 2026, 777, 1111, 2222, 3333, 4444, 5555]`.  
9. **Contract validation** – each `InferenceRun` JSON is validated against `contracts/inference_run.schema.yaml`; failures abort the run and are logged.

All repetitions are deterministic once seeds are fixed.

## Statistical Analysis Plan
- **Scaling law**: Fit OLS `log(Energy_per_token) ~ log(Parameter_count) + C(Quantization) + Frequency` using `statsmodels`. Report slope (exponent) per quantization and overall.  
- **Power analysis**: Using `statsmodels.stats.power.TTestIndPower`, we confirm that **10 repetitions give ≥ 80 % power** to detect a medium effect (Cohen’s d ≈ 0.5) at α = 0.05; this justification is documented in the analysis script.  
- **Assumption checks**: Shapiro‑Wilk normality & Levene equal‑variance per quantization. If violated, switch to Wilcoxon signed‑rank (pairwise) or Kruskal‑Wallis (multiple) while still applying Bonferroni correction.  
- **Pairwise comparisons**: Two‑sample t‑tests between quantization levels for each model size when assumptions hold; Bonferroni correction (`α_adj = 0.05 / 3`). Use non‑parametric equivalents if assumptions fail, still applying Bonferroni.  
- **Dequantization overhead**: Compute `(energy_quant - energy_fp16) / energy_fp16`. Flag when **≥ 10 %** **and** statistically significant (p < 0.05) vs. FP16 baseline (FR‑007).  
- **Variance stability**: Verify `std_energy_per_token / mean_energy_per_token ≤ 0.15` for each configuration; violations flagged (SC‑004).  

All statistical code lives in `code/utils/stats.py` and is unit‑tested.

## Edge‑Case Handling
| Situation | Detection | Response |
|-----------|-----------|----------|
| `pyRAPL` unavailable | ImportError / RuntimeError on init | Switch to `powerstat`; if also unavailable, log and skip energy aggregation. |
| Model OOM on load | `MemoryError` or torch OOM | Log `"Model {name} OOM, skipping"`; set `load_success: false`. |
| Quantization failure | Exception from `auto-gptq` or `bitsandbytes` | Fall back to FP16 for that config; record `quantization: fp16`. |
| WikiText download failure | HTTP error / missing file | Abort with clear error; dataset is mandatory. |
| Tokenizer returns zero tokens | `len(tokens) == 0` | Abort that run, log warning, retry with next seed. |
| Frequency instability > 5 % | Recorded frequency deviates > 5 % after stabilization wait | Log warning; include frequency as covariate. |
| Measurement validation discrepancy | Comparison of `pyRAPL` vs. `powerstat` on known workload exceeds 10 % | Record uncertainty in logs and propagate as additional variance term. |

All failures are graceful, satisfying FR‑002 fallback clauses.

## Compute Feasibility Decision
- **CPU‑first**: All inference, quantization, and analysis steps run on CPU and stay within the available RAM constraints when using low‑precision (e.g., sub‑byte) models.  
- **GPU escape hatch**: Not required.  
- **Runtime budget**: Estimated total wall‑time is comfortably within the CI time limit.

## Deliverables
- `data/results/aggregated.csv` – per‑configuration mean ± std.  
- `data/results/summary.json` – regression exponent, p‑values, overhead flags.  
- Figures: `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`.  
- Full logs under `logs/` for reproducibility.  
- Optional Raspberry Pi 4 logs (`logs/pi4_*.log`).  

All artifacts will be checksummed and referenced in the final paper, satisfying the Single Source of Truth principle.

---



