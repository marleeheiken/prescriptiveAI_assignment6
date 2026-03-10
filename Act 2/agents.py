"""
Game Theory Agents
All agent strategies for the Market Entry Game simulation
"""
from abc import ABC, abstractmethod
import random

# Game constants
INVEST = True
UNDERCUT = False

class Agent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, description: str = "", noise: float = 0.0):
        self.name = name
        self.description = description
        self.noise = noise
        self.reset()
    
    def reset(self):
        """Reset agent state for a new game"""
        self.history = []
        self.my_history = []
        self.round_num = 0
    
    @abstractmethod
    def choose_action(self) -> bool:
        """Choose an action based on current state"""
        pass
    
    def _apply_noise(self, intended_action: bool) -> bool:
        """Apply noise to the intended action"""
        if self.noise > 0 and random.random() < self.noise:
            return not intended_action
        return intended_action
    
    def update_history(self, my_action: bool, opponent_action: bool):
        """Update the agent's memory"""
        self.my_history.append(my_action)
        self.history.append(opponent_action)
        self.round_num += 1
    
    def __str__(self):
        return self.name


class AlwaysInvestAgent(Agent):
    """Always cooperates"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Always Invest", "Always invests in market development", noise)
    
    def choose_action(self) -> bool:
        return self._apply_noise(INVEST)


class AlwaysUndercutAgent(Agent):
    """Always defects"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Always Undercut", "Always undercuts competitors", noise)
    
    def choose_action(self) -> bool:
        return self._apply_noise(UNDERCUT)


class TitForTatAgent(Agent):
    """Copies opponent's last move"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Tit-for-Tat", "Starts friendly, then copies opponent", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) == 0:
            intended_action = INVEST
        else:
            intended_action = self.history[-1]
        return self._apply_noise(intended_action)


class GrimTriggerAgent(Agent):
    """Cooperates until betrayed once, then defects forever"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Grim Trigger", "Invests until betrayed once, then undercuts forever", noise)
        self.betrayed = False
    
    def reset(self):
        super().reset()
        self.betrayed = False
    
    def choose_action(self) -> bool:
        if self.betrayed:
            intended_action = UNDERCUT
        elif UNDERCUT in self.history:
            self.betrayed = True
            intended_action = UNDERCUT
        else:
            intended_action = INVEST
        return self._apply_noise(intended_action)


class PavlovAgent(Agent):
    """Win-Stay-Lose-Shift strategy"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Pavlov", "Win-Stay-Lose-Shift strategy", noise)
        self.last_payoff = None
    
    def reset(self):
        super().reset()
        self.last_payoff = None
    
    def choose_action(self) -> bool:
        if len(self.my_history) == 0:
            intended_action = INVEST
        elif self.last_payoff in [3, 5]:
            intended_action = self.my_history[-1]
        else:
            intended_action = not self.my_history[-1]
        return self._apply_noise(intended_action)
    
    def update_history(self, my_action: bool, opponent_action: bool):
        from game_engine import get_payoffs
        payoff, _ = get_payoffs(my_action, opponent_action)
        self.last_payoff = payoff
        super().update_history(my_action, opponent_action)


class RandomAgent(Agent):
    """Randomly chooses actions"""
    def __init__(self, cooperate_prob: float = 0.5, noise: float = 0.0):
        super().__init__(f"Random ({cooperate_prob:.1f})", 
                        f"Randomly invests {cooperate_prob*100:.0f}% of the time", noise)
        self.cooperate_prob = cooperate_prob
    
    def choose_action(self) -> bool:
        intended_action = random.random() < self.cooperate_prob
        return self._apply_noise(intended_action)


class TitForTwoTatsAgent(Agent):
    """Only retaliates after two consecutive defections"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Tit-for-Two-Tats", "Tolerates one betrayal, retaliates after two", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) < 2:
            intended_action = INVEST
        else:
            intended_action = not (self.history[-1] == UNDERCUT and self.history[-2] == UNDERCUT)
        return self._apply_noise(intended_action)


class GenerousTitForTatAgent(Agent):
    """Tit-for-Tat but occasionally forgives"""
    def __init__(self, forgiveness_prob: float = 0.1, noise: float = 0.0):
        super().__init__("Generous Tit-for-Tat", 
                        f"Tit-for-Tat with {forgiveness_prob*100:.0f}% forgiveness", noise)
        self.forgiveness_prob = forgiveness_prob
    
    def choose_action(self) -> bool:
        if len(self.history) == 0:
            intended_action = INVEST
        elif self.history[-1] == UNDERCUT:
            if random.random() < self.forgiveness_prob:
                intended_action = INVEST
            else:
                intended_action = UNDERCUT
        else:
            intended_action = INVEST
        return self._apply_noise(intended_action)


