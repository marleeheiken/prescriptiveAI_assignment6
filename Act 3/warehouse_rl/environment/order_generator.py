import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Order:
    id: int
    items: List[int]
    value: float
    arrival_time: int
    status: str = "pending"  # pending, claimed, delivered
    priority: str = "normal"  # normal, priority, express
    deadline: Optional[int] = None  # Only for express orders
    
    def claim(self) -> bool:
        if self.status == "pending":
            self.status = "claimed"
            return True
        return False
    
    def deliver(self) -> bool:
        if self.status == "claimed":
            self.status = "delivered"
            return True
        return False
    
    def is_expired(self, current_time: int) -> bool:
        return self.deadline is not None and current_time > self.deadline

class OrderGenerator:
    def __init__(self, num_item_types: int = 50, arrival_rate: float = 0.3, 
                 order_timeout: int = 200, seed: Optional[int] = None):
        self.num_item_types = num_item_types
        self.base_arrival_rate = arrival_rate  # Base λ for Poisson process
        self.rng = np.random.RandomState(seed)
        
        # Adaptive Order Generation Parameters
        self.customer_satisfaction = 1.0  # Start with neutral satisfaction (0.5-2.0 range)
        self.satisfaction_history = []    # Track satisfaction over time
        self.satisfaction_window = 100    # Timesteps to track satisfaction
        
        # Time-of-day patterns (24 hour cycle, 100 timesteps per hour)
        self.timesteps_per_hour = 100
        self.day_length = 24 * self.timesteps_per_hour  # 2400 timesteps = 1 day
        
        # Order complexity distribution - enhanced to favor complex orders with higher rewards
        self.complexity_distribution = {
            'simple': {'weight': 0.40, 'items': (1, 2), 'base_value': 25},     # Reduced weight, increased value
            'medium': {'weight': 0.35, 'items': (3, 4), 'base_value': 90},     # Increased weight and value
            'complex': {'weight': 0.25, 'items': (5, 7), 'base_value': 200}    # Much higher weight and value
        }
        
        # Priority distribution
        self.priority_distribution = {
            'normal': {'weight': 0.80, 'value_multiplier': 1.0, 'deadline': None},
            'priority': {'weight': 0.15, 'value_multiplier': 1.5, 'deadline': None},
            'express': {'weight': 0.05, 'value_multiplier': 2.0, 'deadline': 300}  # 3 hours
        }
        
        # Track order statistics
        self.next_order_id = 1
        self.total_orders_generated = 0
        self.orders_in_last_window = []  # For satisfaction calculation
        
        # Randomized item frequency weights for this episode
        self.item_weights = self._generate_item_weights()
        self.item_popularity = self.item_weights
        self.cooccurrence_matrix = self._generate_cooccurrence_patterns()
    
    def _generate_item_weights(self) -> np.ndarray:
        """Generate enhanced item frequency weights with clear hot/cold items"""
        # Create more pronounced popularity differences for better swap testing
        weights = np.zeros(self.num_item_types)
        
        # Create "hot" items (first 20% of items are very popular)
        hot_items = int(self.num_item_types * 0.2)
        weights[:hot_items] = self.rng.zipf(1.5, hot_items) * 5  # Much higher weights
        
        # Create "warm" items (next 30% are moderately popular)
        warm_start = hot_items
        warm_end = int(self.num_item_types * 0.5)
        weights[warm_start:warm_end] = self.rng.zipf(2, warm_end - warm_start) * 2
        
        # Create "cold" items (remaining 50% are rarely ordered)
        cold_start = warm_end
        weights[cold_start:] = self.rng.zipf(3, self.num_item_types - cold_start) * 0.5
        
        # Normalize to probabilities
        weights = weights / np.sum(weights)
        return weights
    
    def _generate_cooccurrence_patterns(self) -> np.ndarray:
        """Generate enhanced co-occurrence patterns with strong correlations for testing"""
        matrix = np.eye(self.num_item_types) * 0.05  # Lower base correlation
        
        # Create stronger item clusters with higher co-occurrence
        cluster_size = 4  # Smaller clusters for stronger relationships
        num_clusters = self.num_item_types // cluster_size
        
        for cluster in range(num_clusters):
            start_idx = cluster * cluster_size
            end_idx = min(start_idx + cluster_size, self.num_item_types)
            
            # Items in same cluster have MUCH higher co-occurrence
            for i in range(start_idx, end_idx):
                for j in range(start_idx, end_idx):
                    if i != j:
                        matrix[i, j] = self.rng.uniform(0.6, 0.9)  # Very high correlation
        
        # Add some cross-cluster correlations for hot items
        hot_items = int(self.num_item_types * 0.2)
        for i in range(hot_items):
            for j in range(hot_items):
                if i != j and matrix[i, j] < 0.4:  # Don't override strong cluster relationships
                    matrix[i, j] = self.rng.uniform(0.4, 0.6)  # Hot items often ordered together
        
        # Create some "anti-correlations" for testing (items rarely ordered together)
        cold_start = int(self.num_item_types * 0.7)
        for i in range(cold_start, self.num_item_types):
            for j in range(cold_start, self.num_item_types):
                if i != j:
                    matrix[i, j] = self.rng.uniform(0.01, 0.05)  # Very low correlation
        
        return matrix
    
    def generate_orders(self, current_time: int, queue_length: int = 0, num_employees: int = 1) -> List[Order]:
        # Calculate adaptive arrival rate
        time_multiplier = self._get_time_of_day_multiplier(current_time)
        satisfaction_multiplier = self._get_satisfaction_multiplier()
        pressure_multiplier = self._get_queue_pressure_multiplier(queue_length, num_employees)
        
        # Combined arrival rate
        effective_arrival_rate = (self.base_arrival_rate * time_multiplier * 
                                satisfaction_multiplier * pressure_multiplier)
        
        # Use Poisson process to determine number of new orders
        num_new_orders = self.rng.poisson(effective_arrival_rate)
        
        orders = []
        for _ in range(num_new_orders):
            order = self._generate_single_order(current_time)
            orders.append(order)
            self.total_orders_generated += 1
        
        return orders
    
    def _get_queue_pressure_multiplier(self, queue_length: int, num_employees: int) -> float:
        """Reduce order generation when queue is backing up (customers see delays)"""
        if num_employees == 0:
            return 0.1  # Avoid division by zero
        
        queue_ratio = queue_length / max(1, num_employees)
        
        if queue_ratio > 8:      # Severe backlog
            return 0.4           # Many customers order elsewhere
        elif queue_ratio > 5:    # Heavy backlog
            return 0.6           # Some customers deterred
        elif queue_ratio > 3:    # Moderate backlog
            return 0.8           # Slight deterrent effect
        else:                    # Manageable queue
            return 1.0           # Normal ordering
    
    def _get_time_of_day_multiplier(self, current_time: int) -> float:
        """Get order frequency multiplier based on time of day"""
        # Convert timestep to hour of day (0-23)
        hour_of_day = (current_time % self.day_length) / self.timesteps_per_hour
        
        # Define time patterns (24-hour cycle) - more moderate swings
        if 9 <= hour_of_day < 11:      # Morning rush
            return 1.4
        elif 11 <= hour_of_day < 14:   # Lunch lull
            return 0.7
        elif 14 <= hour_of_day < 17:   # Afternoon peak
            return 1.2
        elif 17 <= hour_of_day < 20:   # Evening
            return 0.9
        else:                          # Night/early morning
            return 0.4
    
    def _get_satisfaction_multiplier(self) -> float:
        """Get order frequency multiplier based on customer satisfaction"""
        # Satisfaction affects future orders (word of mouth effect)
        # Range: 0.3x (terrible service) to 2.0x (excellent service)
        return max(0.3, min(2.0, 0.5 + (self.customer_satisfaction * 1.5)))
    
    def update_customer_satisfaction(self, completion_rate: float, current_time: int):
        """Update customer satisfaction based on recent performance"""
        # Add current performance to history
        self.orders_in_last_window.append({
            'completion_rate': completion_rate,
            'timestamp': current_time
        })
        
        # Keep only recent history
        cutoff_time = current_time - self.satisfaction_window
        self.orders_in_last_window = [
            entry for entry in self.orders_in_last_window 
            if entry['timestamp'] > cutoff_time
        ]
        
        # Calculate rolling average satisfaction
        if self.orders_in_last_window:
            recent_completion_rate = np.mean([
                entry['completion_rate'] for entry in self.orders_in_last_window
            ])
            
            # Update satisfaction (0.6+ completion = good, 0.8+ = excellent)
            target_satisfaction = self._completion_rate_to_satisfaction(recent_completion_rate)
            
            # Smooth transition (gradual change)
            alpha = 0.1  # Learning rate
            self.customer_satisfaction = (1 - alpha) * self.customer_satisfaction + alpha * target_satisfaction
    
    def _completion_rate_to_satisfaction(self, completion_rate: float) -> float:
        """Convert completion rate to customer satisfaction score"""
        if completion_rate >= 0.9:      # Excellent service
            return 2.0
        elif completion_rate >= 0.8:    # Good service  
            return 1.5
        elif completion_rate >= 0.7:    # Acceptable service
            return 1.0
        elif completion_rate >= 0.5:    # Poor service
            return 0.7
        else:                           # Terrible service
            return 0.3
    
    def _generate_single_order(self, arrival_time: int) -> Order:
        # Select order complexity
        complexity = self._select_complexity()
        complexity_info = self.complexity_distribution[complexity]
        
        # Select order priority
        priority = self._select_priority()
        priority_info = self.priority_distribution[priority]
        
        # Determine order size within complexity range
        min_items, max_items = complexity_info['items']
        order_size = self.rng.randint(min_items, max_items + 1)
        
        # Generate items for the order
        items = self._generate_order_items(order_size)
        
        # Calculate order value with complexity and priority multipliers
        base_value = complexity_info['base_value']
        value_multiplier = priority_info['value_multiplier']
        
        # Add some randomness (±20%)
        value_variation = self.rng.uniform(0.8, 1.2)
        value = base_value * value_multiplier * value_variation
        
        # Set deadline for express orders
        deadline = None
        if priority == 'express':
            deadline = arrival_time + priority_info['deadline']
        
        order = Order(
            id=self.next_order_id,
            items=items,
            value=value,
            arrival_time=arrival_time,
            priority=priority,
            deadline=deadline
        )
        
        self.next_order_id += 1
        return order
    
    def _select_complexity(self) -> str:
        """Select order complexity based on distribution"""
        complexities = list(self.complexity_distribution.keys())
        weights = [self.complexity_distribution[c]['weight'] for c in complexities]
        return self.rng.choice(complexities, p=weights)
    
    def _select_priority(self) -> str:
        """Select order priority based on distribution"""
        priorities = list(self.priority_distribution.keys())
        weights = [self.priority_distribution[p]['weight'] for p in priorities]
        return self.rng.choice(priorities, p=weights)
    
    def _generate_order_items(self, order_size: int) -> List[int]:
        if order_size == 1:
            # Single item based on popularity
            item = self.rng.choice(self.num_item_types, p=self.item_popularity)
            return [item]
        
        items = set()
        
        # Start with a random item based on popularity
        first_item = self.rng.choice(self.num_item_types, p=self.item_popularity)
        items.add(first_item)
        
        # Add additional items based on co-occurrence patterns
        while len(items) < order_size:
            if len(items) == 1:
                # Second item based on co-occurrence with first
                last_item = list(items)[-1]
                cooccurrence_probs = self.cooccurrence_matrix[last_item]
                cooccurrence_probs = cooccurrence_probs / np.sum(cooccurrence_probs)
                
                # Don't select items already in the order
                for existing_item in items:
                    cooccurrence_probs[existing_item] = 0
                
                if np.sum(cooccurrence_probs) > 0:
                    cooccurrence_probs = cooccurrence_probs / np.sum(cooccurrence_probs)
                    next_item = self.rng.choice(self.num_item_types, p=cooccurrence_probs)
                else:
                    # Fallback to random selection
                    available_items = [i for i in range(self.num_item_types) if i not in items]
                    next_item = self.rng.choice(available_items)
                
                items.add(next_item)
            else:
                # Additional items: mix of co-occurrence and randomness
                if self.rng.random() < 0.7:  # 70% chance to use co-occurrence
                    # Average co-occurrence with all items in order
                    avg_cooccurrence = np.mean([self.cooccurrence_matrix[item] for item in items], axis=0)
                    
                    # Don't select items already in the order
                    for existing_item in items:
                        avg_cooccurrence[existing_item] = 0
                    
                    if np.sum(avg_cooccurrence) > 0:
                        avg_cooccurrence = avg_cooccurrence / np.sum(avg_cooccurrence)
                        next_item = self.rng.choice(self.num_item_types, p=avg_cooccurrence)
                    else:
                        available_items = [i for i in range(self.num_item_types) if i not in items]
                        next_item = self.rng.choice(available_items)
                else:
                    # Random selection from remaining items
                    available_items = [i for i in range(self.num_item_types) if i not in items]
                    next_item = self.rng.choice(available_items)
                
                items.add(next_item)
        
        return sorted(list(items))

