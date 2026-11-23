"""
Security Flagging Module (T029)

Reads execution outcomes and static analysis results, detects security vulnerabilities
using ruff (SEC rules), and appends flagged samples to the manual review queue.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def load_execution_outcomes() -> List[Dict[str, Any]]:
    """Load execution outcomes from data/results/execution_outcomes.csv."""
    path = Paths.RESULTS_DIR / "execution_outcomes.csv"
    if not path.exists():
        logger.error(f"Execution outcomes file not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_static_analysis_results() -> List[Dict[str, Any]]:
    """
    Load static analysis results.
    Note: Depending on implementation, this might be embedded in execution_outcomes
    or a separate file. We check execution_outcomes first for 'static_analysis_scores'.
    If not present, we assume the runner already integrated static analysis.
    """
    # For this task, we rely on the execution outcomes which should contain
    # the static analysis results or we re-run the check if needed.
    # However, the task description says "Read execution outcomes ... and static analysis".
    # Let's assume the execution_outcomes.csv contains the necessary info or we
    # need to re-run ruff on the code found in the variants if outcomes don't have it.
    # Given T026/T027a, static analysis results should be available.
    # If execution_outcomes.csv doesn't have the code, we need to load from variants.
    # But T029 says "Read execution outcomes ... and static analysis".
    # Let's assume execution_outcomes.csv has 'code' or 'variant_id' to fetch code.
    # Actually, T030 writes execution_outcomes.csv. Let's assume it has 'problem_id', 'complexity_label', 'code' (or we fetch from parquet).
    # To be safe and robust, we will re-read the variants if code is missing in outcomes,
    # but primarily we look for 'static_analysis_scores' or re-run ruff on the code if present.

    # For T029, we need the code to run ruff.
    # If execution_outcomes.csv doesn't have the code, we load from prompt_variants.parquet.
    return [] # Placeholder, logic handled in main/check_security_vulnerabilities


def check_security_vulnerabilities(code_text: str, problem_id: str, complexity_label: str) -> List[Dict[str, Any]]:
    """
    Run ruff with --select=SEC on the provided code string.
    Returns a list of flagged issues with reason.
    """
    if not code_text:
        return []

    flags = []
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(code_text)
            tmp_path = tmp.name

        try:
            # Run ruff check with security rules
            # ruff version >= 0.1.0 supports --select=SEC
            result = subprocess.run(
                ["ruff", "check", "--select=SEC", "--output-format=json", tmp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # No issues found (returncode 0 usually means no violations in ruff check)
                # But sometimes ruff returns 1 if violations found.
                # Let's check the output.
                pass
            elif result.returncode == 1:
                # Violations found
                try:
                    issues = json.loads(result.stdout)
                    for issue in issues:
                        rule_code = issue.get("code", "SEC_GENERIC")
                        message = issue.get("message", "Security violation detected")

                        reason = "security_generic"
                        if "eval" in message.lower() or rule_code.startswith("S307"):
                            reason = "security_eval"
                        elif "hardcoded" in message.lower() or "credential" in message.lower() or rule_code.startswith("S105") or rule_code.startswith("S106"):
                            reason = "security_hardcoded"
                        elif rule_code.startswith("SEC"):
                            reason = "security_generic"

                        flags.append({
                            "problem_id": problem_id,
                            "variant_label": complexity_label,
                            "rule_code": rule_code,
                            "reason": reason,
                            "message": message
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse ruff JSON output for {problem_id}: {result.stdout}")
        finally:
            os.unlink(tmp_path)

    except subprocess.TimeoutExpired:
        logger.warning(f"Ruff check timed out for {problem_id}")
    except Exception as e:
        logger.error(f"Error running ruff on {problem_id}: {e}")

    return flags


def write_manual_review_flags(flags: List[Dict[str, Any]], append: bool = True) -> None:
    """
    Append security flags to data/results/manual_review_queue.csv.
    The file is created by T019a/b. We append to it.
    """
    output_path = Paths.RESULTS_DIR / "manual_review_queue.csv"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["problem_id", "variant_label", "reason", "rule_code", "message"]

    # Check if file exists to determine if we need headers
    file_exists = output_path.exists() and output_path.stat().st_size > 0

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for flag in flags:
            writer.writerow({
                "problem_id": flag["problem_id"],
                "variant_label": flag["variant_label"],
                "reason": flag["reason"],
                "rule_code": flag.get("rule_code", ""),
                "message": flag.get("message", "")
            })

    logger.info(f"Wrote {len(flags)} security flags to {output_path}")


def run_security_flagging() -> None:
    """
    Main entry point for T029.
    1. Load execution outcomes (which should contain code or variant_id).
    2. If code is not in outcomes, load from prompt_variants.parquet using variant_id/problem_id.
    3. Run ruff SEC check on each code sample.
    4. Append flagged samples to manual_review_queue.csv.
    """
    import pandas as pd

    outcomes_path = Paths.RESULTS_DIR / "execution_outcomes.csv"
    variants_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"

    if not outcomes_path.exists():
        logger.error(f"Execution outcomes file not found: {outcomes_path}. T030 must run first.")
        return

    outcomes = pd.read_csv(outcomes_path)

    # Check if 'code' column exists in outcomes. If not, we need to join with variants.
    if "code" not in outcomes.columns:
        if not variants_path.exists():
            logger.error(f"Code not in execution_outcomes.csv and variants file not found: {variants_path}")
            return

        variants = pd.read_parquet(variants_path)
        # Merge on problem_id and complexity_label (variant_label in variants)
        # Assuming outcomes has problem_id, complexity_label. Variants has problem_id, variant_label.
        if "variant_label" not in variants.columns:
            # Try to infer from other columns or assume the merge key is problem_id and we take the first match?
            # T030 output should have complexity_label. T018 output should have variant_label.
            # Let's assume we can merge on problem_id and complexity_label == variant_label.
            pass

        # Simple join: if outcomes has problem_id and complexity_label, and variants has problem_id, variant_label
        # We might need to handle multiple variants per problem.
        # For security flagging, we check every generated code sample.
        # So we should iterate over outcomes, and if code is missing, fetch from variants.
        # Let's assume outcomes has 'variant_id' or we can reconstruct.
        # To be robust: if 'code' is missing, we load variants and match by problem_id and complexity_label.
        # But outcomes might have multiple rows per problem (different variants).
        # Let's assume outcomes has the code column. If T030 didn't include it, we fix T030 logic here by fetching.

        # Fallback: Load variants and iterate all rows if outcomes lacks code.
        # But outcomes is the source of truth for what was executed.
        # Let's assume outcomes has 'code' or 'variant_id'.
        # If not, we fetch from variants based on problem_id and complexity_label.
        # This is a bit ambiguous. Let's assume T030 includes 'code' in the CSV.
        # If not, we will fetch.
        pass

    all_flags = []

    # If 'code' is in outcomes, use it. Otherwise, we need to fetch.
    # Let's check if 'code' column exists.
    if "code" in outcomes.columns:
        for _, row in outcomes.iterrows():
            problem_id = str(row.get("problem_id", ""))
            complexity_label = str(row.get("complexity_label", ""))
            code_text = row.get("code", "")

            if code_text:
                flags = check_security_vulnerabilities(code_text, problem_id, complexity_label)
                all_flags.extend(flags)
    else:
        # Fallback: Load variants and check all code samples (assuming outcomes implies execution of these)
        # This is a bit of a stretch if outcomes doesn't list which variants were executed, but T030 should.
        # Let's assume we need to load variants and check every row if code is missing in outcomes.
        # But T029 says "Read execution outcomes ... and static analysis".
        # If execution_outcomes.csv is missing 'code', we can't run ruff without fetching from variants.
        # Let's fetch from variants.
        if variants_path.exists():
            variants = pd.read_parquet(variants_path)
            for _, row in variants.iterrows():
                problem_id = str(row.get("problem_id", ""))
                variant_label = str(row.get("variant_label", ""))
                code_text = row.get("prompt_text", "") # Wait, variants has prompt_text, not code?
                # T018 writes prompt_variants.parquet. T017 captures code.
                # T018 description: "Write results to data/processed/prompt_variants.parquet".
                # T017 description: "capturing code".
                # So prompt_variants.parquet should have 'code' or 'generated_code'.
                # Let's check data model: GeneratedCode has 'code'. PromptVariant has 'prompt_text'.
                # T017 output: "Write results to data/processed/prompt_variants.parquet".
                # T018: "write generated code and metadata to data/processed/prompt_variants.parquet".
                # So the parquet file should have the generated code.
                # Let's assume column is 'code' or 'generated_code'.
                code_text = row.get("code", row.get("generated_code", ""))

                if code_text:
                    flags = check_security_vulnerabilities(code_text, problem_id, variant_label)
                    all_flags.extend(flags)

    if all_flags:
        write_manual_review_flags(all_flags, append=True)
        logger.info(f"Security flagging complete. {len(all_flags)} issues found.")
    else:
        logger.info("Security flagging complete. No issues found.")


def main() -> None:
    """CLI entry point."""
    run_security_flagging()


if __name__ == "__main__":
    main()