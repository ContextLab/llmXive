---
action_items:
- id: 96a9acee1d4a
  severity: science
  text: "The ablation studies in Appendix~\ref{sec:app_ablation} (Tables~\ref{tab:ablation_scale},\
    \ \ref{tab:ablation_blur}, \ref{tab:ablation_temperature}) report single-point\
    \ performance metrics without any measure of variance (e.g., standard deviation)\
    \ or statistical significance testing. Given the stochastic nature of deep learning\
    \ training, claims of superiority based on small metric differences (e.g., CD\
    \ 0.190 vs 0.189) are statistically unsupported without reporting results over\
    \ multiple random seeds."
- id: 0d26a4ce18a2
  severity: science
  text: "In Section~\ref{sec:setup} and Table~\ref{tab:main_re10k}, the evaluation\
    \ protocol does not specify the number of random seeds used for training or the\
    \ variance across runs. To ensure the reported improvements (e.g., +2.75 dB PSNR)\
    \ are robust and not artifacts of specific initialization, the authors must report\
    \ mean and standard deviation over at least 3 independent training runs for the\
    \ main baselines and their method."
- id: b14f2faee314
  severity: science
  text: "The large-loss filter mentioned in Section~\ref{sec:supervision} ('suppress\
    \ outlier samples after warm-up') lacks a statistical definition. The threshold\
    \ for 'large loss' should be explicitly defined (e.g., based on a specific percentile\
    \ of the loss distribution or a multiple of the standard deviation) to ensure\
    \ reproducibility and prevent arbitrary data curation that could bias the results."
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:55:36.456798Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the experimental evaluation requires strengthening to support the strong claims of performance superiority. While the paper presents extensive quantitative results in Tables~\ref{tab:main_dl3dv_surface}, \ref{tab:main_dl3dv_nvs}, and \ref{tab:main_re10k}, these tables report only point estimates (means) without any indication of variance or statistical significance.

Specifically, the ablation studies in Appendix~\ref{sec:app_ablation} (Sections~\ref{sec:app_ablation_scale}, \ref{sec:app_ablation_blur}, \ref{sec:app_ablation_temperature}) compare hyperparameter settings based on single-run metrics. For instance, Table~\ref{tab:ablation_scale} shows a Chamfer Distance of 0.189 for the $[0.5, 10.0]$ range versus 0.190 for the $[0.5, 18.0]$ range. Without reporting standard deviations from multiple random seeds, it is impossible to determine if these differences are statistically significant or merely noise inherent to the training process. The same issue applies to the main comparisons against baselines; a 2.75 dB PSNR gain is substantial, but the absence of variance metrics makes it difficult to assess the reliability of this improvement across different data splits or initialization seeds.

Furthermore, the "large-loss filter" described in Section~\ref{sec:supervision} is a critical component of the training stability but is defined vaguely. The text states that samples with loss $> 0.06$ (or pose loss $> 1.0$) are scaled down, but it does not clarify if these thresholds are fixed constants or derived dynamically from the loss distribution (e.g., $3\sigma$ clipping). If fixed, the justification for these specific values is missing. If dynamic, the statistical method for calculating the threshold must be detailed to ensure reproducibility.

To address these concerns, the authors should re-run the main experiments and key ablations with at least three different random seeds, reporting the mean and standard deviation for all metrics. Additionally, the statistical definition of the loss filtering mechanism must be explicitly stated.