class OrderQueue:
    def __init__(self):
        self.orders: List[Order] = []
        self.completed_orders: List[Order] = []
        self.cancelled_orders: List[Order] = []
    
    def add_order(self, order: Order):
        self.orders.append(order)
    
    def get_next_order(self) -> Optional[Order]:
        if self.orders:
            return self.orders[0]
        return None
    
    def assign_order(self, order_id: int) -> Optional[Order]:
        for i, order in enumerate(self.orders):
            if order.id == order_id:
                return self.orders.pop(i)
        return None
    
    def complete_order(self, order: Order, completion_time: int) -> float:
        self.completed_orders.append(order)
        return order.value
    
    def cancel_expired_orders(self, current_time: int) -> List[Order]:
        # Cancel express orders that have expired
        expired_orders = []
        remaining_orders = []
        
        for order in self.orders:
            if order.is_expired(current_time):
                expired_orders.append(order)
                self.cancelled_orders.append(order)
            else:
                remaining_orders.append(order)
        
        self.orders = remaining_orders
        return expired_orders
    
    def get_queue_state(self, current_time: int) -> List[Dict]:
        return [
            {
                'id': order.id,
                'items': order.items,
                'num_items': len(order.items),
                'value': order.value,
                'time_remaining': 999999,  # No expiry
                'arrival_time': order.arrival_time
            }
            for order in self.orders
        ]
    
    def get_statistics(self) -> Dict:
        total_orders = len(self.completed_orders) + len(self.cancelled_orders) + len(self.orders)
        completion_rate = len(self.completed_orders) / total_orders if total_orders > 0 else 0
        
        total_revenue = sum(order.value for order in self.completed_orders)
        
        # No deadlines anymore, so completion time calculation removed
        avg_completion_time = 0
        
        return {
            'total_orders': total_orders,
            'completed_orders': len(self.completed_orders),
            'cancelled_orders': len(self.cancelled_orders),
            'pending_orders': len(self.orders),
            'completion_rate': completion_rate,
            'total_revenue': total_revenue,
            'avg_completion_time': avg_completion_time
        }