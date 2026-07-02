# Automated-review action items — Rethinking Cross-Layer Information Routing in Diffusion Transformers

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3 (Diagnosing Cross-Layer Information Flow), the claim that forward magnitude grows from ~15.5 to ~1576 (100x inflation) is attributed to Fig. 1. However, the text states this is measured at t=1.0, while the abstract and intro imply these symptoms persist throughout training. Clarify if the 100x figure is specific to the final timestep or an average, as the magnitude of inflation likely varies with noise level.
- **[science]** The claim in Section 5.2 that DAR+REPA at 100K iterations (FID 7.09) surpasses REPA alone at 200K (FID 6.89) is mathematically incorrect based on Table 2. 7.09 is worse than 6.89. The text likely meant to compare against REPA at 100K (9.89) or claim a different iteration count. This numerical error undermines the '2x acceleration' claim in the abstract.
- **[science]** The abstract claims DAR matches the baseline's converged quality with 8.75x fewer iterations. The baseline (SiT) is trained for 1.75M iterations, and DAR for 600K (static) or 500K (dynamic). 1.75M / 600K ≈ 2.9x, not 8.75x. The 8.75x figure appears to be a calculation error or refers to a different baseline not clearly defined in the text.
- **[writing]** In Section 5.3, the text claims the dynamic variant attains the best ODE FID with CFG (2.05). Table 1 shows 'Dynamic c4 ODE w/ guidance' has FID 2.05, but 'Static c4 ODE w/ guidance' has 2.08. While 2.05 is indeed the best in that specific row, the text implies a general superiority that might be overstated given the small margin and the fact that Static c4 SDE w/o guidance (6.92) is the overall best FID reported. Ensure the claim 'best ODE FID' is qualified correctly.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Forward Magnitude' and 'Gradient Magnitude' plots show the orange line ('DAR Static b4') as flat at zero, which is physically impossible for gradient magnitudes in a functioning network and likely indicates a plotting error or missing data rather than a valid comparison.
- **[writing]** Figure 1: The legend is positioned outside the plot area at the top center without a bounding box or clear alignment, making it ambiguous which subplot it applies to, although context implies all three.
- **[science]** Figure 2: The y-axis for the 'block 13' subplots (both SiT and DAR) is labeled with non-sequential integers (0, 3, 6, 10, 13), which contradicts the caption's description of plotting patterns across 'source index n' and makes the data density and continuity ambiguous.
- **[writing]** Figure 2: The x-axis tick labels ('0.01', '0.5', '0.99') are inconsistent with the caption's claim that measurements are taken 'across denoising timesteps' (implying a continuous range) and do not clearly indicate the direction of time (forward vs. reverse).
- **[science]** Figure 3: The x-axis on the left plot ('Latency speedup') is non-linear and discontinuous (1, 10, 20, 30, 40, 50, 57), which distorts the visual representation of the speedup trend and makes the slope between points misleading.
- **[writing]** Figure 3: The legend in the right plot ('Activation-memory saving') is placed inside the plot area, partially obscuring the data points for N=40 and N=50.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'DiT' and 'DMD' at first use. 'DiT' appears in the abstract without definition. 'DMD' appears in the abstract and Section 5.2 without definition, relying on the reader to know 'Distribution Matching Distillation'.
- **[writing]** Define 'REPA' at first use. The acronym appears in the abstract and Introduction without spelling out 'Representation Alignment for Generation' or similar, assuming prior knowledge of the cited work.
- **[writing]** Define 'adaLN' and 'adaLN-Zero'. These terms appear in Section 4.2 and the Introduction without definition. While common in specific sub-fields, they are not standard enough for a general ML audience without a brief explanation (e.g., 'adaptive Layer Normalization').
- **[writing]** Define 'T2I' and 'T2V'. These acronyms appear in the abstract and Section 5.2. They should be spelled out as 'text-to-image' and 'text-to-video' upon first occurrence.
- **[writing]** Define 'HBM' in the Infrastructure section. The text mentions 'materializing... in HBM' without defining it as 'High Bandwidth Memory', which may be opaque to readers focused on algorithmic design rather than hardware implementation.
- **[writing]** Clarify 'PreNorm'. The term 'PreNorm dilution' is used frequently (Abstract, Intro, Sec 3) assuming the reader knows 'Pre-Normalization'. A brief parenthetical definition on first use would improve accessibility.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim of '8.75x fewer iterations' (Abstract) compares 600K (Static) vs 1.75M (SiT). However, the best ODE FID comes from Dynamic (500K), implying a 3.5x speedup. Clarify which variant supports the 8.75x claim or correct the multiplier to match the best-performing model's data.
- **[science]** Section 5.2 claims the dynamic query works because $v_{l-1}$ retains timestep info, but the linear probe measures $h_l$ (aggregated state), not $v_{l-1}$ (query input). The logic requires confirming the probe was on $v_{l-1}$ or explaining why $h_l$ is a valid proxy for the query's input signal.
- **[science]** Proposition 1 derives optimal chunk size $S^*$ from a theoretical cost function, yet Table 4 shows empirical FID results. The paper assumes minimizing this theoretical cost minimizes FID without proving the correlation. Clarify if the cost function was empirically validated against FID or if the agreement is coincidental.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim of '8.75x fewer iterations' to match 'converged quality' (Abstract) is unsupported. Table 1 shows the baseline improves significantly between 600K and 1.75M iterations. The paper does not prove DAR at 600K matches the baseline's final converged state, only its intermediate state.
- **[writing]** The claim that DAR 'preserves high-frequency details' in DMD (Abstract, Sec 5.5) lacks evidence in the main text. The authors defer samples to the appendix without showing visual comparisons or quantitative metrics (e.g., LPIPS) to substantiate this specific qualitative claim.
- **[writing]** The statement that diagnostic symptoms 'tighten in lockstep' with FID gains (Intro) overstates the evidence. The paper shows symptoms exist in the baseline and FID improves with DAR, but lacks a direct quantitative correlation analysis proving the reduction in symptoms tracks the FID improvement.

