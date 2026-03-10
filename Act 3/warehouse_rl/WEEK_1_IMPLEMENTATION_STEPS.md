# Week 1: Layout Optimization Implementation Steps

Welcome to Week 1! This week you'll focus entirely on making your warehouse layout intelligent. Layout optimization has the biggest visual impact and provides compound benefits over time - when you move a popular item closer to delivery, it saves time on every future order containing that item.

## Learning Objectives
By the end of this week, you will:
- Understand how spatial organization affects warehouse efficiency
- Implement frequency-based item placement algorithms
- Use co-occurrence analysis to group related items
- Measure the compound benefits of layout improvements over time

## Background Reading
Start by reading these sections in your provided guides:
1. **UNIT_INTRO_TO_OPTIMIZATION.md** - Section "Decision Domain 3: Spatial Layout Optimization" (lines 116-125)
2. **OPTIMIZATION_STRATEGY_GUIDE.md** - Section "Layout Optimization" (complete section)
3. **DEBUGGING_AND_PERFORMANCE_GUIDE.md** - Section "Performance Diagnosis Toolkit" for testing your implementations

---

## Step 1: Environment Setup and Baseline Testing

### 1.1 Navigate to Your Agent File
Open the file: `agents/skeleton_rl_agent.py`

### 1.2 Run Baseline Test
Before making any changes, establish your baseline performance:

```bash
# Run this command in your terminal from the warehouse_rl directory
python main.py --agent skeleton_optimization --episodes 3

# Record the results - you should see something like:
# skeleton_optimization: $2,180 ± $5,102 profit, 40.0% ± 10.5% completion
```

### 1.3 Understand Current Layout Method
Navigate to line 111 in `skeleton_rl_agent.py` and examine the `_get_naive_layout_action()` method. 

**Current Problems:**
- Makes random swaps every 100 timesteps
- Ignores which items are popular
- Doesn't consider distances to delivery areas
- Wastes expensive manager time on pointless moves

**Your Goal:** Replace this with intelligent layout optimization that moves hot items closer to delivery and groups related items together.

---

## Step 2: Implement Frequency-Based Layout Optimization

### 2.1 Study the Algorithm: Greedy Local Search for Facility Location

**Algorithm Type:** Greedy Local Search with Distance Minimization

**Core Concept:** This is a variant of the facility location problem where you iteratively improve the layout by making locally optimal moves. Each step examines potential swaps and greedily selects the one with highest immediate benefit.

**Algorithmic Framework:**
```
GREEDY-FREQUENCY-OPTIMIZATION():
1. Identify hot items (high access frequency)
2. For each hot item:
   a. Calculate current distance to delivery
   b. If distance > threshold:
      - Search neighborhood for better positions
      - Calculate benefit = frequency × distance_saved
      - If benefit > minimum_improvement:
        * Return best swap
3. Return no_swap if no beneficial moves found
```

**Key Insight:** If an item is accessed 10 times per episode and you move it 3 steps closer to delivery, you save 30 steps of total walking time. The greedy algorithm finds these high-impact improvements first.

### 2.2 Navigate to Layout Method
Go to the `_get_naive_layout_action()` method (line 111) in `skeleton_rl_agent.py`.

