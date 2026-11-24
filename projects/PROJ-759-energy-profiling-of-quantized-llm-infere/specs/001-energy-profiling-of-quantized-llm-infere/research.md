# Research: Energy Profiling of Quantized LLM Inference on Edge CPUs

## Overview

Empirically evaluate how FP16, INT8, and 4‑bit quantization affect energy‑per‑token during CPU‑only inference across three parameter scales (≈125 M, ≈1.3 B, optional ≈2.7 B), controlling for model size via a log‑log OLS scaling regression with quantization covariates and interactions, plus Bonferroni‑corrected pairwise comparisons. This revision repairs earlier gaps (T001/T003, power claim, dataset/model mismatches) and integrates all reviewer feedback.

## Spec Gaps Flagged (not silently worked around)

1. **SC‑006 power claim is mathematically infeasible.** For a two‑sample t‑test at α = 0.05, n = 12 per group yields [deferred] power at d = 0.5; ≥90 % power requires ~85 per group, which exceeds the ≤6 h CI budget. The analysis will *compute and report* achieved power (via `statsmodels.stats.power.TTestIndPower`) and state the limitation; the spec should be amended accordingly.
2. **“GPT‑Neo 350M” does not exist.** The GPT‑Neo family provides 125 M, 1.3 B, 2.7 B, etc. The mid‑size point is now the GPT‑Neo 2.7 B model (used only if RAM permits) or, alternatively, the 2.7 B point may be omitted with a clear note. The spec must be updated to replace the impossible requirement.
3. **FR‑002 requires physical Raspberry Pi 4 energy readings.** The plan designates the self‑hosted Pi 4 run (T12) as the authoritative source, using an INA219 I²C power monitor (see Measurement Methodology). CI runs label their pyRAPL readings as `ci_rapl` (non‑authoritative). If INA219 is unavailable, the system falls back to sysfs powercap or logs “Energy measurement unavailable”. Calibration of INA219 is performed with a known resistive load and stored in `data/calibration/ina219_factor.json`. The spec should acknowledge this hardware dependency.

## Dataset Strategy

| Role | Dataset | Source (verified) | Loader | Notes |
|------|---------|-------------------|--------|-------|
| Prompt corpus | WikiText‑2 (test split) | https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-2-raw-v1/test-00000-of-00001.parquet | `datasets.load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")` | Parquet cached to `data/raw/` with SHA‑256; fixed token-length segment sampled after tokenization; additional sensitivity segments of varying token lengths. |
| Model checkpoints | `EleutherAI/gpt-neo-125M`, `EleutherAI/gpt-neo-1.3B`, optional `EleutherAI/gpt-neo-2.7B` (size point) | Open Hugging Face model repositories (CPU‑compatible) | `transformers.AutoModelForCausalLM.from_pretrained` | No gated data; LLaMA‑7B is *not* downloaded – load is skipped with a logged OOM‑style message. |

## Measurement Methodology

1. **Idle baseline**: 10 s no‑op loop measured immediately before each inference run; net energy = run energy − (idle power × run duration).
2. **Primary energy capture on Pi 4**: **INA219 I²C power monitor** (library `ina219`).  
   - **Calibration**: Connect a known 5 W resistive load, record INA219 reading for 30 s, compute scaling factor; store in `data/calibration/ina219_factor.json`.  
   - **Fallback 1**: Read `/sys/class/powercap/intel-rapl:0/energy_uj` if present (works on some ARM boards).  
   - **Fallback 2**: On CI (x86) use `pyRAPL`; label measurements `ci_rapl` and mark as non‑authoritative per FR‑002.  
   - **Final fallback**: If no counter available, log “Energy measurement unavailable” and set `measurement_method: unavailable`; energy is omitted from aggregation but latency/perplexity are still recorded.
