# API Documentation

## code/analyzer.py
- `check_normality(data)`: Performs Shapiro-Wilk test on coverage differences.
- `run_statistical_test(data)`: Runs paired t-test or Wilcoxon signed-rank based on normality.
- `calculate_effect_size(data)`: Calculates Cohen's d or Rank-biserial correlation.
- `run_power_analysis(data)`: Calculates achieved power.
- `calculate_confidence_intervals(data)`: Computes confidence intervals for mean ratio.
- `main()`: Entry point for analysis.

## code/config.py
- `init_runtime_tracker()`: Initializes runtime tracking.
- `check_runtime_limit()`: Checks if runtime limit exceeded.
- `get_sample_limit()`: Returns configured sample limit.
- `get_timeout_compile()`: Returns compilation timeout.
- `get_timeout_exec()`: Returns execution timeout.
- `get_timeout_inference()`: Returns inference timeout.
- `get_runtime_limit()`: Returns runtime limit.
- `get_model_path()`: Returns model path.
- `get_data_dir()`: Returns data directory.
- `get_output_dir()`: Returns output directory.
- `get_logs_dir()`: Returns logs directory.
- `ensure_directories()`: Ensures required directories exist.

## code/data_loader.py
- `DataFetchError`: Exception for data fetch errors.
- `MemoryExceededError`: Exception for memory limit exceeded.
- `load_state(project_id)`: Loads project state.
- `save_state(project_id, state)`: Saves project state.
- `record_checksum(project_id, artifact_name, checksum)`: Records checksum.
- `compute_sha256(file_path)`: Computes SHA-256 hash.
- `fetch_defects4j_data(streaming)`: Fetches Defects4J dataset.
- `load_defects4j_data()`: Loads and yields defects4j data.
- `verify_data_integrity(project_id, artifact_name, file_path)`: Verifies data integrity.
- `extract_changed_lines(project_id, dataset_stream)`: Extracts changed lines from diff.
- `validate_manual_baseline_existence(bug_id)`: Validates manual baseline existence.
- `map_issue_description(item)`: Extracts and validates issue description.
- `extract_bug_fix_description(item)`: Formats bug description as prompt.
- `log_fallback_prompt_usage(bug_id, reason)`: Logs fallback prompt usage.
- `filter_pairable_samples(df, exclusion_log_path)`: Filters pairable samples, excluding deferred/timeout.
- `ensure_data_loaded_and_integrity_recorded(project_id)`: Ensures data integrity.
- `main()`: Entry point for data loader.

## code/llm_generator.py
- `MemoryExceededError`: Exception for memory limit exceeded.
- `load_model()`: Loads the LLM model.
- `generate_from_prompt(prompt)`: Generates code from prompt.
- `generate_test_code(prompt)`: Generates test code.
- `validate_syntax_java(code)`: Validates Java syntax.
- `main()`: Entry point for LLM generator.

## code/main.py
- `RuntimeLimitExceeded`: Exception for runtime limit exceeded.
- `SampleLimitExceeded`: Exception for sample limit exceeded.
- `check_sample_limit(count)`: Checks sample limit.
- `run_pipeline()`: Runs the full pipeline.
- `main()`: Entry point for main script.

## code/power_sensitivity_analysis.py
- `calculate_power_for_sample_sizes(data)`: Calculates power for different sample sizes.
- `generate_power_sensitivity_plot(data)`: Generates power sensitivity plot.
- `update_report_with_plot_reference(report_path, plot_path)`: Updates report with plot reference.
- `main()`: Entry point for power sensitivity analysis.

## code/report_generator.py
- `generate_markdown_report(data)`: Generates markdown report.
- `generate_final_report(data)`: Generates final report.

## code/test_executor.py
- `CompilationFailedError`: Exception for compilation failure.
- `ExecutionError`: Exception for execution failure.
- `ExecutionResult`: Data class for execution results.
- `enforce_test_timeout(cmd)`: Enforces test timeout.
- `retry_compile(cmd)`: Retries compilation.
- `compile_test(cmd)`: Compiles test.
- `extract_compilation_error(log)`: Extracts compilation error.
- `update_csv_for_failed_test(df, row, error)`: Updates CSV for failed test.
- `parse_jacoco_xml(xml_path)`: Parses JaCoCo XML.
- `run_with_jacoco(cmd)`: Runs test with JaCoCo.
- `calculate_coverage_ratio(coverage_data, changed_lines)`: Calculates coverage ratio.
- `count_assertions(code)`: Counts assertions.
- `calculate_assertion_density(code)`: Calculates assertion density.
- `collect_coverage_records(records)`: Collects coverage records.
- `write_coverage_csv(df, path)`: Writes coverage CSV.
- `main()`: Entry point for test executor.

## code/utils/retry.py
- `retry_with_backoff(func, args, kwargs, retries)`: Retries function with backoff.
- `execute_with_retry(func, args, kwargs, retries)`: Executes function with retry.

## code/validate_schemas.py
- `load_schema(schema_path)`: Loads schema.
- `validate_artifact(artifact, schema)`: Validates artifact.
- `validate_all_artifacts()`: Validates all artifacts.
- `main()`: Entry point for schema validation.
