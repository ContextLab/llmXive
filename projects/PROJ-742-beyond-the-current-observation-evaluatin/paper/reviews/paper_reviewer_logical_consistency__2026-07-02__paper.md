---
action_items:
- id: c14ba0d384ab
  severity: writing
  text: The paper presents a compelling benchmark for non-Markov games, but several
    logical inconsistencies in the presentation of metrics and results undermine the
    clarity of the conclusions. First, the Game Score (GS) formula in Equation 1 is
    mathematically inconsistent with the values reported in Table 1. The formula $GS
    = \frac{SR + SR \times Eff + (1-SR) \times Explore}{2}$ produces a value between
    0 and 1. For Gemini-3.1-Pro in the 3D Maze ($13 \times 13$), the table reports
    $SR=50.0\%$, $Eff=62.5
artifact_hash: 2dace62b4db749210548d655003e141d33d2469d6916df6eba8fda5f05abc5c8
artifact_path: projects/PROJ-742-beyond-the-current-observation-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:44:31.858963Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a compelling benchmark for non-Markov games, but several logical inconsistencies in the presentation of metrics and results undermine the clarity of the conclusions.

First, the **Game Score (GS)** formula in Equation 1 is mathematically inconsistent with the values reported in Table 1. The formula $GS = \frac{SR + SR \times Eff + (1-SR) \times Explore}{2}$ produces a value between 0 and 1. For Gemini-3.1-Pro in the 3D Maze ($13 \times 13$), the table reports $SR=50.0\%$, $Eff=62.5\%$, and $Explore=36.4\%$. Plugging these into the formula: $(0.5 + 0.5 \times 0.625 + 0.5 \times 0.364) / 2 = (0.5 + 0.3125 + 0.182) / 2 = 0.49725$, which corresponds to 49.7%. While the calculation matches the reported 49.7%, the table lists "GS%" as 49.7, implying the formula output is treated as a percentage directly. However, for GPT-5.4, $SR=20.0\%$, $Eff=75.7\%$, $Explore=32.3\%$. Calculation: $(0.2 + 0.2 \times 0.757 + 0.8 \times 0.323) / 2 = (0.2 + 0.1514 + 0.2584) / 2 = 0.3049$, or 30.5%. The values match, but the text and table headers are confusing. The primary issue is the lack of explicit normalization explanation. If the inputs are percentages (e.g., 50.0), the formula must divide by 100 or the inputs must be decimals. The table presents inputs as percentages (e.g., 50.0) but the formula implicitly treats them as decimals (0.50). This is a notational inconsistency that requires clarification to ensure the metric is reproducible and logically sound.

Second, the **Memory Gap** definition in Equation 2 and its application in Table 4 are logically flawed. The text defines $S^*(m)$ as the "score with oracle hidden state injected." However, the data in Table 4 suggests $S^*(m)$ is actually the score achieved with the *external memory intervention* (the memory map or minimap), not the true oracle. For Qwen3.5-397B on Matching Pairs, the baseline is 38.3% and the intervention is 78.7%. The reported MemGap is 51.3%. If $S^*(m)$ were the true oracle (100%), the gap would be $1 - 0.383 = 61.7\%$. The value 51.3% is derived from $1 - (38.3/78.7)$. This means the "Memory Gap" is actually measuring the *relative improvement* provided by the external memory tool, not the gap between the model and the true oracle. This mislabeling invalidates the conclusion that "most errors are due to forgetting" (which requires comparing to the true oracle). If the gap is only 51.3% relative to the *intervention*, it implies the intervention itself is not perfect, and the remaining error could be due to planning or perception, not just memory. The authors must either redefine the metric to use the true oracle score or rephrase the conclusion to reflect that the metric measures the efficacy of the external memory tool.

Third, the **Duel Protocol** results in the Introduction and Table 2 are ambiguous. The Introduction states "Gemini-3.1-Pro wins all 16 head-to-head duels." Table 2 shows Gemini with 16 Wins, 0 Ties, 0 Losses. However, the table also lists GPT-5.4 with 7 Wins, 2 Ties, 7 Losses (50% win rate) and Qwen with 7 Wins, 1 Tie, 8 Losses (46.7% win rate). If Gemini played 16 games and won all, who did they play? If they played GPT and Qwen, the total games would be 16 (e.g., 8 vs GPT, 8 vs Qwen). But then GPT's 7 wins and Qwen's 7 wins must be against each other or against other models not listed. The text "wins all 16 matchups" is logically incomplete without specifying the opponent set. If the 16 games were against a single opponent, the other models' records are unexplained. If the 16 games were a round-robin, the total number of games would be higher. The logical structure of the tournament is unclear, making the claim "wins all" difficult to verify or interpret.

These issues are primarily notational and definitional but significantly impact the logical consistency of the paper's claims. The metrics are not defined in a way that matches their calculation, and the experimental setup is described ambiguously.
