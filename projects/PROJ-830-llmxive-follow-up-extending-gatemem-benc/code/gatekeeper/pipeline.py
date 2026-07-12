"""
Gatekeeper Pipeline Implementation.

Orchestrates the query processing flow:
1. Rule Check (Deletion logs and Role definitions)
2. Intent Classification (DistilBERT)
3. Decision Logic (Allow/Deny/Timeout)
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import from existing API surface
from gatekeeper.rules import (
    check_access_policy,
    parse_deletion_log,
    parse_role_definitions,
    DeletionLog,
    RoleDefinition
)
from gatekeeper.classifier import (
    FrozenDistilBERTClassifier,
    ClassificationResult,
    run_intent_classification
)
from models import Query, EvaluationResult
from logging_config import setup_logging, pin_random_seed

# Configure logging for this module
logger = logging.getLogger(__name__)

class GatekeeperPipeline:
    """
    Main pipeline class for the Gatekeeper module.
    Executes the sequence of checks for incoming queries.
    """

    def __init__(
        self,
        deletion_log_path: Optional[str] = None,
        role_definition_path: Optional[str] = None,
        classifier: Optional[FrozenDistilBERTClassifier] = None,
        timeout_seconds: float = 5.0
    ):
        """
        Initialize the pipeline components.

        Args:
            deletion_log_path: Path to JSON file containing deletion logs.
            role_definition_path: Path to JSON file containing role definitions.
            classifier: Pre-initialized classifier instance. If None, a default
                        frozen DistilBERT classifier is instantiated.
            timeout_seconds: Maximum allowed time for the classification step.
        """
        self.timeout_seconds = timeout_seconds
        
        # Load Rules
        self.deletion_logs: List[DeletionLog] = []
        self.role_definitions: List[RoleDefinition] = []
        
        if deletion_log_path and os.path.exists(deletion_log_path):
            self.deletion_logs = parse_deletion_log(deletion_log_path)
            logger.info(f"Loaded {len(self.deletion_logs)} deletion logs.")
        else:
            logger.warning(f"Deletion log path not found or empty: {deletion_log_path}")

        if role_definition_path and os.path.exists(role_definition_path):
            self.role_definitions = parse_role_definitions(role_definition_path)
            logger.info(f"Loaded {len(self.role_definitions)} role definitions.")
        else:
            logger.warning(f"Role definition path not found or empty: {role_definition_path}")

        # Load Classifier
        self.classifier = classifier or FrozenDistilBERTClassifier()
        logger.info("Gatekeeper Pipeline initialized.")

    def run_query(self, query: Query) -> EvaluationResult:
        """
        Execute the full gatekeeper pipeline on a single query.

        This function performs:
        1. Access Policy Check (Deletion Logs + Role Rules)
        2. Intent Classification (if access is not immediately denied)
        3. Final Decision

        Args:
            query: The incoming Query object.

        Returns:
            EvaluationResult containing the decision, reasons, and timing.
        """
        start_time = time.time()
        reasons: List[str] = []
        allowed = True
        classification_result: Optional[ClassificationResult] = None
        
        # 1. Rule Check (Deletion Logs and Role Definitions)
        # Priority: If a target is deleted, deny immediately regardless of role.
        # Then check if the role is authorized for the target.
        
        access_decision = check_access_policy(
            query=query,
            deletion_logs=self.deletion_logs,
            role_definitions=self.role_definitions
        )
        
        if not access_decision.is_allowed:
            allowed = False
            reasons.append(f"Access Denied by Rules: {access_decision.reason}")
            logger.info(f"Query blocked by rules: {query.query_text[:50]}... Reason: {access_decision.reason}")
        else:
            # 2. Intent Classification
            # Only proceed if rules allow access.
            try:
                # Enforce timeout on the classification step
                start_classify = time.time()
                
                # We pass the query text to the classifier
                classification_result = run_intent_classification(
                    query_text=query.query_text,
                    classifier=self.classifier,
                    timeout_seconds=self.timeout_seconds
                )
                
                classify_duration = time.time() - start_classify
                logger.debug(f"Classification took {classify_duration:.4f}s")

                # If classification indicates a high-risk intent (e.g., data extraction),
                # we might override the rule-based allow.
                # For now, we log the intent but respect the rule decision unless
                # specific high-risk thresholds are met (future extensibility).
                if classification_result.intent == "data_extraction":
                    reasons.append(f"High Risk Intent Detected: {classification_result.intent}")
                    # Optional: Uncomment to strictly block extraction intents
                    # allowed = False 
                
                reasons.append(f"Intent: {classification_result.intent} (confidence: {classification_result.confidence:.2f})")

            except TimeoutError as e:
                allowed = False
                reasons.append(f"Timeout during classification: {str(e)}")
                logger.error(f"Classification timeout for query: {query.query_text[:50]}...")
            except Exception as e:
                allowed = False
                reasons.append(f"Classification Error: {str(e)}")
                logger.error(f"Unexpected error during classification: {e}")

        end_time = time.time()
        total_duration = end_time - start_time

        result = EvaluationResult(
            query_id=query.query_id,
            is_allowed=allowed,
            reasons=reasons,
            intent=classification_result.intent if classification_result else "unknown",
            intent_confidence=classification_result.confidence if classification_result else 0.0,
            duration_seconds=total_duration,
            timestamp=datetime.now().isoformat()
        )

        return result

def run_query(query: Query) -> EvaluationResult:
    """
    Convenience function to run the pipeline with default configurations.
    
    This is the entry point expected by the task description.
    It initializes the pipeline with default paths and runs the query.
    
    Args:
        query: The query to process.
        
    Returns:
        EvaluationResult: The decision and metadata.
    """
    # Determine default paths based on project structure
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deletion_log_path = os.path.join(base_dir, "data", "processed", "deletion_logs.json")
    role_def_path = os.path.join(base_dir, "data", "processed", "role_definitions.json")
    
    # If files don't exist, we pass None to the pipeline (it will warn but continue)
    pipeline = GatekeeperPipeline(
        deletion_log_path=deletion_log_path if os.path.exists(deletion_log_path) else None,
        role_definition_path=role_def_path if os.path.exists(role_def_path) else None
    )
    
    return pipeline.run_query(query)

def main():
    """
    Main entry point for script execution (CLI or simple test).
    """
    # Setup logging
    setup_logging()
    pin_random_seed(42)
    
    logger.info("Starting Gatekeeper Pipeline Test.")
    
    # Create a dummy query for testing
    test_query = Query(
        query_id="test-001",
        query_text="What is the user's email address?",
        role="external_auditor",
        target_entity="user_profile",
        timestamp=datetime.now().isoformat()
    )
    
    try:
        result = run_query(test_query)
        logger.info(f"Pipeline Result: Allowed={result.is_allowed}, Intent={result.intent}")
        print(json.dumps(result.model_dump(), indent=2))
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
