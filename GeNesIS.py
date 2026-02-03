import streamlit as st
import numpy as np
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
import json
import zipfile
import io
import torch
import random
from genesis_world import GenesisWorld, Resource
from genesis_brain import GenesisAgent

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

if "gene_pool" not in st.session_state:
    st.session_state.gene_pool = [] 
    
if "max_generation" not in st.session_state:
    st.session_state.max_generation = 0

if "running" not in st.session_state:
    st.session_state.running = False

# Event Log for "Every Drop of Decision"
if "event_log" not in st.session_state:
    st.session_state.event_log = []

# ============================================================
# 🔄 1. LOGIC STEP (UPDATE WORLD)
# ============================================================
# We run the logic FIRST, then render.
if st.session_state.running:
    world = st.session_state.world
    
    # Physics
    world.step()
    
    # Agent Loop
    current_thoughts = 0
    current_reflexes = 0
    deaths = []
    events_this_tick = []
    
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
        interaction_text = ""
        
        if action == 5: # EAT
            r = world.attempt_eat(agent)
            if r > 0: 
                reward = 5.0
                interaction_text = "😋 ATE FOOD"
            elif r < 0: 
                reward = -10.0 
                interaction_text = "🤮 ATE POISON"
            else: 
                reward = -0.1 
        elif action == 0:
            reward = 0.05 
        else:
            world.move_agent(agent, action)
            reward = -0.05 
            
        # Neural Metamorphosis
        learned = agent.metabolize_outcome(reward)
        
        if learned: 
            current_thoughts += 1
            # Log Significant Learning Events
            if abs(reward) > 1.0: # Only significant moments
                events_this_tick.append({
                    "Tick": world.time_step,
                    "Agent": agent.id,
                    "Gen": agent.generation,
                    "Event": f"{interaction_text} -> REWIRING BRAIN",
                    "Energy": f"{agent.energy:.1f}"
                })
        else: 
            current_reflexes += 1
            
        agent.energy -= 0.5 
        
    for dead_id in deaths:
        dead_agent = world.agents[dead_id]
        if dead_agent.age > 20: 
            st.session_state.gene_pool.append(dead_agent.get_genome())
            if len(st.session_state.gene_pool) > 50:
                st.session_state.gene_pool.pop(0)
            events_this_tick.append({
                "Tick": world.time_step,
                "Agent": dead_agent.id,
                "Gen": dead_agent.generation,
                "Event": "💀 DIED (GENES SAVED)",
                "Energy": "0.0"
            })
        del world.agents[dead_id]
        
    # Spawning
    if len(world.agents) < 40:
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        genome = None
        gen = 0
        if st.session_state.gene_pool and np.random.random() < 0.8:
            genome = random.choice(st.session_state.gene_pool)
            st.session_state.max_generation += 1 
            gen = st.session_state.max_generation
        
        new_agent = GenesisAgent(x, y, genome=genome, generation=gen)
        world.agents[new_agent.id] = new_agent
        if gen > 0:
             events_this_tick.append({
                "Tick": world.time_step,
                "Agent": new_agent.id,
                "Gen": gen,
                "Event": "👶 BORN (INHERITED)",
                "Energy": "50.0"
            })
            
    # Update Stats
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
        
    # Update Event Log (Keep last 20)
    for e in events_this_tick:
        st.session_state.event_log.insert(0, e) # Prepend
    st.session_state.event_log = st.session_state.event_log[:20]

# ============================================================
# 🖥️ 2. VISUALIZATION (RENDER ALWAYS)
# ============================================================
st.title("⚛️ Zero Point Genesis: Causal Adaptation")

# Header
curr_season_idx = st.session_state.world.current_season
season_mode = "SUMMER 🌞" if curr_season_idx % 2 == 0 else "WINTER ❄️"
season_color = "#ffbd45" if curr_season_idx % 2 == 0 else "#45b6fe"
next_flip = 50 - st.session_state.world.season_timer

col_head1, col_head2, col_head3 = st.columns([2, 1, 1])
with col_head1:
    st.markdown(f"""
    ### Current Epoch: <span style='color:{season_color}'>{season_mode}</span>
    **Next Quantum Flip in:** `{next_flip}` ticks
    **Gene Pool:** `{len(st.session_state.gene_pool)}` | **Max Gen:** `{st.session_state.max_generation}`
    """, unsafe_allow_html=True)
