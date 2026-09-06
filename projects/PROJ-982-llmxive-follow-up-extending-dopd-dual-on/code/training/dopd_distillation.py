import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import sys
import os
import json
from datetime import datetime

# Import from existing API surface
from agents.student import TabularQStudent
from agents.teacher import TeacherOracle
from agents.baseline_estimator import create_baseline_estimator
from env.privilege_mdp import PrivilegeMDP
from utils.logging import TrainingLogger
from utils.seeding import seed_everything

class DOPDTrainer:
    """
    DOPD Trainer: Dynamic On-Policy Distillation based on Advantage Gap.
    
    Implements FR-002:
    - Calculates Teacher advantage gap: A_gap = Q_teacher(s, a) - V_baseline(s)
    - Measures dynamic range (max - min) over current batch.
    - If dynamic range < 0.1, triggers min-max normalization switch.
    - Formula: lambda = (A_gap - min) / (max - min)
    - Epsilon-guarded division (epsilon=1e-8). If division fails, lambda=1.0.
    - Logs lambda switch events to data/raw/training_log.json.
    """
    
    def __init__(self, env: PrivilegeMDP, student: TabularQStudent, teacher: TeacherOracle, 
                 baseline_estimator, config: Dict[str, Any], logger: TrainingLogger):
        self.env = env
        self.student = student
        self.teacher = teacher
        self.baseline_estimator = baseline_estimator
        self.config = config
        self.logger = logger
        
        # Config defaults
        self.epsilon = config.get('epsilon', 1e-8)
        self.range_threshold = config.get('range_threshold', 0.1)
        self.learning_rate = config.get('learning_rate', 0.1)
        self.discount_factor = config.get('discount_factor', 0.99)
        
    def get_teacher_advantage(self, state: Tuple[int, int, int], action: int) -> float:
        """
        Calculate Teacher advantage gap: Q(s,a) - V_baseline(s).
        Q(s,a) is approximated by the Teacher's expected return or Q-value if available.
        Here we use the Teacher's immediate reward + gamma * V_baseline(next_state) as a proxy 
        for Q(s,a) if exact Q is not stored, or use the Teacher's action value if accessible.
        
        For this discrete MDP, we assume the Teacher acts optimally. 
        We approximate Q(s,a) by simulating the Teacher's expected return for that action.
        """
        # Get baseline V(s)
        s_flat = self.env.flatten_state(state)
        v_baseline = self.baseline_estimator.get_v_baseline(s_flat)
        
        # Estimate Q(s,a) for the specific action 'action'
        # We take one step with the Teacher policy from state 'state' taking 'action'
        # and estimate the return. Since Teacher is optimal, we can use the 
        # expected immediate reward + gamma * V(next_state)
        
        # Simulate transition for the specific action
        next_state, reward, done, info = self.env.step_with_action(state, action)
        
        # If done, Q = reward
        if done:
            q_sa = float(reward)
        else:
            # Q = reward + gamma * V(next_state)
            next_s_flat = self.env.flatten_state(next_state)
            v_next = self.baseline_estimator.get_v_baseline(next_s_flat)
            q_sa = float(reward) + self.discount_factor * v_next
        
        advantage = q_sa - v_baseline
        return advantage

    def calculate_lambda(self, advantages: List[float]) -> Tuple[float, str]:
        """
        Calculate dynamic weighting factor lambda based on advantage gap dynamic range.
        
        Per FR-002:
        - Measure dynamic range (max - min) over current batch.
        - If range < 0.1, trigger min-max normalization.
        - Formula: lambda = (A_gap - min) / (max - min)
        - Epsilon-guarded division.
        
        Returns:
            lambda_val: The calculated weighting factor (or 1.0 if fallback).
            switch_type: 'min_max' or 'uniform' (or 'fallback').
        """
        if not advantages:
            return 1.0, 'fallback'
            
        advantages_np = np.array(advantages)
        min_val = np.min(advantages_np)
        max_val = np.max(advantages_np)
        dynamic_range = max_val - min_val
        
        if dynamic_range < self.range_threshold:
            # Trigger min-max normalization switch
            # Formula: lambda = (A_gap - min) / (max - min)
            # We need to handle the case where max == min (range=0) even if < threshold
            if dynamic_range < self.epsilon:
                # Division by zero guard: if range is effectively zero, use uniform
                lambda_val = 1.0
                switch_type = 'uniform' # Fallback to uniform when no signal
            else:
                # Normalize each advantage to [0, 1] range
                # Note: The task asks for a single lambda for the batch or per-step?
                # "Formula: lambda = (A_gap - min) / (max - min)" implies per-step normalization.
                # However, the training loop usually aggregates. We will return the normalized array
                # or a single scalar if the context implies a batch-level weight.
                # Re-reading: "Calculate Teacher advantage gap ... Measure dynamic range ... 
                # if dynamic range < 0.1, trigger min-max normalization switch".
                # The switch implies a mode change. The formula calculates the weight.
                # We will return the normalized values for the batch, and the switch type.
                # But the function signature suggests a single lambda. 
                # Let's assume the caller expects a single scalar weight for the batch update 
                # OR the function returns the array and the caller handles it.
                # Given the prompt "set lambda=1.0 per Edge Cases", it implies a scalar fallback.
                # Let's calculate the mean lambda for the batch if normalization is used.
                normalized = (advantages_np - min_val) / (dynamic_range + self.epsilon)
                lambda_val = float(np.mean(normalized)) # Average weight for the batch
                switch_type = 'min_max'
        else:
            # Dynamic range is large, use uniform weighting (lambda = 1.0 or similar)
            # Or perhaps the "switch" is only for small ranges.
            # If range >= 0.1, we might just use the raw advantage or a fixed weight.
            # The prompt says: "if dynamic range < 0.1, trigger min-max normalization switch".
            # Implies if >= 0.1, we do NOT trigger it (i.e., use Uniform/Fixed).
            lambda_val = 1.0
            switch_type = 'uniform'
            
        return lambda_val, switch_type

    def train_step(self, state: Tuple[int, int, int], action: int, 
                   teacher_action: int, reward: float, next_state: Tuple[int, int, int], 
                   done: bool) -> Dict[str, Any]:
        """
        Perform a single training step with DOPD logic.
        """
        s_flat = self.env.flatten_state(state)
        
        # Calculate Advantage Gap for the Teacher's action
        # We assume the student is being trained to mimic the teacher, 
        # so we evaluate the teacher's action advantage.
        advantage = self.get_teacher_advantage(state, teacher_action)
        
        # Update student Q-table
        # Standard Q-learning update for the student, but weighted by lambda?
        # The prompt mentions "DOPD reduces reliance on Teacher's actions when advantage gap is low".
        # This implies the learning rate or the loss weight is modulated by lambda.
        
        # For now, we calculate lambda based on a batch. In a step-by-step loop,
        # we might accumulate advantages and calculate lambda periodically.
        # Here we return the raw advantage and let the caller handle batching.
        
        return {
            'state': s_flat,
            'action': teacher_action,
            'advantage': advantage,
            'reward': reward,
            'done': done
        }

    def train_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train on a batch of transitions with DOPD weighting.
        """
        advantages = [step['advantage'] for step in batch]
        
        # Calculate lambda and switch type
        lambda_val, switch_type = self.calculate_lambda(advantages)
        
        # Log the switch event
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'dopd_lambda_switch',
            'dynamic_range': float(np.max(advantages) - np.min(advantages)) if advantages else 0.0,
            'lambda_value': lambda_val,
            'switch_type': switch_type,
            'batch_size': len(batch)
        }
        self.logger.log_metrics(log_entry)
        
        # Update student Q-table with weighted updates
        # Weights are lambda_val (or normalized advantages if we passed them)
        # For simplicity, applying lambda_val as a global multiplier to the learning rate
        effective_lr = self.learning_rate * lambda_val
        
        for step in batch:
            s = step['state']
            a = step['action']
            r = step['reward']
            next_s = self.env.flatten_state(step.get('next_state', s)) # Handle if not stored
            done = step['done']
            
            # Q-learning update: Q(s,a) = Q(s,a) + alpha * (R + gamma * max(Q(next_s)) - Q(s,a))
            # But we are distilling from Teacher. 
            # Standard distillation: Minimize (Q_student(s,a) - Q_teacher(s,a))^2 ?
            # Or policy distillation? The prompt says "reduces reliance on Teacher's actions".
            # Let's assume we update Q_student towards the Teacher's Q (approximated by advantage + V).
            # Or simply standard Q-learning but with a weighted learning rate based on the Teacher's confidence (advantage).
            
            # Since we have the Teacher's advantage, we can weight the update.
            # If advantage is low, lambda is low (in min_max mode) -> less update.
            # If advantage is high, lambda is high -> more update.
            
            # Simple Q-update for student:
            current_q = self.student.q_table[s, a]
            if done:
                target = r
            else:
                max_next_q = np.max(self.student.q_table[next_s, :])
                target = r + self.discount_factor * max_next_q
                
            # Apply weighted update
            # We use the lambda calculated for the batch. 
            # Ideally, we'd use per-step normalized advantage, but lambda_val is the batch mean.
            # Let's use the specific advantage for this step to weight the update directly?
            # The prompt says "lambda = (A_gap - min) / (max - min)".
            # We'll use the step's normalized advantage if available, or the batch mean.
            # To keep it simple and aligned with the "lambda switch" logic:
            # We apply the batch-level lambda as a multiplier to the learning rate for this batch.
            
            update = effective_lr * (target - current_q)
            self.student.q_table[s, a] += update
            
        return {
            'lambda': lambda_val,
            'switch_type': switch_type,
            'advantages': advantages,
            'effective_lr': effective_lr
        }

def train_dopd(env: PrivilegeMDP, student: TabularQStudent, teacher: TeacherOracle,
               config: Dict[str, Any], seed: int, steps: int = 1000) -> Dict[str, Any]:
    """
    Main training loop for DOPD regime.
    """
    seed_everything(seed)
    
    # Initialize baseline estimator
    # T022a requirement: Run Monte Carlo until convergence.
    # We assume baseline_estimator is pre-computed or computed here.
    # For this script, we instantiate and run the estimation.
    baseline_estimator = create_baseline_estimator(env, config.get('baseline_config', {}))
    
    # Initialize logger
    logger = TrainingLogger()
    logger.log_config(config, seed)
    
    trainer = DOPDTrainer(env, student, teacher, baseline_estimator, config, logger)
    
    batch = []
    batch_size = config.get('batch_size', 50)
    
    state = env.reset()
    total_reward = 0.0
    steps_count = 0
    
    for t in range(steps):
        # Teacher acts
        teacher_action = teacher.select_action(state)
        # Student acts (optional, or we just observe teacher)
        # The task is "Distillation", so we train student on teacher's behavior.
        # We collect transitions from the Teacher's policy.
        
        next_state, reward, done, info = env.step(teacher_action)
        total_reward += reward
        
        # Record step
        step_data = {
            'state': state,
            'action': teacher_action, # Teacher's action
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'advantage': None # Calculated later
        }
        
        # Calculate advantage for this step
        step_data['advantage'] = trainer.get_teacher_advantage(state, teacher_action)
        
        batch.append(step_data)
        state = next_state
        steps_count += 1
        
        if done:
            state = env.reset()
        
        # Process batch
        if len(batch) >= batch_size:
            result = trainer.train_batch(batch)
            batch = []
            
            # Log metrics
            logger.log_metrics({
                'step': steps_count,
                'regime': 'dopd',
                'total_reward': total_reward,
                'lambda': result['lambda'],
                'switch_type': result['switch_type']
            })
            
            total_reward = 0.0
            
    # Final batch
    if batch:
        trainer.train_batch(batch)
        
    # Save logs
    logger.save_logs('data/raw/training_log.json')
    
    return {
        'student': student,
        'total_steps': steps_count,
        'config': config,
        'seed': seed
    }

def run_generalization_analysis(env: PrivilegeMDP, student: TabularQStudent, 
                                teacher: TeacherOracle, config: Dict[str, Any], 
                                seed: int, steps: int = 1000) -> Dict[str, Any]:
    """
    Run generalization analysis for DOPD trained student.
    """
    # Import generalization test logic
    from analysis.generalization_test import evaluate_agent_in_masked_mode, calculate_performance_drop
    
    # Evaluate unmasked
    acc_unmasked, _ = evaluate_agent_in_masked_mode(env, student, teacher, unmasked=True, steps=steps, seed=seed)
    
    # Evaluate masked (remove H)
    acc_masked, _ = evaluate_agent_in_masked_mode(env, student, teacher, unmasked=False, steps=steps, seed=seed)
    
    performance_drop = calculate_performance_drop(acc_unmasked, acc_masked)
    
    return {
        'acc_unmasked': acc_unmasked,
        'acc_masked': acc_masked,
        'performance_drop': performance_drop
    }
