# Quick script to reload modules in Jupyter
import importlib
import sys

# Remove modules from cache
modules_to_reload = ['animated_game', 'agents', 'game_engine']
for module in modules_to_reload:
    if module in sys.modules:
        del sys.modules[module]

print("Modules cleared from cache. Now re-import them:")
print("from agents import *")
print("from game_engine import Game, Tournament") 
print("from animated_game import show_animated_game, show_payoff_matrix")