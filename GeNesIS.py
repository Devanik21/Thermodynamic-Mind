import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from genesis_world import GenesisWorld, Resource
from genesis_brain import GenesisAgent
import random

# ============================================================
# ⚙️ CONFIG & STATE
# ============================================================
st.set_page_config(layout="wide", page_title="Zero Point Genesis", page_icon="⚛️")

if "world" not in st.session_state:
    st.session_state.world = GenesisWorld(size=40)
    # Spawn Adam & Eves (64 Agents)
    for _ in range(64):
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        agent = GenesisAgent(x, y)
        st.session_state.world.agents[agent.id] = agent
        
    for _ in range(150):
        st.session_state.world.spawn_resource()

if "stats_history" not in st.session_state:
    st.session_state.stats_history = []

# 🧬 GENE POOL: The Hall of Ancestors
if "gene_pool" not in st.session_state:
    st.session_state.gene_pool = [] # List of genomes (dicts)
    
if "max_generation" not in st.session_state:
    st.session_state.max_generation = 0

if "running" not in st.session_state:
    st.session_state.running = False

# ============================================================
# 🖥️ UI HEADER: THE CHAOS MONITOR
# ============================================================
st.title("⚛️ Zero Point Genesis: Causal Adaptation")

# Dynamic Season Indicator
season_mode = "SUMMER 🌞" if st.session_state.world.current_season % 2 == 0 else "WINTER ❄️"
season_color = "#ffbd45" if st.session_state.world.current_season % 2 == 0 else "#45b6fe"
next_flip = 50 - st.session_state.world.season_timer

col_head1, col_head2, col_head3 = st.columns([2, 1, 1])
with col_head1:
    st.markdown(f"""
    ### Current Epoch: <span style='color:{season_color}'>{season_mode}</span>
    **Next Quantum Flip in:** `{next_flip}` ticks
    
    *Evolution is Active. Successful agents pass genes to the next generation.*
    **Gene Pool Size:** `{len(st.session_state.gene_pool)}` | **Max Generation:** `{st.session_state.max_generation}`
    """, unsafe_allow_html=True)
with col_head2:
    if st.button("▶️ SYSTEM TOGGLE", use_container_width=True):
        st.session_state.running = not st.session_state.running
with col_head3:
    if st.button("♻️ BIG BANG (Reset)", use_container_width=True):
        st.session_state.world = GenesisWorld(size=40)
        st.session_state.stats_history = []
        st.session_state.gene_pool = []
        st.session_state.max_generation = 0
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
    np.random.shuffle(agents) 
    
    for agent in agents:
        if agent.energy <= 0:
            deaths.append(agent.id)
            continue
            
        # Sensory Input
        signal = world.get_sensory_input(agent)
        
        # Causal Decision
        action = agent.decide(signal)
        
        # Interaction
        reward = 0.0
        if action == 5: # EAT
            r = world.attempt_eat(agent)
            if r > 0: reward = 5.0  
            elif r < 0: reward = -10.0 
            else: reward = -0.1 
        elif action == 0:
            reward = 0.05 
        else:
            world.move_agent(agent, action)
            reward = -0.05 
            
        # Neural Metamorphosis
        learned = agent.metabolize_outcome(reward)
        if learned: current_thoughts += 1
        else: current_reflexes += 1
            
        agent.energy -= 0.5 
        
    for dead_id in deaths:
        # ⚰️ FUNERAL RITE: Save Genes if worthy
        dead_agent = world.agents[dead_id]
        if dead_agent.age > 20: # Only adults contribute
            st.session_state.gene_pool.append(dead_agent.get_genome())
            # Keep pool fresh (drift)
            if len(st.session_state.gene_pool) > 50:
                st.session_state.gene_pool.pop(0)
                
        del world.agents[dead_id]
        
    # 🌱 REBIRTH: Evolutionary Spawning
    if len(world.agents) < 40:
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        
        # Inheritance Logic
        genome = None
        generation = 0
        if st.session_state.gene_pool and np.random.random() < 0.8: # 80% chance to inherit
            genome = random.choice(st.session_state.gene_pool)
            # We don't strictly track generation in the dict, but we can infer progress
            # For simplicity, we just increment global counter if inheritance happens
            st.session_state.max_generation += 1 
            generation = st.session_state.max_generation
        
        new_agent = GenesisAgent(x, y, genome=genome, generation=generation)
        world.agents[new_agent.id] = new_agent
        
    # Stats
    stats = {
        "tick": world.time_step,
        "population": len(world.agents),
        "thoughts": current_thoughts,
        "reflexes": current_reflexes,
        "avg_energy": np.mean([a.energy for a in world.agents.values()]) if world.agents else 0,
        "season_flip": 1 if world.season_timer == 1 else 0
    }
    st.session_state.stats_history.append(stats)
    if len(st.session_state.stats_history) > 200:
        st.session_state.stats_history.pop(0)
    
    time.sleep(0.01) 
    st.rerun()

# ============================================================
# 📊 THE ADAPTATION MONITOR
# ============================================================
if st.session_state.stats_history:
    df = pd.DataFrame(st.session_state.stats_history)
    
    # 1. The Adaptation Graph
    fig = go.Figure()
    
    flips = df[df['season_flip'] == 1]
    
    fig.add_trace(go.Scatter(
        x=df['tick'], y=df['population'], 
        name="Survivors", 
        line=dict(color='#00ffa3', width=2),
        fill='tozeroy', 
        fillcolor='rgba(0, 255, 163, 0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['tick'], y=df['thoughts'], 
        name="Neuro-Plasticity Events", 
        line=dict(color='#ff4b4b', width=1),
        mode='lines'
    ))
    
    # Markers for Season Change
    fig.add_trace(go.Scatter(
        x=flips['tick'], y=flips['population'],
        mode='markers', name="QUANTUM FLIP",
        marker=dict(symbol='star', size=12, color='yellow')
    ))

    fig.update_layout(
        title="Survival vs Adaptation Lag",
        font=dict(color='#e0e4de'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor='#333')
    )
    st.plotly_chart(fig, use_container_width=True)

# 2. Grid & Brains
col_grid, col_info = st.columns([3, 1])

with col_grid:
    # Heatmap
    grid_map = np.zeros((40, 40))
    for (rx, ry), res in st.session_state.world.grid.items():
        val = res.get_nutrition(st.session_state.world.current_season)
        grid_map[ry, rx] = val 
            
    for agent in st.session_state.world.agents.values():
        # High Energy = Brighter
        intensity = 50 + (agent.energy * 1.5) 
        grid_map[agent.y, agent.x] = intensity 

    fig_map = px.imshow(
        grid_map, 
        color_continuous_scale='RdBu', 
        zmin=-50, zmax=150, # Expanded range for super-charged agents
        title=f"Environment Truth Map ({season_mode})"
    )
    fig_map.update_traces(showscale=False)
    fig_map.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig_map, use_container_width=True)

with col_info:
    if st.session_state.stats_history:
        curr = st.session_state.stats_history[-1]
        st.metric("Agents", curr["population"])
        st.metric("Avg Energy", f"{curr['avg_energy']:.1f}")
        
        # Max Age
        max_age = 0
        if st.session_state.world.agents:
            max_age = max([a.age for a in st.session_state.world.agents.values()])
        st.metric("Oldest Agent (Ticks)", max_age)
        
    st.info("""
    **Legend:**
    🔴 Red Pixels = POISON
    🔵 Blue Pixels = FOOD
    ✨ White/Bright = HIGH ENERGY AGENT
    🌑 Dim = DYING AGENT
    
    *Resources now move (Drift).*
    """)

