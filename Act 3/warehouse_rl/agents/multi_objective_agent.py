#!/usr/bin/env python3
"""
Multi-Objective Optimization Agent - Demonstrates Pareto frontier tradeoffs

This agent shows clear tradeoffs between profit maximization and service quality.
It uses a controlled order environment to ensure meaningful optimization choices.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import copy
from .standardized_agents import BaselineAgent

class ControlledOrderGenerator:
    """Simplified order generator for multi-objective demo"""
    
    def __init__(self, arrival_rate: float = 0.4, seed: Optional[int] = None):
        self.arrival_rate = arrival_rate
        self.rng = np.random.RandomState(seed)
        self.next_order_id = 1
        
        # Simplified order patterns for clear tradeoffs
        self.order_types = {
            'quick_small': {'items': 1, 'value': 15, 'weight': 0.5},
            'medium': {'items': 3, 'value': 60, 'weight': 0.3},
            'large_valuable': {'items': 5, 'value': 150, 'weight': 0.2}
        }
    
    def generate_orders(self, current_time: int, queue_length: int = 0) -> List[Dict]:
        """Generate orders at a controlled rate"""
        # Simple Poisson arrival
        num_orders = self.rng.poisson(self.arrival_rate)
        
        orders = []
        for _ in range(num_orders):
            order_type = self.rng.choice(
                list(self.order_types.keys()), 
                p=[self.order_types[k]['weight'] for k in self.order_types.keys()]
            )
            
            order_info = self.order_types[order_type]
            items = self.rng.choice(50, order_info['items'], replace=False).tolist()
            
            order = {
                'id': self.next_order_id,
                'items': items,
                'value': order_info['value'] * self.rng.uniform(0.9, 1.1),
                'arrival_time': current_time,
                'status': 'pending'
            }
            orders.append(order)
            self.next_order_id += 1
        
        return orders

class MultiObjectiveAgent(BaselineAgent):
    """
    Agent that demonstrates multi-objective optimization tradeoffs
    """
    
    def __init__(self, env, profit_weight: float = 0.5, service_weight: float = 0.5):
        super().__init__(env)
        self.name = f"MultiObjective_P{profit_weight:.1f}_S{service_weight:.1f}"
        
        # Objective weights (must sum to 1.0)
        total_weight = profit_weight + service_weight
        self.profit_weight = profit_weight / total_weight
        self.service_weight = service_weight / total_weight
        
        # Performance tracking
        self.timestep_profits = []
        self.timestep_service_rates = []
        self.objective_scores = []
        
        # Decision parameters
        self.optimal_employee_ratio = 2.5  # orders per employee
        self.service_threshold = 0.8  # target completion rate
        
        # Use controlled order generation for clearer tradeoffs
        self.controlled_generator = ControlledOrderGenerator(arrival_rate=0.35, seed=42)
        
    def reset(self):
        """Reset agent state"""
        super().reset()
        self.timestep_profits = []
        self.timestep_service_rates = []
        self.objective_scores = []
        
    def get_action(self, observation: Dict) -> Dict:
        """Generate action optimizing weighted objectives"""
        
        # Set preferred wage for wage strategy agents
        if hasattr(self, 'wage_level'):
            self.env._preferred_wage = self.wage_level
        
        # Extract current state
        financial = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']
        current_time = observation['time'][0]
        
        current_profit = financial[0]
        current_queue_length = np.sum(queue_info[:, 0] > 0)  # Count non-empty orders
        num_employees = np.sum(employee_info[:, 0] > 0)  # Count active employees
        
        # Calculate current service quality (completion rate proxy)
        workload_ratio = current_queue_length / max(1, num_employees)
        estimated_service_rate = max(0, min(1, 1.2 - (workload_ratio * 0.15)))
        
        # Multi-objective decision making
        action = {
            'staffing_action': self._get_multi_objective_staffing(
                current_profit, workload_ratio, num_employees, estimated_service_rate
            ),
            'layout_swap': self._get_strategic_layout_action(current_time, workload_ratio),
            'order_assignments': self._get_priority_assignments(queue_info, employee_info)
        }
        
        # Track performance
        self.timestep_profits.append(current_profit)
        self.timestep_service_rates.append(estimated_service_rate)
        
        # Calculate combined objective score
        normalized_profit = max(-1, min(1, current_profit / 500))  # Normalize to [-1, 1]
        objective_score = (self.profit_weight * normalized_profit + 
                          self.service_weight * estimated_service_rate)
        self.objective_scores.append(objective_score)
        
        return action
    
    def _get_multi_objective_staffing(self, current_profit: float, workload_ratio: float, 
                                    num_employees: int, service_rate: float) -> int:
        """Staffing decisions balancing profit vs service with wage choices"""
        
        # Profit-focused logic: minimize costs by hiring low-wage workers or firing
        if self.profit_weight > 0.6:
            if current_profit < -50 and num_employees > 1:
                return 2  # Fire aggressively to cut costs
            elif workload_ratio < 1.5 and num_employees > 3:
                return 2  # Fire when not busy
            elif workload_ratio > 4 and current_profit > 0:
                return 1  # Hire low-wage workers (cheap but slow)
            elif workload_ratio > 7 and current_profit > 100:
                return 3  # Hire manager only when very profitable
        
        # Service-focused logic: hire high-wage workers for fast service
        elif self.service_weight > 0.6:
            if workload_ratio > 2.0 and num_employees < 10:
                if current_profit > 50:
                    return 5  # Hire high-wage workers (expensive but fast)
                else:
                    return 4  # Hire medium-wage workers (balanced)
            elif workload_ratio > 5 and num_employees < 8:
                return 3  # Hire manager for coordination
            elif workload_ratio < 0.8 and num_employees > 5:
                return 2  # Only fire when very over-staffed
        
        # Balanced approach: strategic wage decisions
        else:
            if workload_ratio > 5 and current_profit > 100:
                return 4  # Hire medium-wage workers when profitable and busy
            elif workload_ratio > 3 and current_profit > 0:
                return 1  # Hire low-wage workers when moderately busy
            elif workload_ratio < 1.0 and current_profit < -50:
                return 2  # Fire when over-staffed and losing money
            elif workload_ratio > 8:
                return 3  # Hire manager in crisis
        
        return 0
    
    def _get_strategic_layout_action(self, current_time: int, workload_ratio: float) -> List[int]:
        """Layout optimization based on service vs efficiency tradeoffs"""
        
        # Service-focused: only optimize when not busy
        if self.service_weight > 0.6 and workload_ratio > 2.5:
            return [0, 0]  # Don't disrupt operations when busy
        
        # Profit-focused: optimize more aggressively for long-term gains
        if self.profit_weight > 0.6:
            optimization_frequency = 80  # More frequent optimization
        else:
            optimization_frequency = 150  # Less frequent to avoid service disruption
        
        if current_time % optimization_frequency == 0 and np.random.random() < 0.3:
            grid_size = self.env.grid_width * self.env.grid_height
            # Focus on moving popular items (first 20% of item types) to better positions
            popular_positions = list(range(grid_size // 4))  # First quarter of grid
            other_positions = list(range(grid_size // 4, grid_size))
            
            pos1 = np.random.choice(popular_positions)
            pos2 = np.random.choice(other_positions)
            return [pos1, pos2]
        
        return [0, 0]
    
    def _get_priority_assignments(self, queue_info: np.ndarray, employee_info: np.ndarray) -> List[int]:
        """Order assignment based on objective priorities"""
        
        assignments = [0] * 20
        
        num_employees = int(np.sum(employee_info[:, 0] > 0))
        active_orders = queue_info[queue_info[:, 0] > 0]  # Non-empty orders
        
        if num_employees == 0 or len(active_orders) == 0:
            return assignments
        
        # Service-focused: assign orders to minimize wait times (FIFO)
        if self.service_weight > 0.6:
            # Sort by arrival time (oldest first)
            order_priorities = list(range(len(active_orders)))
        else:
            # Profit-focused: prioritize by value
            order_values = active_orders[:, 1]  # Value column
            order_priorities = sorted(range(len(active_orders)), 
                                    key=lambda i: order_values[i], reverse=True)
        
        # Assign top priority orders to available employees
        assignments_made = 0
        for order_idx in order_priorities:
            if assignments_made >= min(num_employees, 8):  # Limit concurrent assignments
                break
            
            # Assign to next available employee
            employee_idx = (assignments_made % num_employees) + 1
            assignments[order_idx] = employee_idx
            assignments_made += 1
        
        return assignments
    
    def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics for analysis"""
        if not self.timestep_profits:
            return {
                'avg_profit': 0, 'avg_service_rate': 0, 'avg_objective_score': 0,
                'profit_weight': self.profit_weight, 'service_weight': self.service_weight
            }
        
        return {
            'avg_profit': np.mean(self.timestep_profits[-500:]),  # Last 500 timesteps
            'avg_service_rate': np.mean(self.timestep_service_rates[-500:]),
            'avg_objective_score': np.mean(self.objective_scores[-500:]),
            'final_profit': self.timestep_profits[-1] if self.timestep_profits else 0,
            'final_service_rate': self.timestep_service_rates[-1] if self.timestep_service_rates else 0,
            'profit_weight': self.profit_weight,
            'service_weight': self.service_weight,
            'profit_std': np.std(self.timestep_profits[-500:]) if len(self.timestep_profits) > 10 else 0,
            'service_std': np.std(self.timestep_service_rates[-500:]) if len(self.timestep_service_rates) > 10 else 0
        }

