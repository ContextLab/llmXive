# Automated-review action items — Kairos: A Native World Model Stack for Physical AI

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The claim of 'perfect scores' (1.00) in Newtonian, fluid, and gravity on WorldModelBench (Table 1, e002) is statistically improbable. Verify if these are rounded values; if so, rephrase to 'near-perfect' or provide exact decimals to avoid misleading readers.
- **[writing]** The latency speedup range of 28x–85x (Table 2, e001) lacks a clear derivation for the 28x lower bound from the provided 1GPU/4GPU data. Clarify which specific configuration yields the 28x figure or adjust the range to match the calculated ratios (~58x–76x).
- **[science]** The paper cites 'Qwen3.5' (2026 preprint) and attributes specific benchmark scores (e.g., MMMU 64.2) to it (Table 3, e002). Verify these models are publicly available and scores are accurate, as using unreleased models as baselines can be misleading.
- **[writing]** The text conflates the theoretical guarantee of 'state propagation' (risk bounds in Theorem 2) with 'linear time complexity' (algorithmic efficiency). Explicitly distinguish between the statistical sufficiency of the memory and the computational complexity claims.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The Sankey diagram lacks a legend defining the color coding (e.g., purple, beige, yellow, green, grey) for the nodes and flows, making it impossible to distinguish between data sources, intermediate stages, and specific filter types.
- **[science]** Figure 1: The diagram is missing quantitative units or values (e.g., number of samples, percentages) on the flows or nodes, rendering the 'pipeline' visualization qualitative and unable to support claims about data volume reduction or filtering efficiency.
- **[writing]** Figure 5: The caption contains a typo, spelling the dataset as 'WordelModelBench' instead of 'WorldModelBench'.
- **[writing]** Figure 8: The caption 'Human evaluation results' is too generic for a complex multi-panel figure; it should specify that the figure compares Kairos against four specific baselines (cosmos-predict2.5, lingbot-14B, wan2.2) across three datasets.
- **[writing]** Figure 8: The y-axis labels 'Paibench robot-subset', 'WorldModelBench robot-subset', and 'Dreamgen' are repeated in every subplot; consolidating these into a single shared axis or using a grid layout would reduce visual clutter.
- **[writing]** Figure 9: The caption states 'Kairos samples on the PAI-Bench dataset' but does not specify that the images show 'Input frame' followed by 'Predicted frames', making the temporal nature of the samples unclear.
- **[writing]** Figure 9: The column headers 'Input frame' and 'Predicted frames' are present but the number of predicted frames per input is not specified in the caption, leaving the reader to infer the temporal span.
- **[writing]** Figure 10: The caption 'Kairos samples(TI2V)' is ambiguous; it does not explicitly state that the left column represents the input frame and the subsequent columns represent the predicted frames, forcing the reader to infer the temporal progression.
- **[writing]** Figure 10: The image contains internal labels ('input frame', 'Predicted frames') that are not referenced or defined in the caption, creating a disconnect between the visual annotation and the textual description.
- **[science]** Figure 12: The 'Generated Frames' columns show significant visual artifacts and temporal inconsistencies (e.g., flickering mixer, morphing coffee stream, unstable waterfall) compared to the 'Prompt' column, which undermines the claim of generating high-quality physical AI samples.
- **[writing]** Figure 12: The caption is overly brief and does not explain the layout (e.g., that the first column is the prompt and subsequent columns are generated frames) or the nature of the 'VideoPhy dataset' samples shown.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript suffers from significant jargon overuse, relying heavily on unexplained acronyms and marketing-style terminology that obscures meaning for non-specialist readers. The term "Physical AI" is used repeatedly as a proper noun without definition, creating an immediate barrier to entry. Similarly, "Native" is used as a modifier for "Pre-training Paradigm" and "Unified Architecture" without technical justification, functioning more as a buzzword than a descriptor. Acronyms are frequently

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is generally strong in its theoretical framing but contains gaps in the causal linkage between the proposed mechanisms and the empirical claims. First, the theoretical argument for the necessity of persistent states (Theorem 1, Section 3.3 and Section 6.1) is logically sound: it correctly identifies that if a target depends on history outside a window, a window-restricted predictor incurs irreducible excess risk. However, the paper asserts that baseline model

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper exhibits significant overreach in its framing of theoretical guarantees and performance claims. First, the Abstract and Conclusion repeatedly assert that the architecture "mathematically guarantee[s] state propagation" and "guarantee[s] long-horizon state maintenance." This is a strong over-claim. The theoretical section (Section 6) provides theorems establishing the *necessity* of persistent states for supra-window dependence and the *approximate sufficiency* of a hybrid memory under

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Consent: How was consent obtained from individuals appearing in the "human-centric" and "first-person" videos?
- **[writing]** Copyright: What is the licensing status of the "internet-crawled" material?
- **[writing]** Privacy: How are personally identifiable information (PII) and biometric data (faces, voices) handled in the training set? Without a clear statement on compliance with GDPR, CCPA, or similar frameworks, the use of such a massive, uncurated dataset poses a severe privacy risk. Safety of Generated Outputs (Section Evaluation Results): The paper claims state-of-the-art performance on physical benchmarks (WorldModelBench, PAI-Bench) but lacks a dedicated safety evaluation. For a model designed to co
- **[writing]** Reward Hacking: The model might optimize for the internal reward function in ways that violate safety constraints.
- **[writing]** Drift: Unsupervised self-improvement could lead to the emergence of unsafe behaviors over time. The paper must discuss the safeguards, monitoring mechanisms, and human-in-the-loop requirements for these autonomous loops. Dual-Use Concerns: The capability to simulate complex physical interactions and generate high-fidelity robotic control policies has inherent dual-use potential. The authors should include a brief discussion on the responsible release of the model and data, potentially considerin

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The claim of 'mathematically guaranteeing state propagation' (Abstract) and 'exact sufficiency' (Corollary 3) relies on unverified assumptions about the contractivity of the learned Gated Linear Attention (GLA) gates. The paper must provide empirical evidence (e.g., spectral radius analysis of learned gates) or a rigorous proof that the learned parameters satisfy the contraction condition (rho < 1) required by Theorem 2, rather than assuming it holds by design.
- **[science]** Benchmark results (e.g., Table 1, Table 2) show marginal or statistically insignificant differences between Kairos and baselines (e.g., 9.30 vs 9.26 on WorldModelBench). The paper lacks statistical significance testing (p-values, confidence intervals, or standard deviations over multiple seeds) to support the claim of 'SOTA' performance. Without this, the observed gains could be due to random variance.
- **[science]** The ablation study in Table 3 (Human-Centric Data Scaling) reports a Total Score increase from 9.08 to 9.25. However, the paper does not specify the number of training runs, seeds, or variance associated with these scores. Given the small absolute gain (~1.8%), the robustness of this claim is questionable without statistical validation.
- **[science]** The efficiency claims (Table 4) compare Kairos-4B against baselines with different parameter counts and architectures. The paper fails to normalize for compute budget (FLOPs) or training data volume. The '28x-85x speedup' is a raw latency comparison that does not account for the fact that baselines may be larger models; a fair comparison requires controlling for model scale or training compute.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** Human evaluation methodology is statistically under-specified. Section 'Human Evaluation' cites '10 volunteers' but omits the statistical test used (e.g., binomial test, t-test), confidence intervals, or p-values for the reported win rates (e.g., 60.2% vs Cosmos). Without variance estimates or significance testing, these claims are anecdotal rather than statistical evidence.
- **[science]** Ablation study sample sizes are missing. Tables 4 and 5 report performance deltas (e.g., +6.0 on LIBERO-Plus) but do not state the number of evaluation episodes or seeds used. Without N, it is impossible to determine if these gains are statistically significant or within the noise floor of the benchmark.
- **[science]** Benchmark metrics lack uncertainty quantification. Tables 1, 2, 3, and 6 present point estimates for scores (e.g., 9.30, 0.538) without standard deviations, confidence intervals, or error bars. Given the stochastic nature of diffusion models and RL, single-point reporting is insufficient to claim 'SOTA' status over baselines with similar scores.
- **[science]** The theoretical 'excess risk' bounds in Section 6 are not empirically validated. The paper derives bounds involving constants (L, rho, epsilon) but provides no empirical estimation of these parameters or a comparison between the theoretical bound and the observed error on the test set, rendering the theoretical contribution disconnected from the experimental results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a comprehensive technical contribution, but the writing quality is currently compromised by significant structural redundancy and inconsistent formatting that impedes readability. The most critical issue is the duplication of major sections. Specifically, the "Conclusion and Future Works" and "Theoretical Analysis" sections appear in multiple chunks (e.g., e002 and e003) with slight variations in phrasing. This suggests a compilation error or a failure to merge draft vers
