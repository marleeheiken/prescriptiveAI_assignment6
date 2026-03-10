import os
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
import gymnasium as gym

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.warehouse_env import WarehouseEnv
from agents.baselines import get_baseline_agents

class WarehouseTrainingCallback(BaseCallback):
    """Custom callback for monitoring training progress"""
    
    def __init__(self, eval_freq: int = 10000, verbose: int = 1):
        super().__init__(verbose)
        self.eval_freq = eval_freq
        self.episode_rewards = []
        self.episode_profits = []
        self.episode_completion_rates = []
        
    def _on_step(self) -> bool:
        # Log episode statistics when episode ends
        if len(self.locals['infos']) > 0:
            for info in self.locals['infos']:
                if info.get('episode'):
                    # Episode ended
                    self.episode_rewards.append(info['episode']['r'])
                    if 'profit' in info:
                        self.episode_profits.append(info['profit'])
                    if 'completion_rate' in info:
                        self.episode_completion_rates.append(info['completion_rate'])
        
        return True
    
    def _on_training_end(self) -> None:
        # Plot training progress
        self._plot_training_progress()
    
    def _plot_training_progress(self):
        if len(self.episode_rewards) == 0:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Episode rewards
        axes[0, 0].plot(self.episode_rewards)
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        
        # Episode profits
        if self.episode_profits:
            axes[0, 1].plot(self.episode_profits)
            axes[0, 1].set_title('Episode Profits')
            axes[0, 1].set_xlabel('Episode')
            axes[0, 1].set_ylabel('Profit ($)')
        
        # Completion rates
        if self.episode_completion_rates:
            axes[1, 0].plot(self.episode_completion_rates)
            axes[1, 0].set_title('Order Completion Rate')
            axes[1, 0].set_xlabel('Episode')
            axes[1, 0].set_ylabel('Completion Rate')
        
        # Running average rewards
        if len(self.episode_rewards) > 10:
            window_size = min(100, len(self.episode_rewards) // 10)
            running_avg = np.convolve(self.episode_rewards, 
                                    np.ones(window_size)/window_size, mode='valid')
            axes[1, 1].plot(running_avg)
            axes[1, 1].set_title(f'Running Average Rewards (window={window_size})')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Average Reward')
        
        plt.tight_layout()
        plt.savefig('training_progress.png')
        plt.show()

def create_warehouse_env(**kwargs):
    """Factory function to create warehouse environment"""
    return WarehouseEnv(**kwargs)

def train_ppo_agent(env_kwargs=None, total_timesteps=1000000, save_path="warehouse_ppo"):
    """Train a PPO agent on the warehouse environment"""
    
    if env_kwargs is None:
        env_kwargs = {}
    
    # Create environment
    env = make_vec_env(lambda: Monitor(create_warehouse_env(**env_kwargs)), n_envs=1)
    env = VecNormalize(env, norm_obs=True, norm_reward=True)
    
    # Create PPO model
    model = PPO(
        "MultiInputPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        tensorboard_log="./tensorboard_logs/"
    )
    
    # Set up callbacks
    callback = WarehouseTrainingCallback(eval_freq=10000)
    
    # Train the model
    print("Starting PPO training...")
    model.learn(total_timesteps=total_timesteps, callback=callback)
    
    # Save the model
    model.save(save_path)
    env.save(f"{save_path}_env")
    
    print(f"Training completed. Model saved to {save_path}")
    return model, env

def train_dqn_agent(env_kwargs=None, total_timesteps=1000000, save_path="warehouse_dqn"):
    """Train a DQN agent (if action space is compatible)"""
    
    if env_kwargs is None:
        env_kwargs = {}
    
    # Note: DQN requires discrete action space, might need wrapper
    print("Warning: DQN requires discrete action space. Consider using PPO instead.")
    
    # This is a placeholder - DQN would need action space modification
    # env = create_warehouse_env(**env_kwargs)
    # model = DQN("MultiInputPolicy", env, verbose=1)
    # model.learn(total_timesteps=total_timesteps)
    # model.save(save_path)
    
    return None, None

def evaluate_agent(model, env, n_episodes=10):
    """Evaluate a trained agent"""
    episode_rewards = []
    episode_profits = []
    episode_completion_rates = []
    
    for episode in range(n_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward
        
        episode_rewards.append(episode_reward)
        if isinstance(info, list) and len(info) > 0:
            episode_info = info[0]
            if 'profit' in episode_info:
                episode_profits.append(episode_info['profit'])
            if 'completion_rate' in episode_info:
                episode_completion_rates.append(episode_info['completion_rate'])
    
    print(f"Evaluation Results ({n_episodes} episodes):")
    print(f"Average Reward: {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    if episode_profits:
        print(f"Average Profit: ${np.mean(episode_profits):.2f} ± ${np.std(episode_profits):.2f}")
    if episode_completion_rates:
        print(f"Average Completion Rate: {np.mean(episode_completion_rates):.1%} ± {np.std(episode_completion_rates):.1%}")
    
    return {
        'rewards': episode_rewards,
        'profits': episode_profits,
        'completion_rates': episode_completion_rates
    }

def compare_agents(env_kwargs=None, n_episodes=20):
    """Compare RL agent with baseline agents"""
    
    if env_kwargs is None:
        env_kwargs = {}
    
    # Create environment for baselines
    env = create_warehouse_env(**env_kwargs)
    baseline_agents = get_baseline_agents(env)
    
    results = {}
    
    # Evaluate baseline agents
    for name, agent in baseline_agents.items():
        print(f"\nEvaluating {name}...")
        agent_rewards = []
        agent_profits = []
        agent_completion_rates = []
        
        for episode in range(n_episodes):
            obs, _ = env.reset()
            agent.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action = agent.get_action(obs)
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                episode_reward += reward
            
            agent_rewards.append(episode_reward)
            agent_profits.append(info.get('profit', 0))
            agent_completion_rates.append(info.get('completion_rate', 0))
        
        results[name] = {
            'rewards': agent_rewards,
            'profits': agent_profits,
            'completion_rates': agent_completion_rates
        }
        
        print(f"Average Reward: {np.mean(agent_rewards):.2f}")
        print(f"Average Profit: ${np.mean(agent_profits):.2f}")
        print(f"Average Completion Rate: {np.mean(agent_completion_rates):.1%}")
    
    # Try to load and evaluate trained RL agent
    try:
        from stable_baselines3 import PPO
        model = PPO.load("warehouse_ppo")
        print(f"\nEvaluating trained PPO agent...")
        rl_results = evaluate_agent(model, env, n_episodes)
        results['PPO'] = rl_results
    except:
        print("No trained PPO model found. Train first with train_ppo_agent()")
    
    # Plot comparison
    _plot_agent_comparison(results)
    
    return results

def _plot_agent_comparison(results):
    """Plot comparison of different agents"""
    
    if not results:
        return
    
    agent_names = list(results.keys())
    avg_rewards = [np.mean(results[name]['rewards']) for name in agent_names]
    avg_profits = [np.mean(results[name]['profits']) for name in agent_names]
    avg_completion_rates = [np.mean(results[name]['completion_rates']) for name in agent_names]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Average rewards
    axes[0].bar(agent_names, avg_rewards)
    axes[0].set_title('Average Episode Rewards')
    axes[0].set_ylabel('Reward')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Average profits
    axes[1].bar(agent_names, avg_profits)
    axes[1].set_title('Average Episode Profits')
    axes[1].set_ylabel('Profit ($)')
    axes[1].tick_params(axis='x', rotation=45)
    
    # Average completion rates
    axes[2].bar(agent_names, avg_completion_rates)
    axes[2].set_title('Average Completion Rates')
    axes[2].set_ylabel('Completion Rate')
    axes[2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('agent_comparison.png')
    plt.show()

def curriculum_training():
    """Implement curriculum learning approach"""
    
    print("Starting curriculum training...")
    
    # Phase 1: Simple environment (fixed demand, no layout changes)
    print("\nPhase 1: Fixed demand, no layout optimization")
    phase1_kwargs = {
        'order_arrival_rate': 0.3,  # Lower demand
        'episode_length': 2000,     # Shorter episodes
    }
    model1, env1 = train_ppo_agent(
        env_kwargs=phase1_kwargs,
        total_timesteps=500000,
        save_path="warehouse_ppo_phase1"
    )
    
    # Phase 2: Variable demand
    print("\nPhase 2: Variable demand")
    phase2_kwargs = {
        'order_arrival_rate': 0.5,  # Normal demand
        'episode_length': 3000,
    }
    
    # Load previous model and continue training
    model2 = PPO.load("warehouse_ppo_phase1")
    env2 = make_vec_env(lambda: Monitor(create_warehouse_env(**phase2_kwargs)), n_envs=1)
    env2 = VecNormalize.load(f"warehouse_ppo_phase1_env", env2)
    
    model2.set_env(env2)
    model2.learn(total_timesteps=500000)
    model2.save("warehouse_ppo_phase2")
    env2.save("warehouse_ppo_phase2_env")
    
    # Phase 3: Full environment
    print("\nPhase 3: Full environment with layout optimization")
    phase3_kwargs = {
        'order_arrival_rate': 0.7,  # Higher demand
        'episode_length': 5000,     # Full episodes
    }
    
    model3 = PPO.load("warehouse_ppo_phase2")
    env3 = make_vec_env(lambda: Monitor(create_warehouse_env(**phase3_kwargs)), n_envs=1)
    env3 = VecNormalize.load(f"warehouse_ppo_phase2_env", env3)
    
    model3.set_env(env3)
    model3.learn(total_timesteps=1000000)
    model3.save("warehouse_ppo_final")
    env3.save("warehouse_ppo_final_env")
    
    print("Curriculum training completed!")
    return model3, env3

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train RL agents on warehouse environment")
    parser.add_argument("--mode", type=str, default="train", 
                      choices=["train", "evaluate", "compare", "curriculum"],
                      help="Training mode")
    parser.add_argument("--timesteps", type=int, default=1000000,
                      help="Number of training timesteps")
    parser.add_argument("--episodes", type=int, default=20,
                      help="Number of evaluation episodes")
    
    args = parser.parse_args()
    
    if args.mode == "train":
        train_ppo_agent(total_timesteps=args.timesteps)
    elif args.mode == "evaluate":
        try:
            model = PPO.load("warehouse_ppo")
            env = create_warehouse_env()
            evaluate_agent(model, env, args.episodes)
        except:
            print("No trained model found. Train first with --mode train")
    elif args.mode == "compare":
        compare_agents(n_episodes=args.episodes)
    elif args.mode == "curriculum":
        curriculum_training()