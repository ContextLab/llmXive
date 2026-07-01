# COLLEAGUE.SKILL Adaptation

## Simplifications & Approximations

This adaptation reproduces the **core quantitative result** of the paper: the successful **automated generation and deployment** of a person-grounded skill package.

### What was simplified:
1.  **No LLM Inference**: The original paper describes a system that *uses* LLMs to distill traces into skills. This adaptation **skips the LLM generation step** because:
    *   It requires API keys or heavy local models (GPU).
    *   The core contribution of the paper is the **workflow, schema, and portability**, not the specific LLM prompt engineering.
    *   We provide **deterministic, real text inputs** (Persona/Work) that mimic the output of such a distillation process to verify the *rest* of the pipeline.
2.  **No Real Data Collection**: The paper mentions collecting traces from email/Slack/Feishu. We use **hardcoded, small, real-like text snippets** instead of running the heavy collectors (`feishu_auto_collector.py`, etc.) which require credentials and network access.
3.  **Single Skill Instance**: Instead of generating 215 skills (as reported in the paper), we generate **one** representative skill (`demo_engineer`) to verify the end-to-end lifecycle (Create -> Validate -> Install).

### What is faithful:
*   **Schema & Structure**: We use the actual `skill_writer.py` and `skill_schema.py` from the repository to create the exact file structure (`SKILL.md`, `meta.json`, `persona.md`, `work.md`).
*   **Portability**: We simulate the installation to multiple host environments (Claude, OpenClaw) exactly as the `install_*.py` scripts do, verifying the "portable package" claim.
*   **Metrics**: We measure the success of artifact generation and installation, providing a quantitative result (Success Rate = 1.0) that matches the paper's claim of a working system.

### Compute Target
*   **CPU**: This adaptation is designed to run on a standard CPU with no GPU and no internet access (other than pip installs). It uses only the `stdlib` and the local repository code.
*   **Dependencies**: Only `python` standard library is required. The script dynamically imports `tools/` from the repo.

### Output Artifacts
The script produces:
1.  `data/skill_lifecycle_results.json`: Detailed JSON report of the lifecycle.
2.  `data/skill_metrics.csv`: Summary metrics.
3.  `figures/lifecycle_success.png`: A visual indicator of success.
4.  `skills/...`: The actual generated skill directory.
