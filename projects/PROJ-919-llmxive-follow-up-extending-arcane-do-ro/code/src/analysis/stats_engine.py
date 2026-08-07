import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.lib.config import get_config
from src.lib.utils import get_logger

logger = get_logger(__name__)

def aggregate_consistency_scores(
    results: List[Dict[str, Any]],
    judge_weight: float = 0.7,
    rule_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Combine the Judge score (T025) and rule-based score (T026) into a single
    'Consistency Score' artifact.

    Formula: Consistency_Score = (judge_weight * judge_score) + (rule_weight * rule_score)

    Args:
        results: List of result dictionaries containing 'judge_score' and 'rule_score'.
        judge_weight: Weight for the Judge model score (default 0.7).
        rule_weight: Weight for the rule-based score (default 0.3).

    Returns:
        List of result dictionaries with an added 'consistency_score' field.
    """
    aggregated = []
    for item in results:
        if 'judge_score' not in item:
            logger.warning(f"Missing 'judge_score' in result item: {item.get('id', 'unknown')}")
            judge_score = 0.0
        else:
            judge_score = float(item['judge_score'])

        if 'rule_score' not in item:
            logger.warning(f"Missing 'rule_score' in result item: {item.get('id', 'unknown')}")
            rule_score = 0.0
        else:
            rule_score = float(item['rule_score'])

        # Ensure weights sum to 1.0 for normalization, though defaults do.
        total_weight = judge_weight + rule_weight
        if total_weight == 0:
            consistency_score = 0.0
        else:
            consistency_score = (
                (judge_weight * judge_score) + (rule_weight * rule_score)
            ) / total_weight

        # Clamp to [0, 5] assuming Likert scale, or [0, 1] if normalized.
        # Based on T025 description (Likert scale), we assume 0-5 range.
        # If scores are 0-1, this still works (0-1).
        # We'll clamp to [0, 5] to be safe for Likert, but if inputs are 0-1,
        # the result will be 0-1. Let's assume the input scores are on the same scale.
        # If the scale is 0-5, we clamp to 5. If 0-1, we clamp to 1.
        # Given T025 uses "standard Likert scale" (usually 1-5 or 0-5),
        # and T026 returns a "discrete score", we assume they are comparable.
        # We will not clamp unless we know the scale. Let's assume 0-5 max.
        # Actually, let's just trust the input range and not clamp arbitrarily,
        # unless we want to enforce a specific output range.
        # For safety, let's clamp to [0, 5] as it's a common Likert max.
        # But if the scores are 0-1, this is redundant.
        # Let's assume the scores are normalized to [0, 1] for flexibility,
        # or [0, 5]. We'll leave it as is, but log if out of expected bounds.
        if consistency_score < 0 or consistency_score > 5:
            logger.warning(f"Consistency score {consistency_score} outside expected [0, 5] range.")

        item['consistency_score'] = round(consistency_score, 4)
        aggregated.append(item)

    return aggregated

def write_results_to_jsonl(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write the aggregated results to a JSONL file.

    Args:
        results: List of result dictionaries (with consistency_score).
        output_path: Path to the output file. If None, uses default from config.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        config = get_config()
        output_path = Path(config['data']['derived']) / 'results.jsonl'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    logger.info(f"Results written to {output_path}")
    return output_path

def run_aggregation_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    judge_weight: float = 0.7,
    rule_weight: float = 0.3
) -> Path:
    """
    Main pipeline function to read results, aggregate scores, and write output.

    Args:
        input_path: Path to input JSONL file (from T025/T026).
        output_path: Path to output JSONL file.
        judge_weight: Weight for Judge score.
        rule_weight: Weight for Rule score.

    Returns:
        Path to the output file.
    """
    if input_path is None:
        config = get_config()
        # Assuming T025/T026 outputs are combined or we need to merge them.
        # For this task, we assume a single input file containing both scores,
        # or we need to load and merge. Let's assume a single input file for now.
        # If separate, we would need to merge them here.
        # The task says "combine the Judge score (T025) and rule-based score (T026)".
        # We assume the input to this function already has both scores.
        # If not, we would need to load from two files and merge.
        # For simplicity, we assume one input file with both scores.
        # If the project structure has separate files, we'd need to adjust.
        # Let's assume the input is a JSONL with both scores.
        input_path = Path(config['data']['derived']) / 'probes_with_scores.jsonl'
        # If that doesn't exist, try 'results.jsonl' from previous step?
        # Let's use a generic name and let the caller specify if needed.
        # Actually, T025 and T026 produce scores. We need to combine them.
        # We'll assume the input is a file that has been prepared with both scores.
        # If not, we'll try to load from a default location.
        # For now, we'll use 'data/derived/probes_with_scores.jsonl' as a placeholder.
        # The caller should provide the correct input path.
        pass

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    logger.info(f"Loaded {len(results)} results from {input_path}")

    aggregated = aggregate_consistency_scores(
        results,
        judge_weight=judge_weight,
        rule_weight=rule_weight
    )

    output_path = write_results_to_jsonl(aggregated, output_path)

    return output_path

def main():
    """
    CLI entry point for running the aggregation pipeline.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Aggregate consistency scores from Judge and Rule-based scores.")
    parser.add_argument("--input", type=str, help="Path to input JSONL file")
    parser.add_argument("--output", type=str, help="Path to output JSONL file")
    parser.add_argument("--judge-weight", type=float, default=0.7, help="Weight for Judge score")
    parser.add_argument("--rule-weight", type=float, default=0.3, help="Weight for Rule score")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else None
    output_path = Path(args.output) if args.output else None

    output_file = run_aggregation_pipeline(
        input_path=input_path,
        output_path=output_path,
        judge_weight=args.judge_weight,
        rule_weight=args.rule_weight
    )
    print(f"Aggregation complete. Output written to: {output_file}")

if __name__ == "__main__":
    main()