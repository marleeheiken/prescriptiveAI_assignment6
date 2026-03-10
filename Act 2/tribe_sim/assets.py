import pygame
import os
from config import *

class AssetManager:
    def __init__(self):
        self.images = {}
        self.load_assets()
    
    def load_assets(self):
        """Load all image assets"""
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        # Load and scale images
        try:
            # Food (apple)
            apple_path = os.path.join(assets_dir, 'apple.png')
            if os.path.exists(apple_path):
                apple_img = pygame.image.load(apple_path)
                self.images['food'] = pygame.transform.scale(apple_img, (FOOD_SIZE * 2, FOOD_SIZE * 2))
            else:
                print(f"Warning: apple.png not found at {apple_path}")
                self.images['food'] = None
            
            # Gatherer (friendly)
            friendly_path = os.path.join(assets_dir, 'friendly.png')
            if os.path.exists(friendly_path):
                friendly_img = pygame.image.load(friendly_path)
                self.images['gatherer'] = pygame.transform.scale(friendly_img, (GATHERER_RADIUS * 2, GATHERER_RADIUS * 2))
            else:
                print(f"Warning: friendly.png not found at {friendly_path}")
                self.images['gatherer'] = None
            
            # Predator (jaguar)
            jaguar_path = os.path.join(assets_dir, 'jaguar.png')
            if os.path.exists(jaguar_path):
                jaguar_img = pygame.image.load(jaguar_path)
                self.images['predator'] = pygame.transform.scale(jaguar_img, (PREDATOR_SIZE * 2, PREDATOR_SIZE * 2))
            else:
                print(f"Warning: jaguar.png not found at {jaguar_path}")
                self.images['predator'] = None
            
            # Ninja tribe
            ninja_path = os.path.join(assets_dir, 'ninja.png')
            if os.path.exists(ninja_path):
                ninja_img = pygame.image.load(ninja_path)
                self.images['ninja'] = pygame.transform.scale(ninja_img, (GATHERER_RADIUS * 2, GATHERER_RADIUS * 2))
            else:
                print(f"Warning: ninja.png not found at {ninja_path}")
                self.images['ninja'] = None
            
            # Runner tribe
            runner_path = os.path.join(assets_dir, 'runner.png')
            if os.path.exists(runner_path):
                runner_img = pygame.image.load(runner_path)
                self.images['runner'] = pygame.transform.scale(runner_img, (GATHERER_RADIUS * 2, GATHERER_RADIUS * 2))
            else:
                print(f"Warning: runner.png not found at {runner_path}")
                self.images['runner'] = None
            
            # Farmer tribe
            farmer_path = os.path.join(assets_dir, 'farmer.png')
            if os.path.exists(farmer_path):
                farmer_img = pygame.image.load(farmer_path)
                self.images['farmer'] = pygame.transform.scale(farmer_img, (GATHERER_RADIUS * 2, GATHERER_RADIUS * 2))
            else:
                print(f"Warning: farmer.png not found at {farmer_path}")
                self.images['farmer'] = None
            
            # Intro screen
            intro_path = os.path.join(assets_dir, 'introscreen.png')
            if os.path.exists(intro_path):
                intro_img = pygame.image.load(intro_path)
                # Scale to fit window size
                self.images['intro'] = pygame.transform.scale(intro_img, (WINDOW_WIDTH, WINDOW_HEIGHT))
            else:
                print(f"Warning: introscreen.png not found at {intro_path}")
                self.images['intro'] = None
                
        except pygame.error as e:
            print(f"Error loading assets: {e}")
    
    def get_image(self, name):
        """Get an image by name"""
        return self.images.get(name, None)
    
    def get_colored_gatherer(self, color):
        """Get a gatherer image tinted with the specified color"""
        base_image = self.images.get('gatherer')
        if base_image is None:
            return None
        
        # Create a colored version of the gatherer
        colored_image = base_image.copy()
        
        # Create a color overlay
        overlay = pygame.Surface(colored_image.get_size(), pygame.SRCALPHA)
        overlay.fill((*color, 128))  # Semi-transparent color
        
        # Blend the overlay with the original image
        colored_image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return colored_image