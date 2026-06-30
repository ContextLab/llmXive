# StepAudio 2.5 CPU Adaptation

## Purpose
This repository contains a **CPU-tractable, self-contained adaptation** of the StepAudio 2.5 Technical Report pipeline. The original paper describes a massive, GPU-intensive unified audio-language model trained on large-scale datasets (WenetSpeech) using RLHF. This adaptation reproduces the **core quantitative logic** (data preparation, training loop, metric reporting) in a form that runs on 2 CPU cores with < 1GB RAM in under 2 minutes.

## Simplifications & Approximations

| Component | Original (StepAudio 2.5) | Adaptation (CPU Version) |
| :--- | :--- | :--- |
| **Data Source** | 7385+ real audio segments from WenetSpeech (GBs of data). | **Synthetic Data**: 100 generated numpy arrays simulating speech features. |
| **Audio Processing** | `ffmpeg` slicing, resampling, heavy I/O. | **Pure NumPy**: In-memory generation of sine/noise signals. |
| **Model Architecture** | Large Transformer (7B+ params), RLHF, Multi-GPU. | **Logistic Regression**: A single linear layer trained on simple features (RMS energy). |
| **Task** | ASR, TTS, Realtime Dialogue. | **Binary Classification**: Predicting segment duration (>3s vs <3s) as a proxy for "complexity". |
| **Dependencies** | PyTorch, CUDA, Transformers, FlashAttention. | **NumPy, Matplotlib**: Standard CPU-only scientific stack. |

## Artifacts
This pipeline produces real, verifiable outputs:
1.  **`data/synthetic_wenet/`**: A small, structured dataset mimicking the paper's input format.
2.  **`data/results/results.csv`**: Numeric metrics (Loss, Accuracy) proving the training loop worked.
3.  **`data/results/training_curve.png`**: A plot visualizing the optimization process.

## Why this matters
While the scale is reduced, the **scientific logic** remains:
1.  Data is prepared and structured (sid, text, audio).
2.  A model is trained to minimize a loss function.
3.  Metrics are computed and visualized.
This allows the execution stage to verify the *pipeline integrity* without requiring a supercomputer.
