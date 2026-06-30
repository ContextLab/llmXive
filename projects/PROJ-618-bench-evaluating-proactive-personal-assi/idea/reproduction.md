# Reproduce & validate: $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/   (clone of https://github.com/Simplified-Reasoning/Pi-Bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** $π$-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows

**Abstract:** The rise of personal assistant agents, e.g., OpenClaw, highlights the growing potential of large language models to support users across everyday life and work. A core challenge in these settings is proactive assistance, since users often begin with underspecified requests and leave important needs, constraints, or preferences unstated. However, existing benchmarks rarely evaluate whether agents can identify and act on such hidden intents before they are explicitly stated, especially in sustained multi-turn interactions where user needs emerge gradually. To address this gap, we introduce $π$-Bench, a benchmark for proactive assistance comprising 100 multi-turn tasks across 5 domain-specific user personas. By incorporating hidden user intents, inter-task dependencies, and cross-session continuity, $π$-Bench evaluates agents' ability to anticipate and address user needs over extended interactions, jointly measuring proactivity and task completion in long-horizon trajectories that better reflect real-world use. Experiments show (1) proactive assistance remains challenging, (2) a clear distinction between task completion and proactivity, and (3) the value of prior interaction for proactive intent resolution in later tasks.

## Shipped code — file tree (`projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/`)

