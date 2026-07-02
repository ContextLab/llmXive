# Automated-review action items — Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer — verdict: major_revision_writing

- **[writing]** Resolve LaTeX compilation failure: The document relies on a custom class file 'shengshu.cls' and local preamble files not provided in the source. Re-run the build with a standard conference template (e.g., CVPR, NeurIPS) or provide the missing class files to verify the paper structure.
- **[writing]** Fix bibliography verification: The citation list contains a GitHub Actions URL and a PyTorch CPU wheel URL marked as 'mismatch' or 'verified' but irrelevant to the scientific claims. Replace these with proper citations for the referenced methods (e.g., Wan2.1, CausVid, Self Forcing) and ensure all URLs point to valid arXiv or conference pages.
- **[writing]** Clarify latency measurement: The paper claims 50% latency reduction but notes measurements are on A800 without VAE costs, while baselines (Self Forcing, Causal Forcing) used H100. Re-run baselines on A800 or explicitly state the hardware discrepancy to ensure a fair comparison.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 'surpasses... by 0.1 in VBench Total' for the 2-step setting. Table 1 confirms 84.14 vs 84.04 (diff 0.10). However, the 4-step CF++ (84.10) only improves by 0.06. Clarify that the specific 0.1/0.3 gains apply strictly to the 2-step row to avoid confusion with the 4-step results.
- **[writing]** Abstract claims 'reducing... Stage 2 training cost by ~4x'. Table 2 shows Causal ODE (11600) vs Causal CD (2900). 11600/2900 = 4.0. This is accurate. Ensure the text explicitly links the '4x' claim to the Stage 2 data in Table 2 to prevent ambiguity with total pipeline costs.
- **[writing]** Section 3.2 claims Causal CD uses 'a single online teacher ODE step between adjacent timesteps'. While accurate, the description of the step direction (denoising vs forward) could be slightly clearer to ensure readers understand the 'online' nature avoids pre-computed trajectories. Clarify the ODE solver direction in the text.

## paper_reviewer_code_quality_paper — verdict: minor_revision

- **[science]** The LaTeX source lacks a `requirements.txt`, `pyproject.toml`, or `Dockerfile`. Without these, the reproducibility of the 3-stage pipeline (AR training, Causal CD, Asymmetric DMD) is impossible to verify from scratch. Add a dependency manifest and a build script.
- **[science]** The paper claims a 4x reduction in training cost (11,600 vs 2,900 GPU hours) and zero storage overhead. However, the code artifacts required to reproduce the 'Causal CD' online step (specifically the single-step ODE solver integration and EMA update logic) are not provided. Include the core training loop implementation to validate these efficiency claims.
- **[writing]** The `src/3-Method.tex` file contains complex mathematical derivations (Eq. 1-5) but no corresponding pseudocode or algorithm block. For code quality and reproducibility, an `algorithm` environment detailing the Causal CD update rule and the asymmetric DMD self-rollout loop is required.

## paper_reviewer_data_quality_paper — verdict: full_revision

