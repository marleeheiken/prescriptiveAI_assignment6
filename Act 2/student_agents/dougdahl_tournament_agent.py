#!/usr/bin/env python
"""
Tournament Agent: King kong
Student: Doug Dahl
Generated: 2025-10-16 21:14:09

Evolution Details:
- Generations: 100
- Final Fitness: N/A
- Trained against: Random (0.9), Gradual, Soft Majority, Suspicious Tit-for-Tat, Pavlov...

Strategy: climb to the top of the empire state building
"""

from agents import Agent, INVEST, UNDERCUT
import random


class DougDahlAgent(Agent):
    """
    King kong
    
    climb to the top of the empire state building
    
    Evolved Genes: [0.9970462326330012, 0.9747697307676272, 0.5775165988663097, 0.2694337203265058, 0.5915625504553477, 0.7908011628894027]
    """
    
    def __init__(self):
        # These genes were evolved through 100 generations
        self.genes = [0.9970462326330012, 0.9747697307676272, 0.5775165988663097, 0.2694337203265058, 0.5915625504553477, 0.7908011628894027]
        
        # Required for tournament compatibility
        self.student_name = "Doug Dahl"
        
        super().__init__(
            name="King kong",
            description="climb to the top of the empire state building"
        )
    
    def choose_action(self) -> bool:
        """
        IMPROVED decision logic - AGGRESSIVE VERSION
        More likely to retaliate, less exploitable
        """
        
        # First 3 rounds: use initial cooperation gene
        if self.round_num < 3:
            return random.random() < self.genes[0]
        
        # Calculate memory window
        memory_length = max(1, int(self.genes[4] * 10) + 1)
        recent_history = self.history[-memory_length:]
        cooperation_rate = sum(recent_history) / len(recent_history)
        
        # AGGRESSIVE STRATEGY: Higher threshold for cooperation
        
        # Only cooperate if opponent is VERY cooperative (>80%)
        if cooperation_rate > 0.8:
            return random.random() < self.genes[1]  # gene[1] should evolve HIGH
        
        # If somewhat cooperative (50-80%), be cautious
        elif cooperation_rate > 0.5:
            # Mix of cooperation and defection
            coop_prob = self.genes[1] * (cooperation_rate - 0.5) * 2  # Scale 0-1
            return random.random() < coop_prob
        
        # If aggressive (<50%), retaliate hard
        else:
            # Mostly defect, with small chance to forgive
            if random.random() < self.genes[3] * 0.3:  # Reduced forgiveness
                return INVEST
            else:
                return UNDERCUT



# Convenience function for tournament loading
def get_agent():
    """Return an instance of this agent for tournament use"""
    return DougDahlAgent()


if __name__ == "__main__":
    # Test that the agent can be instantiated
    agent = get_agent()
    print(f"✅ Agent loaded successfully: {agent.name}")
    print(f"   Genes: {agent.genes}")
    print(f"   Description: {agent.description}")