with col_head2:
    if st.button("▶️ SYSTEM TOGGLE", use_container_width=True):
        st.session_state.running = not st.session_state.running
with col_head3:
    if st.button("♻️ BIG BANG", use_container_width=True):
        st.session_state.world = GenesisWorld(size=40)
        st.session_state.stats_history = []
        st.session_state.gene_pool = []
        st.session_state.max_generation = 0
        st.rerun()

    # Report Generator
    def generate_report():
        # 1. Stats
        stats_json = json.dumps(st.session_state.stats_history, indent=2)
        
        # 2. Gene Pool (Convert Tensors to Lists)
        encoded_pool = []
        for genome in st.session_state.gene_pool:
            clean_genome = {k: v.cpu().tolist() for k, v in genome.items()}
            encoded_pool.append(clean_genome)
        gene_json = json.dumps(encoded_pool)
        
        # 3. Events
        events_json = json.dumps(st.session_state.event_log, indent=2)
        
        # Zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("stats.json", stats_json)
            zf.writestr("genes.json", gene_json)
            zf.writestr("events.json", events_json)
        return zip_buffer.getvalue()

    st.download_button(
        label="💾 SAVE DATA",
        data=generate_report(),
        file_name="genesis_data.zip",
        mime="application/zip",
        use_container_width=True
    )

# --- MAIN GRAPH: The Nobel Metric ---
if st.session_state.stats_history:
    df = pd.DataFrame(st.session_state.stats_history)
    fig = go.Figure()
    flips = df[df['season_flip'] == 1]
    
    fig.add_trace(go.Scatter(x=df['tick'], y=df['population'], name="Survivors", line=dict(color='#00ffa3', width=2), fill='tozeroy', fillcolor='rgba(0, 255, 163, 0.1)'))
    fig.add_trace(go.Scatter(x=df['tick'], y=df['thoughts'], name="Brain Plasticity (Backprop)", line=dict(color='#ff4b4b', width=1)))
    fig.add_trace(go.Scatter(x=flips['tick'], y=flips['population'], mode='markers', name="QUANTUM FLIP", marker=dict(symbol='star', size=12, color='yellow')))

    fig.update_layout(title="Evolutionary Trajectory", font=dict(color='#e0e4de'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#333'))
    st.plotly_chart(fig, use_container_width=True)

# --- LOWER SECTION: MAP & SYNAPTIC LOG ---
col_grid, col_log = st.columns([2, 1])

with col_grid:
    # 🌍 Environment Truth Map
    grid_map = np.zeros((40, 40))
    for (rx, ry), res in st.session_state.world.grid.items():
        # VISUALIZE TRUTH based on CURRENT SEASON variable used in HEADER
        val = res.get_nutrition(curr_season_idx)
        grid_map[ry, rx] = val 
            
    for agent in st.session_state.world.agents.values():
        intensity = 50 + (agent.energy * 2.0) 
        grid_map[agent.y, agent.x] = intensity 

    # Custom Logic: Red=Poison, Black=Empty, Green=Food, White=Agents
    # Range is roughly -50 to 150
    # -50 = Red
    # 0 = Black
    # 20 = Green
    # 100+ = White
    
    custom_colors = [
        [0.0, "red"],       # -50 (Poison)
        [0.25, "black"],    # 0 (Empty)
        [0.35, "green"],    # +20 (Food)
        [1.0, "white"]      # +150 (High Energy Agent)
    ]

    fig_map = px.imshow(
        grid_map, 
        color_continuous_scale=custom_colors, 
        zmin=-50, zmax=150, 
        title=f"Environment Truth: {season_mode} (Green=Food, Red=Poison)"
    )
    fig_map.update_traces(showscale=False)
    fig_map.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig_map, use_container_width=True)

with col_log:
    st.subheader("Synaptic Stream ⚡")
    if st.session_state.event_log:
        log_df = pd.DataFrame(st.session_state.event_log)
        st.dataframe(
            log_df[["Agent", "Gen", "Event"]], 
            use_container_width=True, 
            height=400,
            column_config={
                "Agent": st.column_config.TextColumn("ID", width="small"),
                "Gen": st.column_config.NumberColumn("G", width="small"),
                "Event": st.column_config.TextColumn("Synaptic Event", width="large")
            }
        )
    else:
        st.info("Waiting for neural events...")

# ============================================================
# 🔄 3. LOOP RESTART
# ============================================================
if st.session_state.running:
    time.sleep(0.01) # Small throttle
    st.rerun()
