import pygame
import sys

# Check command line arguments for mode selection
def parse_arguments():
    if "--high-data" in sys.argv:
        return True
    elif "--game" in sys.argv:
        return False
    else:
        # Default to high data mode
        return True

# Window settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
SIMULATION_WIDTH = 900
SIMULATION_HEIGHT = 800
STATS_PANEL_WIDTH = 300
FPS = 60

# Simulation parameters
# High-data mode: Large populations for better genetic algorithm data
HIGH_DATA_MODE = parse_arguments()  # Use CLI flag: --high-data or --game

if HIGH_DATA_MODE:
    # Large populations for statistical significance
    INITIAL_POPULATION = 100  # Evolving tribe
    NINJA_POPULATION = 100
    RUNNER_POPULATION = 100
    FARMER_POPULATION = 100
    PREDATOR_COUNT = 50
    FOOD_COUNT = 300
    
    # Display subset (what gets rendered)
    DISPLAY_POPULATION = 10  # Evolving tribe
    DISPLAY_NINJA = 10
    DISPLAY_RUNNER = 10
    DISPLAY_FARMER = 10
    DISPLAY_PREDATORS = 5
    DISPLAY_FOOD = 30
else:
    # Original game settings
    INITIAL_POPULATION = 5  # Evolving tribe
    NINJA_POPULATION = 5
    RUNNER_POPULATION = 5
    FARMER_POPULATION = 5
    PREDATOR_COUNT = 5
    FOOD_COUNT = 50
    
    # Display everything in game mode
    DISPLAY_POPULATION = INITIAL_POPULATION
    DISPLAY_NINJA = NINJA_POPULATION
    DISPLAY_RUNNER = RUNNER_POPULATION
    DISPLAY_FARMER = FARMER_POPULATION
    DISPLAY_PREDATORS = PREDATOR_COUNT
    DISPLAY_FOOD = FOOD_COUNT

GENERATION_LENGTH = 1800  # frames (30 seconds at 60 FPS)

# Genetic algorithm parameters
SURVIVAL_RATE = 0.05  # Top 5% survive
MUTATION_RATE = 0.1  # 10% chance per gene
MUTATION_STRENGTH = 0.2  # ±20% of current value

# Entity parameters
if HIGH_DATA_MODE:
    # Tiny entities for high population simulation (background data)
    GATHERER_RADIUS = 5   # Very small for lots of agents
    PREDATOR_SIZE = 8     # Very small for lots of predators  
    FOOD_SIZE = 3         # Very small for lots of food
    
    # Display sizes for visual representation (original game sizes)
    DISPLAY_GATHERER_RADIUS = 22  # Half of 45
    DISPLAY_PREDATOR_SIZE = 37    # Half of 75
    DISPLAY_FOOD_SIZE = 18        # Half of 36
else:
    # Original game sizes (used for both simulation and display)
    GATHERER_RADIUS = 22  # Half of 45
    PREDATOR_SIZE = 37    # Half of 75
    FOOD_SIZE = 18        # Half of 36
    
    DISPLAY_GATHERER_RADIUS = GATHERER_RADIUS
    DISPLAY_PREDATOR_SIZE = PREDATOR_SIZE
    DISPLAY_FOOD_SIZE = FOOD_SIZE
GATHERER_START_ENERGY = 100
GATHERER_MAX_ENERGY = 100
ENERGY_DECAY_RATE = 0.1
FOOD_ENERGY_VALUE = 20
FOOD_RESPAWN_TIME = 300  # frames (5 seconds)

# Predator parameters
PREDATOR_SPEED = 2.0
PREDATOR_HUNT_RADIUS = 150
PREDATOR_HUNTING_COOLDOWN = 30  # frames (0.5 seconds at 60 FPS)

# Gene ranges
GENE_RANGES = {
    'speed': (0.5, 3.0),
    'caution': (0, 100),
    'search_pattern': (0, 1),
    'efficiency': (0.5, 2.0),
    'cooperation': (0.0, 1.0)
}

# Colors
COLORS = {
    'background': (173, 216, 230),
    'gatherer_low': (255, 0, 0),     # Red
    'gatherer_mid': (255, 255, 0),   # Yellow
    'gatherer_high': (0, 255, 0),    # Green
    'predator': (255, 0, 0),
    'predator_alert': (255, 100, 100, 50),
    'food': (0, 255, 0),
    'food_glow': (0, 255, 0, 100),
    'boundary': (100, 100, 100),
    'text': (255, 255, 255),
    'panel_bg': (40, 40, 50),
    'button': (70, 70, 80),
    'button_hover': (90, 90, 100),
    'trail': (255, 255, 255, 30)
}

# Food clustering
FOOD_CLUSTER_SIZE = (5, 10)  # min, max food items per cluster
FOOD_CLUSTER_RADIUS = 50

# Spawn balancing
SPAWN_ZONE_CENTER_X = SIMULATION_WIDTH // 2
SPAWN_ZONE_CENTER_Y = SIMULATION_HEIGHT // 2
SPAWN_ZONE_RADIUS = 100  # All tribe members spawn within this radius of center

# Cooperation constants
INTERACTION_RANGE = 30  # pixels
INTERACTION_COOLDOWN = 120  # frames (2 seconds at 60fps)

COOPERATION_REWARD = 15
DEFECTION_REWARD = 25
EXPLOITATION_PENALTY = -10
EXPLOITATION_DEATH_CHANCE = 0.2
MUTUAL_DEFECTION_DEATH_CHANCE = 0.1