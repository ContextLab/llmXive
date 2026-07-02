---
action_items:
- id: 65bdc99cb4a1
  severity: science
  text: Section 3.3 claims the mask for chunk k is derived from chunk k-1. Logically,
    an edit moving in chunk k cannot be masked correctly using k-1's data. Explain
    how the mask for k is determined causally without ground truth.
- id: 2869f011c1aa
  severity: writing
  text: Section 4.1 states a fixed 70% pruning ratio. This contradicts 'strict preservation'
    if the edit region varies. Clarify if 70% is an average or if the logic holds
    for large edits.
- id: f8e2382886e6
  severity: science
  text: Table 2 shows Dynamic Degree drops to 0.017 with FFN caching. The text blames
    'blurring,' but near-zero DD implies static video. Explain if the metric collapse
    is due to motion freezing.
artifact_hash: ad807d68c3634218d8a37b306582366b9db8e405a9dcf34fb28dd7323fcbdd9e
artifact_path: projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:44:36.278461Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent high-level argument for streaming video editing but contains logical gaps in the causal mechanisms of its core contributions.

First, the **AR-oriented Mask Cache** (Section 3.3) suffers from a causality error. The mask $M^k$ for the current chunk $k$ is derived from the difference between the edited and source latents of the *previous* chunk ($k-1$). The text then uses this mask to route computation for chunk $k$. This logic fails if the editing region moves or changes between chunks (e.g., a moving object being edited). The state of chunk $k-1$ does not causally determine the editing activity in chunk $k$. Without a mechanism to predict or detect the edit location in $k$ before processing it, the mask will be misaligned, leading to artifacts or missed edits. The paper must explain how the mask for $k$ is generated without access to the ground truth of $k$.

Second, the **pruning logic** in Section 4.1 is contradictory. The authors state the threshold $\tau$ is set to "explicitly prune 70% of the redundant spatial tokens." This implies a fixed ratio regardless of content. However, the method claims "strict background preservation." If an edit covers a large portion of the frame, a fixed 70% prune ratio might force the system to treat active editing regions as static background, violating the preservation claim. The logic of a fixed ratio is incompatible with variable edit sizes unless "70%" refers to a dataset average, which is not clarified.

Finally, the **ablation results** in Table 2 (Section 4.3) show Dynamic Degree (DD) collapsing to 0.017 when caching FFN layers. The authors attribute this to "high-frequency spatial information" loss (blurring). However, DD measures motion consistency; a value near zero suggests the video became static or motion was lost entirely, not just blurred. The causal link between FFN caching and the specific metric collapse (motion freezing vs. blurring) is not logically explained.
