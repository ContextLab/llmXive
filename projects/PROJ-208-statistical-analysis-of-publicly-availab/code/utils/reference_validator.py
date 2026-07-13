"""
Reference-Validator Agent for llmXive pipeline.

Implements Constitution Principle II:
1. Checkpoint execution verification at artifact write
2. Advancement-Evaluator logic
3. research_review -> research_accepted state transition validation
"""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

class CheckpointVerificationError(Exception):
    """Raised when checkpoint verification fails."""
    pass

class AdvancementEvaluator:
    """
    Evaluates whether a research artifact meets criteria for advancement
    from one state to another (e.g., research_review -> research_accepted).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.thresholds = self.config.get('advancement_thresholds', {
            'min_completeness': 0.95,
            'max_error_rate': 0.05,
            'required_fields': ['checksum', 'timestamp', 'artifact_path']
        })
    
    def evaluate(self, artifact_metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate if artifact meets advancement criteria.
        
        Returns:
            Tuple of (is_advanced, reason)
        """
        # Check required fields
        for field in self.thresholds['required_fields']:
            if field not in artifact_metadata:
                return False, f"Missing required field: {field}"
        
        # Check completeness threshold
        completeness = artifact_metadata.get('completeness', 0.0)
        if completeness < self.thresholds['min_completeness']:
            return False, f"Completeness {completeness:.2f} below threshold {self.thresholds['min_completeness']}"
        
        # Check error rate
        error_rate = artifact_metadata.get('error_rate', 0.0)
        if error_rate > self.thresholds['max_error_rate']:
            return False, f"Error rate {error_rate:.2f} exceeds threshold {self.thresholds['max_error_rate']}"
        
        # Check checksum validity
        if not artifact_metadata.get('checksum'):
            return False, "Missing checksum"
        
        return True, "Advancement criteria met"

class ReferenceValidator:
    """
    Main validator class that orchestrates checkpoint verification,
    advancement evaluation, and state transition validation.
    """
    
    def __init__(self, project_root: Path, config: Optional[Dict[str, Any]] = None):
        self.project_root = Path(project_root)
        self.config = config or {}
        self.state_dir = self.project_root / "state"
        self.data_dir = self.project_root / "data"
        self.advancement_evaluator = AdvancementEvaluator(self.config.get('advancement', {}))
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_checksum(self, file_path: Path) -> str:
        """Compute SHA-256 checksum of a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def verify_checkpoint(self, artifact_path: Path, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify checkpoint execution at artifact write.
        
        Args:
            artifact_path: Path to the artifact file
            expected_checksum: Optional expected checksum for validation
        
        Returns:
            Dict containing verification results
        
        Raises:
            CheckpointVerificationError: If verification fails
        """
        if not artifact_path.exists():
            raise CheckpointVerificationError(f"Artifact not found: {artifact_path}")
        
        # Compute actual checksum
        actual_checksum = self.compute_checksum(artifact_path)
        
        # Validate against expected if provided
        if expected_checksum and actual_checksum != expected_checksum:
            raise CheckpointVerificationError(
                f"Checksum mismatch. Expected: {expected_checksum}, Got: {actual_checksum}"
            )
        
        # Gather metadata
        stat = artifact_path.stat()
        verification_result = {
            'artifact_path': str(artifact_path),
            'checksum': actual_checksum,
            'file_size': stat.st_size,
            'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'verification_status': 'passed',
            'verification_time': datetime.now().isoformat()
        }
        
        # Log to state file
        self._log_checkpoint(verification_result)
        
        return verification_result
    
    def _log_checkpoint(self, result: Dict[str, Any]) -> None:
        """Log checkpoint verification to state file."""
        checkpoint_log = self.state_dir / "checkpoint_log.json"
        
        if checkpoint_log.exists():
            with open(checkpoint_log, 'r') as f:
                logs = json.load(f)
        else:
            logs = {'checkpoints': []}
        
        logs['checkpoints'].append(result)
        
        with open(checkpoint_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def validate_state_transition(
        self, 
        from_state: str, 
        to_state: str, 
        artifact_metadata: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate state transition (e.g., research_review -> research_accepted).
        
        Args:
            from_state: Current state
            to_state: Target state
            artifact_metadata: Metadata about the artifact being transitioned
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Define valid transitions
        valid_transitions = {
            'research_review': ['research_accepted', 'research_rejected'],
            'research_accepted': ['published'],
            'draft': ['research_review'],
            'data_collection': ['preprocessing', 'archived']
        }
        
        if from_state not in valid_transitions:
            return False, f"Unknown source state: {from_state}"
        
        if to_state not in valid_transitions[from_state]:
            return False, f"Invalid transition: {from_state} -> {to_state}"
        
        # Use AdvancementEvaluator for quality checks
        if to_state == 'research_accepted':
            is_advanced, reason = self.advancement_evaluator.evaluate(artifact_metadata)
            if not is_advanced:
                return False, f"Advancement criteria not met: {reason}"
        
        # Update state file
        self._update_state(from_state, to_state, artifact_metadata)
        
        return True, f"Transition {from_state} -> {to_state} validated"
    
    def _update_state(
        self, 
        from_state: str, 
        to_state: str, 
        artifact_metadata: Dict[str, Any]
    ) -> None:
        """Update the project state file."""
        state_file = self.state_dir / "project_state.json"
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                state_data = json.load(f)
        else:
            state_data = {'transitions': [], 'current_state': None}
        
        transition_record = {
            'from_state': from_state,
            'to_state': to_state,
            'timestamp': datetime.now().isoformat(),
            'artifact_metadata': artifact_metadata
        }
        
        state_data['transitions'].append(transition_record)
        state_data['current_state'] = to_state
        state_data['last_updated'] = datetime.now().isoformat()
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)

def create_validator(project_root: Path, config: Optional[Dict[str, Any]] = None) -> ReferenceValidator:
    """Factory function to create a ReferenceValidator instance."""
    return ReferenceValidator(project_root, config)

def verify_checkpoint(artifact_path: Path, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to verify a checkpoint."""
    validator = create_validator(Path.cwd())
    return validator.verify_checkpoint(artifact_path, expected_checksum)

def validate_state_transition(
    from_state: str, 
    to_state: str, 
    artifact_metadata: Dict[str, Any],
    project_root: Optional[Path] = None
) -> Tuple[bool, str]:
    """Convenience function to validate a state transition."""
    root = project_root or Path.cwd()
    validator = create_validator(root)
    return validator.validate_state_transition(from_state, to_state, artifact_metadata)
