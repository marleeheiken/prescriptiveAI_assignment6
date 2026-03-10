# Week 2: Staffing and Assignment Optimization Implementation Steps

Welcome to Week 2! This week you'll add intelligent staffing decisions and optimal order assignment to your existing layout optimization. By integrating all three optimization areas, you'll create a comprehensive warehouse management system that should reach $20,000+ profit.

## Learning Objectives
By the end of this week, you will:
- Implement economic models for workforce management decisions
- Use assignment algorithms for optimal worker-to-order matching
- Integrate multiple optimization areas for maximum profit
- Balance competing factors like distance, value, and urgency

## Background Reading
Start by reading these sections in your provided guides:
1. **UNIT_INTRO_TO_OPTIMIZATION.md** - Sections "Decision Domain 1: Economic Staffing Optimization" and "Decision Domain 2: Assignment Problem Optimization" 
2. **DEBUGGING_AND_PERFORMANCE_GUIDE.md** - Section "Performance Diagnosis Toolkit" for testing your implementations

---

## Step 1: Environment Setup and Week 1 Validation

### 1.1 Verify Your Week 1 Implementation
Before adding new optimization areas, ensure your layout optimization from Week 1 is working:

```bash
# Test your Week 1 layout optimization
python main.py --agent skeleton_optimization --episodes 3

# You should see profit in the $8K-12K range with strategic layout swaps
```

If your Week 1 implementation isn't working well, fix it before proceeding. Week 2 builds on Week 1's foundation.

### 1.2 Understand Current Performance Gaps
Navigate to line 83 in `skeleton_rl_agent.py` and examine the `_get_naive_staffing_action()` method, then line 134 for `_get_naive_order_assignments()`.

**Current Problems:**
- **Staffing:** Random hiring/firing ignoring basic business economics
- **Assignment:** Random order-to-worker matching ignoring efficiency
- **No Integration:** Each decision area operates independently

**Your Goal:** Add intelligent economic staffing and optimal assignment while maintaining your layout optimization improvements.

---

## Step 2: Implement Economic Staffing Optimization (Week 2 Step 1)

### 2.1 Study the Algorithm: Economic Decision Making for Workforce Management

**Algorithm Type:** Economic Optimization with Capacity Planning

**Core Concept:** This implements workforce sizing decisions based on simple business economics. Think of it like balancing your personal budget - you only spend money (hire workers) when you'll make more money back (from completing additional orders). Each hiring decision compares the cost of paying a worker's salary against the extra revenue that worker can generate.

**Algorithmic Framework:**
```
ECONOMIC-STAFFING-OPTIMIZATION():
1. Analyze current demand (how many orders are waiting)
2. Calculate workforce utilization and efficiency
3. For each potential action (hire, fire, do nothing):
   a. Estimate benefit (additional orders completed/revenue)
   b. Calculate cost (salary expenses)
   c. Consider business constraints (current profit, trends)
4. Select action with highest net benefit
5. Use buffer zones to prevent rapid hire/fire cycles
```

**Key Insight:** Hiring a worker costs $0.30 per timestep but can generate much more revenue if there are orders waiting. The algorithm finds the optimal workforce size where the cost of hiring equals the benefit from additional capacity.

### 2.2 Navigate to Staffing Method
Go to the `_get_naive_staffing_action()` method (line 83) in `skeleton_rl_agent.py`.

### 2.3 Replace with Economic Algorithm
Replace the entire method with this framework:

```python
def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
    """
    WEEK 2 STEP 1: Economic staffing optimization
    Make hiring/firing decisions based on simple business economics
    """
    
    # Extract economic and operational data
    current_profit = financial_state[0]
    revenue = financial_state[1]
    costs = financial_state[2]
    burn_rate = financial_state[3]
    
    num_employees = np.sum(employee_info[:, 0] > 0)
    queue_length = len(self.env.order_queue.orders)
    has_manager = np.any(employee_info[:, 5] == 1)
    
    # TODO: Calculate business indicators
    # TODO: - Queue pressure (how much demand vs how much capacity)
    # TODO: - Profit per employee (how efficient is our workforce)
    # TODO: - Recent profit trend (is business growing or shrinking?)
    
    # TODO: Apply economic decision logic
    # TODO: - HIRE when: high demand + profitable + can afford wages
    # TODO: - FIRE when: low demand + losing money + too many workers
    # TODO: - HIRE MANAGER when: profitable + need layout optimization + no manager
    
    # TODO: Implement buffer zones (different thresholds for hire vs fire)
    # TODO: Use higher threshold for hiring, lower threshold for firing
    
    return 0  # Placeholder - implement economic logic
```

