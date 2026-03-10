import pygame
import numpy as np
from typing import Dict, List, Tuple, Optional
import sys

class PygameRenderer:
    def __init__(self, env, window_width: int = 1200, window_height: int = 800):
        pygame.init()
        
        self.env = env
        self.window_width = window_width
        self.window_height = window_height
        
        # Grid display settings
        self.grid_size = min(500, window_height - 100)
        self.cell_size = self.grid_size // max(env.grid_width, env.grid_height)
        self.grid_offset_x = 20
        self.grid_offset_y = 20
        
        # Panel settings
        self.panel_width = window_width - self.grid_size - 60
        self.panel_x = self.grid_size + 40
        
        # Colors
        self.colors = {
            'background': (240, 240, 240),
            'grid_line': (200, 200, 200),
            'empty': (255, 255, 255),
            'storage': (220, 220, 255),
            'packing_station': (255, 200, 200),
            'spawn_zone': (200, 255, 200),
            'employee': (50, 50, 200),
            'employee_path': (150, 150, 255),
            'text': (0, 0, 0),
            'profit_positive': (0, 150, 0),
            'profit_negative': (200, 0, 0),
            'order_bg': (250, 250, 250),
            'order_border': (180, 180, 180),
            'relocation_started': (255, 200, 100),
            'relocation_completed': (100, 255, 100)
        }
        
        # Initialize display
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Warehouse RL Simulator")
        
        # Fonts
        self.font_large = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 14)
        
        # Simulation speed control
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.speed_multiplier = 1.0
        self.paused = False
        
        # Animation state
        self.employee_animations = {}
        
    def render(self) -> Optional[np.ndarray]:
        # Handle events
        self._handle_events()
        
        if not self.paused:
            # Clear screen
            self.screen.fill(self.colors['background'])
            
            # Draw warehouse grid
            self._draw_warehouse_grid()
            
            # Draw employees
            self._draw_employees()
            
            # Draw HUD panels
            self._draw_financial_panel()
            self._draw_orders_panel()
            self._draw_employee_panel()
            self._draw_metrics_panel()
            self._draw_relocations_panel()
            self._draw_controls()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps * self.speed_multiplier)
        
        # Return RGB array if needed
        if self.env.render_mode == "rgb_array":
            return self.get_rgb_array()
        
        return None
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_1:
                    self.speed_multiplier = 1.0
                elif event.key == pygame.K_2:
                    self.speed_multiplier = 2.0
                elif event.key == pygame.K_3:
                    self.speed_multiplier = 5.0
                elif event.key == pygame.K_4:
                    self.speed_multiplier = 10.0
                elif event.key == pygame.K_r:
                    self.env.reset()
    
    def _draw_warehouse_grid(self):
        try:
            from ..environment.warehouse_grid import CellType
        except ImportError:
            from environment.warehouse_grid import CellType
        
        grid = self.env.warehouse_grid
        
        for y in range(grid.height):
            for x in range(grid.width):
                rect = pygame.Rect(
                    self.grid_offset_x + x * self.cell_size,
                    self.grid_offset_y + y * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                
                # Choose color based on cell type
                cell_type = grid.cell_types[y, x]
                if cell_type == CellType.EMPTY.value:
                    color = self.colors['empty']
                elif cell_type == CellType.STORAGE.value:
                    color = self.colors['storage']
                elif cell_type == CellType.PACKING_STATION.value:
                    color = self.colors['packing_station']
                elif cell_type == CellType.SPAWN_ZONE.value:
                    color = self.colors['spawn_zone']
                else:
                    color = self.colors['empty']
                
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, self.colors['grid_line'], rect, 1)
                
                # Draw item type number if it's a storage cell with an item
                if (cell_type == CellType.STORAGE.value and 
                    grid.item_grid[y, x] != -1):
                    item_text = str(grid.item_grid[y, x])
                    text_surface = self.font_small.render(item_text, True, self.colors['text'])
                    text_rect = text_surface.get_rect(center=rect.center)
                    self.screen.blit(text_surface, text_rect)
    
    def _draw_employees(self):
        for employee in self.env.employees:
            # Draw employee path
            if len(employee.path) > 1:
                path_points = []
                # Current position
                curr_x = self.grid_offset_x + employee.position[0] * self.cell_size + self.cell_size // 2
                curr_y = self.grid_offset_y + employee.position[1] * self.cell_size + self.cell_size // 2
                path_points.append((curr_x, curr_y))
                
                # Path points
                for path_pos in employee.path:
                    path_x = self.grid_offset_x + path_pos[0] * self.cell_size + self.cell_size // 2
                    path_y = self.grid_offset_y + path_pos[1] * self.cell_size + self.cell_size // 2
                    path_points.append((path_x, path_y))
                
                if len(path_points) > 1:
                    pygame.draw.lines(self.screen, self.colors['employee_path'], False, path_points, 2)
            
            # Draw employee
            emp_x = self.grid_offset_x + employee.position[0] * self.cell_size + self.cell_size // 2
            emp_y = self.grid_offset_y + employee.position[1] * self.cell_size + self.cell_size // 2
            
            # Employee color based on state
            try:
                from ..environment.employee import EmployeeState
            except ImportError:
                from environment.employee import EmployeeState
            if employee.state == EmployeeState.IDLE:
                emp_color = (100, 100, 255)
            elif employee.state == EmployeeState.MOVING:
                emp_color = (255, 255, 100)
            elif employee.state == EmployeeState.PICKING_ITEM:
                emp_color = (255, 150, 100)
            elif employee.state == EmployeeState.DELIVERING:
                emp_color = (100, 255, 100)
            elif employee.state == EmployeeState.RELOCATING_ITEM:
                emp_color = (255, 100, 255)
            else:
                emp_color = self.colors['employee']
            
            pygame.draw.circle(self.screen, emp_color, (emp_x, emp_y), self.cell_size // 3)
            
            # Draw employee ID
            id_text = str(employee.id)
            text_surface = self.font_small.render(id_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(emp_x, emp_y))
            self.screen.blit(text_surface, text_rect)
    
    def _draw_financial_panel(self):
        y_offset = 20
        
        # Title
        title = self.font_large.render("Financial Status", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 30
        
        # Profit (large, colored)
        profit = self.env.cumulative_profit
        profit_color = self.colors['profit_positive'] if profit >= 0 else self.colors['profit_negative']
        profit_text = f"${profit:.2f}"
        profit_surface = self.font_large.render(profit_text, True, profit_color)
        self.screen.blit(profit_surface, (self.panel_x, y_offset))
        y_offset += 35
        
        # Revenue
        revenue_text = f"Revenue: ${self.env.total_revenue:.2f}"
        revenue_surface = self.font_medium.render(revenue_text, True, self.colors['text'])
        self.screen.blit(revenue_surface, (self.panel_x, y_offset))
        y_offset += 20
        
        # Costs
        costs_text = f"Costs: ${self.env.total_costs:.2f}"
        costs_surface = self.font_medium.render(costs_text, True, self.colors['text'])
        self.screen.blit(costs_surface, (self.panel_x, y_offset))
        y_offset += 20
        
        # Burn rate
        burn_rate = len(self.env.employees) * self.env.employee_salary
        burn_text = f"Burn Rate: ${burn_rate:.2f}/step"
        burn_surface = self.font_medium.render(burn_text, True, self.colors['text'])
        self.screen.blit(burn_surface, (self.panel_x, y_offset))
    
    def _draw_orders_panel(self):
        y_offset = 140
        
        # Title
        title = self.font_large.render("Order Queue", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 25
        
        # Queue summary
        queue_length = len(self.env.order_queue.orders)
        summary_text = f"Orders: {queue_length}"
        summary_surface = self.font_medium.render(summary_text, True, self.colors['text'])
        self.screen.blit(summary_surface, (self.panel_x, y_offset))
        y_offset += 25
        
        # Individual orders (first 6)
        orders = self.env.order_queue.get_queue_state(self.env.current_timestep)[:6]
        
        for order in orders:
            # Order background
            order_rect = pygame.Rect(self.panel_x, y_offset, self.panel_width - 20, 20)
            pygame.draw.rect(self.screen, self.colors['order_bg'], order_rect)
            pygame.draw.rect(self.screen, self.colors['order_border'], order_rect, 1)
            
            # Order text
            order_text = f"#{order['id']} | {order['num_items']} items | ${order['value']} | {order['time_remaining']}s"
            order_surface = self.font_small.render(order_text, True, self.colors['text'])
            self.screen.blit(order_surface, (self.panel_x + 5, y_offset + 3))
            
            y_offset += 22
    
    def _draw_employee_panel(self):
        y_offset = 340
        
        # Title
        title = self.font_large.render("Employees", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 25
        
        # Employee count
        count_text = f"Count: {len(self.env.employees)}/{self.env.max_employees}"
        count_surface = self.font_medium.render(count_text, True, self.colors['text'])
        self.screen.blit(count_surface, (self.panel_x, y_offset))
        y_offset += 25
        
        # Employee status
        try:
            from ..environment.employee import EmployeeState
        except ImportError:
            from environment.employee import EmployeeState
        state_counts = {state: 0 for state in EmployeeState}
        for employee in self.env.employees:
            state_counts[employee.state] += 1
        
        for state, count in state_counts.items():
            if count > 0:
                state_text = f"{state.name}: {count}"
                state_surface = self.font_small.render(state_text, True, self.colors['text'])
                self.screen.blit(state_surface, (self.panel_x, y_offset))
                y_offset += 15
    
    def _draw_metrics_panel(self):
        y_offset = 450
        
        # Title
        title = self.font_large.render("Metrics", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 25
        
        # Order statistics
        stats = self.env.order_queue.get_statistics()
        
        metrics = [
            f"Completed: {stats['completed_orders']}",
            f"Cancelled: {stats['cancelled_orders']}",
            f"Rate: {stats['completion_rate']:.1%}",
            f"Avg Time: {stats['avg_completion_time']:.1f}s"
        ]
        
        for metric in metrics:
            metric_surface = self.font_small.render(metric, True, self.colors['text'])
            self.screen.blit(metric_surface, (self.panel_x, y_offset))
            y_offset += 15
    
    def _draw_relocations_panel(self):
        y_offset = 540
        
        # Title
        title = self.font_large.render("Item Relocations", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 25
        
        if not hasattr(self.env, 'relocations_history'):
            return
        
        # Total relocations
        total_relocations = len(self.env.relocations_history)
        completed_relocations = sum(1 for r in self.env.relocations_history if r['status'] == 'completed')
        
        summary_text = f"Total: {total_relocations} | Completed: {completed_relocations}"
        summary_surface = self.font_medium.render(summary_text, True, self.colors['text'])
        self.screen.blit(summary_surface, (self.panel_x, y_offset))
        y_offset += 25
        
        # Recent relocations (last 3)
        recent_relocations = self.env.relocations_history[-3:]
        
        for relocation in recent_relocations:
            # Relocation background
            reloc_rect = pygame.Rect(self.panel_x, y_offset, self.panel_width - 20, 18)
            
            # Color based on status
            if relocation['status'] == 'started':
                bg_color = self.colors['relocation_started']
            else:
                bg_color = self.colors['relocation_completed']
            
            pygame.draw.rect(self.screen, bg_color, reloc_rect)
            pygame.draw.rect(self.screen, self.colors['order_border'], reloc_rect, 1)
            
            # Relocation text
            from_pos = relocation['from_pos']
            to_pos = relocation['to_pos']
            item_type = relocation['item_type']
            timestep = relocation['timestep']
            
            reloc_text = f"Item {item_type}: ({from_pos[0]},{from_pos[1]}) → ({to_pos[0]},{to_pos[1]}) @{timestep}"
            if relocation['status'] == 'completed':
                duration = relocation.get('completed_timestep', timestep) - timestep
                reloc_text += f" ✓({duration}s)"
            else:
                reloc_text += " ⏳"
            
            reloc_surface = self.font_small.render(reloc_text, True, self.colors['text'])
            self.screen.blit(reloc_surface, (self.panel_x + 5, y_offset + 2))
            
            y_offset += 20
    
    def _draw_controls(self):
        y_offset = 660
        
        # Title
        title = self.font_medium.render("Controls", True, self.colors['text'])
        self.screen.blit(title, (self.panel_x, y_offset))
        y_offset += 20
        
        # Control instructions
        controls = [
            "SPACE: Pause/Resume",
            "1-4: Speed (1x, 2x, 5x, 10x)",
            "R: Reset Episode"
        ]
        
        for control in controls:
            control_surface = self.font_small.render(control, True, self.colors['text'])
            self.screen.blit(control_surface, (self.panel_x, y_offset))
            y_offset += 15
        
        # Current speed and status
        status_text = f"Speed: {self.speed_multiplier}x"
        if self.paused:
            status_text += " (PAUSED)"
        
        status_surface = self.font_small.render(status_text, True, self.colors['text'])
        self.screen.blit(status_surface, (self.panel_x, y_offset + 10))
        
        # Timestep
        timestep_text = f"Timestep: {self.env.current_timestep}/{self.env.episode_length}"
        timestep_surface = self.font_small.render(timestep_text, True, self.colors['text'])
        self.screen.blit(timestep_surface, (self.panel_x, y_offset + 25))
    
    def get_rgb_array(self) -> np.ndarray:
        # Convert pygame surface to numpy array
        rgb_array = pygame.surfarray.array3d(self.screen)
        rgb_array = np.transpose(rgb_array, (1, 0, 2))  # Pygame uses (width, height, channels)
        return rgb_array
    
    def close(self):
        pygame.quit()