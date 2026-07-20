import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Generator
from dataclasses import dataclass, field

# Importing logger utilities from the project's existing logger module
from logger import get_logger, configure_global_logging

@dataclass
class AgentConfig:
    model_name: str
    max_new_tokens: int = 128
    temperature: float = 0.0
    top_p: float = 1.0
    max_steps: int = 1000
    context_window_size: int = 50000  # Characters
    device: str = "cpu"
    dtype: str = "float32"

@dataclass
class AgentState:
    step: int = 0
    mental_map: Dict[str, Any] = field(default_factory=dict)
    action_log: List[Dict[str, Any]] = field(default_factory=list)
    is_terminated: bool = False
    termination_reason: Optional[str] = None
    error_log: List[Dict[str, Any]] = field(default_factory=list)

class TextAgent:
    """
    Text-only agent that processes ASCII grid and event logs.
    Implements error handling for inference failures (NaN, OOM) as per T027.
    """
    def __init__(self, config: AgentConfig):
        self.config = config
        self.logger = get_logger(__name__)
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the quantized text-only LLM."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch

            self.logger.info(f"Loading model: {self.config.model_name}")
            
            # Configure quantization for CPU optimization if needed
            bnb_config = None
            if "4bit" in self.config.model_name or "int8" in self.config.model_name:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16
                )

            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            
            device_map = "auto" if self.config.device != "cpu" else None
            if self.config.device == "cpu":
                device_map = None

            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map=device_map,
                torch_dtype=torch.float32 if self.config.device == "cpu" else torch.float16,
                trust_remote_code=True
            )

            if self.config.device == "cpu" and self.model.device.type != "cpu":
                self.model = self.model.to("cpu")
            
            self.model.eval()
            self.logger.info("Model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    def _check_inference_health(self, output_text: str) -> bool:
        """
        Check for NaN, inf, or corrupted output patterns.
        Returns False if output is unhealthy.
        """
        if not output_text:
            return False
        
        # Check for common NaN/Inf string representations
        if "nan" in output_text.lower() or "inf" in output_text.lower():
            return False
        
        # Check for empty or whitespace-only output
        if not output_text.strip():
            return False

        return True

    def _handle_inference_failure(self, error: Exception, step: int, context: str):
        """
        Logs the failure, records it in state, and discards the current run attempt.
        """
        failure_entry = {
            "step": step,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context_preview": context[:200] + "..." if len(context) > 200 else context,
            "timestamp": time.time()
        }
        
        self.logger.critical(f"Inference failure at step {step}: {error}", exc_info=True)
        self.logger.warning("Discarding current run due to unrecoverable inference error.")
        
        # Return a signal to indicate the run should be discarded
        return failure_entry

    def step(self, ascii_grid: str, event_log: List[Dict[str, Any]], state: AgentState) -> Tuple[Optional[Dict[str, Any]], AgentState]:
        """
        Perform one inference step.
        Returns (action, updated_state). If a critical failure occurs, action is None and state is updated with termination.
        """
        if state.is_terminated:
            return None, state

        if state.step >= self.config.max_steps:
            state.is_terminated = True
            state.termination_reason = "max_steps_reached"
            return None, state

        # Construct prompt (simplified for this implementation)
        prompt = f"Current State:\n{ascii_grid}\n\nEvent Log:\n{json.dumps(event_log[-5:])}\n\nAction:"
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            if self.config.device != "cpu":
                inputs = {k: v.to(self.config.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_new_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=self.config.temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the new part (after the prompt)
            generated_part = output_text[len(prompt):].strip()

            # Health check
            if not self._check_inference_health(generated_part):
                raise ValueError(f"Unhealthy output detected: {generated_part[:100]}")

            # Parse JSON action (assuming model outputs JSON)
            try:
                # Attempt to find JSON block
                start = generated_part.find('{')
                end = generated_part.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = generated_part[start:end+1]
                    action = json.loads(json_str)
                else:
                    # Fallback: try to parse whole string
                    action = json.loads(generated_part)
            except json.JSONDecodeError:
                self.logger.warning(f"Failed to parse JSON from model output: {generated_part}")
                action = {"type": "noop", "reason": "parse_error", "raw": generated_part}

            state.step += 1
            state.action_log.append({"step": state.step, "action": action})
            state.mental_map = action.get("mental_map_update", state.mental_map)

            return action, state

        except torch.cuda.OutOfMemoryError as e:
            failure = self._handle_inference_failure(e, state.step, prompt)
            state.error_log.append(failure)
            state.is_terminated = True
            state.termination_reason = "OOM"
            return None, state

        except RuntimeError as e:
            if "CUDA" in str(e) or "CUDA out of memory" in str(e):
                failure = self._handle_inference_failure(e, state.step, prompt)
                state.error_log.append(failure)
                state.is_terminated = True
                state.termination_reason = "OOM"
                return None, state
            elif "nan" in str(e).lower() or "inf" in str(e).lower():
                failure = self._handle_inference_failure(e, state.step, prompt)
                state.error_log.append(failure)
                state.is_terminated = True
                state.termination_reason = "NaN/Inf"
                return None, state
            else:
                # Re-raise other runtime errors
                raise

        except Exception as e:
            failure = self._handle_inference_failure(e, state.step, prompt)
            state.error_log.append(failure)
            state.is_terminated = True
            state.termination_reason = "InferenceFailure"
            return None, state

def main():
    """
    Entry point for running the agent loop.
    Demonstrates error handling by running a dummy cycle or loading config.
    """
    configure_global_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting TextAgent main loop.")
    
    # Example configuration
    config = AgentConfig(
        model_name="microsoft/phi-2", # Example small model
        max_steps=10
    )
    
    agent = TextAgent(config)
    state = AgentState()
    
    # Dummy input for demonstration of the loop structure
    dummy_ascii = "O\n"
    dummy_log = []
    
    try:
        action, final_state = agent.step(dummy_ascii, dummy_log, state)
        if final_state.is_terminated and final_state.termination_reason in ["OOM", "NaN/Inf", "InferenceFailure"]:
            logger.error(f"Run terminated due to error: {final_state.termination_reason}")
            # In a real run, this would trigger a discard of the run data
            return 1
        logger.info("Agent step completed successfully.")
        return 0
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}")
        return 1

if __name__ == "__main__":
    exit(main())