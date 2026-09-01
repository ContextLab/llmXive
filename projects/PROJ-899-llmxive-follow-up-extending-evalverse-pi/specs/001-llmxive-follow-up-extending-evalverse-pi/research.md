# Research: VLM Proxy Dimension Mimicry & Bias Characterization

## 1. Research Question
Which **VLM-generated scores** in the **verified VLM proxy datasets** (VLM_SingleAction2, vlm_split, vlmsareblind) exhibit a correlation (r) with low-level features (optical flow, audio spectral centroids) such that they are predictable by these features? The study explicitly reframes the goal as measuring **"VLM Bias Characterization"** (how much the VLM relies on low-level cues) rather than "Human Viability," acknowledging that the ground truth is VLM output and that the datasets contain **action-based** scores, not "cinematic dimensions."

## 2. Dataset Strategy

### Verified Datasets
The following datasets are verified and available for programmatic access. **No other URLs are used.**

| Dataset Name | Verified Source (URL) | Usage in Plan |
| :--- | :--- | :--- |
| **VLM_SingleAction2** | `https://huggingface.co/datasets/zesquirrelnator/VLM_SingleAction2/resolve/main/data/train-00000-of-00001.parquet` | Source of **Ground Truth** scores (VLM-generated ratings) for specific **actions** (e.g., "jump", "run"). Dimensions are discovered dynamically. |
| **vlm_split** | `https://huggingface.co/datasets/flipwooyoung/vlm_split/resolve/main/data/train-00000-of-00003.parquet` | Supplemental **Ground Truth** scores for cross-validation of **action** dimensions. |
| **vlmsareblind** | `https://huggingface.co/datasets/XAI/vlmsareblind/resolve/main/data/valid-00000-of-00001.parquet` | Validation set for **Ground Truth** scores to ensure no data leakage. |
| **EvalVerse** | *NO verified source found* | **Constraint**: The plan does NOT attempt to download a non-existent EvalVerse URL. The "EvalVerse" analysis is reframed to use the structure of the VLM proxy datasets as the target. The research question is updated to reflect this. If the proxy datasets do not contain the specific "cinematic" dimensions of interest, the plan will explicitly report that the question cannot be answered for those dimensions using the available open data. |

### Data Access Strategy
- **Streaming**: All datasets are loaded using `datasets.load_dataset(..., streaming=True)`. This prevents loading the full dataset into RAM.
- **Dynamic Dimension Discovery**: The pipeline will scan the first 100 clips to identify unique dimension labels (e.g., "action_type", "score_type"). It will not abort if "EvalVerse" dimensions are missing; it will analyze the **action-based** dimensions that *are* present.
- **Missing Data**: If a clip in the VLM proxy dataset lacks a video file URL or the video is broken, that clip is skipped (logged in `data/processed/skipped_clips.log`).
- **Proxy Validation**: A strict gate (Phase 0.5) ensures that the dimensions found in the proxy data match the expected "Action" or "Score" types. If the data contains dimensions that do not match the expected rubric, the pipeline aborts to prevent inappropriate analysis.

## 3. Methodology

### 3.1 Feature Extraction (CPU-First)
For each video clip in the stream:
1.  **Optical Flow**: Calculate magnitude and direction histograms using `opencv` (Farneback method, downsampled to 1/4 resolution for speed).
2.  **Audio**: Extract spectral centroid, zero-crossing rate, and MFCCs using `librosa` (downsampled audio).
3.  **Aggregation**: Compute mean and std dev of these features over the clip duration.

### 3.2 Correlation Analysis (FR-004, FR-007)
- **Metric**: Pearson (linear) and Spearman (monotonic) correlation coefficients between the aggregated low-level features and the VLM ground truth scores.
- **Confidence Intervals**: Calculated using `scipy.stats.bootstrap` with `method="basic"` and `n_resamples=1000`.
- **Threshold**: A dimension is flagged as "VLM-Reliance-High" if the lower bound of the 95% CI for Pearson r ≥ 0.85. However, a full sensitivity sweep is performed. **Note**: This does not imply "Human Sufficiency" due to the lack of human ground truth.

### 3.3 Baseline Validation (FR-008)
- **Mean Baseline**: Predict the mean score for all clips. Calculate R² and RMSE.
- **Shuffled Baseline**: Shuffle the ground truth labels 100 times, calculate correlation distribution.
- **Comparison**: The "VLM-Reliance-High" claim is only valid if the low-level feature correlation significantly exceeds the shuffled baseline. **Explicit Note**: Exceeding the baseline proves predictive power for the VLM, not sufficiency for human judgment.

### 3.4 Sensitivity Analysis (FR-005, SC-004)
- **Threshold Sweep**: Sweep the correlation threshold from 0.0 to 0.95 in steps of 0.05.
- **Flip Rate**: Calculate the percentage of dimensions that change classification (High vs Low) at each step.
- **Multiple Comparison Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values derived from permutation tests to control family-wise error rate.
- **Max-T Aggregation**: Aggregate permutation test statistics using the Max-T method to control for multiple comparisons.
- **Winner's Curse Mitigation**: Classification requires the **lower bound** of the 95% CI to exceed the threshold. Point estimates alone are insufficient.

### 3.5 Compute Feasibility Profiling (US2)
- **Memory Tracking**: Use `tracemalloc` to measure peak memory per clip.
- **Scaling**: Project total runtime based on the average time per clip observed in the first 100 clips and the total N found in the dataset.
- **Gate**: If `peak_memory > 6.5GB` or `projected_time > 5.5h`, the pipeline halts and reports a constraint violation.

### 3.6 Power Analysis (Methodology Concern)
- **Method**: Calculate the minimum sample size (N) required to detect a correlation of r=0.85 with 95% power (1-beta=0.95) and alpha=0.05.
- **Gate**: If the actual N in the dataset is less than the required N, the result is flagged as "Underpowered". No definitive classification is made for "Underpowered" dimensions.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: With ~15+ dimensions (dynamic), the probability of false positives is high. The plan uses Benjamini-Hochberg correction on all p-values and Max-T aggregation for permutation tests.
- **Power Analysis**: The sample size is determined by the available clips in the verified VLM proxy datasets. If N < 30 for a dimension, the CI will be wide, and the "VLM-Reliance-High" claim will be flagged as "low power".
- **Causal Claims**: No causal claims are made. The analysis is strictly associational (VLM Mimicry).
- **Collinearity**: Optical flow and motion magnitude are definitionally related. The plan will report the correlation of each *individually* but will note the collinearity in the `data-model.md` and avoid claiming "independent effects" for both.
- **Threshold Justification**: The 0.85 threshold is treated as a "High-Reliance" marker, not a "Human Sufficiency" cutoff. The report will show the threshold at which classification changes, acknowledging that 0.85 may be empirically impossible for high-level semantic dimensions using low-level features.
- **Data Reality**: The sample size N is determined by the verified datasets. The "10k clips" goal is replaced by "all available clips (N = dynamic, expected ~50-500)".

## 5. Decision Rationale (Compute Feasibility)
- **CPU-Only**: The method relies on statistical correlation and simple feature extraction (OpenCV/Librosa), which are highly optimized for CPU. No GPU is required.
- **Streaming**: The use of `datasets` streaming ensures that even if the underlying dataset is 50GB, the RAM usage remains constant (~2-3GB) as only one clip is processed at a time.
- **No Fabrication**: All results are derived from the real data in the verified HuggingFace URLs. No synthetic data or "toy" datasets are used.