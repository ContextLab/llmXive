"""Core logic modules."""
from .evaluator import Evaluator, main
from .hard_floor_enforcer import HardFloorEnforcer
from .memory_monitor import MemoryMonitor
from .reward_computation import (
    ImplicitRewardComputer,
    compute_implicit_reward,
    validate_reward_computation,
    main,
)
from .statistical_tests import (
    paired_ttest,
    wilcoxon_signed_rank,
    bonferroni_correction,
    holm_bonferroni_correction,
    cluster_robust_se,
    classify_significance,
    run_comprehensive_tests,
    main,
)
from .trainer import DistillationDataset, OnPolicyTrainer, main
