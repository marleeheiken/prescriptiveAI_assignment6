"""
Game Engine
Core game logic and tournament management
"""
from typing import Tuple, List, Dict
from dataclasses import dataclass
import pandas as pd
import numpy as np

# Payoff matrix
PAYOFF_MATRIX = {
    (True, True): (3, 3),      # Both invest
    (True, False): (0, 5),     # Investor loses
    (False, True): (5, 0),     # Undercutter wins
    (False, False): (1, 1)     # Price war
}

def get_payoffs(action1: bool, action2: bool) -> Tuple[int, int]:
    """Get payoffs for both players"""
    return PAYOFF_MATRIX[(action1, action2)]


@dataclass
class GameRound:
    """Represents a single round"""
    round_num: int
    player1_action: bool
    player2_action: bool
    player1_payoff: int
    player2_payoff: int


class Game:
    """Manages a single game between two agents"""
    
    def __init__(self, agent1, agent2, num_rounds: int = 100):
        self.agent1 = agent1
        self.agent2 = agent2
        self.num_rounds = num_rounds
        self.rounds = []
        self.score1 = 0
        self.score2 = 0
    
    def play(self) -> Tuple[int, int]:
        """Play the full game and return final scores"""
        self.agent1.reset()
        self.agent2.reset()
        self.rounds = []
        self.score1 = 0
        self.score2 = 0
        
        for round_num in range(self.num_rounds):
            action1 = self.agent1.choose_action()
            action2 = self.agent2.choose_action()
            
            payoff1, payoff2 = get_payoffs(action1, action2)
            
            self.score1 += payoff1
            self.score2 += payoff2
            
            self.rounds.append(GameRound(
                round_num=round_num + 1,
                player1_action=action1,
                player2_action=action2,
                player1_payoff=payoff1,
                player2_payoff=payoff2
            ))
            
            self.agent1.update_history(action1, action2)
            self.agent2.update_history(action2, action1)
        
        return self.score1, self.score2
    
    def get_dataframe(self) -> pd.DataFrame:
        """Convert game results to a pandas DataFrame for analysis"""
        data = []
        for round_data in self.rounds:
            data.append({
                'Round': round_data.round_num,
                f'{self.agent1.name}_Action': 'Invest' if round_data.player1_action else 'Undercut',
                f'{self.agent2.name}_Action': 'Invest' if round_data.player2_action else 'Undercut',
                f'{self.agent1.name}_Payoff': round_data.player1_payoff,
                f'{self.agent2.name}_Payoff': round_data.player2_payoff,
                f'{self.agent1.name}_Cumulative': sum(r.player1_payoff for r in self.rounds[:round_data.round_num]),
                f'{self.agent2.name}_Cumulative': sum(r.player2_payoff for r in self.rounds[:round_data.round_num])
            })
        return pd.DataFrame(data)

class Tournament:
    """Manages a round-robin tournament"""
    
    def __init__(self, agents: List, rounds_per_match: int = 100, num_tournaments: int = 1):
        self.agents = agents
        self.rounds_per_match = rounds_per_match
        self.num_tournaments = num_tournaments
        self.results = {}
        self.total_scores = {agent.name: 0 for agent in agents}
        self.match_results = []
        self.tournament_scores = []
    
    def run_tournament(self):
        """Run a complete round-robin tournament"""
        print(f"Running {self.num_tournaments} tournament(s) with {len(self.agents)} agents...")
        
        for tournament_num in range(self.num_tournaments):
            if self.num_tournaments > 1:
                print(f"\nTournament {tournament_num + 1}/{self.num_tournaments}")
            
            # Reset agents between tournaments
            for agent in self.agents:
                if hasattr(agent, 'reset'):
                    agent.reset()
            
            tournament_scores = {agent.name: 0 for agent in self.agents}
            total_matches = len(self.agents) * (len(self.agents) - 1)
            match_count = 0
            
            for i, agent1 in enumerate(self.agents):
                for j, agent2 in enumerate(self.agents):
                    if i != j:
                        match_count += 1
                        if self.num_tournaments == 1:
                            print(f"Match {match_count}/{total_matches}: {agent1.name} vs {agent2.name}")
                        
                        game = Game(agent1, agent2, self.rounds_per_match)
                        score1, score2 = game.play()
                        
                        match_key = (agent1.name, agent2.name)
                        if tournament_num == 0:
                            self.results[match_key] = []
                        self.results[match_key].append((score1, score2))
                        
                        tournament_scores[agent1.name] += score1
                        self.total_scores[agent1.name] += score1
                        
                        # Store detailed match results
                        self.match_results.append({
                            'Tournament': tournament_num + 1,
                            'Agent1': agent1.name,
                            'Agent2': agent2.name,
                            'Agent1_Score': score1,
                            'Agent2_Score': score2,
                            'Winner': agent1.name if score1 > score2 else agent2.name if score2 > score1 else 'Tie'
                        })
            
            self.tournament_scores.append(tournament_scores)
        
        print("Tournament complete!")
    
    def get_rankings(self) -> List[Tuple[str, int]]:
        """Get tournament rankings sorted by total score"""
        return sorted(self.total_scores.items(), key=lambda x: x[1], reverse=True)
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get tournament results as a pandas DataFrame"""
        return pd.DataFrame(self.match_results)
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the tournament"""
        import numpy as np
        df = self.get_results_dataframe()
        
        stats = {}
        for agent_name in self.total_scores.keys():
            agent_matches = df[(df['Agent1'] == agent_name) | (df['Agent2'] == agent_name)]
            
            wins = len(agent_matches[agent_matches['Winner'] == agent_name])
            total_matches = len(agent_matches)
            
            agent1_scores = df[df['Agent1'] == agent_name]['Agent1_Score'].tolist()
            agent2_scores = df[df['Agent2'] == agent_name]['Agent2_Score'].tolist()
            all_scores = agent1_scores + agent2_scores
            
            # Calculate per-tournament statistics
            tournament_totals = [t[agent_name] for t in self.tournament_scores]
            
            stats[agent_name] = {
                'total_score': self.total_scores[agent_name],
                'wins': wins,
                'total_matches': total_matches,
                'win_rate': wins / total_matches if total_matches > 0 else 0,
                'avg_score_per_match': sum(all_scores) / len(all_scores) if all_scores else 0,
                'avg_per_tournament': np.mean(tournament_totals) if tournament_totals else 0,
                'std_dev': np.std(tournament_totals) if len(tournament_totals) > 1 else 0
            }
        
        return stats
    
    def create_payoff_matrix(self) -> pd.DataFrame:
        """Create a payoff matrix showing average results between all agent pairs"""
        agent_names = [agent.name for agent in self.agents]
        matrix = pd.DataFrame(index=agent_names, columns=agent_names, dtype=float)
        
        for (agent1, agent2), scores in self.results.items():
            avg_score = np.mean([s[0] for s in scores]) if isinstance(scores, list) else scores[0]
            matrix.loc[agent1, agent2] = avg_score
            
        return matrix