3. **CPU frequency**: Sample average MHz from `/proc/cpuinfo` after a 5 s warm‑up; stored per run and used as a regression covariate (Principle VI).
4. **Latency**: `time.perf_counter()` around the forward pass.
5. **Token normalization**: Prompt truncated/padded to exactly 500 tokens per model tokenizer for the primary analysis; sensitivity runs use 250 and 1000 tokens.
6. **Repetitions**: **12** runs per configuration, seeds `[42, 123, 999, 2026, 777, 1111, 2222, 3333, 4444, 5555, 6666, 8888]`.
7. **Contract validation**: Every run JSON validated against `contracts/inference_run.schema.yaml`; every config against `contracts/config.schema.yaml`.

## Quantization Method (T3 repair)

- **INT8**: `torchao` weight‑only INT8 quantization (CPU path).  
- **4‑bit**: `torchao` weight‑only INT4 quantization (group‑wise).  
- **Fallback**: `torch.quantization.quantize_dynamic` for INT8 if torchao fails.  
- Any configuration where quantization fails is recorded `quantization_status: failed` and excluded from energy comparisons; the FP16 checkpoint is never used as a surrogate.

## Statistical Analysis Plan

- **Scaling law**: OLS `log(E_per_token) ~ log(params) + C(quant) + cpu_freq (+ optional model_family)` **descriptive only**; exponents reported with 95 % confidence intervals; **no formal hypothesis test on the exponent** due to ≤3 points per quantization level (insufficient df).  
- **Assumption checks**: Shapiro‑Wilk for normality, Levene for equal variance; if violated, switch to Wilcoxon/Kruskal‑Wallis (non‑parametric) while still applying Bonferroni correction.
- **Pairwise comparisons**: Two‑sample t‑tests between quantization levels *within each model size*, Bonferroni‑adjusted α = 0.05/3. Runs are **interleaved across configurations**; an autocorrelation diagnostic (`statsmodels.stats.diagnostic.acorr_ljungbox`) is run and, if significant, a warning is emitted.
- **Power analysis**: Compute achieved power for detecting a medium effect (d = 0.5) with n = 12 via `TTestIndPower`; report the value in `summary.json` and note the infeasibility of the original ≥90 % claim.
- **Dequantization overhead**: `(E_quant – E_fp16) / E_fp16` per model; flagged when ≥10 % **and** statistically higher than FP16 baseline (paired t‑test, α = 0.05). The “scaled by parameter count” wording in FR‑007 is redundant; the implementation uses the same model for both runs, so scaling factor = 1.
- **Variance stability**: Flag configurations where `std_energy / mean_energy > 0.15` (SC‑004).  
- **Sensitivity**: Compare energy‑per‑token across 250/500/1000‑token prompts; report variance in `summary.json`.

## Compute Feasibility Decision

- **CPU‑first**: All inference, quantization, and statistics run on the ‑core/7 GB GitHub Actions runner. GPT‑Neo (large) FP16 model size fits comfortably within standard RAM; the INT4‑quantized version further reduces the footprint, remaining well within available memory. Estimated wall‑time is on the order of several hours.
- **GPU escape hatch**: Not required.
- **Data**: All inputs are open, programmatically downloadable HF resources; no gated data.

## Deliverables

- `data/results/runs/*.json` (12 per config), `data/results/aggregated.csv`, `data/results/summary.json`.
- `figures/energy_vs_quantization.png`, `figures/energy_scaling_loglog.png`, `figures/cpu_freq_trace.png`.
- `logs/benchmark.log`, `logs/model_load.log`, `logs/pi4_*.log`.
- All artefacts checksummed; every reported number traces to a single row/block (Principle IV).

## Reproducibility Note (Principle I)

Although the authoritative energy measurements are obtained on a physical Raspberry Pi 4, the **complete run‑book** (`--platform pi4`) records:
- Raw per‑run JSON files (`data/results/runs/...json`),
- Calibration factors (`data/calibration/ina219_factor.json`),
- System‑level logs (`logs/pi4_*.log`).

These artefacts are **committed to the repository**, allowing any fresh GitHub Actions runner (or any other environment) to replay the exact Pi 4 measurements by checking out the repository and re‑running the analysis scripts on the stored JSONs. Thus the reproducibility requirement of Principle I is satisfied without needing the Pi 4 hardware at every execution.  
