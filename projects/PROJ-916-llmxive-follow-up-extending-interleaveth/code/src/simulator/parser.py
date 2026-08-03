"""
Parser module for converting text captions into structured SceneDescription JSON objects.

Implements Perfect Mode parsing: deterministic conversion of text prompts into
SceneDescription objects with objects, relationships, and attributes.
"""
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from src.data_models import ObjectNode, RelationshipEdge, SceneGraph
from src.utils.logging import track_step


@dataclass
class ParsedObject:
    """Intermediate representation of a parsed object."""
    name: str
    attributes: Dict[str, Any]
    bounding_box: Optional[Tuple[float, float, float, float]] = None

@dataclass
class ParsedRelationship:
    """Intermediate representation of a parsed relationship."""
    subject: str
    predicate: str
    object_ref: str
    confidence: float = 1.0

@dataclass
class SceneDescription:
    """
    Structured JSON-compatible representation of a scene.
    Matches the output schema expected by the simulator.
    """
    objects: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    attributes: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    def to_scene_graph(self) -> SceneGraph:
        """Convert to SceneGraph data model."""
        object_nodes = []
        for obj in self.objects:
            node = ObjectNode(
                id=obj.get("id"),
                name=obj["name"],
                attributes=obj.get("attributes", {}),
                bounding_box=obj.get("bounding_box")
            )
            object_nodes.append(node)

        relationship_edges = []
        for rel in self.relationships:
            edge = RelationshipEdge(
                source=rel["subject"],
                target=rel["object_ref"],
                predicate=rel["predicate"],
                confidence=rel.get("confidence", 1.0)
            )
            relationship_edges.append(edge)

        return SceneGraph(
            objects=object_nodes,
            relationships=relationship_edges,
            attributes=self.attributes,
            metadata=self.metadata
        )


# Pattern definitions for parsing
OBJECT_PATTERN = re.compile(
    r'\b(the|a|an)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:is|are|has|with|on|in|at|by|near|next to|behind|in front of|under|over|above|below|between|among|inside|outside|around|through|across|along|against|upon|within|without|toward|towards|into|onto|upon|over|under|above|below|beside|behind|before|after|during|while|since|until|from|to|for|of|with|without|against|among|throughout|toward|upon|within|without)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
    re.IGNORECASE
)

SIMPLE_OBJECT_PATTERN = re.compile(
    r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:is|are|has|with|on|in|at|by|near|next to|behind|in front of|under|over|above|below|between|among|inside|outside|around|through|across|along|against|upon|within|without|toward|towards|into|onto|upon|over|under|above|below|beside|behind|before|after|during|while|since|until|from|to|for|of|with|without|against|among|throughout|toward|upon|within|without)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)',
    re.IGNORECASE
)

ATTRIBUTE_PATTERN = re.compile(
    r'\b(\w+)\s+(?:is|are|seems|appears|looks|feels|smells|tastes|becomes|remains|stays|keeps|continues|grows|turns|proves|turns out to be|ends up being|comes to be|gets|gets to be|becomes|becomes more|becomes less|becomes increasingly|becomes progressively|becomes gradually|becomes increasingly more|becomes increasingly less|becomes progressively more|becomes progressively less|becomes gradually more|becomes gradually less|becomes increasingly increasingly|becomes increasingly increasingly more|becomes increasingly increasingly less|becomes progressively progressively|becomes progressively progressively more|becomes progressively progressively less|becomes gradually gradually|becomes gradually gradually more|becomes gradually gradually less)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\b',
    re.IGNORECASE
)

SIMPLE_ATTRIBUTE_PATTERN = re.compile(
    r'\b([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:is|are|seems|appears|looks|feels|smells|tastes|becomes|remains|stays|keeps|continues|grows|turns|proves|turns out to be|ends up being|comes to be|gets|gets to be|becomes|becomes more|becomes less|becomes increasingly|becomes progressively|becomes gradually|becomes increasingly more|becomes increasingly less|becomes progressively more|becomes progressively less|becomes gradually more|becomes gradually less|becomes increasingly increasingly|becomes increasingly increasingly more|becomes increasingly increasingly less|becomes progressively progressively|becomes progressively progressively more|becomes progressively progressively less|becomes gradually gradually|becomes gradually gradually more|becomes gradually gradually less)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\b',
    re.IGNORECASE
)


