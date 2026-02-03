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
# ⚙️ SYSTEM CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Zero Point Genesis", page_icon="⚛️")

# Custom CSS for "Comfortable UI"
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #0e1117;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #262730;
        border-bottom: 2px solid #4CAF50;
    }
    .metric-card {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🛠️ INITIALIZATION HOOKS
# ============================================================
def init_system():
    if "world" not in st.session_state:
        st.session_state.world = GenesisWorld(size=40)
        for _ in range(64):
            x, y = np.random.randint(0, 40), np.random.randint(0, 40)
            agent = GenesisAgent(x, y)
            st.session_state.world.agents[agent.id] = agent
        for _ in range(150):
            st.session_state.world.spawn_resource()

    if "stats_history" not in st.session_state: st.session_state.stats_history = []
    if "gene_pool" not in st.session_state: st.session_state.gene_pool = [] 
    if "max_generation" not in st.session_state: st.session_state.max_generation = 0
    if "running" not in st.session_state: st.session_state.running = False
    if "event_log" not in st.session_state: st.session_state.event_log = []

init_system()

# ============================================================
# 🔄 SIMULATION LOGIC LOOP
# ============================================================
def update_simulation():
    if not st.session_state.running:
        return

    world = st.session_state.world
    world.step()
    
    current_thoughts = 0
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
            
        signal = world.get_local_signal(agent.x, agent.y)
        reality_vector_tensor = agent.decide(signal) 
        flux, log_text = world.resolve_quantum_state(agent, reality_vector_tensor)
        
        if flux > 0: total_pos_flux += flux
        elif flux < 0: total_neg_flux += abs(flux)
            
        learned = agent.metabolize_outcome(flux)
        
        if "IDLE" not in log_text and "MOVE" not in log_text:
             events_this_tick.append({
                "Tick": world.time_step,
                "Agent": agent.id,
                "Gen": agent.generation,
                "Event": f"{log_text} ({flux:.1f}E)",
                "Vector": reality_vector_tensor.tolist()[0]
            })
            
        if learned: current_thoughts += 1
        agent.energy -= 0.5 
        
        # 🧬 MITOSIS (The unlocking of "No Limit")
        # If they hoard energy, they MUST reproduce.
        if agent.energy > 100.0:
            agent.energy -= 50.0 # Cost of birth
            # Create offspring near parent
            off_x = (agent.x + np.random.randint(-1, 2)) % 40
            off_y = (agent.y + np.random.randint(-1, 2)) % 40
            
            # Inheritance
            child_genome = agent.get_genome()
            child = GenesisAgent(off_x, off_y, genome=child_genome, generation=agent.generation + 1)
            
            # 100% Entropy Injection for Child (Mutation)
            child._mutate(rate=0.2) # High mutation for faster evolution
            
            # Add to world immediately
            world.agents[child.id] = child
            events_this_tick.append({
                "Tick": world.time_step,
                "Agent": agent.id,
                "Gen": agent.generation,
                "Event": "🐣 MITOSIS",
                "Vector": reality_vector_tensor.tolist()[0]
            })
        
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
        
    # Failsafe: only restart if TRULY extinct
    if len(world.agents) < 4:
        x, y = np.random.randint(0, 40), np.random.randint(0, 40)
        genome = None
        gen = 0
        if st.session_state.gene_pool:
            genome = random.choice(st.session_state.gene_pool)
            gen = st.session_state.max_generation
        new_agent = GenesisAgent(x, y, genome=genome, generation=gen)
        world.agents[new_agent.id] = new_agent
        
    # Update Stats
        "tick": world.time_step,
        "population": len(world.agents),
        "thoughts": current_thoughts,
        "avg_energy": np.mean([a.energy for a in world.agents.values()]) if world.agents else 0,
        "pos_flux": total_pos_flux,
        "neg_flux": total_neg_flux
    
    st.session_state.stats_history.append(stats)
    if len(st.session_state.stats_history) > 200:
        st.session_state.stats_history.pop(0)
        
    for e in events_this_tick:
        st.session_state.event_log.insert(0, e) 
    st.session_state.event_log = st.session_state.event_log[:20]

update_simulation()

# ============================================================
# 🖥️ UI RENDERER
# ============================================================
st.title("⚛️ Zero Point Genesis: 21-Dimensional Sandbox")

# --- HEADER FRAGMENT ---
with st.container():
    curr_season_idx = st.session_state.world.current_season
    season_mode = "SUMMER 🌞" if curr_season_idx % 2 == 0 else "WINTER ❄️"
    season_color = "#ffbd45" if curr_season_idx % 2 == 0 else "#45b6fe"

    col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1, 1, 1])
    with col_h1:
        st.markdown(f"### Orbit: <span style='color:{season_color}'>{season_mode}</span>", unsafe_allow_html=True)
        st.caption(f"Gene Pool: {len(st.session_state.gene_pool)} | Max Gen: {st.session_state.max_generation}")
    with col_h2:
        if st.button("▶️ TOGGLE SIMULATION", use_container_width=True, type="primary" if not st.session_state.running else "secondary"):
            st.session_state.running = not st.session_state.running
    with col_h3:
        if st.button("♻️ RESET WORLD", use_container_width=True):
            st.session_state.world = GenesisWorld(size=40)
            st.session_state.stats_history = []
            st.session_state.gene_pool = []
            st.session_state.max_generation = 0
            st.rerun()
    with col_h4:
        # Optimized Report Generator
        @st.cache_data
        def generate_report_cached(stats, genes, events):
            stats_json = json.dumps(stats, indent=2)
            gene_json = json.dumps(genes)
            events_json = json.dumps(events, indent=2)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("stats.json", stats_json)
                zf.writestr("genes.json", gene_json)
                zf.writestr("events.json", events_json)
            return zip_buffer.getvalue()

        # We convert complex objects to simpler ones for caching if needed, but for now passing session state contents directly
        # To avoid caching issues with mutable objects, we clone them or just run generate_report on click.
        # Streamlit's new button callback pattern is cleaner.
        
        encoded_pool_clean = [{k: v.cpu().tolist() for k, v in g.items()} for g in st.session_state.gene_pool]
        
        st.download_button(
            "💾 EXPORT DATA", 
            generate_report_cached(st.session_state.stats_history, encoded_pool_clean, st.session_state.event_log), 
            "genesis_data.zip", 
            "application/zip", 
            use_container_width=True
        )

