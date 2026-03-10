# Debugging and Performance Enhancement Guide

This guide helps you identify, diagnose, and fix common problems when implementing optimization algorithms for your warehouse agent. Whether your agent is crashing, performing poorly, or behaving unpredictably, this guide provides systematic approaches to get back on track.

## Table of Contents
1. [Common Implementation Problems](#common-implementation-problems)
2. [Performance Diagnosis Toolkit](#performance-diagnosis-toolkit)
3. [Testing and Validation Strategies](#testing-and-validation-strategies)
4. [Performance Optimization Techniques](#performance-optimization-techniques)
5. [Statistical Analysis and Interpretation](#statistical-analysis-and-interpretation)
6. [Emergency Fixes for Common Crashes](#emergency-fixes-for-common-crashes)

---

## Common Implementation Problems

### My Agent Is Crashing

**Problem:** Your agent throws errors and stops running.

**Symptoms:** Python exceptions, environment crashes, or simulation stops unexpectedly.

**Common Causes and Solutions:**

#### 1. Data Access Errors
```python
# WRONG: Accessing data without checking if it exists
def get_action(self, observation):
    profit = observation['financial'][0]  # Crashes if financial data is missing
    queue_length = len(self.env.order_queue.orders)  # Crashes if queue is None

# RIGHT: Safe data access with validation
def get_action(self, observation):
    # Always check if data exists before using it
    if 'financial' not in observation or len(observation['financial']) < 4:
        return {'staffing_action': 0, 'layout_swap': [0, 0], 'order_assignments': [0] * 20}
    
    profit = observation['financial'][0]
    
    # Check if environment components exist
    if not hasattr(self.env, 'order_queue') or self.env.order_queue is None:
        return {'staffing_action': 0, 'layout_swap': [0, 0], 'order_assignments': [0] * 20}
    
    queue_length = len(self.env.order_queue.orders)
```

#### 2. Division by Zero Errors
```python
# WRONG: Not protecting against zero values
def calculate_efficiency(self):
    num_employees = len(self.env.employees)
    profit_per_employee = self.env.cumulative_profit / num_employees  # Crashes with 0 employees

# RIGHT: Always protect division operations
def calculate_efficiency(self):
    num_employees = len(self.env.employees)
    profit_per_employee = self.env.cumulative_profit / max(1, num_employees)  # Never divides by zero
```

#### 3. Array Index Errors
```python
# WRONG: Assuming arrays have expected size
def analyze_orders(self):
    orders = self.env.order_queue.orders
    first_order = orders[0]  # Crashes if no orders exist

# RIGHT: Check array sizes before accessing
def analyze_orders(self):
    orders = self.env.order_queue.orders
    if len(orders) == 0:
        return None  # Handle empty case gracefully
    
    first_order = orders[0]  # Safe to access now
```

### My Agent Makes No Decisions

**Problem:** Your agent returns all zeros and never takes any actions.

**Symptoms:** Staffing action always 0, no layout swaps, no order assignments.

**Common Causes and Solutions:**

#### 1. Logic Never Triggers
```python
# WRONG: Conditions that are never met
def _get_staffing_action(self, financial_state, employee_info):
    profit = financial_state[0]
    if profit > 100000:  # This threshold is too high - never reached
        return 1
    return 0

# RIGHT: Realistic conditions based on actual data ranges
def _get_staffing_action(self, financial_state, employee_info):
    profit = financial_state[0]
    queue_length = len(self.env.order_queue.orders)
    num_employees = np.sum(employee_info[:, 0] > 0)
    
    # Use realistic thresholds based on environment scales
    if queue_length > num_employees * 2.0 and profit > 500:  # Achievable conditions
        return 1
    return 0
```

#### 2. Wrong Data Types or Formats
```python
# WRONG: Returning wrong format
def _get_order_assignments(self, queue_info, employee_info):
    return 0  # Should return list of 20 integers, not single integer

# RIGHT: Return correct format
def _get_order_assignments(self, queue_info, employee_info):
    assignments = [0] * 20  # Correct format: list of 20 integers
    # ... your assignment logic here ...
    return assignments
```

### My Agent Performs Worse Than Random

**Problem:** Your optimization agent has lower profit than the skeleton agent.

**Symptoms:** Negative profits, very low completion rates, high variance.

**Diagnosis Steps:**

#### 1. Check Decision Frequency
```python
def track_decisions(self):
    """Add to your agent to track what decisions you're making"""
    if not hasattr(self, 'decision_counter'):
        self.decision_counter = {'hire': 0, 'fire': 0, 'no_action': 0, 'swaps': 0, 'assignments': 0}
    
    # Call this in get_action to track decisions
    action = self.get_action(observation)
    
    if action['staffing_action'] == 1:
        self.decision_counter['hire'] += 1
    elif action['staffing_action'] == 2:
        self.decision_counter['fire'] += 1
    else:
        self.decision_counter['no_action'] += 1
    
    if action['layout_swap'] != [0, 0]:
        self.decision_counter['swaps'] += 1
    
    if any(a > 0 for a in action['order_assignments']):
        self.decision_counter['assignments'] += 1
    
    # Print every 1000 steps to see what you're doing
    if self.env.current_timestep % 1000 == 0:
        print(f"Decisions so far: {self.decision_counter}")
```

#### 2. Check for Over-Optimization
```python
# WRONG: Too aggressive optimization that hurts performance
def _get_staffing_action(self, financial_state, employee_info):
    # Firing too aggressively
    if len(self.env.employees) > 1:
        return 2  # Fire constantly - this will hurt performance

# RIGHT: Balanced approach with reasonable thresholds
def _get_staffing_action(self, financial_state, employee_info):
    queue_length = len(self.env.order_queue.orders)
    num_employees = len(self.env.employees)
    
    # Only hire when clearly needed
    if queue_length > num_employees * 3.0:
        return 1
    # Only fire when clearly overstaffed
    elif queue_length < num_employees * 1.0 and num_employees > 3:
        return 2
    return 0
```

---

## Performance Diagnosis Toolkit

### Real-Time Performance Monitoring

Add these functions to your agent to track performance in real-time:

```python
def __init__(self, env):
    super().__init__(env)
    # Add performance tracking
    self.performance_log = []
    self.last_profit = 0
    
def record_performance_snapshot(self):
    """Call this every 100 timesteps to track progress"""
    current_profit = self.env.cumulative_profit
    profit_delta = current_profit - self.last_profit
    
    snapshot = {
        'timestep': self.env.current_timestep,
        'total_profit': current_profit,
        'profit_delta': profit_delta,
        'queue_length': len(self.env.order_queue.orders),
        'num_employees': len(self.env.employees),
        'completed_orders': self._count_completed_orders(),
        'queue_pressure': len(self.env.order_queue.orders) / max(1, len(self.env.employees))
    }
    
    self.performance_log.append(snapshot)
    self.last_profit = current_profit
    
    # Print progress every 1000 steps
    if self.env.current_timestep % 1000 == 0:
        print(f"Step {self.env.current_timestep}: Profit=${current_profit:.0f}, "
              f"Queue={snapshot['queue_length']}, Employees={snapshot['num_employees']}")

def _count_completed_orders(self):
    """Helper to count how many orders we've completed"""
    # This is an approximation - you might need to track this more carefully
    total_revenue = getattr(self.env, 'total_revenue', 0)
    avg_order_value = 100  # Rough estimate
    return int(total_revenue / avg_order_value)
```

### Performance Comparison Tool

```python
def compare_with_baseline(self):
    """Compare your performance with known baselines"""
    current_profit = self.env.cumulative_profit
    current_timestep = self.env.current_timestep
    
    # Calculate per-timestep profit rate
    profit_rate = current_profit / max(1, current_timestep)
    
    # Known baseline performance (profit per timestep)
    baselines = {
        'skeleton_random': 0.29,      # $2,180 / 7,500 steps
        'greedy_std': 1.33,           # $10,000 / 7,500 steps  
        'intelligent_hiring': 2.02,   # $15,123 / 7,500 steps
        'intelligent_queue': 3.04,    # $22,793 / 7,500 steps
        'aggressive_swap': 3.44,      # $25,834 / 7,500 steps
        'fixed_std': 3.61             # $27,103 / 7,500 steps
    }
    
    print(f"\nPerformance Comparison (Profit per timestep):")
    print(f"Your agent: ${profit_rate:.2f}")
    
    for name, baseline_rate in baselines.items():
        if profit_rate > baseline_rate:
            print(f"✓ BEATING {name}: ${baseline_rate:.2f}")
        else:
            print(f"✗ Behind {name}: ${baseline_rate:.2f}")
    
    # Project final performance
    projected_final = profit_rate * 7500
    print(f"\nProjected final profit: ${projected_final:.0f}")
```

### Decision Quality Analysis

```python
def analyze_decision_quality(self):
    """Analyze whether your decisions are helping or hurting"""
    if len(self.performance_log) < 10:
        return
    
    recent_performance = self.performance_log[-10:]
    
    # Check if profit is trending up or down
    profit_trend = recent_performance[-1]['total_profit'] - recent_performance[0]['total_profit']
    
    # Check queue management
    avg_queue_pressure = sum(p['queue_pressure'] for p in recent_performance) / len(recent_performance)
    
    # Check employee efficiency
    avg_profit_per_employee = sum(p['total_profit'] / max(1, p['num_employees']) 
                                 for p in recent_performance) / len(recent_performance)
    
    print(f"\nDecision Quality Analysis:")
    print(f"Profit trend (last 1000 steps): ${profit_trend:.0f}")
    print(f"Average queue pressure: {avg_queue_pressure:.2f}")
    print(f"Average profit per employee: ${avg_profit_per_employee:.0f}")
    
    # Provide recommendations
    if profit_trend < 0:
        print("⚠️  WARNING: Profit is declining - check your optimization logic")
    
    if avg_queue_pressure > 5.0:
        print("⚠️  WARNING: Queue pressure too high - consider hiring more aggressively")
    elif avg_queue_pressure < 1.0:
        print("⚠️  WARNING: Queue pressure too low - consider firing or finding more orders")
    
    if avg_profit_per_employee < 100:
        print("⚠️  WARNING: Low profit per employee - check efficiency")
```

---

## Testing and Validation Strategies

### Incremental Testing Approach

Test your changes one piece at a time to isolate problems:

```python
# Phase 1: Test ONLY staffing changes
def get_action(self, observation):
    action = {
        'staffing_action': self._get_improved_staffing_action(observation),
        'layout_swap': [0, 0],  # Disable layout changes for testing
        'order_assignments': [0] * 20  # Disable assignment changes for testing
    }
    return action

# Phase 2: Add assignment optimization
def get_action(self, observation):
    action = {
        'staffing_action': self._get_improved_staffing_action(observation),
        'layout_swap': [0, 0],  # Still disabled
        'order_assignments': self._get_improved_assignments(observation)  # Now enabled
    }
    return action

# Phase 3: Add layout optimization
def get_action(self, observation):
    action = {
        'staffing_action': self._get_improved_staffing_action(observation),
        'layout_swap': self._get_improved_layout(observation),  # Now enabled
        'order_assignments': self._get_improved_assignments(observation)
    }
    return action
```

### Quick Validation Tests

```python
def run_quick_test(self):
    """Quick test to see if basic logic is working"""
    # Test with mock data
    mock_observation = {
        'financial': [1000, 2000, 1000, 10],  # [profit, revenue, costs, burn_rate]
        'employees': np.zeros((20, 6)),        # No employees initially
        'order_queue': np.zeros((20, 4)),      # No orders initially  
        'time': [100]
    }
    
    # Test that your methods don't crash
    try:
        action = self.get_action(mock_observation)
        print(f"✓ Basic action generation works: {action}")
        
        # Test individual components
        staffing = self._get_improved_staffing_action(mock_observation['financial'], 
                                                     mock_observation['employees'])
        print(f"✓ Staffing logic works: {staffing}")
        
        assignments = self._get_improved_assignments(mock_observation['order_queue'],
                                                    mock_observation['employees'])
        print(f"✓ Assignment logic works: {len(assignments)} assignments")
        
    except Exception as e:
        print(f"✗ Error in basic logic: {e}")
        import traceback
        traceback.print_exc()
```

### A/B Testing Framework

```python
def run_ab_test(self, episodes=5):
    """Compare your optimization against the skeleton agent"""
    # You'll need to run this manually with different configurations
    print("Run this test by:")
    print("1. Set optimization_enabled = False")
    print("2. Run 5 episodes and record average profit")
    print("3. Set optimization_enabled = True") 
    print("4. Run 5 episodes and record average profit")
    print("5. Compare results")
    
    # Example usage in your get_action method:
    optimization_enabled = True  # Change this for testing
    
    if optimization_enabled:
        return self._get_optimized_action(observation)
    else:
        return self._get_skeleton_action(observation)  # Original logic
```

---

## Performance Optimization Techniques

### Memory and Speed Optimization

```python
def optimize_performance(self):
    """Techniques to make your agent run faster and use less memory"""
    
    # 1. Cache expensive calculations
    if not hasattr(self, '_distance_cache'):
        self._distance_cache = {}
    
    def get_cached_distance(self, pos1, pos2):
        key = (tuple(pos1), tuple(pos2))
        if key not in self._distance_cache:
            distance = self.env.warehouse_grid.manhattan_distance(pos1, pos2)
            self._distance_cache[key] = distance
        return self._distance_cache[key]
    
    # 2. Limit history tracking
    if hasattr(self, 'performance_log') and len(self.performance_log) > 100:
        self.performance_log = self.performance_log[-50:]  # Keep only recent data
    
    # 3. Use numpy operations instead of loops when possible
    def count_active_employees_fast(self, employee_info):
        return np.sum(employee_info[:, 0] > 0)  # Faster than loops
    
    # 4. Avoid recalculating the same values
    def cache_environment_state(self):
        """Calculate common values once per timestep"""
        if not hasattr(self, '_cached_timestep') or self._cached_timestep != self.env.current_timestep:
            self._cached_timestep = self.env.current_timestep
            self._cached_queue_length = len(self.env.order_queue.orders)
            self._cached_num_employees = len(self.env.employees)
            self._cached_profit = self.env.cumulative_profit
        
        return {
            'queue_length': self._cached_queue_length,
            'num_employees': self._cached_num_employees,
            'profit': self._cached_profit
        }
```

### Algorithm Efficiency Improvements

```python
def improve_algorithm_efficiency(self):
    """Make your optimization algorithms more efficient"""
    
    # 1. Early termination in search algorithms
    def find_best_assignment_fast(self, employees, orders):
        best_score = -float('inf')
        best_assignment = None
        
        # Stop searching after finding a "good enough" solution
        good_enough_threshold = 0.8  # 80% of theoretical maximum
        
        for assignment in self._generate_assignments(employees, orders):
            score = self._calculate_assignment_score(assignment)
            if score > best_score:
                best_score = score
                best_assignment = assignment
                
                # Early termination if we find a good solution
                if score >= good_enough_threshold:
                    break
        
        return best_assignment
    
    # 2. Limit search space for layout optimization
    def find_beneficial_swaps_efficient(self):
        # Only consider swaps involving frequently accessed items
        grid = self.env.warehouse_grid
        frequencies = grid.item_access_frequency
        
        # Focus on top 20% of items by frequency
        hot_items = np.argsort(frequencies)[-int(len(frequencies) * 0.2):]
        
        # Only check swaps involving these hot items
        for item in hot_items:
            # ... your swap logic here ...
            pass
    
    # 3. Batch operations when possible
    def batch_distance_calculations(self, positions):
        """Calculate multiple distances at once"""
        distances = []
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                dist = self.env.warehouse_grid.manhattan_distance(pos1, pos2)
                distances.append((i, j, dist))
        return distances
```

---

## Statistical Analysis and Interpretation

### Understanding Your Results

```python
def analyze_statistical_significance(self, your_results, baseline_results):
    """Determine if your improvements are statistically significant"""
    
    # Example results format: [profit1, profit2, profit3, profit4, profit5]
    import numpy as np
    
    your_mean = np.mean(your_results)
    your_std = np.std(your_results)
    baseline_mean = np.mean(baseline_results)
    baseline_std = np.std(baseline_results)
    
    # Calculate confidence intervals (95%)
    n = len(your_results)
    your_ci = 1.96 * your_std / np.sqrt(n)
    baseline_ci = 1.96 * baseline_std / np.sqrt(n)
    
    print(f"Your agent: ${your_mean:.0f} ± ${your_ci:.0f}")
    print(f"Baseline: ${baseline_mean:.0f} ± ${baseline_ci:.0f}")
    
    # Check for statistical significance
    improvement = your_mean - baseline_mean
    combined_ci = your_ci + baseline_ci
    
    if improvement > combined_ci:
        print(f"✓ SIGNIFICANT IMPROVEMENT: ${improvement:.0f}")
    elif improvement > 0:
        print(f"? Possible improvement: ${improvement:.0f} (not statistically significant)")
    else:
        print(f"✗ No improvement: ${improvement:.0f}")
    
    # Calculate effect size
    pooled_std = np.sqrt((your_std**2 + baseline_std**2) / 2)
    effect_size = improvement / pooled_std
    
    if effect_size > 0.8:
        print(f"Effect size: {effect_size:.2f} (Large effect)")
    elif effect_size > 0.5:
        print(f"Effect size: {effect_size:.2f} (Medium effect)")
    elif effect_size > 0.2:
        print(f"Effect size: {effect_size:.2f} (Small effect)")
    else:
        print(f"Effect size: {effect_size:.2f} (Negligible effect)")
```

### Performance Variance Analysis

```python
def analyze_performance_variance(self, results):
    """Understand why your performance varies between episodes"""
    
    profits = [r['final_profit'] for r in results]
    completion_rates = [r['completion_rate'] for r in results]
    
    print(f"Performance Analysis:")
    print(f"Profit - Mean: ${np.mean(profits):.0f}, Std: ${np.std(profits):.0f}")
    print(f"Completion - Mean: {np.mean(completion_rates):.1f}%, Std: {np.std(completion_rates):.1f}%")
    
    # Identify outliers
    profit_mean = np.mean(profits)
    profit_std = np.std(profits)
    
    for i, profit in enumerate(profits):
        if abs(profit - profit_mean) > 2 * profit_std:
            print(f"Episode {i+1}: Outlier profit ${profit:.0f}")
            # You could add more detailed analysis of what went wrong/right
    
    # Check correlation between metrics
    correlation = np.corrcoef(profits, completion_rates)[0, 1]
    print(f"Profit-Completion correlation: {correlation:.3f}")
    
    if correlation > 0.7:
        print("✓ Strong positive correlation - completing more orders = more profit")
    elif correlation < 0.3:
        print("⚠️  Weak correlation - check if you're optimizing the right thing")
```

---

## Emergency Fixes for Common Crashes

### Import Errors

```python
# If you get import errors, add these at the top of your file:
import numpy as np
from typing import Dict, Optional, List
import sys
import os

# If you need to import from environment modules:
try:
    from ..environment.employee import EmployeeState
except ImportError:
    try:
        from environment.employee import EmployeeState  
    except ImportError:
        # Define your own if imports fail
        class EmployeeState:
            IDLE = 0
            MOVING = 1
            PICKING = 2
            DELIVERING = 3
```

### Attribute Errors

```python
# If you get "AttributeError" for environment properties:
def safe_get_attribute(self, obj, attr_name, default=None):
    """Safely get an attribute with a default value"""
    return getattr(obj, attr_name, default)

# Usage:
item_frequencies = self.safe_get_attribute(self.env.warehouse_grid, 'item_access_frequency', np.zeros(50))
```

### Shape Mismatch Errors

```python
# If you get numpy shape errors:
def ensure_correct_shape(self, array, expected_shape):
    """Ensure array has the expected shape"""
    if array.shape != expected_shape:
        print(f"Warning: Array shape {array.shape} doesn't match expected {expected_shape}")
        # Return a default array with correct shape
        return np.zeros(expected_shape)
    return array

# Usage:
employee_info = self.ensure_correct_shape(observation['employees'], (20, 6))
```

### Action Format Errors

```python
def validate_action_format(self, action):
    """Ensure action has correct format before returning"""
    
    # Ensure staffing_action is an integer 0-3
    if 'staffing_action' not in action:
        action['staffing_action'] = 0
    action['staffing_action'] = max(0, min(3, int(action['staffing_action'])))
    
    # Ensure layout_swap is a list of 2 integers
    if 'layout_swap' not in action or len(action['layout_swap']) != 2:
        action['layout_swap'] = [0, 0]
    action['layout_swap'] = [int(action['layout_swap'][0]), int(action['layout_swap'][1])]
    
    # Ensure order_assignments is a list of 20 integers
    if 'order_assignments' not in action or len(action['order_assignments']) != 20:
        action['order_assignments'] = [0] * 20
    action['order_assignments'] = [max(0, min(20, int(a))) for a in action['order_assignments']]
    
    return action

# Use in get_action:
def get_action(self, observation):
    # ... your optimization logic ...
    
    action = {
        'staffing_action': staffing_decision,
        'layout_swap': layout_decision, 
        'order_assignments': assignment_decisions
    }
    
    return self.validate_action_format(action)  # Always validate before returning
```

---

## Final Debugging Checklist

When your agent isn't working, go through this checklist systematically:

### 1. **Basic Functionality**
□ Agent doesn't crash when running  
□ Agent returns valid action format  
□ Agent makes some non-zero decisions  

### 2. **Data Access**
□ Check observation data is accessible  
□ Validate environment attributes exist  
□ Protect against division by zero  
□ Handle empty arrays/lists safely  

### 3. **Logic Validation**
□ Thresholds are realistic for the environment  
□ Conditions actually trigger with real data  
□ Calculations use correct data types  
□ Results are in expected ranges  

### 4. **Performance Validation**
□ Track decisions being made  
□ Monitor profit trends  
□ Compare against baselines  
□ Check for statistical significance  

### 5. **Optimization Quality**
□ Algorithms focus on high-impact decisions  
□ Parameters are tuned appropriately  
□ Search spaces are reasonable  
□ Early termination prevents infinite loops  

Remember: debugging optimization algorithms requires patience and systematic analysis. Start with simple implementations that work reliably, then add complexity gradually while validating each change. Most performance problems come from logical errors rather than algorithmic sophistication, so focus on getting the basics right before implementing advanced techniques.