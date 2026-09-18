import random
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict
from sympy import simplify_logic, symbols, Implies, And, Or, Not, Symbol
import logging
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RuleSet:
    """Represents a distinct logical rule set for a sub-population."""
    def __init__(self, rule_id: str, domain: str, rules: List[str], performance_score: float = 0.0):
        self.rule_id = rule_id
        self.domain = domain
        self.rules = rules
        self.performance_score = performance_score
        self.history = [performance_score]

    def update_performance(self, new_score: float):
        self.performance_score = new_score
        self.history.append(new_score)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "rules": self.rules,
            "performance_score": self.performance_score,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleSet':
        return cls(
            rule_id=data['rule_id'],
            domain=data['domain'],
            rules=data['rules'],
            performance_score=data.get('performance_score', 0.0)
        )


class CoevolvingAgent(BaseAgent):
    """
    Manages sub-populations of rule-sets and executes bidirectional exchanges.
    Implements selection pressure to discard non-performing rule-sets.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sub_populations: Dict[str, List[RuleSet]] = defaultdict(list)
        self.generation_count = 0
        self.evaluation_budget = config.get('rule_evaluation_budget', 1000)
        self.selection_threshold = config.get('selection_threshold', 0.1)
        self.discard_rate = config.get('discard_rate', 0.2)
        self.population_target_size = config.get('population_target_size', 50)
        self._rule_set_counter = 0

    def initialize_populations(self, initial_rule_sets: List[RuleSet]):
        """Initialize sub-populations with initial rule-sets."""
        for rs in initial_rule_sets:
            self.sub_populations[rs.domain].append(rs)
        logger.info(f"Initialized {len(self.sub_populations)} sub-populations")

    def evaluate_sub_populations(self, test_instances: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate all rule-sets in all sub-populations against test instances.
        Returns a mapping of domain -> average performance score.
        """
        domain_scores = {}
        for domain, rule_sets in self.sub_populations.items():
            if not rule_sets:
                domain_scores[domain] = 0.0
                continue

            total_score = 0.0
            for rs in rule_sets:
                score = self._evaluate_rule_set(rs, test_instances)
                rs.update_performance(score)
                total_score += score
            domain_scores[domain] = total_score / len(rule_sets)
        return domain_scores

    def _evaluate_rule_set(self, rule_set: RuleSet, test_instances: List[Dict[str, Any]]) -> float:
        """
        Evaluate a single rule-set against test instances.
        For logic tasks: check if rules satisfy logical proofs.
        For grid tasks: check if rules solve grid paths.
        Returns a score between 0.0 and 1.0.
        """
        if not test_instances:
            return 0.0

        # Filter instances relevant to this rule-set's domain
        relevant_instances = [inst for inst in test_instances if inst.get('domain') == rule_set.domain]
        if not relevant_instances:
            return 0.0

        correct = 0
        for inst in relevant_instances:
            try:
                if self._check_rule_compliance(rule_set, inst):
                    correct += 1
            except Exception as e:
                logger.warning(f"Error evaluating rule set {rule_set.rule_id} on instance {inst.get('id')}: {e}")

        return correct / len(relevant_instances)

    def _check_rule_compliance(self, rule_set: RuleSet, instance: Dict[str, Any]) -> bool:
        """
        Check if a rule-set satisfies the constraints of an instance.
        Simplified implementation: assumes rules are logical implications.
        """
        instance_data = instance.get('instance_data', {})
        # Placeholder for actual logic evaluation using sympy
        # In a real implementation, this would evaluate sympy expressions
        # against the instance constraints.
        return random.random() > 0.3  # Simulated evaluation for structure

    def execute_bidirectional_exchange(self):
        """
        Exchange rule-sets between sub-populations.
        Select top performers from each domain and swap a fraction of them.
        """
        domains = list(self.sub_populations.keys())
        if len(domains) < 2:
            logger.warning("Need at least 2 domains for bidirectional exchange")
            return

        # Identify top performers in each domain
        exchange_candidates = {}
        for domain in domains:
            sorted_rules = sorted(
                self.sub_populations[domain],
                key=lambda x: x.performance_score,
                reverse=True
            )
            # Take top 20% or at least 1
            exchange_count = max(1, int(len(sorted_rules) * 0.2))
            exchange_candidates[domain] = sorted_rules[:exchange_count]

        # Swap candidates between domains
        for i in range(len(domains)):
            source_domain = domains[i]
            target_domain = domains[(i + 1) % len(domains)]

            if exchange_candidates[source_domain] and exchange_candidates[target_domain]:
                # Exchange a random candidate from each
                src_rule = random.choice(exchange_candidates[source_domain])
                tgt_rule = random.choice(exchange_candidates[target_domain])

                # Remove from source and add to target
                self.sub_populations[source_domain].remove(src_rule)
                self.sub_populations[target_domain].append(src_rule)

                self.sub_populations[target_domain].remove(tgt_rule)
                self.sub_populations[source_domain].append(tgt_rule)

                logger.info(f"Exchanged rule {src_rule.rule_id} <-> {tgt_rule.rule_id} between {source_domain} and {target_domain}")

    def apply_selection_pressure(self):
        """
        Discard non-performing rule-sets to prevent population collapse.
        Implements a hard discard rate for rule-sets below a performance threshold.
        """
        total_discarded = 0
        for domain, rule_sets in self.sub_populations.items():
            if not rule_sets:
                continue

            # Calculate average performance for this domain
            avg_performance = sum(rs.performance_score for rs in rule_sets) / len(rule_sets)

            # Identify rule-sets to discard
            # Discard if score is below (avg - threshold) or in bottom discard_rate fraction
            threshold_score = avg_performance * (1 - self.selection_threshold)
            discard_count = max(1, int(len(rule_sets) * self.discard_rate))

            # Sort by performance (ascending)
            sorted_rules = sorted(rule_sets, key=lambda x: x.performance_score)

            # Mark bottom performers for discard
            to_remove = sorted_rules[:discard_count]
            removed_ids = []

            for rs in to_remove:
                if rs.performance_score < threshold_score:
                    self.sub_populations[domain].remove(rs)
                    removed_ids.append(rs.rule_id)
                    total_discarded += 1

            if removed_ids:
                logger.info(f"Discarded {len(removed_ids)} underperforming rule-sets in {domain}: {removed_ids}")

        # Prevent collapse: ensure minimum population size per domain
        for domain in list(self.sub_populations.keys()):
            if len(self.sub_populations[domain]) < 2:
                logger.warning(f"Population collapse detected in {domain}. Regenerating rules.")
                self._regenerate_rules(domain)

        return total_discarded

    def _regenerate_rules(self, domain: str):
        """Regenerate rule-sets for a domain if population is too small."""
        num_to_generate = max(5, self.population_target_size - len(self.sub_populations[domain]))
        for _ in range(num_to_generate):
            self._rule_set_counter += 1
            new_rule = RuleSet(
                rule_id=f"{domain}_gen_{self._rule_set_counter}",
                domain=domain,
                rules=[f"rule_{random.randint(1000, 9999)}"],
                performance_score=0.5  # Neutral start
            )
            self.sub_populations[domain].append(new_rule)
        logger.info(f"Regenerated {num_to_generate} rule-sets for {domain}")

    def step(self, test_instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute one generation step:
        1. Evaluate populations
        2. Apply selection pressure
        3. Execute bidirectional exchange
        """
        self.generation_count += 1
        logger.info(f"--- Generation {self.generation_count} ---")

        # Evaluate
        scores = self.evaluate_sub_populations(test_instances)
        logger.info(f"Domain scores: {scores}")

        # Selection pressure
        discarded = self.apply_selection_pressure()
        logger.info(f"Total rule-sets discarded: {discarded}")

        # Exchange
        self.execute_bidirectional_exchange()

        return {
            "generation": self.generation_count,
            "scores": scores,
            "discarded_count": discarded,
            "population_sizes": {k: len(v) for k, v in self.sub_populations.items()}
        }

    def get_state(self) -> Dict[str, Any]:
        """Return serializable state of the agent."""
        return {
            "generation_count": self.generation_count,
            "sub_populations": {
                domain: [rs.to_dict() for rs in rules]
                for domain, rules in self.sub_populations.items()
            },
            "evaluation_budget": self.evaluation_budget
        }

    def set_state(self, state: Dict[str, Any]):
        """Restore agent state from a dictionary."""
        self.generation_count = state.get("generation_count", 0)
        self.sub_populations = defaultdict(list)
        for domain, rule_dicts in state.get("sub_populations", {}).items():
            self.sub_populations[domain] = [RuleSet.from_dict(d) for d in rule_dicts]


def main():
    """Demo entry point for CoevolvingAgent."""
    import json
    from pathlib import Path

    # Create a minimal config
    config = {
        "rule_evaluation_budget": 100,
        "selection_threshold": 0.1,
        "discard_rate": 0.2,
        "population_target_size": 10
    }

    agent = CoevolvingAgent(config)

    # Create dummy rule-sets
    rules = [
        RuleSet("logic_A_1", "logic", ["A -> B", "B -> C"], 0.8),
        RuleSet("logic_A_2", "logic", ["C -> D"], 0.6),
        RuleSet("grid_A_1", "grid", ["avoid_red", "diagonal"], 0.7),
        RuleSet("grid_A_2", "grid", ["shortest_path"], 0.9)
    ]

    agent.initialize_populations(rules)

    # Dummy test instances
    test_instances = [
        {"id": "t1", "domain": "logic", "instance_data": {"axiom": "A", "goal": "C"}},
        {"id": "t2", "domain": "grid", "instance_data": {"start": (0, 0), "end": (5, 5)}}
    ]

    # Run a few generations
    for i in range(3):
        result = agent.step(test_instances)
        print(f"Generation {i+1} result: {json.dumps(result, indent=2)}")

    # Save state
    state = agent.get_state()
    output_path = Path("data/coevolving_agent_state.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Agent state saved to {output_path}")

if __name__ == "__main__":
    main()