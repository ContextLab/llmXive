---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/300
paper_authors:
  - Weijie Wang
  - Haoyu Zhao
  - Yifan Yang
  - Feng Chen
  - Zeyu Zhang
  - Yefei He
  - Zicheng Duan
  - Donny Y. Chen
  - Yuqing Yang
  - Bohan Zhuang
---

# Latent Spatial Memory for Video World Models

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.09828
Paper authors (from arXiv): Weijie Wang, Haoyu Zhao, Yifan Yang, Feng Chen, Zeyu Zhang, Yefei He, Zicheng Duan, Donny Y. Chen, Yuqing Yang, Bohan Zhuang

Submitted by: github-actions[bot]

(Intake from human-submission issue #300.)

## Rejection rationale (2026-06-10)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[658ec39de72f]** Restore the truncated reference.bib file to ensure all citations are defined and LaTeX compiles without errors.
- **[9a3dfd97ed94]** Populate verification_status for all citations in state/citations/ to satisfy acceptance criteria for reference validation.
- **[0f024dac9585]** Several in‑text citations have no corresponding entry in the bibliography (e.g., \cite{wan2025wan}, \cite{zhang2023adding}, \cite{carion2025sam3segmentconcepts}, \cite{yang2025qwen3}). Add complete bibliographic records for all cited works so that each claim can be verified against the source.
- **[d4d0de9c07ec]** The paper reports a "10.57× faster" end‑to‑end generation speed and "55× lower GPU memory" usage (Fig. 5). However, the experimental details (hardware configuration, batch size, exact settings for both methods) are not fully disclosed, and no variance or statistical analysis is presented. Provide a detailed description of the measurement protocol and include confidence intervals or repeated‑run statistics.
- **[5347be52c962]** The claim of achieving state‑of‑the‑art performance on WorldScore is based on a single average score table. Include statistical significance testing (e.g., paired bootstrap) to demonstrate that the improvement over the previous best (Spatia) is not due to random variation.
- **[0afafdd69f03]** The abstract and introduction state that the latent‑space cache “eliminates both the information loss of pixel‑space reconstruction and the computational burden of repeated encoding and rendering.” While the methodology description supports this, no quantitative ablation directly isolates the impact of each of these two factors. Add an ablation that measures quality and speed when only one of the two bottlenecks is removed.
- **[9c439d5187f2]** The paper frequently attributes performance gains to the “dynamic object filter” (Sec. 3.4) but provides no quantitative breakdown of its contribution beyond the ablation table. Include a dedicated experiment that reports metrics with and without the filter on the same dataset.
- **[508e55c529b6]** Code repository and implementation scripts are missing from the submission package, preventing reproducibility and code quality assessment.
- **[caa3598ef1fc]** Dataset license for RealEstate10K and WorldScore benchmark is not specified. Add explicit license terms for all training/evaluation data to ensure legal compliance and reproducibility (Section 4.1, lines 1-30).
- **[51b3dc34a51d]** No code repository URL or version control information (Git tags, commit hashes) is provided. Add a stable code release link with versioning to support reproducibility (Section 4.1 or Appendix).
- **[f2221eb35f83]** The aka.ms project page link is a short URL that may suffer from link rot. Provide a permanent archive link (e.g., Zenodo DOI, GitHub) for project resources.
- **[24434bc8e5a2]** Data schema for the latent spatial memory cache (Eq. 2-4) lacks formal documentation. Specify file formats, coordinate conventions, and data types for any released cache artifacts.
- **[ab4d4e63f46d]** Missing data handling policies (dynamic object filtering, sky exclusion) are described but lack quantitative thresholds. Document data quality criteria and filtering thresholds used in cache construction.
- **[6638e776f15a]** Ensure axis labels in figures/efficiency.pdf explicitly include units (e.g., 's/frame', 'MiB') and are legible at print scale; captions describe them but the figure itself must carry them.
- **[5f79a81a47c1]** Embed method names directly on qualitative comparison figures (re10k_video.pdf, open.pdf) as row/column labels to reduce reliance on caption for identification.
- **[aeee77c4f337]** Add accessibility alt-text descriptions for all figures to comply with arXiv/venue accessibility standards; current LaTeX source lacks figure descriptions.
- **[0ca6f8599dd1]** Remove the Chinese comment block found in sections/04_experiments.tex prior to fig:re10k_revisit to ensure source cleanliness.
- **[ce069c7fd857]** Shorten the teaser.pdf caption; quantitative claims (10.57x, 55x) should reside in the abstract/main text to improve visual balance on the title page.
- **[cf2e35e150c7]** Define the acronym VAE (Variational Autoencoder) at first use in the Abstract and Section 3 to aid non-specialist readers.
- **[bd5bd92643fd]** Expand LoRA (Low-Rank Adaptation) upon first mention in Section 3.4 (Efficient Adaptation) to clarify the technique.
- **[64090cf985bc]** Define FSDP (Fully Sharded Data Parallel) in Appendix Implementation Details where it appears without context.
- **[6ed2ed645d15]** Clarify SE(3) as Special Euclidean Group in Appendix Geometry to prevent confusion for readers from non-robotics backgrounds.
- **[b90a5fd56015]** Replace 'z-buffered' with 'depth-buffered' or add a parenthetical explanation in Section 3 Preliminaries for broader accessibility.
- **[8b422b2cdbf8]** Clarify the quantitative basis for the '55x' GPU memory reduction claim. Stated VAE parameters (s=16, C=48 vs RGB 3) imply a theoretical storage limit of ~16x. The text attributes this to 'squared VAE compression factor' (Fig 1), which implies 256x. The discrepancy requires explanation of whether the metric includes rendering buffers or baseline implementation details.
- **[d5d46f655c82]** Efficiency claim (10.57x) conflates cache-read speed with end-to-end generation. Section 4.1 measures cache-read, but Abstract/Intro claim end-to-end. Re-measure or clarify.
- **[3bde8e9332cb]** Memory claim (55x) refers to cache footprint, not total GPU memory. Clarify scope to avoid misleading deployment implications.
- **[26d557022c50]** WorldScore SOTA margin (0.63 pts) lacks statistical significance testing. Training on RE10K while claiming general SOTA on WorldScore requires stronger evidence.
- **[72210ecca21a]** Precision of efficiency metrics (10.57x, 55x) is unjustified without error bars. Round to appropriate significant figures.
- **[68637befbd73]** Add a 'Societal Impact' or 'Safety' section discussing dual-use risks (e.g., deepfakes) and mitigation strategies given the efficiency gains.
- **[e97e63a5c4f8]** Explicitly declare Conflict of Interest regarding Microsoft Research affiliations and funding support in a dedicated statement.
- **[2e088a86f4de]** Report standard deviations for all benchmark metrics (Tables 1-2) across multiple seeds to establish statistical significance of the performance gains.
- **[826fadc56cb2]** Clarify the training status of baseline models (zero-shot vs. fine-tuned) in Section 4.1 to ensure fair comparison of data efficiency.
- **[0f8cb2f0db25]** Specify the exact rollout configuration (total frames, chunks) for the efficiency measurements in Figure 5 to enable reproducibility of memory footprint claims.
- **[b6dd7997c397]** Report mean ± standard deviation for all quantitative metrics (WorldScore, PSNR, SSIM, efficiency) across multiple random seeds to establish statistical significance.
- **[c00c9fd2253a]** Clarify sample size (number of prompts/videos) for evaluation and specify random seed values for reproducibility in Section 4.1.
- **[897c1f7fb52c]** Replace "up to" efficiency claims (e.g., 10.57x) with mean performance and variance to avoid cherry-picking best-case scenarios.
- **[ceee02faaa63]** Standardize figure references to use 'Figure' or 'Fig.' consistently across all sections (e.g., 'Fig~' in Introduction vs 'Figure' in Experiments).
- **[ba6d5c002251]** Unify table formatting by either applying \resizebox to all wide tables or ensuring consistent manual width adjustments to avoid font size disparities.
- **[957d07e004b4]** Verify the \captionof usage in the teaser figure (main.tex) to ensure correct numbering relative to standard figure environments.
- **[b0b4a5480e32]** In sections/04_experiments.tex, correct 'Figure... provides' to 'provide' for subject-verb agreement. Ensure all plural subjects have plural verbs.
- **[961061a76152]** Standardize hyphenation in sections/04_experiments.tex. Convert 'state of the art', '3D aware', 'per step', 'long horizon', 'component level', and 'Two stage' to hyphenated forms (e.g., 'state-of-the-art').
- **[d39e497c5c6f]** Unify spelling conventions across the document. Choose either American (e.g., 'color', 'summarize') or British (e.g., 'colour', 'summarise') English and apply consistently.
- **[f3b519b69ec0]** In sections/03_method.tex, change 'over the overlapping chunk' to 'chunks' for plural consistency. In sections/04_experiments.tex, fix 'baselines that rasterises' to 'rasterize'.