def parse_caption_to_scene_description(caption: str, seed: Optional[int] = None) -> SceneDescription:
    """
    Parse a text caption into a structured SceneDescription object (Perfect Mode).
    
    This function performs deterministic parsing of natural language captions into
    structured scene descriptions containing objects, relationships, and attributes.
    
    Args:
        caption: Natural language text describing a scene.
        seed: Optional random seed for reproducibility (not used in Perfect Mode).
    
    Returns:
        SceneDescription: Structured representation of the parsed scene.
    
    Raises:
        ValueError: If the caption cannot be parsed into a valid scene description.
    """
    if not caption or not isinstance(caption, str):
        raise ValueError("Caption must be a non-empty string")
    
    caption = caption.strip()
    if not caption:
        raise ValueError("Caption cannot be empty after stripping whitespace")
    
    with track_step("parser", "parse_caption", {"caption_length": len(caption)}):
        # Extract objects
        objects = _extract_objects(caption)
        
        # Extract relationships
        relationships = _extract_relationships(caption, objects)
        
        # Extract attributes
        attributes = _extract_attributes(caption, objects)
        
        # Build metadata
        metadata = {
            "source": "text_caption",
            "parsed_at": datetime.now().isoformat(),
            "caption_length": len(caption),
            "object_count": len(objects),
            "relationship_count": len(relationships),
            "attribute_count": len(attributes)
        }
        
        scene_desc = SceneDescription(
            objects=objects,
            relationships=relationships,
            attributes=attributes,
            metadata=metadata
        )
        
        return scene_desc


def _extract_objects(caption: str) -> List[Dict[str, Any]]:
    """Extract objects from the caption."""
    objects = []
    seen_names = set()
    object_id = 0
    
    # Simple object extraction: look for nouns that are likely objects
    words = re.findall(r'\b([a-zA-Z]+)\b', caption)
    
    # Common object nouns to look for
    object_nouns = {
        'person', 'man', 'woman', 'child', 'boy', 'girl', 'baby',
        'dog', 'cat', 'bird', 'fish', 'horse', 'cow', 'sheep', 'pig',
        'car', 'bus', 'train', 'plane', 'boat', 'bicycle', 'motorcycle',
        'table', 'chair', 'sofa', 'bed', 'desk', 'shelf', 'cabinet',
        'computer', 'laptop', 'phone', 'tv', 'monitor', 'camera',
        'book', 'newspaper', 'magazine', 'paper', 'pen', 'pencil',
        'cup', 'bowl', 'plate', 'spoon', 'fork', 'knife', 'glass',
        'tree', 'flower', 'grass', 'plant', 'bush', 'leaf', 'fruit',
        'building', 'house', 'apartment', 'office', 'store', 'school',
        'road', 'street', 'sidewalk', 'bridge', 'fence', 'wall',
        'sky', 'cloud', 'sun', 'moon', 'star', 'rain', 'snow',
        'water', 'river', 'lake', 'ocean', 'sea', 'beach', 'sand',
        'mountain', 'hill', 'valley', 'forest', 'field', 'garden',
        'room', 'kitchen', 'bathroom', 'bedroom', 'living room', 'dining room',
        'door', 'window', 'floor', 'ceiling', 'roof', 'stairs', 'elevator',
        'light', 'lamp', 'clock', 'watch', 'mirror', 'picture', 'painting',
        'clothes', 'shirt', 'pants', 'dress', 'skirt', 'jacket', 'coat',
        'shoe', 'boot', 'hat', 'glove', 'scarf', 'tie', 'belt',
        'food', 'meat', 'vegetable', 'bread', 'rice', 'pasta', 'soup',
        'animal', 'wildlife', 'pet', 'livestock', 'insect', 'bug'
    }
    
    # Extract potential objects
    for word in words:
        word_lower = word.lower()
        if word_lower in object_nouns and word_lower not in seen_names:
            seen_names.add(word_lower)
            obj = {
                "id": f"obj_{object_id}",
                "name": word_lower,
                "attributes": {},
                "bounding_box": None
            }
            objects.append(obj)
            object_id += 1
    
    # If no objects found, create a generic one
    if not objects:
        objects.append({
            "id": "obj_0",
            "name": "scene",
            "attributes": {},
            "bounding_box": None
        })
    
    return objects


