---
action_items:
- id: 04909354308b
  severity: science
  text: Table 1 claims iLLaDA-Base is 'slightly stronger' than Qwen2.5 7B (63.9 vs
    63.3). Without reported standard deviations or multiple evaluation seeds, this
    0.6-point difference may be statistically insignificant. Please report variance
    estimates or run multiple seeds to validate significance.
- id: da345e81ae6f
  severity: science
  text: Figure 3 shows SFT performance plateauing after 8-10 epochs, yet the text
    claims continuous improvement. Please analyze if gains at 12 epochs are statistically
    significant versus 8 or 10 epochs and discuss overfitting risks given the small
    instruction corpus.
- id: 46c7fb7cc5b7
  severity: science
  text: The claim that the Qwen2.5-Instruct gap is solely due to missing RL alignment
    is unverified. Please provide evidence (e.g., controlled ablation or specific
    citations on RL gains in diffusion) that RL accounts for the observed gap magnitude,
    ruling out SFT data differences.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T10:46:04.286249Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence presented in the manuscript is generally robust, demonstrating a clear and substantial improvement of iLLaDA over the baseline LLaDA model across multiple benchmarks. The scaling of pre-training to 12T tokens and the architectural modifications (GQA, tied embeddings) are well-motivated and the resulting performance gains (e.g., +21.6 on BBH, +14.9 on ARC-Challenge) are significant and unlikely to be artifacts of random variation. The ablation studies on scoring rules (Table 3) provide concrete evidence that the proposed confidence-based scoring improves evaluation metrics, supporting the methodological choices.

However, the statistical rigor regarding the comparison with the strong autoregressive baseline (Qwen2.5 7B) is insufficient. In Table 1, the claim that iLLaDA-Base is "slightly stronger on average" (63.9 vs 63.3) relies on a single point estimate per benchmark. Large language model benchmarks often exhibit non-negligible variance due to stochastic decoding, prompt sensitivity, or evaluation script variations. Without reporting standard deviations, confidence intervals, or results from multiple evaluation seeds, the statistical significance of this 0.6-point average difference cannot be established. It is possible that the difference is not statistically significant, which would alter the interpretation of the model's competitiveness.

Furthermore, the analysis of the SFT duration ablation (Figure 3) lacks a critical discussion of overfitting. While the curves show improvement up to 12 epochs, the rate of improvement appears to diminish, and in some cases (e.g., MATH), the curve flattens. The text asserts that the model "continues to improve" but does not quantify the marginal gain of the final epochs or test for statistical significance between 8, 10, and 12 epochs. Given the small size of the instruction corpus (25B tokens) relative to the pre-training corpus, the risk of overfitting is non-trivial, and the authors should provide evidence that the 12-epoch setting is optimal rather than merely the limit of their compute budget.

Finally, the attribution of the performance gap in the instruction-tuned setting solely to the lack of RL alignment is a plausible hypothesis but remains an unverified claim. The authors should clarify if the SFT data for iLLaDA is directly comparable to that of Qwen2.5 or if differences in data quality/quantity could contribute to the gap. A more rigorous control or citation of specific RL impact magnitudes in similar diffusion settings would strengthen this argument.
