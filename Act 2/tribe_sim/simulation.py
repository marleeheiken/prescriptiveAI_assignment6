import pygame
import random
import math
import sys
from entities import Gatherer, Predator, Food, NinjaTribe, RunnerTribe, FarmerTribe, InteractionManager
from genetics import GeneticAlgorithm
from ui import UI, StartupScreen, IntroScreen
from assets import AssetManager
from config import *

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Hunter-Gatherer Tribe Simulation")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = 'intro'  # 'intro', 'startup', 'running', 'paused'
        self.tribe_name = ""
        
        # Simulation components
        self.ga = GeneticAlgorithm()
        self.population = []  # Evolving tribe
        self.ninja_tribe = []
        self.runner_tribe = []
        self.farmer_tribe = []
        self.predators = []
        self.food_items = []
        self.interaction_manager = InteractionManager()
        
        # Generation advancement tracking
        self.last_advance_reason = "Time"  # "Time" or "Extinct"
        
        # Tribe comparison tracking
        self.tribe_comparison_history = []
        
        # Assets
        self.asset_manager = AssetManager()
        
        # UI
        self.ui = UI(self.screen)
        self.intro_screen = IntroScreen(self.screen, self.asset_manager)
        self.startup_screen = StartupScreen(self.screen)
        
        # Timing
        self.frame_count = 0
        self.paused = False
        
        # Initialize simulation
        self.reset_simulation()
    
    def reset_simulation(self):
        self.ga.reset()
        self.population = self.ga.create_initial_population()
        self.ninja_tribe = self.create_ninja_tribe()
        self.runner_tribe = self.create_runner_tribe()
        self.farmer_tribe = self.create_farmer_tribe()
        self.predators = self.create_predators()
        self.food_items = self.create_food_clusters()
        self.interaction_manager = InteractionManager()
        self.frame_count = 0
        self.paused = False
    
    def create_ninja_tribe(self):
        tribe = []
        for _ in range(NINJA_POPULATION):
            ninja = NinjaTribe()
            tribe.append(ninja)
        return tribe
    
    def create_runner_tribe(self):
        tribe = []
        for _ in range(RUNNER_POPULATION):
            runner = RunnerTribe()
            tribe.append(runner)
        return tribe
    
    def create_farmer_tribe(self):
        tribe = []
        for _ in range(FARMER_POPULATION):
            farmer = FarmerTribe()
            tribe.append(farmer)
        return tribe
    
    def create_predators(self):
        predators = []
        for _ in range(PREDATOR_COUNT):
            predator = Predator()
            predators.append(predator)
        return predators
    
    def create_food_clusters(self):
        food_items = []
        clusters_needed = FOOD_COUNT // ((FOOD_CLUSTER_SIZE[0] + FOOD_CLUSTER_SIZE[1]) // 2)
        
        for _ in range(clusters_needed):
            # Random cluster center
            cluster_x = random.uniform(FOOD_CLUSTER_RADIUS, SIMULATION_WIDTH - FOOD_CLUSTER_RADIUS)
            cluster_y = random.uniform(FOOD_CLUSTER_RADIUS, SIMULATION_HEIGHT - FOOD_CLUSTER_RADIUS)
            
            # Random number of food items in cluster
            cluster_size = random.randint(*FOOD_CLUSTER_SIZE)
            
            for _ in range(cluster_size):
                # Random position within cluster
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, FOOD_CLUSTER_RADIUS)
                food_x = cluster_x + math.cos(angle) * distance
                food_y = cluster_y + math.sin(angle) * distance
                
                # Keep within bounds
                food_x = max(FOOD_SIZE, min(SIMULATION_WIDTH - FOOD_SIZE, food_x))
                food_y = max(FOOD_SIZE, min(SIMULATION_HEIGHT - FOOD_SIZE, food_y))
                
                food = Food(food_x, food_y)
                food_items.append(food)
        
        # Add remaining food items randomly
        while len(food_items) < FOOD_COUNT:
            food_x = random.uniform(FOOD_SIZE, SIMULATION_WIDTH - FOOD_SIZE)
            food_y = random.uniform(FOOD_SIZE, SIMULATION_HEIGHT - FOOD_SIZE)
            food = Food(food_x, food_y)
            food_items.append(food)
        
        return food_items
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif self.state == 'running':
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_n:
                        self.next_generation()
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == 'running':
                    mouse_pos = pygame.mouse.get_pos()
                    action = self.ui.handle_click(mouse_pos)
                    if action == 'next_generation':
                        self.next_generation()
                    elif action == 'reset':
                        self.reset_simulation()
            
            elif event.type == pygame.MOUSEMOTION:
                if self.state == 'running':
                    self.ui.handle_mouse_hover(pygame.mouse.get_pos())
            
            # Handle intro screen events
            if self.state == 'intro':
                result = self.intro_screen.handle_event(event)
                if result == 'continue':
                    self.state = 'startup'
            
            # Handle startup screen events
            elif self.state == 'startup':
                result = self.startup_screen.handle_event(event)
                if result == 'start':
                    self.tribe_name = self.startup_screen.tribe_name.strip()
                    if self.tribe_name:
                        self.state = 'running'
        
        return True
    
    def update(self):
        if self.state == 'intro':
            self.intro_screen.update()
            return
        elif self.state == 'startup':
            self.startup_screen.update()
            return
        
        if self.state == 'running' and not self.paused:
            self.frame_count += 1
            
            # Update all entities
            available_food = [f for f in self.food_items if f.available]
            
            # Update all tribes
            for gatherer in self.population:
                gatherer.update(self.predators, available_food)
            
            for ninja in self.ninja_tribe:
                ninja.update(self.predators, available_food)
            
            for runner in self.runner_tribe:
                runner.update(self.predators, available_food)
            
            for farmer in self.farmer_tribe:
                farmer.update(self.predators, available_food)
            
            # Update predators - they hunt all tribes
            all_tribes = [self.population, self.ninja_tribe, self.runner_tribe, self.farmer_tribe]
            all_members = []
            for tribe in all_tribes:
                all_members.extend(tribe)
            
            for predator in self.predators:
                predator.update(all_members)
                predator.check_kills(all_tribes)
            
            for food in self.food_items:
                food.update()
            
            # Check food collection for all tribes
            self.check_food_collection()
            
            # Check cooperation interactions
            self.interaction_manager.check_interactions(all_members)
            
            # Auto-advance generation if time is up OR all evolving tribe members are dead
            alive_evolving_members = sum(1 for member in self.population if member.alive)
            if self.frame_count >= GENERATION_LENGTH:
                self.last_advance_reason = "Time"
                self.next_generation()
            elif alive_evolving_members == 0:
                self.last_advance_reason = "Extinct"
                self.next_generation()
    
    def check_food_collection(self):
        # Check food collection for all tribes with sharing mechanism
        all_tribes = [self.population, self.ninja_tribe, self.runner_tribe, self.farmer_tribe]
        
        for food in self.food_items:
            if not food.available:
                continue
            
            # Find all tribe members within collection range of this food
            collectors = []
            for tribe in all_tribes:
                for member in tribe:
                    if not member.alive:
                        continue
                    
                    distance = math.sqrt((member.x - food.x)**2 + (member.y - food.y)**2)
                    if distance < GATHERER_RADIUS + FOOD_SIZE:
                        collectors.append((member, distance, tribe))
            
            # If someone can collect this food
            if collectors:
                if food.collect():
                    # Calculate sharing based on proximity between collectors
                    self.distribute_food_with_sharing(collectors, food)
    
    def distribute_food_with_sharing(self, collectors, food):
        """Distribute food among collectors based on distance-based sharing"""
        if len(collectors) == 1:
            # Only one collector, gets full food
            member, _, _ = collectors[0]
            member.collect_food(food)
            return
        
        # Calculate sharing portions for each collector
        sharing_portions = []
        
        for i, (member_i, _, _) in enumerate(collectors):
            # Start with base portion (everyone gets something)
            portion = 1.0
            
            # Reduce portion based on proximity to other collectors
            for j, (member_j, _, _) in enumerate(collectors):
                if i != j:
                    # Calculate distance between collectors
                    distance = math.sqrt((member_i.x - member_j.x)**2 + (member_i.y - member_j.y)**2)
                    
                    # Exponential falloff: full sharing at 0 distance, no sharing at 100+ distance
                    if distance < 100:
                        sharing_factor = math.exp(-distance / 30)  # e^(-d/30) for smooth falloff
                        portion *= (1 - sharing_factor * 0.5)  # Reduce portion by up to 50% per nearby collector
            
            sharing_portions.append(portion)
        
        # Normalize portions so they sum to 1.0 (conservation of food)
        total_portions = sum(sharing_portions)
        if total_portions > 0:
            sharing_portions = [p / total_portions for p in sharing_portions]
        
        # Distribute fractional food to each collector
        for (member, _, _), portion in zip(collectors, sharing_portions):
            member.collect_fractional_food(food, portion)
    
    def next_generation(self):
        # Record tribe comparison data before resetting
        self.record_tribe_comparison()
        
        # Only the GA tribe evolves, others respawn fresh
        self.population = self.ga.create_next_generation(self.population)
        
        # Respawn competing tribes fresh (no evolution)
        self.ninja_tribe = self.create_ninja_tribe()
        self.runner_tribe = self.create_runner_tribe()
        self.farmer_tribe = self.create_farmer_tribe()
        
        self.frame_count = 0
        
        # Reset predators
        for predator in self.predators:
            predator.x = random.uniform(0, SIMULATION_WIDTH)
            predator.y = random.uniform(0, SIMULATION_HEIGHT)
        
        # Reset food
        for food in self.food_items:
            food.available = True
            food.respawn_timer = 0
    
    def record_tribe_comparison(self):
        """Record performance comparison between all tribes"""
        def get_tribe_stats(tribe, name):
            if not tribe:
                return {'name': name, 'alive': 0, 'avg_fitness': 0, 'best_fitness': 0, 'total_food': 0, 'avg_survival': 0}
            
            alive_count = sum(1 for member in tribe if member.alive)
            total_food = sum(member.food_collected for member in tribe)
            avg_survival = sum(member.age for member in tribe) / len(tribe)
            
            if hasattr(tribe[0], 'calculate_fitness'):
                fitness_scores = [member.calculate_fitness() for member in tribe]
                avg_fitness = sum(fitness_scores) / len(fitness_scores)
                best_fitness = max(fitness_scores)
            else:
                # For non-GA tribes, use same fitness calculation
                fitness_scores = [(member.age / 100 * 0.5) + (member.food_collected / 10 * 1.0) for member in tribe]
                avg_fitness = sum(fitness_scores) / len(fitness_scores)
                best_fitness = max(fitness_scores)
            
            return {
                'name': name,
                'alive': alive_count,
                'avg_fitness': avg_fitness,
                'best_fitness': best_fitness,
                'total_food': total_food,
                'avg_survival': avg_survival
            }
        
        comparison_data = {
            'generation': self.ga.generation,
            'ga_tribe': get_tribe_stats(self.population, 'GA'),
            'ninja_tribe': get_tribe_stats(self.ninja_tribe, 'Ninja'),
            'runner_tribe': get_tribe_stats(self.runner_tribe, 'Runner'),
            'farmer_tribe': get_tribe_stats(self.farmer_tribe, 'Farmer')
        }
        
        self.tribe_comparison_history.append(comparison_data)
    
    def render(self):
        self.screen.fill(COLORS['background'])
        
        if self.state == 'intro':
            self.intro_screen.draw()
        elif self.state == 'startup':
            self.startup_screen.draw()
        else:
            self.render_simulation()
            cooperation_stats = self.interaction_manager.get_cooperation_stats()
            self.ui.draw_stats_panel(self.tribe_name, self.ga, self.population, self.frame_count, self.last_advance_reason, self.tribe_comparison_history, cooperation_stats)
            
            # Pause indicator
            if self.paused:
                pause_text = self.ui.font_large.render("PAUSED", True, COLORS['text'])
                pause_rect = pause_text.get_rect(center=(SIMULATION_WIDTH // 2, 50))
                self.screen.blit(pause_text, pause_rect)
        
        pygame.display.flip()
    
    def render_simulation(self):
        # Draw simulation boundary
        boundary_rect = pygame.Rect(0, 0, SIMULATION_WIDTH, SIMULATION_HEIGHT)
        pygame.draw.rect(self.screen, COLORS['boundary'], boundary_rect, 2)
        
        # Draw food (subset for display)
        food_to_display = self.food_items[:DISPLAY_FOOD]
        for food in food_to_display:
            if food.available:
                pulse = food.get_pulse_intensity()
                
                # Try to use apple image, fallback to circle
                food_image = self.asset_manager.get_image('food')
                if food_image:
                    # Use original apple image size - no scaling
                    image_rect = food_image.get_rect(center=(int(food.x), int(food.y)))
                    self.screen.blit(food_image, image_rect)
                else:
                    # Fallback to circle
                    color = COLORS['food']
                    pygame.draw.circle(self.screen, color, (int(food.x), int(food.y)), DISPLAY_FOOD_SIZE)
        
        # Draw trails for display subset of tribes
        display_tribes = [
            self.population[:DISPLAY_POPULATION], 
            self.ninja_tribe[:DISPLAY_NINJA], 
            self.runner_tribe[:DISPLAY_RUNNER], 
            self.farmer_tribe[:DISPLAY_FARMER]
        ]
        for tribe in display_tribes:
            for member in tribe:
                if member.alive and len(member.trail) > 1:
                    for i in range(len(member.trail) - 1):
                        alpha = int(255 * (i / len(member.trail)) * 0.3)
                        if alpha > 0:
                            start_pos = member.trail[i]
                            end_pos = member.trail[i + 1]
                            # Create a surface for the alpha line
                            trail_surface = pygame.Surface((SIMULATION_WIDTH, SIMULATION_HEIGHT), pygame.SRCALPHA)
                            pygame.draw.line(trail_surface, (*COLORS['trail'][:3], alpha), start_pos, end_pos, 1)
                            self.screen.blit(trail_surface, (0, 0))
        
        # Draw predators (subset for display)
        predators_to_display = self.predators[:DISPLAY_PREDATORS]
        for predator in predators_to_display:
            # Draw hunt radius if hunting
            if predator.hunting:
                hunt_surface = pygame.Surface((SIMULATION_WIDTH, SIMULATION_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(hunt_surface, COLORS['predator_alert'], 
                                 (int(predator.x), int(predator.y)), PREDATOR_HUNT_RADIUS)
                self.screen.blit(hunt_surface, (0, 0))
            
            # Draw predator
            predator_image = self.asset_manager.get_image('predator')
            if predator_image:
                # Center the image
                image_rect = predator_image.get_rect(center=(int(predator.x), int(predator.y)))
                self.screen.blit(predator_image, image_rect)
            else:
                # Fallback to triangle using display size
                points = [
                    (predator.x, predator.y - DISPLAY_PREDATOR_SIZE),
                    (predator.x - DISPLAY_PREDATOR_SIZE, predator.y + DISPLAY_PREDATOR_SIZE),
                    (predator.x + DISPLAY_PREDATOR_SIZE, predator.y + DISPLAY_PREDATOR_SIZE)
                ]
                pygame.draw.polygon(self.screen, COLORS['predator'], points)
        
        # Draw tribes (display subset only)
        # Draw evolving tribe (with fitness coloring)
        for gatherer in self.population[:DISPLAY_POPULATION]:
            self._draw_tribe_member(gatherer, 'gatherer', use_fitness_color=True)
        
        # Draw competing tribes (no fitness coloring)
        for ninja in self.ninja_tribe[:DISPLAY_NINJA]:
            self._draw_tribe_member(ninja, 'ninja', use_fitness_color=False)
        
        for runner in self.runner_tribe[:DISPLAY_RUNNER]:
            self._draw_tribe_member(runner, 'runner', use_fitness_color=False)
        
        for farmer in self.farmer_tribe[:DISPLAY_FARMER]:
            self._draw_tribe_member(farmer, 'farmer', use_fitness_color=False)
        
        # Interaction effects removed per user request
    
    def _draw_tribe_member(self, member, sprite_name, use_fitness_color=False):
        """Helper method to draw a tribe member with appropriate sprite"""
        # Always get color for death animation, but use fitness color only for evolving tribe
        color = member.get_color()
        if not use_fitness_color and member.alive:
            # Override with white for living non-evolving tribes (but keep death alpha)
            if len(color) == 4:  # Has alpha (dying)
                color = (255, 255, 255, color[3])
            else:  # Alive
                color = (255, 255, 255)
        
        # Try to use tribe-specific image
        member_image = self.asset_manager.get_image(sprite_name)
        if member_image:
            if len(color) == 4:  # RGBA (dying)
                # Create a copy and apply alpha
                dying_image = member_image.copy()
                dying_image.set_alpha(color[3])
                image_rect = dying_image.get_rect(center=(int(member.x), int(member.y)))
                self.screen.blit(dying_image, image_rect)
            else:  # RGB (alive)
                if use_fitness_color:
                    # Get colored version based on fitness for evolving tribe
                    colored_image = self.asset_manager.get_colored_gatherer(color)
                    if colored_image:
                        image_rect = colored_image.get_rect(center=(int(member.x), int(member.y)))
                        self.screen.blit(colored_image, image_rect)
                    else:
                        # Just use the base image
                        image_rect = member_image.get_rect(center=(int(member.x), int(member.y)))
                        self.screen.blit(member_image, image_rect)
                else:
                    # Use the base image without coloring for competing tribes
                    image_rect = member_image.get_rect(center=(int(member.x), int(member.y)))
                    self.screen.blit(member_image, image_rect)
        else:
            # Fallback to circles using display size
            if len(color) == 4:  # RGBA (dying)
                member_surface = pygame.Surface((DISPLAY_GATHERER_RADIUS * 4, DISPLAY_GATHERER_RADIUS * 4), pygame.SRCALPHA)
                pygame.draw.circle(member_surface, color, 
                                 (DISPLAY_GATHERER_RADIUS * 2, DISPLAY_GATHERER_RADIUS * 2), DISPLAY_GATHERER_RADIUS)
                self.screen.blit(member_surface, 
                               (member.x - DISPLAY_GATHERER_RADIUS * 2, member.y - DISPLAY_GATHERER_RADIUS * 2))
            else:  # RGB (alive)
                pygame.draw.circle(self.screen, color, (int(member.x), int(member.y)), DISPLAY_GATHERER_RADIUS)
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Check for help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Hunter-Gatherer Tribe Simulation")
        print("Usage: python simulation.py [OPTIONS]")
        print("")
        print("Options:")
        print("  --high-data    Run with large populations (100 per tribe) for better GA data (default)")
        print("  --game         Run with small populations (original game experience)")
        print("  --help, -h     Show this help message")
        print("")
        print("Examples:")
        print("  python simulation.py --high-data")
        print("  python simulation.py --game")
        sys.exit(0)
    
    simulation = Simulation()
    simulation.run()