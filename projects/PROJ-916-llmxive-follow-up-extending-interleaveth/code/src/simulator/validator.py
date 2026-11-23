"""
Validator module for detecting ambiguous spatial relationships in scene descriptions.

This module implements logic to identify samples with unclear or contradictory
spatial relationships that should be flagged for exclusion from evaluation.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from src.data_models import SceneGraph, ObjectNode, RelationshipEdge
from src.simulator.parser import SceneDescription

# Common ambiguous spatial prepositions and patterns
AMBIGUOUS_PREPOSITIONS = {
    "near", "close to", "by", "beside", "next to", "around",
    "about", "approximately", "roughly", "somewhere", "nearby"
}

# Patterns that indicate spatial uncertainty
UNCERTAINTY_PATTERNS = [
    r"\b(near|close\s+to|by|beside|next\s+to)\s+\w+\s+(and|or|but)\s+\w+",  # Conflicting relations
    r"\b(approximately|roughly|somewhere)\s+(near|close)",  # Redundant uncertainty
    r"\b(left|right|front|back)\s+of\s+the\s+same\s+(one|object)",  # Self-referential ambiguity
    r"\b(slightly|somewhat|a\s+little)\s+(left|right|above|below)",  # Vague modifiers
]

# Directional relationships that should be precise
PRECISE_DIRECTIONS = {
    "left of", "right of", "above", "below", "on top of", "under",
    "in front of", "behind", "to the left of", "to the right of"
}

@dataclass
class AmbiguityFlag:
    """Represents a detected ambiguity in a scene description."""
    object_id: str
    relationship_type: str
    reason: str
    confidence: float  # 0.0 to 1.0, higher means more certain it's ambiguous
    suggestion: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of validating a scene description for ambiguities."""
    is_valid: bool
    flags: List[AmbiguityFlag]
    excluded: bool
    exclusion_reason: Optional[str] = None
    ambiguity_count: int = 0

def _check_ambiguous_preposition(self, relation: str) -> Tuple[bool, Optional[str]]:
    """Check if a relationship uses an ambiguous preposition."""
    relation_lower = relation.lower()
    for prep in AMBIGUOUS_PREPOSITIONS:
        if prep in relation_lower:
            return True, f"Uses ambiguous preposition: '{prep}'"
    return False, None

def _check_uncertainty_pattern(self, relation: str) -> Tuple[bool, Optional[str]]:
    """Check if a relationship matches uncertainty patterns."""
    for pattern in UNCERTAINTY_PATTERNS:
        if re.search(pattern, relation, re.IGNORECASE):
            return True, f"Matches uncertainty pattern: {pattern}"
    return False, None

def _check_conflicting_directions(self, obj_id: str, relationships: List[RelationshipEdge]) -> List[AmbiguityFlag]:
    """Check for conflicting directional relationships for an object."""
    flags = []
    direction_counts: Dict[str, List[str]] = {}

    for rel in relationships:
        if rel.subject_id == obj_id:
            rel_type_lower = rel.rel_type.lower()
            for direction in PRECISE_DIRECTIONS:
                if direction in rel_type_lower:
                    # Extract the primary direction
                    primary_dir = direction.split()[0] if direction.split() else direction
                    if primary_dir not in direction_counts:
                        direction_counts[primary_dir] = []
                    direction_counts[primary_dir].append(rel.rel_type)

    # Check for contradictions (e.g., both "left of" and "right of" the same reference)
    for direction, relations in direction_counts.items():
        if len(relations) > 1:
            # Check if they reference the same object in conflicting ways
            refs = set()
            for rel_str in relations:
                # Simple heuristic: if multiple precise directions exist for same object
                refs.add(rel_str)
            if len(refs) > 1:
                flags.append(AmbiguityFlag(
                    object_id=obj_id,
                    relationship_type=direction,
                    reason=f"Multiple conflicting directions detected: {', '.join(relations)}",
                    confidence=0.8,
                    suggestion="Specify a single precise direction or remove conflicting relationships"
                ))

    return flags

def _check_object_reference_ambiguity(self, relationships: List[RelationshipEdge]) -> List[AmbiguityFlag]:
    """Check for ambiguous object references in relationships."""
    flags = []
    object_ids = set()

    # Collect all referenced object IDs
    for rel in relationships:
        object_ids.add(rel.subject_id)
        object_ids.add(rel.object_id)

    # Check for vague references like "the same object", "another one", etc.
    vague_refs = ["the same object", "another one", "that object", "this object", "the other"]
    for rel in relationships:
        for vague in vague_refs:
            if vague in rel.rel_type.lower():
                flags.append(AmbiguityFlag(
                    object_id=rel.subject_id,
                    relationship_type=rel.rel_type,
                    reason=f"Ambiguous object reference: '{vague}'",
                    confidence=0.9,
                    suggestion="Use explicit object IDs instead of vague references"
                ))

    return flags

