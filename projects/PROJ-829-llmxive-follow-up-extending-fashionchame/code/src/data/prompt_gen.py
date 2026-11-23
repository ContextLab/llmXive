"""
Prompt Generation Module for DeepFashion2.

Implements FR-008: Blind metadata-to-text prompt generation.
Converts dataset attributes into natural language prompts for VLM verification.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from sibling modules as per API surface
from src.data.loader import load_config


def load_settings(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load settings from YAML configuration.

    Args:
        config_path: Path to settings.yaml. If None, attempts to find
                     it in the standard project location.

    Returns:
        Dictionary of configuration settings.
    """
    return load_config(config_path)


def normalize_attribute(attr_name: str) -> str:
    """
    Normalize an attribute name for consistent processing.

    Args:
        attr_name: Raw attribute name from dataset.

    Returns:
        Normalized attribute name (lowercase, underscores replaced with spaces).
    """
    if not attr_name:
        return ""
    
    # Convert to lowercase
    normalized = attr_name.lower()
    
    # Replace underscores and hyphens with spaces
    normalized = normalized.replace("_", " ").replace("-", " ")
    
    # Remove extra whitespace
    normalized = " ".join(normalized.split())
    
    return normalized


def generate_prompt(attributes: List[Dict[str, Any]], 
                    garment_type: Optional[str] = None,
                    style: Optional[str] = None) -> str:
    """
    Generate a natural language prompt from garment attributes.

    Args:
        attributes: List of attribute dictionaries with 'name' and 'value'.
        garment_type: Optional garment type (e.g., "dress", "shirt").
        style: Optional style descriptor.

    Returns:
        Natural language prompt string.
    """
    parts = []
    
    # Add garment type if available
    if garment_type:
        parts.append(f"a {normalize_attribute(garment_type)}")
    else:
        parts.append("a garment")
    
    # Add style if available
    if style:
        parts.append(f"with {normalize_attribute(style)} style")
    
    # Process attributes
    attribute_descriptions = []
    for attr in attributes:
        if not isinstance(attr, dict):
            continue
        
        name = attr.get("name", "")
        value = attr.get("value", "")
        
        if not name:
            continue
        
        normalized_name = normalize_attribute(name)
        
        if value:
            attribute_descriptions.append(f"{normalized_name} {normalize_attribute(value)}")
        else:
            attribute_descriptions.append(normalized_name)
    
    if attribute_descriptions:
        if len(attribute_descriptions) == 1:
            parts.append(f"that is {attribute_descriptions[0]}")
        else:
            # Join with commas and 'and'
            last = attribute_descriptions.pop()
            parts.append(f"that is {', '.join(attribute_descriptions)} and {last}")
    
    return " ".join(parts) + "."


def generate_prompts_batch(samples: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate prompts for a batch of samples.

    Args:
        samples: List of dataset samples.

    Returns:
        List of dictionaries with 'image_id' and 'prompt' keys.
    """
    results = []
    
    for sample in samples:
        image_id = sample.get("image_id", sample.get("id", "unknown"))
        attributes = sample.get("attributes", sample.get("attr", []))
        garment_type = sample.get("category", sample.get("garment_type"))
        style = sample.get("style")
        
        prompt = generate_prompt(attributes, garment_type, style)
        
        results.append({
            "image_id": image_id,
            "prompt": prompt,
            "original_attributes": attributes
        })
    
    return results


def save_prompts_to_file(prompts: List[Dict[str, str]], output_path: Path):
    """
    Save generated prompts to a JSON file.

    Args:
        prompts: List of prompt dictionaries.
        output_path: Path to output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)


def main():
    """
    Main entry point for prompt generation script.
    """
    config = load_config()
    
    # Get paths from config
    output_dir = Path(config.get("paths", {}).get("processed", "data/processed"))
    prompts_path = output_dir / "generated_prompts.json"
    
    print("Prompt Generation Module initialized.")
    print(f"Configuration loaded from: {config.get('config_path', 'default')}")
    print(f"Prompts will be saved to: {prompts_path}")
    
    # Example usage demonstration
    sample_attributes = [
        {"name": "color", "value": "red"},
        {"name": "pattern", "value": "floral"},
        {"name": "texture", "value": "silk"}
    ]
    
    example_prompt = generate_prompt(sample_attributes, "dress", "summer")
    print(f"\nExample prompt generation:")
    print(f"Attributes: {sample_attributes}")
    print(f"Generated prompt: '{example_prompt}'")


if __name__ == "__main__":
    main()
