import os
import numpy as np
import onnxruntime as ort
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from .models import LabelType
import logging
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

class ClassifierError(Exception):
    """Base exception for classifier errors."""
    pass

class ModelNotFoundError(ClassifierError):
    """Raised when the model file is not found."""
    pass

class InferenceError(ClassifierError):
    """Raised when inference fails."""
    pass

class CodeBERTClassifier:
    """
    CodeBERT classifier wrapper using ONNX Runtime for CPU inference.
    Predicts whether a code block is LLM-generated or Human-written.
    Uses the actual transformers tokenizer for preprocessing.
    """
    
    # Default path to the ONNX model relative to project root
    MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "codebert-base-onnx"
    # HuggingFace model name for the tokenizer
    TOKENIZER_NAME = "microsoft/codebert-base"
    LABELS = {0: LabelType.HUMAN, 1: LabelType.LLM}
    CONFIDENCE_THRESHOLD = 0.8

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or self.MODEL_PATH
        self.session = None
        self.tokenizer = None
        self._load_model()
        self._load_tokenizer()
    
    def _load_model(self):
        """Load the ONNX model."""
        if not self.model_path.exists():
            # Fallback to checking if model directory exists
            if self.model_path.is_dir():
                # Try to find .onnx file inside
                onnx_files = list(self.model_path.glob("*.onnx"))
                if onnx_files:
                    self.model_path = onnx_files[0]
                else:
                    raise ModelNotFoundError(f"No ONNX model file found in {self.model_path}")
            else:
                raise ModelNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            # Use CPU-only execution provider as required
            providers = ['CPUExecutionProvider']
            self.session = ort.InferenceSession(str(self.model_path), providers=providers)
            logger.info(f"Loaded ONNX model from {self.model_path}")
        except Exception as e:
            raise InferenceError(f"Failed to load ONNX model: {e}")
    
    def _load_tokenizer(self):
        """Load the CodeBERT tokenizer from transformers."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.TOKENIZER_NAME)
            logger.info(f"Loaded tokenizer from {self.TOKENIZER_NAME}")
        except Exception as e:
            raise InferenceError(f"Failed to load tokenizer: {e}")
    
    def _preprocess(self, text: str) -> Dict[str, Any]:
        """
        Preprocess text for CodeBERT input using the real transformers tokenizer.
        
        Args:
            text: The code text to classify.
            
        Returns:
            Dict containing input_ids and attention_mask as numpy arrays.
        """
        if not self.tokenizer:
            raise ClassifierError("Tokenizer not loaded")
        
        # Truncate long inputs to model's max length (512 for CodeBERT)
        # Return_tensors='np' returns numpy arrays directly
        encoded = self.tokenizer(
            text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=512
        )
        
        return {
            'input_ids': encoded['input_ids'],
            'attention_mask': encoded['attention_mask']
        }
    
    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict label and confidence for a code block.
        
        Args:
            text: The code text to classify.
            
        Returns:
            Dict with 'label' (LabelType), 'confidence' (float), and 'probabilities'.
        """
        if not self.session:
            raise ClassifierError("Model not loaded")
        if not self.tokenizer:
            raise ClassifierError("Tokenizer not loaded")
        
        try:
            inputs = self._preprocess(text)
            
            # Run inference
            # Get input names from the session
            input_names = [input.name for input in self.session.get_inputs()]
            feed_dict = {name: inputs[name] for name in input_names}
            
            outputs = self.session.run(None, feed_dict)
            
            # Assume first output is logits
            logits = outputs[0][0]
            
            # Softmax to get probabilities
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            
            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class])
            
            label = self.LABELS.get(predicted_class, LabelType.HUMAN)
            
            # Create probability dict with LabelType keys
            prob_dict = {}
            for i, p in enumerate(probs):
                if i in self.LABELS:
                    prob_dict[self.LABELS[i]] = float(p)
            
            return {
                'label': label,
                'confidence': confidence,
                'probabilities': prob_dict
            }
            
        except Exception as e:
            raise InferenceError(f"Inference failed: {e}")
    
    def predict_batch(self, texts: list) -> list:
        """
        Predict labels and confidences for a batch of code blocks.
        
        Args:
            texts: List of code texts to classify.
            
        Returns:
            List of dicts with 'label', 'confidence', and 'probabilities'.
        """
        results = []
        for text in texts:
            try:
                result = self.predict(text)
                results.append(result)
            except InferenceError as e:
                logger.warning(f"Skipping block due to inference error: {e}")
                results.append({
                    'label': LabelType.HUMAN,
                    'confidence': 0.0,
                    'probabilities': {LabelType.HUMAN: 0.5, LabelType.LLM: 0.5}
                })
        return results
