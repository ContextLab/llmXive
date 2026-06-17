---
action_items: []
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:27:08.177852Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.5
verdict: accept
---

The manuscript presents a thorough empirical evaluation of MiniMax Sparse Attention (MSA), a block‑wise sparse attention mechanism built on Grouped‑Query Attention (GQA). The authors substantiate their central claims with a substantial body of quantitative evidence across multiple dimensions:

1. **Sample Size and Training Budget** – Both the from‑scratch (MSA‑PT) and continued‑pretraining (MSA‑CPT) experiments are conducted on a 109 B‑parameter Mixture‑of‑Experts model trained for a total of 3 T tokens (Sections 4.1–4.2). This scale is comparable to state‑of‑the‑art LLM pretraining regimes and provides a solid foundation for assessing long‑context behavior.

2. **Controls and Baselines** – The paper consistently compares MSA against a full‑attention GQA baseline under identical model architectures, token budgets, and optimizer settings (Table 1, Fig. 6). This direct pairing isolates the effect of the sparse attention modification.

3. **Replication through Ablations** – A comprehensive suite of ablations (Appendix A and B) probes each design choice: gradient sources for the Index Branch, KL‑gradient detachment, indexer warm‑up, block size, forced sink/local selection, and the presence of the Index Branch value head. Each ablation reports performance on a representative subset of benchmarks, enabling readers to gauge the robustness of the final configuration.

4. **Effect Size and Statistical Signals** – The reported performance deltas are modest but consistent. For example, on the RULER‑8K retrieval benchmark MSA‑PT improves the score from 79.8 (Full) to 84.2 (+4.4), while on most language‑modeling perplexity tasks the differences are within ±0.01 (Table 1). The size of these effects is appropriate given the drastic reduction in compute (28.4× FLOP savings at 1 M context) and aligns with prior work on sparse attention.

5. **Risk of Over‑fitting / p‑hacking** – The authors evaluate on a wide spectrum of tasks (text, math, code, image, video, long‑context retrieval, and agent‑oriented perplexity). The diversity of benchmarks mitigates cherry‑picking risk. Moreover, the same hyper‑parameters are used across all evaluations, and the ablations are performed on a separate pilot 10 B model (Appendix A.1), further reducing the chance of over‑fitting to a single test set.

6. **Training Stability Evidence** – Figures 6 and 7 display LM loss and gradient‑norm trajectories for both full‑attention and MSA training, showing near‑identical curves and no divergence spikes. This directly supports the claim that the KL‑detach and warm‑up mechanisms yield stable optimization.

7. **Efficiency Measurements** – The paper supplies both theoretical FLOP reductions (Section 4.5, Eq. 9) and empirical wall‑clock speedups for prefill (14.2×) and decoding (7.6×) on H800 GPUs (Fig. 8). The runtime gains are corroborated by a dedicated top‑k kernel benchmark (Table 2) and a detailed kernel design (Section 5).

Overall, the experimental methodology is sound, the controls are appropriate, and the effect sizes are reported transparently. The evidence convincingly supports the authors’ claims that MSA maintains model quality while delivering substantial compute savings. No fatal methodological flaws are detected. Consequently, I recommend acceptance.
