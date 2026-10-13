"""
Executes ruff linting on the entire project and writes the output
to ``data/logs/ruff.log``. The log is expected to contain the line
``✔ No errors`` which is used by the verification step of T001.
"""
import subprocess

from llmxive_toolkit import paths


def main() -> None:
    # Ensure the logs directory exists
    log_path = paths.data("logs", "ruff.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Run ruff and capture its output
    with open(log_path, "w", encoding="utf-8") as f:
        subprocess.run(
            ["ruff", "check", "."],
            stdout=f,
            stderr=subprocess.STDOUT,
            check=False,
        )

if __name__ == "__main__":
    main()
