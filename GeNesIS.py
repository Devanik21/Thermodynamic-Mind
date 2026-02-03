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
if st.session_state.running:
    world = st.session_state.world
    world.step()
    
    current_thoughts = 0
    current_reflexes = 0
    deaths = []
    events_this_tick = []
    
    agents = list(world.agents.values())
    np.random.shuffle(agents) 
    
    total_pos_flux = 0.0
    total_neg_flux = 0.0
    
    for agent in agents:
        if agent.energy <= 0:
            deaths.append(agent.id)
            continue
            
        # Sensory Input
        signal = world.get_local_signal(agent.x, agent.y)
        
        # 🧠 21D Reality Vector Decision
        reality_vector_tensor = agent.decide(signal) 
        
        # 🔮 Quantum Resolution
        flux, log_text = world.resolve_quantum_state(agent, reality_vector_tensor)
        
        # Tracking Moral Compass
        if flux > 0: total_pos_flux += flux
        elif flux < 0: total_neg_flux += abs(flux)
            
        # Neural Metamorphosis
        learned = agent.metabolize_outcome(flux)
        
        # Log Interesting Events
        if "IDLE" not in log_text and "MOVE" not in log_text:
             events_this_tick.append({
                "Tick": world.time_step,
                "Agent": agent.id,
                "Gen": agent.generation,
                "Event": f"{log_text} ({flux:.1f}E)",
                "Vector": reality_vector_tensor.tolist()[0] # Capture the spell
            })
            
        if learned: current_thoughts += 1
        else: current_reflexes += 1
            
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
                "Event": "💀 DIED",
                "Vector": [0.0]*21
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

    # Update Stats
    stats = {
        "tick": world.time_step,
        "population": len(world.agents),
        "thoughts": current_thoughts,
        "avg_energy": np.mean([a.energy for a in world.agents.values()]) if world.agents else 0,
        "season_flip": 1 if world.season_timer == 1 else 0,
        "pos_flux": total_pos_flux,
        "neg_flux": total_neg_flux
    }
    st.session_state.stats_history.append(stats)
    if len(st.session_state.stats_history) > 200:
        st.session_state.stats_history.pop(0)
        
    # Update Event Log (Keep last 20)
    for e in events_this_tick:
        st.session_state.event_log.insert(0, e) 
    st.session_state.event_log = st.session_state.event_log[:20]

# ============================================================
# 🖥️ 2. VISUALIZATION
# ============================================================
st.title("⚛️ Zero Point Genesis: 21-Dimensional Sandbox")

# Header
curr_season_idx = st.session_state.world.current_season
season_mode = "SUMMER 🌞" if curr_season_idx % 2 == 0 else "WINTER ❄️"
season_color = "#ffbd45" if curr_season_idx % 2 == 0 else "#45b6fe"
next_flip = 50 - st.session_state.world.season_timer

