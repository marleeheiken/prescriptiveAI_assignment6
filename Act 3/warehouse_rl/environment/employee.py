import numpy as np
from typing import Tuple, List, Optional, Union
from enum import Enum
import heapq

class EmployeeState(Enum):
    IDLE = 0
    MOVING = 1
    PICKING_ITEM = 2
    DELIVERING = 3
    RELOCATING_ITEM = 4

class Employee:
    def __init__(self, employee_id: int, start_position: Tuple[int, int], salary_per_timestep: float = 0.30, is_manager: bool = False):
        self.id = employee_id
        self.is_manager = is_manager
        self.position = start_position
        self.salary_per_timestep = salary_per_timestep
        
        # Productivity based on salary
        self.base_speed_multiplier = self._calculate_speed_from_salary(salary_per_timestep)
        
        # State management
        self.state = EmployeeState.IDLE
        self.current_order_id = None
        self.order_items = []  # Items needed for current order
        self.items_collected = []
        self.target_position = None
        self.path = []
        self.target_item_position = None  # Position of storage cell we're picking from
        
        # Task management
        self.task_timer = 0  # For actions that take multiple timesteps
        self.is_carrying_item = False
        self.carrying_item_type = None
        
        # Relocation task
        self.relocation_task = None  # (source_pos, target_pos, stage, source_item, target_item)
        
        # Collision handling
        self.collision_wait_count = 0  # How long we've been waiting due to collisions
        self.last_collision_position = None  # Track where collision occurred
        self.collision_cooldown = 0  # Wait timer after moving to avoid collision
        self.failed_paths = set()  # Track failed pathfinding attempts to avoid repeating them
        
        # Stuck detection
        self.stuck_position = None
        self.stuck_timer = 0
        self.max_stuck_time = 3  # Reduced from 5 for faster response
        
        # Traffic jam detection
        self.traffic_jam_zones = set()  # Positions to avoid due to congestion
        self.last_positions = []  # Track recent positions to detect circular movement
        self.max_position_history = 8  # Reduced for more responsive detection
        self.global_traffic_zones = set()  # Shared traffic zones across all agents
        self.alternative_targets = []  # List of alternative targets when main target is blocked
        
        # Movement tracking for productivity
        self.steps_since_last_action = 0
    
    def _calculate_speed_from_salary(self, salary: float) -> float:
        """Calculate movement speed with piecewise linear diminishing returns"""
        
        # Piecewise linear function with diminishing marginal returns:
        # $0.15-1.00: slope = 1 (1:1 speed increase)
        # $1.00-2.00: slope = 0.5 (diminishing returns)
        # $2.00+: slope = 0.25 (severe diminishing returns)
        
        # Ensure $0.30 = 1x speed as baseline
        if salary <= 0.30:
            # Linear from 0.15 to 0.30: speed goes from ~0.5x to 1.0x
            return 0.5 + (salary - 0.15) * (0.5 / 0.15)
        elif salary <= 1.00:
            # Linear 1:1 slope from $0.30 (1x speed) to $1.00 (1.7x speed)
            return 1.0 + (salary - 0.30) * 1.0
        elif salary <= 2.00:
            # Diminishing returns: slope = 0.5
            # At $1.00 we have 1.7x speed, at $2.00 we have 2.2x speed
            base_speed_at_1 = 1.7
            return base_speed_at_1 + (salary - 1.00) * 0.5
        else:
            # Severe diminishing returns: slope = 0.25
            # At $2.00 we have 2.2x speed
            base_speed_at_2 = 2.2
            return base_speed_at_2 + (salary - 2.00) * 0.25
        
    def set_order(self, order_id: int, order_items: List[int]):
        if self.state == EmployeeState.IDLE:
            self.current_order_id = order_id
            self.order_items = [int(x) for x in order_items]  # Ensure consistent data types
            self.items_collected = []
            self.state = EmployeeState.MOVING
            # Reset recursion guards when starting new task
            self._recursion_guard = 0
            self._alternative_attempts = 0
            return True
        return False
    
    def set_relocation_task(self, source_pos: Tuple[int, int], target_pos: Tuple[int, int], warehouse_grid):
        if self.state == EmployeeState.IDLE:
            # Find walkable adjacent position to source
            source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
            if source_adjacent:
                # Get both items (target might be empty for a move operation)
                source_item = warehouse_grid.get_item_at_position(source_pos[0], source_pos[1])
                target_item = warehouse_grid.get_item_at_position(target_pos[0], target_pos[1])
                
                if source_item is not None:  # Source must have an item
                    self.relocation_task = (source_pos, target_pos, 'go_to_source', source_item, target_item)
                    self.state = EmployeeState.RELOCATING_ITEM
                    self.target_position = source_adjacent
                    # Calculate path to adjacent position first
                    self.calculate_path_to_target(warehouse_grid, source_adjacent)
                    return True
        return False
    
    def move_towards_target(self, warehouse_grid) -> bool:
        if not self.target_position or len(self.path) == 0:
            return False
        
        # Apply speed multiplier - higher paid workers move multiple times per timestep
        moves_this_timestep = int(self.base_speed_multiplier)  # 5x speed = 5 moves per timestep
        remaining_fractional = self.base_speed_multiplier - moves_this_timestep
        
        # Handle fractional part (e.g., 0.5x speed moves every other timestep)
        if remaining_fractional > 0:
            self.steps_since_last_action += remaining_fractional
            if self.steps_since_last_action >= 1.0:
                moves_this_timestep += 1
                self.steps_since_last_action -= 1.0
        
        # Make all the moves for this timestep
        for _ in range(moves_this_timestep):
            if not self.target_position or len(self.path) == 0:
                break
                
            next_position = self.path[0]
            
            # Check if next position is walkable (no collision)
            if warehouse_grid.is_walkable(next_position[0], next_position[1]):
                self.position = next_position
                self.path.pop(0)
                
                # Check if reached target
                if self.position == self.target_position:
                    self.target_position = None
                    self.path = []
                    return True
            else:
                # Collision - stop moving for this timestep
                break
        
        return len(self.path) == 0  # Return True if we completed the path
    
    def pick_item(self, warehouse_grid, item_type: int) -> bool:
        # Legacy method - pick from current position
        return self.pick_item_from_position(warehouse_grid, item_type, self.position)
    
    def pick_item_from_position(self, warehouse_grid, item_type: int, pick_position: Tuple[int, int]) -> bool:
        # Apply speed multiplier to picking tasks too
        pick_time = max(1, int(2.0 / self.base_speed_multiplier))  # Higher paid workers pick faster
        
        # Start picking task
        if self.task_timer == 0:
            self.task_timer = pick_time
            return False
        
        # Continue picking task
        if self.task_timer > 0:
            self.task_timer -= 1
            if self.task_timer == 0:
                # Picking complete
                item = warehouse_grid.pick_item_at_position(pick_position[0], pick_position[1])
                if item == item_type:
                    self.items_collected.append(int(item_type))  # Ensure consistent data type
                    warehouse_grid.update_item_access(item_type)
                    return True
            return False
        
        return False
    
    def deliver_items(self, warehouse_grid) -> dict:
        if not warehouse_grid.is_truck_bay_position(self.position):
            return {'items': [], 'order_id': None}
        
        # Apply speed multiplier to delivery tasks too
        delivery_time = max(1, int(2.0 / self.base_speed_multiplier))  # Higher paid workers deliver faster
        
        # Start delivery task
        if self.task_timer == 0:
            self.task_timer = delivery_time
            return {'items': [], 'order_id': None}
        
        # Continue delivery task
        if self.task_timer > 0:
            self.task_timer -= 1
            if self.task_timer == 0:
                # Delivery complete - return items AND order_id before clearing
                delivered_items = self.items_collected.copy()
                completed_order_id = self.current_order_id
                
                # Clear employee state
                self.items_collected = []
                self.order_items = []
                self.current_order_id = None
                self.state = EmployeeState.IDLE
                
                return {'items': delivered_items, 'order_id': completed_order_id}
            return {'items': [], 'order_id': None}
        
        return {'items': [], 'order_id': None}
    
    def step(self, warehouse_grid, assigned_positions: set = None) -> dict:
        if assigned_positions is None:
            assigned_positions = set()
        
        action_result = {
            'moved': False,
            'picked_item': None,
            'delivered_items': [],
            'completed_relocation': False,
            'collision': False,
            'stuck_resolved': False
        }
        
        # Handle collision cooldown
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1
            action_result['collision'] = True
            
            # When cooldown ends, recalculate path to target or find new task
            if self.collision_cooldown == 0:
                self._resume_task_after_collision(warehouse_grid)
            
            return action_result
        
        # Track position history for traffic jam detection
        self.last_positions.append(self.position)
        if len(self.last_positions) > self.max_position_history:
            self.last_positions.pop(0)
        
        # Detect circular movement (traffic jam indicator)
        if len(self.last_positions) >= 4:  # Reduced threshold for faster detection
            # Check if we're moving in circles
            recent_positions = set(self.last_positions[-4:])
            if len(recent_positions) <= 2:  # Only 2 unique positions in last 4 moves
                # Mark these positions as traffic jam zones
                self.traffic_jam_zones.update(recent_positions)
                self.global_traffic_zones.update(recent_positions)
                # Try to find alternative target immediately
                if self.target_position and self.target_position in recent_positions:
                    self._find_alternative_target(warehouse_grid)
                # Clear old traffic jam zones periodically
                if len(self.traffic_jam_zones) > 12:
                    # Keep only the most recent jam zones
                    self.traffic_jam_zones = set(list(self.traffic_jam_zones)[-8:])
        
        # Check if stuck in same position (only for MOVING state)
        if self.state == EmployeeState.MOVING:
            if self.stuck_position == self.position:
                self.stuck_timer += 1
                if self.stuck_timer >= self.max_stuck_time:
                    # Force unstuck by finding new target or clearing current one
                    self._handle_stuck_agent(warehouse_grid)
                    self.stuck_timer = 0
                    action_result['stuck_resolved'] = True
                    # Mark this position as a traffic jam zone
                    self.traffic_jam_zones.add(self.position)
            else:
                # Position changed, reset stuck detection
                self.stuck_position = self.position
                self.stuck_timer = 0
        
        if self.state == EmployeeState.IDLE:
            pass
        
        elif self.state == EmployeeState.MOVING:
            # First, check if we're stuck in a storage cell and need to escape
            from .warehouse_grid import CellType
            if (warehouse_grid.is_valid_position(self.position[0], self.position[1]) and
                warehouse_grid.cell_types[self.position[1], self.position[0]] == CellType.STORAGE.value):
                # We're in a storage cell! Move to nearest walkable space immediately
                self._escape_from_storage_cell(warehouse_grid, assigned_positions)
                action_result['moved'] = True
                return action_result
            
            # Check if we're at an item location we need (or adjacent to one)
            if self.current_order_id:
                # First check current position
                item_at_pos = warehouse_grid.get_item_at_position(self.position[0], self.position[1])
                if item_at_pos is not None and item_at_pos in self.order_items and item_at_pos not in self.items_collected:
                    self.state = EmployeeState.PICKING_ITEM
                    self.task_timer = 0  # Reset timer for picking
                    return action_result
                
                # Check adjacent positions for needed items
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    adj_x, adj_y = self.position[0] + dx, self.position[1] + dy
                    adjacent_item = warehouse_grid.get_item_at_position(adj_x, adj_y)
                    if (adjacent_item is not None and adjacent_item in self.order_items 
                        and adjacent_item not in self.items_collected):
                        # Pick from adjacent storage cell WITHOUT moving into it
                        from .warehouse_grid import CellType
                        if (warehouse_grid.is_valid_position(adj_x, adj_y) and 
                            warehouse_grid.cell_types[adj_y, adj_x] == CellType.STORAGE.value):
                            # Stay in current walkable position and pick from adjacent storage
                            self.state = EmployeeState.PICKING_ITEM
                            self.task_timer = 0  # Reset timer for picking
                            self.target_item_position = (adj_x, adj_y)  # Track which storage cell we're picking from
                            return action_result
            
            # Continue moving if we have a path
            if self.target_position and len(self.path) > 0:
                next_pos = self.path[0]
                # Check for collision with other employees
                if next_pos not in assigned_positions:
                    if self.move_towards_target(warehouse_grid):
                        action_result['moved'] = True
                        self.collision_wait_count = 0  # Reset collision counter on successful move
                        # Check if we've reached target and need to look for items or go to delivery
                        if not self.target_position:  # We just reached our target
                            if self.current_order_id:
                                # Check if we have all items for the order
                                items_needed = set(self.order_items) - set(self.items_collected)
                                if not items_needed:  # All items collected
                                    self.state = EmployeeState.DELIVERING
                                    self.task_timer = 0  # Reset timer for delivery
                                    nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                                    self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
                                # If we still need items, the logic below will find the next item
                else:
                    # Collision detected - implement improved deadlock resolution
                    action_result['collision'] = True
                    self.collision_wait_count += 1
                    self.last_collision_position = next_pos
                    
                    # More aggressive collision resolution
                    if self.collision_wait_count >= 2:  # Reduced from 3 for faster response
                        # Try collision resolution first
                        if self._handle_collision_deadlock(warehouse_grid, assigned_positions):
                            # Successfully moved to free space, will resume task after cooldown
                            pass
                        else:
                            # If can't find free space, try alternative target as last resort
                            # But avoid infinite recursion by limiting attempts
                            if not hasattr(self, '_alternative_attempts'):
                                self._alternative_attempts = 0
                            if self._alternative_attempts < 2:
                                self._alternative_attempts += 1
                                self._find_alternative_target(warehouse_grid)
                            else:
                                # Reset and just wait
                                self._alternative_attempts = 0
                                self.collision_cooldown = 3
                        self.collision_wait_count = 0
            # If no target or empty path, but still have an order, need to find next item
            elif self.current_order_id and (not self.target_position or len(self.path) == 0):
                # Find next item we need to collect
                items_needed = set(self.order_items) - set(self.items_collected)
                if items_needed:
                    # Find closest needed item with walkable access
                    closest_item_pos = self._find_closest_needed_item(warehouse_grid, items_needed)
                    if closest_item_pos:
                        # Find walkable adjacent position to the item (guaranteed to exist)
                        target_pos = self._find_walkable_adjacent_position(warehouse_grid, closest_item_pos)
                        self.calculate_path_to_target(warehouse_grid, target_pos)
                else:
                    # All items collected, go to delivery
                    self.state = EmployeeState.DELIVERING
                    self.task_timer = 0  # Reset timer for delivery
                    nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                    self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
        
        elif self.state == EmployeeState.PICKING_ITEM:
            if self.current_order_id:
                # Check if we have a specific target item position or pick from current position
                pick_position = getattr(self, 'target_item_position', None) or self.position
                item_at_pos = warehouse_grid.get_item_at_position(pick_position[0], pick_position[1])
                
                if item_at_pos is not None and item_at_pos in self.order_items:
                    if self.pick_item_from_position(warehouse_grid, item_at_pos, pick_position):
                        action_result['picked_item'] = item_at_pos
                        if hasattr(self, 'target_item_position'):
                            self.target_item_position = None  # Clear after picking
                        
                        # Check if we have all items needed for the order
                        items_needed = set(self.order_items)
                        items_collected = set(self.items_collected)
                        
                        if items_needed.issubset(items_collected):
                            # All items collected, go to delivery
                            self.state = EmployeeState.DELIVERING
                            self.task_timer = 0  # Reset timer for delivery
                            nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                            self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
                        else:
                            # Still need more items, continue moving to find them
                            self.state = EmployeeState.MOVING
                            # Clear target to force finding next needed item
                            self.target_position = None
                            self.path = []
                    # If pick_item returns False, just continue trying (timer-based)
                else:
                    # Item not here or wrong type, go back to moving to find correct item
                    self.state = EmployeeState.MOVING
                    self.task_timer = 0
                    # Don't clear target_position here - let the MOVING state handle finding next item
                    # Only clear if we have no items left to collect
                    items_needed = set(self.order_items) - set(self.items_collected)
                    if not items_needed:
                        # All items collected, go to delivery
                        self.state = EmployeeState.DELIVERING
                        nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                        self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
                    else:
                        # Still need items, clear target to force new search
                        self.target_position = None
                        self.path = []
        
        elif self.state == EmployeeState.DELIVERING:
            # First, check if we're stuck in a storage cell and need to escape
            from .warehouse_grid import CellType
            if (warehouse_grid.is_valid_position(self.position[0], self.position[1]) and
                warehouse_grid.cell_types[self.position[1], self.position[0]] == CellType.STORAGE.value):
                # We're in a storage cell! Move to nearest walkable space immediately
                self._escape_from_storage_cell(warehouse_grid, assigned_positions)
                action_result['moved'] = True
                return action_result
            
            # If not at any truck bay, move towards nearest one
            if not warehouse_grid.is_truck_bay_position(self.position):
                # Check if any truck bay position is occupied by another employee
                truck_bay_occupied = any(bay_pos in assigned_positions for bay_pos in warehouse_grid.truck_bay_positions)
                nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                
                if truck_bay_occupied and warehouse_grid.manhattan_distance(self.position, nearest_truck_bay) <= 2:
                    # If packing station is occupied and we're close, wait in current position
                    action_result['collision'] = True
                    # Don't increment collision count for waiting near packing station
                else:
                    # Always ensure we have a target and path to truck bay
                    if not self.target_position or not warehouse_grid.is_truck_bay_position(self.target_position):
                        nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                    self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
                    
                    if self.target_position and len(self.path) > 0:
                        next_pos = self.path[0]
                        if next_pos not in assigned_positions:
                            if self.move_towards_target(warehouse_grid):
                                action_result['moved'] = True
                                self.collision_wait_count = 0
                        else:
                            action_result['collision'] = True
                            self.collision_wait_count += 1
                            
                            # Handle deadlock for delivering employees too
                            if self.collision_wait_count >= 3:
                                self._handle_collision_deadlock(warehouse_grid, assigned_positions)
                                self.collision_wait_count = 0
                    else:
                        # No path found, try again next step
                        nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                    self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
            else:
                # At packing station, deliver items
                delivery_result = self.deliver_items(warehouse_grid)
                if delivery_result['items']:
                    action_result['delivered_items'] = delivery_result['items']
                    action_result['completed_order_id'] = delivery_result['order_id']
        
        elif self.state == EmployeeState.RELOCATING_ITEM:
            if self.relocation_task:
                source_pos, target_pos, stage, source_item, target_item = self.relocation_task
                
                if stage == 'go_to_source':
                    # Check if we're adjacent to source position
                    source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
                    if self.position == source_adjacent:
                        # Stay adjacent and pick up source item (like workers do)
                        item = warehouse_grid.remove_item_at_position(source_pos[0], source_pos[1])
                        if item == source_item:
                            self.is_carrying_item = True
                            self.carrying_item_type = item
                            # Now go to target - find adjacent position to target
                            target_adjacent = self._find_walkable_adjacent_position(warehouse_grid, target_pos)
                            if target_adjacent:
                                self.relocation_task = (source_pos, target_pos, 'go_to_target', source_item, target_item)
                                self.target_position = target_adjacent
                                self.calculate_path_to_target(warehouse_grid, target_adjacent)
                            else:
                                # No walkable adjacent to target, cancel relocation
                                self._cancel_relocation(warehouse_grid, item)
                        else:
                            # Wrong item or no item, cancel relocation
                            if item is not None:
                                warehouse_grid.set_item_at_position(source_pos[0], source_pos[1], item)
                            self._cancel_relocation(warehouse_grid)
                    else:
                        # Continue moving toward source adjacent position
                        if len(self.path) == 0 and source_adjacent:
                            self.calculate_path_to_target(warehouse_grid, source_adjacent)
                        
                        if len(self.path) > 0:
                            next_pos = self.path[0]
                            if next_pos not in assigned_positions:
                                if self.move_towards_target(warehouse_grid):
                                    self.collision_wait_count = 0
                            else:
                                action_result['collision'] = True
                                self.collision_wait_count += 1
                                if self.collision_wait_count >= 3:
                                    self._handle_collision_deadlock(warehouse_grid, assigned_positions)
                                    self.collision_wait_count = 0
                
                elif stage == 'go_to_target':
                    # Check if we're adjacent to target position
                    target_adjacent = self._find_walkable_adjacent_position(warehouse_grid, target_pos)
                    if self.position == target_adjacent:
                        # Stay adjacent and place item (like workers do when picking)
                        if self.is_carrying_item and self.carrying_item_type == source_item:
                            if target_item is None:
                                # Simple move to empty position - just place the item
                                warehouse_grid.set_item_at_position(target_pos[0], target_pos[1], self.carrying_item_type)
                                self.is_carrying_item = False
                                self.carrying_item_type = None
                                self.relocation_task = None
                                self.state = EmployeeState.IDLE
                                action_result['completed_relocation'] = True
                            else:
                                # Swap operation - pick up target item and place source item
                                current_target_item = warehouse_grid.remove_item_at_position(target_pos[0], target_pos[1])
                                # Place source item at target
                                # Place item at target position (debug silenced)
                                result = warehouse_grid.set_item_at_position(target_pos[0], target_pos[1], self.carrying_item_type)
                                self.is_carrying_item = False
                                
                                # Now carry target item back to source
                                if current_target_item == target_item:
                                    self.carrying_item_type = target_item
                                    self.is_carrying_item = True
                                    # Go back to source to complete the swap
                                    source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
                                    if source_adjacent:
                                        self.relocation_task = (source_pos, target_pos, 'return_to_source', source_item, target_item)
                                        self.target_position = source_adjacent
                                        self.calculate_path_to_target(warehouse_grid, source_adjacent)
                                    else:
                                        # Can't complete swap, cancel
                                        self._cancel_relocation(warehouse_grid, target_item)
                                else:
                                    # Target item changed, cancel
                                    self._cancel_relocation(warehouse_grid)
                    else:
                        # Continue moving toward target adjacent position
                        if len(self.path) == 0 and target_adjacent:
                            self.calculate_path_to_target(warehouse_grid, target_adjacent)
                        
                        if len(self.path) > 0:
                            next_pos = self.path[0]
                            if next_pos not in assigned_positions:
                                if self.move_towards_target(warehouse_grid):
                                    self.collision_wait_count = 0
                            else:
                                action_result['collision'] = True
                                self.collision_wait_count += 1
                                if self.collision_wait_count >= 3:
                                    self._handle_collision_deadlock(warehouse_grid, assigned_positions)
                                    self.collision_wait_count = 0
                
                elif stage == 'return_to_source':
                    # Check if we're adjacent to source position to complete the swap
                    source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
                    if self.position == source_adjacent:
                        # Stay adjacent and place target item back at source
                        if self.is_carrying_item and self.carrying_item_type == target_item:
                            # Place target item back at source (debug silenced)
                            result = warehouse_grid.set_item_at_position(source_pos[0], source_pos[1], self.carrying_item_type)
                            self.is_carrying_item = False
                            self.carrying_item_type = None
                            self.relocation_task = None
                            self.state = EmployeeState.IDLE
                            action_result['completed_relocation'] = True
                    else:
                        # Continue moving toward source adjacent position
                        if len(self.path) == 0 and source_adjacent:
                            self.calculate_path_to_target(warehouse_grid, source_adjacent)
                        
                        if len(self.path) > 0:
                            next_pos = self.path[0]
                            if next_pos not in assigned_positions:
                                if self.move_towards_target(warehouse_grid):
                                    self.collision_wait_count = 0
                            else:
                                action_result['collision'] = True
                                self.collision_wait_count += 1
                                if self.collision_wait_count >= 3:
                                    self._handle_collision_deadlock(warehouse_grid, assigned_positions)
                                    self.collision_wait_count = 0
        
        return action_result
    
    def _cancel_relocation(self, warehouse_grid, item_to_return=None):
        """Cancel relocation task and return item if carrying one"""
        if item_to_return is not None:
            # Return item to original position or find a suitable storage location
            warehouse_grid.set_item_at_position(self.position[0], self.position[1], item_to_return)
        
        self.is_carrying_item = False
        self.carrying_item_type = None
        self.relocation_task = None
        self.target_position = None
        self.path = []
        self.state = EmployeeState.IDLE
    
    def _find_closest_needed_item(self, warehouse_grid, needed_items: set) -> Optional[Tuple[int, int]]:
        """Find the closest item location that contains an item we need and has walkable access"""
        candidates = []
        
        for item_type in needed_items:
            item_locations = warehouse_grid.find_item_locations(item_type)
            for location in item_locations:
                # Check if this item has walkable adjacent positions
                walkable_pos = self._find_walkable_adjacent_position(warehouse_grid, location)
                if walkable_pos:
                    distance = warehouse_grid.manhattan_distance(self.position, location)
                    candidates.append((distance, location))
        
        if candidates:
            # Return closest item with walkable access
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        
        return None
    
    def _find_walkable_adjacent_position(self, warehouse_grid, item_position: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Find a walkable position adjacent to an item location"""
        x, y = item_position
        
        # Check all 4 adjacent positions
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            if warehouse_grid.is_walkable(adj_x, adj_y):
                return (adj_x, adj_y)
        
        return None
    
    def _handle_collision_deadlock(self, warehouse_grid, assigned_positions: set = None) -> bool:
        """Handle collision deadlocks with improved strategies"""
        if assigned_positions is None:
            assigned_positions = set()
            
        # Strategy 1: Find free spaces prioritizing those away from traffic jams
        free_spaces = []
        safe_spaces = []
        
        search_radius = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1),
                        (0, 2), (2, 0), (0, -2), (-2, 0)]  # Expanded search
        
        for dx, dy in search_radius:
            adj_x, adj_y = self.position[0] + dx, self.position[1] + dy
            adj_pos = (adj_x, adj_y)
            if (warehouse_grid.is_walkable(adj_x, adj_y) and 
                adj_pos not in assigned_positions):
                free_spaces.append(adj_pos)
                # Prioritize spaces away from traffic jams
                if adj_pos not in self.traffic_jam_zones and adj_pos not in self.global_traffic_zones:
                    safe_spaces.append(adj_pos)
        
        chosen_space = None
        if safe_spaces:
            # Prefer safe spaces away from traffic
            chosen_space = min(safe_spaces, 
                             key=lambda pos: warehouse_grid.manhattan_distance(pos, self.target_position) 
                             if self.target_position else 0)
        elif free_spaces:
            # Fall back to any free space
            chosen_space = min(free_spaces,
                             key=lambda pos: warehouse_grid.manhattan_distance(pos, self.target_position)
                             if self.target_position else 0)
        
        if chosen_space:
            self.position = chosen_space
            self.collision_cooldown = 1
            self.path = []
            # Mark the collision area as a traffic jam zone
            if self.last_collision_position:
                self.traffic_jam_zones.add(self.last_collision_position)
                self.global_traffic_zones.add(self.last_collision_position)
            return True
        else:
            # Strategy 2: Wait and try alternative pathfinding
            self.collision_cooldown = 2
            # Mark current path as failed
            if self.target_position:
                self.failed_paths.add((self.position, self.target_position))
            return False
    
    def _handle_stuck_agent(self, warehouse_grid):
        """Handle when an agent is stuck in the same position for too long"""
        # Mark current position as a traffic jam zone
        self.traffic_jam_zones.add(self.position)
        self.global_traffic_zones.add(self.position)
        
        if self.current_order_id:
            # Clear current target and path to force recalculation
            if self.target_position:
                self.failed_paths.add((self.position, self.target_position))
            self.target_position = None
            self.path = []
            
            # Find alternative targets more aggressively
            items_needed = set(self.order_items) - set(self.items_collected)
            if items_needed:
                self._find_alternative_item_target(warehouse_grid, items_needed)
            
        # If still no target found, reassess the task
        if not self.target_position:
            self._reassess_current_task(warehouse_grid)
    
    def calculate_path_to_target(self, warehouse_grid, target: Tuple[int, int]):
        self.target_position = target
        self._calculate_path(warehouse_grid)
    
    def _calculate_path(self, warehouse_grid):
        if not self.target_position:
            return
        
        # Check if this path has failed before
        path_key = (self.position, self.target_position)
        if path_key in self.failed_paths:
            # If this specific path has failed before, don't try alternatives again
            # Just clear the failed paths and try once more
            self.failed_paths.clear()
        
        # A* pathfinding with enhanced traffic jam avoidance
        start = self.position
        goal = self.target_position
        
        def heuristic(pos):
            base_cost = warehouse_grid.manhattan_distance(pos, goal)
            # Moderate penalty for traffic jam zones (reduced to prevent over-avoidance)
            if pos in self.traffic_jam_zones:
                base_cost += 5
            if pos in self.global_traffic_zones:
                base_cost += 8
            # Extra penalty for previously collision positions
            if pos == self.last_collision_position:
                base_cost += 10
            return base_cost
        
        open_set = [(heuristic(start), start)]
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                self.path = path
                return
            
            for neighbor in warehouse_grid.get_neighbors(current[0], current[1]):
                # Base movement cost
                move_cost = 1
                
                # Moderate penalty for entering traffic jam zones (reduced)
                if neighbor in self.traffic_jam_zones:
                    move_cost += 3
                if neighbor in self.global_traffic_zones:
                    move_cost += 4
                if neighbor == self.last_collision_position:
                    move_cost += 5
                
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, neighbor))
        
        # No path found - mark as failed
        if path_key not in self.failed_paths:
            self.failed_paths.add(path_key)
        self.path = []
    
    def _calculate_path_direct(self, warehouse_grid):
        """Calculate path without checking failed paths - used to prevent recursion"""
        if not self.target_position:
            return
        
        # A* pathfinding with enhanced traffic jam avoidance
        start = self.position
        goal = self.target_position
        
        def heuristic(pos):
            base_cost = warehouse_grid.manhattan_distance(pos, goal)
            # Moderate penalty for traffic jam zones (reduced to prevent over-avoidance)
            if pos in self.traffic_jam_zones:
                base_cost += 5
            if pos in self.global_traffic_zones:
                base_cost += 8
            # Extra penalty for previously collision positions
            if pos == self.last_collision_position:
                base_cost += 10
            return base_cost
        
        open_set = [(heuristic(start), start)]
        came_from = {}
        g_score = {start: 0}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                self.path = path
                return
            
            for neighbor in warehouse_grid.get_neighbors(current[0], current[1]):
                # Base movement cost
                move_cost = 1
                
                # Moderate penalty for entering traffic jam zones (reduced)
                if neighbor in self.traffic_jam_zones:
                    move_cost += 3
                if neighbor in self.global_traffic_zones:
                    move_cost += 4
                if neighbor == self.last_collision_position:
                    move_cost += 5
                
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, neighbor))
        
        # No path found
        self.path = []
    
    def _find_alternative_target(self, warehouse_grid) -> bool:
        """Find an alternative target when current target is blocked or causing traffic jams"""
        if not self.current_order_id:
            return False
            
        items_needed = set(self.order_items) - set(self.items_collected)
        if not items_needed:
            return False
            
        return self._find_alternative_item_target(warehouse_grid, items_needed)
    
    def _find_alternative_item_target(self, warehouse_grid, items_needed: set) -> bool:
        """Find alternative item targets avoiding traffic jam zones"""
        # Prevent recursion by limiting calls
        if not hasattr(self, '_recursion_guard'):
            self._recursion_guard = 0
        if self._recursion_guard > 2:
            return False
        
        self._recursion_guard += 1
        
        try:
            all_candidates = []
            
            for item_type in items_needed:
                item_locations = warehouse_grid.find_item_locations(item_type)
                for location in item_locations:
                    # Skip locations in traffic jam zones
                    if location in self.traffic_jam_zones or location in self.global_traffic_zones:
                        continue
                        
                    # Skip locations that are too close to collision areas
                    if (self.last_collision_position and 
                        warehouse_grid.manhattan_distance(location, self.last_collision_position) < 3):
                        continue
                    
                    walkable_pos = self._find_walkable_adjacent_position(warehouse_grid, location)
                    if walkable_pos:
                        # Check if the walkable position is also safe
                        if (walkable_pos not in self.traffic_jam_zones and 
                            walkable_pos not in self.global_traffic_zones):
                            distance = warehouse_grid.manhattan_distance(self.position, location)
                            all_candidates.append((distance, location, walkable_pos))
            
            if all_candidates:
                # Sort by distance and choose the closest safe option
                all_candidates.sort(key=lambda x: x[0])
                _, target_location, target_pos = all_candidates[0]
                # Set target directly without recursion
                self.target_position = target_pos
                self._calculate_path_direct(warehouse_grid)
                return True
            
            return False
        finally:
            self._recursion_guard -= 1
    
    def _resume_task_after_collision(self, warehouse_grid):
        """Resume the original task after collision resolution"""
        if self.state == EmployeeState.MOVING and self.current_order_id:
            # Resume order fulfillment - find next needed item
            items_needed = set(self.order_items) - set(self.items_collected)
            if items_needed:
                # Try to find the closest needed item, avoiding recent collision areas
                closest_item_pos = self._find_closest_needed_item_safe(warehouse_grid, items_needed)
                if closest_item_pos:
                    target_pos = self._find_walkable_adjacent_position(warehouse_grid, closest_item_pos)
                    if target_pos:
                        self.calculate_path_to_target(warehouse_grid, target_pos)
                        return
            else:
                # All items collected, go to delivery
                self.state = EmployeeState.DELIVERING
                nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
                return
        
        elif self.state == EmployeeState.DELIVERING:
            # Resume delivery - go to truck bay
            nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
            self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
            return
        
        elif self.state == EmployeeState.RELOCATING_ITEM and self.relocation_task:
            # Resume relocation task
            source_pos, target_pos, stage, source_item, target_item = self.relocation_task
            if stage == 'go_to_source':
                source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
                if source_adjacent:
                    self.calculate_path_to_target(warehouse_grid, source_adjacent)
            elif stage == 'go_to_target':
                target_adjacent = self._find_walkable_adjacent_position(warehouse_grid, target_pos)
                if target_adjacent:
                    self.calculate_path_to_target(warehouse_grid, target_adjacent)
            elif stage == 'return_to_source':
                source_adjacent = self._find_walkable_adjacent_position(warehouse_grid, source_pos)
                if source_adjacent:
                    self.calculate_path_to_target(warehouse_grid, source_adjacent)
            return
        
        # If no specific task, just stay idle
        self.target_position = None
        self.path = []

    def _find_closest_needed_item_safe(self, warehouse_grid, needed_items: set) -> Optional[Tuple[int, int]]:
        """Find closest needed item while avoiding collision zones"""
        candidates = []
        
        for item_type in needed_items:
            item_locations = warehouse_grid.find_item_locations(item_type)
            for location in item_locations:
                # Skip items in traffic jam zones or near recent collisions
                if (location in self.traffic_jam_zones or 
                    location in self.global_traffic_zones):
                    continue
                    
                if (self.last_collision_position and 
                    warehouse_grid.manhattan_distance(location, self.last_collision_position) < 2):
                    continue
                
                # Check if this item has walkable adjacent positions
                walkable_pos = self._find_walkable_adjacent_position(warehouse_grid, location)
                if walkable_pos and walkable_pos not in self.traffic_jam_zones:
                    distance = warehouse_grid.manhattan_distance(self.position, location)
                    candidates.append((distance, location))
        
        # If no safe candidates, fall back to any available item
        if not candidates:
            return self._find_closest_needed_item(warehouse_grid, needed_items)
        
        # Return closest safe item
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _reassess_current_task(self, warehouse_grid):
        """Reassess and restart current task when completely lost"""
        if self.state == EmployeeState.MOVING and self.current_order_id:
            # Restart order fulfillment from scratch
            items_needed = set(self.order_items) - set(self.items_collected)
            if items_needed:
                # Clear any failed paths and try again
                self.failed_paths.clear()
                closest_item_pos = self._find_closest_needed_item(warehouse_grid, items_needed)
                if closest_item_pos:
                    target_pos = self._find_walkable_adjacent_position(warehouse_grid, closest_item_pos)
                    if target_pos:
                        self.calculate_path_to_target(warehouse_grid, target_pos)
            else:
                # Go to delivery
                self.state = EmployeeState.DELIVERING
                nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
                self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
        
        elif self.state == EmployeeState.DELIVERING:
            # Go directly to truck bay
            nearest_truck_bay = warehouse_grid.get_nearest_truck_bay_position(self.position)
            self.calculate_path_to_target(warehouse_grid, nearest_truck_bay)
        
        elif self.state == EmployeeState.RELOCATING_ITEM:
            # Cancel relocation if completely stuck
            self._cancel_relocation(warehouse_grid)
        
        else:
            # Default to idle state if completely lost
            self.state = EmployeeState.IDLE
            self.target_position = None
            self.path = []

    def _escape_from_storage_cell(self, warehouse_grid, assigned_positions: set = None):
        """Immediately move out of a storage cell to the nearest walkable space"""
        if assigned_positions is None:
            assigned_positions = set()
        
        # Find the nearest walkable adjacent space
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            escape_x, escape_y = self.position[0] + dx, self.position[1] + dy
            escape_pos = (escape_x, escape_y)
            
            if (warehouse_grid.is_walkable(escape_x, escape_y) and 
                escape_pos not in assigned_positions):
                self.position = escape_pos
                # Clear any current path since we've moved unexpectedly
                self.path = []
                self.target_position = None
                return
        
        # If no adjacent walkable space, try a wider search
        for radius in range(2, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:
                        escape_x, escape_y = self.position[0] + dx, self.position[1] + dy
                        escape_pos = (escape_x, escape_y)
                        
                        if (warehouse_grid.is_walkable(escape_x, escape_y) and
                            escape_pos not in assigned_positions):
                            self.position = escape_pos
                            self.path = []
                            self.target_position = None
                            return

    def get_state(self) -> dict:
        return {
            'id': self.id,
            'position': self.position,
            'state': self.state.value,
            'current_order_id': self.current_order_id,
            'items_collected': self.items_collected.copy(),
            'target_position': self.target_position,
            'is_carrying_item': self.is_carrying_item,
            'carrying_item_type': self.carrying_item_type,
            'has_relocation_task': self.relocation_task is not None
        }