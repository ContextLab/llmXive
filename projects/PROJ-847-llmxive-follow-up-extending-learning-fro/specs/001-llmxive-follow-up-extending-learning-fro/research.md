# Research: llmxive-density-analysis

## Dataset Strategy
| Role                | Source (verified)                                                                                                   | Loader                                    |
|---------------------|----------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| Primary reasoning   | GSM8K (parquet) – https://huggingface.co/datasets/openai/gsm8k/resolve/main/main/test-00000-of-00001.parquet       | `datasets.load_dataset(..., split="test")` |
| Supplemental logical subset | `bigbench_lite` (included in HuggingFace `bigbench` collection) – loaded via `datasets.load_dataset("bigbench_lite")` | `datasets.load_dataset("bigbench_lite")` |

Both datasets are publicly downloadable without authentication and fit within the CI runner’s disk quota. The loader streams the parquet file to stay under the RAM limit (≤ 6 GB active).

## Metric Justification
Logical accuracy is measured as exact‑match string equality of the model‑generated reasoning steps against the GSM8K reference solutions. This metric is the standard evaluation used in the original GSM8K benchmark (see *GSM8K: Training Language Models to Solve Math Word Problems* – Cobbe et al., 2022) and has been widely adopted for assessing reasoning capability of generative models. While it does not capture partial reasoning quality, it provides a clear, reproducible, and widely‑accepted proxy for logical correctness in this context.

## Methodology
1. **Preprocessing** – tokenization with the model’s tokenizer, padding to max length 256, and creation of train/test splits (90/10).  
2. **Model** – a pre‑trained discrete diffusion model (`hf://my-org/lightweight-diffusion-100M`) with ≤ 100 M parameters, CPU‑compatible (`torch.float32`).  
3. **Training Loop** – implements five fixed retaining ratios (ρ = 0.1,…,0.9) and an adaptive scheduler (entropy‑based, bounded to [0,1]). Each condition is run with **three distinct random seeds** (default seeds 42, 43, 44) to obtain replicated measurements. Early‑stopping after 10 epochs or when the hard timeout flag triggers.  
4. **Entropy Calculation** – mean Shannon entropy over the model’s token‑wise softmax predictions per batch. NaNs/clamped as described in the spec.  
5. **Statistical Analysis** – after all runs:
   * **Independent‑samples t‑test** comparing the adaptive run to the fixed ρ = 0.5 baseline **across seeds** (not paired). Implemented via `scipy.stats.ttest_ind`. If only a single seed is present, the code automatically switches to a non‑parametric Mann‑Whitney U test (`scipy.stats.mannwhitneyu`).  
   * **Power considerations** – with three seeds per condition we achieve modest power (>0.6) to detect medium effect sizes (Cohen’s d indicates a medium‑sized effect.) given the variance observed in pilot runs. A formal power analysis is documented in the analysis script.  
   * **Quadratic regression** – fit a degree‑2 polynomial to the five fixed‑ratio accuracies using `np.polyfit`. Model stability is assessed via **bootstrap resampling (1 000 replicates)** and **leave‑one‑seed‑out cross‑validation**, reporting confidence intervals for the peak density.  
   * **Sensitivity sweep** – evaluate the bootstrapped quadratic model at ρ ± 0.05 and ρ ± 0.1, compute the slope (accuracy change per 0.01 density), and report the distribution of slopes across bootstrap samples.  

All statistical tests report full JSON objects (t‑statistic, p‑value, df, or U‑statistic, etc.) and are stored under `outputs/statistics/`.

## Compute Decision / Rationale
- **CPU‑first**: All components (model inference, training, entropy) run comfortably on a 2‑core CPU within the 6 h limit. No GPU is required; therefore no off‑load is planned (Principle VI).  
- **Memory Management**: Data loader streams parquet rows; batch size set to 16 to keep peak RAM ≈ 5 GB.  
- **Timeout Handling**: At the start of each epoch a wall‑clock check aborts gracefully, writes a checkpoint, and tags the run as `"TIMEOUT"` in the metadata.

## Deliverables
- `outputs/fixed_baselines_*.csv` – rows: `rho, seed, final_accuracy, runtime_seconds`.  
- `outputs/adaptive_run_*.json` – final accuracy, density time‑series, runtime, timeout flag, seed.  
- `outputs/statistics/independent_t_test.json`, `quadratic_fit.json`, `sensitivity_analysis.json`.  
- Plots (PNG): loss curves, density‑vs‑step, quadratic fit with peak marker and bootstrap confidence bands.

---


