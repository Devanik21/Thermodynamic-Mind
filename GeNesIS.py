import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from genesis_world import GenesisWorld, Resource
from genesis_brain import GenesisAgent

# ============================================================
# ⚙️ CONFIG & STATE
# ============================================================
st.set_page_config(layout="wide", page_title="Zero Point Genesis", page_icon="⚛️")

if "world" not in st.session_state:
    st.session_state.world = GenesisWorld(size=40)
    # Spawn Adam & Eves (50 Agents)
    for _ in range(50):
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        agent = GenesisAgent(x, y)
        st.session_state.world.agents[agent.id] = agent
        
    # Spawn Initial Resources
    for _ in range(100):
        st.session_state.world.spawn_resource()

if "stats_history" not in st.session_state:
    st.session_state.stats_history = []
    
if "running" not in st.session_state:
    st.session_state.running = False

# ============================================================
# 🖥️ UI HEADER
# ============================================================
st.title("⚛️ Zero Point Genesis")
st.markdown("""
**The Hypothesis:** Intelligence is not about thinking; it's about *not* thinking.
Agents burn **5.0 Energy** to Learn (Backprop) but only **0.1 Energy** to Act (Reflex).
Watch the **Red Line** (Thinking) drop as they evolve habits to survive.
""")

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("▶️ Start / Pause"):
        st.session_state.running = not st.session_state.running
with col2:
    if st.button("💀 Extinction Event (Reset)"):
        st.session_state.world = GenesisWorld(size=40)
        for _ in range(50):
            x, y = np.random.randint(0, 40), np.random.randint(0, 40)
            agent = GenesisAgent(x, y)
            st.session_state.world.agents[agent.id] = agent
        st.session_state.stats_history = []
        st.rerun()

# ============================================================
# 🔄 SIMULATION LOOP
# ============================================================
if st.session_state.running:
    world = st.session_state.world
    
    # 1. Physics Step
    world.step()
    
    # 2. Agent Steps
    current_thoughts = 0
    current_reflexes = 0
    deaths = []
    
    agents = list(world.agents.values())
    for agent in agents:
        # Check Existence
        if agent.energy <= 0:
            deaths.append(agent.id)
            continue
            
        # Sensory Input
        signal = world.get_sensory_input(agent)
        
        # Decision (Thought or Reflex?)
        action = agent.decide(signal)
        
        # Execute Action
        # 0: Stay, 1: Up, 2: Down, 3: Left, 4: Right, 5: Eat
        reward = 0.0
        if action == 5:
            r = world.attempt_eat(agent)
            if r > 0: reward = 10.0 # Big dopamine for food
            elif r < 0: reward = -5.0 # Pain for bad action
        elif action == 0:
            reward = 0.1 # Tiny reward for conserving energy?
        else:
            world.move_agent(agent, action)
            reward = -0.1 # Small cost for moving
            
        # Metabolic Outcome
        learned = agent.metabolize_outcome(reward)
        
        if learned:
            current_thoughts += 1
        else:
            current_reflexes += 1
            
        # Existence Tax
        agent.energy -= 0.5
        
    # Process Deaths
    for dead_id in deaths:
        del world.agents[dead_id]
        
        
    # Auto-Repopulate (If too few)
    # This prevents the simulation from ending too quickly during the initial "Stupid Phase"
    if len(world.agents) < 10:
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        new_agent = GenesisAgent(x, y)
        world.agents[new_agent.id] = new_agent
        
    # Record Stats
    stats = {
        "tick": world.time_step,
        "population": len(world.agents),
        "total_thoughts": current_thoughts,
        "total_reflexes": current_reflexes,
        "avg_energy": np.mean([a.energy for a in world.agents.values()]) if world.agents else 0
    }
    st.session_state.stats_history.append(stats)
    
    # Keep history bounded
    if len(st.session_state.stats_history) > 100:
        st.session_state.stats_history.pop(0)
    
    time.sleep(0.05) # Rate limit
    st.rerun()

# ============================================================
# 📊 VISUALIZATION
# ============================================================
if st.session_state.stats_history:
    df = pd.DataFrame(st.session_state.stats_history)
    
    # 1. The Nobel Graph
    # We use secondary Y axis for Thoughts to see the contrast better
    fig = go.Figure()
    
    # Trace 1: Conscious Thoughts (Red)
    fig.add_trace(go.Scatter(
        x=df['tick'], y=df['total_thoughts'], 
        name="Conscious Thoughts (Backprop)", 
        line=dict(color='#ff4b4b', width=3),
        mode='lines'
    ))
    
    # Trace 2: Survivors (Green)
    fig.add_trace(go.Scatter(
        x=df['tick'], y=df['population'], 
        name="Survivors", 
        line=dict(color='#00ffa3', width=2),
        yaxis='y2'
    ))
    
    # Layout
    fig.update_layout(
        title="Thermodynamics of Mind: Learning Cost Analysis",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e4de'),
        xaxis=dict(title="Time Ticks", gridcolor='#333'),
        yaxis=dict(title="Calculation Events", gridcolor='#333'),
        yaxis2=dict(
            title="Population Count",
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

# 2. The Grid View
st.subheader("🌍 The Simulation Grid")
col_map, col_metrics = st.columns([3, 1])

with col_map:
    # Create a matrix for heatmap
    grid_map = np.zeros((40, 40))
    
    # Fill with Resources
    for (rx, ry), res in st.session_state.world.grid.items():
        if res.nutrition > 0:
            grid_map[ry, rx] = 50 # Food (Yellowish)
        else:
            grid_map[ry, rx] = -50 # Poison (Purpleish)
            
    # Fill with Agents (Overwrites resources visually)
    for agent in st.session_state.world.agents.values():
        grid_map[agent.y, agent.x] = 100 # Bright spot (Agent)

    fig_map = px.imshow(
        grid_map, 
        color_continuous_scale='Viridis', 
        zmin=-50, zmax=100
    )
    fig_map.update_traces(showscale=False)
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False)
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_metrics:
    if st.session_state.stats_history:
        curr = st.session_state.stats_history[-1]
        st.metric("Population", curr["population"])
        st.metric("Thoughts/Tick", curr["total_thoughts"], delta_color="inverse")
        st.metric("Avg Energy", f"{curr['avg_energy']:.1f}")
