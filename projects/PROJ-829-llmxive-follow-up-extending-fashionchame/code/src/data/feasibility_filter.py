import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import yaml

import torch
from transformers import BlipForConditionalGeneration, BlipProcessor
from datasets import load_dataset
import pandas as pd

# Constants for edge case handling
VLM_CONFIDENCE_THRESHOLD = 0.8
AMBIGUITY_REASON_PREFIX = "Ambiguous: "
CONFLICT_REASON_PREFIX = "Conflict: "

class GarmentFeatureClass(Enum):
    COLOR = "color"
    PATTERN = "pattern"
    TEXTURE = "texture"

class FeasibilityFilter:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.vlm_confidence_threshold = self.config.get("vlm_confidence_threshold", VLM_CONFIDENCE_THRESHOLD)
        
        # Initialize VLM (BLIP) for verification
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
        self.vlm_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-large", 
            torch_dtype=torch.float32
        ).to("cpu") # Default to CPU as per project constraints

    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def verify_prompt_with_vlm(self, image_path: str, prompt: str) -> Tuple[bool, float, str]:
        """
        Verifies if the generated prompt matches the image content using BLIP.
        
        Returns:
            Tuple[is_valid, confidence_score, reason]
        """
        try:
            from PIL import Image
            import requests
            
            # Load image
            if image_path.startswith("http"):
                image = Image.open(requests.get(image_path, stream=True).raw).convert('RGB')
            else:
                image = Image.open(image_path).convert('RGB')
            
            # Process inputs
            inputs = self.processor(image, return_tensors="pt")
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.vlm_model.generate(**inputs)
            
            generated_caption = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            
            # Simple heuristic: Check for keyword overlap and confidence proxy
            # Since BLIP doesn't output a direct "confidence" for a specific prompt match,
            # we use the probability of the generated tokens as a proxy or a semantic similarity check.
            # For this implementation, we'll simulate a confidence score based on caption relevance.
            # A more robust approach would use a dedicated VQA model for the specific prompt.
            
            # Fallback for this task: We assume the VLM returns a confidence score if we frame it as VQA.
            # However, standard BLIP is captioning. Let's use a simple overlap heuristic as a proxy for "confidence"
            # or assume the task implies a VQA model is used. 
            # Given the prompt asks for "VLM verification", we'll use the generated caption to check consistency.
            
            # Let's use a simple word overlap as a proxy for "confidence" in the absence of a specific VQA head.
            prompt_words = set(prompt.lower().split())
            caption_words = set(generated_caption.lower().split())
            
            if not prompt_words:
                return False, 0.0, "Empty prompt"
            
            overlap = len(prompt_words.intersection(caption_words)) / len(prompt_words)
            confidence = min(overlap * 2.0, 1.0) # Scale overlap to 0-1 range, capped at 1.0
            
            is_valid = confidence >= self.vlm_confidence_threshold
            
            reason = f"Caption: {generated_caption}. Overlap: {overlap:.2f}"
            
            return is_valid, confidence, reason

        except Exception as e:
            return False, 0.0, f"VLM Error: {str(e)}"

    def filter_ambiguous_prompts(
        self, 
        samples: List[Dict[str, Any]], 
        output_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Filters samples with ambiguous prompts (VLM confidence < threshold) 
        or conflicting attributes.
        
        Args:
            samples: List of sample dicts from the dataset.
            output_path: Path to write the filtered manifest.
        
        Returns:
            List of valid samples.
        """
        valid_samples = []
        excluded_samples = []
        
        print(f"Processing {len(samples)} samples for edge cases...")
        
        for i, sample in enumerate(samples):
            image_path = sample.get("image", "")
            prompt = sample.get("prompt", "")
            attributes = sample.get("attributes", {})
            
            # Check for conflicting attributes (e.g., "red" and "blue" in same category)
            conflict_reason = self._check_attribute_conflicts(attributes)
            if conflict_reason:
                excluded_samples.append({
                    "sample_id": sample.get("id", f"unknown_{i}"),
                    "reason": CONFLICT_REASON_PREFIX + conflict_reason,
                    "excluded_type": "conflict",
                    "original_sample": sample
                })
                continue
            
            # VLM Verification
            is_valid, confidence, reason = self.verify_prompt_with_vlm(image_path, prompt)
            
            if not is_valid:
                excluded_samples.append({
                    "sample_id": sample.get("id", f"unknown_{i}"),
                    "reason": AMBIGUITY_REASON_PREFIX + reason,
                    "confidence": confidence,
                    "excluded_type": "low_confidence",
                    "original_sample": sample
                })
            else:
                valid_samples.append(sample)
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i+1}/{len(samples)} samples. Valid: {len(valid_samples)}, Excluded: {len(excluded_samples)}")
        
        # Write excluded manifest
        manifest = {
            "total_samples": len(samples),
            "valid_samples": len(valid_samples),
            "excluded_samples": len(excluded_samples),
            "excluded_list": excluded_samples,
            "threshold_used": self.vlm_confidence_threshold
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Filtered manifest written to {output_path}")
        return valid_samples

    def _check_attribute_conflicts(self, attributes: Dict[str, Any]) -> Optional[str]:
        """
        Checks for logical conflicts in garment attributes.
        Returns a reason string if conflict found, else None.
        """
        # Example logic: Check if multiple mutually exclusive colors are present
        # This is a simplified check; real logic depends on the ontology
        color_attrs = attributes.get("colors", [])
        if len(color_attrs) > 1:
            # Assuming color_attrs are strings like "red", "blue"
            # If the ontology allows "multi-colored", we might need more logic
            # For now, flag multiple specific colors as potential conflict
            return f"Multiple colors detected: {color_attrs}. Ambiguous primary color."
        
        return None

def main():
    """
    Entry point for the feasibility filter pipeline.
    Usage: python -m src.data.feasibility_filter --input <path> --output <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter ambiguous prompts from DeepFashion2 dataset")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON/CSV with samples")
    parser.add_argument("--output", type=str, required=True, help="Path to output filtered manifest")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    
    args = parser.parse_args()
    
    # Load samples
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.suffix == '.json':
        with open(input_path, 'r') as f:
            samples = json.load(f)
    elif input_path.suffix == '.csv':
        samples = pd.read_csv(input_path).to_dict('records')
    else:
        raise ValueError("Unsupported input format. Use .json or .csv")
    
    # Ensure samples is a list
    if isinstance(samples, dict) and "samples" in samples:
        samples = samples["samples"]
    elif not isinstance(samples, list):
        samples = [samples]
    
    filter_engine = FeasibilityFilter(config_path=Path(args.config) if args.config else None)
    valid_samples = filter_engine.filter_ambiguous_prompts(samples, Path(args.output))
    
    print(f"Pipeline complete. {len(valid_samples)} valid samples retained.")

if __name__ == "__main__":
    main()
