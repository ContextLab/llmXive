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
reviewed_at: '2026-06-09T21:17:49.713007Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The revision fails to address two critical overreach concerns from the prior review, leaving the paper's empirical and theoretical claims misaligned with the presented evidence.

First, the '10x speedup' claim in the Abstract and Section 4.1 remains unsubstantiated in Table 1. The table footnote defines Speedup as 'GRPO's best-Avg step / this row's first-reach step', yet the table only displays the 'peak-mean step' (e.g., `62.8@100` for Qwen3-4B). The specific first-reach step (implied to be ~20 for a 10x speedup from GRPO's 200 steps) is not reported. Without explicit reporting of the first-reach step, the 10x figure is derived from hidden data, which constitutes overreach in empirical reporting. The claim "AntiSD reaches the GRPO baseline's accuracy in 2 to 10x fewer training steps" cannot be verified by inspecting the table alone.

Second, the Abstract's claim of a 'naturally bounded advantage' is not qualified. While Section 3.2 and Lemma 1 correctly describe the advantage as asymmetrically bounded (capped on the deliberation side, unbounded on the shortcut side), the Abstract presents it as globally bounded without this nuance. This risks overstating the theoretical stability and misrepresenting the method's behavior on shortcut tokens where the advantage is linear/unbounded. Precise theoretical characterization is necessary to prevent misleading expectations about gradient stability.

No new overreach issues were identified in this revision beyond these unaddressed points. Accurate reporting of training dynamics is essential for reproducibility and trust in RL efficiency claims. These revisions are necessary to align the claims with the presented data and proofs.
