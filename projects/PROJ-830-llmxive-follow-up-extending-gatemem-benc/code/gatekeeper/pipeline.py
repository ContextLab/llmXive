import os
import json
import logging
import time
import argparse
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from code.logging_config import setup_logging
from code.data.loader import fetch_gatemem
from code.utils.data_loader import load_from_jsonl
from code.gatekeeper.classifiers import FrozenDistilBERTClassifier
from code.gatekeeper.rules import check_access_policy, load_role_definitions, load_deletion_logs
from code.utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb, get_process_memory_mb

# Setup logging
logger = setup_logging("pipeline")

class GatekeeperPipeline:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.classifier = None
        self.role_definitions = None
        self.deletion_logs = None
        self.prompts = None
        self._load_resources()

    def _load_resources(self):
        """Load classifier, rules, and prompt templates."""
        logger.info("Loading Gatekeeper resources...")
        
        # Load Classifier
        if self.config.get("use_classifier", True):
            self.classifier = FrozenDistilBERTClassifier(
                model_name=self.config.get("classifier_model", "distilbert-base-uncased"),
                device=self.config.get("device", "cpu")
            )
            logger.info("Classifier loaded successfully.")
        
        # Load Rules
        self.role_definitions = load_role_definitions(
            self.config.get("role_definitions_path", "data/raw/role_definitions.json")
        )
        self.deletion_logs = load_deletion_logs(
            self.config.get("deletion_logs_path", "data/raw/deletion_logs.json")
        )
        
        # Load Prompts
        prompts_path = self.config.get("prompts_path", "templates/prompts.yaml")
        import yaml
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

    def run_gatekeeper(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full Gatekeeper pipeline:
        1. Intent Classification
        2. Rule Checking (Deletion + Role)
        3. Retrieval (if allowed)
        4. Generation (if allowed)
        """
        start_profiling()
        start_time = time.time()
        
        result = {
            "episode_id": episode.get("id"),
            "domain": episode.get("domain"),
            "query": episode.get("query"),
            "allowed": False,
            "reason": "",
            "retrieved_context": None,
            "response": None,
            "latency_ms": 0,
            "peak_ram_mb": 0
        }

        try:
            # 1. Intent Classification
            if self.classifier:
                classification = self.classifier.run_intent_classification([episode])
                intent = classification[0].intent if classification else "unknown"
                result["intent"] = intent
                if intent in ["deny", "restricted"]:
                    result["allowed"] = False
                    result["reason"] = f"Intent classification blocked: {intent}"
                    return result

            # 2. Rule Checking
            role = episode.get("role", "guest")
            target = episode.get("target_id")
            
            is_authorized = check_access_policy(
                role=role,
                target=target,
                role_defs=self.role_definitions,
                deletion_logs=self.deletion_logs
            )
            
            if not is_authorized:
                result["allowed"] = False
                result["reason"] = "Access policy violation (Deletion or Role)"
                return result

            # 3. Retrieval
            # Filter memory based on allowed status (already checked)
            # In a real scenario, this would query a vector DB
            context = episode.get("context", [])
            if not context:
                result["allowed"] = False
                result["reason"] = "No context available for retrieval"
                return result
            
            # Simulate retrieval with top-k
            k = self.config.get("retrieval_top_k", 5)
            result["retrieved_context"] = context[:k]

            # 4. Generation (Simulated for benchmark)
            # In a real scenario, this would call an LLM
            prompt_template = self.prompts["retrieval_only"]["user_prompt_template"]
            prompt = prompt_template.format(
                context="\n".join(result["retrieved_context"]),
                query=episode.get("query")
            )
            
            # Simulate LLM response (since we don't have a real LLM endpoint in this script)
            # In a real implementation, this would call an LLM API
            result["response"] = f"[Simulated Response for: {episode.get('query')}]"
            result["allowed"] = True
            result["reason"] = "Access granted"

        except Exception as e:
            logger.error(f"Error in gatekeeper pipeline: {e}")
            result["allowed"] = False
            result["reason"] = f"Pipeline error: {str(e)}"
        
        finally:
            end_time = time.time()
            stop_profiling()
            result["latency_ms"] = (end_time - start_time) * 1000
            result["peak_ram_mb"] = get_peak_memory_mb()

        return result

    def run_baseline_retrieval_only(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """
        Baseline: Retrieval-only (No Gatekeeper).
        Directly retrieves context and generates response.
        """
        start_profiling()
        start_time = time.time()
        
        result = {
            "episode_id": episode.get("id"),
            "domain": episode.get("domain"),
            "query": episode.get("query"),
            "method": "baseline_retrieval_only",
            "allowed": True,
            "reason": "Baseline (no gatekeeper)",
            "retrieved_context": None,
            "response": None,
            "latency_ms": 0,
            "peak_ram_mb": 0
        }

        try:
            # Direct retrieval without filtering
            context = episode.get("context", [])
            k = self.config.get("retrieval_top_k", 5)
            result["retrieved_context"] = context[:k]

            # Generate response
            prompt_template = self.prompts["retrieval_only"]["user_prompt_template"]
            prompt = prompt_template.format(
                context="\n".join(result["retrieved_context"]),
                query=episode.get("query")
            )
            
            result["response"] = f"[Simulated Response for: {episode.get('query')}]"

        except Exception as e:
            logger.error(f"Error in baseline retrieval pipeline: {e}")
            result["allowed"] = False
            result["reason"] = f"Pipeline error: {str(e)}"
        
        finally:
            end_time = time.time()
            stop_profiling()
            result["latency_ms"] = (end_time - start_time) * 1000
            result["peak_ram_mb"] = get_peak_memory_mb()

        return result

    def run_baseline_long_context(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """
        Baseline: Long-Context (No Gatekeeper).
        Uses full context without retrieval filtering.
        """
        start_profiling()
        start_time = time.time()
        
        result = {
            "episode_id": episode.get("id"),
            "domain": episode.get("domain"),
            "query": episode.get("query"),
            "method": "baseline_long_context",
            "allowed": True,
            "reason": "Baseline (long context, no gatekeeper)",
            "retrieved_context": None,
            "full_context": None,
            "response": None,
            "latency_ms": 0,
            "peak_ram_mb": 0
        }

        try:
            # Use full context
            full_context = episode.get("context", [])
            result["full_context"] = full_context

            # Generate response using long context template
            prompt_template = self.prompts["long_context"]["user_prompt_template"]
            prompt = prompt_template.format(
                long_context="\n".join(full_context),
                query=episode.get("query")
            )
            
            result["response"] = f"[Simulated Response for: {episode.get('query')}]"

        except Exception as e:
            logger.error(f"Error in baseline long context pipeline: {e}")
            result["allowed"] = False
            result["reason"] = f"Pipeline error: {str(e)}"
        
        finally:
            end_time = time.time()
            stop_profiling()
            result["latency_ms"] = (end_time - start_time) * 1000
            result["peak_ram_mb"] = get_peak_memory_mb()

        return result


def run_gatekeeper(
    data_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute the Gatekeeper pipeline on a dataset.
    """
    if config is None:
        config = {
            "use_classifier": True,
            "classifier_model": "distilbert-base-uncased",
            "device": "cpu",
            "role_definitions_path": "data/raw/role_definitions.json",
            "deletion_logs_path": "data/raw/deletion_logs.json",
            "prompts_path": "templates/prompts.yaml",
            "retrieval_top_k": 5
        }

    pipeline = GatekeeperPipeline(config)
    
    # Load data
    if os.path.exists(data_path):
        episodes = load_from_jsonl(data_path)
    else:
        # Try to fetch from HF
        logger.warning(f"Data path {data_path} not found. Attempting to fetch from HF...")
        # In a real scenario, we would call fetch_gatemem here
        # For now, we assume the data is pre-loaded or this fails loudly
        raise FileNotFoundError(f"Data file not found: {data_path}")

    results = []
    for i, episode in enumerate(episodes):
        logger.info(f"Processing episode {i+1}/{len(episodes)}")
        result = pipeline.run_gatekeeper(episode)
        results.append(result)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Gatekeeper results saved to {output_path}")
    return results


def run_baseline(
    data_path: str,
    output_path: str,
    baseline_type: str = "retrieval_only",
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Execute the Baseline pipeline (Retrieval-only or Long-Context).
    """
    if config is None:
        config = {
            "retrieval_top_k": 5,
            "prompts_path": "templates/prompts.yaml"
        }

    pipeline = GatekeeperPipeline(config)
    
    # Load data
    if os.path.exists(data_path):
        episodes = load_from_jsonl(data_path)
    else:
        raise FileNotFoundError(f"Data file not found: {data_path}")

    results = []
    for i, episode in enumerate(episodes):
        logger.info(f"Processing baseline episode {i+1}/{len(episodes)}")
        
        if baseline_type == "retrieval_only":
            result = pipeline.run_baseline_retrieval_only(episode)
        elif baseline_type == "long_context":
            result = pipeline.run_baseline_long_context(episode)
        else:
            raise ValueError(f"Unknown baseline type: {baseline_type}")
        
        results.append(result)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline results ({baseline_type}) saved to {output_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Run Gatekeeper or Baseline pipelines")
    parser.add_argument("--mode", choices=["gatekeeper", "baseline_retrieval", "baseline_long_context"], required=True)
    parser.add_argument("--input", required=True, help="Input JSONL data path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--config", type=str, default=None, help="Path to config JSON (optional)")
    
    args = parser.parse_args()
    
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)

    if args.mode == "gatekeeper":
        run_gatekeeper(args.input, args.output, config)
    elif args.mode == "baseline_retrieval":
        run_baseline(args.input, args.output, "retrieval_only", config)
    elif args.mode == "baseline_long_context":
        run_baseline(args.input, args.output, "long_context", config)


if __name__ == "__main__":
    main()