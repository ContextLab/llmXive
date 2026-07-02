# Automated-review action items — Visual Generation in the New Era: An Evolution from Atomic Mapping to Agentic World Modeling

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Fig 1 caption claims 2025 contributed 188 papers (45.7%) of 411 post-2014 refs. Bibliography contains 2026 citations (e.g., he2026gems). If 2026 refs are included, the 45.7% stat for 2025 is mathematically inconsistent. Recalculate stats or clarify the corpus cutoff date.
- **[fatal]** Section 5.1 claims 'GPT 5.5 verified mismatches'. GPT 5.5 is not a released model. Citing a non-existent model as a factual verifier invalidates the stress test results. Correct to an existing model (e.g., GPT-4o) or remove the specific version.
- **[writing]** Section 2.2 cites 2026 papers (e.g., HunyuanImage 3.0) as established facts with specific architecture details. Verify these are publicly available preprints and not speculative roadmaps. Qualify claims if sources are unreleased.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The x-axis includes 2026, but the caption states the analysis covers '411 post-2014 references' and the 2025 bar is labeled '2025 surge' with 188 papers. If 2026 data is included, the total count and percentages (e.g., 45.7% for 2025) may be inaccurate or misleading if 2026 is incomplete or projected.
- **[writing]** Figure 1: The y-axis label 'Annual Publications' is clear, but the right y-axis label 'Cumulative Count' lacks a unit or clarification that it represents the running total of publications, which could confuse readers unfamiliar with cumulative plots.
- **[science]** Figure 1: The 2026 bar shows 26 publications, but since the current year is 2026 and the data may be incomplete, presenting it as a full-year count without qualification misrepresents the data's completeness and could distort trend interpretation.
- **[writing]** Figure 2: The caption text is truncated mid-sentence at the end ('...diffusion & flow models anch'), cutting off the description of mature foundations.
- **[science]** Figure 2: The bubble labeled 'Text Rendering & Design' is positioned at a mean publication year of ~2024 but has a very low recency share (~0.25), which contradicts the caption's claim that the upper-right quadrant represents recent topics, as this topic appears neither recent nor growing relative to others.
- **[science]** Figure 4: The timeline includes models with future release dates (e.g., '2025-06 FLUX.1', '2026 Nano-Banana') and labels the current period as '2024–2025', implying the preprint is written from the future or contains speculative projections presented as historical facts without clear distinction.
- **[writing]** Figure 4: The legend defines 'Closed Sourced (Infered) Hybrid/Agentic' with a dashed border, but the corresponding nodes (e.g., '2026 GPT-Image2') are not explicitly labeled as 'Closed Sourced' in the node text itself, relying entirely on the border style which may be ambiguous.
- **[writing]** Figure 5: The caption for (5) Hybrid (AR + Diffusion) is truncated mid-sentence ('producing th'), cutting off the description of the final image generation.
- **[writing]** Figure 6: The caption states '$$ denotes unified models', but the rendered figure uses a star symbol (★) to mark these models (e.g., Bridge, Chameleon). The caption text must be corrected to match the visual symbol.
- **[science]** Figure 6: The legend box on the right lists 'Adversarial' as a category with a corresponding color swatch, but the 'Adversarial' models (DCGAN, WGAN, etc.) are positioned in a separate box at the bottom, outside the main Venn diagram structure implied by the legend.
- **[science]** Figure 9: The diagram depicts a 'Reasoning controller' and 'Verifier' as distinct, separate agents (robots) with thought bubbles, but the caption describes a single 'frontier VLM' that ingests instructions and emits plans. This visual separation contradicts the textual description of a unified model performing these steps.
- **[writing]** Figure 9: The 'Tool set' box on the left lists 'Web search grounding' and 'Image retrieval', but the caption's example tools are 'text-rendering' and 'font alignment'. The mismatch between the visualized tools and the caption's examples creates ambiguity about the system's actual capabilities.
- **[writing]** Figure 11: The caption lists 'Wan-Image' as an example for Trajectory Matching, but the figure panel (a) only labels 'Hyper-SD, RayFlow'.
- **[writing]** Figure 11: The caption lists 'rCM' as an example for Consistency, but the figure panel (b) only labels 'CM, LCM, sCM, MeanFlow'.
- **[writing]** Figure 11: The caption lists 'MeanFlow' as an example for Distribution Matching, but the figure panel (c) only labels 'DMD, DMD2, ADD'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define acronyms at first use throughout the manuscript (e.g., SFT, MoE, VAE, SSM, RL, DPO, GRPO, ODE, LLM, DiT, AR, VLM, MDP, NFEs, VQ, SSL, RAE, MLLM, VLA, VFM, CLIP, SigLIP, LoRA, GAN, DDPM, DDIM, SDE, CE, MoT, MPO, NLP, BLEU, SMILES, OCR, VQ-VAE, VQ-GAN, VQ-Transformer, VQ-VAE-2, VQ-VAE-3, VQ-VAE-4, VQ-VAE-5, VQ-VAE-6, VQ-VAE-7, VQ-VAE-8, VQ-VAE-9, VQ-VAE-10).
- **[writing]** Replace or define the colloquial term "Nano Banana" in the Introduction (Section 1, Paragraph 2) as it is not a standard technical term and excludes non-specialist readers.
- **[writing]** Define "Rectified Flow" and "Flow Matching" explicitly upon first mention in Section 2.1, as these are specific technical concepts not universally known outside the immediate subfield.
- **[writing]** Clarify the term "Agentic" in the context of "Agentic World Modeling" (Title and Section 1) to ensure readers understand it refers to autonomous decision-making loops rather than general agency.
- **[writing]** Define "VLM-as-a-Judge" in Section 4.1.1, as this is a specific paradigm that requires explanation for readers unfamiliar with the latest evaluation trends.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that 2025 contributed 45.7% of the 411 post-2014 references (Fig 1 caption) is mathematically inconsistent with the timeline. If the corpus ends in 2025, a single year cannot constitute nearly half of a 10-year span unless the publication rate is exponentially skewed, which requires explicit justification or a correction of the denominator (e.g., '45.7% of *recent* works' vs 'total works').
- **[science]** The distinction between Level 3 (In-Context) and Level 4 (Agentic) relies on 'single forward pass' vs 'multiple passes' (Table 1, Sec 2.3/2.4). However, the text cites 'Multi-turn editing' under Level 3, which inherently implies multiple passes. This creates a logical contradiction in the taxonomy definition that must be resolved by clarifying if 'turns' in L3 are batched into one pass or if the definition of L3 needs adjustment.
- **[science]** The paper asserts that closed-source systems realize 'L4 agentic generation' while open systems are 'L3-bounded by construction' (Sec 2.4, Community Message). This is a causal claim unsupported by evidence; it assumes architectural opacity implies a specific control loop structure. The argument conflates 'observed capability' with 'internal mechanism' without providing a logical bridge or counter-example analysis.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that '60% of recent frontier reports ship a fully unified architecture' (Section 2.1, Highlight Box) is based on a self-selected cohort of ten specific reports. The authors must clarify if this percentage is a generalizable industry statistic or a specific observation of their curated list to avoid over-generalization.
- **[writing]** The paper asserts that closed-source systems (e.g., GPT-Image) realize 'L4 agentic generation' while open systems are 'L3-bounded by construction' (Section 2.3). This is a strong architectural claim without empirical evidence of the internal agent loops of proprietary models. The language should be softened to 'conjecture' or 'hypothesis' rather than stated as a definitive fact.
- **[writing]** In Section 5.1, the paper states that 'Reasoning-augmented generation is most useful in three regimes' and implies it generally fails for aesthetic prompts. This overstates the current consensus; while trade-offs exist, the claim that explicit reasoning 'amplifies hallucinations' for aesthetic prompts is a broad generalization not fully supported by the cited examples (e.g., the physics-exam case).

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper extensively discusses 'Agentic Generation' (L4) and 'World-Modeling' (L5) for embodied tasks and robotics (Sec 3.4, 5.4). It must explicitly address safety guardrails for physical deployment, specifically how these models prevent generating unsafe trajectories or instructions that could cause physical harm to humans or property.
- **[science]** The 'Stress Testing' section (Sec 4) and 'World Modeling' section (Sec 5.4) describe generating counterfactuals (e.g., collisions, sinking objects) and simulating physical interactions. The manuscript should clarify the ethical boundaries of these simulations, particularly regarding the potential for dual-use in training agents for malicious physical actions or bypassing safety filters in real-world robotics.
- **[writing]** The paper cites the use of 'User-Generated Content' from Reddit (r/PhotoshopRequest) and 'Frontier Distillation' from proprietary APIs (Sec 3.2.2). It lacks a statement on data privacy, consent, and the ethical handling of potentially sensitive or personally identifiable information (PII) within these datasets, as well as the terms of service compliance for distilling closed-source models.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The stress-test case studies (e.g., Metro Map, Jigsaw Puzzle in Sec 6) lack quantitative rigor. Report sample sizes (N), number of model runs per prompt, and statistical significance of failure rates rather than single qualitative examples.
- **[science]** Claims regarding 'closed-source' superiority (Sec 2.4) are presented as conjecture without empirical data. Provide comparative metrics (e.g., adherence scores, error rates) against open baselines or explicitly label these as unverified hypotheses.
- **[science]** The taxonomy (L1-L5) is a conceptual framework, not an empirically validated hierarchy. Clarify that the 'levels' are qualitative distinctions and avoid implying a strict, measurable progression without defining quantitative thresholds for each level.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The publication trend analysis (Fig 1) reports 2025 contributing 45.7% of 411 references. As 2025 is the current year, this figure is likely biased by the cutoff date of the bibliography rather than a true exponential surge. The authors must clarify the data collection window and whether this percentage reflects a genuine trend or a sampling artifact.
- **[science]** The 'Stress Testing' section (Sec 6) presents qualitative failure modes (e.g., Metro Map, Jigsaw) without quantitative aggregation. To support claims about 'spatial logic' failures, the authors should report success rates, confidence intervals, or statistical significance tests across a larger, defined set of prompts rather than relying on anecdotal case studies.
- **[science]** In the evaluation section (Sec 5), the paper cites Spearman agreement scores (0.57–0.75) for VLM judges against humans but does not specify the sample size (N) or the specific benchmark subsets used. Without N and p-values, the statistical reliability of these correlation claims cannot be assessed.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2.1 (Level 1), the phrase 'Uncontrolled variation' is used as a key challenge header, but the subsequent explanation lacks a clear subject-verb structure, reading as a fragment. Rephrase to a complete sentence (e.g., 'The primary challenge is uncontrolled variation...') to improve flow.
- **[writing]** In Section 3.1, the sentence 'Views denoising as an MDP' is grammatically incomplete. It should be 'We view denoising as an MDP' or 'This section views denoising as an MDP' to establish the subject.
- **[writing]** In Section 4.2, the phrase 'The field is shifting from optimizing statistical plausibility to satisfying explicit constraints' is slightly ambiguous regarding the agent. Clarify to 'The field is shifting from optimizing for statistical plausibility to satisfying explicit constraints' for better readability.
- **[writing]** Throughout the paper (e.g., Section 2.4, 3.2), the use of 'L1', 'L2', etc., is introduced without a consistent definition of the abbreviation 'L' (Level) in the immediate context of the first usage in each subsection. Ensure 'Level 1 (L1)' is explicitly defined at first mention in every major section to aid reader navigation.
