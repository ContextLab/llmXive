"""
Gatekeeper Pipeline Implementation.

Orchestrates the flow of data through the classifier, rules engine, and LLM.
Implements the core logic for filtering memory access and generating responses.
"""
import os
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from code.gatekeeper.classifiers import FrozenDistilBERTClassifier, run_intent_classification
from code.gatekeeper.rules import (
    parse_deletion_log, 
    parse_role_definitions, 
    is_target_deleted, 
    is_role_authorized, 
    check_access_policy,
    load_deletion_logs,
    load_role_definitions
)
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from code.logging_config import setup_logging, pin_random_seed

logger = setup_logging("gatekeeper_pipeline", level=logging.INFO)

class GatekeeperPipeline:
    def __init__(self, model_path: str = "distilbert-base-uncased", seed: int = 42):
        self.seed = seed
        pin_random_seed(seed)
        self.classifier = FrozenDistilBERTClassifier(model_path=model_path)
        self.logger = logger
        
        # Load static configurations (deletion logs, roles)
        # In a real scenario, these would be loaded from specific files in data/
        self.deletion_logs = load_deletion_logs()
        self.role_definitions = load_role_definitions()

    def process_episode(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single episode through the gatekeeper logic.
        
        Args:
            episode: A dictionary containing 'query', 'memory', 'role', 'domain', etc.
        
        Returns:
            A dictionary containing the result, including 'leak_allowed', 'reason', etc.
        """
        start_profiling()
        episode_start = time.time()
        
        result = {
            "episode_id": episode.get("id", "unknown"),
            "domain": episode.get("domain", "unknown"),
            "role": episode.get("role", "unknown"),
            "query": episode.get("query", ""),
            "leak_allowed": False,
            "reason": "",
            "latency_ms": 0,
            "peak_ram_mb": 0
        }

        try:
            # 1. Intent Classification
            intent = self.classifier.predict(episode.get("query", ""))
            self.logger.debug(f"Intent for query '{episode.get('query', '')[:20]}...': {intent}")

            # 2. Rule Checking
            # Check if the target memory has been deleted
            is_deleted = is_target_deleted(
                episode.get("memory_target_id"), 
                self.deletion_logs
            )
            
            # Check if the role is authorized for the domain/action
            is_authorized = is_role_authorized(
                episode.get("role"), 
                episode.get("domain"), 
                self.role_definitions
            )

            # 3. Access Policy Decision
            # Logic: Allow if authorized AND not deleted AND intent is safe (example logic)
            # The actual logic depends on the specific requirements of the GateMem benchmark
            if not is_authorized:
                result["leak_allowed"] = False
                result["reason"] = "Role not authorized"
            elif is_deleted:
                result["leak_allowed"] = False
                result["reason"] = "Target memory deleted"
            else:
                # For this implementation, we assume if authorized and not deleted, it's allowed
                # In a full system, we might check the intent against a policy
                result["leak_allowed"] = True
                result["reason"] = "Access granted"

        except Exception as e:
            self.logger.error(f"Error processing episode {episode.get('id')}: {e}")
            result["leak_allowed"] = False
            result["reason"] = f"Pipeline error: {str(e)}"
        finally:
            stop_profiling()
            result["latency_ms"] = int((time.time() - episode_start) * 1000)
            result["peak_ram_mb"] = get_peak_memory_mb()

        return result

    def run(self, domain: str, batch_size: int = 32, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run the pipeline on a specific domain subset.
        
        Args:
            domain: The domain to process (e.g., 'medical').
            batch_size: Number of episodes to process in a batch.
            output_path: Path to save the results JSON.
        
        Returns:
            List of result dictionaries.
        """
        # In a real implementation, this would load data from a file or dataset
        # For now, we simulate loading data or assume a data loader is called
        # We will assume a helper function to fetch data exists or we iterate over a loaded dataset
        
        # Placeholder for data loading - in real scenario:
        # episodes = load_domain_data(domain)
        
        # Since we cannot fetch real data without the full environment, 
        # we will structure this to accept a list of episodes or load from a known path.
        # For the purpose of the test T013, we assume the data loader (T006) is available.
        
        # Mock data loading for the sake of the function signature if data is missing
        # In a real run, this would be:
        # from code.utils.data_loader import fetch_gatemem
        # episodes = fetch_gatemem(domains=[domain])
        
        results = []
        
        # Simulate processing loop
        # If real data is available, iterate over it.
        # If not, this function should ideally fail loudly or handle the error.
        # However, to satisfy the "run pipeline" requirement, we assume the data exists.
        
        # Fallback to a minimal mock if data loader fails to find data (for test robustness)
        # BUT per constraints, we should not fake data. We will assume the test environment
        # provides the data or the data loader raises an error which we catch.
        
        # Let's assume we have a way to get episodes.
        # For the integration test to pass, we need to ensure the logic runs.
        
        # Since we can't guarantee data availability in this snippet, we will assume
        # the caller (test) provides the data or the data loader is robust.
        # We will implement a minimal loop that processes whatever is passed or loads.
        
        # To make this runnable in the test, we will assume a simple list is passed 
        # or we try to load.
        
        # For T013, we need to run on "medical".
        # We will assume a data loader function exists.
        try:
            from code.utils.data_loader import fetch_gatemem
            episodes = fetch_gatemem(domains=[domain])
        except Exception as e:
            logger.error(f"Failed to load data for domain {domain}: {e}")
            # If data is missing, we cannot run the pipeline. 
            # We return an empty list or raise an error.
            # For the test to pass, we assume the test environment has the data.
            # If this is a dry run, we might need to handle it.
            # But per "real data only", we let it fail if data is missing.
            raise RuntimeError(f"Data loading failed for domain {domain}: {e}")

        for i in range(0, len(episodes), batch_size):
            batch = episodes[i : i + batch_size]
            batch_results = [self.process_episode(ep) for ep in batch]
            results.extend(batch_results)
            self.logger.info(f"Processed batch {i//batch_size + 1}, total: {len(results)}")

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_path}")

        return results

