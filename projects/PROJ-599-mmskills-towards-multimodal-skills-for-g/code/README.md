# MMSkills Adaptation: Static Skill Structure Validator

## Original Paper Goal
The MMSkills paper proposes a framework for **multimodal procedural knowledge**, where agents use "skill packages" containing text, state cards, and keyframes to solve complex GUI/Game tasks. The core quantitative result involves running an agent (e.g., `MMSkillAgent` or `GeneralSkillAgent`) in an environment (OSWorld) to measure **success rate improvements** over a baseline when using these skills.

## Adaptation Strategy (CPU-Safe, Scaled-Down)
The original evaluation requires:
1.  A full virtualized desktop environment (OSWorld) with running VMs.
2.  A multimodal LLM API (OpenAI/Gemini) for the agent loop.
3.  Thousands of steps to gather success rates.

**This adaptation cannot run the full agent loop on a CPU CI runner** (no VMs, no API keys). Instead, it reproduces the **structural integrity and coverage analysis** of the MMSkills framework, which is a prerequisite for the quantitative results.

**What we measure:**
1.  **Skill Schema Compliance:** We parse the `skills_library` (provided in the repo) to verify that every skill adheres to the MMSkills schema (presence of `plan.json`, `state_cards.json`, `runtime_state_cards.json`, and image references).
2.  **Visual Grounding Audit:** We verify that referenced images exist and are valid files (simulating the "visual grounding" step).
3.  **State Transition Consistency:** We check if the `runtime_state_cards` logically follow the `plan.json` steps (a static analysis of the procedural knowledge).

**Approximations:**
-   **Replaced:** Dynamic Agent Execution → Static Schema & Content Validation.
-   **Replaced:** Success Rate Metric → "Schema Validity Rate" & "Image Coverage Rate".
-   **Replaced:** GPU/LLM Inference → Pure Python JSON/OS file parsing (CPU only).

**Result:** A real report on the quality and completeness of the MMSkills library provided in the repository, written to `data/` and `figures/`.
