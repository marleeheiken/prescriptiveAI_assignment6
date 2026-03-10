from typing import Dict
from .standardized_agents import get_standardized_agents, BaselineAgent
from .skeleton_rl_agent import create_skeleton_optimization_agent

def get_baseline_agents(env) -> Dict[str, BaselineAgent]:
    """Get all available baseline agents"""
    agents = get_standardized_agents(env)
    
    # Add skeleton optimization agent for students to improve
    agents['skeleton_optimization'] = create_skeleton_optimization_agent(env)
    
    return agents