def _extract_relationships(caption: str, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract relationships from the caption."""
    relationships = []
    object_names = {obj["name"] for obj in objects}
    
    # Prepositions that indicate relationships
    prepositions = [
        'on', 'in', 'at', 'by', 'near', 'next to', 'behind', 'in front of',
        'under', 'over', 'above', 'below', 'between', 'among', 'inside',
        'outside', 'around', 'through', 'across', 'along', 'against', 'upon',
        'within', 'without', 'toward', 'towards', 'into', 'onto', 'beside',
        'before', 'after', 'during', 'while', 'since', 'until', 'from', 'to',
        'for', 'of', 'with', 'without', 'against', 'among', 'throughout'
    ]
    
    # Simple relationship extraction
    words = caption.lower().split()
    i = 0
    while i < len(words) - 2:
        # Look for patterns like "noun preposition noun"
        if words[i] in object_names:
            for preposition in prepositions:
                if words[i:i+len(preposition.split())] == preposition.split():
                    # Check if the word after preposition is an object
                    end_idx = i + len(preposition.split())
                    if end_idx < len(words) and words[end_idx] in object_names:
                        rel = {
                            "subject": words[i],
                            "predicate": preposition,
                            "object_ref": words[end_idx],
                            "confidence": 1.0
                        }
                        # Avoid duplicates
                        if rel not in relationships:
                            relationships.append(rel)
                    break
        i += 1
    
    return relationships


def _extract_attributes(caption: str, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract attributes from the caption."""
    attributes = {}
    
    # Adjectives that could be attributes
    adjectives = {
        'big', 'small', 'large', 'tiny', 'huge', 'tiny', 'fat', 'thin',
        'tall', 'short', 'long', 'wide', 'narrow', 'high', 'low',
        'round', 'square', 'rectangular', 'oval', 'triangular', 'circular',
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink',
        'black', 'white', 'gray', 'grey', 'brown', 'beige', 'silver', 'gold',
        'happy', 'sad', 'angry', 'excited', 'calm', 'quiet', 'loud',
        'fast', 'slow', 'quick', 'rapid', 'steady', 'smooth', 'rough',
        'hard', 'soft', 'heavy', 'light', 'thick', 'thin', 'deep', 'shallow',
        'old', 'new', 'young', 'fresh', 'stale', 'clean', 'dirty',
        'wet', 'dry', 'hot', 'cold', 'warm', 'cool', 'freezing', 'boiling',
        'bright', 'dark', 'dim', 'glowing', 'shining', 'sparkling',
        'beautiful', 'ugly', 'pretty', 'handsome', 'attractive', 'hideous',
        'interesting', 'boring', 'funny', 'serious', 'strange', 'normal',
        'safe', 'dangerous', 'risky', 'secure', 'stable', 'unstable',
        'strong', 'weak', 'powerful', 'fragile', 'durable', 'temporary',
        'permanent', 'fixed', 'mobile', 'static', 'dynamic', 'active', 'passive',
        'open', 'closed', 'empty', 'full', 'partial', 'complete', 'broken',
        'working', 'functional', 'defective', 'damaged', 'intact', 'whole',
        'single', 'multiple', 'many', 'few', 'several', 'some', 'all', 'none'
    }
    
    words = caption.lower().split()
    for word in words:
        if word in adjectives:
            # Try to associate with nearby objects
            for obj in objects:
                if obj["name"] in words:
                    obj_idx = words.index(obj["name"])
                    word_idx = words.index(word)
                    if abs(obj_idx - word_idx) <= 2:
                        # This is a rough heuristic
                        if "color" not in obj["attributes"]:
                            obj["attributes"]["color"] = word
                        elif "size" not in obj["attributes"]:
                            obj["attributes"]["size"] = word
                        elif "emotion" not in obj["attributes"]:
                            obj["attributes"]["emotion"] = word
                        else:
                            obj["attributes"]["general"] = word
    
    # Add global attributes if present
    if "sunny" in caption.lower():
        attributes["weather"] = "sunny"
    if "rainy" in caption.lower() or "raining" in caption.lower():
        attributes["weather"] = "rainy"
    if "cloudy" in caption.lower():
        attributes["weather"] = "cloudy"
    if "night" in caption.lower():
        attributes["time"] = "night"
    elif "morning" in caption.lower():
        attributes["time"] = "morning"
    elif "afternoon" in caption.lower():
        attributes["time"] = "afternoon"
    elif "evening" in caption.lower():
        attributes["time"] = "evening"
    
    return attributes


def parse_to_json(caption: str, seed: Optional[int] = None) -> str:
    """
    Parse a caption and return the result as a JSON string.
    
    Args:
        caption: Natural language text describing a scene.
        seed: Optional random seed for reproducibility.
    
    Returns:
        str: JSON string representation of the scene description.
    """
    scene_desc = parse_caption_to_scene_description(caption, seed)
    return scene_desc.to_json()


def parse_to_dict(caption: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Parse a caption and return the result as a dictionary.
    
    Args:
        caption: Natural language text describing a scene.
        seed: Optional random seed for reproducibility.
    
    Returns:
        Dict[str, Any]: Dictionary representation of the scene description.
    """
    scene_desc = parse_caption_to_scene_description(caption, seed)
    return scene_desc.to_dict()