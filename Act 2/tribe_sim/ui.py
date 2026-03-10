import pygame
import math
from config import *

class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # Button rects
        self.next_gen_button = pygame.Rect(SIMULATION_WIDTH + 20, 400, 260, 40)
        self.reset_button = pygame.Rect(SIMULATION_WIDTH + 20, 450, 260, 40)
        self.cycle_graph_button = pygame.Rect(SIMULATION_WIDTH + 20, 500, 260, 30)
        
        self.button_hover = None
        
        # Graph cycling
        self.graph_types = ['fitness', 'traits', 'tribe_comparison']
        self.current_graph = 0
    
    def handle_mouse_hover(self, mouse_pos):
        self.button_hover = None
        if self.next_gen_button.collidepoint(mouse_pos):
            self.button_hover = 'next_gen'
        elif self.reset_button.collidepoint(mouse_pos):
            self.button_hover = 'reset'
        elif self.cycle_graph_button.collidepoint(mouse_pos):
            self.button_hover = 'cycle_graph'
    
    def handle_click(self, mouse_pos):
        if self.next_gen_button.collidepoint(mouse_pos):
            return 'next_generation'
        elif self.reset_button.collidepoint(mouse_pos):
            return 'reset'
        elif self.cycle_graph_button.collidepoint(mouse_pos):
            self.current_graph = (self.current_graph + 1) % len(self.graph_types)
            return 'cycle_graph'
        return None
    
    def draw_stats_panel(self, tribe_name, ga, population, frame_count, last_advance_reason="Time", tribe_comparison_history=None, cooperation_stats=None):
        # Draw panel background
        panel_rect = pygame.Rect(SIMULATION_WIDTH, 0, STATS_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['panel_bg'], panel_rect)
        
        # Draw vertical separator
        pygame.draw.line(self.screen, COLORS['boundary'], 
                        (SIMULATION_WIDTH, 0), (SIMULATION_WIDTH, WINDOW_HEIGHT), 2)
        
        y_offset = 20
        
        # Tribe name
        tribe_text = self.font_large.render(tribe_name, True, COLORS['text'])
        self.screen.blit(tribe_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 50
        
        # Generation
        gen_text = self.font_medium.render(f"Generation: {ga.generation}", True, COLORS['text'])
        self.screen.blit(gen_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 25
        
        # Last advance reason (if not generation 1)
        if ga.generation > 1:
            reason_color = COLORS['gatherer_low'] if last_advance_reason == "Extinct" else COLORS['text']
            reason_text = self.font_small.render(f"Last advance: {last_advance_reason}", True, reason_color)
            self.screen.blit(reason_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 20
        
        # Generation progress
        progress = min(1.0, frame_count / GENERATION_LENGTH)
        progress_rect = pygame.Rect(SIMULATION_WIDTH + 20, y_offset, 260, 10)
        pygame.draw.rect(self.screen, COLORS['boundary'], progress_rect)
        fill_width = int(260 * progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(SIMULATION_WIDTH + 20, y_offset, fill_width, 10)
            pygame.draw.rect(self.screen, COLORS['gatherer_high'], fill_rect)
        y_offset += 25
        
        # Population stats
        stats = ga.get_population_stats(population)
        
        pop_text = self.font_small.render(f"Population: {stats['alive_count']} / {stats['total_count']}", True, COLORS['text'])
        self.screen.blit(pop_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 25
        
        avg_fit_text = self.font_small.render(f"Avg Fitness: {stats['avg_fitness']:.2f}", True, COLORS['text'])
        self.screen.blit(avg_fit_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 20
        
        best_fit_text = self.font_small.render(f"Best Fitness: {stats['best_fitness']:.2f}", True, COLORS['text'])
        self.screen.blit(best_fit_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 20
        
        avg_speed_text = self.font_small.render(f"Avg Speed: {stats['avg_speed']:.2f}", True, COLORS['text'])
        self.screen.blit(avg_speed_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 20
        
        avg_caution_text = self.font_small.render(f"Avg Caution: {stats['avg_caution']:.1f}", True, COLORS['text'])
        self.screen.blit(avg_caution_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 20
        
        avg_cooperation_text = self.font_small.render(f"Avg Cooperation: {stats['avg_cooperation']:.2f}", True, COLORS['text'])
        self.screen.blit(avg_cooperation_text, (SIMULATION_WIDTH + 20, y_offset))
        y_offset += 25
        
        # Cooperation outcomes bar graph
        if cooperation_stats:
            self.draw_cooperation_bar_graph(cooperation_stats, SIMULATION_WIDTH + 20, y_offset)
            y_offset += 90
        else:
            y_offset += 15
        
        # Buttons
        self.draw_button(self.next_gen_button, "Next Generation", self.button_hover == 'next_gen')
        self.draw_button(self.reset_button, "Reset Simulation", self.button_hover == 'reset')
        
        # Graph cycling button
        self.draw_button(self.cycle_graph_button, "Change Graph", self.button_hover == 'cycle_graph')
        
        # Graph title
        graph_titles = {
            'fitness': 'GA Performance vs Other Tribes (%)',
            'traits': 'Trait Evolution', 
            'tribe_comparison': 'Tribe Fitness Comparison'
        }
        current_title = graph_titles[self.graph_types[self.current_graph]]
        title_text = self.font_medium.render(current_title, True, COLORS['text'])
        self.screen.blit(title_text, (SIMULATION_WIDTH + 20, 545))
        
        # Draw appropriate graph based on current selection
        if self.current_graph == 0 and tribe_comparison_history and len(tribe_comparison_history) > 1:
            self.draw_relative_fitness_graph(tribe_comparison_history, SIMULATION_WIDTH + 20, 570)
        elif self.current_graph == 1 and len(ga.trait_history) > 1:
            self.draw_trait_graph(ga.trait_history, SIMULATION_WIDTH + 20, 570)
        elif self.current_graph == 2 and tribe_comparison_history and len(tribe_comparison_history) > 1:
            self.draw_tribe_comparison_graph(tribe_comparison_history, SIMULATION_WIDTH + 20, 570)
    
    def draw_button(self, rect, text, hovered):
        color = COLORS['button_hover'] if hovered else COLORS['button']
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, COLORS['boundary'], rect, 2)
        
        text_surface = self.font_small.render(text, True, COLORS['text'])
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def draw_fitness_graph(self, fitness_history, x, y):
        if len(fitness_history) < 2:
            return
        
        graph_width = 260
        graph_height = 150
        
        # Draw graph background
        graph_rect = pygame.Rect(x, y, graph_width, graph_height)
        pygame.draw.rect(self.screen, COLORS['background'], graph_rect)
        pygame.draw.rect(self.screen, COLORS['boundary'], graph_rect, 1)
        
        
        # Show only last 20 generations
        recent_history = fitness_history[-20:]
        if len(recent_history) < 2:
            return
        
        # Find min/max for scaling
        all_values = []
        for entry in recent_history:
            all_values.extend([entry['best_fitness'], entry['avg_fitness']])
        
        if not all_values:
            return
        
        min_fitness = min(all_values)
        max_fitness = max(all_values)
        
        if max_fitness == min_fitness:
            max_fitness = min_fitness + 1
        
        # Draw lines
        def scale_y(fitness):
            return y + graph_height - int(((fitness - min_fitness) / (max_fitness - min_fitness)) * graph_height)
        
        def scale_x(generation_index):
            return x + int((generation_index / max(1, len(recent_history) - 1)) * graph_width)
        
        # Best fitness line (green)
        if len(recent_history) > 1:
            best_points = []
            avg_points = []
            
            for i, entry in enumerate(recent_history):
                x_pos = scale_x(i)
                best_y = scale_y(entry['best_fitness'])
                avg_y = scale_y(entry['avg_fitness'])
                
                best_points.append((x_pos, best_y))
                avg_points.append((x_pos, avg_y))
            
            if len(best_points) > 1:
                pygame.draw.lines(self.screen, COLORS['gatherer_high'], False, best_points, 2)
            if len(avg_points) > 1:
                pygame.draw.lines(self.screen, COLORS['gatherer_mid'], False, avg_points, 2)
        
        # Legend
        legend_y = y + graph_height + 5
        legend_best = self.font_small.render("Best", True, COLORS['gatherer_high'])
        legend_avg = self.font_small.render("Avg", True, COLORS['gatherer_mid'])
        self.screen.blit(legend_best, (x, legend_y))
        self.screen.blit(legend_avg, (x + 50, legend_y))
    
    def draw_relative_fitness_graph(self, tribe_comparison_history, x, y):
        if len(tribe_comparison_history) < 2:
            return
        
        graph_width = 260
        graph_height = 120
        
        # Draw graph background
        graph_rect = pygame.Rect(x, y, graph_width, graph_height)
        pygame.draw.rect(self.screen, COLORS['background'], graph_rect)
        pygame.draw.rect(self.screen, COLORS['boundary'], graph_rect, 1)
        
        # Show only last 20 generations
        recent_history = tribe_comparison_history[-20:]
        if len(recent_history) < 2:
            return
        
        # Calculate relative performance for each generation
        relative_data = []
        for entry in recent_history:
            ga_avg = entry['ga_tribe']['avg_fitness']
            ga_best = entry['ga_tribe']['best_fitness']
            
            # Calculate field average (average of all other tribes)
            field_avg = (
                entry['ninja_tribe']['avg_fitness'] + 
                entry['runner_tribe']['avg_fitness'] + 
                entry['farmer_tribe']['avg_fitness']
            ) / 3
            
            # Calculate field best (best performer from all other tribes)
            field_best = max(
                entry['ninja_tribe']['best_fitness'],
                entry['runner_tribe']['best_fitness'], 
                entry['farmer_tribe']['best_fitness']
            )
            
            # Calculate percentage differences
            # GA Average vs Field Average
            if field_avg > 0:
                ga_avg_vs_field_avg = ((ga_avg - field_avg) / field_avg) * 100
            else:
                ga_avg_vs_field_avg = 0
                
            # GA Best vs Field Best
            if field_best > 0:
                ga_best_vs_field_best = ((ga_best - field_best) / field_best) * 100
            else:
                ga_best_vs_field_best = 0
            
            relative_data.append({
                'ga_avg_vs_field_avg': ga_avg_vs_field_avg,
                'ga_best_vs_field_best': ga_best_vs_field_best
            })
        
        if not relative_data:
            return
        
        # Find min/max for scaling (center around 0%)
        all_values = []
        for entry in relative_data:
            all_values.extend([entry['ga_avg_vs_field_avg'], entry['ga_best_vs_field_best']])
        
        if not all_values:
            return
        
        min_val = min(all_values)
        max_val = max(all_values)
        
        # Ensure 0% line is visible
        min_val = min(min_val, -10)
        max_val = max(max_val, 10)
        
        if max_val == min_val:
            max_val = min_val + 10
        
        # Draw 0% reference line
        zero_y = y + graph_height - int(((0 - min_val) / (max_val - min_val)) * graph_height)
        pygame.draw.line(self.screen, COLORS['boundary'], (x, zero_y), (x + graph_width, zero_y), 1)
        
        # Add 0% label
        zero_label = self.font_small.render("0%", True, COLORS['text'])
        self.screen.blit(zero_label, (x - 20, zero_y - 8))
        
        # Draw percentage lines
        def draw_percentage_line(values, color):
            if len(values) > 1:
                points = []
                for i, value in enumerate(values):
                    x_pos = x + int((i / max(1, len(values) - 1)) * graph_width)
                    y_pos = y + graph_height - int(((value - min_val) / (max_val - min_val)) * graph_height)
                    points.append((x_pos, y_pos))
                
                if len(points) > 1:
                    pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Draw lines
        ga_avg_values = [entry['ga_avg_vs_field_avg'] for entry in relative_data]
        ga_best_values = [entry['ga_best_vs_field_best'] for entry in relative_data]
        
        draw_percentage_line(ga_avg_values, COLORS['gatherer_mid'])  # Yellow
        draw_percentage_line(ga_best_values, COLORS['gatherer_high'])  # Green
        
        # Legend
        legend_y = y + graph_height + 5
        legend_avg = self.font_small.render("Avg GA vs Field Avg", True, COLORS['gatherer_mid'])
        legend_best = self.font_small.render("Best GA vs Best Field", True, COLORS['gatherer_high'])
        self.screen.blit(legend_avg, (x, legend_y))
        self.screen.blit(legend_best, (x + 120, legend_y))
    
    def draw_trait_graph(self, trait_history, x, y):
        if len(trait_history) < 2:
            return
        
        graph_width = 260
        graph_height = 120
        
        # Draw graph background
        graph_rect = pygame.Rect(x, y, graph_width, graph_height)
        pygame.draw.rect(self.screen, COLORS['background'], graph_rect)
        pygame.draw.rect(self.screen, COLORS['boundary'], graph_rect, 1)
        
        
        # Show only last 20 generations
        recent_history = trait_history[-20:]
        if len(recent_history) < 2:
            return
        
        # Normalize traits for display (0-1 range)
        def normalize_trait(trait_values, trait_name):
            if trait_name == 'avg_speed':
                return [(val - 0.5) / 2.5 for val in trait_values]  # 0.5-3.0 -> 0-1
            elif trait_name == 'avg_caution':
                return [val / 100 for val in trait_values]  # 0-100 -> 0-1
            elif trait_name == 'avg_search_pattern':
                return trait_values  # Already 0-1
            elif trait_name == 'avg_efficiency':
                return [(val - 0.5) / 1.5 for val in trait_values]  # 0.5-2.0 -> 0-1
            elif trait_name == 'avg_cooperation':
                return trait_values  # Already 0-1
            return trait_values
        
        # Draw trait lines
        trait_colors = {
            'avg_speed': (255, 100, 100),      # Red
            'avg_caution': (100, 255, 100),   # Green  
            'avg_search_pattern': (100, 100, 255),  # Blue
            'avg_efficiency': (255, 255, 100),  # Yellow
            'avg_cooperation': (255, 100, 255)  # Magenta
        }
        
        for trait_name, color in trait_colors.items():
            trait_values = [entry[trait_name] for entry in recent_history]
            normalized_values = normalize_trait(trait_values, trait_name)
            
            if len(normalized_values) > 1:
                points = []
                for i, norm_val in enumerate(normalized_values):
                    x_pos = x + int((i / max(1, len(normalized_values) - 1)) * graph_width)
                    y_pos = y + graph_height - int(norm_val * graph_height)
                    points.append((x_pos, y_pos))
                
                if len(points) > 1:
                    pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Legend
        legend_y = y + graph_height + 5
        legend_items = [
            ("Speed", (255, 100, 100)),
            ("Caution", (100, 255, 100)),
            ("Search", (100, 100, 255)),
            ("Efficiency", (255, 255, 100)),
            ("Cooperation", (255, 100, 255))
        ]
        
        for i, (name, color) in enumerate(legend_items):
            legend_text = self.font_small.render(name, True, color)
            # Rotate text 45 degrees to fit more labels
            rotated_text = pygame.transform.rotate(legend_text, 45)
            self.screen.blit(rotated_text, (x + i * 52, legend_y))
    
    def draw_tribe_comparison_graph(self, comparison_history, x, y):
        if len(comparison_history) < 2:
            return
        
        graph_width = 260
        graph_height = 120
        
        # Draw graph background
        graph_rect = pygame.Rect(x, y, graph_width, graph_height)
        pygame.draw.rect(self.screen, COLORS['background'], graph_rect)
        pygame.draw.rect(self.screen, COLORS['boundary'], graph_rect, 1)
        
        
        # Show only last 20 generations
        recent_history = comparison_history[-20:]
        if len(recent_history) < 2:
            return
        
        # Find min/max fitness for scaling
        all_fitness = []
        for entry in recent_history:
            all_fitness.extend([
                entry['ga_tribe']['avg_fitness'],
                entry['ninja_tribe']['avg_fitness'],
                entry['runner_tribe']['avg_fitness'],
                entry['farmer_tribe']['avg_fitness']
            ])
        
        if not all_fitness:
            return
        
        min_fitness = min(all_fitness)
        max_fitness = max(all_fitness)
        
        if max_fitness == min_fitness:
            max_fitness = min_fitness + 1
        
        # Draw tribe fitness lines
        tribe_colors = {
            'ga_tribe': COLORS['gatherer_high'],      # Green (evolving)
            'ninja_tribe': (150, 150, 255),          # Light blue
            'runner_tribe': (255, 150, 150),         # Light red
            'farmer_tribe': (255, 255, 150)          # Light yellow
        }
        
        for tribe_name, color in tribe_colors.items():
            fitness_values = [entry[tribe_name]['avg_fitness'] for entry in recent_history]
            
            if len(fitness_values) > 1:
                points = []
                for i, fitness in enumerate(fitness_values):
                    x_pos = x + int((i / max(1, len(fitness_values) - 1)) * graph_width)
                    y_pos = y + graph_height - int(((fitness - min_fitness) / (max_fitness - min_fitness)) * graph_height)
                    points.append((x_pos, y_pos))
                
                if len(points) > 1:
                    pygame.draw.lines(self.screen, color, False, points, 2)
        
        # Legend
        legend_y = y + graph_height + 5
        legend_items = [
            ("GA", COLORS['gatherer_high']),
            ("Ninja", (150, 150, 255)),
            ("Runner", (255, 150, 150)),
            ("Farmer", (255, 255, 150))
        ]
        
        for i, (name, color) in enumerate(legend_items):
            legend_text = self.font_small.render(name, True, color)
            self.screen.blit(legend_text, (x + i * 65, legend_y))
    
    def draw_cooperation_bar_graph(self, cooperation_stats, x, y):
        """Draw a bar graph showing cooperation outcomes"""
        # Title
        title_text = self.font_small.render("Cooperation Outcomes:", True, COLORS['text'])
        self.screen.blit(title_text, (x, y))
        y += 35
        
        # Bar graph settings
        bar_width = 50
        bar_spacing = 55
        max_height = 40
        
        # Get max value for scaling
        values = [
            cooperation_stats['mutual_cooperation'],
            cooperation_stats['exploitation'], 
            cooperation_stats['mutual_defection']
        ]
        max_value = max(values) if max(values) > 0 else 1
        
        # Bar colors and labels
        bars = [
            (cooperation_stats['mutual_cooperation'], (0, 255, 0), "Coop"),
            (cooperation_stats['exploitation'], (255, 255, 0), "Expl"),
            (cooperation_stats['mutual_defection'], (255, 0, 0), "Defect")
        ]
        
        for i, (value, color, label) in enumerate(bars):
            bar_x = x + i * bar_spacing
            bar_height = int((value / max_value) * max_height) if max_value > 0 else 0
            bar_y = y + max_height - bar_height
            
            # Draw bar
            if bar_height > 0:
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, bar_width, bar_height))
            
            # Draw border
            pygame.draw.rect(self.screen, COLORS['boundary'], (bar_x, y, bar_width, max_height), 1)
            
            # Draw value on top
            value_text = self.font_small.render(str(value), True, COLORS['text'])
            value_rect = value_text.get_rect(center=(bar_x + bar_width//2, bar_y - 10))
            self.screen.blit(value_text, value_rect)
            
            # Draw label below
            label_text = self.font_small.render(label, True, COLORS['text'])
            label_rect = label_text.get_rect(center=(bar_x + bar_width//2, y + max_height + 10))
            self.screen.blit(label_text, label_rect)

class StartupScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.tribe_name = ""
        self.input_active = True
        self.cursor_timer = 0
        
        # Input box
        self.input_box = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2, 300, 40)
        self.start_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 80, 200, 50)
        self.button_hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    if self.tribe_name.strip():
                        return 'start'
                elif event.key == pygame.K_BACKSPACE:
                    self.tribe_name = self.tribe_name[:-1]
                else:
                    if len(self.tribe_name) < 20:  # Limit name length
                        self.tribe_name += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.collidepoint(event.pos):
                if self.tribe_name.strip():
                    return 'start'
        
        elif event.type == pygame.MOUSEMOTION:
            self.button_hovered = self.start_button.collidepoint(event.pos)
        
        return None
    
    def update(self):
        self.cursor_timer += 1
    
    def draw(self):
        self.screen.fill(COLORS['background'])
        
        # Title
        title = self.font_large.render("Hunter-Gatherer Tribe Simulation", True, COLORS['text'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)
        
        # Instructions
        instruction = self.font_medium.render("Enter your tribe name:", True, COLORS['text'])
        instruction_rect = instruction.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(instruction, instruction_rect)
        
        # Input box
        pygame.draw.rect(self.screen, COLORS['panel_bg'], self.input_box)
        pygame.draw.rect(self.screen, COLORS['boundary'], self.input_box, 2)
        
        # Text in input box
        text_surface = self.font_medium.render(self.tribe_name, True, COLORS['text'])
        self.screen.blit(text_surface, (self.input_box.x + 10, self.input_box.y + 8))
        
        # Cursor
        if self.input_active and (self.cursor_timer // 30) % 2:
            cursor_x = self.input_box.x + 10 + text_surface.get_width()
            pygame.draw.line(self.screen, COLORS['text'], 
                           (cursor_x, self.input_box.y + 5), 
                           (cursor_x, self.input_box.y + 35), 2)
        
        # Start button
        button_color = COLORS['button_hover'] if self.button_hovered else COLORS['button']
        pygame.draw.rect(self.screen, button_color, self.start_button)
        pygame.draw.rect(self.screen, COLORS['boundary'], self.start_button, 2)
        
        start_text = self.font_medium.render("Start Simulation", True, COLORS['text'])
        start_rect = start_text.get_rect(center=self.start_button.center)
        self.screen.blit(start_text, start_rect)
        
        # Instructions at bottom
        controls = [
            "Controls:",
            "SPACE - Pause/Resume",
            "N - Next Generation",
            "R - Reset Simulation",
            "ESC - Quit"
        ]
        
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, COLORS['text'])
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120 + i * 20))
            self.screen.blit(text, text_rect)

class IntroScreen:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.blink_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return 'continue'
        return None
    
    def update(self):
        self.blink_timer += 1
    
    def draw(self):
        # Try to draw intro image, fallback to text
        intro_image = self.asset_manager.get_image('intro')
        if intro_image:
            self.screen.blit(intro_image, (0, 0))
            
            # Add blinking "Press Enter" text over the image
            if (self.blink_timer // 30) % 2:  # Blink every 30 frames
                enter_text = self.font_medium.render("Press ENTER to continue", True, COLORS['text'])
                enter_rect = enter_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
                
                # Add background for better visibility
                bg_rect = pygame.Rect(enter_rect.x - 10, enter_rect.y - 5, enter_rect.width + 20, enter_rect.height + 10)
                pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
                
                self.screen.blit(enter_text, enter_rect)
        else:
            # Fallback to simple text screen
            self.screen.fill(COLORS['background'])
            
            # Title
            title = self.font_large.render("Hunter-Gatherer Tribe Simulation", True, COLORS['text'])
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
            self.screen.blit(title, title_rect)
            
            # Subtitle
            subtitle = self.font_medium.render("Genetic Algorithm Evolution Demo", True, COLORS['text'])
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(subtitle, subtitle_rect)
            
            # Blinking enter prompt
            if (self.blink_timer // 30) % 2:
                enter_text = self.font_medium.render("Press ENTER to continue", True, COLORS['gatherer_high'])
                enter_rect = enter_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
                self.screen.blit(enter_text, enter_rect)