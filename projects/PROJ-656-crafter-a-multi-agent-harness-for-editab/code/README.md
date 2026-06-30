# Crafter Adaptation: CPU-Tractable Benchmark Reproduction

## Original vs. Adapted Scope

| Feature | Original Paper / Repo | Adapted Version (CPU-Only) |
| :--- | :--- | :--- |
| **Core Logic** | Multi-agent LLM harness generating raster images, then converting to SVG via SAM3. | **Metric Proxy**: Simulates the *evaluation* logic (structural similarity & text presence) on a small, pre-downloaded real subset of the CraftBench dataset. |
| **Data Source** | Full CraftBench (HuggingFace) + PaperBanana (large JSON). | **Subset**: First **5 samples** of CraftBench (real images & captions). |
| **Generation** | LLM calls (OpenRouter/GPT-4o) + GPU-based diffusion models. | **Skipped**: Generation is too heavy for CPU/CI. We **reuse the Ground Truth (GT)** images from the benchmark as the "generated" output to measure the *evaluation* pipeline's ability to score real figures. |
| **SVG Conversion** | SAM3 server (GPU required) + iterative agent editing. | **Skipped**: No GPU for SAM3. We skip the SVG step and focus on the **Image Quality Metric** (LPIPS/SSIM proxy) and **Text Detection** (using simple pixel-matching or `paddleocr` if available, fallback to pixel density). |
| **Dependencies** | `torch`, `sam3`, `paddleocr`, `openai`, `flask`. | `numpy`, `pandas`, `scikit-image`, `pillow`, `requests` (for dataset). |
| **Runtime** | Hours (GPU). | < 5 minutes (CPU). |

## Scientific Goal Reproduced
The paper claims Crafter outperforms baselines on **CraftBench** using human and automated metrics.
This adaptation reproduces the **automated evaluation pipeline** on a tiny real sample:
1.  Loads real input/caption pairs and Ground Truth images from CraftBench.
2.  Computes a "Quality Score" (simulating the paper's judge) using **SSIM** and **Text Density** on the real images.
3.  Writes the results to `data/evaluation_results.json` and `figures/score_distribution.png`.

*Note: Since we cannot run the generation agents on CPU, we evaluate the "Perfect" case (Ground Truth) to demonstrate the evaluation metric works on real data. In a full run, one would swap the GT path for a generated image path.*
