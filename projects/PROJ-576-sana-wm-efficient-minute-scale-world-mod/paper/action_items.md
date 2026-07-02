# Automated-review action items — SANA-WM: Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: minor_revision

- **[writing]** Clarify the derivation and intuition behind the 1/sqrt(D*S) key scaling factor in the GDN section to improve reproducibility.
- **[writing]** Expand the description of the two-stage refiner's training procedure, specifically the loss function formulation and reference conditioning mechanism.
- **[writing]** Elaborate on the limitations section to explicitly discuss failure modes in highly dynamic scenes or rare viewpoints as mentioned in the conclusion.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The review focuses on the factual accuracy of claims and their supporting evidence within the provided manuscript. Hardware and Performance Claims The most critical factual issue lies in the Abstract and Introduction, where the authors claim: "its distilled variant can be deployed on a single RTX 5090 with NVFP4 quantization to denoise a 60s 720p clip in 34s." As of the current date, the NVIDIA RTX 5090 is not a released product, nor are its specifications or performance benchmarks publicly avai

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[writing]** The manuscript references external LaTeX files (e.g., `tables/train-data.tex`, `tables/main_table.tex`) that are not included in the provided source. This breaks reproducibility from scratch. Ensure all `.tex` fragments are either embedded or explicitly listed as required build artifacts.
- **[writing]** The `figures_tex/` directory contains standalone LaTeX snippets (e.g., `bench_trajectory.tex`) that are not standard figure environments. These should be consolidated into the main document or clearly documented as required build inputs to ensure the PDF compiles without missing file errors.
- **[science]** The paper claims custom Triton kernels for GDN (Sec 5.1) but provides no code repository link or appendix detailing the kernel implementation. Without the kernel source, the efficiency claims (36x throughput) are not reproducible.

## paper_reviewer_data_quality_paper — verdict: minor_revision

