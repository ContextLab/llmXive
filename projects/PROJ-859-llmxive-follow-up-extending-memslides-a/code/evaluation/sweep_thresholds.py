import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import shutil

class SweepThresholdsError(Exception):
    """Raised when threshold sweeping fails."""
    pass

def load_global_rules(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SweepThresholdsError(f"Global rules file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prune_rules_by_min_support(rules: List[Dict], min_support: float) -> List[Dict]:
    """Prune rules based on minimum support threshold."""
    return [r for r in rules if r.get('support', 0) >= min_support]

def prune_rules_by_max_depth(rules: List[Dict], max_depth: int) -> List[Dict]:
    """Prune rules based on maximum depth."""
    return [r for r in rules if r.get('depth', 0) <= max_depth]

def prune_rules_by_count(rules: List[Dict], max_count: int) -> List[Dict]:
    """Keep only the top N rules by support."""
    sorted_rules = sorted(rules, key=lambda x: x.get('support', 0), reverse=True)
    return sorted_rules[:max_count]

def apply_pruning(rules: List[Dict], strategy: str, threshold: float) -> List[Dict]:
    if strategy == 'min_support':
        return prune_rules_by_min_support(rules, threshold)
    elif strategy == 'max_depth':
        # Assuming depth is integer, threshold might be float, cast to int
        return prune_rules_by_max_depth(rules, int(threshold))
    elif strategy == 'count':
        return prune_rules_by_count(rules, int(threshold))
    else:
        raise SweepThresholdsError(f"Unknown pruning strategy: {strategy}")

def calculate_compression_ratio(original_count: int, pruned_count: int) -> float:
    if original_count == 0:
        return 0.0
    return pruned_count / original_count

def save_rule_set(rules: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2)

def run_sweep(global_rules_path: Path, output_dir: Path, config: Dict[str, Any]):
    """
    Run the threshold sweep.
    config: {
      'strategy': 'min_support' | 'max_depth' | 'count',
      'thresholds': [list of float/int],
      'output_prefix': str
    }
    """
    rules = load_global_rules(global_rules_path)
    original_count = len(rules)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    strategy = config.get('strategy', 'min_support')
    thresholds = config.get('thresholds', [0.1, 0.2, 0.3, 0.4, 0.5])

    for t in thresholds:
        pruned_rules = apply_pruning(rules, strategy, t)
        ratio = calculate_compression_ratio(original_count, len(pruned_rules))
        
        # Save individual rule set
        filename = f"{config.get('output_prefix', 'rules')}_t_{t}.json"
        save_path = output_dir / filename
        save_rule_set(pruned_rules, save_path)
        
        results.append({
            'threshold': t,
            'strategy': strategy,
            'original_count': original_count,
            'pruned_count': len(pruned_rules),
            'compression_ratio': ratio,
            'file': str(save_path)
        })

    return results

def main():
    """
    Main entry point for T037a.
    Generates multiple compressed rule sets by sweeping a compression/pruning threshold.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    code_root = project_root / "code"
    data_root = project_root / "data"
    
    global_rules_path = data_root / "processed" / "rules" / "global_rules.json"
    output_dir = data_root / "processed" / "rules" / "sweeps"
    sweep_config_path = data_root / "processed" / "sweep_config.json"

    # Default configuration for the sweep
    sweep_config = {
        "strategy": "min_support",
        "thresholds": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "output_prefix": "pruned_rules"
    }

    if not global_rules_path.exists():
        raise SweepThresholdsError(f"Global rules file not found at {global_rules_path}. "
                                   "Please run rule_induction.py first.")

    print(f"Running threshold sweep with config: {sweep_config}")
    
    results = run_sweep(global_rules_path, output_dir, sweep_config)
    
    # Save the sweep config and results metadata
    with open(sweep_config_path, 'w', encoding='utf-8') as f:
        json.dump({
            "config": sweep_config,
            "results": results
        }, f, indent=2)
    
    print(f"Sweep completed. Results saved to {sweep_config_path}")
    print(f"Rule sets saved to {output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
