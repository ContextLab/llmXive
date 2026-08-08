import os
import json
import logging
from typing import Dict, Any, List
from config import get_config

logger = logging.getLogger(__name__)

class DataFlowViolationError(Exception):
    pass

# T065: Schema definitions for critical artifacts
ARTIFACT_CHAIN = [
    {
        "path": "data/processed/injected_datasets.json",
        "schema": {
            "required_keys": ["datasets"],
            "dataset_schema": {
                "required_keys": ["name", "clusters"],
                "cluster_schema": {
                    "required_keys": ["id", "members"]
                }
            }
        }
    },
    {
        "path": "data/processed/clusters.json",
        "schema": {
            "required_keys": ["clusters"],
            "cluster_schema": {
                "required_keys": ["id", "members", "jaccard_avg"]
            }
        }
    }
]

def validate_artifact_chain():
    """
    T065: Dependency Graph Validator.
    Checks existence and schema compliance of critical artifacts before ranker loop.
    """
    for artifact in ARTIFACT_CHAIN:
        path = artifact["path"]
        schema = artifact["schema"]
        
        if not os.path.exists(path):
            raise DataFlowViolationError(f"Artifact missing: {path}")
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DataFlowViolationError(f"Artifact invalid JSON: {path} - {e}")
        
        # Basic schema check
        if "required_keys" in schema:
            for key in schema["required_keys"]:
                if key not in data:
                    raise DataFlowViolationError(f"Artifact missing key '{key}': {path}")
        
        # Nested schema checks (simplified for T065)
        if "dataset_schema" in schema and "datasets" in data:
            for ds in data["datasets"]:
                for key in schema["dataset_schema"]["required_keys"]:
                    if key not in ds:
                        raise DataFlowViolationError(f"Dataset missing key '{key}' in {path}")
                if "clusters" in ds:
                    for cluster in ds["clusters"]:
                        for key in schema["dataset_schema"]["cluster_schema"]["required_keys"]:
                            if key not in cluster:
                                raise DataFlowViolationError(f"Cluster missing key '{key}' in {path}")
        
        if "cluster_schema" in schema and "clusters" in data:
            for cluster in data["clusters"]:
                for key in schema["cluster_schema"]["required_keys"]:
                    if key not in cluster:
                        raise DataFlowViolationError(f"Cluster missing key '{key}' in {path}")

        logger.info(f"Artifact validated: {path}")

    logger.info("Full artifact chain validated.")

def main():
    validate_artifact_chain()

if __name__ == "__main__":
    main()
