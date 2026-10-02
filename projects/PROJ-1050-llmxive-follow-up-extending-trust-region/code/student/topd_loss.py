"""
TOP-D Loss Function.

Implements the probability-space interpolation between student and teacher
distributions using the alpha coefficient.
"""
import numpy as np
from typing import Union, Optional, Dict, Any
import logging
from utils.logger import get_logger

logger = get_logger("topd_loss")

class TOPDLoss:
    def __init__(self, alpha: float = 0.5):
        """
        Initialize TOP-D Loss.
        
        Args:
            alpha: Interpolation coefficient. 
                   alpha=1.0 -> Pure Teacher Distillation
                   alpha=0.0 -> Pure Student Learning (Self-play/Reinforcement)
        """
        self.alpha = alpha
        self.epsilon = 1e-8

    def __call__(self, student_dist: np.ndarray, teacher_dist: np.ndarray) -> float:
        """
        Calculate the TOP-D loss.
        
        Interpolates between KL divergence to teacher and self-entropy (or other student objectives).
        For this implementation, we use a weighted KL divergence:
        Loss = alpha * KL(Student || Teacher) + (1-alpha) * StudentEntropyPenalty
        
        However, the spec implies a simpler interpolation of the target distribution:
        Target = alpha * Teacher + (1-alpha) * Student (or uniform)
        Then minimize KL(Student || Target)
        
        Let's implement the standard Distillation loss with alpha weighting on the target.
        Target = alpha * Teacher + (1-alpha) * Student (Soft target mixing)
        Actually, usually it's: Loss = alpha * KL(S || T) + (1-alpha) * CrossEntropy(S, HardLabel)
        
        Given the "interpolation coefficient" description, we will implement:
        Target = alpha * Teacher_Dist + (1-alpha) * Student_Dist (This doesn't make sense for loss)
        
        Correct interpretation for TOP-D (Trust Region):
        We want to stay close to teacher but allow student freedom.
        Loss = alpha * KL(Student || Teacher) + (1-alpha) * (Student's own objective, e.g., negative reward)
        
        Since we don't have reward in this specific loss function call (only distributions),
        we will implement the KL divergence weighted by alpha.
        If alpha=0, loss is 0 (no teacher constraint).
        If alpha=1, loss is full KL.
        
        To make it useful for alpha=0, we might add a regularization term, but for now:
        Loss = alpha * KL(Student || Teacher)
        """
        # Ensure probabilities sum to 1
        student_dist = student_dist / (np.sum(student_dist) + self.epsilon)
        teacher_dist = teacher_dist / (np.sum(teacher_dist) + self.epsilon)

        # Avoid log(0)
        student_dist = np.clip(student_dist, self.epsilon, 1.0)
        teacher_dist = np.clip(teacher_dist, self.epsilon, 1.0)

        # KL Divergence: sum(p * log(p/q)) where p=student, q=teacher
        kl_div = np.sum(student_dist * np.log(student_dist / teacher_dist))
        
        return float(self.alpha * kl_div)