def validate_scene_description(self, scene_desc: SceneDescription, threshold: float = 0.7) -> ValidationResult:
    """
    Validate a scene description for ambiguous spatial relationships.

    Args:
        scene_desc: The scene description to validate
        threshold: Minimum confidence score to flag an ambiguity (default 0.7)

    Returns:
        ValidationResult with flags and exclusion decision
    """
    flags = []

    # Check each object's relationships
    for obj in scene_desc.objects:
        obj_id = obj.id

        # Check for ambiguous prepositions
        for rel in scene_desc.relationships:
            if rel.subject_id == obj_id or rel.object_id == obj_id:
                is_ambig, reason = self._check_ambiguous_preposition(rel.rel_type)
                if is_ambig:
                    flags.append(AmbiguityFlag(
                        object_id=obj_id,
                        relationship_type=rel.rel_type,
                        reason=reason,
                        confidence=0.75
                    ))

                # Check uncertainty patterns
                is_uncertain, unc_reason = self._check_uncertainty_pattern(rel.rel_type)
                if is_uncertain:
                    flags.append(AmbiguityFlag(
                        object_id=obj_id,
                        relationship_type=rel.rel_type,
                        reason=unc_reason,
                        confidence=0.85
                    ))

        # Check for conflicting directions
        conflicting = self._check_conflicting_directions(obj_id, scene_desc.relationships)
        flags.extend(conflicting)

    # Check for vague object references
    ref_flags = self._check_object_reference_ambiguity(scene_desc.relationships)
    flags.extend(ref_flags)

    # Filter flags by confidence threshold
    filtered_flags = [f for f in flags if f.confidence >= threshold]

    # Determine if sample should be excluded
    # Exclude if more than 20% of relationships are ambiguous or if any high-confidence (>=0.9) ambiguity exists
    total_rels = len(scene_desc.relationships)
    should_exclude = False
    exclusion_reason = None

    if total_rels > 0:
        ambiguity_ratio = len(filtered_flags) / total_rels
        if ambiguity_ratio > 0.2:
            should_exclude = True
            exclusion_reason = f"High ambiguity ratio: {ambiguity_ratio:.2%} ({len(filtered_flags)}/{total_rels} relationships)"
        elif any(f.confidence >= 0.9 for f in filtered_flags):
            should_exclude = True
            exclusion_reason = "High-confidence ambiguity detected (>=0.9)"

    return ValidationResult(
        is_valid=len(filtered_flags) == 0,
        flags=filtered_flags,
        excluded=should_exclude,
        exclusion_reason=exclusion_reason,
        ambiguity_count=len(filtered_flags)
    )

def validate_scene_graph(self, scene_graph: SceneGraph, threshold: float = 0.7) -> ValidationResult:
    """
    Validate a SceneGraph model for ambiguous spatial relationships.

    Converts SceneGraph to SceneDescription format for validation.

    Args:
        scene_graph: The SceneGraph to validate
        threshold: Minimum confidence score to flag an ambiguity

    Returns:
        ValidationResult with flags and exclusion decision
    """
    # Convert SceneGraph to SceneDescription
    objects = []
    for node in scene_graph.objects:
        objects.append(ParsedObject(
            id=node.id,
            name=node.name,
            attributes=node.attributes or {}
        ))

    relationships = []
    for edge in scene_graph.relationships:
        relationships.append(ParsedRelationship(
            subject_id=edge.subject_id,
            object_id=edge.object_id,
            rel_type=edge.rel_type
        ))

    scene_desc = SceneDescription(
        objects=objects,
        relationships=relationships,
        metadata={"source": "scene_graph_conversion"}
    )

    return self.validate_scene_description(scene_desc, threshold)

def filter_ambiguous_samples(self, samples: List[SceneDescription], threshold: float = 0.7) -> Tuple[List[SceneDescription], List[SceneDescription]]:
    """
    Filter a list of scene descriptions, separating valid from ambiguous samples.

    Args:
        samples: List of scene descriptions to validate
        threshold: Minimum confidence score to flag an ambiguity

    Returns:
        Tuple of (valid_samples, excluded_samples)
    """
    valid = []
    excluded = []

    for sample in samples:
        result = self.validate_scene_description(sample, threshold)
        if result.excluded:
            excluded.append(sample)
        else:
            valid.append(sample)

    return valid, excluded

def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Generate a summary of validation results.

    Args:
        results: List of ValidationResult objects

    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    if total == 0:
        return {
            "total_samples": 0,
            "valid_count": 0,
            "excluded_count": 0,
            "exclusion_rate": 0.0,
            "total_ambiguities": 0,
            "avg_ambiguities_per_sample": 0.0
        }

    valid_count = sum(1 for r in results if not r.excluded)
    excluded_count = total - valid_count
    total_ambiguities = sum(r.ambiguity_count for r in results)

    return {
        "total_samples": total,
        "valid_count": valid_count,
        "excluded_count": excluded_count,
        "exclusion_rate": excluded_count / total if total > 0 else 0.0,
        "total_ambiguities": total_ambiguities,
        "avg_ambiguities_per_sample": total_ambiguities / total if total > 0 else 0.0,
        "exclusion_reasons": list(set(r.exclusion_reason for r in results if r.exclusion_reason))
    }

# Module-level convenience function
def detect_ambiguous_relationships(scene_desc: SceneDescription, threshold: float = 0.7) -> ValidationResult:
    """
    Convenience function to detect ambiguous spatial relationships in a scene description.

    Args:
        scene_desc: The scene description to validate
        threshold: Minimum confidence score to flag an ambiguity

    Returns:
        ValidationResult with flags and exclusion decision
    """
    validator = AmbiguityValidator()
    return validator.validate_scene_description(scene_desc, threshold)

class AmbiguityValidator:
    """Class-based validator for scene descriptions."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
    
    def validate(self, scene_desc: SceneDescription) -> ValidationResult:
        """Validate a scene description."""
        return validate_scene_description(scene_desc, self.threshold)
    
    def validate_graph(self, scene_graph: SceneGraph) -> ValidationResult:
        """Validate a SceneGraph."""
        return validate_scene_graph(scene_graph, self.threshold)
    
    def filter_samples(self, samples: List[SceneDescription]) -> Tuple[List[SceneDescription], List[SceneDescription]]:
        """Filter samples by ambiguity."""
        return filter_ambiguous_samples(samples, self.threshold)
    
    def get_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get validation summary."""
        return get_validation_summary(results)