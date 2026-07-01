# Reproduce & validate: COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Distillation

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/   (clone of https://github.com/titanwings/colleague-skill)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Distillation

**Abstract:** LLM agents are increasingly expected not only to complete isolated tasks, but also to carry bounded representations of human expertise, judgment, and interaction style. Building such person-grounded agents remains difficult because actionable knowledge associated with a person or role is usually embedded in heterogeneous traces rather than written as clean instructions. Existing memory and persona systems capture fragments of this evidence, while skill frameworks provide portable packaging formats; however, there is no end-to-end workflow for distilling these traces into inspectable, correctable, and agent-usable skills. We present an automated trace-to-skill distillation system for generating person-grounded AI skills via expert knowledge distillation. Given materials from a target person or role, COLLEAGUE.SKILL produces a versioned skill package with two coordinated tracks: a capability track for practices, mental models, and decision heuristics, and a bounded behavior track for communication style, interaction rules, and correction history. The package can be inspected, invoked, updated through natural-language feedback, rolled back, installed across agent hosts, and optionally prepared for controlled distribution. We describe the artifact contract, generation workflow, correction lifecycle, deployment surface, and domain presets implemented in the open-source system. At the time of writing, the public repository has approximately 18.5k GitHub stars; the gallery lists 215 skills from 165 contributors and more than 100k cumulative stars across listed skill cards. The system illustrates how person-grounded skills can be represented as portable, correctable packages rather than opaque prompts or hidden memories.

## Shipped code — file tree (`projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/`)

```
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.md
.github/ISSUE_TEMPLATE/question.md
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/ci.yml
.gitignore
CITATION.cff
CONTRIBUTING.md
INSTALL.md
LICENSE
README.md
ROADMAP.md
SKILL.md
colleague_skill.pdf
docs/PRD.md
docs/SKILL_TYPE_ABSTRACTION_DESIGN.md
docs/SKILL_TYPE_ABSTRACTION_DESIGN_ZH.md
docs/assets/wechat-group-qr-10.png
docs/assets/wechat-group-qr-11.png
docs/assets/wechat-group-qr-12.png
docs/assets/wechat-group-qr-3.png
docs/assets/wechat-group-qr-5.png
docs/assets/wechat-group-qr-6.png
docs/assets/wechat-group-qr-7.png
docs/assets/wechat-group-qr-8.png
docs/assets/wechat-group-qr-9.png
docs/lang/README_DE.md
docs/lang/README_EN.md
docs/lang/README_ES.md
docs/lang/README_JA.md
docs/lang/README_KO.md
docs/lang/README_PT.md
docs/lang/README_RU.md
docs/lang/README_ZH.md
docs/lang/ROADMAP_DE.md
docs/lang/ROADMAP_ES.md
docs/lang/ROADMAP_JA.md
docs/lang/ROADMAP_KO.md
docs/lang/ROADMAP_PT.md
docs/lang/ROADMAP_RU.md
docs/lang/ROADMAP_ZH.md
openarena-claim.txt
prompts/celebrity/budget_unfriendly/audit.md
prompts/celebrity/budget_unfriendly/persona_analyzer.md
prompts/celebrity/budget_unfriendly/persona_builder.md
prompts/celebrity/budget_unfriendly/research.md
prompts/celebrity/budget_unfriendly/synthesis.md
prompts/celebrity/budget_unfriendly/validation.md
prompts/celebrity/intake.md
prompts/celebrity/merger.md
prompts/celebrity/persona_analyzer.md
prompts/celebrity/persona_builder.md
prompts/celebrity/research.md
prompts/correction_handler.md
prompts/intake.md
prompts/merger.md
prompts/persona_analyzer.md
prompts/persona_builder.md
prompts/relationship/intake.md
prompts/relationship/merger.md
prompts/relationship/persona_analyzer.md
prompts/relationship/persona_builder.md
prompts/work_analyzer.md
prompts/work_builder.md
references/celebrity_budget_unfriendly_framework.md
references/celebrity_budget_unfriendly_template.md
requirements.txt
skills/colleague/example_jiaxiu/meta.json
skills/colleague/example_jiaxiu/persona.md
skills/colleague/example_jiaxiu/work.md
skills/colleague/example_tianyi/meta.json
skills/colleague/example_tianyi/persona.md
skills/colleague/example_tianyi/work.md
skills/colleague/example_zhangsan/meta.json
skills/colleague/example_zhangsan/persona.md
skills/colleague/example_zhangsan/work.md
tests/test_cli_lifecycle.py
tests/test_install_claude_generated_skill.py
tests/test_install_hermes_skill.py
tests/test_install_openclaw_and_codex.py
tests/test_research_tools.py
tests/test_skill_entrypoint_docs.py
tests/test_skill_writer.py
tools/dingtalk_auto_collector.py
tools/email_parser.py
tools/feishu_auto_collector.py
tools/feishu_browser.py
tools/feishu_mcp_client.py
tools/feishu_parser.py
tools/install_claude_generated_skill.py
tools/install_codex_generated_skill.py
tools/install_codex_skill.py
tools/install_generated_skill_common.py
tools/install_hermes_skill.py
tools/install_openclaw_generated_skill.py
tools/install_openclaw_skill.py
tools/research/__init__.py
tools/research/download_subtitles.sh
tools/research/merge_research.py
tools/research/quality_check.py
tools/research/srt_to_transcript.py
tools/research/transcribe_audio.py
tools/skill_presets.py
tools/skill_schema.py
tools/skill_writer.py
tools/slack_auto_collector.py
tools/version_manager.py
```

## Detected entry points

- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_cli_lifecycle.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_install_claude_generated_skill.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_install_hermes_skill.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_install_openclaw_and_codex.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_research_tools.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_skill_entrypoint_docs.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tests/test_skill_writer.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/dingtalk_auto_collector.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/email_parser.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/feishu_auto_collector.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/feishu_browser.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/feishu_mcp_client.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/feishu_parser.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/install_claude_generated_skill.py`
- `projects/PROJ-650-colleague-skill-automated-ai-skill-gener/external/colleague-skill/tools/install_codex_generated_skill.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `colleague-skill` — not re-implementing it.