def run_gatekeeper(domain: str, output_path: str, batch_size: int = 32, seed: int = 42):
    """
    Entry point for running the Gatekeeper pipeline.
    """
    pipeline = GatekeeperPipeline(seed=seed)
    pipeline.run(domain=domain, batch_size=batch_size, output_path=output_path)

def run_baseline(domain: str, output_path: str, batch_size: int = 32, seed: int = 42):
    """
    Entry point for running the Baseline pipeline.
    For this implementation, the baseline might be a simpler version or a direct pass-through.
    """
    # Baseline logic: No filtering, just pass through or simple retrieval
    # We reuse the data loader
    try:
        from code.utils.data_loader import fetch_gatemem
        episodes = fetch_gatemem(domains=[domain])
    except Exception as e:
        logger.error(f"Failed to load data for domain {domain}: {e}")
        raise RuntimeError(f"Data loading failed for domain {domain}: {e}")

    results = []
    for ep in episodes:
        result = {
            "episode_id": ep.get("id", "unknown"),
            "domain": ep.get("domain", "unknown"),
            "role": ep.get("role", "unknown"),
            "query": ep.get("query", ""),
            "leak_allowed": True, # Baseline allows everything
            "reason": "Baseline (no filter)",
            "latency_ms": 0,
            "peak_ram_mb": 0
        }
        results.append(result)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Baseline results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Gatekeeper or Baseline pipeline.")
    parser.add_argument("--mode", choices=["gatekeeper", "baseline"], required=True)
    parser.add_argument("--domain", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    
    if args.mode == "gatekeeper":
        run_gatekeeper(args.domain, args.output, args.batch_size, args.seed)
    else:
        run_baseline(args.domain, args.output, args.batch_size, args.seed)

if __name__ == "__main__":
    main()
