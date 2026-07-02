---
action_items:
- id: 16ef6aa092ac
  severity: writing
  text: The logical consistency of the proposed methodology contains several gaps
    where the stated mechanisms do not fully support the claimed outcomes. First,
    in Section 3.3 (Training-Free KV Cache Rescheduling), the logic regarding Reference
    KV Disentangle is circular and potentially contradictory. The authors state that
    to maintain coherence during garment switching, they replace the static reference
    KV ($KV^{\text{src}}$) with a KV derived from the last generated frame ($KV^{\text{k}}$).
    They claim
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:57:55.582180Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The logical consistency of the proposed methodology contains several gaps where the stated mechanisms do not fully support the claimed outcomes.

First, in **Section 3.3 (Training-Free KV Cache Rescheduling)**, the logic regarding **Reference KV Disentangle** is circular and potentially contradictory. The authors state that to maintain coherence during garment switching, they replace the static reference KV ($KV^{\text{src}}$) with a KV derived from the last generated frame ($KV^{\text{k}}$). They claim this new KV corresponds to "four decoded frames" (a chunk) while the original corresponds to a "single-frame." The logical flaw here is that the "I2V property" (Image-to-Video) relies on the model conditioning on a *static* reference image to anchor the identity and pose. By replacing the static reference with a dynamic, generated frame, the model effectively loses its anchor to the original character identity. The paper asserts this preserves coherence but fails to explain logically how the model avoids drifting from the original character's identity when the conditioning signal itself becomes a moving target derived from the generation process.

Second, in **Section 3.2 (Streaming Distillation)**, the causal claim linking **Gradient-Reweighted DMD** to **motion coherence** is unsupported. The authors observe that naive DMD leads to "distorted human motions" and attribute this to error accumulation. They propose reweighting gradients based on an "aesthetic reward model" ($\mathcal{R}$). However, the logical bridge is missing: an aesthetic score typically evaluates static visual quality (texture, lighting, composition), not temporal consistency or physical plausibility of motion. There is no stated mechanism explaining why a frame with low aesthetic quality would necessarily be the one suffering from motion drift, or why penalizing the gradient based on aesthetics would specifically correct motion artifacts rather than just sharpening the image. The assumption that "low aesthetic score = motion error" is an unproven premise.

Third, in **Section 3.3**, the **Historical KV Withdraw** mechanism presents a paradox. The authors correctly identify that the model attends more to historical KV than conditional KV, causing the old garment to persist. Their solution is to withdraw the historical KV. Logically, if the model relies on historical KV for motion coherence (as the attention visualization suggests), removing it should result in a loss of temporal continuity (e.g., the character "teleporting" or losing motion flow) at the switch point. The paper claims this enables "seamless garment transitions while preserving coherent human motion" but does not provide a logical explanation for how motion coherence is maintained in the absence of the historical context that the model was shown to depend on. The mechanism appears to trade one form of incoherence (garment persistence) for another (motion discontinuity) without a clear resolution.