- **[writing]** The paper claims to use 'public video sources' but Tab. 1 (train-data.tex) and App. B (asset_terms.tex) list several datasets (SpatialVID-HQ, DL3DV, OmniWorld) with non-commercial (CC-BY-NC-SA) or custom 'Project Terms' licenses. The manuscript must explicitly state if the training corpus is restricted to non-commercial research use and clarify the license status of the final model weights to avoid legal ambiguity for downstream users.
- **[writing]** The benchmark construction relies on 'Nano Banana Pro' (Google/Gemini) for initial frames. The license/terms for these generated images are not standard open licenses. The paper must clarify if the benchmark dataset (80 scenes + trajectories) is released under a specific license or if it is restricted by Google's product terms, as this affects reproducibility and the ability of others to use the benchmark.
- **[writing]** The data pipeline uses 'Pi3X' and 'MoGe-2' for pose annotation. While code licenses are mentioned, the specific terms for the *model weights* used in the pipeline (e.g., Pi3X weights are CC BY-NC 4.0) must be explicitly confirmed as compatible with the intended release of the SANA-WM model. If the training data was processed using non-commercial weights, the resulting model's commercial viability is legally compromised.
- **[writing]** The paper mentions '213K public video clips' but the breakdown in Tab. 1 shows a mix of real and synthetic (3DGS) data. The provenance of the 'Sekai Walking-HQ' dataset is listed as 'Real' but the source project page lacks a clear standard license. A specific citation to the exact license version or a statement of 'unknown license, used under fair use/research exemption' is required for this specific subset.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Fig. 1 (teaser) and Fig. 2 (pipeline) lack explicit axis labels or scale bars where spatial dimensions are implied. The '64-GPU training' and 'single-GPU inference' claims in captions are text-heavy; consider moving these to the main text and using a small inset icon or schematic for hardware scale to improve visual clarity at print resolution.
- **[writing]** Fig. 4 (efficiency-analysis) sub-figure (b) shows 'OOM' for all-softmax but lacks a clear y-axis label for memory (GB) and x-axis for sequence length (frames/seconds). The 'scaled for readability' note in the caption for sub-figure (a) is insufficient; the bars must have explicit numerical tick marks or a secondary axis to allow quantitative comparison of latency.
- **[writing]** Fig. 5 (train-stability) combines a table and a line plot. The line plot (loss-vs-scale) has no visible axis labels or units in the provided source context. Ensure the y-axis clearly indicates 'Loss' or 'Gradient Norm' and the x-axis indicates 'Training Steps' with appropriate scaling to verify the 'NaN events' claim visually.
- **[writing]** Qualitative figures (Fig. 6, Fig. 7, Fig. 12) rely on 'Green borders' and 'transparent overlays' for comparison. At standard print resolution (300 DPI), these overlays may be illegible. Verify that the 'Zoom in for details' instruction is supported by sufficient resolution in the PDF and that the green border contrast is high enough for grayscale printing.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Acronyms without definition: Terms like "DiT" (Section 3), "AR" (Section 5), "SFT" (Appendix), and "LoRA" (Appendix) are used without being spelled out first. "6-DoF" appears in the Abstract and Introduction but is never expanded to "six degrees of freedom."
- **[writing]** Hardware/Toolchain Specifics: "NVFP4" (Abstract) and "OOM" (Figure 2 caption) are specific to NVIDIA's ecosystem and developer slang, respectively. These should be replaced with "4-bit floating point quantization" and "runs out of memory" to maintain formal tone and accessibility.
- **[writing]** Unexplained Geometric/Math Terms: "UCPE" and "Pl\"ucker" (Section 3) are introduced as if they are common knowledge. A brief parenthetical explanation (e.g., "Plücker coordinates, a method for representing 3D lines...") is necessary for clarity.
- **[writing]** Metric Acronyms: "FVD" and "VBench" (Section 5) are standard in the niche but obscure to the general scientific audience. They should be defined upon first mention. The paper would benefit from a "glossary-style" approach in the introduction or a strict rule of "define at first use" throughout the text. Currently, the density of undefined acronyms forces the reader to constantly pause and infer meaning or look up external references, disrupting the flow of the argument.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent architecture for minute-scale world modeling, but several causal claims and comparative metrics lack precise grounding in the provided evidence. First, the efficiency claim in the Abstract ("36x higher throughput") is not fully supported by the comparative data in Section 5.3. The text compares SANA-WM against Infinite-World (480p) and notes that LingBot-World's 720p inference is "unaffordable" under the evaluation budget. The 36x figure likely relies on an external

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'comparable visual quality' to industrial baselines (LingBot-World, HY-WorldPlay) is over-claimed. Table 1 shows SANA-WM+Refiner achieves 80.62 VBench Overall vs. LingBot's 81.82. While close, the baselines are 480p while SANA-WM is 720p; the paper conflates resolution differences with quality parity without normalizing for resolution or providing perceptual user studies to justify 'comparable' status.
- **[writing]** The '36x higher throughput' claim (Abstract) lacks a clear, fair baseline definition. The paper compares SANA-WM (single GPU, 720p) against baselines running on 8 GPUs at 480p. The throughput difference is driven by both resolution and hardware count. The claim implies architectural superiority alone drives this, but the comparison is confounded by the 8x GPU difference and resolution gap.
- **[writing]** The claim that the model 'natively trained for one-minute generation' (Abstract) is slightly misleading. Section 3.1 describes a progressive training strategy starting from 5s clips (Stage 1-2) before extending to minute-scale (Stage 3). While the final model is trained on minute data, the 'native' implication of skipping short-horizon pre-training is not fully accurate.
- **[writing]** The 'single RTX 5090' deployment claim (Abstract) is speculative. The RTX 5090 is not a released product at the time of writing (implied by the paper's context). Claiming specific performance (34s) on unreleased hardware without a clear extrapolation methodology or disclaimer is an overreach.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper claims deployment on an 'RTX 5090' (Abstract, Sec 1). As this hardware does not currently exist, this claim is factually incorrect and potentially misleading regarding the model's actual accessibility and hardware requirements. This must be corrected to reflect available hardware (e.g., RTX 4090) or clarified as a hypothetical projection.
- **[science]** The 'Broader Impact' section (Sec 7) acknowledges risks of deepfakes and safety-critical misuse but lacks a concrete mitigation strategy for the 'Robust Annotation Pipeline' (Sec 4). The pipeline uses VLMs (Qwen3.5) to filter data and generate captions. There is no discussion of how the pipeline handles or filters out sensitive content (e.g., faces, private locations, hate speech) from the 213K public video clips, creating a risk of training on or generating harmful content.
- **[writing]** The benchmark construction (Sec 5, App B) uses 'Nano Banana Pro' (a Google product) to generate initial frames. The paper states these are marked with SynthID, but does not explicitly confirm that the *training* data pipeline includes a mechanism to detect and exclude SynthID-marked or other watermarked content to prevent model collapse or copyright leakage.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of '36x higher throughput' (Abstract) lacks a defined baseline. The main table (Tab. 1) shows SANA-WM (24.1 v/h) vs LingBot-World (0.6 v/h), which is ~40x, but LingBot uses 8 GPUs while SANA-WM uses 1. The comparison must normalize for GPU count or explicitly state the baseline is 'per-GPU throughput' to avoid misleading efficiency claims.
- **[science]** The 'Robust Annotation Pipeline' relies on Pi3X and MoGe-2 for metric-scale poses on public videos. The paper provides no quantitative validation of these estimated poses against ground truth (e.g., on OmniWorld or DL3DV subsets where GT exists). Without error bars or correlation metrics for the pose estimation pipeline, the 'precise 6-DoF trajectory adherence' claim is unsupported by direct evidence.
- **[science]** The ablation study for GDN key scaling (Fig. 5) demonstrates stability (avoiding NaNs) but does not report the final generation quality (e.g., FVD or VBench) of the stable model compared to the unstable baselines. Stability is necessary but not sufficient; evidence that the scaling improves final video quality is missing.
- **[science]** The benchmark uses 80 initial images generated by 'Nano Banana Pro'. The paper does not report the variance of results across different seeds for the initial image generation or the trajectory sampling. With only 80 scenes, the statistical power to claim 'stronger action-following accuracy' (Abstract) is low; confidence intervals or significance tests (e.g., t-test p-values) are required.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The evaluation protocol relies on a single generated video per scene (80 total) without reporting confidence intervals, standard errors, or statistical significance tests for the reported metrics (RotErr, VBench). Given the high variance in generative models, point estimates are insufficient to claim 'stronger action-following accuracy' over baselines. Please report 95% confidence intervals or perform paired statistical tests (e.g., Wilcoxon signed-rank) across the 80 scenes.
- **[science]** The ablation study on GDN key scaling (Fig. 5) reports binary outcomes (NaN vs. stable) but lacks quantitative stability metrics (e.g., gradient norm variance, loss curve smoothness) or multiple random seeds. To support the claim that the proposed scaling is 'the only variant' ensuring stability, please include error bars or results from at least 3 independent runs to rule out seed-dependent luck.
- **[science]** The benchmark construction uses 80 scenes generated by a single model (Nano Banana Pro). The statistical power of the evaluation is limited by this small sample size and potential bias from the generator's specific distribution. Please clarify if the 80 scenes are a random sample or a curated subset, and discuss the implications for generalizability. Additionally, report the standard deviation of metrics across the 80 scenes, not just the mean.

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** In `sections/5_experiments.tex`, the command `\input{}` is present without a filename argument, which will cause a LaTeX compilation error. The intended file (likely `tables/ablation_vbench.tex` or similar) must be specified.
- **[writing]** In `figures_tex/train-stability-camera-condition.tex`, the `\captionof{table}` and `\captionof{figure}` commands are used inside a `figure` environment. This creates a nested caption structure that may result in duplicate numbering or formatting conflicts. The outer `figure` environment should be removed, or the `captionof` commands should be replaced with standard `\caption` if the environment is kept.
- **[writing]** In `sections/7_appendix.tex`, the `\appendix` command is called, but the subsequent sections use `\section` instead of `\subsection` or `\subsubsection` for the appendix structure. While valid, this often leads to inconsistent numbering (e.g., 'Section A' vs 'Section 7') depending on the class file. Verify if the `nv` class expects `\section` to automatically switch to appendix numbering or if manual adjustment is needed for consistency with the main text.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Remove all author-specific debug macros (e.g., \cjs, \enze, \yy, \jc, \jy, \cai, \crh, \muyang, \haozhe, \haoyi) from preamble.tex. These are visible in the source and indicate an incomplete pre-submission cleanup.
- **[writing]** In sections/3_method.tex, the phrase 'From Token-wise GDN to Frame-wise GDN' is a section header but lacks the standard LaTeX \subsection or \paragraph command, breaking the document structure and TOC generation.
- **[writing]** In sections/5_experiments.tex, the line '\input{}' is empty and should be removed. It likely indicates a missing table file or a copy-paste error.
- **[writing]** In preamble.tex, the command '\def\vs{\emph{vs}\onedot}' is defined but 'vs' is typically not italicized in standard academic writing (unlike 'e.g.' or 'i.e.'). Consider removing the \emph wrapper for consistency with standard style guides.
