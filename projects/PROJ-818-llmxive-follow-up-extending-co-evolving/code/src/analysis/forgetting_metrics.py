import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict

# Importing from existing API surface
from src.utils.config import Config, load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RuleIdentityRecord:
    """Record of rule IDs retained from initial to final state."""
    initial_rule_ids: Set[str]
    final_rule_ids: Set[str]
    retained_rule_ids: Set[str]
    lost_rule_ids: Set[str]
    retention_rate: float


@dataclass
class ForgettingResult:
    """Result of forgetting metric calculation."""
    run_id: str
    condition: str
    initial_accuracy: float
    final_accuracy: float
    forgetting_rate: float
    initial_metrics_source: str
    final_metrics_source: str


@dataclass
class RetentionMetrics:
    """Result of retention metric calculation."""
    run_id: str
    condition: str
    rule_identity_record: Dict[str, Any]
    retention_rate: float
    initial_state_source: str
    final_state_source: str


def load_test_instances(path: str) -> List[Dict[str, Any]]:
    """Load held-out test instances from JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Test instances file not found: {path}")
    
    with open(p, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of test instances, got {type(data)}")
    
    logger.info(f"Loaded {len(data)} test instances from {path}")
    return data


def load_agent_state(path: str) -> Dict[str, Any]:
    """Load agent state from JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Agent state file not found: {path}")
    
    with open(p, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded agent state from {path}")
    return data


def get_agent_rule_ids(agent_state: Dict[str, Any]) -> Set[str]:
    """Extract rule IDs from agent state."""
    if 'population' not in agent_state:
        logger.warning(f"No 'population' key in agent state from {agent_state.get('source', 'unknown')}")
        return set()
    
    rule_ids = set()
    population = agent_state['population']
    
    if isinstance(population, list):
        for agent in population:
            if isinstance(agent, dict) and 'rule_set' in agent:
                rule_set = agent['rule_set']
                if isinstance(rule_set, list):
                    for rule in rule_set:
                        if isinstance(rule, dict) and 'rule_id' in rule:
                            rule_ids.add(rule['rule_id'])
                elif isinstance(rule_set, dict) and 'rule_id' in rule_set:
                    rule_ids.add(rule_set['rule_id'])
    elif isinstance(population, dict):
        # Handle dict-based population structure
        if 'rule_sets' in population:
            for rule_set in population['rule_sets']:
                if isinstance(rule_set, dict) and 'rule_id' in rule_set:
                    rule_ids.add(rule_set['rule_id'])
    
    logger.info(f"Extracted {len(rule_ids)} unique rule IDs from agent state")
    return rule_ids


def evaluate_agent_on_instances(agent_state: Dict[str, Any], test_instances: List[Dict[str, Any]]) -> float:
    """
    Evaluate agent performance on test instances.
    
    Since the actual evaluation logic depends on the agent's internal structure
    and the test instance format, we extract the accuracy from the agent state
    if available, or compute it based on the rule sets.
    
    For this implementation, we assume the agent state contains an 'accuracy'
    or 'metrics' field that reflects performance on the test set.
    """
    # Try to get accuracy directly from state
    if 'metrics' in agent_state:
        metrics = agent_state['metrics']
        if isinstance(metrics, dict):
            if 'accuracy' in metrics:
                return float(metrics['accuracy'])
            if 'test_accuracy' in metrics:
                return float(metrics['test_accuracy'])
    
    if 'accuracy' in agent_state:
        return float(agent_state['accuracy'])
    
    # Fallback: compute based on rule set quality (simplified)
    # In a real implementation, this would run the agent on each test instance
    rule_ids = get_agent_rule_ids(agent_state)
    if not rule_ids:
        logger.warning("No rule IDs found, returning 0.0 accuracy")
        return 0.0
    
    # Simplified heuristic: assume more rules = better coverage (up to a point)
    # This is a placeholder for actual evaluation logic
    # Real implementation would simulate agent on test_instances
    max_rules = 100  # Expected max rules per agent
    raw_score = min(len(rule_ids) / max_rules, 1.0)
    return float(raw_score)


def calculate_retention_rate(initial_rule_ids: Set[str], final_rule_ids: Set[str]) -> float:
    """Calculate the retention rate of rule IDs from initial to final state."""
    if not initial_rule_ids:
        logger.warning("Initial rule IDs are empty, returning 0.0 retention rate")
        return 0.0
    
    retained = initial_rule_ids.intersection(final_rule_ids)
    rate = len(retained) / len(initial_rule_ids)
    logger.info(f"Retention rate: {len(retained)}/{len(initial_rule_ids)} = {rate:.4f}")
    return float(rate)


def compute_forgetting_metrics(
    run_id: str,
    condition: str,
    initial_metrics_path: str,
    final_metrics_path: str
) -> ForgettingResult:
    """
    Compute forgetting metrics by comparing initial and final accuracy.
    
    Formula: Forgetting Rate = (initial_accuracy - final_accuracy) / initial_accuracy
    """
    # Load initial metrics
    if not os.path.exists(initial_metrics_path):
        raise FileNotFoundError(f"Initial metrics file not found: {initial_metrics_path}")
    
    with open(initial_metrics_path, 'r') as f:
        initial_data = json.load(f)
    
    # Load final metrics
    if not os.path.exists(final_metrics_path):
        raise FileNotFoundError(f"Final metrics file not found: {final_metrics_path}")
    
    with open(final_metrics_path, 'r') as f:
        final_data = json.load(f)
    
    # Extract accuracies
    # Handle different possible structures
    initial_accuracy = None
    if isinstance(initial_data, dict):
        if 'accuracy' in initial_data:
            initial_accuracy = float(initial_data['accuracy'])
        elif 'metrics' in initial_data and isinstance(initial_data['metrics'], dict):
            initial_accuracy = float(initial_data['metrics'].get('accuracy', 0.0))
        elif 'initial_accuracy' in initial_data:
            initial_accuracy = float(initial_data['initial_accuracy'])
    
    final_accuracy = None
    if isinstance(final_data, dict):
        if 'accuracy' in final_data:
            final_accuracy = float(final_data['accuracy'])
        elif 'metrics' in final_data and isinstance(final_data['metrics'], dict):
            final_accuracy = float(final_data['metrics'].get('accuracy', 0.0))
        elif 'final_accuracy' in final_data:
            final_accuracy = float(final_data['final_accuracy'])
    
    if initial_accuracy is None:
        raise ValueError(f"Could not extract initial_accuracy from {initial_metrics_path}")
    if final_accuracy is None:
        raise ValueError(f"Could not extract final_accuracy from {final_metrics_path}")
    
    # Calculate forgetting rate
    if initial_accuracy == 0:
        forgetting_rate = 0.0  # Avoid division by zero
        logger.warning(f"Initial accuracy is 0, setting forgetting rate to 0.0")
    else:
        forgetting_rate = (initial_accuracy - final_accuracy) / initial_accuracy
    
    logger.info(f"Forgetting metrics for {run_id} ({condition}):")
    logger.info(f"  Initial accuracy: {initial_accuracy:.4f}")
    logger.info(f"  Final accuracy: {final_accuracy:.4f}")
    logger.info(f"  Forgetting rate: {forgetting_rate:.4f}")
    
    return ForgettingResult(
        run_id=run_id,
        condition=condition,
        initial_accuracy=initial_accuracy,
        final_accuracy=final_accuracy,
        forgetting_rate=forgetting_rate,
        initial_metrics_source=initial_metrics_path,
        final_metrics_source=final_metrics_path
    )


def compute_retention_metrics(
    run_id: str,
    condition: str,
    initial_state_path: str,
    final_state_path: str
) -> RetentionMetrics:
    """
    Compute retention metrics by comparing rule IDs from initial to final state.
    """
    # Load agent states
    initial_state = load_agent_state(initial_state_path)
    final_state = load_agent_state(final_state_path)
    
    # Extract rule IDs
    initial_rule_ids = get_agent_rule_ids(initial_state)
    final_rule_ids = get_agent_rule_ids(final_state)
    
    # Calculate retention
    retention_rate = calculate_retention_rate(initial_rule_ids, final_rule_ids)
    
    # Create identity record
    retained = initial_rule_ids.intersection(final_rule_ids)
    lost = initial_rule_ids - final_rule_ids
    
    identity_record = RuleIdentityRecord(
        initial_rule_ids=list(initial_rule_ids),
        final_rule_ids=list(final_rule_ids),
        retained_rule_ids=list(retained),
        lost_rule_ids=list(lost),
        retention_rate=retention_rate
    )
    
    logger.info(f"Retention metrics for {run_id} ({condition}):")
    logger.info(f"  Initial rules: {len(initial_rule_ids)}")
    logger.info(f"  Final rules: {len(final_rule_ids)}")
    logger.info(f"  Retained: {len(retained)}")
    logger.info(f"  Lost: {len(lost)}")
    logger.info(f"  Retention rate: {retention_rate:.4f}")
    
    return RetentionMetrics(
        run_id=run_id,
        condition=condition,
        rule_identity_record=asdict(identity_record),
        retention_rate=retention_rate,
        initial_state_source=initial_state_path,
        final_state_source=final_state_path
    )


def save_forgetting_metrics(results: List[ForgettingResult], output_path: str) -> None:
    """Save forgetting metrics to JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = [asdict(r) for r in results]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(results)} forgetting metrics to {output_path}")


def save_retention_metrics(results: List[RetentionMetrics], output_path: str) -> None:
    """Save retention metrics to JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = [asdict(r) for r in results]
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {len(results)} retention metrics to {output_path}")


def main():
    """
    Main entry point for computing forgetting and retention metrics.
    
    This function:
    1. Loads test instances (for context, though not directly used in this simplified version)
    2. Iterates through run directories to find initial and final metrics/states
    3. Computes forgetting and retention metrics for each run
    4. Saves results to data/results/baseline_metrics.json and data/results/final_metrics.json
    
    Expected directory structure:
    data/results/
        run_001/
            initial_metrics.json
            final_metrics.json
            initial_state.json
            final_state.json
        run_002/
            ...
    """
    results_dir = Path("data/results")
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        sys.exit(1)
    
    forgetting_results = []
    retention_results = []
    
    # Find all run directories
    run_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("run_")])
    
    if not run_dirs:
        logger.warning(f"No run directories found in {results_dir}")
        # Create empty output files
        save_forgetting_metrics([], "data/results/baseline_metrics.json")
        save_retention_metrics([], "data/results/final_metrics.json")
        return
    
    logger.info(f"Found {len(run_dirs)} run directories")
    
    for run_dir in run_dirs:
        run_id = run_dir.name
        
        # Determine condition from directory name or file content
        condition = "unknown"
        # Try to extract condition from run_id (e.g., run_001_sequential)
        parts = run_id.split("_")
        if len(parts) > 2:
            condition = parts[-1]
        
        # Paths for initial and final metrics
        initial_metrics_path = run_dir / "initial_metrics.json"
        final_metrics_path = run_dir / "final_metrics.json"
        initial_state_path = run_dir / "initial_state.json"
        final_state_path = run_dir / "final_state.json"
        
        # Compute forgetting metrics if files exist
        if initial_metrics_path.exists() and final_metrics_path.exists():
            try:
                forgetting_result = compute_forgetting_metrics(
                    run_id=run_id,
                    condition=condition,
                    initial_metrics_path=str(initial_metrics_path),
                    final_metrics_path=str(final_metrics_path)
                )
                forgetting_results.append(forgetting_result)
            except Exception as e:
                logger.error(f"Failed to compute forgetting metrics for {run_id}: {e}")
        else:
            logger.warning(f"Missing metrics files for {run_id}: "
                         f"{initial_metrics_path.exists()}, {final_metrics_path.exists()}")
        
        # Compute retention metrics if state files exist
        if initial_state_path.exists() and final_state_path.exists():
            try:
                retention_result = compute_retention_metrics(
                    run_id=run_id,
                    condition=condition,
                    initial_state_path=str(initial_state_path),
                    final_state_path=str(final_state_path)
                )
                retention_results.append(retention_result)
            except Exception as e:
                logger.error(f"Failed to compute retention metrics for {run_id}: {e}")
        else:
            logger.warning(f"Missing state files for {run_id}: "
                         f"{initial_state_path.exists()}, {final_state_path.exists()}")
    
    # Save results
    save_forgetting_metrics(forgetting_results, "data/results/baseline_metrics.json")
    save_retention_metrics(retention_results, "data/results/final_metrics.json")
    
    logger.info(f"Completed processing {len(forgetting_results)} forgetting metrics and "
               f"{len(retention_results)} retention metrics")


if __name__ == "__main__":
    main()
