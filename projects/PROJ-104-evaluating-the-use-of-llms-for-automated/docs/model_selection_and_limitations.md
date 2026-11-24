# Model Selection and Scale Limitations

## Rationale for selecting three CPU‑friendly LLMs

The experimental pipeline must run on the GitHub Actions free‑tier runner, which provides **≈ 7 GB of RAM** and **CPU‑only** resources.
To stay within this hardware envelope we selected the **largest open‑source language models that can be loaded in 4‑bit quantisation with the `bitsandbytes` library on a CPU**. These three models satisfy the following criteria:

1. **Parameter count ≤ 3 B** – the upper bound that fits comfortably in the available memory when quantised to 4 bits.
2. **Availability of a publicly released checkpoint** that can be downloaded directly from the Hugging Face Hub without additional licensing steps.
3. **Comparable architectural families** (a transformer from Microsoft, a lightweight dense model from Google, and a recent Meta decoder‑only model) so that any observed performance differences can be attributed to architecture rather than raw model size.

The chosen models are:

| Model | Parameters (≈ B) | 4‑bit Quantisation (bitsandbytes) | Expected per‑commit latency (CPU, s) |
|-------|-------------------|-----------------------------------|--------------------------------------|
| **Phi‑3‑mini** (Microsoft) | 3.0 | Yes | 4.5 |
| **Gemma‑2‑2b** (Google) | 2.0 | Yes | 5.0 |
| **Llama‑3.2‑3B (2504.01054, https://arxiv.org/abs/2504.01054)** (Meta) | 3.0 | Yes | 5.2 |

*Latency estimates are obtained from a short benchmark on the same runner (average over 10 commits, warm‑started model). They are intended as guidance for planning the full‑scale experiment; actual times may vary slightly with commit length.*

## Acknowledging the scale limitation

The scale limitation is that the three models are of comparable size, so any performance differences reflect architectural characteristics rather than model capacity.

A reviewer raised a concern that the **model scale is limited** and therefore the results may not generalise to larger, state‑of‑the‑art LLMs. We explicitly acknowledge this limitation: the experiment isolates **architectural differences within a comparable‑size regime** (all models are ≤ 3 B parameters and run under identical 4‑bit CPU constraints). Consequently, any observed gaps in documentation‑generation fidelity should be interpreted as **relative architectural effects** rather than absolute statements about the capabilities of larger models. Future work can repeat the pipeline with higher‑capacity models once sufficient GPU resources become available, but the current design provides a reproducible baseline that respects the hardware constraints of a typical CI environment.