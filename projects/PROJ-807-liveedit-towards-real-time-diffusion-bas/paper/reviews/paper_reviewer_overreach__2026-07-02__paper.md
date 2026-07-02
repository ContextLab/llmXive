---
action_items:
- id: ff3498042b0d
  severity: writing
  text: The claim of 'zero visual degradation' in unedited regions (Sec 3.3, Sec 5)
    is an absolute over-claim. Table 3 shows a drop in Aesthetic Quality (0.584 to
    0.581) and Imaging Quality (0.720 to 0.708) when the cache is enabled. The text
    must be revised to reflect that degradation is 'negligible' rather than non-existent.
- id: ef03210f6f2e
  severity: writing
  text: The assertion that the method 'strictly outperforms' bidirectional offline
    models in Text Alignment (Sec 4.3) is not fully supported by the data. While the
    final score (0.270) beats InsV2V (0.259), the claim implies universal superiority
    over the class, which is not demonstrated against all baselines. The phrasing
    should be qualified to 'outperforms specific strong baselines' or 'achieves competitive
    SOTA'.
- id: e01e1887bfaa
  severity: writing
  text: The claim that the AR-oriented Mask Cache 'guarantees' absolute visual consistency
    (Sec 3.3) is an over-interpretation of the $L_2$ distance heuristic. The method
    relies on a threshold $\tau$ to prune 70% of tokens; if the threshold is not perfectly
    tuned for every scene, artifacts could occur. The word 'guarantees' should be
    replaced with 'significantly preserves' to align with the empirical nature of
    the evaluation.
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:45:59.292510Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the performance and capabilities of the LiveEdit framework that exceed the evidence provided in the text and tables.

First, the authors repeatedly use absolute language such as "zero visual degradation" (Abstract, Sec 3.3, Sec 5) and "strictly guaranteeing absolute visual consistency" (Sec 3.3). This is an over-claim. The quantitative results in Table 3 (Ablation Study) explicitly show that enabling the cache results in a decrease in Aesthetic Quality (from 0.584 to 0.581) and Imaging Quality (from 0.720 to 0.708) compared to the "W/o Cache" baseline. While these drops may be small, they are non-zero. Claiming "zero degradation" contradicts the provided data. The text should be softened to reflect that the degradation is minimal or imperceptible to human evaluators, rather than mathematically non-existent.

Second, the claim in Section 4.3 that the unidirectional streaming approach "strictly outperforms" bidirectional offline architectures in Text Alignment is slightly misleading. While the final model (0.270) does outperform InsV2V (0.259), the "W/o Cache" version (0.265) also outperforms it, but the margin is narrow. More importantly, the claim implies a general superiority over the entire class of offline models, yet the table shows the method is competitive but not universally dominant across all metrics against all baselines (e.g., StreamDiffusionV2 has a higher Motion Smoothness score). The phrasing should be more precise, such as "achieves state-of-the-art performance among streaming methods and competitive results against offline baselines."

Finally, the assertion that the Mask Cache mechanism "guarantees" strict background preservation (Sec 3.3) relies on a heuristic threshold $\tau$ to prune 70% of tokens. While the ablation study supports the efficacy of this approach, the use of "guarantee" suggests a theoretical bound or perfect execution that is not demonstrated. The method is empirical; if the $L_2$ distance threshold fails to capture subtle changes in a specific scene, artifacts could theoretically occur. The language should be adjusted to "effectively preserves" or "maintains high-fidelity consistency" to accurately reflect the empirical nature of the results.