### 2.4 Implementation Details: Economic Decision Parameters

**Algorithm Parameters to Implement:**
- **Queue Pressure Threshold:** Hire when queue > employees × 3.0, fire when queue < employees × 1.5
- **Profit Threshold:** Only hire when profit > $1000 (can afford wages)
- **Manager Threshold:** Hire manager when profit > $2000 and no manager exists
- **Minimum Staff:** Never fire below 2 employees (maintain baseline capacity)

Fill in each TODO section using economic analysis:

**Business Indicators Calculation:**
```python
# TODO: Calculate queue pressure (demand vs capacity)
# HINT: queue_pressure = queue_length / max(1, num_employees)

# TODO: Calculate profit efficiency  
# HINT: profit_per_employee = current_profit / max(1, num_employees)

# TODO: Track profit trend (if you have history)
# HINT: Compare recent profit to older profit levels
```

**Economic Decision Logic:**
```python
# TODO: HIRING LOGIC - when does hiring make business sense?
# TODO: Check: queue pressure > hire_threshold AND current_profit > profit_threshold
# TODO: Manager hiring: profit > manager_threshold AND not has_manager

# TODO: FIRING LOGIC - when does firing save money without hurting capacity?  
# TODO: Check: queue pressure < fire_threshold AND num_employees > min_staff
# TODO: Extra consideration: only fire if losing money or severe overstaffing
```

**Buffer Zone Implementation:**
```python
# TODO: Use different thresholds for hiring vs firing decisions
# TODO: This prevents flip-flopping between hiring and firing every few steps
# HINT: hire_threshold = 3.0, fire_threshold = 1.5 creates buffer zone
```

### 2.5 Test Your Economic Staffing
Run your agent and observe staffing decisions:

```bash
python main.py --agent skeleton_optimization --episodes 3
```

**Expected Results:** You should see strategic hiring when queues build up and firing when overstaffed. No more random staffing decisions.

**Debugging Reference:** If you encounter issues, consult the debugging guide section on common implementation problems.

---

## Step 3: Implement Order Assignment Optimization (Week 2 Step 2)

### 3.1 Study the Algorithm: Worker-to-Order Matching Problem

**Algorithm Type:** Worker-to-Order Matching with Multiple Factor Optimization

**Core Concept:** This solves the classic problem of matching workers to orders optimally. Think of it like assigning the best players to the most important positions on a sports team. The algorithm considers multiple factors (how far workers have to walk, how valuable orders are, how urgent they are) to find assignments that work best overall.

**Algorithmic Framework:**
```
WORKER-TO-ORDER-MATCHING():
1. Identify available workers (idle, not managers)
2. Identify pending orders (up to action space limit)
3. For each worker-order pair:
   a. Calculate distance cost (how far worker must walk to items)
   b. Calculate value benefit (how much money this order is worth)
   c. Calculate urgency factor (how soon order must be completed)
   d. Compute combined assignment score
4. Apply assignment algorithm (choose best matches)
5. Return optimal worker-order assignments
```

**Key Insight:** A $200 order assigned to a worker 2 steps away is better than a $50 order assigned to a worker 1 step away. The algorithm balances walking efficiency with revenue maximization, like choosing between a nearby cheap restaurant and a farther expensive one.

### 3.2 Navigate to Assignment Method
Go to the `_get_naive_order_assignments()` method (line 134) in `skeleton_rl_agent.py`.

### 3.3 Replace with Assignment Algorithm
Replace the entire method with this framework:

```python
def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
    """
    WEEK 2 STEP 2: Worker-to-order matching optimization
    Optimally match idle workers to pending orders
    """
    
    assignments = [0] * 20  # Initialize with no assignments
    
    # TODO: Find idle workers (not managers, currently available)
    # HINT: Check employee_info for active workers with idle state
    
    # TODO: Get pending orders (limit to action space size)
    # HINT: Use self.env.order_queue.orders[:20]
    
    # TODO: If no workers or orders available, return empty assignments
    
    # TODO: Calculate assignment scores for all worker-order pairs
    # TODO: For each worker-order combination:
    # TODO: - Calculate distance to order items
    # TODO: - Calculate order value benefit  
    # TODO: - Compute combined assignment score
    
    # TODO: Apply assignment algorithm (choose best matches)
    # TODO: Ensure each worker and order assigned at most once
    
    return assignments
```

### 3.4 Implementation Details: Assignment Algorithm Components

