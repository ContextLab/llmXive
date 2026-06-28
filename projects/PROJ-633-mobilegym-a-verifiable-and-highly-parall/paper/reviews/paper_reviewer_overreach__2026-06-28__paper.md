---
action_items:
- id: aca854dd336b
  severity: science
  text: The Sim-to-Real transfer claim (95.1% retained gain) is based on a filtered
    subset (59 tasks) that excludes 8 tasks deemed 'unreproducible' on real devices.
    This selection bias risks overstating the generalizability of the transfer rate.
    Please clarify the subset selection criteria and discuss how excluding unreproducible
    tasks affects the validity of the 95.1% figure as a benchmark-wide metric.
- id: b344cdcf2446
  severity: writing
  text: The Abstract claims MobileGym enables capabilities 'previously out of reach'.
    AndroidWorld and similar emulators do support online RL, albeit at higher cost.
    This phrasing overstates the novelty. Consider revising to 'more scalable' or
    'cost-effective' to accurately reflect the contribution relative to existing emulator-based
    RL.
- id: b4021bbc39b9
  severity: writing
  text: The paper claims to cover 'everyday mobile use' with 12 everyday apps, but
    admits the backend logic is synthetic (Section 2.1). This limitation should be
    more prominently stated in the Abstract and Introduction to avoid overclaiming
    the realism of the 'everyday' claim, as synthetic backends may not capture real-world
    logic drift.
artifact_hash: f4cd930b7a9ee408f16628fa968792c28c81dba6a7a2d564441d29e182ecd8b7
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T06:28:31.252348Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling platform for mobile GUI agent research, but several claims overreach the evidence provided, particularly regarding the Sim-to-Real transfer validation and the novelty of the RL capabilities.

**Sim-to-Real Transfer Overreach (§5.2):**
The headline claim of "95.1% retained gain" is derived from a 59-task subset of the 256-task test set. Crucially, this subset was constructed by selecting tasks where the simulation showed a training signal (Uplift, Stable-pass, Mid) and explicitly excluding 8 tasks that could not be reproduced on real devices. This selection process introduces a bias: the transfer rate is measured on tasks where the simulation *already worked well enough* to show a signal, while tasks that failed in simulation (Stable-fail) were largely excluded (only 15 sampled as negative control). Presenting 95.1% as a general Sim-to-Real metric overstates the platform's ability to transfer training gains across the *entire* benchmark. The text should clarify that this figure applies to the *signal-bucket subset* and discuss the implications of excluding unreproducible tasks on the generalizability of the claim.

**"Previously Out of Reach" Claim (Abstract, §1):**
The Abstract states MobileGym enables capabilities "previously out of reach for everyday apps." However, emulator-based environments like AndroidWorld *do* support online RL (e.g., UI-Venus-1.5 used AndroidWorld for RL), just at a higher resource cost. The novelty is the *scalability* and *cost-efficiency*, not the fundamental capability. This phrasing overclaims the novelty relative to existing work. Revising to "more scalable" or "cost-effective" would be more accurate.

**"Everyday Apps" Realism (§2.1, §5):**
The paper claims to simulate "everyday mobile use" with 12 everyday apps, but explicitly states in §2.1 that it "does not aim to reproduce real everyday app backends." While the UI is realistic, the backend logic (e.g., search ranking, payment processing) is synthetic. This limitation is critical for "everyday" claims, as agents may learn patterns specific to the synthetic logic that do not transfer to real apps. This should be more prominently stated in the Abstract and Introduction to temper expectations about the realism of the "everyday" claim.

**Deterministic Judging (§2.2):**
The claim of "deterministic outcome signals" relies on the completeness of the JSON state model. If the state model omits relevant side effects (e.g., notifications not captured in JSON), the judging is not truly deterministic for all real-world scenarios. While the "Unexpected Side Effects" metric helps, the paper should acknowledge that determinism is bounded by the state model's coverage.

These issues do not invalidate the core contribution but require tempering of claims to align with the evidence.