### 2.3 Replace with Frequency-Based Algorithm
Replace the entire method with this framework (you'll fill in the details):

```python
def _get_naive_layout_action(self, current_timestep) -> list:
    """
    WEEK 1 STEP 1: Frequency-based layout optimization
    Move frequently accessed items closer to delivery areas
    """
    
    # Only optimize every 100 steps to avoid disrupting operations
    if current_timestep % 100 != 0:
        return [0, 0]
    
    # TODO: Get item frequency data from environment
    # HINT: Use self.env.warehouse_grid.item_access_frequency
    
    # TODO: Identify "hot" items (frequently accessed)
    # HINT: Use np.percentile to find top 25% of items by frequency
    
    # TODO: Find delivery positions
    # HINT: Use getattr(grid, 'truck_bay_positions', [(grid.width//2, grid.height//2)])
    
    # TODO: For each hot item, check if it's far from delivery
    # HINT: Use grid.manhattan_distance() to calculate distances
    
    # TODO: If hot item is >3 steps from delivery, find closer position
    # HINT: Look for empty spots or positions with cold items
    
    # TODO: Return [current_position_index, target_position_index] for beneficial swap
    
    return [0, 0]  # No beneficial swap found
```

### 2.4 Implementation Details: Greedy Search Parameters

**Algorithm Parameters to Implement:**
- **Hot Item Threshold:** Top 25% by access frequency (75th percentile)
- **Distance Threshold:** Only optimize items >3 steps from delivery
- **Minimum Improvement:** Require at least 1 step closer to delivery
- **Search Scope:** Examine all storage positions for better placement

Fill in each TODO section using greedy selection criteria:

**Getting Frequency Data (Objective Function Input):**
```python
# TODO: Access the environment's frequency tracking
# HINT: Use self.env.warehouse_grid.item_access_frequency
# HINT: Check if frequency data exists before proceeding
```

**Identifying Hot Items (Greedy Selection Criteria):**
```python
# TODO: Filter to only items that have been accessed (frequency > 0)
# TODO: Calculate 75th percentile threshold for "hot" items
# HINT: Use np.percentile(active_frequencies, 75)
# TODO: Find all items above this threshold
```

**Greedy Search for Better Positions:**
```python
# TODO: For each hot item, get its current location
# TODO: Calculate distance to nearest delivery point
# TODO: Apply distance threshold (>3 steps) to decide if optimization needed
# TODO: If optimization needed, search for closer positions
# HINT: Call helper method to find best swap position
```

### 2.5 Implement Helper Method: Neighborhood Search
Add this helper method after your main layout method:

```python
def _find_closer_position(self, current_pos, delivery_positions):
    """
    Greedy neighborhood search for better item placement.
    
    Algorithm: Exhaustive search of all storage positions to find
    the position that minimizes distance to delivery points.
    
    Returns [current_index, target_index] if beneficial swap found.
    """
    grid = self.env.warehouse_grid
    current_idx = current_pos[1] * grid.width + current_pos[0]
    current_dist = min(grid.manhattan_distance(current_pos, delivery_pos) 
                      for delivery_pos in delivery_positions)
    
    # TODO: Implement exhaustive neighborhood search
    # TODO: Loop through all grid positions (nested for loops over x,y)
    # TODO: Check if position is a storage cell (grid.cell_types[y, x] == 1)
    # TODO: Calculate distance from candidate position to delivery
    # TODO: Apply greedy selection: choose position with maximum distance improvement
    # TODO: Require minimum improvement threshold (>1 step closer)
    # TODO: Convert 2D coordinates to 1D index for return value
    # HINT: 1D index = y * grid.width + x
    
    return None  # No better position found
```

### 2.6 Test Your Implementation
Run your agent and check for improvements:

```bash
python main.py --agent skeleton_optimization --episodes 3
```

**Expected Results:** You should see some improvement in profit, and the agent should start making layout swaps that move popular items closer to delivery areas.

**Debugging Reference:** If you encounter issues, consult the debugging guide section on common implementation problems.

---

## Step 3: Add Co-occurrence Analysis

### 3.1 Study the Algorithm: Greedy Clustering for Association Mining

**Algorithm Type:** Greedy Clustering with Association-Based Objectives

**Core Concept:** This implements a spatial clustering algorithm that groups items based on their co-occurrence patterns. The greedy approach prioritizes the highest-benefit clustering moves first.

**Algorithmic Framework:**
```
GREEDY-COOCCURRENCE-CLUSTERING():
1. Scan co-occurrence matrix for high-frequency pairs
2. For each high-frequency pair (frequency > threshold):
   a. Calculate current spatial distance
   b. If distance > clustering_threshold:
      - Calculate benefit = frequency × distance
      - Store as candidate clustering move
3. Select highest-benefit clustering move (greedy choice)
4. Execute adjacency swap to cluster items
```

**Key Insight:** If items A and B are ordered together 10 times and are currently 8 steps apart, clustering them adjacent could save 70+ steps of walking time (10 orders × 7 steps saved per order).

### 3.2 Extend Your Layout Method: Two-Phase Optimization
Add co-occurrence analysis to your layout method. This creates a **hierarchical greedy algorithm** where Phase 1 (frequency) has priority over Phase 2 (clustering).

**Algorithm Timing:**
- **Phase 1:** Frequency optimization every 100 timesteps
- **Phase 2:** Co-occurrence optimization every 200 timesteps (less frequent)

```python
# Phase 2: If no frequency-based improvement found, try co-occurrence clustering
if current_timestep % 200 == 0:  # Less frequent than hot-item optimization
    cooccurrence_swap = self._find_cooccurrence_swap()
    if cooccurrence_swap:
        return cooccurrence_swap
```

**Design Rationale:** Frequency optimization addresses immediate efficiency gains, while co-occurrence clustering provides longer-term layout improvements. The different timing ensures hot items get priority.

### 3.3 Implement Co-occurrence Helper: Greedy Benefit Maximization
Add this new helper method:

```python
def _find_cooccurrence_swap(self):
    """
    Greedy clustering algorithm for association-based spatial optimization.
    
    Algorithm: Scan all item pairs for clustering opportunities,
    calculate benefit for each, and greedily select highest-benefit move.
    
    Returns swap that maximizes benefit = co-occurrence_frequency × distance_saved
    """
    grid = self.env.warehouse_grid
    cooccurrence = grid.item_cooccurrence
    
    # Greedy search parameters
    min_cooccurrence = 3      # Minimum frequency threshold
    min_distance = 4          # Minimum distance threshold for clustering
    best_benefit = 0          # Track best benefit found
    best_swap = None          # Track best swap candidate
    
    # TODO: Implement greedy benefit maximization
    # TODO: Scan co-occurrence matrix (nested loops: item1, item2 where item1 < item2)
    # TODO: Apply frequency filter (cooccurrence[item1, item2] > min_cooccurrence)
    # TODO: Get current locations using grid.find_item_locations()
    # TODO: Calculate current distance between items
    # TODO: Apply distance filter (current_distance > min_distance)
    # TODO: Calculate benefit = cooccurrence_count × current_distance
    # TODO: Update best_benefit and best_swap if this benefit is higher
    # TODO: Find adjacency swap for best pair (call helper method)
    
    return best_swap  # Return highest-benefit clustering move
```

**Algorithm Parameters:**
- **Minimum Co-occurrence:** 3 (pairs must be ordered together at least 3 times)
- **Minimum Distance:** 4 (only cluster items that are far apart)  
- **Benefit Function:** frequency × distance (prioritizes high-impact clustering)
- **Selection Criteria:** Greedy maximum benefit selection

### 3.4 Test Co-occurrence Implementation

Run extended tests to see co-occurrence optimization in action:

```bash
python main.py --agent skeleton_optimization --episodes 5
```

You should see your agent making two types of layout decisions:
1. Moving hot items closer to delivery areas
2. Grouping frequently co-ordered items together

---

## Step 4: Performance Analysis and Optimization

### 4.1 Add Performance Tracking: Algorithm Effectiveness Measurement
Add this method to track your greedy algorithm's effectiveness:

```python
def track_layout_performance(self):
    """
    Performance analysis for greedy layout optimization algorithms.
    
    Measures: 
    - Layout efficiency (frequency-weighted distances)
    - Algorithm convergence (swaps per period)
    - Optimization impact over time
    """
    if not hasattr(self, 'layout_metrics'):
        self.layout_metrics = []
    
    # Calculate current layout efficiency using weighted distance metric
    efficiency = self._calculate_layout_efficiency()
    
    self.layout_metrics.append({
        'timestep': self.env.current_timestep,
        'efficiency': efficiency,
        'total_swaps': len([a for a in self.action_history if a['layout_swap'] != [0, 0]]),
        'phase1_swaps': self._count_frequency_swaps(),
        'phase2_swaps': self._count_cooccurrence_swaps()
    })
    
    # Print progress every 1000 steps
    if self.env.current_timestep % 1000 == 0:
        recent_efficiency = np.mean([m['efficiency'] for m in self.layout_metrics[-10:]])
        print(f"Layout efficiency: {recent_efficiency:.3f}")

def _calculate_layout_efficiency(self):
    """
    Objective function evaluation for layout quality.
    
    Algorithm: Weighted average distance where weights = access frequency
    Lower weighted distance = higher efficiency (better layout)
    """
    # TODO: Implement frequency-weighted distance calculation
    # TODO: Get item frequencies and delivery positions
    # TODO: For each item with frequency > 0:
    #       - Get item location
    #       - Calculate distance to nearest delivery
    #       - Weight distance by access frequency
    # TODO: Return normalized efficiency score (0-1 scale)
    # HINT: efficiency = 1.0 - (weighted_avg_distance / max_possible_distance)
    
    return 0.5  # Placeholder - implement the weighted distance calculation
```

### 4.2 Integration Testing
Add performance tracking to your `get_action` method:

```python
def get_action(self, observation: Dict) -> Dict:
    # ... existing code ...
    
    # Track layout performance every 100 steps
    if observation['time'][0] % 100 == 0:
        self.track_layout_performance()
    
    # ... rest of existing code ...
```

### 4.3 Run Comprehensive Tests

Test your complete Week 1 implementation:

```bash
# Run longer episodes to see compound benefits
python main.py --agent skeleton_optimization --episodes 10

# Compare with baseline agents
python main.py --compare agents skeleton_optimization,greedy_std --episodes 5
```

**Expected Results:**
- Profit should improve from ~$2,000 to $8,000-$12,000
- You should see consistent layout swaps that make strategic sense
- Layout efficiency should improve over time

---

## Step 5: Week 1 Validation and Documentation

### 5.1 Performance Validation
Your Week 1 implementation should achieve:
- **Target Profit:** $8,000 - $12,000 (up from ~$2,000)
- **Consistency:** Lower variance than baseline skeleton agent
- **Strategic Behavior:** Clear evidence of hot items moving toward delivery

### 5.2 Debugging Common Issues

**If your agent crashes:** Check the debugging guide section on emergency fixes for common crashes

**If performance doesn't improve:** 
- Verify you're accessing `item_access_frequency` correctly
- Check that your distance calculations are accurate
- Ensure your swap indices are calculated properly (row * width + col)

**If swaps seem random:**
- Add print statements to see what items you're moving and why
- Verify hot item identification is working
- Check that delivery positions are correct

### 5.3 Code Review Checklist
Before finishing Week 1, verify:

□ Layout method only optimizes when queue is manageable  
□ Hot items are correctly identified using frequency data  
□ Distance calculations use Manhattan distance correctly  
□ Swap indices are calculated properly (2D to 1D conversion)  
□ Performance tracking shows improving efficiency over time  
□ No crashes or errors during extended runs  

### 5.4 Prepare for Week 2
Document your Week 1 results:
- Final profit achieved
- Number of layout swaps per episode
- Most effective optimization strategies discovered

**Next Week Preview:** You'll add intelligent staffing and order assignment while keeping your layout optimization improvements. The goal is reaching $20,000+ profit by integrating all three optimization areas.

---

## Course Materials Reference

For additional implementation guidance and debugging support:
- **OPTIMIZATION_STRATEGY_GUIDE.md** - Layout Optimization section
- **DEBUGGING_AND_PERFORMANCE_GUIDE.md** - Testing and validation
- **UNIT_INTRO_TO_OPTIMIZATION.md** - Background concepts

Remember: This week focuses on mastering spatial optimization. Take time to understand why your algorithms work, not just getting them to run. The insights you gain about layout optimization will be crucial for the multi-objective optimization in Week 3!