# Reproduce & validate: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/   (clone of https://github.com/tomerkeren42/TASTE-task-synthesis-from-tool-sequence-evolution)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

**Abstract:** As agent capabilities advance, existing benchmarks, such as $τ^2$-Bench, are becoming increasingly saturated. Yet constructing new benchmark tasks remains complex, costly, and labor-intensive. Moreover, the standard approach, in which scenarios are first written in natural language and then mapped to tool sequences, captures only a narrow subset of the tool-use patterns agents exercise. In this paper, we address these problems by reversing the task construction process. We propose TASTE: Task Synthesis from Tool Sequence Evolution, an automatic method that generates challenging tasks with broader tool-use coverage. TASTE utilizes an Adaptive Contrastive $n$-gram model trained on LLM-judged validity signals. This enables sampling valid tool sequences that cover a vast range of tool combinations. TASTE then selects representative sequences from the pool via clustering, instantiates them into complete benchmark tasks, and refines them through iterative difficulty evolution. Using TASTE, we construct $τ^c$-Bench, a challenging extension of the three domains of $τ^2$-Bench. We evaluate $11$ agent/user LLM pairs and find that models nearly saturating $τ^2$-Bench suffer severe performance drops on our tasks (e.g., Gemini-3-Flash falls from $0.82\!-\!0.94$ to $0.28\!-\!0.61$). Beyond increasing difficulty, our generated tasks more than double the number of unique tool combinations agents must execute. Our results suggest high scores on existing benchmarks often reflect saturation rather than robust task-solving ability. By automating the generation of difficult, high-coverage benchmarks, TASTE enables continuous, scalable evaluation of future agents.

## Shipped code — file tree (`projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/`)