**Assignment Parameters:**
- **Distance Weight:** 70% (efficiency matters most)
- **Value Weight:** 30% (revenue is important but secondary)
- **Maximum Distance:** Grid width + height (for normalization)
- **Assignment Method:** Greedy (good performance, simpler than optimal)

**Worker Identification:**
```python
# TODO: Find available workers
# TODO: Check: employee active AND employee idle AND not manager
# HINT: Use employee_info array columns for status information
```

**Assignment Score Calculation:**
```python
# TODO: For each worker-order pair, calculate:
# TODO: 1. Distance score = 1 / (1 + min_distance_to_items)
# TODO: 2. Value score = order_value / max_order_value  
# TODO: 3. Combined score = distance_weight × distance_score + value_weight × value_score
# HINT: Higher score = better assignment
```

**Greedy Assignment Algorithm:**
```python
# TODO: Sort all worker-order pairs by assignment score (highest first)
# TODO: Choose best available combinations one at a time
# TODO: Track assigned workers and orders to avoid double-assignment
# HINT: Use sets to track what's already assigned
```

### 3.5 Implement Assignment Helper Methods
Add these helper methods to support your assignment algorithm:

```python
def _calculate_order_distance(self, worker_pos, order):
    """
    Calculate minimum distance from worker to any item needed for this order.
    
    Algorithm: Find closest item location for each item type in order,
    return minimum distance across all required items.
    """
    min_distance = float('inf')
    
    # TODO: For each item type in order.items:
    # TODO: - Find item locations using grid.find_item_locations()
    # TODO: - Calculate distance from worker_pos to each location
    # TODO: - Track minimum distance found
    
    return min_distance if min_distance != float('inf') else 0

def _get_idle_workers(self, employee_info):
    """
    Identify workers available for order assignment.
    
    Returns list of (worker_index, worker_position) for available workers.
    """
    idle_workers = []
    
    # TODO: Loop through employee_info array
    # TODO: Check if employee is active, idle, and not a manager
    # TODO: Extract position and add to idle_workers list
    # HINT: employee_info format: [x, y, state, has_order, items_collected, is_manager]
    
    return idle_workers
```

### 3.6 Test Your Assignment Optimization
Run extended tests to see assignment optimization working:

```bash
python main.py --agent skeleton_optimization --episodes 5
```

You should see your agent making strategic worker assignments that consider both distance and order value, not random assignments.

---

## Step 4: Integration Testing and Performance Analysis

### 4.1 Add Integrated Performance Tracking
Add this method to track how well your integrated optimization is working:

```python
def track_integrated_performance(self):
    """
    Performance analysis for integrated optimization system.
    
    Measures:
    - Economic efficiency (profit per employee)
    - Assignment quality (distance vs value optimization)
    - Layout effectiveness (from Week 1)
    - Overall system performance
    """
    if not hasattr(self, 'integrated_metrics'):
        self.integrated_metrics = []
    
    # Calculate comprehensive performance metrics
    current_profit = self.env.cumulative_profit
    num_employees = len(self.env.employees)
    queue_length = len(self.env.order_queue.orders)
    
    # TODO: Calculate economic efficiency metrics
    # TODO: Calculate assignment quality metrics  
    # TODO: Calculate layout efficiency (from Week 1)
    # TODO: Track optimization decisions made
    
    self.integrated_metrics.append({
        'timestep': self.env.current_timestep,
        'profit_per_employee': current_profit / max(1, num_employees),
        'queue_pressure': queue_length / max(1, num_employees),
        'total_decisions': len([a for a in self.action_history if any(a.values())]),
        'layout_efficiency': self._calculate_layout_efficiency()  # From Week 1
    })
    
    # Print integrated progress every 1000 steps
    if self.env.current_timestep % 1000 == 0:
        recent_metrics = self.integrated_metrics[-10:]
        avg_profit_per_emp = np.mean([m['profit_per_employee'] for m in recent_metrics])
        avg_queue_pressure = np.mean([m['queue_pressure'] for m in recent_metrics])
        print(f"Integrated Performance: ${avg_profit_per_emp:.0f}/employee, Queue pressure: {avg_queue_pressure:.2f}")
```

### 4.2 Integration Testing in get_action
Modify your `get_action` method to coordinate all three optimization areas:

