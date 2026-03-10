#!/usr/bin/env python3
"""
Multi-Objective Optimization Demo

Demonstrates Pareto frontier tradeoffs between profit maximization and service quality
in the warehouse environment. Shows clear intersection points and optimization choices.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import warnings
from typing import Dict, List, Tuple
import time

# Optional scipy import for smooth curves
try:
    from scipy.interpolate import make_interp_spline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings("ignore")

from environment.warehouse_env import WarehouseEnv
from agents.multi_objective_agent import create_multi_objective_agents

def run_multi_objective_experiment(episodes: int = 5, episode_length: int = 2000) -> Dict:
    """Run multi-objective optimization experiment"""
    
    print("🎯 Multi-Objective Optimization Demo")
    print("=====================================")
    print(f"Running {episodes} episodes per configuration...")
    print(f"Testing {len(create_multi_objective_agents(None))} different wage levels...")
    print("Objectives: Profit Maximization vs Service Quality")
    print("💰 Wage-based productivity tradeoffs:")
    print("   • Blue points: Low wages, slow workers, low cost")
    print("   • Red points: High wages, fast workers, high cost")  
    print("   • Pareto frontier shows optimal tradeoff curve")
    print()
    
    # Create environment with controlled parameters for clear tradeoffs
    env = WarehouseEnv(
        episode_length=episode_length,
        order_arrival_rate=0.40,  # Moderate pressure to allow strategy differences
        initial_employees=2,      # Start lean
        max_employees=12,         # Limit staffing options
        employee_salary=0.5,      # Medium baseline wage
        grid_width=15,
        grid_height=15,
        num_item_types=30
    )
    
    # Create multi-objective agents
    agents = create_multi_objective_agents(env)
    
    results = {}
    
    for agent_name, agent in agents.items():
        print(f"Testing {agent_name}...", end='', flush=True)
        
        episode_results = []
        
        for episode in range(episodes):
            obs, _ = env.reset()
            agent.reset()
            
            episode_profit = 0
            episode_service_metrics = []
            timestep = 0
            
            while timestep < episode_length:
                action = agent.get_action(obs)
                obs, reward, terminated, truncated, info = env.step(action)
                
                # Track metrics every 100 timesteps for stability
                if timestep % 100 == 0:
                    current_profit = info.get('profit', 0)
                    completion_rate = info.get('completion_rate', 0)
                    episode_service_metrics.append(completion_rate)
                
                timestep += 1
                
                if terminated or truncated:
                    break
            
            # Record episode results
            final_profit = info.get('profit', 0)
            avg_service_rate = np.mean(episode_service_metrics) if episode_service_metrics else 0
            
            episode_results.append({
                'profit': final_profit,
                'service_rate': avg_service_rate,
                'completion_rate': info.get('completion_rate', 0),
                'orders_completed': info.get('orders_completed', 0),
                'orders_cancelled': info.get('orders_cancelled', 0)
            })
            
            # Progress indicator
            percent = int(((episode + 1) / episodes) * 100)
            print(f'\r{agent_name}... [{percent}%]', end='', flush=True)
        
        # Calculate statistics
        profits = [r['profit'] for r in episode_results]
        service_rates = [r['service_rate'] for r in episode_results]
        completion_rates = [r['completion_rate'] for r in episode_results]
        
        results[agent_name] = {
            'avg_profit': np.mean(profits),
            'avg_service_rate': np.mean(service_rates),
            'avg_completion_rate': np.mean(completion_rates),
            'profit_std': np.std(profits),
            'service_std': np.std(service_rates),
            'profit_weight': agent.profit_weight,
            'service_weight': agent.service_weight,
            'all_results': episode_results
        }
        
        print(f'\r{agent_name}... Done! ')
        print(f"  Avg Profit: ${results[agent_name]['avg_profit']:.1f}, "
              f"Service Rate: {results[agent_name]['avg_completion_rate']:.1%}")
    
    env.close()
    return results

def plot_pareto_frontier(results: Dict):
    """Create modern wage-strategy scatterplot visualization"""
    
    # Extract data for plotting
    configurations = []
    for agent_name, data in results.items():
        # Extract wage level from agent name (format: "Wage_$0.15")
        wage_level = 0.5  # default
        if 'Wage_' in agent_name:
            try:
                # Remove the $ sign and convert to float
                wage_str = agent_name.split('_')[-1].replace('$', '')
                wage_level = float(wage_str)
            except:
                pass
        
        configurations.append({
            'name': agent_name,
            'profit': data['avg_profit'],
            'service': data['avg_completion_rate'],
            'wage_level': wage_level,
            'profit_std': data['profit_std'],
            'service_std': data['service_std']
        })
    
    # Sort by wage level for better visualization
    configurations.sort(key=lambda x: x['wage_level'])
    
    # Set modern style
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Extract coordinates and wage levels
    profits = [c['profit'] for c in configurations]
    services = [c['service'] for c in configurations]
    wage_levels = [c['wage_level'] for c in configurations]
    
    # Modern color scheme - using viridis-based gradient
    min_wage, max_wage = min(wage_levels), max(wage_levels)
    normalized_wages = [(w - min_wage) / (max_wage - min_wage) for w in wage_levels]
    
    # Create modern scatter plot with gradient colors
    scatter = ax.scatter(services, profits, 
                        c=normalized_wages, 
                        s=120, 
                        alpha=0.85,
                        cmap='plasma',  # Modern, perceptually uniform colormap
                        edgecolors='white', 
                        linewidth=2,
                        zorder=3)
    
    # Add modern colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, aspect=20)
    cbar.set_label('Wage Level ($/timestep)', fontsize=12, fontweight='600', labelpad=15)
    cbar.ax.tick_params(labelsize=10)
    
    # Add subtle error bars
    for config in configurations:
        ax.errorbar(config['service'], config['profit'], 
                   xerr=config['service_std'], yerr=config['profit_std'],
                   color='lightgray', alpha=0.4, capsize=3, capthick=1, 
                   elinewidth=1, zorder=1)
    
    # Calculate and draw Pareto frontier
    pareto_points = []
    configurations_sorted = sorted(configurations, key=lambda x: x['service'])
    
    for config in configurations_sorted:
        is_pareto = True
        for other in configurations:
            if (other['service'] >= config['service'] and other['profit'] >= config['profit'] and
                (other['service'] > config['service'] or other['profit'] > config['profit'])):
                is_pareto = False
                break
        if is_pareto:
            pareto_points.append(config)
    
    # Sort Pareto points by service quality for smooth curve
    pareto_points.sort(key=lambda x: x['service'])
    
    # Draw Pareto frontier with smooth curve
    if len(pareto_points) >= 2:
        pareto_services = np.array([p['service'] for p in pareto_points])
        pareto_profits = np.array([p['profit'] for p in pareto_points])
        
        # Create smooth curve using interpolation if scipy is available and we have enough points
        if SCIPY_AVAILABLE and len(pareto_points) >= 3:
            # Create smooth curve
            x_smooth = np.linspace(pareto_services.min(), pareto_services.max(), 100)
            spl = make_interp_spline(pareto_services, pareto_profits, k=min(3, len(pareto_points)-1))
            y_smooth = spl(x_smooth)
            ax.plot(x_smooth, y_smooth, color='#2E86AB', linewidth=4, alpha=0.9, 
                   label='Pareto Frontier', zorder=4)
        else:
            ax.plot(pareto_services, pareto_profits, color='#2E86AB', linewidth=4, alpha=0.9,
                   label='Pareto Frontier', zorder=4)
        
        # Highlight Pareto points with modern styling
        ax.scatter(pareto_services, pareto_profits, 
                  color='#F18F01', s=200, 
                  edgecolors='white', linewidth=3, 
                  alpha=0.95, zorder=5, marker='D',
                  label='Pareto Optimal Points')
    
    
    # Modern styling
    ax.set_xlabel('Service Quality (Order Completion Rate)', fontsize=14, fontweight='600', labelpad=10)
    ax.set_ylabel('Profit ($)', fontsize=14, fontweight='600', labelpad=10)
    ax.set_title('Multi-Objective Optimization: Wage Strategy Impact\nProfit vs. Service Quality Analysis', 
                fontsize=16, fontweight='700', pad=25, color='#2E3440')
    
    # Clean up grid
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Modern legend with improved styling - moved to top right
    legend = ax.legend(loc='upper right', fontsize=11, frameon=True, 
                      fancybox=True, shadow=True, framealpha=0.95)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('#E5E7EB')
    
    # Expand axis limits to give annotation boxes more room
    ax_xlim = ax.get_xlim()
    ax_ylim = ax.get_ylim()
    x_range = ax_xlim[1] - ax_xlim[0]
    y_range = ax_ylim[1] - ax_ylim[0]
    
    # Expand by 15% on each side
    ax.set_xlim(ax_xlim[0] - 0.15 * x_range, ax_xlim[1] + 0.15 * x_range)
    ax.set_ylim(ax_ylim[0] - 0.15 * y_range, ax_ylim[1] + 0.15 * y_range)
    
    # Add modern annotation boxes with more breathing room
    ax.text(0.05, 0.95, 'Low Wage Strategy\n• Lower costs\n• Reduced productivity\n• Higher service variability', 
            transform=ax.transAxes, fontsize=11, fontweight='500',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#EEF2FF', 
                     edgecolor='#6366F1', alpha=0.9, linewidth=1.5),
            verticalalignment='top')
    
    ax.text(0.95, 0.05, 'High Wage Strategy\n• Higher costs\n• Increased productivity\n• Consistent service quality', 
            transform=ax.transAxes, fontsize=11, fontweight='500',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='#FEF2F2', 
                     edgecolor='#EF4444', alpha=0.9, linewidth=1.5),
            verticalalignment='bottom', horizontalalignment='right')
    
    # Format axes with modern styling
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}'))
    
    # Improve tick styling
    ax.tick_params(axis='both', which='major', labelsize=11, colors='#374151')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E7EB')
    ax.spines['bottom'].set_color('#E5E7EB')
    
    # Add subtle background
    ax.set_facecolor('#FAFAFA')
    
    plt.tight_layout(pad=2.0)
    
    # Save with high quality
    plt.savefig('wage_productivity_scatterplot.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print(f"\n📊 Modern wage-productivity visualization saved as 'wage_productivity_scatterplot.png'")
    
    plt.show()

def print_detailed_results(results: Dict):
    """Print detailed analysis of wage strategy results"""
    
    print("\n" + "="*70)
    print("DETAILED WAGE-PRODUCTIVITY ANALYSIS")
    print("="*70)
    
    # Sort by wage level
    wage_results = []
    for agent_name, data in results.items():
        wage_level = 0.5  # default
        if 'Wage_' in agent_name:
            try:
                # Remove the $ sign and convert to float
                wage_str = agent_name.split('_')[-1].replace('$', '')
                wage_level = float(wage_str)
            except:
                pass
        wage_results.append((agent_name, data, wage_level))
    
    sorted_results = sorted(wage_results, key=lambda x: x[2])
    
    print(f"{'Wage Level':<12} {'Profit':<12} {'Service':<12} {'Efficiency':<15}")
    print("-" * 70)
    
    for agent_name, data, wage_level in sorted_results:
        efficiency = data['avg_profit'] / (wage_level * 1000)  # Profit per wage dollar
        
        print(f"${wage_level:<11.2f} "
              f"${data['avg_profit']:>8.0f} "
              f"{data['avg_completion_rate']:>10.1%} "
              f"{efficiency:>13.1f}")
    
    print("\n" + "="*70)
    print("KEY INSIGHTS:")
    print("="*70)
    
    # Find extreme points
    max_profit_result = max(sorted_results, key=lambda x: x[1]['avg_profit'])
    max_service_result = max(sorted_results, key=lambda x: x[1]['avg_completion_rate'])
    max_efficiency_result = max(sorted_results, key=lambda x: x[1]['avg_profit'] / (x[2] * 1000))
    
    print(f"🏆 Highest Profit: ${max_profit_result[2]:.2f} wage")
    print(f"   Profit: ${max_profit_result[1]['avg_profit']:.0f}, Service: {max_profit_result[1]['avg_completion_rate']:.1%}")
    
    print(f"\n⭐ Best Service: ${max_service_result[2]:.2f} wage")
    print(f"   Profit: ${max_service_result[1]['avg_profit']:.0f}, Service: {max_service_result[1]['avg_completion_rate']:.1%}")
    
    print(f"\n💡 Most Efficient: ${max_efficiency_result[2]:.2f} wage")
    print(f"   Profit: ${max_efficiency_result[1]['avg_profit']:.0f}, Service: {max_efficiency_result[1]['avg_completion_rate']:.1%}")
    efficiency_score = max_efficiency_result[1]['avg_profit'] / (max_efficiency_result[2] * 1000)
    print(f"   Efficiency: {efficiency_score:.1f} profit per wage dollar")
    
    # Calculate wage-productivity relationship
    wages = [x[2] for x in sorted_results]
    profits = [x[1]['avg_profit'] for x in sorted_results]
    services = [x[1]['avg_completion_rate'] for x in sorted_results]
    
    # Find sweet spot (best profit-to-wage ratio)
    import numpy as np
    if len(wages) > 3:
        best_ratio_idx = np.argmax([p/(w*1000) for p, w in zip(profits, wages)])
        sweet_spot = sorted_results[best_ratio_idx]
        print(f"\n🎯 Sweet Spot: ${sweet_spot[2]:.2f} wage level")
        print(f"   Optimal balance of productivity and cost")

def main():
    """Run multi-objective optimization demo"""
    
    print("Starting Multi-Objective Warehouse Optimization Demo...")
    
    # Run experiment with multiple runs for statistical reliability
    results = run_multi_objective_experiment(episodes=5, episode_length=2000)
    
    # Display results
    print_detailed_results(results)
    
    # Create visualization
    plot_pareto_frontier(results)
    
    print("\n✅ Wage-productivity optimization demo completed!")
    print("The scatterplot shows how different wage levels affect performance.")
    print("\nKey takeaways:")
    print("• Blue points (low wages): Cheaper workers but slower service")
    print("• Red points (high wages): Expensive workers but faster service") 
    print("• Gold star shows the optimal wage level for maximum profit")
    print("• Color gradient reveals the wage-productivity relationship")
    print("• There's often a 'sweet spot' where moderate wages maximize efficiency")

if __name__ == "__main__":
    main()