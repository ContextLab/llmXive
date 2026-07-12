import os
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List

from logging_config import setup_logging
from utils.profiling import start_profiling, stop_profiling, profile_block
from gatekeeper.classifiers import FrozenDistilBERTClassifier, run_intent_classification
from gatekeeper.rules import parse_role_definitions, parse_deletion_log, check_access_policy
from data.loader import fetch_gatemem, validate_fields

logger = setup_logging(__name__)


class GatekeeperPipeline:
    """Pipeline for Gatekeeper evaluation."""

    def __init__(
        self,
        classifier: FrozenDistilBERTClassifier,
        role_defs: List[Dict[str, Any]],
        deletion_logs: List[Dict[str, Any]]
    ):
        self.classifier = classifier
        self.roles = parse_role_definitions(role_defs)
        self.deletion_logs = [
            parse_deletion_log(log) for log in deletion_logs
            if parse_deletion_log(log) is not None
        ]
        logger.info(f"Pipeline initialized with {len(self.roles)} roles and {len(self.deletion_logs)} deletion logs")

    def run(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run the gatekeeper pipeline on a list of queries.

        Args:
            queries: List of query dictionaries.

        Returns:
            List of results with access decisions.
        """
        start_profiling()
        results = []

        # Classify intents
        with profile_block("classification"):
            classifications = run_intent_classification(self.classifier, queries)

        # Apply rules
        for query, classification in zip(queries, classifications):
            target_id = query.get("target_id", "")
            domain = query.get("domain", "")
            user_role = self.roles[0] if self.roles else None  # Simplified: use first role
            
            if not user_role:
                decision = {"allowed": False, "reason": "No role defined"}
            else:
                is_personal = query.get("is_personal", False)
                decision = check_access_policy(
                    target_id, domain, user_role, self.deletion_logs, is_personal
                )

            # Combine classifier and rule decision (AND logic)
            # For simplicity: if classifier says 'deny', block. If rules say 'deny', block.
            classifier_allow = classification.intent == "allow"
            rule_allow = decision["allowed"]
            
            final_allow = classifier_allow and rule_allow

            results.append({
                "query_id": query.get("id"),
                "intent": classification.intent,
                "classifier_allow": classifier_allow,
                "rule_decision": decision,
                "final_decision": "allow" if final_allow else "deny",
                "latency_ms": 0.0,  # Placeholder
                "peak_ram_mb": 0.0   # Placeholder
            })

        peak_mem = stop_profiling()
        logger.info(f"Pipeline run complete. Processed {len(results)} queries.")
        return results


def run_gatekeeper_pipeline(
    queries: List[Dict[str, Any]],
    role_defs: List[Dict[str, Any]],
    deletion_logs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Convenience function to run the gatekeeper pipeline.

    Args:
        queries: List of queries.
        role_defs: List of role definitions.
        deletion_logs: List of deletion logs.

    Returns:
        List of results.
    """
    classifier = FrozenDistilBERTClassifier()
    classifier.load()
    pipeline = GatekeeperPipeline(classifier, role_defs, deletion_logs)
    return pipeline.run(queries)


def run_baseline_pipeline(queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run a baseline pipeline (e.g., retrieval-only) for comparison.

    Args:
        queries: List of queries.

    Returns:
        List of baseline results.
    """
    logger.info("Running baseline pipeline")
    results = []
    for q in queries:
        results.append({
            "query_id": q.get("id"),
            "final_decision": "allow",
            "latency_ms": 0.0,
            "peak_ram_mb": 0.0
        })
    return results


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run Gatekeeper Evaluation")
    parser.add_argument("--domain", type=str, required=True, help="Domain to evaluate")
    parser.add_argument("--output", type=str, default="data/processed/results.json", help="Output file")
    args = parser.parse_args()

    logger.info(f"Starting evaluation for domain: {args.domain}")

    # Mock data for demonstration
    queries = [{"id": "1", "target_id": "t1", "domain": args.domain, "is_personal": False}]
    roles = [{"role_name": "user", "allowed_domains": {args.domain}}]
    logs = [{"request_id": "r1", "user_id": "u1", "target_id": "t1", "timestamp": "2023-01-01"}]

    results = run_gatekeeper_pipeline(queries, roles, logs)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
