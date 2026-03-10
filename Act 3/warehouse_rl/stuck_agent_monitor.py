#!/usr/bin/env python3
"""
Comprehensive stuck agent monitor and warehouse simulation test.
This runs a full simulation and tracks when agents get stuck.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from environment.warehouse_env import WarehouseEnv
from environment.employee import Employee, EmployeeState
from environment.warehouse_grid import WarehouseGrid, CellType
import numpy as np
import time

class StuckAgentMonitor:
    def __init__(self, env):
        self.env = env
        self.stuck_history = {}  # agent_id -> list of stuck positions
        self.stuck_counters = {}  # agent_id -> consecutive stuck steps
        self.position_history = {}  # agent_id -> recent positions
        self.collision_counts = {}  # agent_id -> collision count
        self.max_history = 10
        self.stuck_threshold = 5  # Steps without meaningful progress
        
    def update(self, step_num):
        """Update monitoring for all agents"""
        stuck_agents = []
        
        for emp in self.env.employees:
            emp_id = emp.id
            current_pos = emp.position
            
            # Initialize tracking for new agents
            if emp_id not in self.position_history:
                self.position_history[emp_id] = []
                self.stuck_counters[emp_id] = 0
                self.stuck_history[emp_id] = []
                self.collision_counts[emp_id] = 0
            
            # Update position history
            self.position_history[emp_id].append(current_pos)
            if len(self.position_history[emp_id]) > self.max_history:
                self.position_history[emp_id].pop(0)
            
            # Check for stuck behavior
            if len(self.position_history[emp_id]) >= 3:
                recent_positions = set(self.position_history[emp_id][-5:])
                
                # Agent is stuck if they've only been in 1-2 positions recently
                if len(recent_positions) <= 1:
                    self.stuck_counters[emp_id] += 1
                else:
                    self.stuck_counters[emp_id] = 0
                
                # Report stuck agents
                if self.stuck_counters[emp_id] >= self.stuck_threshold:
                    stuck_info = {
                        'id': emp_id,
                        'position': current_pos,
                        'state': emp.state.name,
                        'stuck_steps': self.stuck_counters[emp_id],
                        'target': getattr(emp, 'target_position', None),
                        'order': getattr(emp, 'current_order_id', None),
                        'path_length': len(getattr(emp, 'path', [])),
                        'recent_positions': list(recent_positions)
                    }
                    
                    # Check if in storage cell
                    x, y = current_pos
                    if (self.env.warehouse_grid.is_valid_position(x, y) and
                        self.env.warehouse_grid.cell_types[y, x] == CellType.STORAGE.value):
                        stuck_info['in_storage'] = True
                    
                    # Check collision indicators
                    if hasattr(emp, 'collision_wait_count') and emp.collision_wait_count > 0:
                        stuck_info['collision_wait'] = emp.collision_wait_count
                    
                    stuck_agents.append(stuck_info)
        
        return stuck_agents
    
    def print_warehouse_layout(self):
        """Print detailed warehouse layout for analysis"""
        print("\n=== WAREHOUSE LAYOUT ANALYSIS ===")
        grid = self.env.warehouse_grid
        
        # Count cell types
        storage_count = np.sum(grid.cell_types == CellType.STORAGE.value)
        corridor_count = np.sum(grid.cell_types == CellType.EMPTY.value)
        packing_count = np.sum(grid.cell_types == CellType.PACKING_STATION.value)
        spawn_count = np.sum(grid.cell_types == CellType.SPAWN_ZONE.value)
        
        print(f"Grid size: {grid.width}x{grid.height}")
        print(f"Storage cells: {storage_count}")
        print(f"Corridor cells: {corridor_count}")
        print(f"Packing stations: {packing_count}")
        print(f"Spawn zones: {spawn_count}")
        print(f"Total agents: {len(self.env.employees)}")
        
        # Analyze corridor widths
        print("\nCorridor width analysis:")
        self._analyze_corridor_widths()
        
        # Print grid with agent positions
        print("\nCurrent layout (S=storage, .=corridor, P=packing, Z=spawn, A=agent):")
        employee_positions = {emp.position: f"A{emp.id}" for emp in self.env.employees}
        
        for y in range(min(20, grid.height)):  # Limit output
            row = f"{y:2d}: "
            for x in range(min(30, grid.width)):  # Limit output
                pos = (x, y)
                if pos in employee_positions:
                    row += f"{employee_positions[pos]:>3}"
                elif grid.cell_types[y, x] == CellType.STORAGE.value:
                    item = grid.item_grid[y, x]
                    if item != -1:
                        row += f"S{item%10}"
                    else:
                        row += " E"
                elif grid.cell_types[y, x] == CellType.PACKING_STATION.value:
                    row += " P"
                elif grid.cell_types[y, x] == CellType.SPAWN_ZONE.value:
                    row += " Z"
                elif grid.cell_types[y, x] == CellType.EMPTY.value:
                    row += " ."
                else:
                    row += " ?"
                row += " "
            print(row)
    
    def _analyze_corridor_widths(self):
        """Analyze corridor widths to check for 2-cell requirement"""
        grid = self.env.warehouse_grid
        narrow_corridors = 0
        
        for y in range(1, grid.height - 1):
            for x in range(1, grid.width - 1):
                if grid.cell_types[y, x] == CellType.EMPTY.value:
                    # Check horizontal corridor width
                    horizontal_width = 1
                    for dx in [-1, 1]:
                        if (x + dx >= 0 and x + dx < grid.width and
                            grid.cell_types[y, x + dx] == CellType.EMPTY.value):
                            horizontal_width += 1
                    
                    # Check vertical corridor width
                    vertical_width = 1
                    for dy in [-1, 1]:
                        if (y + dy >= 0 and y + dy < grid.height and
                            grid.cell_types[y + dy, x] == CellType.EMPTY.value):
                            vertical_width += 1
                    
                    # Count narrow spots
                    if horizontal_width < 2 and vertical_width < 2:
                        narrow_corridors += 1
        
        print(f"  Narrow corridor cells (< 2 wide): {narrow_corridors}")

def run_stuck_monitor_test():
    """Run a full simulation with stuck agent monitoring"""
    print("=== STUCK AGENT MONITORING TEST ===")
    
    # Create larger environment
    env = WarehouseEnv(
        grid_width=30,
        grid_height=20,
        num_item_types=10,
        max_employees=8,
        initial_employees=6,
        episode_length=500,
        render_mode=None
    )
    
    monitor = StuckAgentMonitor(env)
    
    # Reset environment
    obs, info = env.reset()
    monitor.print_warehouse_layout()
    
    print(f"\nStarting simulation with {len(env.employees)} agents...")
    
    stuck_report_interval = 20
    max_steps = 200
    total_stuck_incidents = 0
    
    for step in range(max_steps):
        # Take a random action (let the environment auto-manage)
        action = {
            'staffing_action': 0,
            'layout_swap': [0, 0],
            'order_assignments': [0] * 20
        }
        
        try:
            obs, reward, done, truncated, info = env.step(action)
        except Exception as e:
            print(f"Environment error at step {step}: {e}")
            break
        
        # Monitor for stuck agents
        stuck_agents = monitor.update(step)
        
        if stuck_agents:
            total_stuck_incidents += len(stuck_agents)
            print(f"\n🚨 STEP {step}: {len(stuck_agents)} agents stuck:")
            for agent_info in stuck_agents:
                print(f"  Agent {agent_info['id']}: {agent_info}")
        
        # Periodic reports
        if step % stuck_report_interval == 0 and step > 0:
            print(f"\n📊 Step {step} Status:")
            print(f"  Active agents: {len([e for e in env.employees if e.state != EmployeeState.IDLE])}")
            print(f"  Orders in queue: {len(env.order_queue.orders)}")
            print(f"  Total stuck incidents so far: {total_stuck_incidents}")
            
            # Check for persistent stuck agents
            persistent_stuck = [info for info in stuck_agents if info['stuck_steps'] > 10]
            if persistent_stuck:
                print(f"  ⚠️  {len(persistent_stuck)} agents persistently stuck!")
        
        if done or truncated:
            print(f"Simulation ended at step {step}")
            break
    
    print(f"\n=== FINAL REPORT ===")
    print(f"Total simulation steps: {step + 1}")
    print(f"Total stuck incidents: {total_stuck_incidents}")
    print(f"Average stuck incidents per step: {total_stuck_incidents / (step + 1):.2f}")
    
    # Final agent status
    print(f"\nFinal agent states:")
    for emp in env.employees:
        stuck_count = monitor.stuck_counters.get(emp.id, 0)
        status = "🔴 STUCK" if stuck_count > 5 else "🟢 OK"
        print(f"  Agent {emp.id}: {emp.state.name} at {emp.position} - {status}")

def test_warehouse_generation():
    """Test warehouse grid generation specifically"""
    print("\n=== WAREHOUSE GENERATION TEST ===")
    
    for size in [(20, 15), (30, 20), (40, 25)]:
        width, height = size
        print(f"\nTesting {width}x{height} warehouse:")
        
        env = WarehouseEnv(
            grid_width=width,
            grid_height=height,
            num_item_types=15,
            max_employees=10,
            initial_employees=8,
            episode_length=100,
            render_mode=None
        )
        
        env.reset()
        monitor = StuckAgentMonitor(env)
        monitor.print_warehouse_layout()

if __name__ == "__main__":
    print("Starting comprehensive warehouse simulation test...")
    
    try:
        test_warehouse_generation()
        run_stuck_monitor_test()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed.")