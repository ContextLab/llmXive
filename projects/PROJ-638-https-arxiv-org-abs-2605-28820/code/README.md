# Adaptation: NEO-ov Core Metric Reproduction (Scaled-Down)

## Goal
Reproduce the core quantitative claim of the paper "From Pixels to Words": that a **native** vision-language architecture (end-to-end, no external encoders) can achieve competitive performance on a fine-grained visual perception task compared to a modular baseline, when trained on a scaled-down subset.

## Simplifications vs. Original
1.  **Model Architecture (Proxy):** The original NEO-ov is a massive, custom-trained Transformer. We cannot retrain it. Instead, we implement a **Tiny Native Proxy**: a minimal Transformer that processes image tokens (via a lightweight CNN) and text tokens jointly in a single forward pass (no separate encoder/decoder fusion). We compare this against a **Tiny Modular Proxy**: a standard CNN image encoder + a frozen LLM text head with a simple projection layer.
2.  **Dataset:** We use a **small subset (N=200)** of the **VCR-Bench** (Visual Commonsense Reasoning) dataset, which tests fine-grained visual reasoning. The full dataset is large; this subset is sufficient to demonstrate the metric difference on CPU.
3.  **Training:** We perform **5 epochs** of training on the small subset.
4.  **Compute Target:** **CPU**. The proxy models are tiny (<10M params) and designed to run on 2 cores. The original paper requires GPUs for the full scale, but the *relative advantage* of the native architecture on small data is the key finding we are reproducing.
5.  **Metric:** We measure **Exact Match Accuracy** on the multiple-choice reasoning task.

## Output Artifacts
- `data/results.csv`: Contains the accuracy scores for both the Native Proxy and Modular Proxy.
- `figures/accuracy_comparison.png`: A bar chart comparing the two models.

## Why this is valid
The paper argues that removing modular boundaries improves fine-grained signal flow. By implementing a "Native" vs. "Modular" proxy on the *same* small dataset and measuring the same metric, we isolate the architectural impact, faithfully reproducing the *logic* of the core claim, even if the absolute numbers differ from the full-scale paper.
