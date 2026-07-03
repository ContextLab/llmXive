---
action_items:
- id: 892e09192805
  severity: writing
  text: Task 107 (073-force-quit-frozen-doc) and Task 107 (106-create-charles-ssh-user)
    involve creating system users and modifying OS configurations. The paper must
    explicitly state that these tasks are executed in isolated, disposable containers
    (Harbor framework) and that no persistent system changes or real user accounts
    are created on host machines to prevent privilege escalation risks.
- id: d4f46eade1e9
  severity: writing
  text: Several tasks (e.g., 027-add-dota-dlc-cart, 037-electric-cars-under-50k) involve
    interacting with live commercial websites (Steam, Cars.com). The manuscript should
    clarify the protocol for rate limiting, bot detection avoidance, and ensuring
    that automated agents do not violate Terms of Service or incur unintended financial
    charges during benchmark execution.
- id: 802cdd406093
  severity: writing
  text: Task 044 (044-etsy-saved-passwords) and Task 099 (098-extract-email-doc-image)
    involve accessing sensitive user data (passwords, emails). The authors must confirm
    that all test data used in the benchmark is synthetic or anonymized, and that
    the evaluation protocol explicitly forbids agents from exfiltrating or logging
    real credentials.
artifact_hash: 24b3876d2f6d382fabc2cec7e848c6b9800288aa6424ce399e516dbcde8b3ba2
artifact_path: projects/PROJ-805-tua-bench-a-benchmark-for-general-purpos/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:50:46.291285Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper introduces TUA-Bench, a benchmark for terminal-use agents, which inherently carries safety and dual-use risks due to the nature of terminal interactions (system administration, file manipulation, and web automation). While the authors mention using isolated Linux containers (Harbor framework) in Section 3.1, the safety review requires more explicit mitigation strategies for specific high-risk tasks.

First, regarding system administration tasks, Task 107 (106-create-charles-ssh-user) explicitly instructs the agent to create a new system user with a password and home directory. While likely intended for a sandbox, the manuscript lacks a clear statement confirming that these operations are strictly confined to ephemeral containers and that no persistent changes are made to the host infrastructure. Without this explicit confirmation, there is a risk that the benchmark could be misused to test privilege escalation or persistence mechanisms on real systems. The authors should add a sentence in Section 3.1 or the Limitations section clarifying the isolation guarantees and the disposal of container states post-execution.

Second, the benchmark includes tasks interacting with live commercial websites (e.g., Task 027 adding items to a Steam cart, Task 037 searching for cars). Automated agents interacting with live sites pose risks of violating Terms of Service, triggering bot detection, or inadvertently causing financial transactions if the agent logic fails. The paper should describe the safeguards in place, such as rate limiting, the use of test accounts with zero balance, or the restriction of agents to "read-only" or "cart-add-only" modes that do not proceed to checkout.

Finally, tasks involving sensitive data handling (e.g., Task 044 navigating to saved passwords, Task 099 extracting images from email attachments) require assurance that the dataset does not contain real PII. The authors should explicitly state that all input artifacts (emails, password stores) are synthetic or fully anonymized to prevent privacy violations during the benchmarking process. Given the "English-only" limitation mentioned in Section 6, there is also a potential bias in the safety evaluation, as agents might behave differently on non-English interfaces, but this is a secondary concern compared to the direct system and privacy risks.
