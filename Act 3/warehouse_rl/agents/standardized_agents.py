#!/usr/bin/env python3
"""
Standardized agents with parameterized strategies for hiring, queue management, and layout optimization.
This provides a clean foundation for RL to learn optimal parameter combinations.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from abc import ABC, abstractmethod

class BaselineAgent(ABC):
    """Base class for baseline heuristic agents"""
    
    def __init__(self, env):
        self.env = env
        self.name = "BaselineAgent"
    
    @abstractmethod
    def get_action(self, observation: Dict) -> Dict:
        """Generate action based on current observation"""
        pass
    
    def reset(self):
        """Reset agent state if needed"""
        pass

class StandardizedAgentParams:
    """Standardized parameters for warehouse agents"""
    
    def __init__(self,
                 # Hiring Strategy Parameters
                 hiring_strategy: str = "greedy",  # "greedy", "fixed", "profit_based", "sustained_profit"
                 hire_threshold_ratio: float = 3.0,  # queue/employees ratio to trigger hiring
                 fire_threshold_ratio: float = 2.0,  # queue/employees ratio to trigger firing
                 profit_threshold_for_hiring: float = 0.0,  # minimum profit required to hire
                 max_employees_strategy: int = 100,  # max employees for this strategy
                 manager_hiring_enabled: bool = False,  # whether to hire managers
                 manager_hire_timing: str = "immediate",  # "immediate", "profit_based", "never"
                 
                 # Queue Management Parameters
                 queue_strategy: str = "fifo",  # "fifo", "value_based", "distance_based", "smart"
                 order_value_weight: float = 0.0,  # weight for order value in assignment (0-1)
                 distance_weight: float = 0.0,  # weight for distance in assignment (0-1)
                 batch_assignment_size: int = 1,  # how many orders to assign at once
                 
                 # Layout Optimization Parameters
                 layout_strategy: str = "none",  # "none", "moderate", "aggressive"
                 layout_optimization_interval: int = 50,  # timesteps between layout checks (reduced from 500)
                 ev_threshold_for_swaps: float = 10.0,  # minimum EV improvement for swaps (reduced from 50.0)
                 layout_queue_condition_ratio: float = 20.0,  # only optimize when queue < employees * ratio (much more permissive)
                 
                 # Economic Parameters
                 profit_tracking_window: int = 100,  # timesteps to track for profit trends
                 decision_interval: int = 50):  # how often to make major decisions
        
        # Hiring Strategy
        self.hiring_strategy = hiring_strategy
        self.hire_threshold_ratio = hire_threshold_ratio
        self.fire_threshold_ratio = fire_threshold_ratio
        self.profit_threshold_for_hiring = profit_threshold_for_hiring
        self.max_employees_strategy = max_employees_strategy
        self.manager_hiring_enabled = manager_hiring_enabled
        self.manager_hire_timing = manager_hire_timing
        
        # Queue Management
        self.queue_strategy = queue_strategy
        self.order_value_weight = order_value_weight
        self.distance_weight = distance_weight
        self.batch_assignment_size = batch_assignment_size
        
        # Layout Optimization
        self.layout_strategy = layout_strategy
        self.layout_optimization_interval = layout_optimization_interval
        self.ev_threshold_for_swaps = ev_threshold_for_swaps
        self.layout_queue_condition_ratio = layout_queue_condition_ratio
        
        # Economic
        self.profit_tracking_window = profit_tracking_window
        self.decision_interval = decision_interval

class StandardizedAgent(BaselineAgent):
    """Base agent with standardized parameter system"""
    
    def __init__(self, env, params: StandardizedAgentParams, name: str = "StandardizedAgent"):
        super().__init__(env)
        self.name = name
        self.params = params
        
        # Internal state tracking
        self.profit_history = []
        self.last_major_decision = 0
        self.last_layout_optimization = 0
        self.has_manager = False
        
        # Simplified swap tracking system
        self.recent_swaps = {}  # {(pos1, pos2): timestep} - track when swaps happened
        self.swap_cooldown_period = 50  # Short cooldown for responsive optimization
        
        # Simple tracking for hot item optimization
        self.moved_hot_items = set()  # Track items we've already moved closer to delivery
        self.last_hot_item_optimization = 0  # Last time we did hot item optimization
        self.last_cooccurrence_optimization = 0  # Last time we did co-occurrence optimization
        self.hot_item_frequency_window = 125  # Steps to analyze for hot items
        self.cooccurrence_optimization_interval = 300  # Steps between co-occurrence optimization
        
        # Enable unlimited hiring for specific strategies
        if params.hiring_strategy in ["greedy"]:
            self.env._unlimited_hiring = True
    
    def reset(self):
        """Reset agent state between episodes"""
        self.profit_history = []
        self.last_major_decision = 0
        self.last_layout_optimization = 0
        self.has_manager = False
        self.recent_swaps = {}  # Clear swap history
        
        # Reset simplified tracking data
        self.moved_hot_items = set()
        self.last_hot_item_optimization = 0
        self.last_cooccurrence_optimization = 0
    
    def get_action(self, observation: Dict) -> Dict:
        action = {
            'staffing_action': 0,
            'layout_swap': [0, 0],
            'order_assignments': [0] * 20
        }
        
        current_time = self.env.current_timestep
        
        # Make major decisions at intervals
        if current_time - self.last_major_decision >= self.params.decision_interval:
            action['staffing_action'] = self._get_staffing_action()
            self.last_major_decision = current_time
        
        # Handle simplified layout optimization
        if current_time - self.last_layout_optimization >= self.params.layout_optimization_interval:
            layout_action = self._get_simple_layout_action(current_time)
            if layout_action:
                action['layout_swap'] = layout_action
                self.last_layout_optimization = current_time
                # Record the swap with simple tracking
                self._record_swap_execution(layout_action[0], layout_action[1], current_time)
        
        # Handle order assignments
        action['order_assignments'] = self._get_order_assignments()
        
        return action
    
    def _get_staffing_action(self) -> int:
        """Determine staffing action based on hiring strategy"""
        queue_length = len(self.env.order_queue.orders)
        num_employees = len(self.env.employees)
        num_workers = sum(1 for emp in self.env.employees if not emp.is_manager)
        current_profit = self.env.cumulative_profit
        
        # Update manager status
        self.has_manager = any(emp.is_manager for emp in self.env.employees)
        
        if self.params.hiring_strategy == "greedy":
            # Hire as fast as possible
            if queue_length > num_employees * self.params.hire_threshold_ratio:
                return 1  # Hire worker
            elif queue_length < num_employees * self.params.fire_threshold_ratio and num_employees > 1:
                return 2  # Fire
        
        elif self.params.hiring_strategy == "fixed":
            # Fixed strategy: hire to target immediately, then maintain
            target_workers = 5
            if not self.has_manager and self.params.manager_hiring_enabled:
                return 3  # Hire manager first
            elif num_workers < target_workers:
                return 1  # Hire worker to reach target
            elif num_workers > target_workers:
                return 2  # Fire excess workers
        
        elif self.params.hiring_strategy == "profit_based":
            # Only hire if profitable and need capacity
            if (current_profit > self.params.profit_threshold_for_hiring and 
                queue_length > num_employees * self.params.hire_threshold_ratio and
                num_employees < self.params.max_employees_strategy):
                
                # Hire manager first if enabled
                if (not self.has_manager and self.params.manager_hiring_enabled and 
                    self.params.manager_hire_timing == "profit_based" and
                    current_profit > 5000):
                    return 3
                else:
                    return 1  # Hire worker
            elif current_profit < 0 and num_employees > 3:
                return 2  # Fire if unprofitable
        
        elif self.params.hiring_strategy == "sustained_profit":
            # Track profit trends for sustained profitability
            self.profit_history.append(current_profit)
            if len(self.profit_history) > self.params.profit_tracking_window:
                self.profit_history.pop(0)
            
            if len(self.profit_history) >= 3:
                recent_trend = np.mean(self.profit_history[-3:]) - np.mean(self.profit_history[-6:-3])
                
                if (recent_trend > 0 and queue_length > num_employees * self.params.hire_threshold_ratio and
                    num_employees < self.params.max_employees_strategy):
                    return 1  # Hire if profit trending up
                elif recent_trend < -100 and num_employees > 5:
                    return 2  # Fire if profit declining significantly
        
        return 0  # No action
    
    def _get_layout_action(self) -> Optional[List[int]]:
        """Determine layout optimization based on strategy"""
        if self.params.layout_strategy == "none":
            return None
        
        queue_length = len(self.env.order_queue.orders)
        num_employees = len(self.env.employees)
        
        # Only optimize when queue is manageable
        if queue_length > num_employees * self.params.layout_queue_condition_ratio:
            return None
        
        # Need a manager for layout optimization
        manager = next((emp for emp in self.env.employees if emp.is_manager), None)
        if not manager:
            return None
        
        try:
            from ..environment.employee import EmployeeState
        except ImportError:
            from environment.employee import EmployeeState
            
        if manager.state != EmployeeState.IDLE:
            return None
        
        # Find beneficial swap using EV calculation
        proposed_swap = self._find_beneficial_swap()
        
        # Check anti-thrashing cooldown before returning
        if proposed_swap:
            current_time = self.env.current_timestep
            pos1_idx, pos2_idx = proposed_swap
            swap_key = tuple(sorted([pos1_idx, pos2_idx]))
            
            if swap_key in self.recent_swaps:
                last_swap_time = self.recent_swaps[swap_key]
                if current_time - last_swap_time < self.swap_cooldown_period:
                    # Still on cooldown, reject this swap
                    pass  # Swap blocked due to cooldown
                    return None
        
        return proposed_swap
    
    def _find_beneficial_swap(self) -> Optional[List[int]]:
        """Find beneficial layout swap based on EV threshold"""
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence
        packing_station = grid.packing_station
        
        best_swap = None
        best_benefit = 0
        
        # Simple co-occurrence based optimization
        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                if cooccurrence[item1, item2] > 2:  # Frequently ordered together (reduced threshold)
                    
                    item1_locs = grid.find_item_locations(item1)
                    item2_locs = grid.find_item_locations(item2)
                    
                    if item1_locs and item2_locs:
                        current_distance = grid.manhattan_distance(item1_locs[0], item2_locs[0])
                        
                        # Find potential swap partners
                        for other_item in range(grid.num_item_types):
                            if other_item != item1 and other_item != item2:
                                other_locs = grid.find_item_locations(other_item)
                                if other_locs:
                                    new_distance = grid.manhattan_distance(other_locs[0], item2_locs[0])
                                    benefit = (current_distance - new_distance) * cooccurrence[item1, item2]
                                    
                                    if benefit > best_benefit and benefit > self.params.ev_threshold_for_swaps:
                                        best_benefit = benefit
                                        pos1_idx = item1_locs[0][1] * grid.width + item1_locs[0][0]
                                        pos2_idx = other_locs[0][1] * grid.width + other_locs[0][0]
                                        best_swap = [pos1_idx, pos2_idx]
        
        # Fallback: Frequency-based optimization when no co-occurrence data
        if not best_swap:
            # Get item access frequencies
            item_frequencies = {}
            if hasattr(grid, 'item_access_frequency'):
                # Convert numpy array to dict for easier processing
                freq_array = grid.item_access_frequency
                item_frequencies = {i: freq_array[i] for i in range(len(freq_array)) if freq_array[i] > 0}
            
            # If we have frequency data, optimize based on that
            if item_frequencies and max(item_frequencies.values()) > 0:
                # Find packing stations for distance calculation
                packing_positions = getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])
                
                # Find high frequency items that are far from packing stations
                high_freq_items = []
                for item_type, freq in item_frequencies.items():
                    if freq > 2:  # High frequency threshold
                        item_locs = grid.find_item_locations(item_type)
                        if item_locs:
                            # Calculate average distance to packing stations
                            avg_dist = sum(min(grid.manhattan_distance(pos, pack_pos) 
                                             for pack_pos in packing_positions) 
                                         for pos in item_locs) / len(item_locs)
                            high_freq_items.append((item_type, freq, avg_dist, item_locs[0]))
                
                # Sort by frequency (descending) then distance (descending) 
                high_freq_items.sort(key=lambda x: (-x[1], -x[2]))
                
                # Find low frequency items closer to packing stations to swap with
                for high_item_type, high_freq, high_dist, high_pos in high_freq_items:
                    for low_item_type, low_freq in item_frequencies.items():
                        if low_freq < high_freq * 0.5:  # Much lower frequency
                            low_locs = grid.find_item_locations(low_item_type)
                            if low_locs:
                                for low_pos in low_locs:
                                    low_dist = min(grid.manhattan_distance(low_pos, pack_pos) 
                                                 for pack_pos in packing_positions)
                                    
                                    # Benefit = bringing high freq item closer to packing
                                    benefit = (high_dist - low_dist) * (high_freq - low_freq)
                                    
                                    if benefit > best_benefit and benefit > self.params.ev_threshold_for_swaps:
                                        best_benefit = benefit
                                        pos1_idx = high_pos[1] * grid.width + high_pos[0]
                                        pos2_idx = low_pos[1] * grid.width + low_pos[0]
                                        best_swap = [pos1_idx, pos2_idx]
                                        break
                            if best_swap:
                                break
                    if best_swap:
                        break
        
        return best_swap
    
    def _cleanup_old_swaps(self, current_time: int):
        """Remove swap records that are beyond the cooldown period"""
        cutoff_time = current_time - self.swap_cooldown_period
        keys_to_remove = [key for key, timestamp in self.recent_swaps.items() if timestamp < cutoff_time]
        for key in keys_to_remove:
            del self.recent_swaps[key]
    
    def record_swap_execution(self, pos1_idx: int, pos2_idx: int):
        """Record that a swap was executed to start its cooldown period"""
        current_time = self.env.current_timestep
        swap_key = tuple(sorted([pos1_idx, pos2_idx]))
        self.recent_swaps[swap_key] = current_time
        pass  # Swap recorded
    
    def _smart_assignment(self, idle_workers: List[int], orders: List) -> List[int]:
        """Smart assignment using value and distance weights"""
        assignments = [0] * 20
        if not idle_workers or not orders:
            return assignments
        
        # Calculate priority scores for each worker-order pair
        worker_order_scores = []
        
        for worker_idx in idle_workers:
            worker = self.env.employees[worker_idx]
            worker_pos = worker.position
            
            for order_idx, order in enumerate(orders):
                # Find closest item needed for this order
                min_distance = float('inf')
                for item_type in order.items:
                    item_locations = self.env.warehouse_grid.find_item_locations(item_type)
                    for item_pos in item_locations:
                        distance = self.env.warehouse_grid.manhattan_distance(worker_pos, item_pos)
                        min_distance = min(min_distance, distance)
                
                if min_distance == float('inf'):
                    continue  # Skip if no items found
                
                # Calculate priority score (higher is better)
                # Normalize distance (closer = higher score)
                max_distance = self.env.warehouse_grid.width + self.env.warehouse_grid.height
                distance_score = (max_distance - min_distance) / max_distance
                
                # Normalize value
                max_value = max(o.value for o in orders) if orders else 1
                value_score = order.value / max_value
                
                # Weighted combination
                priority = (self.params.distance_weight * distance_score + 
                           self.params.order_value_weight * value_score)
                
                worker_order_scores.append((priority, worker_idx, order_idx))
        
        # Sort by priority (highest first) and assign greedily
        worker_order_scores.sort(reverse=True)
        assigned_workers = set()
        assigned_orders = set()
        
        for priority, worker_idx, order_idx in worker_order_scores:
            if worker_idx not in assigned_workers and order_idx not in assigned_orders:
                assignments[order_idx] = worker_idx + 1  # +1 for action encoding
                assigned_workers.add(worker_idx)
                assigned_orders.add(order_idx)
        
        return assignments
    
    def _distance_based_assignment(self, idle_workers: List[int], orders: List) -> List[int]:
        """Pure distance-based assignment (closest items first)"""
        assignments = [0] * 20
        if not idle_workers or not orders:
            return assignments
        
        # Calculate distances for each worker-order pair
        worker_order_distances = []
        
        for worker_idx in idle_workers:
            worker = self.env.employees[worker_idx]
            worker_pos = worker.position
            
            for order_idx, order in enumerate(orders):
                # Find closest item needed for this order
                min_distance = float('inf')
                for item_type in order.items:
                    item_locations = self.env.warehouse_grid.find_item_locations(item_type)
                    for item_pos in item_locations:
                        distance = self.env.warehouse_grid.manhattan_distance(worker_pos, item_pos)
                        min_distance = min(min_distance, distance)
                
                if min_distance != float('inf'):
                    worker_order_distances.append((min_distance, worker_idx, order_idx))
        
        # Sort by distance (closest first) and assign greedily
        worker_order_distances.sort()
        assigned_workers = set()
        assigned_orders = set()
        
        for distance, worker_idx, order_idx in worker_order_distances:
            if worker_idx not in assigned_workers and order_idx not in assigned_orders:
                assignments[order_idx] = worker_idx + 1  # +1 for action encoding
                assigned_workers.add(worker_idx)
                assigned_orders.add(order_idx)
        
        return assignments
    
    def _get_order_assignments(self) -> List[int]:
        """Assign orders based on queue management strategy"""
        try:
            from ..environment.employee import EmployeeState
        except ImportError:
            from environment.employee import EmployeeState
        
        # Find idle workers (not managers)
        idle_workers = []
        for i, employee in enumerate(self.env.employees):
            if employee.state == EmployeeState.IDLE and not employee.is_manager:
                idle_workers.append(i)
        
        orders = self.env.order_queue.orders[:20]  # Limit to action space size
        assignments = [0] * 20
        
        if not idle_workers or not orders:
            return assignments
        
        if self.params.queue_strategy == "fifo":
            # Simple FIFO assignment
            assignment_count = min(len(idle_workers), len(orders))
            for i in range(assignment_count):
                assignments[i] = idle_workers[i % len(idle_workers)] + 1
        
        elif self.params.queue_strategy == "value_based":
            # Prioritize high-value orders
            order_priorities = [(order.value, i) for i, order in enumerate(orders)]
            order_priorities.sort(reverse=True)  # Highest value first
            
            assignment_count = min(len(idle_workers), len(order_priorities))
            for i in range(assignment_count):
                order_idx = order_priorities[i][1]
                worker_idx = idle_workers[i % len(idle_workers)]
                assignments[order_idx] = worker_idx + 1
        
        elif self.params.queue_strategy == "smart":
            # Smart assignment: workers get orders with items closest to their current position
            # Use a combination of value and distance weights
            assignments = self._smart_assignment(idle_workers, orders)
        
        elif self.params.queue_strategy == "distance_based":
            # Pure distance-based assignment (closest items first)
            assignments = self._distance_based_assignment(idle_workers, orders)
        
        return assignments
    
    def _get_simple_layout_action(self, current_time: int) -> Optional[List[int]]:
        """Simple layout optimization: move hot items close to delivery, group co-occurring items"""
        if self.params.layout_strategy == "none":
            return None
        
        queue_length = len(self.env.order_queue.orders)
        num_employees = len(self.env.employees)
        
        # Only optimize when queue is manageable
        if queue_length > num_employees * self.params.layout_queue_condition_ratio:
            return None
        
        # Need a manager for layout optimization
        manager = next((emp for emp in self.env.employees if emp.is_manager), None)
        if not manager:
            return None
        
        try:
            from ..environment.employee import EmployeeState
        except ImportError:
            from environment.employee import EmployeeState
            
        if manager.state != EmployeeState.IDLE:
            return None
        
        # Check cooldown
        proposed_swap = None
        
        # Two-phase optimization approach
        # Phase 1: Move hot items closer to delivery (every optimization interval)
        if current_time - self.last_hot_item_optimization >= self.hot_item_frequency_window:
            proposed_swap = self._find_hot_item_swap(current_time)
            if proposed_swap:
                self.last_hot_item_optimization = current_time
        
        # Phase 2: Group co-occurring items together (every 300 steps)
        if not proposed_swap and current_time - self.last_cooccurrence_optimization >= self.cooccurrence_optimization_interval:
            proposed_swap = self._find_cooccurrence_swap(current_time)
            if proposed_swap:
                self.last_cooccurrence_optimization = current_time
        
        # Check cooldown before returning
        if proposed_swap:
            pos1_idx, pos2_idx = proposed_swap
            swap_key = tuple(sorted([pos1_idx, pos2_idx]))
            
            if swap_key in self.recent_swaps:
                last_swap_time = self.recent_swaps[swap_key]
                if current_time - last_swap_time < self.swap_cooldown_period:
                    return None
        
        return proposed_swap
    
    def _find_hot_item_swap(self, current_time: int) -> Optional[List[int]]:
        """Find hot items from last 125 steps that need to move closer to delivery"""
        grid = self.env.warehouse_grid
        
        if not hasattr(grid, 'item_access_frequency'):
            return None
        
        # Get item frequencies from the last window
        freq_array = grid.item_access_frequency
        if freq_array.max() == 0:
            return None
        
        # Find hot items that we haven't moved yet
        hot_items = []
        for item_type in range(len(freq_array)):
            if freq_array[item_type] > 0 and item_type not in self.moved_hot_items:
                item_locs = grid.find_item_locations(item_type)
                if item_locs:
                    hot_items.append((item_type, freq_array[item_type], item_locs[0]))
        
        if not hot_items:
            return None
        
        # Sort by frequency (highest first)
        hot_items.sort(key=lambda x: x[1], reverse=True)
        
        # Get delivery positions (truck bays)
        delivery_positions = getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])
        
        # Find the hottest item that's far from delivery
        for item_type, _, item_pos in hot_items:
            # Calculate distance to nearest delivery spot
            min_delivery_dist = min(grid.manhattan_distance(item_pos, delivery_pos) 
                                  for delivery_pos in delivery_positions)
            
            # Only move if it's reasonably far (distance > 2)
            if min_delivery_dist <= 2:
                continue
            
            # Find a better position closer to delivery
            best_swap = self._find_closer_position(grid, item_pos, delivery_positions, item_type)
            if best_swap:
                # Mark this item as moved
                self.moved_hot_items.add(item_type)
                return best_swap
        
        return None
    
    def _find_closer_position(self, grid, current_pos, delivery_positions, item_type) -> Optional[List[int]]:
        """Find a position closer to delivery to swap with"""
        current_dist = min(grid.manhattan_distance(current_pos, delivery_pos) 
                          for delivery_pos in delivery_positions)
        
        current_idx = current_pos[1] * grid.width + current_pos[0]
        
        # Look for empty spots or spots with cold items closer to delivery
        best_swap = None
        best_improvement = 0
        
        # Check all storage positions
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.cell_types[y, x] != 1:  # CellType.STORAGE.value = 1
                    continue
                
                # Calculate distance to delivery
                candidate_dist = min(grid.manhattan_distance((x, y), delivery_pos) 
                                   for delivery_pos in delivery_positions)
                
                # Only consider positions that are closer
                improvement = current_dist - candidate_dist
                if improvement <= 1:  # Need at least 2 step improvement
                    continue
                
                # Check what's at this position
                existing_item = grid.get_item_at_position(x, y)
                
                if existing_item is None:
                    # Empty spot - perfect for swapping
                    if improvement > best_improvement:
                        best_improvement = improvement
                        candidate_idx = y * grid.width + x
                        best_swap = [current_idx, candidate_idx]
                
                elif hasattr(grid, 'item_access_frequency'):
                    # Occupied spot - only swap with cold items
                    freq_array = grid.item_access_frequency
                    if existing_item < len(freq_array) and freq_array[existing_item] == 0:
                        # Cold item - good candidate for swapping
                        if improvement > best_improvement:
                            best_improvement = improvement
                            candidate_idx = y * grid.width + x
                            best_swap = [current_idx, candidate_idx]
        
        return best_swap
    
    def _find_cooccurrence_swap(self, current_time: int) -> Optional[List[int]]:
        """Group items that co-occur frequently to be close together"""
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence
        
        if cooccurrence.max() == 0:
            return None
        
        best_swap = None
        best_benefit = 0
        
        # Find pairs with high co-occurrence that are far apart
        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                cooccur_count = cooccurrence[item1, item2]
                
                if cooccur_count > 2:  # Frequently ordered together
                    item1_locs = grid.find_item_locations(item1)
                    item2_locs = grid.find_item_locations(item2)
                    
                    if item1_locs and item2_locs:
                        current_distance = grid.manhattan_distance(item1_locs[0], item2_locs[0])
                        
                        # Only optimize if they're far apart (distance > 3)
                        if current_distance <= 3:
                            continue
                        
                        # Find a way to bring them closer
                        swap = self._find_grouping_swap(grid, item1_locs[0], item2_locs[0], item1, item2)
                        if swap:
                            benefit = cooccur_count * (current_distance - 2)  # Assume we can get them 2 apart
                            if benefit > best_benefit:
                                best_benefit = benefit
                                best_swap = swap
        
        return best_swap
    
    def _find_grouping_swap(self, grid, pos1, pos2, item1, item2) -> Optional[List[int]]:
        """Find a swap to bring two co-occurring items closer together"""
        # Try to move item1 closer to item2's area
        target_area = [(pos2[0] + dx, pos2[1] + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                      if 0 <= pos2[0] + dx < grid.width and 0 <= pos2[1] + dy < grid.height 
                      and grid.cell_types[pos2[1] + dy, pos2[0] + dx] == 1]  # CellType.STORAGE.value = 1
        
        pos1_idx = pos1[1] * grid.width + pos1[0]
        
        for target_pos in target_area:
            if target_pos == pos1 or target_pos == pos2:
                continue
            
            existing_item = grid.get_item_at_position(target_pos[0], target_pos[1])
            
            # Can swap with empty spot or cold item
            if existing_item is None:
                target_idx = target_pos[1] * grid.width + target_pos[0]
                return [pos1_idx, target_idx]
            
            elif hasattr(grid, 'item_access_frequency'):
                freq_array = grid.item_access_frequency
                if existing_item < len(freq_array) and freq_array[existing_item] == 0:
                    target_idx = target_pos[1] * grid.width + target_pos[0]
                    return [pos1_idx, target_idx]
        
        return None
    
    def _record_swap_execution(self, pos1_idx: int, pos2_idx: int, current_time: int):
        """Simple swap execution recording"""
        swap_key = tuple(sorted([pos1_idx, pos2_idx]))
        self.recent_swaps[swap_key] = current_time
    
    def _update_swap_performance_metrics(self, current_time: int):
        """Update performance metrics for previous swaps to guide future decisions"""
        for swap_key, swap_data in list(self.swap_performance_history.items()):
            if swap_data['evaluation_complete']:
                continue
                
            execution_time = swap_data['execution_time']
            time_since_swap = current_time - execution_time
            
            if time_since_swap >= self.swap_evaluation_window:
                # Calculate actual performance impact
                pre_swap_profit = swap_data['pre_profit']
                post_window_profit = self.env.cumulative_profit
                actual_profit_impact = post_window_profit - pre_swap_profit
                
                # Calculate expected vs actual performance
                expected_benefit = swap_data['predicted_benefit']
                actual_benefit = actual_profit_impact
                
                # Update swap performance record
                self.swap_performance_history[swap_key].update({
                    'actual_benefit': actual_benefit,
                    'success_ratio': actual_benefit / max(1, expected_benefit),
                    'evaluation_complete': True
                })
                
                pass  # Swap performance evaluated
    
    def _get_adaptive_cooldown(self, swap_key: tuple) -> int:
        """Calculate adaptive cooldown period based on swap success history"""
        if not self.adaptive_cooldown_enabled:
            return self.swap_cooldown_period
        
        # Calculate success rate for this specific swap pair
        if swap_key in self.swap_performance_history:
            swap_data = self.swap_performance_history[swap_key]
            if swap_data['evaluation_complete']:
                success_ratio = swap_data['success_ratio']
                
                if success_ratio > 1.5:  # Very successful swap
                    return self.min_cooldown
                elif success_ratio > 0.8:  # Moderately successful
                    return int(self.min_cooldown * 1.5)
                elif success_ratio > 0.3:  # Somewhat successful
                    return self.swap_cooldown_period
                else:  # Poor performance
                    return self.max_cooldown
        
        # Calculate general success rate across all swaps
        completed_swaps = [data for data in self.swap_performance_history.values() if data['evaluation_complete']]
        if len(completed_swaps) >= 3:
            avg_success_ratio = sum(data['success_ratio'] for data in completed_swaps) / len(completed_swaps)
            
            if avg_success_ratio > 1.2:  # Generally successful strategy
                return max(self.min_cooldown, int(self.swap_cooldown_period * 0.7))
            elif avg_success_ratio < 0.5:  # Generally unsuccessful
                return min(self.max_cooldown, int(self.swap_cooldown_period * 1.5))
        
        return self.swap_cooldown_period
    
    def _find_beneficial_swap_enhanced(self, current_time: int) -> Optional[List[int]]:
        """Enhanced swap finding with predictive modeling and market condition analysis"""
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence
        
        best_swap = None
        best_predicted_benefit = 0
        
        # Get current market conditions for context
        current_market = self.market_condition_history[-1] if self.market_condition_history else {}
        recent_profit_rate = self._calculate_recent_profit_rate()
        
        # Enhanced co-occurrence analysis with market context
        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                cooccur_count = cooccurrence[item1, item2]
                
                # Dynamic threshold based on market conditions
                base_threshold = 2
                if current_market.get('order_pressure', 1) > 2.0:  # High pressure
                    threshold = base_threshold * 0.5  # Lower threshold for faster optimization
                elif recent_profit_rate > 0:  # Profitable conditions
                    threshold = base_threshold * 0.7
                else:
                    threshold = base_threshold
                
                if cooccur_count > threshold:
                    item1_locs = grid.find_item_locations(item1)
                    item2_locs = grid.find_item_locations(item2)
                    
                    if item1_locs and item2_locs:
                        current_distance = grid.manhattan_distance(item1_locs[0], item2_locs[0])
                        
                        # Find potential swap partners with enhanced evaluation
                        for other_item in range(grid.num_item_types):
                            if other_item != item1 and other_item != item2:
                                other_locs = grid.find_item_locations(other_item)
                                if other_locs:
                                    new_distance = grid.manhattan_distance(other_locs[0], item2_locs[0])
                                    
                                    # Enhanced benefit calculation
                                    distance_benefit = (current_distance - new_distance) * cooccur_count
                                    
                                    # Add market condition multipliers
                                    market_multiplier = 1.0
                                    if current_market.get('order_pressure', 1) > 1.5:
                                        market_multiplier = 1.3  # Higher value during busy periods
                                    if recent_profit_rate > 0:
                                        market_multiplier *= 1.2  # Bonus for profitable trends
                                    
                                    predicted_benefit = distance_benefit * market_multiplier
                                    
                                    # Lower threshold during profitable periods
                                    effective_threshold = self.params.ev_threshold_for_swaps
                                    if recent_profit_rate > 5:  # Strong profit trend
                                        effective_threshold *= 0.5
                                    elif recent_profit_rate < -2:  # Declining profits
                                        effective_threshold *= 2.0
                                    
                                    if predicted_benefit > best_predicted_benefit and predicted_benefit > effective_threshold:
                                        best_predicted_benefit = predicted_benefit
                                        pos1_idx = item1_locs[0][1] * grid.width + item1_locs[0][0]
                                        pos2_idx = other_locs[0][1] * grid.width + other_locs[0][0]
                                        best_swap = [pos1_idx, pos2_idx]
        
        # Enhanced frequency-based optimization fallback
        if not best_swap:
            best_swap = self._find_frequency_based_swap_enhanced(grid, current_market, recent_profit_rate)
        
        # Record swap candidate for analysis (whether executed or not)
        if best_swap:
            swap_key = tuple(sorted(best_swap))
            self.swap_candidates_history.append({
                'timestep': current_time,
                'swap_key': swap_key,
                'predicted_benefit': best_predicted_benefit,
                'market_conditions': current_market.copy(),
                'profit_rate': recent_profit_rate,
                'executed': True  # Will be updated if swap is actually executed
            })
        
        return best_swap
    
    def _find_frequency_based_swap_enhanced(self, grid, current_market: dict, recent_profit_rate: float) -> Optional[List[int]]:
        """Enhanced frequency-based optimization with market awareness"""
        item_frequencies = {}
        if hasattr(grid, 'item_access_frequency'):
            freq_array = grid.item_access_frequency
            item_frequencies = {i: freq_array[i] for i in range(len(freq_array)) if freq_array[i] > 0}
        
        if not item_frequencies or max(item_frequencies.values()) == 0:
            return None
        
        # Adaptive frequency threshold based on market conditions
        base_freq_threshold = 2
        if current_market.get('order_pressure', 1) > 2.0:
            freq_threshold = base_freq_threshold * 0.5  # More aggressive during high demand
        else:
            freq_threshold = base_freq_threshold
        
        packing_positions = getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])
        
        high_freq_items = []
        for item_type, freq in item_frequencies.items():
            if freq > freq_threshold:
                item_locs = grid.find_item_locations(item_type)
                if item_locs:
                    avg_dist = sum(min(grid.manhattan_distance(pos, pack_pos) 
                                     for pack_pos in packing_positions) 
                                 for pos in item_locs) / len(item_locs)
                    high_freq_items.append((item_type, freq, avg_dist, item_locs[0]))
        
        if not high_freq_items:
            return None
        
        high_freq_items.sort(key=lambda x: (-x[1], -x[2]))  # Sort by frequency then distance
        
        best_swap = None
        best_benefit = 0
        
        for _, high_freq, high_dist, high_pos in high_freq_items:
            for low_item_type, low_freq in item_frequencies.items():
                if low_freq < high_freq * 0.5:  # Much lower frequency
                    low_locs = grid.find_item_locations(low_item_type)
                    if low_locs:
                        for low_pos in low_locs:
                            low_dist = min(grid.manhattan_distance(low_pos, pack_pos) 
                                         for pack_pos in packing_positions)
                            
                            # Enhanced benefit calculation with market factors
                            base_benefit = (high_dist - low_dist) * (high_freq - low_freq)
                            
                            # Market condition multipliers
                            market_multiplier = 1.0
                            if current_market.get('item_diversity', 0) > 8:  # High diversity
                                market_multiplier = 1.2
                            if recent_profit_rate > 0:
                                market_multiplier *= 1.1
                            
                            benefit = base_benefit * market_multiplier
                            
                            # Dynamic threshold based on profit trends
                            threshold = self.params.ev_threshold_for_swaps
                            if recent_profit_rate > 3:
                                threshold *= 0.6  # More aggressive when profitable
                            elif recent_profit_rate < -1:
                                threshold *= 1.5  # More conservative when losing money
                            
                            if benefit > best_benefit and benefit > threshold:
                                best_benefit = benefit
                                pos1_idx = high_pos[1] * grid.width + high_pos[0]
                                pos2_idx = low_pos[1] * grid.width + low_pos[0]
                                best_swap = [pos1_idx, pos2_idx]
                                break
                    if best_swap:
                        break
            if best_swap:
                break
        
        return best_swap
    
    def record_swap_execution_enhanced(self, pos1_idx: int, pos2_idx: int, current_time: int):
        """Enhanced swap execution recording with performance tracking setup"""
        # Record for cooldown tracking (existing functionality)
        swap_key = tuple(sorted([pos1_idx, pos2_idx]))
        self.recent_swaps[swap_key] = current_time
        
        # Set up performance tracking for this swap
        pre_swap_profit = self.env.cumulative_profit
        
        # Calculate predicted benefit (re-run the evaluation)
        grid = self.env.warehouse_grid
        pos1_x, pos1_y = pos1_idx % grid.width, pos1_idx // grid.width
        pos2_x, pos2_y = pos2_idx % grid.width, pos2_idx // grid.width
        
        # Estimate benefit based on current co-occurrence and frequency data
        item1 = grid.get_item_at_position(pos1_x, pos1_y)
        item2 = grid.get_item_at_position(pos2_x, pos2_y)
        
        predicted_benefit = 0
        if item1 is not None and item2 is not None:
            # Use co-occurrence data to estimate benefit
            cooccur_matrix = grid.item_cooccurrence
            for other_item in range(grid.num_item_types):
                if other_item != item1 and other_item != item2:
                    benefit_estimate = max(
                        cooccur_matrix[item1, other_item] * 2,  # Rough estimate
                        cooccur_matrix[item2, other_item] * 2
                    )
                    predicted_benefit = max(predicted_benefit, benefit_estimate)
        
        # Record swap performance tracking
        self.swap_performance_history[swap_key] = {
            'execution_time': current_time,
            'pre_profit': pre_swap_profit,
            'predicted_benefit': predicted_benefit,
            'pos1': (pos1_x, pos1_y),
            'pos2': (pos2_x, pos2_y),
            'item1': item1,
            'item2': item2,
            'evaluation_complete': False
        }
        
        pass  # Enhanced tracking setup

# Predefined agent configurations
def create_greedy_agent(env) -> StandardizedAgent:
    """Greedy: Hire as fast as possible, FIFO, no layout optimization"""
    params = StandardizedAgentParams(
        hiring_strategy="greedy",
        hire_threshold_ratio=3.0,
        fire_threshold_ratio=2.0,
        queue_strategy="fifo",
        layout_strategy="none",
        manager_hiring_enabled=False
    )
    return StandardizedAgent(env, params, "Greedy")

def create_random_agent(env) -> StandardizedAgent:
    """Random: All parameters randomized"""
    params = StandardizedAgentParams(
        hiring_strategy=np.random.choice(["greedy", "profit_based", "sustained_profit"]),
        hire_threshold_ratio=np.random.uniform(2.0, 5.0),
        fire_threshold_ratio=np.random.uniform(1.5, 3.0),
        profit_threshold_for_hiring=np.random.uniform(0, 2000),
        queue_strategy=np.random.choice(["fifo", "value_based", "smart"]),
        layout_strategy=np.random.choice(["none", "moderate"]),
        ev_threshold_for_swaps=np.random.uniform(25, 150),
        manager_hiring_enabled=np.random.choice([True, False])
    )
    return StandardizedAgent(env, params, "Random")

def create_fixed_hiring_agent(env) -> StandardizedAgent:
    """Fixed: 5 workers + manager immediately, moderate layout optimization"""
    params = StandardizedAgentParams(
        hiring_strategy="fixed",
        queue_strategy="fifo",
        layout_strategy="moderate",
        layout_optimization_interval=25,  # Much more frequent checks
        ev_threshold_for_swaps=5.0,  # Lower threshold for easier swaps
        layout_queue_condition_ratio=20.0,  # Much more permissive queue condition
        manager_hiring_enabled=True,
        manager_hire_timing="immediate"
    )
    return StandardizedAgent(env, params, "FixedHiring")

def create_intelligent_hiring_agent(env) -> StandardizedAgent:
    """Intelligent Hiring: Profit-based hiring, FIFO, moderate layout optimization"""
    params = StandardizedAgentParams(
        hiring_strategy="profit_based",
        hire_threshold_ratio=3.5,
        fire_threshold_ratio=2.0,
        profit_threshold_for_hiring=50,  # Very low threshold to hire managers immediately
        max_employees_strategy=100,
        queue_strategy="fifo",
        layout_strategy="moderate",
        layout_optimization_interval=30,  # More frequent optimization
        ev_threshold_for_swaps=8.0,  # Much lower threshold
        layout_queue_condition_ratio=20.0,  # Much more permissive queue condition
        manager_hiring_enabled=True,
        manager_hire_timing="profit_based"
    )
    return StandardizedAgent(env, params, "IntelligentHiring")

def create_intelligent_queue_agent(env) -> StandardizedAgent:
    """Intelligent Queue: Sustained profit hiring, smart queue management, moderate layout"""
    params = StandardizedAgentParams(
        hiring_strategy="sustained_profit",
        hire_threshold_ratio=3.0,
        fire_threshold_ratio=2.0,
        max_employees_strategy=100,
        profit_tracking_window=150,
        queue_strategy="smart",
        order_value_weight=0.3,  # 30% weight on order value
        distance_weight=0.7,     # 70% weight on distance (efficiency)
        layout_strategy="moderate",
        layout_optimization_interval=35,  # More frequent optimization
        ev_threshold_for_swaps=12.0,  # Lower threshold
        layout_queue_condition_ratio=20.0,  # Much more permissive
        manager_hiring_enabled=True,
        manager_hire_timing="profit_based"
    )
    return StandardizedAgent(env, params, "IntelligentQueue")

def create_distance_based_agent(env) -> StandardizedAgent:
    """Distance-based: Pure distance optimization for queue management"""
    params = StandardizedAgentParams(
        hiring_strategy="profit_based",
        hire_threshold_ratio=3.5,
        fire_threshold_ratio=2.0,
        profit_threshold_for_hiring=100,  # Much lower threshold
        max_employees_strategy=100,
        queue_strategy="distance_based",  # Pure distance optimization
        order_value_weight=0.0,          # No value consideration
        distance_weight=1.0,             # 100% distance optimization
        layout_strategy="moderate",
        layout_optimization_interval=40,  # More frequent optimization
        ev_threshold_for_swaps=15.0,  # Lower threshold
        layout_queue_condition_ratio=20.0,  # Much more permissive
        manager_hiring_enabled=True,
        manager_hire_timing="profit_based"
    )
    return StandardizedAgent(env, params, "DistanceBased")

def create_aggressive_swap_agent(env) -> StandardizedAgent:
    """Aggressive Swap: Forces frequent swaps for testing"""
    params = StandardizedAgentParams(
        hiring_strategy="fixed",
        queue_strategy="fifo",
        layout_strategy="moderate",
        layout_optimization_interval=10,  # Very frequent checks
        ev_threshold_for_swaps=1.0,  # Accept almost any benefit
        layout_queue_condition_ratio=50.0,  # Almost never blocked by queue
        manager_hiring_enabled=True,
        manager_hire_timing="immediate"
    )
    return StandardizedAgent(env, params, "AggressiveSwap")

def get_standardized_agents(env) -> Dict[str, StandardizedAgent]:
    """Get all standardized agents"""
    return {
        'greedy_std': create_greedy_agent(env),
        'random_std': create_random_agent(env),
        'fixed_std': create_fixed_hiring_agent(env),
        'intelligent_hiring': create_intelligent_hiring_agent(env),
        'intelligent_queue': create_intelligent_queue_agent(env),
        'distance_based': create_distance_based_agent(env),
        'aggressive_swap': create_aggressive_swap_agent(env)
    }