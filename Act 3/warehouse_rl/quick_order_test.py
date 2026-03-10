#!/usr/bin/env python3
"""
Quick test to see if orders are being processed at all.
"""

from environment.warehouse_env import WarehouseEnv
from agents.standardized_agents import create_greedy_agent

def main():
    env = WarehouseEnv(
        grid_width=12, 
        grid_height=12, 
        max_employees=15, 
        order_arrival_rate=1.0,  # Higher rate
        employee_salary=0.75
    )
    
    agent = create_greedy_agent(env)
    obs = env.reset()
    
    print("=== Quick Order Processing Test ===")
    
    for step in range(500):
        obs = env._get_observation()
        action = agent.get_action(obs)
        obs, reward, done, truncated, info = env.step(action)
        
        # Show status every 50 steps
        if step % 50 == 0:
            queue_length = len(env.order_queue.orders)
            num_employees = len(env.employees)
            idle_employees = sum(1 for emp in env.employees if emp.state.name == 'IDLE')
            profit = env.cumulative_profit
            orders_completed = info.get('total_completed_orders', 0)
            
            print(f"Step {step}: Queue={queue_length}, Employees={num_employees} ({idle_employees} idle), "
                  f"Profit=${profit:.2f}, Orders completed={orders_completed}")
        
        if done or truncated:
            break
    
    print(f"\nFinal status:")
    print(f"  Total revenue: ${env.total_revenue:.2f}")
    print(f"  Total costs: ${env.total_costs:.2f}")
    print(f"  Final profit: ${env.cumulative_profit:.2f}")
    print(f"  Orders completed: {info.get('total_completed_orders', 0)}")

if __name__ == "__main__":
    main()