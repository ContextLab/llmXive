---
action_items:
- id: 356c4c71a1ca
  severity: writing
  text: 'Abstract: The claim that GPTQ/GPTAQ ''diverge'' at 2-bit is specific to LLaMA-3-70B
    (Table 3), yet the abstract implies a general failure of these methods. Table
    1 shows they work on LLaMA-2 models. Scope the claim to ''on LLaMA-3-70B'' to
    avoid implying universal divergence.'
- id: ce6dc34e79b1
  severity: writing
  text: 'Introduction: The claim of ''consistent state-of-the-art results'' overstates
    the marginal gains on LLaMA-2-70B (W4). Clarify that gains are ''particularly
    significant at ultra-low bit-widths where baselines fail'' to match the evidence
    in Tables 1 and 3.'
- id: 28d956047ba0
  severity: writing
  text: 'Section 5 & Conclusion: Claims of generalization to ''newer model families''
    and ''harder benchmarks'' rely on limited tests (2 models, specific bits). Add
    qualifiers like ''on the tested newer model families'' to align the scope with
    the specific evidence provided.'
artifact_hash: 6bdf7827fba12b0d8bdf1afc2ca37e869d5688f3fbc4e54d47c586b30e10b890
artifact_path: projects/PROJ-1045-kronq-llm-quantization-via-kronecker-fac/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T03:59:17.281374Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for incorporating gradient covariance into post-training quantization, with strong empirical results on the LLaMA family. However, there are minor instances of overreach in the framing of the results' scope, particularly regarding the universality of the "divergence" problem in baselines and the breadth of generalization claims.

In the **Abstract**, the statement that GPTQ and GPTAQ "diverge or produce degenerate quantizations" on LLaMA-3-70B is factually correct based on the provided tables. However, the phrasing implies this is a general property of these methods at 2-bit, whereas the results in Table 1 show that GPTQ and GPTAQ function correctly (albeit with higher perplexity) on LLaMA-2-7B and LLaMA-2-13B at 2-bit. The divergence is a specific artifact of the LLaMA-3-70B weight distribution (as explained in Appendix A.6). The abstract should be slightly narrowed to specify that this failure mode is observed on LLaMA-3-70B, preventing the reader from inferring that 2-bit quantization is universally impossible for GPTQ/GPTAQ on all architectures.

In the **Introduction**, the claim of "consistent state-of-the-art results" is largely supported, but the magnitude of the "state-of-the-art" status varies significantly. On LLaMA-2-70B at W4, the improvement over GPTQ is marginal (3.41 vs 3.50), whereas on LLaMA-3-70B at W2, it is transformative (8.43 vs divergence). The current phrasing risks conflating these two regimes. While not a fatal flaw, clarifying that the "consistent" gains are most pronounced in the ultra-low-bit regime where baselines struggle would better align the rhetoric with the nuanced evidence.

Finally, the **Generalization** claims in Section 5 and the **Conclusion** extend the findings to "newer model families" and "harder benchmarks." While the paper does test Gemma-3, DeepSeek, and Phi-4, the evaluation is restricted to specific bit-widths (W4/W2) and a limited set of benchmarks (MMLU, GPQA, AIME, LiveCodeBench) on only two of these new models. The rhetoric suggests a broader validation than the specific experimental setup provides. Adding qualifiers such as "on the tested newer model families" or "across the evaluated reasoning benchmarks" would ensure the scope of the claim matches the specific evidence presented.

These are primarily issues of precision in the framing of the results rather than fundamental flaws in the evidence. The paper's core contribution is well-supported, but tightening the scope of the general claims will prevent overinterpretation by the reader.