# --- MAIN TABS FRAGMENT ---
tab_macro, tab_micro, tab_omega = st.tabs(["🔭 OBSERVATION DECK", "🧬 QUANTUM SPECTROGRAM", "Ω OMEGA TELEMETRY"])

with tab_macro:
    if st.session_state.stats_history:
        df = pd.DataFrame(st.session_state.stats_history)
        
        # Row 1: Graphs
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['tick'], y=df['population'], name="Survivors", line=dict(color='#00ffa3')))
            fig.add_trace(go.Scatter(x=df['tick'], y=df['thoughts'], name="Plasticity Events", line=dict(color='#ff4b4b')))
            fig.update_layout(title="Evolutionary Trajectory", height=250, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
        with col_g2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df['tick'], y=df['pos_flux'], name="Positive Inventions", line=dict(color='yellow'), fill='tozeroy'))
            fig2.add_trace(go.Scatter(x=df['tick'], y=df['neg_flux'], name="Negative Disasters", line=dict(color='red'), fill='tozeroy'))
            fig2.update_layout(title="The Moral Compass (Efficiency vs Chaos)", height=250, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)
            
        # Row 2: Map
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
        fig_map.update_layout(height=500, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("System Initializing...")

with tab_micro:
    col_vis, col_log = st.columns([2, 1])
    with col_vis:
        st.markdown("### 🧠 The Mind Cloud")
        if st.session_state.world.agents:
            sample_agents = random.sample(list(st.session_state.world.agents.values()), min(len(st.session_state.world.agents), 15))
            vectors = []
            labels = []
            for a in sample_agents:
                if a.last_vector is not None:
                    vectors.append(a.last_vector.tolist()[0])
                    labels.append(f"{a.id[:4]}")
            
            if vectors:
                vec_arr = np.array(vectors)
                fig_spec = px.imshow(
                    vec_arr, 
                    color_continuous_scale='Plasma', 
                    aspect='auto',
                    labels=dict(x="Dimension (0-20)", y="Agent Sample", color="Activation"),
                    title=f"Real-Time Thought Spectrum (n={len(vectors)})"
                )
                fig_spec.update_layout(height=400, margin=dict(l=0,r=0,t=30,b=0))
                st.plotly_chart(fig_spec, use_container_width=True)
        else:
            st.warning("Extinction Event. No Minds Detected.")
            
    with col_log:
        st.markdown("### ⚡ Event Stream")
        if st.session_state.event_log:
             log_df = pd.DataFrame(st.session_state.event_log)
             st.dataframe(log_df[["Agent", "Event"]], use_container_width=True, height=400)

with tab_omega:
    col_civ, col_agent = st.columns([1, 2])
    
    with col_civ:
        st.markdown("### 🏛️ Civilization Status")
        max_energy = 0
        max_age = 0
        if st.session_state.world.agents:
            max_energy = max([a.energy for a in st.session_state.world.agents.values()])
            max_age = max([a.age for a in st.session_state.world.agents.values()])
            
        milestones = []
        if max_age > 100: milestones.append("💀 Conquered Death")
        if max_energy > 200: milestones.append("🔋 Singularity Energy")
        if st.session_state.max_generation > 50: milestones.append("🧬 Deep Evolution")
        if len(st.session_state.gene_pool) > 40: milestones.append("📚 Genetic Library Full")
        
        civ_type = "Type 0: Scavengers"
        if "Conquered Death" in str(milestones): civ_type = "Type I: Alchemists"
        if "Singularity Energy" in str(milestones): civ_type = "Type II: Gods"
        
        st.metric("Civilization Scale", civ_type)
        st.metric("State Space Explored", f"10^-{202 - len(st.session_state.event_log)}%") 
        
        for m in milestones:
            st.success(m)

    with col_agent:
        st.markdown("### 🔬 100+ Metric Grid")
        agent_data = []
        for agent in st.session_state.world.agents.values():
            iq_score = 0.0
            love_score = 0.0
            if agent.last_vector is not None:
                iq_score = float(torch.std(agent.last_vector)) * 100.0
                love_score = float(torch.mean(agent.last_vector))
            
            neuro_plasticity = (agent.thoughts_had / max(1, agent.age)) * 100.0
            
            agent_data.append({
                "ID": agent.id[:6],
                "Gen": agent.generation,
                "Age": agent.age,
                "Energy": f"{agent.energy:.2f}",
                "IQ": f"{iq_score:.4f}",
                "Love": f"{love_score:.4f}",
                "Bio-Hack %": f"{neuro_plasticity:.2f}%",
                "Entropy": f"{np.log(agent.age + 1):.4f}",
                "Reflexes": agent.reflexes_used,
                "Thoughts": agent.thoughts_had
            })
            
        if agent_data:
            df_agents = pd.DataFrame(agent_data)
            st.dataframe(df_agents, use_container_width=True, height=400)

# ============================================================
# 🔄 ANIMATION LOOP
# ============================================================
if st.session_state.running:
    time.sleep(0.02) 
    st.rerun()
