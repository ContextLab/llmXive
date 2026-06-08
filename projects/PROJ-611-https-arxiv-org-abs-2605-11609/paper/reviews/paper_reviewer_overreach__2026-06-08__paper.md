---
action_items:
- id: cc526304f582
  severity: science
  text: Report the 'first-reach step' explicitly in Table 1 or main text to substantiate
    the '10x speedup' claim, as only peak accuracy steps are currently visible (e.g.,
    Qwen3-4B peak step 100 vs. claimed 10x speedup implies step 20).
- id: 0a885d3951f1
  severity: writing
  text: Qualify the Abstract's claim of 'naturally bounded advantage' to reflect the
    asymmetric nature (bounded on deliberation side, linear/unbounded on shortcut
    side) described in Section 3.2.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T14:28:30.362583Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding efficiency and theoretical properties that require tighter alignment with the reported evidence. The primary concern lies in the Abstract and Section 4.1, where the authors claim AntiSD reaches GRPO's accuracy in "2 to 10x fewer training steps." Table 1 reports a "Speedup" metric defined as "GRPO's best-Avg step / this row's first-reach step." However, the table only explicitly displays the **peak accuracy step** (e.g., `62.8@100` for Qwen3-4B), not the **first-reach step** where AntiSD matches GRPO's peak (51.3). For Qwen3-4B, the peak step ratio is 2x (200 vs 100), yet the reported speedup is 10x. This implies AntiSD matched GRPO's accuracy at step 20, but this data point is not visible in the provided tables or figures. This constitutes an overreach in reporting; the claim cannot be verified from the presented results without the explicit "first-reach" data point.

Additionally, the Abstract states AntiSD yields a "naturally bounded advantage in one step." Section 3.2 and Lemma 4 (Appendix) clarify that the advantage $-\varphi(u_t)$ is bounded on the deliberation side (where $u_t < 0$) but grows linearly (unbounded) on the shortcut side (where $u_t > 0$). While the asymmetry is explained in the body, the Abstract's phrasing suggests a global bound, which is technically inaccurate. This simplification overstates the theoretical guarantee.

Finally, the claim that AntiSD is a "drop-in replacement... with no additional cost" (Contributions) glosses over the engineering overhead of the entropy-triggered gate and the data pipeline requirements for privileged context $c$ (sampling verified solutions per batch). While the FLOPs are comparable, the operational complexity is non-zero.

To address these overreaches, the authors should explicitly report the first-reach steps in Table 1 to validate the speedup claims and refine the Abstract's theoretical claims to match the asymmetric bounding detailed in the method section.