## paper_reviewer_safety_ethics — verdict: accept

The manuscript presents a novel architectural modification (Diffusion-Adaptive Routing) for Diffusion Transformers (DiTs) aimed at improving training efficiency and generation quality. From a safety and ethics perspective, the work does not raise immediate red flags regarding dual-use risks, data privacy, or human subject harm.

The research utilizes the ImageNet-1K dataset (Section 5.1), a standard public benchmark for computer vision. The paper correctly cites the dataset source (Russakovsky et al., 2015) and does not claim to use private, sensitive, or personally identifiable information. No human subjects were involved in the data collection or model training process, rendering IRB/IACUC approval unnecessary for this specific study.

Regarding dual-use potential, the proposed method accelerates the training of image generation models. While generative AI can be misused for creating deepfakes or synthetic media, the paper focuses on architectural efficiency (reducing training iterations by 8.75x) rather than introducing new capabilities for generating specific harmful content (e.g., non-consensual imagery, disinformation campaigns, or biological threats). The authors explicitly discuss the method's application in "large-scale T2I model post-training" (Section 5.6) and "Distribution Matching Distillation," which are standard industry practices. The paper does not provide instructions on how to bypass safety filters or generate prohibited content.

The authors acknowledge the broader context of generative models in the introduction and related work but do not make specific claims about the societal impact of their specific architectural change beyond efficiency gains. There are no conflicts of interest disclosed that would compromise the integrity of the safety analysis, although the authors are affiliated with Alibaba Group and academic institutions, which is standard for this field.

The paper does not contain any code or data that would facilitate the immediate creation of harmful artifacts. The "Infrastructure" section (Appendix) details kernel optimizations for efficiency, which are neutral technical improvements. Consequently, the paper is deemed safe for publication from an ethics and safety standpoint, provided the authors maintain standard responsible AI practices in any future deployment of the technology. No action items are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of '8.75x fewer training iterations' (Abstract, Intro) relies on comparing 600K iterations of DAR against 1.75M of SiT. However, Table 1 shows SiT-Plus (752M params) trained for 1M iterations still underperforms DAR. The paper lacks a direct comparison of DAR vs. SiT at the *same* iteration count (e.g., 600K) to isolate the architectural gain from the training duration effect. Re-run or report the FID of the baseline SiT at 600K iterations to validate the convergence speed claim.
- **[science]** The diagnostic in Section 3 (Fig. 1) measures gradient decay and magnitude inflation at a single timestep (t=1.0). The central hypothesis is that these symptoms are time-varying. The evidence is insufficient without showing that these metrics (magnitude, gradient, redundancy) vary significantly across the full denoising trajectory (t=0 to t=1), not just at the start of the process.
- **[science]** The chunk size ablation (Table 3) tests only S={1, 4, 8}. The theoretical derivation (Prop 1) suggests an optimal S* dependent on alpha. Without testing intermediate values (e.g., S=2, 3, 5, 6) or reporting the fitted alpha, the empirical validation of the 'U-shaped' cost function is weak. The claim that S=4 is the global optimum is not robustly supported by the sparse grid search.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 3 (Diagnosing Cross-Layer Information Flow) reports specific diagnostic statistics (e.g., RMS magnitude ~1576, gradient ~5e-7) but lacks measures of variance (standard deviation or confidence intervals) across the 4096 samples. Given the stochastic nature of training and sampling, reporting error bars or standard errors is necessary to confirm these trends are robust and not artifacts of specific random seeds or batch compositions.
- **[science]** Table 1 and Table 2 report FID and other metrics as single point estimates. Standard practice for generative model evaluation requires reporting the mean and standard deviation over multiple independent training runs (typically 3-5 seeds) to account for training stochasticity. Without this, the claimed '2.11 FID improvement' and '8.75x speedup' lack statistical significance testing.
- **[science]** The linear-probe analysis in Section 4.2 (Fig. 4) reports test R^2 values. The methodology mentions fitting a ridge regressor on 'disjoint pair-level train/test splits,' but does not specify the number of splits, the cross-validation strategy, or the variance of the R^2 scores. A single R^2 value per block is insufficient to validate the robustness of the timestep decoding claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Overall, the main contributions of this paper are summarized as follows' is immediately followed by an itemized list without a terminal punctuation mark (period or colon). Insert a colon or period after 'follows' to adhere to standard grammatical conventions.
- **[writing]** In Section 5.2 (Timestep Awareness), the phrase 'timestep awareness---regardless of how it is injected---is the key ingredient' uses em-dashes for parenthetical insertion. While stylistically acceptable, ensure consistent usage of em-dashes (with or without spaces) throughout the manuscript, as some instances in the text use spaces around dashes while others do not.
- **[writing]** In Section 5.3 (DAR Is Orthogonal to REPA), the sentence 'The two interventions therefore act along orthogonal axes, and a natural question is whether their gains compound or merely overlap' is slightly wordy. Consider tightening the phrasing to 'Thus, a natural question is whether these orthogonal interventions compound or merely overlap' to improve flow and conciseness.
