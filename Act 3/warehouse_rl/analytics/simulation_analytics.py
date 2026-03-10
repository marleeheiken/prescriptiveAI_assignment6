import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any
import seaborn as sns
from matplotlib.widgets import Button

class SimulationAnalytics:
    """Analytics module for post-simulation reporting"""
    
    def __init__(self):
        self.metrics_history = []
        self.swap_history = []
        self.episode_data = []
        
    def record_timestep(self, timestep: int, metrics: Dict[str, Any]):
        """Record metrics for a single timestep"""
        metrics['timestep'] = timestep
        self.metrics_history.append(metrics.copy())
    
    def record_swap(self, timestep: int, swap_info: Dict[str, Any]):
        """Record a layout swap event"""
        swap_info['timestep'] = timestep
        self.swap_history.append(swap_info.copy())
    
    def record_episode_completion(self, episode: int, final_metrics: Dict[str, Any]):
        """Record final episode metrics"""
        final_metrics['episode'] = episode
        self.episode_data.append(final_metrics.copy())
    
    def show_analytics(self, agent_name: str = "Unknown"):
        """Display comprehensive analytics as a clickable gallery"""
        if not self.metrics_history:
            print("No metrics data to display")
            return
        
        # Set up the plot style
        plt.style.use('seaborn-v0_8')
        
        # Create gallery data
        self.gallery_plots = self._create_gallery_plots(agent_name)
        self.current_plot = 0
        
        # Create main figure for gallery
        self.fig = plt.figure(figsize=(16, 12))
        self.fig.suptitle(f'Warehouse Analytics Gallery - {agent_name}', fontsize=18, fontweight='bold')
        
        # Create layout for gallery view
        gs = self.fig.add_gridspec(4, 4, hspace=0.4, wspace=0.3, 
                                  left=0.05, right=0.95, top=0.9, bottom=0.15)
        
        # Show initial gallery view
        self._show_gallery_view(gs)
        
        # Add navigation controls
        self._add_navigation_controls()
        
        plt.show()
        
        print(f"\nAnalytics gallery displayed for {agent_name}")
        print("Click on any thumbnail to view the full chart, or use navigation buttons.")
    
    def _create_gallery_plots(self, agent_name: str):
        """Create individual plot data for gallery"""
        # Extract time series data
        timesteps = [m['timestep'] for m in self.metrics_history]
        profits = [m.get('cumulative_profit', 0) for m in self.metrics_history]
        queue_lengths = [m.get('queue_length', 0) for m in self.metrics_history]
        completion_rates = [m.get('completion_rate', 0) for m in self.metrics_history]
        employee_counts = [m.get('employee_count', 0) for m in self.metrics_history]
        customer_satisfaction = [m.get('customer_satisfaction', 1.0) for m in self.metrics_history]
        time_multipliers = [m.get('time_multiplier', 1.0) for m in self.metrics_history]
        satisfaction_multipliers = [m.get('satisfaction_multiplier', 1.0) for m in self.metrics_history]
        pressure_multipliers = [m.get('pressure_multiplier', 1.0) for m in self.metrics_history]
        effective_arrival_rates = [m.get('effective_arrival_rate', 0.3) for m in self.metrics_history]
        hours_of_day = [m.get('hour_of_day', 0) for m in self.metrics_history]
        
        plots = []
        
        # 1. Cumulative Profit
        plots.append({
            'title': 'Cumulative Profit',
            'type': 'line',
            'data': {'x': timesteps, 'y': profits, 'color': 'green', 'ylabel': 'Profit ($)'}
        })
        
        # 2. Queue vs Performance
        plots.append({
            'title': 'Queue vs Performance',
            'type': 'dual_line',
            'data': {
                'x': timesteps,
                'y1': queue_lengths, 'y1_label': 'Queue Length', 'y1_color': 'red',
                'y2': completion_rates, 'y2_label': 'Completion Rate (%)', 'y2_color': 'blue'
            }
        })
        
        # 3. Employee Count
        plots.append({
            'title': 'Employee Count',
            'type': 'line',
            'data': {'x': timesteps, 'y': employee_counts, 'color': 'purple', 'ylabel': 'Number of Employees'}
        })
        
        # 4. Customer Satisfaction
        plots.append({
            'title': 'Customer Satisfaction',
            'type': 'line_with_refs',
            'data': {
                'x': timesteps, 'y': customer_satisfaction, 'color': 'orange',
                'ylabel': 'Satisfaction Score',
                'ref_lines': [(1.0, 'gray', 'Neutral'), (0.7, 'red', 'Poor'), (1.5, 'green', 'Good')]
            }
        })
        
        # 5. Effective Order Arrival Rate
        plots.append({
            'title': 'Effective Order Arrival Rate',
            'type': 'line_with_refs',
            'data': {
                'x': timesteps, 'y': effective_arrival_rates, 'color': 'teal',
                'ylabel': 'Orders/Timestep',
                'ref_lines': [(0.3, 'gray', 'Base Rate (0.3)')]
            }
        })
        
        # 6. Time of Day Patterns
        plots.append({
            'title': 'Time of Day Patterns',
            'type': 'dual_line',
            'data': {
                'x': timesteps,
                'y1': hours_of_day, 'y1_label': 'Hour of Day', 'y1_color': 'navy',
                'y2': time_multipliers, 'y2_label': 'Time Multiplier', 'y2_color': 'gold'
            }
        })
        
        # 7. Order Generation Multipliers
        plots.append({
            'title': 'Order Generation Multipliers',
            'type': 'multi_line',
            'data': {
                'x': timesteps,
                'lines': [
                    (time_multipliers, 'gold', 'Time of Day'),
                    (satisfaction_multipliers, 'orange', 'Customer Satisfaction'),
                    (pressure_multipliers, 'red', 'Queue Pressure')
                ],
                'ylabel': 'Multiplier Value',
                'ref_lines': [(1.0, 'gray', None)]
            }
        })
        
        # 8. Queue Pressure Analysis
        queue_ratios = [q/max(1, e) for q, e in zip(queue_lengths, employee_counts)]
        plots.append({
            'title': 'Queue Pressure Effects',
            'type': 'dual_line',
            'data': {
                'x': timesteps,
                'y1': queue_ratios, 'y1_label': 'Queue/Employee Ratio', 'y1_color': 'red',
                'y2': pressure_multipliers, 'y2_label': 'Pressure Multiplier', 'y2_color': 'darkred'
            }
        })
        
        # 9. Layout Swaps
        plots.append({
            'title': 'Layout Swaps',
            'type': 'scatter',
            'data': {
                'x': [s['timestep'] for s in self.swap_history] if self.swap_history else [],
                'y': list(range(1, len(self.swap_history) + 1)) if self.swap_history else [],
                'color': 'orange',
                'ylabel': 'Cumulative Swaps'
            }
        })
        
        # 10. Profit Rate Analysis
        if len(profits) > 10:
            window = 20
            profit_rates = []
            rate_timesteps = []
            for i in range(window, len(profits)):
                rate = (profits[i] - profits[i-window]) / window
                profit_rates.append(rate)
                rate_timesteps.append(timesteps[i])
            
            plots.append({
                'title': 'Profit Rate Trend',
                'type': 'line_with_refs',
                'data': {
                    'x': rate_timesteps, 'y': profit_rates, 'color': 'green',
                    'ylabel': 'Profit/Step (20-step avg)',
                    'ref_lines': [(0, 'gray', None)]
                }
            })
        else:
            plots.append({
                'title': 'Profit Rate Trend',
                'type': 'text',
                'data': {'text': 'Insufficient Data'}
            })
        
        # 11. Performance Summary
        if self.episode_data:
            episodes = [ep['episode'] for ep in self.episode_data]
            final_profits = [ep['final_profit'] for ep in self.episode_data]
            plots.append({
                'title': 'Episode Performance',
                'type': 'bar',
                'data': {
                    'x': [str(e) for e in episodes], 'y': final_profits,
                    'color': 'green', 'ylabel': 'Final Profit ($)'
                }
            })
        else:
            if timesteps:
                summary_text = f"""Final Metrics:
Profit: ${profits[-1]:.0f}
Completion: {completion_rates[-1]:.1f}%
Queue: {queue_lengths[-1]} orders
Employees: {employee_counts[-1]}
Satisfaction: {customer_satisfaction[-1]:.2f}"""
                plots.append({
                    'title': 'Final Performance',
                    'type': 'text',
                    'data': {'text': summary_text}
                })
        
        # 12. Efficiency Analysis
        efficiency = [p/max(1, e) for p, e in zip(profits, employee_counts)]
        plots.append({
            'title': 'Profit Efficiency ($/Employee)',
            'type': 'line',
            'data': {'x': timesteps, 'y': efficiency, 'color': 'brown', 'ylabel': 'Profit per Employee'}
        })
        
        return plots
    
    def _show_gallery_view(self, gs):
        """Show thumbnail gallery of all plots"""
        self.gallery_axes = []
        
        # Show up to 12 thumbnails in a 3x4 grid
        for i, plot_data in enumerate(self.gallery_plots[:12]):
            if i >= 12:
                break
            
            row = i // 4
            col = i % 4
            ax = self.fig.add_subplot(gs[row, col])
            
            # Create mini thumbnail plot
            self._create_thumbnail(ax, plot_data, i)
            self.gallery_axes.append(ax)
    
    def _create_thumbnail(self, ax, plot_data, index):
        """Create a thumbnail version of the plot"""
        ax.clear()
        
        # Make plot clickable
        def on_click(event):
            if event.inaxes == ax:
                self._show_detailed_view(index)
        
        ax.figure.canvas.mpl_connect('button_press_event', on_click)
        
        data = plot_data['data']
        plot_type = plot_data['type']
        
        if plot_type == 'line':
            ax.plot(data['x'], data['y'], color=data['color'], linewidth=1)
        elif plot_type == 'dual_line':
            ax.plot(data['x'], data['y1'], color=data['y1_color'], linewidth=1, alpha=0.7)
            ax2 = ax.twinx()
            ax2.plot(data['x'], data['y2'], color=data['y2_color'], linewidth=1, alpha=0.7)
            ax2.set_yticks([])
        elif plot_type == 'multi_line':
            for y_data, color, label in data['lines']:
                ax.plot(data['x'], y_data, color=color, linewidth=1, alpha=0.7)
        elif plot_type == 'line_with_refs':
            ax.plot(data['x'], data['y'], color=data['color'], linewidth=1)
            for ref_val, ref_color, ref_label in data['ref_lines']:
                ax.axhline(y=ref_val, color=ref_color, linestyle='--', alpha=0.5, linewidth=0.5)
        elif plot_type == 'scatter':
            if data['x'] and data['y']:
                ax.scatter(data['x'], data['y'], c=data['color'], s=10, alpha=0.7)
        elif plot_type == 'bar':
            ax.bar(data['x'], data['y'], color=data['color'], alpha=0.7)
        elif plot_type == 'text':
            ax.text(0.5, 0.5, data['text'][:50] + '...' if len(data['text']) > 50 else data['text'],
                   ha='center', va='center', transform=ax.transAxes, fontsize=8)
            ax.axis('off')
        
        ax.set_title(plot_data['title'], fontsize=10, fontweight='bold')
        ax.tick_params(axis='both', which='major', labelsize=6)
        ax.tick_params(axis='both', which='minor', labelsize=6)
        
        # Reduce number of ticks for cleaner thumbnails
        if len(data.get('x', [])) > 10:
            ax.locator_params(nbins=3)
        
        ax.grid(True, alpha=0.2)
        
        # Add hover effect
        ax.patch.set_facecolor('lightblue')
        ax.patch.set_alpha(0.1)
    
    def _show_detailed_view(self, plot_index):
        """Show detailed view of selected plot"""
        self.current_plot = plot_index
        
        # Clear and show single plot
        self.fig.clear()
        
        # Create single large plot
        ax = self.fig.add_subplot(111)
        plot_data = self.gallery_plots[plot_index]
        
        # Create full detailed plot
        self._create_detailed_plot(ax, plot_data)
        
        # Add back button
        self._add_detailed_navigation()
        
        self.fig.canvas.draw()
    
    def _create_detailed_plot(self, ax, plot_data):
        """Create a detailed version of the plot"""
        data = plot_data['data']
        plot_type = plot_data['type']
        
        if plot_type == 'line':
            ax.plot(data['x'], data['y'], color=data['color'], linewidth=2)
            ax.set_ylabel(data['ylabel'])
            ax.set_xlabel('Timestep')
        elif plot_type == 'dual_line':
            line1 = ax.plot(data['x'], data['y1'], color=data['y1_color'], linewidth=2, label=data['y1_label'])
            ax2 = ax.twinx()
            line2 = ax2.plot(data['x'], data['y2'], color=data['y2_color'], linewidth=2, label=data['y2_label'])
            ax.set_ylabel(data['y1_label'], color=data['y1_color'])
            ax2.set_ylabel(data['y2_label'], color=data['y2_color'])
            ax.set_xlabel('Timestep')
        elif plot_type == 'multi_line':
            for y_data, color, label in data['lines']:
                ax.plot(data['x'], y_data, color=color, linewidth=2, label=label)
            ax.set_ylabel(data['ylabel'])
            ax.set_xlabel('Timestep')
            ax.legend()
            for ref_val, ref_color, ref_label in data['ref_lines']:
                ax.axhline(y=ref_val, color=ref_color, linestyle='--', alpha=0.7)
        elif plot_type == 'line_with_refs':
            ax.plot(data['x'], data['y'], color=data['color'], linewidth=2)
            ax.set_ylabel(data['ylabel'])
            ax.set_xlabel('Timestep')
            for ref_val, ref_color, ref_label in data['ref_lines']:
                ax.axhline(y=ref_val, color=ref_color, linestyle='--', alpha=0.7, label=ref_label)
            if any(ref[2] for ref in data['ref_lines']):
                ax.legend()
        elif plot_type == 'scatter':
            if data['x'] and data['y']:
                ax.scatter(data['x'], data['y'], c=data['color'], s=50, alpha=0.7)
                ax.set_ylabel(data['ylabel'])
                ax.set_xlabel('Timestep')
            else:
                ax.text(0.5, 0.5, 'No Layout Swaps', ha='center', va='center', transform=ax.transAxes)
        elif plot_type == 'bar':
            ax.bar(data['x'], data['y'], color=data['color'], alpha=0.7)
            ax.set_ylabel(data['ylabel'])
            ax.set_xlabel('Episode')
        elif plot_type == 'text':
            ax.text(0.05, 0.95, data['text'], transform=ax.transAxes, 
                   fontsize=12, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
            ax.axis('off')
        
        ax.set_title(plot_data['title'], fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _add_navigation_controls(self):
        """Add navigation buttons for gallery"""
        # No buttons needed for gallery view - clicking thumbnails handles navigation
        pass
    
    def _add_detailed_navigation(self):
        """Add navigation controls for detailed view"""
        # Add back to gallery button
        ax_back = plt.axes([0.02, 0.02, 0.1, 0.05])
        self.back_button = Button(ax_back, 'Gallery')
        self.back_button.on_clicked(self._back_to_gallery)
        
        # Add previous/next buttons
        ax_prev = plt.axes([0.14, 0.02, 0.08, 0.05])
        self.prev_button = Button(ax_prev, 'Previous')
        self.prev_button.on_clicked(self._prev_plot)
        
        ax_next = plt.axes([0.24, 0.02, 0.08, 0.05])
        self.next_button = Button(ax_next, 'Next')
        self.next_button.on_clicked(self._next_plot)
    
    def _back_to_gallery(self, event):
        """Return to gallery view"""
        self.fig.clear()
        self.fig.suptitle(f'Warehouse Analytics Gallery', fontsize=18, fontweight='bold')
        gs = self.fig.add_gridspec(4, 4, hspace=0.4, wspace=0.3, 
                                  left=0.05, right=0.95, top=0.9, bottom=0.15)
        self._show_gallery_view(gs)
        self.fig.canvas.draw()
    
    def _prev_plot(self, event):
        """Show previous plot"""
        self.current_plot = (self.current_plot - 1) % len(self.gallery_plots)
        self._show_detailed_view(self.current_plot)
    
    def _next_plot(self, event):
        """Show next plot"""
        self.current_plot = (self.current_plot + 1) % len(self.gallery_plots)
        self._show_detailed_view(self.current_plot)
    
    def clear(self):
        """Clear all recorded data"""
        self.metrics_history.clear()
        self.swap_history.clear()
        self.episode_data.clear()