```python
def get_action(self, observation: Dict) -> Dict:
    """
    Week 2: Integrated optimization across all decision areas
    """
    current_timestep = observation['time'][0]
    financial_state = observation['financial']
    queue_info = observation['order_queue']
    employee_info = observation['employees']
    
    action = {
        'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),      # Week 2 Step 1
        'layout_swap': self._get_naive_layout_action(current_timestep),                         # Week 1 (keep working)
        'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)       # Week 2 Step 2
    }
    
    # Track integrated performance every 100 steps
    if current_timestep % 100 == 0:
        self.track_integrated_performance()
    
    # TODO: Record action for optimization analysis
    self.action_history.append(action.copy())
    
    return action
```

### 4.3 Run Comprehensive Integration Tests

Test your complete Week 2 implementation:

```bash
# Test integrated system performance
python main.py --agent skeleton_optimization --episodes 10

# Compare with baseline agents to measure improvement
python main.py --compare agents skeleton_optimization,greedy_std,intelligent_hiring --episodes 5
```

**Expected Results:**
- **Profit should reach $15,000-22,000** (up from $8K-12K in Week 1)
- **Strategic staffing decisions** based on queue pressure and profitability
- **Intelligent worker assignments** considering distance and order value
- **Continued layout optimization** from Week 1

---

## Step 5: Week 2 Validation and Documentation

