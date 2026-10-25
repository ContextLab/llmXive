"""
Prompt engineering module for the evaluation pipeline.

Reads the commit messages parquet produced by ``code.data_acquisition``,
derives a natural‑language prompt for each PR, and classifies the
complexity of the change.

Output parquet (``data/processed/intent_prompts.parquet``) contains:
  - ``pr_id``               : identifier of the pull request
  - ``prompt``              : NL prompt suitable for code generation
  - ``complexity_indicator``: one of ``simple``, ``moderate``, ``complex``
"""

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _determine_complexity(commit_message: str) -> str:
    """
    Very simple heuristic to map a commit message to a complexity level.

    Rules (order matters):
      * if the message contains any of the *complex* keywords → ``complex``
      * elif it contains any of the *moderate* keywords → ``moderate``
      * else → ``simple``

    The keyword lists are deliberately short but cover typical
    verbs found in real commit messages.
    """
    if not isinstance(commit_message, str):
        return "simple"

    msg = commit_message.lower()

    complex_keywords = [
        "rewrite", "redesign", "overhaul", "migrate", "performance",
        "refactor", "optimize", "scalability", "architecture", "restructure"
    ]
    moderate_keywords = [
        "add", "implement", "feature", "create", "introduce",
        "support", "extend", "upgrade", "document", "test", "bugfix",
        "fix", "improve"
    ]

    if any(word in msg for word in complex_keywords):
        return "complex"
    if any(word in msg for word in moderate_keywords):
        return "moderate"
    return "simple"


def _build_prompt(commit_message: str, complexity: str) -> str:
    """
    Construct a natural‑language prompt for code generation from a
    commit message and a complexity label.

    Example output:

    > Write a **moderate‑complexity** change that implements:
    > “Add user authentication with JWT tokens”.
    """
    # Strip surrounding whitespace and newlines
    cleaned_msg = " ".join(commit_message.strip().split())
    return (
        f"Write a {complexity}-complexity change that implements:\n"
        f"\"{cleaned_msg}\""
    )


def main() -> None:
    """
    Entry point for the prompt‑engineering stage.

    1. Load ``commit_messages.parquet`` (produced by the data‑acquisition step).
    2. For each row:
         * infer a ``complexity_indicator`` using a simple heuristic,
         * build a NL ``prompt`` string.
    3. Write the resulting DataFrame to ``intent_prompts.parquet``.
    """
    input_path = paths.data("raw", "commit_messages.parquet")
    output_path = paths.data("processed", "intent_prompts.parquet")

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the raw commit messages
    try:
        df_commits = pd.read_parquet(input_path)
    except Exception as exc:
        log.error(f"Failed to read commit messages from {input_path}: {exc}")
        raise

    # Expect at least a ``pr_id`` and ``commit_message`` column
    required_cols = {"pr_id", "commit_message"}
    missing = required_cols - set(df_commits.columns)
    if missing:
        log.error(f"Missing required columns in commit messages parquet: {missing}")
        raise ValueError(f"Missing columns: {missing}")

    # Build the new DataFrame
    records = []
    for _, row in df_commits.iterrows():
        pr_id = row["pr_id"]
        commit_msg = row["commit_message"]

        complexity = _determine_complexity(commit_msg)
        prompt = _build_prompt(commit_msg, complexity)

        records.append(
            {
                "pr_id": pr_id,
                "prompt": prompt,
                "complexity_indicator": complexity,
            }
        )

    df_out = pd.DataFrame(records)

    # Write the parquet file
    try:
        df_out.to_parquet(output_path, index=False)
        log.info(f"Intent prompts written to {output_path} (rows={len(df_out)})")
    except Exception as exc:
        log.error(f"Failed to write intent prompts parquet: {exc}")
        raise


if __name__ == "__main__":
    main()
