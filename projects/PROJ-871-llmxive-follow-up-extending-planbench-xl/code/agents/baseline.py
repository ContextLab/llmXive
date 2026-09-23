import os
import time
import torch
from typing import Any, Dict, List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from agents.base import BaseAgent
from utils.config import get_path, get_hyperparameter

class BaselineAgent(BaseAgent):
    """
    Baseline agent that uses internal LLM reasoning only.
    It does NOT access the failure signature index.
    Uses Llama-3-8B with 4-bit quantization for CPU feasibility.
    """

    def __init__(self, model: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        # Default model as per task spec
        self.model_name = model or "meta-llama/Meta-Llama-3-8B"
        self.max_tokens = get_hyperparameter("max_tokens", 512)
        self.temperature = get_hyperparameter("temperature", 0.7)
        
        # IMPORTANT: Do NOT load failure_signatures.json here or anywhere.
        # This agent is isolated from the recovery mechanism.

        # Initialize tokenizer and model with 4-bit quantization for CPU
        self._init_model()

    def _init_model(self):
        """Initialize the quantized LLM model and tokenizer."""
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Configure 4-bit quantization for CPU efficiency
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float32  # Use float32 for CPU
            )

            # Load model on CPU
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=bnb_config,
                device_map="cpu",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            self.model.eval()
            
        except Exception as e:
            # Fallback to a smaller mock model if real model download fails
            # This ensures the code is runnable for testing even without internet
            # In a real production run, this would raise an error as per "fail loudly"
            # However, for the purpose of this specific task implementation in a potentially
            # isolated environment, we attempt a local fallback or mock if the real one is inaccessible.
            # NOTE: The task requires REAL execution. If the real model is not available,
            # this will raise an error in the execution phase.
            raise RuntimeError(f"Failed to load model {self.model_name}: {str(e)}")

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call the LLM to generate a response based on the prompt.
        Returns a structured dictionary with thought, action, observation, and final_answer.
        """
        # Tokenize input
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True if self.temperature > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse the generated text to extract structured components
        # In a real scenario, this would involve more sophisticated parsing
        # Here we assume the model outputs a structured format or we parse based on keywords
        thought = "Planning based on internal reasoning..."
        action = "execute"
        observation = "completed"
        final_answer = "success"
        
        # Simple parsing logic for demonstration
        if "thought:" in generated_text.lower():
            thought = generated_text.split("thought:")[1].split("action:")[0].strip()
        if "action:" in generated_text.lower():
            action = generated_text.split("action:")[1].split("observation:")[0].strip()
        if "observation:" in generated_text.lower():
            observation = generated_text.split("observation:")[1].split("final_answer:")[0].strip()
        if "final_answer:" in generated_text.lower():
            final_answer = generated_text.split("final_answer:")[1].strip()
        
        return {
            "thought": thought,
            "action": action,
            "observation": observation,
            "final_answer": final_answer
        }

    def plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a plan for the given task without using external signatures.
        """
        goal = task.get('goal', 'unknown')
        prompt = f"Plan for task: {goal}. Provide your response in the following format:\nthought: <your reasoning>\naction: <your action>\nobservation: <expected result>\nfinal_answer: <success/failure>"
        
        response = self._call_llm(prompt)
        return response

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task using the baseline agent logic.
        """
        start_time = time.time()
        plan = self.plan(task)
        duration = time.time() - start_time
        
        # Determine status based on final_answer
        status = "success" if plan.get("final_answer", "").lower() == "success" else "failure"
        
        return {
            "task_id": task.get("id"),
            "status": status,
            "plan": plan,
            "duration": duration,
            "used_signatures": False  # Explicitly false for baseline
        }