```
.github/workflows/deploy-pages.yml
.gitignore
LICENSE
README.md
assets/image2.png
assets/pi-bench-overview.png
config/bench/evaluation/trace_history.yaml
config/models/MiniMax-M2.5.yaml
config/models/MiniMax-M2.7.yaml
config/models/claude-haiku-4-5-20251001.yaml
config/models/claude-opus-4-6.yaml
config/models/claude-opus-4-7.yaml
config/models/claude-sonnet-4-6.yaml
config/models/deepseek-v3.2.yaml
config/models/deepseek-v4-flash.yaml
config/models/deepseek-v4-pro.yaml
config/models/doubao-seed-2-0-pro-260215.yaml
config/models/example.full.yaml
config/models/gemini-3-flash-preview.yaml
config/models/gemini-3.1-pro-preview.yaml
config/models/glm-5.1.yaml
config/models/glm-5.yaml
config/models/gpt-5.4.yaml
config/models/gpt-5.5.yaml
config/models/kimi-k2.5.yaml
config/models/kimi-k2.6.yaml
config/models/qwen3.6-plus.yaml
data/Financier/episode.yaml
data/Financier/profile.yaml
data/Financier/scripts/Financier_task_002_simple_note.py
data/Financier/scripts/Financier_task_005_gmail.py
data/Financier/scripts/Financier_task_008_todoist.py
data/Financier/scripts/Financier_task_011_phone.py
data/Financier/scripts/Financier_task_015_amazon.py
data/Financier/scripts/Financier_task_017.py
data/Financier/scripts/Financier_task_019.py
data/Financier/scripts/Financier_task_020.py
data/Financier/skills/1pagecreditanalysis-4cnmarket-1.0.0/SKILL.md
data/Financier/skills/1pagecreditanalysis-4cnmarket-1.0.0/_meta.json
data/Financier/skills/financial-analysis-1.0.0/README.md
data/Financier/skills/financial-analysis-1.0.0/SKILL.md
data/Financier/skills/financial-analysis-1.0.0/_meta.json
data/Financier/skills/financial-analysis-1.0.0/manifest.json
data/Financier/skills/financial-analysis-1.0.0/optimized_main.py
data/Financier/skills/financial-analysis-1.0.0/optimized_risk_parity_skill.py
data/Financier/skills/financial-analysis-1.0.0/优化使用指南.md
data/Financier/skills/financial-analysis-1.0.0/优化总结.md
data/Financier/skills/financial-analysis-1.0.0/最终优化总结.md
data/Financier/skills/ifind-repilot-finance-data-search-1.0.0/SKILL.md
data/Financier/skills/ifind-repilot-finance-data-search-1.0.0/_meta.json
data/Financier/skills/ifind-repilot-finance-data-search-1.0.0/scripts/fetch_data.py
data/Financier/skills/json-translator-1.0.0/README.md
data/Financier/skills/json-translator-1.0.0/SKILL.md
data/Financier/skills/json-translator-1.0.0/_meta.json
data/Financier/skills/json-translator-1.0.0/scripts/translate_json.py
data/Financier/skills/jy-customer-requirement-analysis-1.0.1/README.md
data/Financier/skills/jy-customer-requirement-analysis-1.0.1/SKILL.md
data/Financier/skills/jy-customer-requirement-analysis-1.0.1/_meta.json
data/Financier/skills/jy-customer-requirement-analysis-1.0.1/references/output-examples.md
data/Financier/skills/python-data-analysis-1.0.0/README.md
data/Financier/skills/python-data-analysis-1.0.0/SKILL.md
data/Financier/skills/python-data-analysis-1.0.0/_meta.json
data/Financier/tasks/Financier_task_001/pd_validation_priority_draft.md
data/Financier/tasks/Financier_task_001/task.yaml
data/Financier/tasks/Financier_task_002/task.yaml
data/Financier/tasks/Financier_task_003/Model_Performance_Report.md
data/Financier/tasks/Financier_task_003/task.yaml
data/Financier/tasks/Financier_task_004/task.yaml
data/Financier/tasks/Financier_task_004/var_backtesting_priority_draft.md
data/Financier/tasks/Financier_task_005/task.yaml
data/Financier/tasks/Financier_task_006/Model_Development_Report.md
data/Financier/tasks/Financier_task_006/task.yaml
data/Financier/tasks/Financier_task_007/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip
data/Financier/tasks/Financier_task_007/task.yaml
data/Financier/tasks/Financier_task_008/task.yaml
data/Financier/tasks/Financier_task_009/task.yaml
data/Financier/tasks/Financier_task_009/w1594.pdf
data/Financier/tasks/Financier_task_009/w4871.pdf
data/Financier/tasks/Financier_task_010/german.data
data/Financier/tasks/Financier_task_010/german_credit_schema.md
data/Financier/tasks/Financier_task_010/german_credit_split.csv
data/Financier/tasks/Financier_task_010/pd_scorecard_model_spec.yaml
data/Financier/tasks/Financier_task_010/pd_validation_report_draft.md
data/Financier/tasks/Financier_task_010/task.yaml
data/Financier/tasks/Financier_task_011/task.yaml
data/Financier/tasks/Financier_task_012/complaints.csv.zip
data/Financier/tasks/Financier_task_012/task.yaml
data/Financier/tasks/Financier_task_013/task.yaml
data/Financier/tasks/Financier_task_014/SP500.csv
data/Financier/tasks/Financier_task_014/task.yaml
data/Financier/tasks/Financier_task_014/var_backtest_spec.yaml
data/Financier/tasks/Financier_task_014/var_validation_report_draft.md
data/Financier/tasks/Financier_task_015/task.yaml
data/Financier/tasks/Financier_task_016/task.yaml
data/Financier/tasks/Financier_task_017/task.yaml
data/Financier/tasks/Financier_task_018/task.yaml
data/Financier/tasks/Financier_task_019/task.yaml
data/Financier/tasks/Financier_task_020/task.yaml
data/Financier/tools.yaml
data/law_trainee/episode.yaml
data/law_trainee/profile.yaml
data/law_trainee/scripts/law_trainee_task_008_5.py
data/law_trainee/scripts/law_trainee_task_012_5.py
data/law_trainee/scripts/law_trainee_task_014_5.py
data/law_trainee/scripts/law_trainee_task_018_5.py
data/law_trainee/scripts/law_trainee_task_020_5.py
data/law_trainee/skills/china-tax-law-1.0.0/SKILL.md
data/law_trainee/skills/china-tax-law-1.0.0/_meta.json
data/law_trainee/skills/china-tax-law-1.0.0/references/compliance-checklist.md
data/law_trainee/skills/china-tax-law-1.0.0/references/tax-rates.md
data/law_trainee/skills/corporate-lawyer-1.0.0/_meta.json
data/law_trainee/skills/corporate-lawyer-1.0.0/readme.md
data/law_trainee/skills/corporate-lawyer-1.0.0/skill.md
data/law_trainee/skills/data-analysis-1.0.2/SKILL.md
data/law_trainee/skills/data-analysis-1.0.2/_meta.json
data/law_trainee/skills/data-analysis-1.0.2/chart-selection.md
data/law_trainee/skills/data-analysis-1.0.2/decision-briefs.md
data/law_trainee/skills/data-analysis-1.0.2/metric-contracts.md
data/law_trainee/skills/data-analysis-1.0.2/pitfalls.md
data/law_trainee/skills/data-analysis-1.0.2/techniques.md
data/law_trainee/skills/defense-lawyer-1.0.0/_meta.json
data/law_trainee/skills/defense-lawyer-1.0.0/readme.md
data/law_trainee/skills/defense-lawyer-1.0.0/skill.md
data/law_trainee/skills/godfery-news-aggregator-1.0.0/SKILL.md
data/law_trainee/skills/godfery-news-aggregator-1.0.0/_meta.json
data/law_trainee/skills/jargon-translator-1.0.3/SKILL.md
data/law_trainee/skills/jargon-translator-1.0.3/_meta.json
data/law_trainee/skills/jargon-translator-1.0.3/references/glossary.md
data/law_trainee/skills/law-exam-trainer-1.0.0/SKILL.md
data/law_trainee/skills/law-exam-trainer-1.0.0/_meta.json
data/law_trainee/skills/law-exam-trainer-1.0.0/references/resources.md
data/law_trainee/tasks/law_trainee_task_001/task.yaml
data/law_trainee/tasks/law_trainee_task_002/task.yaml
data/law_trainee/tasks/law_trainee_task_003/Compliance_Report_Draft.md
data/law_trainee/tasks/law_trainee_task_003/task.yaml
data/law_trainee/tasks/law_trainee_task_004/task.yaml
data/law_trainee/tasks/law_trainee_task_005/task.yaml
data/law_trainee/tasks/law_trainee_task_006/task.yaml
data/law_trainee/tasks/law_trainee_task_007/2021-2025Judgment_statistics.md
data/law_trainee/tasks/law_trainee_task_007/Case_Summary.txt
data/law_trainee/tasks/law_trainee_task_007/task.yaml
data/law_trainee/tasks/law_trainee_task_008/task.yaml
data/law_trainee/tasks/law_trainee_task_009/task.yaml
data/law_trainee/tasks/law_trainee_task_010/task.yaml
data/law_trainee/tasks/law_trainee_task_011/Loans.md
data/law_trainee/tasks/law_trainee_task_011/task.yaml
data/law_trainee/tasks/law_trainee_task_012/task.yaml
data/law_trainee/tasks/law_trainee_task_013/Complaint_Facts.md
data/law_trainee/tasks/law_trainee_task_013/task.yaml
data/law_trainee/tasks/law_trainee_task_014/task.yaml
data/law_trainee/tasks/law_trainee_task_015/task.yaml
data/law_trainee/tasks/law_trainee_task_016/checklist_project.md
data/law_trainee/tasks/law_trainee_task_016/project_online.md
data/law_trainee/tasks/law_trainee_task_016/task.yaml
data/law_trainee/tasks/law_trainee_task_017/task.yaml
data/law_trainee/tasks/law_trainee_task_018/task.yaml
data/law_trainee/tasks/law_trainee_task_019/Defense_Case_Summary.md
data/law_trainee/tasks/law_trainee_task_019/task.yaml
data/law_trainee/tasks/law_trainee_task_020/task.yaml
data/law_trainee/tools.yaml
data/marketer/episode.yaml
data/marketer/profile.yaml
data/marketer/scripts/marketer_task_004.py
data/marketer/scripts/marketer_task_009.py
data/marketer/scripts/marketer_task_010.py
data/marketer/scripts/marketer_task_014.py
data/marketer/scripts/marketer_task_020.py
data/marketer/tasks/marketer_task_001/task.yaml
data/marketer/tasks/marketer_task_002/task.yaml
data/marketer/tasks/marketer_task_003/task.yaml
data/marketer/tasks/marketer_task_004/task.yaml
data/marketer/tasks/marketer_task_005/task.yaml
data/marketer/tasks/marketer_task_006/task.yaml
data/marketer/tasks/marketer_task_007/task.yaml
data/marketer/tasks/marketer_task_008/task.yaml
data/marketer/tasks/marketer_task_009/task.yaml
data/marketer/tasks/marketer_task_010/task.yaml
data/marketer/tasks/marketer_task_011/task.yaml
data/marketer/tasks/marketer_task_012/Spine_Steward.md
data/marketer/tasks/marketer_task_012/task.yaml
data/marketer/tasks/marketer_task_013/task.yaml
data/marketer/tasks/marketer_task_014/task.yaml
data/marketer/tasks/marketer_task_015/task.yaml
data/marketer/tasks/marketer_task_016/Meeting_Minutes_0409.md
data/marketer/tasks/marketer_task_016/task.yaml
data/marketer/tasks/marketer_task_017/task.yaml
data/marketer/tasks/marketer_task_018/task.yaml
data/marketer/tasks/marketer_task_019/task.yaml
data/marketer/tasks/marketer_task_020/task.yaml
data/marketer/tools.yaml
data/pharmacist/episode.yaml
data/pharmacist/profile.yaml
data/pharmacist/scripts/pharmacist_task_001_gmail.py
data/pharmacist/scripts/pharmacist_task_003_amazon.py
data/pharmacist/scripts/pharmacist_task_009_todoist.py
data/pharmacist/scripts/pharmacist_task_017_splitwise.py
data/pharmacist/scripts/pharmacist_task_020_file_system.py
data/pharmacist/skills/local-file-grounding/SKILL.md
data/pharmacist/skills/local-web-search/SKILL.md
data/pharmacist/skills/medical-research-literature-reader-pro/SKILL.md
… (truncated)
```

## Detected entry points

- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/main.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/scripts/test_server.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/scripts/trace_viewer.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/docker_launcher.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_custom_provider.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_docker_launcher.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_llm_client.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_model_config.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_nanobot_heartbeat.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_nanobot_memory.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/tests/test_runner_channel.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/channels/base.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/channels/discord.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/channels/mock.py`
- `projects/PROJ-618-bench-evaluating-proactive-personal-assi/external/Pi-Bench/src/channels/reset_policy.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Pi-Bench` — not re-implementing it.
