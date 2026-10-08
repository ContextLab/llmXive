run_pytest called ensure_venv(project_dir), which returns a path like 'projects/PROJ-relative/code/.venv/bin/python' when project_dir is relative, then spawned the subprocess with cwd=project_dir/code. The relative executable no longer resolves from the new cwd, so subprocess raises FileNotFoundError. Fix: make the venv python absolute (os.path.abspath, preserving the venv symlink, same as run_in_venv) while keeping the pytest target path relative to the code dir.

Validation: the new regression failed against the baseline and passed with the fix; related existing tests passed in a container without credentials or network access. Independently reviewed by openai.gpt-oss-120b.

Regression: `tests/unit/test_repair_run_pytest_relative_venv.py`.

This is a repair candidate, not an automatically merged change.