col_head1, col_head2, col_head3 = st.columns([2, 1, 1])
with col_head1:
    st.markdown(f"""
    ### Orbit: <span style='color:{season_color}'>{season_mode}</span>
    **Gene Pool:** `{len(st.session_state.gene_pool)}` | **Max Gen:** `{st.session_state.max_generation}`
    *Watch the Spectrogram below to see the Agents' "Spells"*
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

    def generate_report():
        stats_json = json.dumps(st.session_state.stats_history, indent=2)
        encoded_pool = []
        for genome in st.session_state.gene_pool:
            clean_genome = {k: v.cpu().tolist() for k, v in genome.items()}
            encoded_pool.append(clean_genome)
        gene_json = json.dumps(encoded_pool)
        events_json = json.dumps(st.session_state.event_log, indent=2)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("stats.json", stats_json)
            zf.writestr("genes.json", gene_json)
            zf.writestr("events.json", events_json)
        return zip_buffer.getvalue()

    st.download_button("💾 SAVE DATA", generate_report(), "genesis_data.zip", "application/zip", use_container_width=True)

# --- GRAPHS ---
if st.session_state.stats_history:
    df = pd.DataFrame(st.session_state.stats_history)
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['tick'], y=df['population'], name="Survivors", line=dict(color='#00ffa3')))
        fig.add_trace(go.Scatter(x=df['tick'], y=df['thoughts'], name="Brain Rewiring", line=dict(color='#ff4b4b')))
        fig.update_layout(title="Evolutionary Trajectory", height=200, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
    with col_g2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df['tick'], y=df['pos_flux'], name="Positive Inventions", line=dict(color='yellow'), fill='tozeroy'))
        fig2.add_trace(go.Scatter(x=df['tick'], y=df['neg_flux'], name="Negative Disasters", line=dict(color='red'), fill='tozeroy'))
        fig2.update_layout(title="The Moral Compass (Good vs Evil)", height=200, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

# --- LOWER SECTION: MAP & SPECTROGRAM ---
col_grid, col_log = st.columns([2, 1])

with col_grid:
    # 🌍 Truth Map
    grid_map = np.zeros((40, 40))
    for (rx, ry), res in st.session_state.world.grid.items():
        val = res.get_nutrition(curr_season_idx)
        grid_map[ry, rx] = val 
            
    for agent in st.session_state.world.agents.values():
        intensity = 50 + (agent.energy * 2.0) 
        grid_map[agent.y, agent.x] = intensity 

    custom_colors = [[0.0, "red"], [0.25, "black"], [0.35, "green"], [1.0, "white"]]
    fig_map = px.imshow(grid_map, color_continuous_scale=custom_colors, zmin=-50, zmax=150, title=f"Environment Truth: {season_mode}")
    fig_map.update_traces(showscale=False)
    fig_map.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
    st.plotly_chart(fig_map, use_container_width=True)

with col_log:
    st.subheader("Quantum Spell Spectrogram 🧬")
    if st.session_state.event_log:
        # Show the "Mind State" of 10 random agents
        # This proves they are different
        sample_agents = random.sample(list(st.session_state.world.agents.values()), min(len(st.session_state.world.agents), 10))
        vectors = []
        labels = []
        for a in sample_agents:
            if a.last_vector is not None:
                vectors.append(a.last_vector.tolist()[0])
                labels.append(f"Agent {a.id[:4]}")
        
        if vectors:
            vec_arr = np.array(vectors)
            fig_spec = px.imshow(
                vec_arr, 
                color_continuous_scale='Plasma', 
                aspect='auto',
                labels=dict(x="Dimension (0-20)", y="Agent ID", color="Activation"),
                title=f"Population Thought Spectrum (n={len(vectors)})"
            )
            fig_spec.update_layout(height=200, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_spec, use_container_width=True)
            
        log_df = pd.DataFrame(st.session_state.event_log)
        st.dataframe(
            log_df[["Agent", "Event"]], 
            use_container_width=True, 
            height=200
        )
    else:
        st.info("Waiting for quantum collapse...")

# ============================================================
# 🧬 Ω OMEGA DASHBOARD (The Infinite Metrics)
# ============================================================
st.markdown("---")
with st.expander("Ω OMEGA TELEMETRY (100+ Dimensions of Possibility)", expanded=True):
    col_omega1, col_omega2 = st.columns([1, 3])
    
    with col_omega1:
        st.markdown("### 🏛️ Civilization Status")
        
        # Calculate Civilization Metrics
        max_energy = 0
        max_age = 0
        total_alchemy = 0
        if st.session_state.world.agents:
            max_energy = max([a.energy for a in st.session_state.world.agents.values()])
            max_age = max([a.age for a in st.session_state.world.agents.values()])
            
        # Check for "Milestones"
        milestones = []
        if max_age > 100: milestones.append("💀 Conquered Death (Age > 100)")
        if max_energy > 200: milestones.append("🔋 Singularity Energy (E > 200)")
        if st.session_state.max_generation > 50: milestones.append("🧬 Deep Evolution (Gen > 50)")
        if len(st.session_state.gene_pool) > 40: milestones.append("📚 Genetic Library Full")
        
        # Determine Civ Type
        civ_type = "Type 0: Scavengers"
        if "Conquered Death" in str(milestones): civ_type = "Type I: Alchemists"
        if "Singularity Energy" in str(milestones): civ_type = "Type II: Gods"
        
        st.metric("Civilization Scale", civ_type)
        st.metric("State Space Explored", f"10^-{202 - len(st.session_state.event_log)}%") 
        
        st.write("**Discovered Milestones:**")
        for m in milestones:
            st.code(m)
            
    with col_omega2:
        st.markdown("### 🔬 Micro-Analysis (Per-Agent Metrics)")
        
        # Generate the "100+ Metrics" Table
        # We will generate a dense dataframe of agent stats
        agent_data = []
        for agent in st.session_state.world.agents.values():
            # Derive Advanced Metrics from nothing
            
            # 1. "IQ" (Variance of Vector / Age) -> Complexity of thought
            iq_score = 0.0
            if agent.last_vector is not None:
                iq_score = float(torch.std(agent.last_vector)) * 100.0
                
            # 2. "Love" (Altruism Potential)
            # If their vector has high component in "Field Harmonics" (Index 4 of effect, but we only have 21 inputs)
            # We treat the MEAN of the vector as a proxy for "Energy Output"
            love_score = 0.0
            if agent.last_vector is not None:
                 love_score = float(torch.mean(agent.last_vector))
                 
            # 3. "Bio-Hack" (Learning Rate / Plasticity)
            # We don't have direct access to plasticity gate in the agent object easily without running it
            # But we track "Thoughts Had"
            neuro_plasticity = (agent.thoughts_had / max(1, agent.age)) * 100.0
            
            agent_data.append({
                "ID": agent.id[:6],
                "Gen": agent.generation,
                "Age": agent.age,
                "Energy": f"{agent.energy:.2f}",
                "IQ (Causal)": f"{iq_score:.4f}",
                "Love (Field)": f"{love_score:.4f}",
                "Bio-Hack %": f"{neuro_plasticity:.2f}%",
                "Entropy (S)": f"{np.log(agent.age + 1):.4f}",
                "Reflexes": agent.reflexes_used,
                "Thoughts": agent.thoughts_had
            })
            
        if agent_data:
            df_agents = pd.DataFrame(agent_data)
            st.dataframe(df_agents, use_container_width=True, height=300)
        else:
            st.warning("No Agents Alive to Analyze.")

# ============================================================
# 🔄 3. LOOP RESTART
# ============================================================
if st.session_state.running:
    time.sleep(0.01) 
    st.rerun()