class WageStrategyAgent(MultiObjectiveAgent):
    """Agent that tests specific wage levels"""
    
    def __init__(self, env, wage_label: str, wage_level: float):
        # Use balanced objectives to focus on wage effects
        super().__init__(env, profit_weight=0.5, service_weight=0.5)
        self.wage_level = wage_level
        self.name = f"Wage_{wage_label}"
        
    def _get_multi_objective_staffing(self, current_profit: float, workload_ratio: float, 
                                    num_employees: int, service_rate: float) -> int:
        """Staffing decisions based on specific wage strategy"""
        
        # Always use the assigned wage level when hiring
        if workload_ratio > 3.0 and num_employees < 10:
            # Map wage level to action
            if self.wage_level <= 0.25:
                return 1  # Low wage
            elif self.wage_level <= 0.45:
                return 4  # Medium wage  
            else:
                return 5  # High wage
        elif workload_ratio < 1.0 and num_employees > 3:
            return 2  # Fire when over-staffed
        elif workload_ratio > 6 and num_employees < 8:
            return 3  # Hire manager in crisis
        
        return 0

def create_multi_objective_agents(env) -> Dict[str, MultiObjectiveAgent]:
    """Create agents with different wage strategies"""
    
    agents = {}
    
    # Test wage levels including severe diminishing returns beyond $2.00
    wage_levels = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 
                  1.00, 1.20, 1.40, 1.60, 1.80, 2.00, 2.50, 3.00, 3.50, 4.00]
    
    for wage in wage_levels:
        agent = WageStrategyAgent(env, f"${wage:.2f}", wage)
        agents[agent.name] = agent
    
    return agents