```
.gitignore
LICENSE
README.md
artifacts/domains/airline/domain.json
artifacts/domains/airline/policy.md
artifacts/domains/airline/tasks.json
artifacts/domains/airline/tool_spec.json
artifacts/domains/retail/domain.json
artifacts/domains/retail/policy.md
artifacts/domains/retail/tasks.json
artifacts/domains/retail/tool_spec.json
artifacts/domains/telecom/domain.json
artifacts/domains/telecom/policy.md
artifacts/domains/telecom/tasks.json
artifacts/domains/telecom/tool_spec.json
artifacts/ngram/checkpoints/airline/ngram_airline_n3_t3000_final.json
artifacts/ngram/checkpoints/airline/ngram_airline_n3_t800.json
artifacts/ngram/checkpoints/airline/post_seed.json
artifacts/ngram/checkpoints/airline/pre_seed.json
artifacts/ngram/checkpoints/airline_no_neg/ngram_airline_n3_t400.json
artifacts/ngram/checkpoints/airline_no_neg/ngram_airline_n3_t800.json
artifacts/ngram/checkpoints/airline_no_neg/post_seed.json
artifacts/ngram/checkpoints/airline_no_neg/pre_seed.json
artifacts/ngram/checkpoints/retail/ngram_retail_n3_t3000_final.json
artifacts/ngram/checkpoints/retail/ngram_retail_n3_t800.json
artifacts/ngram/checkpoints/retail/post_seed.json
artifacts/ngram/checkpoints/retail/pre_seed.json
artifacts/ngram/checkpoints/telecom/ngram_telecom_n3_t3000_final.json
artifacts/ngram/checkpoints/telecom/ngram_telecom_n3_t800.json
artifacts/ngram/checkpoints/telecom/post_seed.json
artifacts/ngram/checkpoints/telecom/pre_seed.json
artifacts/prompts/stage2/validate_action_sequence.txt
artifacts/prompts/stage3/adversarial_scenario.txt
artifacts/prompts/stage3/adversarial_scenario_lite.txt
artifacts/prompts/stage3/adversarial_strategy.txt
artifacts/prompts/stage3/create_user_task.txt
artifacts/prompts/stage3/db_trap_construction.txt
artifacts/prompts/stage3/generate_db_initialization.txt
artifacts/prompts/stage3/partial_coverage_gt_agent.txt
artifacts/prompts/stage3/patch_db.txt
artifacts/prompts/stage3/patch_task.txt
artifacts/prompts/stage3/task_coherence_review.txt
artifacts/prompts/stage3/telecom/align_scenario_with_end_state.txt
artifacts/prompts/stage3/telecom/generate_env_assertions.txt
artifacts/task_sets/airline_gemini_3_flash/tasks.json
artifacts/task_sets/airline_gemini_3_pro/tasks.json
artifacts/task_sets/airline_gpt_5_2/tasks.json
artifacts/task_sets/retail_base_tasks/tasks.json
artifacts/task_sets/retail_gemini_3_flash/tasks.json
artifacts/task_sets/telecom_base_tasks/tasks.json
artifacts/task_sets/telecom_gemini_3_flash/tasks.json
artifacts/validated_clusters/airline_medoids.json
artifacts/validated_clusters/airline_medoids_no_wed.json
artifacts/validated_clusters/retail_medoids.json
artifacts/validated_clusters/telecom_medoids.json
artifacts/validated_clusters/telecom_medoids_write_only.json
pyproject.toml
src/__init__.py
src/common/__init__.py
src/common/call_to_llm.py
src/common/domain_config.py
src/common/domain_utils.py
src/common/domain_validators/__init__.py
src/common/domain_validators/airline.py
src/common/domain_validators/base.py
src/common/domain_validators/retail.py
src/common/domain_validators/telecom.py
src/common/flight_ambiguity_checker.py
src/common/llm_response_parser.py
src/common/prompt_manager.py
src/common/sampler/__init__.py
src/common/sampler/action_sequence_clusterer.py
src/common/sampler/action_sequence_ngram_sampler.py
src/common/sampler/adaptive_ngram_model.py
src/common/sampler/checkpointable.py
src/common/sampler/length_distribution.py
src/common/sampler/sequence_metrics.py
src/common/tool_spec_retriever.py
src/stage1_ngram/__init__.py
src/stage1_ngram/initialize_ngram_model.py
src/stage2_cluster/__init__.py
src/stage2_cluster/action_sequence_validator.py
src/stage2_cluster/cluster_and_validate.py
src/stage2_cluster/medoid_validation.py
src/stage3_tasks/__init__.py
src/stage3_tasks/action_sequence_policy.py
src/stage3_tasks/adversarial_evolver.py
src/stage3_tasks/database_state_manager.py
src/stage3_tasks/env_assertion_synthesizer.py
src/stage3_tasks/evolve_tasks.py
src/stage3_tasks/generate_tasks.py
src/stage3_tasks/partial_coverage_gt_agent.py
src/stage3_tasks/scenario_aligner.py
src/stage3_tasks/task_builder.py
src/stage3_tasks/task_generation.py
src/stage3_tasks/task_set.py
src/stage3_tasks/task_validator.py
src/stage3_tasks/task_validator_logging.py
src/stage3_tasks/validation_with_retry.py
```

## Detected entry points

- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/call_to_llm.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/domain_config.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/domain_utils.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/flight_ambiguity_checker.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/llm_response_parser.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/prompt_manager.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/common/tool_spec_retriever.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage1_ngram/initialize_ngram_model.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage2_cluster/action_sequence_validator.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage2_cluster/cluster_and_validate.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage2_cluster/medoid_validation.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage3_tasks/action_sequence_policy.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage3_tasks/adversarial_evolver.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage3_tasks/database_state_manager.py`
- `projects/PROJ-653-https-arxiv-org-abs-2605-28556/external/TASTE-task-synthesis-from-tool-sequence-evolution/src/stage3_tasks/env_assertion_synthesizer.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `TASTE-task-synthesis-from-tool-sequence-evolution` — not re-implementing it.
