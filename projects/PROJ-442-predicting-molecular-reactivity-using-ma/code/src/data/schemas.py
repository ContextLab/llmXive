"""
Base data schemas and validation helpers for the molecular reactivity pipeline.

This module defines strict data structures for ReactionRecord, FeatureVector,
and ModelResult, along with validation functions to ensure data integrity
before processing.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import re
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


@dataclass
class ReactionRecord:
    """
    Represents a single chemical reaction record from the source data.

    Attributes:
        reaction_id: Unique identifier for the reaction (e.g., from USPTO).
        reactants_smiles: SMILES string of the reactants.
        products_smiles: SMILES string of the products.
        reagents_smiles: Optional SMILES string of reagents.
        reaction_type: Classification of the reaction (e.g., 'SN1', 'SN2', 'Diels-Alder').
        yield_pct: Experimental yield percentage (0.0 to 100.0).
        success_flag: Boolean indicating if the reaction was successful (1/0 or True/False).
        source_url: URL or reference to the original data source.
        raw_data: Dictionary containing the original raw data payload for provenance.
        errors: List of validation or parsing errors encountered.
    """
    reaction_id: str
    reactants_smiles: str
    products_smiles: str
    reagents_smiles: Optional[str] = None
    reaction_type: Optional[str] = None
    yield_pct: Optional[float] = None
    success_flag: Optional[bool] = None
    source_url: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if the record has no critical errors."""
        return len(self.errors) == 0

    def has_target(self) -> bool:
        """Check if a target variable (yield or success flag) is present."""
        return self.yield_pct is not None or self.success_flag is not None


@dataclass
class FeatureVector:
    """
    Represents a numerical feature vector derived from a molecular reaction.

    Attributes:
        reaction_id: Link to the source ReactionRecord.
        features: Dictionary mapping feature names to their float values.
        metadata: Additional metadata about the feature extraction process.
    """
    reaction_id: str
    features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_array(self) -> List[float]:
        """Convert features to a list of floats, preserving insertion order."""
        return list(self.features.values())

    def feature_names(self) -> List[str]:
        """Return the list of feature names in order."""
        return list(self.features.keys())


@dataclass
class ModelResult:
    """
    Represents the output of a model prediction or training run.

    Attributes:
        reaction_id: Link to the source ReactionRecord.
        predicted_value: The model's predicted yield or probability.
        actual_value: The ground truth value (if available for evaluation).
        prediction_confidence: Optional confidence score (e.g., from XGBoost).
        model_version: Identifier for the model version used.
        timestamp: Timestamp of the prediction.
        error: Any error message if prediction failed.
    """
    reaction_id: str
    predicted_value: float
    actual_value: Optional[float] = None
    prediction_confidence: Optional[float] = None
    model_version: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if the result contains a valid prediction and no errors."""
        return self.error is None and self.predicted_value is not None


def validate_smiles(smiles: str) -> bool:
    """
    Basic validation for SMILES strings using regex.
    Note: RDKit is the definitive validator, but this provides a quick check.

    Args:
        smiles: The SMILES string to validate.

    Returns:
        True if the string matches basic SMILES patterns, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    # Basic pattern: allows atoms, bonds, rings, branches.
    # This is a heuristic; RDKit parsing is required for full validation.
    pattern = r'^[A-Za-z0-9@\-\.%\$\(\)\[\]\{\}\/\+\=]*$'
    return bool(re.match(pattern, smiles))


def validate_reaction_record(record: Dict[str, Any]) -> ReactionRecord:
    """
    Validates and constructs a ReactionRecord from a raw dictionary.

    Args:
        record: Raw dictionary from the ingestion source.

    Returns:
        A ReactionRecord instance, populated with errors if validation fails.
    """
    errors = []

    # Extract ID
    rid = record.get('reaction_id') or record.get('id') or record.get('rxn_id')
    if not rid:
        errors.append("Missing reaction_id")
        rid = "unknown"

    # Extract SMILES
    reactants = record.get('reactants_smiles') or record.get('reactants')
    products = record.get('products_smiles') or record.get('products')

    if not reactants:
        errors.append("Missing reactants_smiles")
    if not products:
        errors.append("Missing products_smiles")

    # Validate SMILES format (heuristic)
    if reactants and not validate_smiles(reactants):
        errors.append(f"Invalid reactants SMILES format: {reactants[:20]}...")
    if products and not validate_smiles(products):
        errors.append(f"Invalid products SMILES format: {products[:20]}...")

    # Extract Target Variables
    yield_val = record.get('yield_pct') or record.get('yield')
    success = record.get('success_flag') or record.get('success')

    if yield_val is not None:
        try:
            yield_val = float(yield_val)
            if not (0.0 <= yield_val <= 100.0):
                errors.append(f"Yield out of range: {yield_val}")
        except (ValueError, TypeError):
            errors.append(f"Invalid yield value: {yield_val}")
            yield_val = None

    if success is not None:
        if isinstance(success, bool):
            pass
        elif isinstance(success, int):
            success = bool(success)
        elif isinstance(success, str):
            success = success.lower() in ('true', '1', 'yes')
        else:
            errors.append(f"Invalid success_flag type: {type(success)}")
            success = None

    return ReactionRecord(
        reaction_id=str(rid),
        reactants_smiles=reactants or "",
        products_smiles=products or "",
        reagents_smiles=record.get('reagents_smiles'),
        reaction_type=record.get('reaction_type'),
        yield_pct=yield_val,
        success_flag=success,
        source_url=record.get('source_url'),
        raw_data=record,
        errors=errors
    )


def validate_feature_vector(vec: FeatureVector) -> bool:
    """
    Validates that a FeatureVector has no NaN/Inf values and is not empty.

    Args:
        vec: The FeatureVector to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not vec.features:
        logger.warning(f"FeatureVector for {vec.reaction_id} is empty.")
        return False

    for name, val in vec.features.items():
        if val is None:
            logger.error(f"Feature {name} is None in {vec.reaction_id}")
            return False
        if not isinstance(val, (int, float)):
            logger.error(f"Feature {name} is not numeric in {vec.reaction_id}")
            return False
        if val != val:  # NaN check
            logger.error(f"Feature {name} is NaN in {vec.reaction_id}")
            return False
        if abs(val) == float('inf'):
            logger.error(f"Feature {name} is Inf in {vec.reaction_id}")
            return False

    return True


def validate_model_result(result: ModelResult) -> bool:
    """
    Validates a ModelResult.

    Args:
        result: The ModelResult to validate.

    Returns:
        True if valid, False otherwise.
    """
    if result.error:
        return False
    if result.predicted_value is None:
        return False
    if result.predicted_value != result.predicted_value:  # NaN check
        return False
    return True
