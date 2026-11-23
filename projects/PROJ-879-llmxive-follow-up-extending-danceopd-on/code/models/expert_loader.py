# Implementation of T029b: Load Expert Field Logic
# Loads individual expert field weights and logic from the teacher model package.
# This module provides the interface to extract and cache specific expert modules
# required for re-inference in the Euler integrator and fidelity evaluation.

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import torch
from utils.config import get_config, get_path
from utils.check_weights import load_manifest, verify_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known expert IDs based on DanceOPD architecture (assumed from context/spec)
# If the teacher model package defines these elsewhere, they should be imported.
# For now, we assume standard expert routing IDs.
KNOWN_EXPERT_IDS = [
    "expert_style",
    "expert_structure",
    "expert_texture",
    "expert_lighting",
    "expert_composition"
]

class ExpertFieldLoader:
    """
    Manages loading and caching of individual expert field modules.
    """
    def __init__(self, teacher_weights_path: Optional[str] = None):
        self.config = get_config()
        self.teacher_weights_path = teacher_weights_path or get_path("TEACHER_WEIGHTS_PATH")
        self.expert_fields: Dict[str, Any] = {}
        self.loaded = False
        
        if not self.teacher_weights_path:
            raise ValueError("TEACHER_WEIGHTS_PATH must be set in config or provided explicitly.")

        if not os.path.exists(self.teacher_weights_path):
            raise FileNotFoundError(f"Teacher weights not found at: {self.teacher_weights_path}")

    def load_manifest(self) -> Dict[str, Any]:
        """Load the weights manifest to verify available expert weights."""
        manifest_path = get_path("WEIGHTS_MANIFEST_PATH")
        if not os.path.exists(manifest_path):
            logger.warning(f"Manifest not found at {manifest_path}. Initializing...")
            # In a real scenario, we might need to generate this or fail.
            # For this task, we assume the manifest exists or is handled by T008.
            return {}
        
        return load_manifest(manifest_path)

    def get_expert_field(self, expert_id: str) -> Any:
        """
        Retrieve a specific expert field module.
        If not loaded, attempts to load it from the teacher weights.
        
        Args:
            expert_id: The identifier of the expert field (e.g., 'expert_style').
        
        Returns:
            The expert field module (state dict or module object).
        
        Raises:
            ValueError: If the expert_id is not known or weights are missing.
        """
        if expert_id in self.expert_fields:
            return self.expert_fields[expert_id]

        # Verify expert_id is known
        if expert_id not in KNOWN_EXPERT_IDS:
            raise ValueError(f"Unknown expert_id: {expert_id}. Known IDs: {KNOWN_EXPERT_IDS}")

        # Attempt to load from weights
        logger.info(f"Loading expert field: {expert_id}")
        try:
            # Assuming the teacher weights are a dict containing expert sub-modules
            # or a state_dict where keys are prefixed by expert_id.
            # The exact loading logic depends on the teacher model architecture.
            # Here we assume a generic loading strategy based on the manifest.
            
            manifest = self.load_manifest()
            if not manifest:
                # Fallback: try loading directly from the main weights file
                # This assumes the teacher model was saved as a single checkpoint
                # containing all expert fields.
                checkpoint = torch.load(self.teacher_weights_path, map_location='cpu', weights_only=True)
                
                # Heuristic: extract expert fields from checkpoint
                # This part is highly dependent on the actual model structure.
                # We assume keys like 'expert_style.weight', 'expert_style.bias', etc.
                expert_state_dict = {}
                for key, value in checkpoint.items():
                    if key.startswith(expert_id):
                        # Strip prefix if necessary, or keep as is
                        expert_state_dict[key] = value
                
                if not expert_state_dict:
                    # Try without prefix if the checkpoint structure is flat per expert
                    # This is a guess; in reality, the model class would define this.
                    logger.warning(f"No keys found with prefix '{expert_id}' in checkpoint. Trying direct load...")
                    # If the checkpoint is a dict of experts directly:
                    if isinstance(checkpoint, dict) and expert_id in checkpoint:
                        expert_state_dict = checkpoint[expert_id]
                    elif isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
                        sd = checkpoint['state_dict']
                        for k, v in sd.items():
                            if k.startswith(expert_id):
                                expert_state_dict[k] = v
                
                if not expert_state_dict:
                    raise KeyError(f"Could not find weights for expert '{expert_id}' in {self.teacher_weights_path}")
                
                self.expert_fields[expert_id] = expert_state_dict
                logger.info(f"Successfully loaded weights for expert: {expert_id}")
                
            else:
                # Use manifest to locate specific expert weights
                # This assumes the manifest has entries for each expert
                if expert_id not in manifest:
                    raise KeyError(f"Expert '{expert_id}' not found in manifest.")
                
                expert_info = manifest[expert_id]
                expert_path = expert_info.get('path')
                if not expert_path or not os.path.exists(expert_path):
                    raise FileNotFoundError(f"Expert weights path from manifest not found: {expert_path}")
                
                # Verify checksum
                if not verify_file(expert_path, expert_info.get('hash')):
                    raise ValueError(f"Checksum verification failed for expert: {expert_id}")
                
                expert_state_dict = torch.load(expert_path, map_location='cpu', weights_only=True)
                self.expert_fields[expert_id] = expert_state_dict
                logger.info(f"Successfully loaded expert weights from manifest: {expert_id}")

        except Exception as e:
            logger.error(f"Failed to load expert field {expert_id}: {e}")
            raise

        return self.expert_fields[expert_id]

    def load_all_experts(self) -> Dict[str, Any]:
        """Load all known expert fields."""
        for expert_id in KNOWN_EXPERT_IDS:
            try:
                self.get_expert_field(expert_id)
            except Exception as e:
                logger.warning(f"Skipping expert {expert_id} due to error: {e}")
        self.loaded = True
        return self.expert_fields

def get_expert_field_logic(expert_id: str) -> Any:
    """
    Convenience function to get an expert field's logic/weights.
    Uses a singleton loader instance.
    """
    # In a real pipeline, we might pass the loader instance or config.
    # Here we instantiate on demand.
    loader = ExpertFieldLoader()
    return loader.get_expert_field(expert_id)

def get_known_expert_ids() -> List[str]:
    """Return the list of known expert IDs."""
    return KNOWN_EXPERT_IDS

def main():
    """
    Entry point for testing/loading experts independently.
    """
    parser = argparse.ArgumentParser(description="Load Expert Field Logic")
    parser.add_argument("--expert-id", type=str, default=None, help="Specific expert ID to load")
    parser.add_argument("--all", action="store_true", help="Load all expert fields")
    args = parser.parse_args()

    try:
        loader = ExpertFieldLoader()
        if args.all:
            experts = loader.load_all_experts()
            print(f"Loaded {len(experts)} expert fields: {list(experts.keys())}")
        elif args.expert_id:
            expert = loader.get_expert_field(args.expert_id)
            print(f"Loaded expert field '{args.expert_id}': {type(expert)}")
            if isinstance(expert, dict):
                print(f"  Keys: {list(expert.keys())[:5]}...") # Show first 5 keys
        else:
            print("Usage: --expert-id <id> or --all")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading expert fields: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()