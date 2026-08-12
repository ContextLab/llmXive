"""
Forward Step Implementation for BES.

Selects and configures a small pre-trained LLM (distilbert-base-uncased)
compatible with CPU-only inference.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.intel import IPEXModel
from typing import Dict, Any, Optional, Tuple

# Import existing project utilities
from code.utils.seed import set_seed
from code.utils.logger import log
from code.exceptions import BaseResearchException


class ForwardStepError(BaseResearchException):
    """Custom exception for forward step failures."""
    pass


class ForwardStep:
    """
    Handles the forward step of the BES loop using a CPU-optimized LLM.
    
    Uses DistilBERT base uncased with Intel IPEX optimization for CPU inference.
    """
    
    def __init__(self, model_id: str = "distilbert-base-uncased", seed: int = 42):
        """
        Initialize the forward step with a small pre-trained model.
        
        Args:
            model_id: Hugging Face model ID to load.
            seed: Random seed for reproducibility.
        """
        self.model_id = model_id
        self.seed = seed
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        
        # Set seed for reproducibility
        set_seed(self.seed)
        
        log(f"Initializing ForwardStep with model: {self.model_id}")
        log(f"Target device: {self.device}")
        
    def load_model(self) -> None:
        """
        Load the tokenizer and model for CPU inference.
        Uses IPEX optimization for Intel CPU acceleration.
        """
        try:
            log(f"Loading tokenizer for {self.model_id}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                revision="main"  # Explicit revision for reproducibility
            )
            
            log(f"Loading model {self.model_id} with IPEX optimization...")
            # Load the model for sequence classification (generic task placeholder)
            # In a full implementation, this would be fine-tuned for the specific task
            self.model = IPEXModel.from_pretrained(
                self.model_id,
                revision="main",
                torchscript=False  # Keep as eager for flexibility, IPEX optimizes at runtime
            )
            
            # Ensure model is in eval mode and on CPU
            self.model.eval()
            self.model.to(self.device)
            
            log(f"Model loaded successfully: {self.model_id}")
            
        except Exception as e:
            log(f"Failed to load model {self.model_id}: {str(e)}")
            raise ForwardStepError(f"Model loading failed: {str(e)}")

    def forward_pass(
        self, 
        input_text: str, 
        sub_goals: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Perform a forward pass through the model.
        
        Args:
            input_text: The puzzle or trajectory text to process.
            sub_goals: Optional list of symbolic sub-goals to guide the step.
        
        Returns:
            Dictionary containing model outputs and metadata.
        """
        if self.model is None or self.tokenizer is None:
            raise ForwardStepError("Model not loaded. Call load_model() first.")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Disable gradient calculation for inference
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Process outputs (logits for classification task)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            
            result = {
                "logits": logits.cpu().numpy(),
                "probabilities": probs.cpu().numpy(),
                "predicted_class": torch.argmax(logits, dim=-1).cpu().numpy().item(),
                "input_length": inputs["input_ids"].shape[1],
                "sub_goals_used": bool(sub_goals),
                "model_id": self.model_id,
                "device": self.device
            }
            
            return result
            
        except Exception as e:
            log(f"Forward pass failed: {str(e)}")
            raise ForwardStepError(f"Inference failed: {str(e)}")

    def recombine_trajectory(
        self, 
        parent_trajectories: list, 
        sub_goals: list
    ) -> str:
        """
        Recombine parent trajectories guided by symbolic sub-goals.
        
        This is a placeholder implementation that selects the best trajectory
        based on model confidence. A full implementation would use the model
        to generate or modify trajectories.
        
        Args:
            parent_trajectories: List of parent trajectory strings.
            sub_goals: List of symbolic sub-goals.
        
        Returns:
            A recombined/selected trajectory string.
        """
        if not parent_trajectories:
            raise ForwardStepError("No parent trajectories provided.")
        
        best_trajectory = None
        best_score = -float("inf")
        
        for traj in parent_trajectories:
            # Combine trajectory with sub-goals for context
            context = f"Trajectory: {traj}\nSub-goals: {', '.join(sub_goals)}"
            
            try:
                result = self.forward_pass(context)
                # Use probability of the predicted class as score
                score = result["probabilities"][0][result["predicted_class"]]
                
                if score > best_score:
                    best_score = score
                    best_trajectory = traj
                    
            except ForwardStepError:
                # Skip trajectories that fail inference
                continue
        
        if best_trajectory is None:
            # Fallback to first trajectory if all fail
            best_trajectory = parent_trajectories[0]
            
        return best_trajectory


def main():
    """
    Entry point for testing the ForwardStep module.
    Demonstrates loading the model and running a sample inference.
    """
    log("Starting ForwardStep demonstration...")
    
    # Initialize forward step
    forward_step = ForwardStep()
    
    try:
        # Load the model
        forward_step.load_model()
        
        # Sample input
        sample_text = "Puzzle: Find a path from A to B avoiding obstacles."
        sample_sub_goals = ["Locate start position", "Identify obstacles", "Plan path"]
        
        # Run forward pass
        log("Running forward pass...")
        result = forward_step.forward_pass(sample_text, sample_sub_goals)
        
        log(f"Forward pass result: {result}")
        
        # Test trajectory recombination
        log("Testing trajectory recombination...")
        parents = [
            "Path: A -> C -> B",
            "Path: A -> D -> B",
            "Path: A -> E -> F -> B"
        ]
        
        recombined = forward_step.recombine_trajectory(parents, sample_sub_goals)
        log(f"Recombined trajectory: {recombined}")
        
        log("ForwardStep demonstration completed successfully.")
        
    except ForwardStepError as e:
        log(f"Error during demonstration: {e}")
        raise


if __name__ == "__main__":
    main()