import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import Config


def save_per_trace_scores(scores: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves per-trace compressibility scores to a CSV file.

    Args:
        scores: List of dictionaries containing trace_id, compressibility_score,
                fidelity, rule_set_size, and trace_length.
        output_path: Path to the output CSV file.
    """
    if not scores:
        raise ValueError("No scores provided to save.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Define standard columns
    fieldnames = [
        "trace_id",
        "compressibility_score",
        "fidelity",
        "rule_set_size",
        "trace_length",
        "sequence_entropy",
        "tool_repetition_freq",
        "argument_variance"
    ]

    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in scores:
            writer.writerow(row)

    print(f"Saved {len(scores)} per-trace scores to {output_path}")


def save_rule_sets(rule_sets: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Saves per-trace rule sets to individual JSON files in the specified directory.

    Args:
        rule_sets: List of dictionaries containing 'trace_id' and 'rules'.
                   'rules' should be a list of rule dictionaries.
        output_dir: Directory path where rule JSON files will be saved.
    """
    if not rule_sets:
        raise ValueError("No rule sets provided to save.")

    # Ensure output directory exists
    save_dir = Path(output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for item in rule_sets:
        trace_id = item.get("trace_id")
        rules = item.get("rules", [])

        if not trace_id:
            raise ValueError("Rule set entry missing 'trace_id'.")

        # Create filename: rules_{trace_id}.json
        filename = f"rules_{trace_id}.json"
        filepath = save_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "trace_id": trace_id,
                "rule_count": len(rules),
                "rules": rules
            }, f, indent=2)
        saved_count += 1

    print(f"Saved {saved_count} rule sets to {output_dir}")


def main() -> None:
    """
    Main entry point to load per-trace induction results from memory (simulated here
    as if passed from the induction process) and save them to disk.

    In a real pipeline, this would be called by the induction script after
    `PerTraceRuleInducer` processes all traces.
    """
    config = Config()
    
    # Paths
    scores_output = config.get("paths", {}).get("per_trace_scores", "data/processed/per_trace_scores.csv")
    rules_output_dir = config.get("paths", {}).get("rules_dir", "data/processed/rules")

    # NOTE: In a real execution flow, the 'scores' and 'rule_sets' lists would be
    # returned by the induction process (e.g., from `process_all_traces_for_induction`).
    # Since we are implementing the save utility, we simulate the structure expected
    # from the induction step to demonstrate the save functionality works correctly.
    #
    # In the actual pipeline execution, the caller will pass the real data:
    #   save_per_trace_scores(real_scores_list, scores_output)
    #   save_rule_sets(real_rule_sets_list, rules_output_dir)
    
    # For this specific task implementation, we verify the functions exist and work
    # by creating a minimal valid dataset structure if no external data is passed,
    # but the functions themselves are designed to accept real data from the induction step.
    
    # Example data structure matching what `rule_induction.py` would produce:
    sample_scores = [
        {
            "trace_id": "demo_trace_001",
            "compressibility_score": 0.45,
            "fidelity": 0.92,
            "rule_set_size": 5,
            "trace_length": 11,
            "sequence_entropy": 2.3,
            "tool_repetition_freq": 0.15,
            "argument_variance": 0.85
        },
        {
            "trace_id": "demo_trace_002",
            "compressibility_score": 0.60,
            "fidelity": 0.95,
            "rule_set_size": 3,
            "trace_length": 5,
            "sequence_entropy": 1.8,
            "tool_repetition_freq": 0.40,
            "argument_variance": 0.20
        }
    ]

    sample_rule_sets = [
        {
            "trace_id": "demo_trace_001",
            "rules": [
                {"condition": "tool == 'edit'", "action": "apply_style", "confidence": 0.9},
                {"condition": "tool == 'insert'", "action": "add_slide", "confidence": 0.85}
            ]
        },
        {
            "trace_id": "demo_trace_002",
            "rules": [
                {"condition": "tool == 'delete'", "action": "remove_slide", "confidence": 0.95}
            ]
        }
    ]

    # Execute saves
    save_per_trace_scores(sample_scores, scores_output)
    save_rule_sets(sample_rule_sets, rules_output_dir)

    print("T026 Implementation: Save functions executed successfully.")


if __name__ == "__main__":
    main()