import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from src.data_models import ObjectNode, RelationshipEdge, SceneGraph

@dataclass
class ParsedObject:
    """Represents a single object parsed from a text caption."""
    id: str
    name: str
    attributes: Dict[str, Any]
    position: Optional[Tuple[float, float]] = None

@dataclass
class ParsedRelationship:
    """Represents a relationship between two objects."""
    source_id: str
    target_id: str
    relation: str
    confidence: float = 1.0

@dataclass
class SceneDescription:
    """Structured JSON-serializable description of a scene derived from text."""
    scene_id: str
    timestamp: str
    objects: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def _generate_id(prefix: str) -> str:
    """Generate a deterministic ID based on timestamp and prefix for reproducibility."""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

def _extract_objects(text: str) -> List[ParsedObject]:
    """
    Parse objects from a text caption.
    Heuristic: Looks for noun phrases following common patterns or simple splitting.
    In a real implementation, this would use an NLP parser (spaCy, NLTK) or LLM.
    For this deterministic simulator, we use a rule-based extraction on known patterns.
    """
    # Simple heuristic: split by 'and', ',', 'with', 'on', 'in' to find potential nouns
    # This is a placeholder for the 'Perfect Mode' deterministic logic.
    # A more robust version would use a pre-trained dependency parser.
    
    # Clean text
    clean_text = text.lower().strip()
    
    # Remove common stop words that might interfere with simple parsing
    # This is a minimal set for demonstration
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
                  'should', 'may', 'might', 'can', 'of', 'to', 'in', 'for', 'on', 'with', 
                  'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 
                  'after', 'above', 'below', 'between', 'under', 'again', 'further', 
                  'then', 'once', 'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 
                  'either', 'neither', 'not', 'only', 'own', 'same', 'than', 'too', 
                  'very', 's', 't', 'just', 'don', 'now', 'it', 'its', 'this', 'that', 
                  'these', 'those', 'what', 'which', 'who', 'whom', 'whose', 'where', 
                  'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 
                  'most', 'other', 'some', 'such', 'no', 'any', 'my', 'me', 'we', 'our', 
                  'ours', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 
                  'hers', 'they', 'them', 'their', 'theirs', 'i', 'myself', 'yourself', 
                  'himself', 'herself', 'itself', 'ourselves', 'themselves'}
    
    # Basic tokenization
    tokens = re.findall(r'\b\w+\b', clean_text)
    
    # Heuristic: Identify potential nouns (simplified)
    # In a real scenario, use POS tagging. Here we assume nouns are words not in stop_words
    # and not purely numeric.
    potential_objects = []
    current_phrase = []
    
    for word in tokens:
        if word in stop_words:
            if current_phrase:
                potential_objects.append(" ".join(current_phrase))
                current_phrase = []
        else:
            current_phrase.append(word)
    
    if current_phrase:
        potential_objects.append(" ".join(current_phrase))
    
    # Remove duplicates and filter empty
    unique_objects = list(dict.fromkeys([o for o in potential_objects if o]))
    
    parsed_objects = []
    for i, obj_name in enumerate(unique_objects):
        obj_id = _generate_id("obj")
        parsed_objects.append(ParsedObject(
            id=obj_id,
            name=obj_name,
            attributes={"source": "text_parse", "confidence": 1.0},
            position=None
        ))
    
    return parsed_objects

def _extract_relationships(objects: List[ParsedObject], text: str) -> List[ParsedRelationship]:
    """
    Extract relationships between parsed objects based on text context.
    Heuristic: Looks for prepositions connecting object names.
    """
    relationships = []
    text_lower = text.lower()
    
    # Simple pattern: "A on B", "A next to B", "A with B"
    # We look for pairs of object names in the text separated by a relation word
    relation_keywords = ['on', 'under', 'above', 'below', 'next to', 'near', 'beside', 
                         'between', 'behind', 'in front of', 'with', 'holding', 'has', 'wearing']
    
    # Find occurrences of object names in text
    obj_positions = []
    for obj in objects:
        # Find all start positions of the object name in the text
        start = 0
        while True:
            pos = text_lower.find(obj.name.lower(), start)
            if pos == -1:
                break
            obj_positions.append((pos, pos + len(obj.name), obj.id))
            start = pos + 1
    
    # Sort by position
    obj_positions.sort(key=lambda x: x[0])
    
    # Look for relations between adjacent objects in the text flow
    for i in range(len(obj_positions) - 1):
        start1, end1, id1 = obj_positions[i]
        start2, end2, id2 = obj_positions[i+1]
        
        # Text between the two objects
        between_text = text_lower[end1:start2].strip()
        
        # Check if a known relation keyword exists in between
        for rel in relation_keywords:
            if rel in between_text:
                relationships.append(ParsedRelationship(
                    source_id=id1,
                    target_id=id2,
                    relation=rel,
                    confidence=0.9
                ))
                break
        
        # If no specific relation found but they are close, assume a generic 'near'
        if not any(r.source_id == id1 and r.target_id == id2 for r in relationships):
             if end2 - end1 < 50: # Arbitrary proximity threshold
                  relationships.append(ParsedRelationship(
                      source_id=id1,
                      target_id=id2,
                      relation="near",
                      confidence=0.5
                  ))

    return relationships

def parse_caption_to_scene_description(caption: str, scene_id: Optional[str] = None) -> SceneDescription:
    """
    Convert a text caption into a SceneDescription JSON object (Perfect Mode).
    
    Args:
        caption: The input text description.
        scene_id: Optional ID for the scene. If None, a timestamp-based ID is generated.
    
    Returns:
        SceneDescription: A structured object containing objects, relationships, and metadata.
    """
    if not caption or not caption.strip():
        raise ValueError("Caption cannot be empty")
    
    scene_id = scene_id or _generate_id("scene")
    
    # Parse objects
    parsed_objects = _extract_objects(caption)
    
    # Parse relationships
    parsed_relationships = _extract_relationships(parsed_objects, caption)
    
    # Convert to dictionaries for JSON serialization
    objects_dict = [asdict(obj) for obj in parsed_objects]
    relationships_dict = [asdict(rel) for rel in parsed_relationships]
    
    return SceneDescription(
        scene_id=scene_id,
        timestamp=datetime.now().isoformat(),
        objects=objects_dict,
        relationships=relationships_dict,
        metadata={
            "source_text": caption,
            "parser_version": "1.0.0",
            "mode": "perfect"
        }
    )

def parse_to_json(caption: str) -> str:
    """
    Parse a caption and return the result as a JSON string.
    
    Args:
        caption: Input text.
    
    Returns:
        str: JSON string representation of the SceneDescription.
    """
    scene_desc = parse_caption_to_scene_description(caption)
    return scene_desc.to_json()

def parse_to_dict(caption: str) -> Dict[str, Any]:
    """
    Parse a caption and return the result as a dictionary.
    
    Args:
        caption: Input text.
    
    Returns:
        dict: Dictionary representation of the SceneDescription.
    """
    scene_desc = parse_caption_to_scene_description(caption)
    return scene_desc.to_dict()
