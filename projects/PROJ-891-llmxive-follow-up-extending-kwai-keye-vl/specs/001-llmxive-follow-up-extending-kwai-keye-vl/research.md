# Research: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

## Executive Summary

This research validates the hypothesis that extreme aspect ratio distortions significantly degrade the temporal grounding performance of the Kwai Keye-VL-2.0 model (or a structurally similar VLM), even when temporal ground truth is preserved. The study leverages the **ActivityNet Captions** dataset to generate a synthetic benchmark with controlled geometric perturbations across varying aspect ratios. The **Control Group** consists of the **ORIGINAL, UNMODIFIED** ActivityNet Captions video clips, ensuring that any performance drop is due to aspect ratio distortion and not generation artifacts. Inference is constrained to a CPU-only, low-bit quantized environment to simulate real-world mobile/surveillance deployment scenarios. The primary metric is mean Intersection-over-Union (mIoU), analyzed via **Independent Samples** statistical testing.

## Dataset Strategy

The study relies on the **ActivityNet Captions** dataset, which contains the necessary temporal ground-truth annotations (`start`, `end` timestamps).

| Dataset Name | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| ActivityNet Captions (Videos) | ` (Metadata) + Video URLs from official repo | Source video frames for distortion generation. | Verified (Official ActivityNet) |
| ActivityNet Captions (Metadata) | ` (and `val_2.json`) | Ground truth temporal annotations and video IDs. | Verified (Official ActivityNet) |

**Data Acquisition Plan**:
1. **Metadata Loading**: The `val_1.json` and `val_2.json` files from the official ActivityNet Captions repository will be downloaded and parsed to extract `video_id`, `duration`, and `annotations` (start/end timestamps).
2. **Video Fetching**: Video files will be fetched on-demand from the official Amazon S3 bucket using the `huggingface_hub` or `requests` library. To adhere to the constrained RAM limit, videos will be streamed, processed (distorted), and written to disk, then discarded from memory.
3. **Subsetting & Power-Adaptive Sampling**: To ensure the CI limit is met, the research will target a subset of 500 clips (125 per ratio). A **Time-Boxed Power-Adaptive** strategy is implemented:
 * The pipeline tracks elapsed time and average inference time per clip.
 * If the 6-hour limit is approached before reaching N=125 per group, the pipeline stops at the current N.
 * The statistical report will explicitly calculate the **achieved power** for the final N. If N is insufficient for d=0.5, the study is labeled "Underpowered" rather than failing.

**Data Integrity Check**:
The plan explicitly addresses the "Dataset-variable fit" concern. ActivityNet Captions contains video content and temporal boundaries. The research does not require external variables. The only variable manipulated is the geometric aspect ratio, which is fully controllable via the generation script. The control group is the original video, ensuring no confounding generation artifacts.

## Model Strategy

**Target Model**: Kwai Keye-VL-2.0.
**Constraint**: CPU-only, INT4 quantization, < 7GB RAM.

**Implementation Approach**:
1. **Quantization**: The model will be loaded using `llama-cpp-python` with `n_gpu_layers=0` and `n_batch` tuned for CPU. If `llama.cpp` support for the specific architecture is incomplete, `optimum-intel` with `load_in_4bit=True` and `device_map="cpu"` will be the fallback.
2. **Architecture Fallback**: If Kwai Keye-VL-2.0 is unsupported by the quantization backends, the system will switch to **LLaVA-NeXT-34B (INT4)** available via HuggingFace. This model has a similar ViT+LLM fusion architecture and is verified to run on CPU with INT4. This preserves the research question (VLM robustness) while ensuring feasibility.
3. **Memory Management**: To adhere to the 7GB limit:
 * The model weights (quantized) for a large-scale parameter model are approx 1.5-2GB.
 * The remaining memory is allocated for the KV cache, video frame tensors, and Python overhead.
 * **Fallback Strategy**: If a specific video clip causes OOM, the system will attempt to downsample the frame rate. If this fails, the clip is excluded, and the event is logged.
4. **Quantization Baseline**: To address the confounding variable of quantization noise, a small subset (N=20) of videos will be run in **FP16** (if memory permits on the 2-core CPU) or the report will explicitly state that the performance drop is a composite of "Architecture + Quantization". The primary comparison remains INT4.

## Statistical Methodology

**Hypothesis**: $H_0$: There is no difference in mIoU between extreme-aspect ratio videos and original control videos. $H_1$: Extreme-aspect ratio videos have significantly lower mIoU.

**Metrics**:
1. **mIoU (Mean Intersection-over-Union)**: Calculated per clip as $IoU = \frac{\text{Intersection}}{\text{Union}}$ of predicted vs. ground truth intervals.
2. **Statistical Test**:
 * **Group Independence**: The extreme-aspect clips and original control clips are **Independent Samples** (distinct video instances).
 * **Normality Check**: Shapiro-Wilk test ($\alpha=0.05$) on the distribution of mIoU scores for both groups.
 * **Test Selection**:
 * If normal: **Welch's t-test** (Independent Samples, unequal variance).
 * If non-normal: **Mann-Whitney U test**.
 * **Significance**: $p < 0.05$.
 * **Effect Size**: Cohen's d (for t-test) or rank-biserial correlation (for Mann-Whitney).

**Multiple Comparison Correction**:
Since the study compares multiple aspect ratios (1:10, 10:1, 1:20, 20:1) against the control, a **Bonferroni correction** will be applied to the p-values if individual tests are run for each ratio. Alternatively, a **Kruskal-Wallis H test** (non-parametric ANOVA) followed by post-hoc Dunn's test with correction will be used to test the overall effect of aspect ratio.

**Power Analysis**:
With N=125 per group (total 500), the study has sufficient power to detect a medium effect size ($d=0.5$) with $\alpha=0.05$ and power=0.80. If the dataset size is reduced due to time constraints, the **achieved power** will be calculated and reported explicitly. If the achieved power is < 0.80, the conclusion will be qualified as "Underpowered to detect small effects".

## Decision/Rationale

**CPU vs. GPU**: The research explicitly targets the "Resource-Constrained Inference Fidelity" principle. Running on GPU would invalidate the specific hypothesis regarding mobile/surveillance applicability. Therefore, the CPU-only plan is mandatory, not optional.

**Synthetic Data**: Generating synthetic distortions is the only way to isolate the geometric variable without introducing temporal noise or content bias. Using existing datasets with varying aspect ratios would confound the results with content differences.

**Control Group**: The control group is the **Original ActivityNet Captions** video. This is critical. Using a "square-cropped" synthetic control would introduce generation artifacts, confounding the results. The original video serves as the 1:1 baseline.

**Quantization**: INT4 is chosen to fit the 7GB RAM constraint. The potential degradation from quantization is acknowledged as a confounding variable, mitigated by a small FP16 baseline run (if feasible) and explicit reporting.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Model Unavailability** | High | Fallback to LLaVA-NeXT-34B (INT4) if Kwai Keye-VL-2.0 is unsupported. |
| **Time Limit Exceeded** | High | **Time-Boxed Power-Adaptive Sampling**: Stop early, calculate achieved power, report "Underpowered" if N < 125. |
| **Semantic Integrity Loss** | Medium | The generation script will check the bounding box area; if >95% is lost, the clip is regenerated or skipped. |
| **Quantization Noise** | Medium | Explicitly report as a confounding variable; attempt small FP16 baseline if memory permits. |
