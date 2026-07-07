# Automated-review action items — Embodied.cpp: A Portable Inference Runtime of Embodied AI Models on Heterogeneous Robots

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Abstract claims 100.0% success for HY-VLA, but Table 1 shows 95% CI [83.9, 100.0]. Stating 100.0% as definitive without qualifying it as the point estimate or upper bound is an overclaim. Qualify as 'up to 100.0% (95% CI: [83.9, 100.0])'.
- **[writing]** Abstract states WAM benchmark reduces memory from 312.2 to 88.1 MiB. Table 2 shows this compares Python BF16 to C++ Q4_K. The gain is from quantization, not the runtime. Clarify that the reduction is achieved via 'Q4_K quantization within the runtime' to avoid misattribution.
- **[science]** Section 2 cites 'Gemini Robotics 1.5' (2025) as a representative model. Verify that this specific version was public and stable by the study date (July 2026) to ensure the claim of it being a 'representative' baseline is factually supportable.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 2: The caption reads 'Project overview of .' with a missing subject (likely 'Embodied.cpp'), making the sentence grammatically incomplete.
- **[writing]** Figure 2: The central title 'Embodied.cpp' is not explicitly defined in the caption, which refers to the system only as 'one embodied-model runtime'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 3.1, Challenge 2: The term 'RK-based' appears without definition. While 'Jetson' is a well-known NVIDIA platform, 'RK-based' (likely Rockchip) is specific hardware shorthand. Add '(e.g., Rockchip-based)' at first use to ensure an adjacent-field reader understands the hardware class.
- **[writing]** Section 3.2, Design Principles: The phrase 'embodied AI kernel warehouse' is introduced as a specific subsystem name. While 'kernel' is standard, 'warehouse' in this context is in-group shorthand for a repository of operators. Add a brief gloss, e.g., 'a repository (warehouse) of reusable operators,' to clarify the operational meaning.
- **[writing]** Section 4, Evaluation: The term 'MEM' appears in the description of HY-VLA ('video-history/MEM vision path') without definition. It is unclear if this refers to a specific module, memory type, or a named component from a prior work. Define 'MEM' (e.g., 'Memory-Enhanced Module') at first use.
- **[writing]** Section 4, Evaluation: The table column header 'Inf. (ms)' uses the abbreviation 'Inf.' for 'Inference'. While common in notes, it is not expanded in the text or table caption. Expand to 'Inference Latency (ms)' or define 'Inf.' in the caption for clarity.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The Abstract claims the WAM benchmark 'reduces block memory from 312.2 MiB to 88.1 MiB,' implying a full model comparison. However, Section 4 (Evaluation) explicitly states the WAM evaluation is a 'preliminary... microbenchmark' on 'only its first Transformer block' because the 'full model is not yet stable.' The Abstract's phrasing suggests a full-system result that the body explicitly denies. Rewrite the Abstract to specify 'single-block memory' to match the body's scope.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims deployment 'across heterogeneous devices, robots, and simulators,' but Section 5 only reports one task (RoboTwin) and a single Transformer block. Narrow the claim to 'demonstrates feasibility on specific targets' or add multi-platform results.
- **[writing]** Table 1 marks 'WAM' and 'Robot' support with a checkmark, implying full validation. Section 5 admits WAM results are a 'preliminary microbenchmark' of one block with no closed-loop execution. Change the checkmark to a partial support symbol (e.g., tmark) to match the evidence.
- **[writing]** The abstract states results 'show... efficiency across diverse architectures,' but the data covers only two VLA models on one task and a WAM block. The conclusion is more modest. Align the abstract's scope with the actual evidence to avoid overgeneralization.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a systems contribution (a C++ inference runtime) for deploying embodied AI models on heterogeneous hardware. From a safety and ethics perspective, the work is low-risk. The research focuses on optimization, portability, and latency reduction for existing model architectures (VLA and WAMs) rather than creating new capabilities for deception, surveillance, or autonomous harm.

The paper does not involve human subjects, personal data collection, or the release of sensitive datasets. The evaluation uses standard benchmarks (RoboTwin) and public model checkpoints (HY-VLA, pi0.5, LingBot-VA) in simulated or controlled environments. There is no evidence of dual-use capabilities being introduced that would lower the barrier to harmful activities (e.g., automated vulnerability discovery, biological synthesis, or mass surveillance) beyond the general capabilities of the underlying models themselves, which are already public.

The authors do not claim to have discovered operational vulnerabilities in live systems, nor do they release exploit code. The "closed-loop control" mentioned refers to standard robotic task execution (e.g., placing a cup), not autonomous weaponization or uncontrolled physical interaction. No conflict of interest is apparent from the text, and the funding/affiliation disclosures are standard for academic research.

As this is a third-party preprint, the absence of a formal "Broader Impacts" statement is noted but does not constitute a safety failure given the low-risk nature of the systems research. The paper does not require specific safety disclosures or mitigations to be published. The verdict is `accept` with no action items required for this lens.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling architectural argument for a specialized C++ runtime for embodied AI, but the experimental evidence provided to support the performance and efficiency claims is currently insufficient to rule out alternative explanations or sampling noise. First, the primary claim of high task success rates in closed-loop execution (Table 1) relies on confidence intervals without disclosing the sample size (number of trials) or the number of random seeds used. A 100% success rate

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical reporting in the Evaluation section requires clarification regarding sample sizes and uncertainty quantification to ensure the reported numbers accurately reflect the underlying data. In Table 1 (VLA deployment results), the success rates are presented with confidence intervals (e.g., HY-VLA: 100.0% [83.9, 100.0]). The presence of a lower bound significantly below 100% for a point estimate of 100% strongly suggests a small number of trials (likely fewer than 10). However, the man

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and the technical narrative is clear, but there are specific instances where the prose impedes the reader's flow or breaks the immersion of a formal research paper. The most significant issue is in Section 4 (Evaluation), where the text begins with "This revision reports..." This phrasing is meta-commentary intended for a peer-review process, not for the final paper text. It forces the reader to pause and wonder if they are reading a draft or a final public
