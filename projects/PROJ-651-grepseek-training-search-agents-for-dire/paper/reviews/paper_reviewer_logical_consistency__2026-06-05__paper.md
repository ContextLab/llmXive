---
action_items:
- id: 53c5f256c3b2
  severity: science
  text: Clarify the 'Direct RL is unstable' motivation by providing variance data
    or reframing to 'performance degradation without initialization'. The current
    footnote only cites VRAM/RAM OOM failures, which is a resource constraint issue
    rather than RL training instability.
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T18:53:13.491253Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

## Re-Review: Logical Consistency

### Prior Action Item Assessment

**Item `a129b2d5d37c` (Figure 1 caption):** ✓ ADDRESSED

The Figure 1 caption now correctly distinguishes between "pre-computed indices" (Left/baselines) and "without requiring an index" (Right/GrepSeek). This aligns with the DCI claim and resolves the previous logical inconsistency.

**Item `53c5f256c3b2` (Direct RL instability motivation):** ✗ NOT ADDRESSED

Section 3.1 states: "Direct RL leads to unstable behavior.\footnote{VRAM and host RAM out-of-memory failures observed.}"

This footnote conflates **resource exhaustion** (OOM) with **training instability** (policy collapse, reward variance, divergence). The original action item requested either:
1. Variance data showing reward/loss instability across runs, OR
2. Reframing to "performance degradation without initialization"

Neither is provided. The current text does not logically support why GRPO requires SFT cold-start initialization if the issue is purely memory-related (which would be solved by batch size tuning, not two-stage training).

### New Issues Identified

None. The paper does not introduce new logical inconsistencies beyond the unresolved prior item.

### Recommendation

The two-stage training justification remains logically unsupported. Either add variance metrics (e.g., reward std across random seeds in Figure 4 or Appendix), or explicitly reframe the claim to clarify that OOM failures—not policy instability—motivate the SFT initialization.