class AdaptiveAgent(Agent):
    """Adapts strategy based on opponent's behavior"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Adaptive", "Adapts to opponent's cooperation rate", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) < 5:
            intended_action = INVEST
        else:
            # Calculate opponent's cooperation rate in last 10 rounds
            recent_history = self.history[-10:]
            coop_rate = sum(recent_history) / len(recent_history)
            
            # Match opponent's cooperation rate with slight bias toward cooperation
            intended_action = random.random() < (coop_rate + 0.1)
        return self._apply_noise(intended_action)
    
class SuspiciousTitForTatAgent(Agent):
    """Starts with defection, then copies opponent (opposite of TFT)"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Suspicious Tit-for-Tat", 
                        "Starts hostile, then copies opponent", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) == 0:
            intended_action = UNDERCUT  # Start hostile
        else:
            intended_action = self.history[-1]  # Copy opponent
        return self._apply_noise(intended_action)


class GradualAgent(Agent):
    """Cooperates but punishes defection with escalating retaliation"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Gradual", 
                        "Escalates punishment after each betrayal", noise)
        self.betrayal_count = 0
        self.punishing = False
        self.punishment_left = 0
        self.calm_down_left = 0
    
    def reset(self):
        super().reset()
        self.betrayal_count = 0
        self.punishing = False
        self.punishment_left = 0
        self.calm_down_left = 0
    
    def choose_action(self) -> bool:
        # If calming down (cooperating after punishment)
        if self.calm_down_left > 0:
            self.calm_down_left -= 1
            intended_action = INVEST
        # If currently punishing
        elif self.punishing:
            self.punishment_left -= 1
            if self.punishment_left == 0:
                self.punishing = False
                self.calm_down_left = 2  # Cooperate twice after punishment
            intended_action = UNDERCUT
        # Check if opponent just defected
        elif len(self.history) > 0 and self.history[-1] == UNDERCUT:
            self.betrayal_count += 1
            self.punishing = True
            self.punishment_left = self.betrayal_count  # Punish N times for Nth betrayal
            intended_action = UNDERCUT
        else:
            intended_action = INVEST
        
        return self._apply_noise(intended_action)


class HardMajorityAgent(Agent):
    """Defects if opponent has defected more than cooperated overall"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Hard Majority", 
                        "Defects if opponent defects >50% of time", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) == 0:
            intended_action = INVEST
        else:
            cooperation_count = sum(self.history)
            defection_count = len(self.history) - cooperation_count
            
            if defection_count > cooperation_count:
                intended_action = UNDERCUT
            else:
                intended_action = INVEST
        
        return self._apply_noise(intended_action)


class SoftMajorityAgent(Agent):
    """Cooperates if opponent has cooperated more than defected overall"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Soft Majority", 
                        "Cooperates if opponent cooperates >=50% of time", noise)
    
    def choose_action(self) -> bool:
        if len(self.history) == 0:
            intended_action = INVEST
        else:
            cooperation_count = sum(self.history)
            defection_count = len(self.history) - cooperation_count
            
            if cooperation_count >= defection_count:
                intended_action = INVEST
            else:
                intended_action = UNDERCUT
        
        return self._apply_noise(intended_action)


class ProberAgent(Agent):
    """Tests opponent with defections, then exploits or cooperates"""
    def __init__(self, noise: float = 0.0):
        super().__init__("Prober", 
                        "Tests opponent's response, then adapts", noise)
        self.testing_phase = True
    
    def reset(self):
        super().reset()
        self.testing_phase = True
    
    def choose_action(self) -> bool:
        # Testing sequence: D, C, C (defect once, cooperate twice)
        if self.round_num == 0:
            intended_action = UNDERCUT  # Test with defection
        elif self.round_num == 1 or self.round_num == 2:
            intended_action = INVEST  # Cooperate to see response
        elif self.round_num == 3:
            # Analyze opponent's response to initial defection
            self.testing_phase = False
            # If opponent retaliated (defected back in round 1 or 2)
            if UNDERCUT in self.history[1:3]:
                # Play Tit-for-Tat (opponent is responsive)
                intended_action = self.history[-1]
            else:
                # Opponent is exploitable (didn't retaliate)
                intended_action = UNDERCUT
        else:
            # After testing phase
            if UNDERCUT in self.history[1:3]:
                # Play Tit-for-Tat
                intended_action = self.history[-1]
            else:
                # Always defect (exploit sucker)
                intended_action = UNDERCUT
        
        return self._apply_noise(intended_action)