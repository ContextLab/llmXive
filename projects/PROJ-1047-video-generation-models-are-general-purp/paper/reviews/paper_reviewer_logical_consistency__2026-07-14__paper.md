---
action_items:
- id: ca6acf267386
  severity: science
  text: Section 4.3 claims joint training 'severely degrades' 3D keypoint estimation,
    but Table 1 shows Generalist-L (71.8 MPJPE) matches Specialist-L (71.8) and beats
    Specialist-S (72.6). The text contradicts the table data; clarify the baseline
    or correct the claim.
- id: 6e55a52d6617
  severity: writing
  text: "The '7x to 500x' data efficiency claim in Abstract/Intro lacks a clear source\
    \ for the 7x lower bound in Table 2, where the video ratio is ~371x and frame\
    \ ratio ~487x vs VGGT-\u03A9. Specify which comparison yields the 7x figure or\
    \ adjust the range to match the presented data."
artifact_hash: bd9b8338c9ef684f69ecde6cb02952f1373be2d283e651b95c30cd6af9990c46
artifact_path: projects/PROJ-1047-video-generation-models-are-general-purp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T04:04:40.301310Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent argument that video generation pre-training serves as a superior foundation for general-purpose vision tasks. The methodology logically follows from the premise that generative models encode rich spatiotemporal priors. However, there are specific inconsistencies between the textual claims and the reported data that undermine the internal consistency of the results section.

First, in Section 4.3 (Ablation Studies), the authors state: "Most notably, we empirically observe that joint training severely degrades 3D human keypoint estimation." This conclusion is drawn to explain why the generalist model might struggle with sparse tasks. However, Table 1 presents data that contradicts this claim. The "Ours - Generalist - L" model achieves an MPJPE of 71.8 on the EMDB dataset. This is identical to the "Ours - Specialist - L" (71.8) and significantly better than the "Ours - Specialist - S" (72.6) and the specialist baseline "Genmo" (73.0). If the generalist matches the best specialist and outperforms the smaller specialist, the claim of "severe degradation" is not supported by the provided numbers. The text suggests a failure mode that the table does not show. This requires either a correction of the text to reflect that performance is maintained (not degraded) or a re-evaluation of the data if the table values are incorrect.

Second, the claim of "7× to 500× less training data" appears in the Abstract, Introduction, and Section 4.3. Table 2 provides the specific numbers for the comparison: VGGT-Ω uses ~3M videos (~600M frames), while the proposed method uses 8.08K videos (1.23M frames). The ratio of frames is approximately 487x, and the ratio of videos is approximately 371x. While these fall within the 7x-500x range, the lower bound of "7x" is not accounted for in this specific comparison (the minimum ratio here is ~371x). The "7x" figure likely refers to a comparison with a different model (perhaps D4RT, which uses ~1M videos) or a specific subset of data not explicitly detailed in the table's summary row. Without clarifying which specific comparison yields the 7x figure, the range "7x to 500x" appears to be an aggregation of disparate comparisons that obscures the actual data efficiency relative to the specific baselines listed in the table. The text should specify the baseline for the lower bound or adjust the range to match the data presented in Table 2.

These issues do not invalidate the core hypothesis but represent a break in the logical chain between the evidence presented (tables) and the conclusions drawn (text).
