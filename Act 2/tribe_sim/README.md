# Hunter-Gatherer Tribe Simulation: Genetic Algorithm Assignment

A hands-on introduction to genetic algorithms through hunter-gatherer simulation. Students will implement three core GA components while learning to think like an evolutionary algorithm designer.

## Table of Contents
- [Setup Instructions](#setup-instructions)
- [Understanding the Simulation](#understanding-the-simulation)
- [Assignment Overview](#assignment-overview)
- [Assignment 1: Fitness Function](#assignment-1-fitness-function)
- [Assignment 2: Mutation Strategy](#assignment-2-mutation-strategy)
- [Assignment 3: Selection Mechanism](#assignment-3-selection-mechanism)
- [Running and Testing](#running-and-testing)
- [Troubleshooting](#troubleshooting)

---

## Setup Instructions

### 1. Fork and Clone the Repository
```bash
# Fork this repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/applied-ai-4.git
cd applied-ai-4/tribe_sim
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
**Requirements:** Python 3.8+ and pygame>=2.0.0

### 3. Test Your Setup
```bash
python simulation.py
```
You should see a window with moving entities. If it works, you're ready to start!

---

## Understanding the Simulation

### The Environment
Your genetic algorithm controls one tribe of hunter-gatherers competing for survival in a world with:
- **Food sources** that spawn randomly and respawn after being consumed
- **Predators** that actively hunt all tribes
- **Competing tribes** with different hardcoded strategies (fast runners, cautious farmers, etc.)

### Genetic Traits
Each gatherer in your evolving tribe has five genetic traits:
- **Speed** (0.5-3.0): How fast they move
- **Caution** (0-100): How far they flee from predators
- **Search Pattern** (0-1): Random wandering vs systematic exploration
- **Efficiency** (0.5-2.0): How quickly they consume energy
- **Cooperation** (0-1): Probability of cooperating when encountering other tribes

### Simulation Modes
- **Game Mode** (`--game`): Small populations, visually engaging, easy to follow individual gatherers
- **High-Data Mode** (`--high-data`, default): Large populations, less visual detail, better statistical data

**Important:** Use high-data mode for your assignments! While game mode is more fun to watch, high-data mode with 100 gatherers per tribe will show the effectiveness of your genetic algorithm much more clearly. The larger sample size makes evolutionary trends more apparent and statistical differences more meaningful.

---

## Assignment Overview

You'll implement three core genetic algorithm components that work together to evolve successful survival strategies:

1. **Fitness Function** - Define what makes a gatherer "successful"
2. **Mutation Strategy** - Control how traits evolve between generations
3. **Selection Mechanism** - Determine which gatherers reproduce

Each assignment builds conceptual understanding of how genetic algorithms balance exploration vs exploitation, short-term vs long-term rewards, and individual traits vs population dynamics.

---

## Assignment 1: Fitness Function

**File:** `entities.py`, line 173 in the `calculate_fitness()` method

### The Conceptual Challenge
You need to define "success" in a complex environment where multiple objectives compete:
- **Survival** vs **Resource Gathering**: A gatherer that hides but never collects food isn't useful
- **Short-term** vs **Long-term**: Energy spent gathering food now enables longer survival later
- **Individual** vs **Group**: Cooperative behavior might benefit the population but hurt individual fitness

### Available Information for Decision Making
Your fitness function can consider:
- **Performance metrics**: How long they lived, how much food they gathered, current energy level
- **Behavioral traits**: Their genetic values for speed, caution, cooperation, etc.
- **Final state**: Whether they're still alive at generation end

### Design Philosophy Questions
Think deeply about these tradeoffs:

**What matters more: living long or gathering resources?** A gatherer that survives the full 30 seconds but collects no food versus one that collects lots of food but dies early - which contributed more to the tribe's success?

**How do you reward efficiency?** Should a gatherer that collects 10 food in 15 seconds be valued higher than one that collects 8 food in 30 seconds? How do you measure "food per unit time"?

**What about cooperation vs selfishness?** In this simulation, gatherers with high cooperation share resources with other tribes. Is this good for your tribe's evolution or does it waste resources that could benefit your own population?

**How do you handle edge cases?** What if a gatherer dies immediately? What if one lives the full time but with zero energy remaining? Should fitness ever be negative?

### Approaching the Problem
Start by considering what you're optimizing for. Are you trying to:
- Maximize total tribe resources collected?
- Develop robust survivors who can handle any situation?
- Create efficient specialists who excel in specific scenarios?
- Balance multiple objectives equally?

The "right" answer depends on your goals, but the best fitness functions typically reward multiple objectives rather than focusing on just one metric.

### Testing Your Intuition
After implementing your fitness function, run the simulation and watch for several generations. Ask yourself:
- Are the "green" (high fitness) gatherers behaving in ways that seem intelligent?
- Is your tribe's average performance improving over time?
- Are you seeing the behavioral strategies you intended to reward?

---

## Assignment 2: Mutation Strategy

**File:** `genetics.py`, line 46 in the `mutate()` method

### The Conceptual Challenge
Mutation is evolution's way of exploring new possibilities. Too little mutation and your population gets stuck in local optima. Too much mutation and you destroy good solutions faster than you can build them.

### Understanding the Exploration-Exploitation Tradeoff
Think of mutation as controlling how "adventurous" evolution is:
- **Conservative mutation**: Small changes preserve good traits but might miss better solutions
- **Aggressive mutation**: Large changes explore more possibilities but might destroy successful strategies
- **Adaptive mutation**: Different amounts of change for different situations

### Gene-Specific Considerations
Each trait type might need different mutation strategies:

**Speed and Efficiency** are continuous values where small adjustments often make sense. A gatherer with speed 2.1 could benefit from trying 2.0 or 2.2, but jumping to 0.5 or 3.0 might be too extreme.

**Caution** represents a distance threshold. Small changes (75 to 80) might barely affect behavior, while larger changes (75 to 25) could completely change survival strategy.

**Search Pattern** controls exploration behavior. Since it's a 0-1 value, how do you meaningfully mutate it? Should changes be gradual or discrete?

**Cooperation** affects interactions with other tribes. Is this something that should evolve gradually or are there distinct strategies (always cooperate vs never cooperate)?

### Mutation Magnitude Philosophy
Consider these approaches:

**Proportional to current value**: Larger traits get larger mutations. This maintains relative relationships but might be unfair to smaller values.

**Fixed step sizes**: All mutations are similar magnitude. This treats all traits equally but might be too large for some genes, too small for others.

**Gaussian/normal distribution**: Most mutations are small, few are large. This mimics biological mutation but requires choosing appropriate standard deviation.

**Adaptive strategies**: Mutation size changes based on population performance or generation number. Early generations might need more exploration, later generations more fine-tuning.

### Boundary Handling
What happens when mutation pushes a value outside its valid range? Simply clamping to the boundary is easy but might bias evolution toward extreme values. Consider whether out-of-bounds mutations should be:
- Clamped to the boundary
- Reflected back into the valid range
- Rejected and retried
- Allowed to "wrap around"

### Testing Your Strategy
Watch how mutation affects population diversity over time:
- Do you see variety in strategies across the population?
- Are improvements gradual and steady, or chaotic?
- Does the population maintain diversity or converge to identical gatherers?

---

## Assignment 3: Selection Mechanism

**File:** `genetics.py`, line 29 in the `select_survivors()` method

### The Conceptual Challenge
Selection creates the pressure that drives evolution. You're deciding which traits get passed to future generations and which disappear forever. This single decision shapes the entire evolutionary trajectory.

### Selection Pressure Concepts
Think about selection as a tuning dial:

**High Pressure** (few survivors): Evolution moves quickly toward the current best strategy, but may get stuck if that strategy isn't globally optimal. The population becomes homogeneous fast.

**Low Pressure** (many survivors): Evolution explores more possibilities and maintains diversity, but improvements happen slowly. Good and bad traits both persist longer.

**Variable Pressure**: Different amounts of selection pressure at different times or under different conditions.

### Fairness vs Performance
Consider these philosophical questions:

**Should the best always survive?** Elitist selection guarantees the top performers reproduce, but what if they're only good in current conditions? Environmental changes might favor currently "inferior" traits.

**What about lucky vs skilled?** A gatherer might have high fitness due to luck (spawned near food, avoided predators by chance) rather than good genes. How do you distinguish between genetic fitness and environmental luck?

**Is diversity valuable?** A population of identical "optimal" gatherers might dominate current conditions but fail when the environment changes. How do you balance immediate performance with long-term adaptability?

### Selection Strategy Philosophies

**Tournament Selection** creates local competition. Gatherers compete in small groups, and the best from each group survives. This balances performance with diversity - even mediocre gatherers can win if they're in the right tournament.

**Proportional Selection** gives everyone a chance based on their fitness. High-fitness gatherers are more likely to be chosen, but low-fitness gatherers aren't automatically eliminated. This maintains diversity but may slow improvement.

**Rank-Based Selection** focuses on relative performance rather than absolute fitness scores. The gap between 1st and 2nd place matters more than the gap between their actual fitness values. This helps when fitness values vary widely.

**Hybrid Strategies** combine approaches. Maybe guarantee the top 10% survive (elitism) but select the rest randomly or through tournaments. This preserves the best while maintaining exploration.

### Population Dynamics
Consider how your selection method affects the population over time:

**Genetic Bottlenecks**: If you repeatedly select only the best performers, you might accidentally eliminate genetic diversity that could be valuable later.

**Founder Effects**: Early generations with limited data might establish trends that persist even when they're not optimal.

**Environmental Adaptation**: Your selection method should ideally produce populations that can adapt to changing conditions, not just excel in current ones.

### Testing Your Selection
Monitor population statistics over many generations:
- Does average fitness improve consistently?
- Do you maintain variety in strategies and traits?
- Can your population recover from bad generations?
- How quickly does evolution respond to your changes?

---

## Running and Testing

### Basic Usage
```bash
python simulation.py                # High-data mode (recommended for assignments)
python simulation.py --game         # Visual mode (for watching behavior)
```

**For Assignments: Use High-Data Mode!** While game mode is more visually engaging with larger, easier-to-follow gatherers, high-data mode runs 100 gatherers per tribe instead of 5-10. This larger population size makes evolutionary improvements much more statistically significant and visible. You'll see clearer trends and more reliable results from your genetic algorithm implementations.

### Controls
- **SPACE**: Pause/Resume simulation
- **N**: Advance to next generation manually
- **R**: Reset simulation to test different implementations
- **ESC**: Quit

### What to Watch For
**Visual Indicators:**
- Your evolving tribe shows fitness colors: Red (poor) → Yellow (medium) → Green (excellent)
- Other tribes remain white (they don't evolve)
- Watch movement patterns and survival strategies emerging

**Statistical Trends:**
- Average fitness should generally increase over generations
- Best fitness should improve or at least not decline significantly
- Population diversity should be maintained (not all gatherers identical)

**Behavioral Evolution:**
- Early generations: Random, chaotic behavior
- Middle generations: Patterns emerging, some strategies working better
- Late generations: Consistent, optimized behavior for the environment

### Iterative Testing Process
1. **Implement one assignment at a time** - don't try to perfect all three simultaneously
2. **Run multiple trials** - genetic algorithms have random elements, so run several times to see consistent patterns
3. **Compare before and after** - note differences between your implementation and the minimal version
4. **Adjust parameters** - if evolution is too slow/fast, consider tweaking mutation rates or selection pressure
5. **Document observations** - what strategies emerge? How do they compare to the competing tribes?

---

## Troubleshooting

### Common Conceptual Issues

**"My fitness function isn't working"**
- Are you seeing differentiation between gatherers? All identical fitness suggests your function isn't discriminating enough
- Try adding print statements to see the range of fitness values
- Consider whether your function rewards the behavior you actually want

**"Nothing evolves"**
- Check that mutation is actually changing gene values significantly
- Verify selection is choosing different gatherers each generation
- Ensure your fitness function produces meaningfully different scores

**"Evolution is too slow/fast"**
- Too slow: Increase mutation rate, reduce selection pressure
- Too fast: Decrease mutation rate, increase selection pressure
- Remember: 20-50 generations often needed to see significant trends

**"All gatherers become identical"**
- Selection pressure might be too high
- Mutation might be too weak to maintain diversity
- Consider hybrid selection strategies

### Technical Issues
- **Import errors**: Ensure you're in the `tribe_sim` directory and have pygame installed
- **Performance issues**: High-data mode is computationally intensive but necessary for good results
- **Visualization problems**: Try game mode temporarily to debug behavior, then switch back to high-data mode

### Getting the Most from the Assignment
- **Think conceptually first**: Understand what you're trying to achieve before coding
- **Start simple**: Implement basic versions, then add complexity
- **Test incrementally**: Make one change at a time to understand its impact
- **Question your assumptions**: Why did you choose this approach? What alternatives exist?
- **Consider the bigger picture**: How do your three implementations work together?

---

## Submission

### Commit Your Work
```bash
git add .
git commit -m "Completed GA assignments 1-3"
git push
```

### What to Think About
As you work on these assignments, consider:
- How do your implementations reflect different philosophies about evolution and optimization?
- What tradeoffs did you make, and why?
- How might your genetic algorithm perform in different environments?
- What does this teach you about both artificial and biological evolution?

The goal isn't just to make the numbers go up - it's to understand the deep principles behind how populations adapt to challenges over time. 🧬🎮