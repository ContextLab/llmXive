"""
Student Agent for the Privilege Illusion MDP.

Implements a Tabular Q-learning agent that operates with partial state access (O).
The Student cannot observe the hidden privileged signal H, forcing it to learn
a policy based solely on observable states.
"""
import numpy as np
from typing import Tuple, Optional, Dict, Any

# Importing from the established project API surface
from env.privilege_mdp import PrivilegeMDP
from utils.seeding import seed_everything


class TabularQStudent:
    """
    A Tabular Q-learning agent designed for the PrivilegeMDP environment.

    This agent only has access to the observable state 'O', not the hidden
    privileged state 'H'. It learns a Q-table mapping observable states to
    action values.

    Attributes:
        env (PrivilegeMDP): The environment instance.
        q_table (np.ndarray): The Q-value table indexed by (observable_state, action).
        learning_rate (float): Alpha parameter for Q-learning updates.
        discount_factor (float): Gamma parameter for future reward weighting.
        epsilon (float): Exploration rate for epsilon-greedy policy.
        epsilon_decay (float): Decay factor for epsilon over time.
        epsilon_min (float): Minimum exploration rate.
        action_space (int): Number of available actions.
        obs_space (int): Number of observable states.
    """

    def __init__(
        self,
        env: PrivilegeMDP,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        seed: Optional[int] = None
    ):
        """
        Initializes the Tabular Q-Student agent.

        Args:
            env: The PrivilegeMDP environment.
            learning_rate: Step size for Q-updates.
            discount_factor: Discount factor for future rewards.
            epsilon: Initial exploration probability.
            epsilon_decay: Rate at which epsilon decays.
            epsilon_min: Minimum value for epsilon.
            seed: Optional random seed for reproducibility.
        """
        self.env = env
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        # Determine dimensions based on the environment's observable space
        # The environment's observation space for the student is discrete
        # We assume the env provides the size of the observable space via a property
        # or we derive it from the observation space object if it's a Discrete space.
        # Based on the API surface, we rely on env properties.
        
        # The PrivilegeMDP should expose the size of the observable space.
        # If not explicitly exposed as a property, we infer from the observation space.
        if hasattr(env, 'observable_space_size'):
            self.obs_space = env.observable_space_size
        elif hasattr(env.observation_space, 'n'):
            self.obs_space = env.observation_space.n
        else:
            # Fallback if structure is unknown, though spec implies discrete
            raise ValueError("Environment must expose observable state space size.")

        self.action_space = env.action_space.n

        # Initialize Q-table: Rows = Observable States, Cols = Actions
        self.q_table = np.zeros((self.obs_space, self.action_space))

        if seed is not None:
            seed_everything(seed)

    def get_observation(self, state: Tuple[int, int]) -> int:
        """
        Extracts the observable part of the state.

        In the PrivilegeMDP, a full state is (O, H). The student only sees O.

        Args:
            state: A tuple (observable, hidden) or a single int if already flattened.

        Returns:
            The observable component of the state.
        """
        # The environment's reset/step returns the full state (O, H) as a tuple
        # or a flattened representation. Based on typical discrete MDPs in this context:
        # If it's a tuple, we take the first element.
        if isinstance(state, tuple):
            return state[0]
        else:
            # If the state is already just the observable index (unlikely for full state)
            # or if the environment handles masking internally and returns just O.
            # We assume the standard case: full state (O, H).
            # If the env returns a flattened index, we might need a mapping,
            # but the task description says "partial state access O", implying
            # we receive (O, H) but only use O.
            # Let's assume state is (O, H).
            # If the environment returns a single integer representing the full state,
            # we would need a mapping function. However, the task implies we receive
            # the state and must filter it.
            # Given the Teacher has (O, H) and Student has O, the step function likely
            # returns the full state.
            raise ValueError(f"Expected state tuple (O, H), got {type(state)}")

    def select_action(self, obs: int) -> int:
        """
        Selects an action using an epsilon-greedy policy based on the Q-table.

        Args:
            obs: The observable state index.

        Returns:
            The selected action index.
        """
        if np.random.random() < self.epsilon:
            # Explore: random action
            return np.random.randint(self.action_space)
        else:
            # Exploit: best action according to Q-table
            # Handle ties by random choice among best actions
            q_values = self.q_table[obs]
            max_q = np.max(q_values)
            best_actions = np.where(q_values == max_q)[0]
            return np.random.choice(best_actions)

    def update(
        self,
        obs: int,
        action: int,
        reward: float,
        next_obs: int,
        done: bool
    ) -> None:
        """
        Performs a Q-learning update step.

        Q(s, a) <- Q(s, a) + alpha * [r + gamma * max(Q(s', a')) - Q(s, a)]

        Args:
            obs: Current observable state.
            action: Action taken.
            reward: Reward received.
            next_obs: Next observable state.
            done: Boolean indicating if the episode terminated.
        """
        # Current Q-value
        current_q = self.q_table[obs, action]

        # Target Q-value
        if done:
            target_q = reward
        else:
            # Bellman optimality update using max over next observable state
            max_next_q = np.max(self.q_table[next_obs])
            target_q = reward + self.discount_factor * max_next_q

        # Update Q-table
        self.q_table[obs, action] += self.learning_rate * (target_q - current_q)

    def decay_epsilon(self) -> None:
        """Decays the exploration rate epsilon."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def get_policy(self) -> np.ndarray:
        """
        Returns the greedy policy derived from the current Q-table.

        Returns:
            A 1D numpy array of shape (obs_space,) where each element is the
            greedy action for that observable state.
        """
        return np.argmax(self.q_table, axis=1)

    def evaluate_episode(self, max_steps: int = 100) -> Dict[str, float]:
        """
        Runs a single episode using the current policy and returns metrics.

        Args:
            max_steps: Maximum number of steps per episode.

        Returns:
            Dictionary containing 'total_reward' and 'success' (if terminal state reached).
        """
        state, _ = self.env.reset()
        total_reward = 0.0
        success = False

        for _ in range(max_steps):
            # Student only sees O
            obs = self.get_observation(state)
            action = self.select_action(obs)
            
            # Step in environment
            next_state, reward, terminated, truncated, _ = self.env.step(action)
            
            total_reward += reward
            state = next_state

            if terminated or truncated:
                # Check if we reached a goal state (reward > 0 or specific condition)
                # Assuming positive reward indicates success in this MDP context
                if reward > 0:
                    success = True
                break

        return {
            'total_reward': total_reward,
            'success': success,
            'steps': _ + 1
        }

    def train(
        self,
        num_episodes: int,
        max_steps_per_episode: int = 100,
        verbose: bool = False
    ) -> Dict[str, list]:
        """
        Trains the agent for a specified number of episodes.

        Args:
            num_episodes: Number of training episodes.
            max_steps_per_episode: Maximum steps per episode.
            verbose: If True, print progress.

        Returns:
            Dictionary containing lists of episode rewards and success rates.
        """
        episode_rewards = []
        episode_successes = []

        for ep in range(num_episodes):
            state, _ = self.env.reset()
            total_reward = 0.0
            success = False

            for step in range(max_steps_per_episode):
                # Get observable state
                obs = self.get_observation(state)
                
                # Select action
                action = self.select_action(obs)
                
                # Step environment
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                
                # Get next observable state
                next_obs = self.get_observation(next_state)
                
                # Update Q-table
                self.update(obs, action, reward, next_obs, terminated or truncated)
                
                total_reward += reward
                state = next_state

                if terminated or truncated:
                    if reward > 0:
                        success = True
                    break

            # Decay epsilon
            self.decay_epsilon()

            episode_rewards.append(total_reward)
            episode_successes.append(1.0 if success else 0.0)

            if verbose and (ep + 1) % 100 == 0:
                avg_reward = np.mean(episode_rewards[-100:])
                avg_success = np.mean(episode_successes[-100:])
                print(f"Episode {ep+1}/{num_episodes}, Avg Reward: {avg_reward:.2f}, Avg Success: {avg_success:.2f}, Epsilon: {self.epsilon:.3f}")

        return {
            'rewards': episode_rewards,
            'successes': episode_successes
        }
