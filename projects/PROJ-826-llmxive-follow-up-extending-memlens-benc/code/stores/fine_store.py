import os
import json
import pickle
from typing import List, Dict, Any, Optional

import config
from stores.base import MemoryStore
from ultralytics import YOLO
from PIL import Image
import torch

class FineStore(MemoryStore):
    """
    Fine-grained memory store implementing Constitution VI.
    
    Loads text summaries and runs a CPU-optimized YOLOv8n model (seed=42)
    to generate object captions and bounding boxes for images.
    If no objects are detected, returns the context string "[No objects detected]".
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the FineStore.
        
        Args:
            model_path: Optional path to a custom YOLOv8n model. 
                        If None, uses the default ultralytics YOLOv8n.
        """
        self.model_path = model_path or "yolov8n.pt"
        self.model = None
        self._load_model()
        
    def _load_model(self) -> None:
        """Load the YOLOv8n model onto CPU with seed=42."""
        # Set global seed for reproducibility
        torch.manual_seed(config.SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(config.SEED)
            torch.backends.cudnn.deterministic = True
            
        # Load YOLO model (CPU optimized by default if CUDA not used)
        self.model = YOLO(self.model_path)
        # Ensure model runs on CPU
        self.model.to("cpu")
        
    def load_data(self, data_path: str) -> List[Dict[str, Any]]:
        """
        Load data from the specified path.
        
        Args:
            data_path: Path to the data file (JSON or pickle).
                        
        Returns:
            List of data records.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")
            
        if data_path.endswith('.json'):
            with open(data_path, 'r') as f:
                return json.load(f)
        elif data_path.endswith('.pkl') or data_path.endswith('.pickle'):
            with open(data_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise ValueError(f"Unsupported file format: {data_path}")
            
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Process a single image to detect objects and generate captions/bboxes.
        
        Args:
            image_path: Path to the image file.
                        
        Returns:
            List of detected objects with their bounding boxes and captions.
        """
        if not os.path.exists(image_path):
            return []
            
        try:
            # Run YOLO inference
            results = self.model(image_path)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                    
                for i in range(len(boxes)):
                    box = boxes[i]
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    
                    # Get class name from model
                    class_name = self.model.names[cls_id]
                    
                    # Create a simple caption based on detection
                    caption = f"{class_name} (confidence: {conf:.2f})"
                    
                    detections.append({
                        "class": class_name,
                        "confidence": conf,
                        "bbox": xyxy,
                        "caption": caption
                    })
                    
            return detections
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return []
            
    def get_context(self, record: Dict[str, Any]) -> str:
        """
        Generate a context string for a data record.
        
        Args:
            record: A data record containing 'summary' and 'image_path'.
                        
        Returns:
            Context string including text summary and object detections.
            If no objects are detected, returns "[No objects detected]".
        """
        # Start with the text summary
        context_parts = []
        summary = record.get("summary", "")
        if summary:
            context_parts.append(f"Text Summary: {summary}")
            
        # Process image if available
        image_path = record.get("image_path")
        if image_path and os.path.exists(image_path):
            detections = self.process_image(image_path)
            
            if not detections:
                context_parts.append("[No objects detected]")
            else:
                context_parts.append("Detected Objects:")
                for obj in detections:
                    context_parts.append(f"  - {obj['caption']} at {obj['bbox']}")
        else:
            context_parts.append("[No image available]")
            
        return "\n".join(context_parts)
        
    def build_index(self, data_path: str) -> Dict[str, Any]:
        """
        Build an index for the data at the specified path.
        
        Args:
            data_path: Path to the data file.
                        
        Returns:
            Index dictionary mapping record IDs to their context.
        """
        data = self.load_data(data_path)
        index = {}
        
        for i, record in enumerate(data):
            record_id = record.get("id", f"record_{i}")
            context = self.get_context(record)
            index[record_id] = context
            
        return index
        
    def save_index(self, index: Dict[str, Any], output_path: str) -> None:
        """
        Save the index to the specified path.
        
        Args:
            index: The index dictionary to save.
            output_path: Path to save the index file.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(index, f)
            
    def load_index(self, index_path: str) -> Dict[str, Any]:
        """
        Load an index from the specified path.
        
        Args:
            index_path: Path to the index file.
                        
        Returns:
            The loaded index dictionary.
        """
        with open(index_path, 'rb') as f:
            return pickle.load(f)
