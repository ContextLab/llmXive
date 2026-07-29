import os
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from data.loader import fetch_gatemem
from data.preprocess import clean_and_format
from gatekeeper.rules import parse_role_definitions, parse_deletion_log, check_access_policy
from gatekeeper.classifiers import FrozenDistilBERTClassifier, ClassificationResult
from utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from logging_config import setup_logging, pin_random_seed
from models import Query, MemoryChunk, EvaluationResult

logger = setup_logging(__name__)

class GatekeeperPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classifier = None
        self.role_defs = None
        self.deletion_log = None
        self.results: List[EvaluationResult] = []

    def load_components(self):
        """Load classifier, rules, and logs."""
        if self.config.get("use_classifier", True):
            logger.info("Loading frozen DistilBERT classifier...")
            self.classifier = FrozenDistilBERTClassifier()
        
        rules_path = Path(self.config.get("rules_path", "data/rules/deletion_logs.json"))
        if rules_path.exists():
            with open(rules_path, "r") as f:
                raw_logs = json.load(f)
            self.deletion_log = parse_deletion_log(raw_logs)
            logger.info(f"Loaded deletion log with {len(self.deletion_log)} entries.")
        else:
            logger.warning(f"Deletion log not found at {rules_path}. Access control will be lenient.")
            self.deletion_log = []

        role_path = Path(self.config.get("roles_path", "data/rules/roles.json"))
        if role_path.exists():
            with open(role_path, "r") as f:
                raw_roles = json.load(f)
            self.role_defs = parse_role_definitions(raw_roles)
            logger.info(f"Loaded {len(self.role_defs)} role definitions.")
        else:
            logger.warning(f"Role definitions not found at {role_path}. Defaulting to allow.")
            self.role_defs = []

    def _run_gatekeeper_logic(self, query: Query, context: List[MemoryChunk]) -> Tuple[bool, str]:
        """
        Core Gatekeeper logic:
        1. Classifier check (if enabled)
        2. Rules check (Deletion + Role)
        3. Return (allow, reason)
        """
        # 1. Classifier Check
        if self.classifier:
            res = self.classifier.predict(query.text)
            if res.intent == "deny" or res.confidence > self.config.get("classifier_threshold", 0.8):
                if res.intent == "deny":
                    return False, f"Classifier denied intent: {res.intent}"

        # 2. Rules Check
        if self.deletion_log and self.role_defs:
            is_authorized = check_access_policy(
                query, 
                self.deletion_log, 
                self.role_defs,
                context
            )
            if not is_authorized:
                return False, "Access denied by policy rules"

        return True, "Access granted"

    def run_gatekeeper(self, data_path: str, output_path: str, domain_filter: Optional[List[str]] = None):
        """Execute the full Gatekeeper pipeline."""
        logger.info(f"Starting Gatekeeper run on {data_path}")
        start_profiling()
        
        raw_data = fetch_gatemem(data_path)
        if domain_filter:
            raw_data = [d for d in raw_data if d.get("domain") in domain_filter]
        
        results = []
        for item in raw_data:
            query = Query(
                id=item.get("id"),
                text=item.get("query"),
                role=item.get("role"),
                domain=item.get("domain")
            )
            # Context construction from dataset
            context = [
                MemoryChunk(id=c["id"], text=c["text"], role=c.get("role", "unknown"))
                for c in item.get("memory_chunks", [])
            ]

            allowed, reason = self._run_gatekeeper_logic(query, context)
            
            # Determine ground truth (simplified: if allowed and ground truth says leak -> leak)
            # In real implementation, we compare against item["leak_target"]
            ground_truth_leak = item.get("leak_target", False)
            
            result = EvaluationResult(
                id=query.id,
                method="Gatekeeper",
                domain=query.domain,
                allowed=allowed,
                reason=reason,
                ground_truth_leak=ground_truth_leak,
                latency_ms=0, # Placeholder, filled by profiling if needed per item
                peak_ram_mb=get_peak_memory_mb()
            )
            results.append(result)

        stop_profiling()
        
        # Save results
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump([r.model_dump() for r in results], f, indent=2)
        
        logger.info(f"Gatekeeper results saved to {output_path}")
        return results

    def run_baseline_retrieval(self, data_path: str, output_path: str, domain_filter: Optional[List[str]] = None):
        """
        Baseline: Retrieval-only. 
        Simulates a standard RAG pipeline without the Gatekeeper filter.
        Uses templates/prompts.yaml for retrieval logic if available, 
        otherwise defaults to direct context passing.
        """
        logger.info(f"Starting Baseline (Retrieval-only) run on {data_path}")
        start_profiling()

        raw_data = fetch_gatemem(data_path)
        if domain_filter:
            raw_data = [d for d in raw_data if d.get("domain") in domain_filter]

        results = []
        for item in raw_data:
            query = Query(
                id=item.get("id"),
                text=item.get("query"),
                role=item.get("role"),
                domain=item.get("domain")
            )
            context = [
                MemoryChunk(id=c["id"], text=c["text"], role=c.get("role", "unknown"))
                for c in item.get("memory_chunks", [])
            ]

            # Baseline logic: Always allow access to context (no filter)
            allowed = True
            reason = "Baseline: No access control applied"

            ground_truth_leak = item.get("leak_target", False)

            result = EvaluationResult(
                id=query.id,
                method="Baseline-Retrieval",
                domain=query.domain,
                allowed=allowed,
                reason=reason,
                ground_truth_leak=ground_truth_leak,
                latency_ms=0,
                peak_ram_mb=get_peak_memory_mb()
            )
            results.append(result)

        stop_profiling()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump([r.model_dump() for r in results], f, indent=2)
        
        logger.info(f"Baseline (Retrieval) results saved to {output_path}")
        return results

    def run_baseline_long_context(self, data_path: str, output_path: str, domain_filter: Optional[List[str]] = None):
        """
        Baseline: Long-Context.
        Simulates passing the entire history to the LLM without retrieval filtering.
        """
        logger.info(f"Starting Baseline (Long-Context) run on {data_path}")
        start_profiling()

        raw_data = fetch_gatemem(data_path)
        if domain_filter:
            raw_data = [d for d in raw_data if d.get("domain") in domain_filter]

        results = []
        for item in raw_data:
            query = Query(
                id=item.get("id"),
                text=item.get("query"),
                role=item.get("role"),
                domain=item.get("domain")
            )
            # In long context, we pass everything
            context = [
                MemoryChunk(id=c["id"], text=c["text"], role=c.get("role", "unknown"))
                for c in item.get("memory_chunks", [])
            ]

            allowed = True
            reason = "Baseline: Long-Context (No filtering)"

            ground_truth_leak = item.get("leak_target", False)

            result = EvaluationResult(
                id=query.id,
                method="Baseline-LongContext",
                domain=query.domain,
                allowed=allowed,
                reason=reason,
                ground_truth_leak=ground_truth_leak,
                latency_ms=0,
                peak_ram_mb=get_peak_memory_mb()
            )
            results.append(result)

        stop_profiling()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump([r.model_dump() for r in results], f, indent=2)
        
        logger.info(f"Baseline (Long-Context) results saved to {output_path}")
        return results