### 5.1 Performance Validation
Your Week 2 implementation should achieve:
- **Target Profit:** $15,000 - $22,000 (up from Week 1's $8K-12K)
- **Integrated Behavior:** Clear evidence of coordinated optimization across all three areas
- **Economic Efficiency:** Profit per employee should improve significantly
- **Assignment Quality:** Orders assigned to nearby workers, high-value orders prioritized

### 5.2 Debugging Common Issues

**If economic staffing isn't working:**
- Verify you're calculating queue pressure correctly
- Check that profit thresholds are realistic for the environment
- Ensure buffer zones prevent rapid hire/fire cycles

**If assignment optimization isn't working:**
- Verify distance calculations use Manhattan distance correctly
- Check that you're identifying idle workers properly
- Ensure assignment scores combine distance and value appropriately

**If integration is causing problems:**
- Test each optimization area individually
- Verify that layout optimization from Week 1 still works
- Check that decisions from different areas don't conflict

### 5.3 Code Review Checklist
Before finishing Week 2, verify:

□ Economic staffing uses queue pressure and profit analysis  
□ Assignment algorithm considers both distance and order value  
□ Layout optimization from Week 1 continues to work  
□ Performance tracking shows improvement across all metrics  
□ No crashes or errors during extended runs  
□ Profit consistently reaches $15K+ range  

### 5.4 Prepare for Week 3
Document your Week 2 results:
- Final profit achieved and consistency
- Most effective optimization strategies discovered
- Integration challenges and solutions found

**Next Week Preview:** You'll add advanced optimization techniques to balance profit with service quality and operational consistency. The goal is competing with top-tier agents ($25,000+) while maintaining robust performance.

---

## Advanced Integration Concepts

### 5.5 Understanding Optimization Interdependencies

Week 2 teaches you that warehouse optimization areas are interconnected:

**Staffing ↔ Layout:** More employees make layout optimization more valuable (more people benefit from efficient layout)

**Staffing ↔ Assignment:** Optimal workforce size depends on assignment efficiency (better assignment = fewer workers needed)  

**Layout ↔ Assignment:** Good layout makes distance-based assignment more effective (shorter average distances)

### 5.6 Economic Trade-offs in Integrated Systems

Your Week 2 implementation balances multiple business considerations:

**Short-term vs Long-term:** Hiring costs money immediately but generates revenue over time

**Efficiency vs Flexibility:** Optimal assignments maximize current efficiency but may not adapt to changing conditions

**Optimization vs Operations:** Layout swaps improve efficiency but temporarily disrupt operations

### 5.7 Performance Analysis Across Optimization Areas

Track how improvements in each area contribute to overall performance:

```python
def analyze_optimization_contributions(self):
    """
    Understand which optimization areas provide the most value.
    This analysis guides Week 3 advanced optimization techniques.
    """
    
    # TODO: Estimate profit contribution from each optimization area
    # TODO: - Layout optimization: compare efficiency before/after swaps
    # TODO: - Staffing optimization: compare capacity utilization
    # TODO: - Assignment optimization: compare assignment quality metrics
    
    # TODO: Identify which optimizations provide highest return on investment
    # TODO: This will inform Week 3 objective weighting decisions
```

---

## Advanced Optional: Hungarian Algorithm Implementation

**For students who finish early and want to push their assignment optimization further**

The greedy assignment algorithm you implemented works well, but there's an even better approach called the Hungarian algorithm that finds truly optimal assignments. This is completely optional - your greedy algorithm is sufficient for Week 2 success.

### 6.1 Understanding the Hungarian Algorithm

**What it does:** The Hungarian algorithm guarantees finding the assignment that minimizes total cost (or maximizes total benefit) across all worker-order pairs simultaneously.

**Why it's better:** The greedy algorithm picks the best individual assignment each time, but sometimes the globally optimal solution requires making some locally suboptimal choices.

**Example:** 
- Greedy might assign Worker A to Order 1 (best individual match)
- But optimal solution assigns Worker A to Order 2 and Worker B to Order 1 (better overall)

### 6.2 Simplified Hungarian Implementation

**Note:** This is a simplified version that's easier to understand than the full Hungarian algorithm.

```python
def _hungarian_assignment(self, idle_workers, orders):
    """
    Simplified Hungarian-style optimal assignment.
    
    Algorithm: Try all possible assignment combinations and pick the best total.
    Warning: This is computationally expensive for large numbers of workers/orders.
    """
    
    if len(idle_workers) == 0 or len(orders) == 0:
        return [0] * 20
    
    # Limit to small numbers for computational feasibility
    max_assignments = min(len(idle_workers), len(orders), 6)
    workers_subset = idle_workers[:max_assignments]
    orders_subset = orders[:max_assignments]
    
    # TODO: Calculate cost matrix for all worker-order pairs
    # TODO: Use negative scores (since Hungarian minimizes cost, but we want to maximize benefit)
    
    # TODO: Try all possible assignment permutations
    # HINT: Use itertools.permutations to generate all possible assignments
    
    # TODO: Calculate total benefit for each assignment permutation
    # TODO: Select assignment with highest total benefit
    
    # TODO: Convert back to assignment array format
    
    return assignments

def _calculate_assignment_benefit_matrix(self, workers, orders):
    """
    Create matrix of benefits for each worker-order pair.
    Higher values = better assignments.
    """
    benefit_matrix = []
    
    for worker_idx, worker_pos in workers:
        worker_benefits = []
        for order in orders:
            # Calculate same score as greedy algorithm
            distance_score = self._calculate_distance_score(worker_pos, order)
            value_score = self._calculate_value_score(order, orders)
            total_benefit = 0.7 * distance_score + 0.3 * value_score
            worker_benefits.append(total_benefit)
        benefit_matrix.append(worker_benefits)
    
    return benefit_matrix
```

### 6.3 When to Use Hungarian vs Greedy

**Use Greedy when:**
- You have many workers and orders (>10 each)
- You need fast decisions
- "Good enough" solutions are acceptable

**Use Hungarian when:**
- You have few workers and orders (<6 each)
- You need truly optimal assignments
- Computational time isn't critical

### 6.4 Testing Hungarian Implementation

```python
def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
    """
    WEEK 2 STEP 2: Now with optional Hungarian optimization
    """
    assignments = [0] * 20
    
    idle_workers = self._get_idle_workers(employee_info)
    orders = self.env.order_queue.orders[:20]
    
    if not idle_workers or not orders:
        return assignments
    
    # Choose algorithm based on problem size
    if len(idle_workers) <= 5 and len(orders) <= 5:
        # Use Hungarian for small problems
        return self._hungarian_assignment(idle_workers, orders)
    else:
        # Use greedy for larger problems
        return self._greedy_assignment(idle_workers, orders)
```

### 6.5 Expected Performance Improvement

With Hungarian algorithm, you might see:
- **2-5% improvement** in assignment efficiency
- **Slightly higher profit** from better worker utilization
- **More consistent performance** across different scenarios

**Trade-off:** Hungarian is computationally more expensive, so only use it when the problem size is small.

### 6.6 Implementation Challenge

**For Advanced Students:** Try implementing the full Hungarian algorithm using matrix operations. This requires understanding:
- Matrix row/column reduction
- Finding minimum spanning assignments
- Iterative optimization until optimality is reached

**Resources for full implementation:**
- Look up "Hungarian Algorithm tutorial" online
- Check operations research textbooks
- Study matrix-based optimization techniques

**Warning:** Full Hungarian implementation is quite complex and not necessary for Week 2 success. Only attempt this if you've mastered the greedy approach and want an extra challenge.

---

## Course Materials Reference

For additional implementation guidance and debugging support:
- **DEBUGGING_AND_PERFORMANCE_GUIDE.md** - Testing and validation
- **UNIT_INTRO_TO_OPTIMIZATION.md** - Background concepts

Remember: This week focuses on integrating multiple optimization areas into a cohesive system. Understanding how different optimizations interact and reinforce each other is crucial for the advanced optimization techniques in Week 3!