- **[science]** The paper claims to use an 80K-video dataset sampled from OpenVid (src/4-Experiment.tex, Setup) but provides no license information, specific subset identifiers, or download scripts. Without a verifiable data manifest or license declaration, the provenance and legal usability of the training data cannot be confirmed.
- **[science]** The evaluation relies on VBench and VisionReward (src/4-Experiment.tex), but the paper does not specify the exact version of these benchmarks, the prompt lists used (beyond "100 prompts from Causal Forcing"), or the random seeds for evaluation. This lack of reproducibility metadata prevents independent verification of the reported scores.
- **[science]** The latency and throughput metrics are measured on an A800 GPU (src/4-Experiment.tex), yet the paper does not disclose the specific hardware configuration (e.g., memory size, driver version, CUDA version) or whether the "ASD trick" (keeping first frame at 4 steps) was applied consistently across all compared baselines in the same environment. This makes the efficiency claims non-reproducible.
- **[writing]** The paper references external GitHub repositories (thu-ml/Causal-Forcing, shengshu-ai/minWM) for code and data but does not include a data availability statement with specific commit hashes or version tags. If these links rot or the repositories are updated, the exact experimental setup described in the paper will become irreproducible.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figures in `Figures_tex/ablation.tex` lack visible axis labels or scale bars. Ensure source PDFs are high-resolution enough to resolve fine artifacts like 'antler separation' at print scale.
- **[writing]** Figure 3 (`Figures_tex/causal-cd.tex`) subfigure (b) claims efficiency gains but lacks y-axis units (e.g., GPU Hours). Explicitly label axes to validate the 4x speedup claim visually.
- **[writing]** Figure 5 (`Figures_tex/performance_comparison.tex`) claims superiority over baselines but lacks quantitative overlays or clear axis labels if it is a chart. Add metrics or labels to substantiate the 'surpassing' claim.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define every acronym (AR, PF-ODE, DMD, CD, ODE, ASD, EMA, KV) at its first occurrence in the text.
- **[writing]** Replace or define jargon-heavy terms like "rollout", "chunk-wise", "frame-wise", "mode-seeking", and "mode-covering" with plain English equivalents or provide brief explanatory clauses.
- **[writing]** Ensure that benchmark names (VBench, VisionReward) are introduced with a brief description of what they measure. These changes are essential to make the paper's contributions understandable to a broader scientific audience beyond the immediate sub-field of diffusion distillation.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that causal CD and causal ODE distillation learn the 'same object' lacks rigorous derivation. Eq (1) minimizes MSE to a clean endpoint, while Eq (2) minimizes distance between adjacent timesteps. The paper asserts equivalence via a numerical error bound (Eq 4) but fails to explicitly derive conditions under which the minimizers of these distinct objectives converge to the same function, especially given different supervision signals.
- **[science]** The argument that causal DMD suffers from 'severe exposure bias' due to 'mode-seeking' behavior (Sec 3.4) relies on an intuitive KL-divergence explanation without quantitative evidence. The paper claims DMD is 'more sensitive to accumulated history errors' but provides no theoretical bound or empirical measurement of error propagation rates comparing DMD vs. CD rollouts to substantiate this causal mechanism.
- **[writing]** The latency reduction claim (50% reduction) in the Abstract and Table 2 relies on the ASD trick (keeping the first frame at 4 steps). The logic that 'first-frame latency is identical' for 1, 2, and 4-step settings (footnote in Table 2) contradicts the premise that reducing steps reduces latency. The paper must clarify if the '50% reduction' refers to the average per-frame latency or total video latency, as the first frame dominates the initial wait time.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper exhibits significant overreach in its comparative claims and efficiency metrics, particularly regarding latency and the superiority of the proposed method over existing baselines. First, the Abstract and Conclusion claim that the method reduces "first-frame latency by 50%." This is directly contradicted by the footnote in Table 1 (tab:performance-comparison), which states: "Because we adopt the ASD trick... the first-frame latency for 1-step, 2-step, and 4-step generation is identical.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper presents a technically significant advancement in real-time video generation but raises several safety and ethics concerns that require addressing before publication. Dual-Use and Misuse Risks: The primary concern is the paper's focus on "real-time interactive video generation" and "action-conditioned world models" (Abstract, Sec 3.3). The ability to generate high-quality, interactive video streams with low latency (0.27s first-frame latency) significantly lowers the barrier for creati

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence supporting the central claims of Causal Forcing++ is currently insufficient due to critical ambiguities in experimental design and metric definitions. First, the primary claim of "50% lower first-frame latency" (Abstract, Table 1) is logically inconsistent with the methodology described in the footnote of Table 1. The authors state that the ASD trick keeps the first-frame latency identical across 1-step, 2-step, and 4-step settings because the first frame is always genera

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The statistical rigor of the experimental evaluation in src/4-Experiment.tex is insufficient to support the paper's central claims regarding performance superiority and efficiency gains. First, the quantitative results in Table 1 (Ablation study) and Table 2 (Performance comparison) present only point estimates for metrics like VBench Total, Quality, and VisionReward. There is no reporting of standard deviations, confidence intervals, or the number of independent runs (N) used to generate these

## paper_reviewer_text_formatting — verdict: minor_revision

- **[writing]** The paper's text formatting exhibits several structural inconsistencies and potential compilation risks that require attention before final submission. First, there is a critical dependency issue regarding macro definitions. In Figures_tex/causal-cd.tex and Figures_tex/dmd-is-worse-than-cd.tex, the code utilizes \hspace*{\figxshift} and \hspace{\figgap}. These macros are defined locally within Figures_tex/multi-step.tex (lines 1-4) but are not declared in the global preamble.tex or main.tex. If

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Correct the typo 'Casual ODE' to 'Causal ODE' in Section 3.1, paragraph 3. This is a critical terminology error that undermines the technical precision of the argument.
- **[writing]** Fix the grammatical error in Section 3.2: 'causal ODE distillation and causal consistency distillation (CD) shares' should be 'share' to agree with the plural subject.
- **[writing]** Standardize the capitalization of 'Causal Forcing++' and 'Causal Forcing' throughout the text. Currently, they are sometimes written as 'Causal Forcing++' and other times as 'causal forcing++' or 'Causal forcing'.
- **[writing]** In Section 4.2, the phrase 'which is we discuss' is grammatically incorrect. It should be rephrased to 'as we discuss' or 'which we discuss'.
- **[writing]** Ensure consistent formatting of citations. Some citations use 'et al.' while others use 'et al' without the period. Standardize to 'et al.' as per the provided style guide.
