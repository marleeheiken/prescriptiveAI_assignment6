#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for 
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization 
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.
    
    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment  
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        
        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = True
        
        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []
        
        self.integrated_metrics = []
        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }
        
        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False
        self.reset()

    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        self.phase1_swap_count = 0
        self.phase2_swap_count = 0
        self.layout_metrics = []
        self._profit_ema_short = None
        self._profit_ema_long = None
        # TODO: Reset any neural network states, replay buffers, etc.
    
    '''
    def get_action(self, observation: Dict) -> Dict:
        """
        Generate action based on observation.
        Current implementation is intentionally terrible - students should improve!
        """
        
        # Extract basic info from observation
        current_timestep = observation['time'][0]
        financial_state = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']
        
        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }
        
        # Track layout performance every 100 steps
        if observation['time'][0] % 100 == 0:
            self.track_layout_performance()
            
        self.action_history.append(action.copy())
        
        return action
    '''

    def get_action(self, observation: Dict) -> Dict:
        """
        Week 2: Integrated optimization across staffing, layout, and order assignments
        """
        current_timestep = observation['time'][0]
        financial_state = observation['financial']
        queue_info = observation['order_queue']
        employee_info = observation['employees']

        # Compute actions
        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }

        # Track integrated performance every 100 steps
        if current_timestep % 100 == 0:
            self.track_integrated_performance()

        # Record action for later analysis
        self.action_history.append(action.copy())

        return action
    
    def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
        """
        WEEK 2 STEP 1: Staffing decisions - students should improve this!
        
        Current problems:
        - Ignores queue length and workload
        - Random decisions regardless of profit
        - No consideration of employee efficiency

        WEEK 2 STEP 1: Economic staffing optimization
        Make hiring/firing decisions based on simple business economics
        """
        
        # Extract economic and operational data
        current_profit = financial_state[0]
        revenue = financial_state[1]
        costs = financial_state[2]
        burn_rate = financial_state[3]
        
        num_employees = np.sum(employee_info[:, 0] > 0)
        queue_length = len(self.env.order_queue.orders)
        has_manager = np.any(employee_info[:, 5] == 1)
        
        # TODO: Calculate business indicators
        
        # Queue pressure (demand vs worker capacity)
        queue_pressure = queue_length / max(1, num_employees)
        
        # Profit efficiency (how productive the workforce is)
        profit_per_employee = current_profit / max(1, num_employees)
        
        # Track profit trend
        if not hasattr(self, "profit_history"):
            self.profit_history = []
        self.profit_history.append(current_profit)
        
        profit_trend = 0
        if len(self.profit_history) > 5:
            recent_avg = np.mean(self.profit_history[-3:])
            older_avg = np.mean(self.profit_history[-6:-3])
            profit_trend = recent_avg - older_avg
        
        # Algorithm Parameters
        hire_threshold = 3.0
        fire_threshold = 1.5
        
        profit_threshold = 1000
        manager_threshold = 2000
        
        min_staff = 2
        if num_employees <= min_staff:
            return 0  # Never fire below min_staff
        

        
        # TODO: Apply economic decision logic        
        # HIRE MANAGER when profitable and no manager exists
        if current_profit > manager_threshold and not has_manager:
            return 2  # Manager hire action
        
        # HIRING LOGIC
        if queue_pressure > hire_threshold and current_profit > profit_threshold:
            return 1  # Hire employee
        
        # FIRING LOGIC
        if queue_pressure < fire_threshold and num_employees > min_staff:
            # Only fire if losing money or clearly inefficient
            if current_profit < 0 or profit_per_employee < 200:
                return -1  # Fire employee
        
        if queue_pressure > hire_threshold or queue_length > 50:
            return 1
        # Buffer zone prevents rapid flip-flopping
        
        return 0  # No staffing change

    def _get_naive_layout_action(self, current_timestep) -> list:
        """
        TWO-PHASE LAYOUT OPTIMIZATION:
        Phase 1: Frequency-based optimization every 100 steps
        Phase 2: Co-occurrence clustering every 200 steps (less frequent)
        """

        grid = self.env.warehouse_grid
        delivery_positions = getattr(
            grid,
            "truck_bay_positions",
            [(grid.width // 2, grid.height // 2)]
        )

        # Phase 1: Frequency
        if current_timestep % 100 == 0:
            item_frequency = grid.item_access_frequency
            if item_frequency is not None and len(item_frequency) > 0:
                active_items = np.where(item_frequency > 0)[0]
                if len(active_items) > 0:
                    hot_thresh = np.percentile(item_frequency[active_items], 75)
                    hot_items = active_items[item_frequency[active_items] >= hot_thresh]

                    for item in hot_items:
                        locations = grid.find_item_locations(int(item))
                        if not locations:
                            continue
                        item_pos = locations[0]
                        current_distance = min(
                            grid.manhattan_distance(item_pos, d) for d in delivery_positions
                        )
                        if current_distance <= 3:
                            continue

                        swap = self._find_closer_position(item_pos, delivery_positions)
                        if swap is not None:
                            self.phase1_swap_count += 1
                            return swap
                        
                        current_index = item_pos[1] * grid.width + item_pos[0]

                        # Search grid for empty closer spot
                        for y in range(grid.height):
                            for x in range(grid.width):
                                if grid.cell_types[y, x] != 1 or (x, y) == item_pos:
                                    continue
                                new_distance = min(
                                    grid.manhattan_distance((x, y), d) for d in delivery_positions
                                )
                                if new_distance >= current_distance:
                                    continue
                                if grid.get_item_at_position(x, y) is None:
                                    target_index = y * grid.width + x
                                    self.phase1_swap_count += 1
                                    return [current_index, target_index]

        # Phase 2: If no frequency-based improvement found, try co-occurrence clustering
        if current_timestep % 200 == 0:  # Less frequent than hot-item optimization
            cooccurrence_swap = self._find_cooccurrence_swap()
            if cooccurrence_swap:
                self.phase2_swap_count += 1
                return cooccurrence_swap

        # No improvement found
        return [0, 0]
    
    def _find_cooccurrence_swap(self):
        """
        Greedy clustering algorithm for association-based spatial optimization.
        
        Algorithm: Scan all item pairs for clustering opportunities,
        calculate benefit for each, and greedily select highest-benefit move.
        
        Returns swap that maximizes benefit = co-occurrence_frequency × distance_saved
        """
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence
        
        # Greedy search parameters
        min_cooccurrence = 3      # Minimum frequency threshold
        min_distance = 4          # Minimum distance threshold for clustering
        best_benefit = 0          # Track best benefit found
        best_swap = None          # Track best swap candidate
        
        if cooccurrence is None or cooccurrence.size == 0:
            return None

        num_items = cooccurrence.shape[0]

        # Greedy benefit maximization over all unique item pairs.
        for item1 in range(num_items):
            for item2 in range(item1 + 1, num_items):
                cooccurrence_count = cooccurrence[item1, item2]
                if cooccurrence_count <= min_cooccurrence:
                    continue

                item1_locations = grid.find_item_locations(int(item1))
                item2_locations = grid.find_item_locations(int(item2))
                if not item1_locations or not item2_locations:
                    continue

                item1_pos = item1_locations[0]
                item2_pos = item2_locations[0]
                current_distance = grid.manhattan_distance(item1_pos, item2_pos)
                if current_distance <= min_distance:
                    continue

                benefit = cooccurrence_count * current_distance
                if benefit > best_benefit:
                    candidate_swap = self._find_adjacency_swap(item1_pos, item2_pos)
                    if candidate_swap is not None:
                        best_benefit = benefit
                        best_swap = candidate_swap
        
        return best_swap  # Return highest-benefit clustering move

    def _find_adjacency_swap(self, source_pos, target_pos):
        """Find a swap that moves source_pos into a storage cell adjacent to target_pos."""
        grid = self.env.warehouse_grid
        source_idx = source_pos[1] * grid.width + source_pos[0]

        adjacent_positions = [
            (target_pos[0] + 1, target_pos[1]),
            (target_pos[0] - 1, target_pos[1]),
            (target_pos[0], target_pos[1] + 1),
            (target_pos[0], target_pos[1] - 1),
        ]

        for x, y in adjacent_positions:
            if not (0 <= x < grid.width and 0 <= y < grid.height):
                continue
            if grid.cell_types[y, x] != 1:
                continue
            if (x, y) == source_pos:
                continue

            target_idx = y * grid.width + x
            return [source_idx, target_idx]

        return None

    def _find_closer_position(self, current_pos, delivery_positions):
        """
        Greedy neighborhood search for better item placement.
        
        Algorithm: Exhaustive search of all storage positions to find
        the position that minimizes distance to delivery points.
        
        Returns [current_index, target_index] if beneficial swap found.
        """
        grid = self.env.warehouse_grid
        current_idx = current_pos[1] * grid.width + current_pos[0]
        current_dist = min(
            grid.manhattan_distance(current_pos, delivery_pos)
            for delivery_pos in delivery_positions
        )

        # Exhaustive neighborhood search over all storage coordinates.
        best_target_idx = None
        best_improvement = 0

        for y in range(grid.height):
            for x in range(grid.width):
                # Only consider storage cells and skip current position.
                if grid.cell_types[y, x] != 1 or (x, y) == current_pos:
                    continue

                candidate_dist = min(
                    grid.manhattan_distance((x, y), delivery_pos)
                    for delivery_pos in delivery_positions
                )
                improvement = current_dist - candidate_dist

                # Require strict minimum threshold: >1 step closer.
                if improvement > 1 and improvement > best_improvement:
                    best_improvement = improvement
                    best_target_idx = y * grid.width + x

        if best_target_idx is not None:
            return [current_idx, best_target_idx]

        return None  # No better position found
    
    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """
        WEEK 2 STEP 2: Order assignment - students should improve this!
        
        Current problems:
        - Ignores employee locations
        - No consideration of order priority/value
        - Random assignments regardless of efficiency
        - Doesn't check if employees are actually available

        WEEK 2 STEP 2: Worker-to-order matching optimization
        Optimally match idle workers to pending orders
        """
        
        max_assignments = 20
        assignments = [0] * max_assignments

        # --- Step 1: Find idle, non-manager workers ---
        idle_workers = [
            i for i in range(len(employee_info))
            if employee_info[i, 0] > 0       # active
            and employee_info[i, 1] == 0     # idle
            and employee_info[i, 5] == 0     # not manager
        ]
        if not idle_workers:
            return assignments

        # --- Step 2: Get pending orders ---
        orders = queue_info.orders[:max_assignments]
        if not orders:
            return assignments

        # --- Step 3: Build worker-order score list ---
        grid = self.env.warehouse_grid
        max_order_value = max(1, max(o.value for o in orders))
        distance_weight = 0.7
        value_weight = 0.3

        scored_pairs = []  # (score, worker_idx, order_idx)

        for w_idx in idle_workers:
            wx, wy = int(employee_info[w_idx, 0]), int(employee_info[w_idx, 1])
            for o_idx, order in enumerate(orders):
                # Compute minimum Manhattan distance to any walkable adjacent cell of order items
                min_dist = float("inf")
                for item_id in order.items:
                    for ix, iy in grid.find_item_locations(int(item_id)):
                        adj_cells = [
                            (ix + dx, iy + dy)
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                            if grid.is_walkable(ix + dx, iy + dy)
                        ]
                        if adj_cells:
                            min_dist = min(min_dist, min(grid.manhattan_distance((wx, wy), p) for p in adj_cells))
                # Compute scores
                distance_score = 1 / (1 + min_dist)
                value_score = order.value / max_order_value
                combined_score = distance_weight * distance_score + value_weight * value_score

                scored_pairs.append((combined_score, w_idx, o_idx))

        # --- Step 4: Greedy assignment ---
        scored_pairs.sort(reverse=True)  # highest score first
        assigned_workers = set()
        assigned_orders = set()

        for score, w_idx, o_idx in scored_pairs:
            if w_idx in assigned_workers or o_idx in assigned_orders:
                continue
            assignments[o_idx] = w_idx + 1  # +1 because 0 = no assignment
            assigned_workers.add(w_idx)
            assigned_orders.add(o_idx)
            if len(assigned_workers) >= len(idle_workers):
                break  # all idle workers assigned

        return assignments
        
    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this
        
        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)
        
        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01
    
    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this
        
        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency
    
    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}
        
        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }
    
    def track_layout_performance(self):
        """
        Performance analysis for greedy layout optimization algorithms.
        
        Measures: 
        - Layout efficiency (frequency-weighted distances)
        - Algorithm convergence (swaps per period)
        - Optimization impact over time
        """
        if not hasattr(self, 'layout_metrics'):
            self.layout_metrics = []
        
        # Calculate current layout efficiency using weighted distance metric
        efficiency = self._calculate_layout_efficiency()
        
        self.layout_metrics.append({
            'timestep': self.env.current_timestep,
            'efficiency': efficiency,
            'total_swaps': len([a for a in self.action_history if a['layout_swap'] != [0, 0]]),
            'phase1_swaps': self._count_frequency_swaps(),
            'phase2_swaps': self._count_cooccurrence_swaps()
        })
        
        # Print progress every 1000 steps
        if self.env.current_timestep % 1000 == 0:
            recent_efficiency = np.mean([m['efficiency'] for m in self.layout_metrics[-10:]])
            print(f"Layout efficiency: {recent_efficiency:.3f}")


    def _calculate_order_distance(self, worker_pos, order):
        """
        Calculate minimum Manhattan distance from worker to any item needed for this order.
        Worker cannot stand on storage cells; compute distance to walkable adjacent cells.
        """
        grid = self.env.warehouse_grid
        wx, wy = worker_pos
        min_distance = float('inf')

        for item_id in order.items:
            # Get all storage locations for this item type
            locations = grid.find_item_locations(int(item_id))
            for ix, iy in locations:
                # Consider only walkable adjacent cells
                adj_cells = [
                    (ix + dx, iy + dy)
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    if grid.is_walkable(ix + dx, iy + dy)
                ]
                if adj_cells:
                    # Compute Manhattan distance to each adjacent cell
                    min_distance = min(min_distance, min(grid.manhattan_distance((wx, wy), p) for p in adj_cells))

        return min_distance if min_distance != float('inf') else 0


    def _get_idle_workers(self, employee_info):
        """
        Identify workers available for order assignment.
        Returns list of (worker_index, (x, y)) for idle workers that are not managers.
        """
        idle_workers = []
        for i, emp in enumerate(employee_info):
            active = emp[0] > 0          # Employee exists
            idle = emp[1] == 0           # Currently idle
            not_manager = emp[5] == 0    # Not a manager
            if active and idle and not_manager:
                x, y = int(emp[0]), int(emp[1])
                idle_workers.append((i, (x, y)))
        return idle_workers

    def _calculate_layout_efficiency(self):
        """
        Objective function evaluation for layout quality.
        
        Algorithm: Weighted average distance where weights = access frequency
        Lower weighted distance = higher efficiency (better layout)
        """
        grid = self.env.warehouse_grid
        item_frequency = grid.item_access_frequency
        delivery_positions = getattr(
            grid,
            "truck_bay_positions",
            [(grid.width // 2, grid.height // 2)]
        )

        if item_frequency is None or len(item_frequency) == 0:
            return 1.0

        weighted_distance_sum = 0.0
        total_frequency = 0.0

        for item_type, frequency in enumerate(item_frequency):
            if frequency <= 0:
                continue

            locations = grid.find_item_locations(int(item_type))
            if not locations:
                continue

            nearest_distance = min(
                grid.manhattan_distance(loc, delivery_pos)
                for loc in locations
                for delivery_pos in delivery_positions
            )
            weighted_distance_sum += frequency * nearest_distance
            total_frequency += frequency

        if total_frequency == 0:
            return 1.0

        weighted_avg_distance = weighted_distance_sum / total_frequency
        max_possible_distance = max(1, grid.width + grid.height - 2)
        efficiency = 1.0 - (weighted_avg_distance / max_possible_distance)

        return float(np.clip(efficiency, 0.0, 1.0))

    def track_integrated_performance(self):
        # Only calculate metrics, do not change self.env or actions
        current_profit = self.env.cumulative_profit
        num_employees = len(self.env.employees)
        queue_length = len(self.env.order_queue.orders)
        
        self.integrated_metrics.append({
            'timestep': self.env.current_timestep,
            'profit_per_employee': current_profit / max(1, num_employees),
            'queue_pressure': queue_length / max(1, num_employees)
        })
            
    def _count_frequency_swaps(self) -> int:
        """Return number of phase-1 (frequency) swaps executed."""
        return int(getattr(self, "phase1_swap_count", 0))

    def _count_cooccurrence_swaps(self) -> int:
        """Return number of phase-2 (co-occurrence) swaps executed."""
        return int(getattr(self, "phase2_swap_count", 0))


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent
    
    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """
    
    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"
        self.integrated_metrics = [] 


        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None

            
    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass
    
    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass
    
    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass
    
    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass
