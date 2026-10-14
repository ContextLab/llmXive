# Research: Energy Profiling of Quantized LLM Inference on Edge CPUs

## Overview
We will empirically evaluate how three quantization schemes—FP with reduced precision, INT8, and 4‑bit—affect **energy‑per‑token** during inference of three GPT‑Neo model sizes (small, 350 M, 1.3 B) on a CPU‑only environment that mimics an edge device (GitHub Actions free‑tier runner). An optional validation run on a Raspberry Pi 4 will confirm proxy fidelity. The study integrates a scaling analysis (log‑log OLS with quantization covariate) and rigorous hypothesis testing (Bonferroni‑corrected t‑tests or non‑parametric alternatives).

## Dataset Strategy
| Role | Dataset | Source (verified URL) | Loader | Notes |
|------|---------|------------------------|--------|-------|
| Prompt corpus | WikiText‑2 (test split) | https://huggingface.co/datasets/EleutherAI/wikitext_document_level/resolve/main/wikitext-103-raw-v1/wikitext-103-raw-v1-test.parquet | `datasets.load_dataset("EleutherAI/wikitext_document_level", split="test", streaming=False)` | Parquet file; checksum recorded; sampled to a **fixed‑length 500‑token** prompt after tokenization. |
| Model checkpoints | GPT‑Neo 125M / 350M / 1.3B | https://huggingface.co/EleutherAI/gpt-neo-125M (similarly for 350M & 1.3B) | `transformers.AutoModelForCausalLM.from_pretrained` | Open‑source, CPU‑compatible. |
| Optional LLaMA‑7B | LLaMA‑7B (any public HF mirror) | *No verified open URL* → Attempted load only; if OOM, skip and log. | — | Not required for primary analysis. |

All data are fetched programmatically; no manual download steps.

## Measurement Methodology
1. **Baseline idle power**: Immediately before each inference run, execute a A short‑duration no‑op loop (e.g., `for _ in range(N): pass`). while `pyRAPL` records the average power. This value is subtracted from the inference measurement to isolate model‑execution energy.
2. **Primary energy capture**:  
   - Use `pyRAPL` (`pyRAPL.Measurement`) to record Joules consumed during the forward pass of the model on the prepared prompt.  
   - If `pyRAPL` raises `RuntimeError` (e.g., missing RAPL interface), fall back to `powerstat -d 1 -c 1` via `subprocess`; parse the reported energy.  
   - If both fail, log `"Energy measurement unavailable"` and continue; the run contributes latency but not energy statistics (FR‑002 fallback clause).
3. **CPU frequency control**: Before any benchmark, set the CPU governor to **performance** (`cpupower frequency-set -g performance`) and record the current frequency (`/proc/cpuinfo`) and temperature (`sensors`) before and after each run. These values are logged for later normalization.
4. **Latency**: Measured with `time.perf_counter()` surrounding the inference call.
5. **Token count & normalization**: The prompt is tokenized **once** using the model’s tokenizer, then truncated or padded to exactly **500 tokens** for every model, ensuring a consistent token count across configurations and eliminating the confound noted in the spec.
6. **Perplexity**: Computed on the same prompt using the model’s logits (optional but stored for completeness).
7. **Repetitions**: Five independent runs per configuration with distinct hard‑coded seeds (`42`, `123`, `999`, `2026`, `777`). This improves power and satisfies the revised SC‑004 variance stability requirement.
8. **Contract validation**: After each run, the generated `InferenceRun` JSON is validated against `contracts/inference_run.schema.yaml`. Failures abort the run and are logged.

All three repetitions per configuration use distinct random seeds and are deterministic once the seeds are fixed.

## Statistical Analysis Plan
- **Scaling law**: Fit a multiple‑regression OLS model  
  `log(Energy_per_token) ~ log(Parameter_count) + C(Quantization)`  
  using `statsmodels.api.OLS`. Report the slope (exponent) for each quantization level and the overall model. If only two model sizes are available, report the deterministic slope without confidence intervals (SC‑003 clause).
- **Assumption checks**: For each group (quantization level) perform Shapiro‑Wilk normality test and Levene’s equal‑variance test. If normality or equal variance fails, switch to non‑parametric Wilcoxon signed‑rank (pairwise) or Kruskal‑Wallis (multiple) tests.
- **Pairwise comparisons**: Conduct two‑sample t‑tests between quantization levels for each model size when assumptions hold; apply Bonferroni correction (`α_adj = 0.05 / 3`). If assumptions fail, use the appropriate non‑parametric test and still apply Bonferroni correction.
- **Dequantization overhead**: Compute `(energy_quantized - energy_fp16) / energy_fp16`. Flag when this ratio ≥ 0.05 **and** the increase is statistically significant (p < 0.05) relative to the FP16 baseline for the same model size.
- **Power analysis**: With five repetitions, a two‑sample t‑test detecting a medium effect size (Cohen’s d indicating a medium magnitude) achieves ≈ 70 % power at α = 0.05. This limitation is documented in the discussion.
- **Variance stability**: Verify `std_energy_per_token / mean_energy_per_token ≤ 0.15` for each configuration; violations are flagged in the aggregated results (SC‑004).

All statistical code resides in `code/utils/stats.py` and is covered by unit tests.

## Edge‑Case Handling
| Situation | Detection | Response |
|-----------|-----------|----------|
| `pyRAPL` unavailable | `ImportError` or `RuntimeError` on init | Switch to `powerstat`; if also unavailable, log and skip energy aggregation for that run. |
| Model OOM on load | `torch.cuda.OutOfMemoryError` (or CPU memory error) | Log `"Model {name} OOM, skipping"`; continue with remaining configs. |
| Quantization failure (e.g., unsupported op) | Exception from `auto_gptq` quantizer | Log error, fallback to FP16 for that config. |
| WikiText download failure | HTTP error / missing file | Abort run with clear error; dataset is mandatory per constitution. |
| Tokenizer returns zero tokens | `len(tokens) == 0` | Abort that run, log warning, and retry with next random seed. |
| CPU frequency scaling unexpectedly changes | Recorded frequency deviates > 5 % from baseline | Log warning; include frequency trace in final report for transparency. |

All failures are **graceful**; the pipeline proceeds with whatever data are available, satisfying FR‑002 fallback clauses.

## Compute Feasibility Decision
- **CPU‑first**: All inference, quantization, and statistical steps are CPU‑bound and fit within the available RAM limit when using the 4‑bit variant (≈ 1 GB)..  
- **GPU escape hatch**: Not required; no method mandates CUDA.  
- **Runtime budget**: Estimated total wall‑time is on the order of several hours (several configurations × 5 runs × approximately several minutes each). plus a brief analysis, comfortably under the 6‑hour CI limit..

## Deliverables
- `data/results/aggregated.csv` – per‑configuration mean ± std.  
- `data/results/summary.json` – regression exponent, p‑values, overhead flags.  
- `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`.  
- Full logs (`logs/benchmark_*.log`) for reproducibility.  
- Optional Raspberry Pi 4 run logs (`logs/pi4_*.log`) for edge‑hardware validation.

All artifacts will be checksum‑recorded and referenced in the final paper.

---

