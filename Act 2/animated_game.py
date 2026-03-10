"""
Animated Game Visualization
Interactive HTML/JS animation for individual games
"""
from IPython.display import HTML, display
import json
import uuid


def show_animated_game(game, animation_speed=800):
    """
    Display an animated visualization of a completed game.
    
    Args:
        game: A Game object that has been played (with .rounds populated)
        animation_speed: Speed of animation in milliseconds (default 800)
    """
    rounds = game.rounds
    agent1 = game.agent1
    agent2 = game.agent2
    
    # Convert rounds to simple data structure
    data = [{
        "r": r.round_num,
        "a1": 1 if r.player1_action else 0,
        "a2": 1 if r.player2_action else 0,
        "p1": r.player1_payoff,
        "p2": r.player2_payoff,
    } for r in rounds[:50]]  # Limit to 50 rounds for display
    
    gid = f"g{uuid.uuid4().hex[:8]}"
    
    html = f"""
<style>
  #{gid} .game-wrap {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 900px;
    margin: 20px auto;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }}
  #{gid} .header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    color: white;
  }}
  #{gid} .agents {{
    display: flex;
    justify-content: space-around;
    margin-top: 10px;
  }}
  #{gid} .agent {{
    text-align: center;
    padding: 10px;
    background: rgba(255,255,255,0.1);
    border-radius: 8px;
    flex: 1;
    margin: 0 10px;
  }}
  #{gid} .controls {{
    padding: 15px;
    background: #f5f5f5;
    display: flex;
    justify-content: center;
    gap: 10px;
  }}
  #{gid} .btn {{
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    background: #667eea;
    color: white;
    cursor: pointer;
    font-weight: 600;
    font-size: 14px;
  }}
  #{gid} .btn:hover {{ background: #5568d3; }}
  #{gid} .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
  #{gid} .scores {{
    display: flex;
    justify-content: space-around;
    padding: 20px;
    background: white;
    font-size: 24px;
    font-weight: bold;
  }}
  #{gid} .score {{ transition: transform 0.3s; }}
  #{gid} .score.bump {{ transform: scale(1.2); }}
  #{gid} .grid {{
    padding: 20px;
    display: grid;
    grid-template-columns: 60px 1fr 1fr;
    gap: 8px;
    align-items: center;
    max-height: 400px;
    overflow-y: auto;
  }}
  #{gid} .round-label {{
    text-align: center;
    color: #666;
    font-weight: 600;
  }}
  #{gid} .action {{
    display: flex;
    justify-content: center;
  }}
  #{gid} .dot {{
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: #999;
    transition: all 0.3s;
  }}
  #{gid} .dot.invest {{ background: #4caf50; color: white; }}
  #{gid} .dot.undercut {{ background: #f44336; color: white; }}
</style>

<div id="{gid}">
  <div class="game-wrap">
    <div class="header">
      <h2 style="margin: 0 0 10px 0; text-align: center;">Market Entry Game</h2>
      <div class="agents">
        <div class="agent">
          <div style="font-size: 18px; font-weight: bold;">{agent1.name}</div>
          <div style="font-size: 12px; margin-top: 5px; opacity: 0.9;">{agent1.description}</div>
        </div>
        <div style="display: flex; align-items: center; color: white; font-size: 24px; font-weight: bold;">VS</div>
        <div class="agent">
          <div style="font-size: 18px; font-weight: bold;">{agent2.name}</div>
          <div style="font-size: 12px; margin-top: 5px; opacity: 0.9;">{agent2.description}</div>
        </div>
      </div>
    </div>
    
    <div class="controls">
      <button id="{gid}-start" class="btn">▶ Start Animation</button>
      <button id="{gid}-reset" class="btn" disabled>↻ Reset</button>
    </div>
    
    <div class="scores">
      <div><span id="{gid}-score1" class="score">0</span> <span style="font-size: 14px; color: #666;">({agent1.name})</span></div>
      <div><span id="{gid}-score2" class="score">0</span> <span style="font-size: 14px; color: #666;">({agent2.name})</span></div>
    </div>
    
    <div class="grid" id="{gid}-grid">
      <div></div>
      <div style="text-align: center; font-weight: bold; color: #667eea;">{agent1.name}</div>
      <div style="text-align: center; font-weight: bold; color: #764ba2;">{agent2.name}</div>
    </div>
  </div>
</div>

<script>
(function() {{
  const data = {json.dumps(data)};
  const speed = {animation_speed};
  const gid = "{gid}";
  
  const btnStart = document.getElementById(gid + "-start");
  const btnReset = document.getElementById(gid + "-reset");
  const score1El = document.getElementById(gid + "-score1");
  const score2El = document.getElementById(gid + "-score2");
  const grid = document.getElementById(gid + "-grid");
  
  let running = false;
  let rows = [];
  
  // Create grid rows
  data.forEach((d, idx) => {{
    const roundLabel = document.createElement("div");
    roundLabel.className = "round-label";
    roundLabel.textContent = d.r;
    
    const action1 = document.createElement("div");
    action1.className = "action";
    const dot1 = document.createElement("div");
    dot1.className = "dot";
    dot1.textContent = "?";
    action1.appendChild(dot1);
    
    const action2 = document.createElement("div");
    action2.className = "action";
    const dot2 = document.createElement("div");
    dot2.className = "dot";
    dot2.textContent = "?";
    action2.appendChild(dot2);
    
    grid.appendChild(roundLabel);
    grid.appendChild(action1);
    grid.appendChild(action2);
    
    rows.push({{ dot1, dot2 }});
  }});
  
  function delay(ms) {{
    return new Promise(resolve => setTimeout(resolve, ms));
  }}
  
  function bump(el) {{
    el.classList.add("bump");
    setTimeout(() => el.classList.remove("bump"), 300);
  }}
  
  async function animate() {{
    if (running) return;
    running = true;
    btnStart.disabled = true;
    
    let s1 = 0, s2 = 0;
    
    for (let i = 0; i < data.length; i++) {{
      const d = data[i];
      const row = rows[i];
      
      await delay(speed * 0.3);
      
      // Reveal player 1
      row.dot1.textContent = d.a1 ? "I" : "U";
      row.dot1.className = "dot " + (d.a1 ? "invest" : "undercut");
      
      await delay(speed * 0.2);
      
      // Reveal player 2
      row.dot2.textContent = d.a2 ? "I" : "U";
      row.dot2.className = "dot " + (d.a2 ? "invest" : "undercut");
      
      await delay(speed * 0.3);
      
      // Update scores
      s1 += d.p1;
      s2 += d.p2;
      score1El.textContent = s1;
      score2El.textContent = s2;
      bump(score1El);
      bump(score2El);
      
      await delay(speed * 0.2);
    }}
    
    running = false;
    btnReset.disabled = false;
  }}
  
  function reset() {{
    rows.forEach(row => {{
      row.dot1.className = "dot";
      row.dot1.textContent = "?";
      row.dot2.className = "dot";
      row.dot2.textContent = "?";
    }});
    score1El.textContent = "0";
    score2El.textContent = "0";
    btnStart.disabled = false;
    btnReset.disabled = true;
  }}
  
  btnStart.addEventListener("click", animate);
  btnReset.addEventListener("click", reset);
}})();
</script>
"""
    
    display(HTML(html))