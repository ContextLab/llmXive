---
action_items:
- id: d0d142384201
  severity: writing
  text: The claim that MIGA achieves 'state-of-the-art' performance (Conclusion) is
    overreaching. Table 1 in the Appendix shows Infinity-RoPE (a train-based method)
    scoring 98.08 O.S. vs. MIGA's 97.82. The paper must explicitly qualify 'SOTA'
    to 'train-free SOTA' or acknowledge the gap with trained methods.
- id: 479562f16f3a
  severity: writing
  text: The assertion that MIGA 'naturally supports infinite frame generation' with
    'constant memory' (Abstract/Conclusion) is technically imprecise. Table 'memory_analysis'
    shows memory increasing from 9929 MiB to 9985 MiB as frames grow from 500 to 2000.
    While the growth is small, it is not constant. The text should reflect 'bounded'
    or 'sub-linear' growth rather than 'constant'.
- id: 09d10b9b318e
  severity: writing
  text: The paper claims DCE improves consistency by '4.7% and 2.0%' (Methods) based
    on VBench scores. However, the ablation table (Tab:ab_1) shows the jump from FIFO
    (95.02) to MIGA (97.82) is 2.8 points, not 4.7. The 4.7% figure likely refers
    to a specific metric (S.C.) or a different baseline comparison not clearly defined
    in the text, creating ambiguity about the magnitude of the claimed improvement.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:34:29.930905Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that slightly overreach the provided evidence or require more precise qualification.

First, the Conclusion states that MIGA yields "state-of-the-art performance." While MIGA leads among *train-free* methods, the Appendix (Tab:comparison_sf_methods) explicitly compares MIGA against train-based methods like Infinity-RoPE, which achieves an Overall Score (O.S.) of 98.08 compared to MIGA's 97.82 (VideoCrafter2-based). Claiming "state-of-the-art" without the "train-free" qualifier is an overstatement given the existence of higher-performing trained baselines in the same table. The authors should refine this to "state-of-the-art among train-free methods" to maintain scientific rigor.

Second, the Abstract and Conclusion assert that the method preserves "constant memory usage" and "naturally supports infinite frame generation." While the memory overhead is minimal, Table 'memory_analysis' in the Appendix demonstrates a measurable increase in peak memory consumption (from 9929 MiB to 9985 MiB) as the frame count scales from 500 to 2000. This contradicts the strict definition of "constant" memory. The claim should be tempered to reflect "bounded" or "negligible" memory growth rather than strictly constant, as the data shows a positive correlation between length and memory usage.

Finally, the Methods section claims DCE improves subject and background consistency by "4.7% and 2.0%." The ablation study in Table 'tab:ab_1' shows the total improvement from the FIFO baseline (95.02 O.S.) to the full MIGA (97.82 O.S.) is 2.8 points. The specific 4.7% figure appears to correspond to the Subject Consistency (S.C.) metric jump (92.92 to 97.66 is ~4.74 points), but the text presents these as general consistency improvements without specifying the metric. This lack of specificity risks misleading the reader about the magnitude of improvement across all consistency dimensions. Clarifying that these percentages apply specifically to Subject Consistency (and potentially Background Consistency if the math holds for that specific metric) is necessary.