def run_gatekeeper(args):
    pin_random_seed(42)
    pipeline = GatekeeperPipeline(vars(args))
    pipeline.load_components()
    pipeline.run_gatekeeper(
        data_path=args.data_path,
        output_path=args.output_path,
        domain_filter=args.domains
    )

def run_baseline(args):
    pin_random_seed(42)
    pipeline = GatekeeperPipeline(vars(args))
    pipeline.load_components()
    
    baseline_type = args.baseline_type or "retrieval"
    
    if baseline_type == "retrieval":
        pipeline.run_baseline_retrieval(
            data_path=args.data_path,
            output_path=args.output_path,
            domain_filter=args.domains
        )
    elif baseline_type == "long_context":
        pipeline.run_baseline_long_context(
            data_path=args.data_path,
            output_path=args.output_path,
            domain_filter=args.domains
        )
    else:
        logger.error(f"Unknown baseline type: {baseline_type}")
        raise ValueError(f"Unknown baseline type: {baseline_type}")

def main():
    parser = argparse.ArgumentParser(description="Gatekeeper Pipeline Runner")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Gatekeeper Command
    p_gate = subparsers.add_parser("gatekeeper", help="Run Gatekeeper pipeline")
    p_gate.add_argument("--data_path", type=str, required=True, help="Path to input dataset")
    p_gate.add_argument("--output_path", type=str, required=True, help="Path to output results")
    p_gate.add_argument("--domains", type=str, nargs="+", default=None, help="Domains to process")
    p_gate.add_argument("--use_classifier", action="store_true", default=True)
    p_gate.add_argument("--classifier_threshold", type=float, default=0.8)

    # Baseline Command
    p_base = subparsers.add_parser("baseline", help="Run Baseline pipeline")
    p_base.add_argument("--data_path", type=str, required=True)
    p_base.add_argument("--output_path", type=str, required=True)
    p_base.add_argument("--domains", type=str, nargs="+", default=None)
    p_base.add_argument("--baseline_type", type=str, choices=["retrieval", "long_context"], default="retrieval")

    args = parser.parse_args()
    
    if args.command == "gatekeeper":
        run_gatekeeper(args)
    elif args.command == "baseline":
        run_baseline(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
