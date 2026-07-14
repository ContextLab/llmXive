"""
Ranking metrics for SWE-Explore benchmark.

Calculates the position of the first relevant line retrieved by an agent.
Handles censored data (where the relevant line is never retrieved) by
applying a penalty of N+1, where N is the total number of lines in the file.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_config_summary


def load_ground_truth_lines(ground_truth_path: Path) -> Dict[str, Set[int]]:
    """
    Load ground truth line numbers for each issue from a JSONL file.
    
    Args:
        ground_truth_path: Path to the ground truth JSONL file.
        
    Returns:
        Dictionary mapping issue_id to a set of relevant line numbers.
    """
    gt_map: Dict[str, Set[int]] = {}
    
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")
        
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            issue_id = record.get('issue_id')
            gt_lines = record.get('ground_truth_lines', [])
            
            if issue_id and gt_lines:
                gt_map[issue_id] = set(gt_lines)
                
    return gt_map


def load_retrieved_context(retrieved_path: Path) -> Dict[str, List[int]]:
    """
    Load retrieved context line numbers for each issue from a JSONL file.
    
    Args:
        retrieved_path: Path to the retrieved context JSONL file.
        
    Returns:
        Dictionary mapping issue_id to a list of retrieved line numbers in order.
    """
    retrieved_map: Dict[str, List[int]] = {}
    
    if not retrieved_path.exists():
        raise FileNotFoundError(f"Retrieved context file not found: {retrieved_path}")
        
    with open(retrieved_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line.strip())
            issue_id = record.get('issue_id')
            retrieved_lines = record.get('retrieved_lines', [])
            
            if issue_id and retrieved_lines:
                retrieved_map[issue_id] = retrieved_lines
                
    return retrieved_map


def calculate_first_relevant_position(
    retrieved_lines: List[int],
    gt_lines: Set[int],
    total_lines: int
) -> Tuple[int, bool]:
    """
    Calculate the position (1-indexed) of the first relevant line.
    
    Args:
        retrieved_lines: List of line numbers retrieved by the agent, in order.
        gt_lines: Set of ground truth line numbers that are relevant.
        total_lines: Total number of lines in the source file (for censored data handling).
        
    Returns:
        Tuple of (position, is_censored):
            - position: 1-indexed position of first relevant line, or total_lines + 1 if censored.
            - is_censored: True if no relevant line was found in retrieved context.
    """
    for idx, line_num in enumerate(retrieved_lines):
        if line_num in gt_lines:
            return (idx + 1, False)  # 1-indexed position
    
    # Censored data: relevant line never retrieved
    return (total_lines + 1, True)


def calculate_ranking_metrics(
    ground_truth_path: Path,
    retrieved_path: Path,
    file_lengths_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Calculate ranking metrics for all issues.
    
    Args:
        ground_truth_path: Path to ground truth JSONL.
        retrieved_path: Path to retrieved context JSONL.
        file_lengths_path: Optional path to JSONL with file lengths per issue_id.
        
    Returns:
        List of dictionaries containing ranking metrics per issue.
    """
    gt_map = load_ground_truth_lines(ground_truth_path)
    retrieved_map = load_retrieved_context(retrieved_path)
    
    file_lengths: Dict[str, int] = {}
    if file_lengths_path and file_lengths_path.exists():
        with open(file_lengths_path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line.strip())
                file_lengths[record['issue_id']] = record['total_lines']
    
    results = []
    
    # Process all issues that have both ground truth and retrieved context
    all_issue_ids = set(gt_map.keys()) & set(retrieved_map.keys())
    
    for issue_id in sorted(all_issue_ids):
        gt_lines = gt_map[issue_id]
        retrieved_lines = retrieved_map[issue_id]
        
        # Determine total lines for censored data penalty
        total_lines = file_lengths.get(issue_id, len(retrieved_lines) + 100)
        
        position, is_censored = calculate_first_relevant_position(
            retrieved_lines, gt_lines, total_lines
        )
        
        results.append({
            'issue_id': issue_id,
            'first_relevant_position': position,
            'is_censored': is_censored,
            'total_lines': total_lines,
            'penalty_applied': is_censored,
            'retrieved_count': len(retrieved_lines),
            'gt_count': len(gt_lines)
        })
        
    return results


def main():
    """Main entry point for ranking metrics calculation."""
    config_summary = get_config_summary()
    print(f"Running ranking metrics calculation with config: {config_summary}")
    
    # Define paths based on project structure
    base_path = Path(__file__).parent.parent
    ground_truth_path = base_path / "data" / "curated" / "hard_subset.jsonl"
    retrieved_path = base_path / "data" / "results" / "agent_logs" / "all_retrieved.jsonl"
    file_lengths_path = base_path / "data" / "curated" / "file_lengths.jsonl"
    output_path = base_path / "data" / "results" / "ranking_metrics.json"
    
    if not ground_truth_path.exists():
        print(f"Error: Ground truth file not found at {ground_truth_path}")
        sys.exit(1)
        
    if not retrieved_path.exists():
        print(f"Error: Retrieved context file not found at {retrieved_path}")
        sys.exit(1)
    
    print(f"Loading ground truth from: {ground_truth_path}")
    print(f"Loading retrieved context from: {retrieved_path}")
    
    results = calculate_ranking_metrics(
        ground_truth_path,
        retrieved_path,
        file_lengths_path
    )
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Ranking metrics saved to: {output_path}")
    print(f"Processed {len(results)} issues")
    
    # Print summary statistics
    if results:
        positions = [r['first_relevant_position'] for r in results]
        censored_count = sum(1 for r in results if r['is_censored'])
        
        print(f"\nSummary:")
        print(f"  Total issues: {len(results)}")
        print(f"  Censored (not found): {censored_count}")
        print(f"  Found: {len(results) - censored_count}")
        print(f"  Mean position (including penalty): {sum(positions) / len(positions):.2f}")
        print(f"  Median position (including penalty): {sorted(positions)[len(positions) // 2]}")


if __name__ == "__main__":
    main()