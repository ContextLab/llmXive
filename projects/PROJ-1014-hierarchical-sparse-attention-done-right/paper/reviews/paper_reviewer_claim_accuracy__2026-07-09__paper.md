---
action_items:
- id: 4e7e96112e10
  severity: writing
  text: The paper presents a novel sparse attention mechanism, HiLS, with strong empirical
    results. However, several factual claims regarding performance metrics and comparisons
    require precise alignment with the provided tables to avoid overstatement or ambiguity.
    First, the Abstract claims HiLS extrapolates "64x the training context length
    with 90% retrieval accuracy." The training length is 8K, so 64x is 512K. Table
    345M_main_ruler shows HiLS achieving 100% on Single Needle (S-N) at 512K, but
    91% on
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:53:48.546555Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a novel sparse attention mechanism, HiLS, with strong empirical results. However, several factual claims regarding performance metrics and comparisons require precise alignment with the provided tables to avoid overstatement or ambiguity.

First, the Abstract claims HiLS extrapolates "64x the training context length with 90% retrieval accuracy." The training length is 8K, so 64x is 512K. Table `345M_main_ruler` shows HiLS achieving 100% on Single Needle (S-N) at 512K, but 91% on Multi-Key (MK-MQ) and 66% on Variable Tracking (VT). The "90%" figure appears to be an average or a specific task score (likely MK-MQ at 1M or an average across tasks at 512K) rather than a universal "retrieval accuracy" for the 64x claim. This needs clarification to ensure the reader understands which metric and context length the 90% refers to.

Second, the Introduction and Section 4.1 state HiLS achieves "better in-domain RULER performance" than full attention. Table `345M_main_ruler` shows HiLS (100/95/72) vs Full-Attn HoPE (100/98/36) at 8K. While HiLS is superior on Variable Tracking (72 vs 36), Full-Attn HoPE is superior on Multi-Key (98 vs 95). The claim of "better" is an overgeneralization; it should be qualified as "superior on Variable Tracking and comparable on other tasks" or similar.

Third, in Section 4.2, the text claims HiLS "consistently achieves lower perplexity" than full attention at 256K. Table `345M_256K_ppl` shows HiLS (7.45) is indeed lower than Full-Attn RoPE (7.49) and Full-Attn HoPE (7.53). However, at 8K, HiLS (9.08) is lower than Full-Attn RoPE (9.11) but the comparison with Full-Attn HoPE (9.20) is also lower. The claim holds, but the phrasing "consistently" might be interpreted as beating *all* full attention variants in *all* settings, which is true here, but the distinction between RoPE and HoPE baselines is crucial for the reader to understand the specific improvements.

Finally, Table `7B_longbench` lists "Olmo3-Base" with a RULER-8K score of 11.34. The text in Section 4.3 explicitly states the base model "lacks the instruction-following ability needed to answer RULER-style retrieval queries." A score of 11.34 (likely ~11% accuracy) is low but non-zero, which might be consistent with random guessing or minimal capability, but the text's strong claim of "lacks ability" contrasts with the table's inclusion of a specific score. It would be clearer to label this row as "Olmo3-Base (No CPT)" or explain that the score reflects the baseline's inability to perform the task, rather than implying it has some functional retrieval capability.

These issues are primarily matters of precision in reporting and do not invalidate the core findings, but they should be corrected to ensure the claims are strictly supported by the data presented.
