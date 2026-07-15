"""
Save per-trace rule sets and compressibility scores to disk.

This module implements the final step of User Story 2 (T026), taking the
in-memory results from the rule induction pipeline and persisting them to:
- data/processed/per_trace_scores.csv
- data/processed/rules/{trace_id}_rules.json
"""
import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import Config
from models.rule_induction import PerTraceRuleInducer, process_all_traces_for_induction

def save_per_trace_scores(
    scores: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save a list of per-trace compressibility scores to a CSV file.

    Args:
        scores: List of dictionaries containing trace_id, compressibility_score,
                rule_set_size, trace_length, and fidelity.
        output_path: Path where the CSV file will be written.
    """
    if not scores:
        raise ValueError("No scores provided to save.")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "trace_id",
        "compressibility_score",
        "rule_set_size",
        "trace_length",
        "fidelity",
        "entropy",
        "tool_repetition_frequency",
        "argument_variance"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in scores:
            # Filter to only include expected keys to avoid CSV errors
            safe_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(safe_row)

    print(f"Saved {len(scores)} scores to {output_path}")

def save_rule_sets(
    rules_data: List[Dict[str, Any]],
    output_dir: Path
) -> None:
    """
    Save individual rule sets to JSON files.

    Args:
        rules_data: List of dictionaries containing trace_id and 'rules' (the rule set).
        output_dir: Directory where individual JSON files will be written.
    """
    if not rules_data:
        raise ValueError("No rule data provided to save.")

    output_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for item in rules_data:
        trace_id = item.get("trace_id")
        if not trace_id or "rules" not in item:
            continue

        file_path = output_dir / f"{trace_id}_rules.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=2, default=str)
        saved_count += 1

    print(f"Saved {saved_count} rule sets to {output_dir}")

def main() -> None:
    """
    Main entry point for T026: Save per-trace rule sets and compressibility scores.

    This function:
    1. Loads traces and runs per-trace rule induction (re-using T023 logic).
    2. Calculates compressibility scores (re-using T024 logic).
    3. Saves scores to data/processed/per_trace_scores.csv.
    4. Saves rule sets to data/processed/rules/.
    """
    config = Config()
    traces_dir = config.traces_dir
    output_scores_path = config.processed_dir / "per_trace_scores.csv"
    output_rules_dir = config.processed_dir / "rules"

    print(f"Starting T026: Saving results to {output_scores_path} and {output_rules_dir}")

    # Run the induction pipeline to get results
    # This re-uses the logic from T023/T024 to ensure consistency
    results = process_all_traces_for_induction(traces_dir, config)

    if not results:
        print("No results generated. Check if traces exist in data/raw/")
        return

    # Separate scores and rule sets for saving
    scores_list = []
    rules_list = []

    for res in results:
        # Construct score row
        score_row = {
            "trace_id": res.get("trace_id"),
            "compressibility_score": res.get("compressibility_score"),
            "rule_set_size": res.get("rule_set_size"),
            "trace_length": res.get("trace_length"),
            "fidelity": res.get("fidelity"),
            "entropy": res.get("entropy"),
            "tool_repetition_frequency": res.get("tool_repetition_frequency"),
            "argument_variance": res.get("argument_variance")
        }
        scores_list.append(score_row)

        # Construct rule set entry
        rules_entry = {
            "trace_id": res.get("trace_id"),
            "rules": res.get("rules", []),
            "model_params": res.get("model_params", {})
        }
        rules_list.append(rules_entry)

    # Save artifacts
    save_per_trace_scores(scores_list, output_scores_path)
    save_rule_sets(rules_list, output_rules_dir)

    print("T026 completed successfully.")

if __name__ == "__main__":
    main()
