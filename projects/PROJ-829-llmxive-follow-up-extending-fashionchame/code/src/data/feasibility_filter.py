import json
import sys
import os
import torch
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from transformers import BlipForConditionalGeneration, BlipProcessor
import yaml

class GarmentFeatureClass(Enum):
    COLOR = "color"
    PATTERN = "pattern"
    TEXTURE = "texture"

class FeasibilityFilter:
    def __init__(self, config_path: str, vlm_confidence_threshold: float = 0.8):
        self.config_path = config_path
        self.vlm_confidence_threshold = vlm_confidence_threshold
        self.settings = self._load_settings()
        self.vlm_confidence_threshold = self.settings.get('model', {}).get('vlm_confidence_threshold', vlm_confidence_threshold)
        
        # Initialize VLM on CPU only
        device = "cpu"
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-large", trust_remote_code=False)
        self.model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-large", 
            torch_dtype=torch.float32, 
            device_map=device,
            trust_remote_code=False
        )
        self.model.eval()
        
        # Load optical flow threshold from config
        self.optical_flow_threshold = self.settings.get('motion', {}).get('optical_flow_threshold', 0.5)

    def _load_settings(self) -> Dict[str, Any]:
        config_path = Path(self.config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def verify_prompt(self, image: Any, prompt: str) -> Tuple[bool, float, str]:
        """
        Verify prompt confidence using VLM.
        Returns (is_valid, confidence_score, reason)
        """
        try:
            inputs = self.processor(image, prompt, return_tensors="pt").to("cpu")
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                scores = outputs.logits[:, 0]
                confidence = float(torch.sigmoid(scores).item())
            
            is_valid = confidence >= self.vlm_confidence_threshold
            reason = "High confidence" if is_valid else f"Low confidence ({confidence:.3f} < {self.vlm_confidence_threshold})"
            
            return is_valid, confidence, reason
        except Exception as e:
            return False, 0.0, f"VLM verification failed: {str(e)}"

    def filter_ambiguous_samples(self, samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter samples based on VLM confidence and attribute conflicts.
        Returns (valid_samples, ambiguous_samples)
        """
        valid_samples = []
        ambiguous_samples = []
        
        for sample in samples:
            # Check VLM confidence
            is_valid, confidence, reason = self.verify_prompt(
                sample.get('image'), 
                sample.get('prompt', '')
            )
            
            # Check for conflicting attributes
            has_conflict = False
            conflict_reason = ""
            
            # Check if sample has multiple garment feature classes that might conflict
            feature_classes = sample.get('garment_feature_classes', [])
            if len(feature_classes) > 1:
                # Check for known conflicts (e.g., color and texture might be ambiguous together)
                if GarmentFeatureClass.COLOR.value in feature_classes and GarmentFeatureClass.TEXTURE.value in feature_classes:
                    has_conflict = True
                    conflict_reason = "Conflicting color and texture attributes"
            
            # Determine if sample is valid
            if is_valid and not has_conflict:
                # Include optical_flow_magnitude and threshold used
                processed_sample = {
                    'sample_id': sample.get('sample_id'),
                    'image_path': sample.get('image_path'),
                    'prompt': sample.get('prompt'),
                    'garment_feature_classes': sample.get('garment_feature_classes', []),
                    'vlm_confidence': confidence,
                    'optical_flow_magnitude': sample.get('optical_flow_magnitude', 0.0),
                    'optical_flow_threshold_used': self.optical_flow_threshold,
                    'is_valid': True,
                    'reason': reason
                }
                valid_samples.append(processed_sample)
            else:
                # Mark as ambiguous
                ambiguous_reason = []
                if not is_valid:
                    ambiguous_reason.append(reason)
                if has_conflict:
                    ambiguous_reason.append(conflict_reason)
                
                ambiguous_sample = {
                    'sample_id': sample.get('sample_id'),
                    'image_path': sample.get('image_path'),
                    'prompt': sample.get('prompt'),
                    'garment_feature_classes': sample.get('garment_feature_classes', []),
                    'vlm_confidence': confidence,
                    'optical_flow_magnitude': sample.get('optical_flow_magnitude', 0.0),
                    'optical_flow_threshold_used': self.optical_flow_threshold,
                    'is_valid': False,
                    'reason': '; '.join(ambiguous_reason)
                }
                ambiguous_samples.append(ambiguous_sample)
        
        return valid_samples, ambiguous_samples

    def generate_filtered_manifest(self, samples: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """
        Generate filtered subset manifest with valid samples only.
        """
        valid_samples, ambiguous_samples = self.filter_ambiguous_samples(samples)
        
        manifest = {
            'metadata': {
                'vlm_confidence_threshold': self.vlm_confidence_threshold,
                'optical_flow_threshold': self.optical_flow_threshold,
                'total_samples_processed': len(samples),
                'valid_samples_count': len(valid_samples),
                'ambiguous_samples_count': len(ambiguous_samples),
                'timestamp': str(torch.utils.data.get_worker_info()) if torch.utils.data.get_worker_info() else "N/A"
            },
            'valid_samples': valid_samples,
            'ambiguous_samples': ambiguous_samples
        }
        
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write manifest to file
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest

def load_samples_from_manifest(input_path: str) -> List[Dict[str, Any]]:
    """
    Load samples from a filtered manifest or raw dataset manifest.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input manifest not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle different manifest formats
    if 'valid_samples' in data:
        # Already filtered manifest - return all samples for re-filtering
        return data.get('valid_samples', []) + data.get('ambiguous_samples', [])
    elif 'samples' in data:
        return data['samples']
    else:
        # Assume direct list of samples
        return data

def main():
    """
    Main entry point for running the feasibility filter.
    Usage: python -m code.src.data.feasibility_filter --input <input_manifest> --output <output_manifest> --config <config_path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Feasibility Filter for DeepFashion2')
    parser.add_argument('--input', type=str, required=True, help='Input manifest path')
    parser.add_argument('--output', type=str, required=True, help='Output manifest path')
    parser.add_argument('--config', type=str, default='code/config/settings.yaml', help='Config file path')
    parser.add_argument('--vlm-threshold', type=float, default=0.8, help='VLM confidence threshold')
    
    args = parser.parse_args()
    
    try:
        # Load samples
        print(f"Loading samples from {args.input}...")
        samples = load_samples_from_manifest(args.input)
        print(f"Loaded {len(samples)} samples")
        
        # Initialize filter
        print(f"Initializing FeasibilityFilter with config {args.config}...")
        filter_instance = FeasibilityFilter(
            config_path=args.config,
            vlm_confidence_threshold=args.vlm_threshold
        )
        
        # Generate filtered manifest
        print("Generating filtered manifest...")
        manifest = filter_instance.generate_filtered_manifest(samples, args.output)
        
        print(f"Filtering complete:")
        print(f"  - Total samples processed: {manifest['metadata']['total_samples_processed']}")
        print(f"  - Valid samples: {manifest['metadata']['valid_samples_count']}")
        print(f"  - Ambiguous samples: {manifest['metadata']['ambiguous_samples_count']}")
        print(f"Output written to: {args.output}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
