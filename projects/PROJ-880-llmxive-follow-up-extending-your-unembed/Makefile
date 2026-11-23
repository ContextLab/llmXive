.PHONY: lint format check install-dev

install-dev:
	pip install -e ".[dev]"

lint:
	flake8 code/ tests/

format:
	black code/ tests/
	isort code/ tests/

check: lint
	@echo "Linting passed."

run-benchmark:
	python code/benchmark_runner.py

run-similarity:
	python code/main.py --task similarity

run-attribution:
	python code/main.py --task attribution

run-statistical:
	python code/main.py --task statistical
