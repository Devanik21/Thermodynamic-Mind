import numpy as np
import torch
import random
import math

# ============================================================
# 🌌 DYNAMIC PHYSICS CONSTANTS
# ============================================================
GRID_SIZE = 40
SIGNAL_DIM = 16
MAX_ENERGY = 100.0
METABOLIC_COST = 0.5 

# QUANTUM SEASONS (The Chaos Factor)
SEASON_LENGTH = 50  # Rules flip every 50 ticks (Fast fluctuation)

# ============================================================
# ⚛️ ENTITIES
# ============================================================
class Entity:
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.type = entity_type
        self.exists = True

class Resource(Entity):
    """
    Polymorphic Resource. 
    Its 'Truth' (Nutrition) depends on the current Quantum Season,
    but its 'Signal' remains constant. This forces the agent to context-switch.
    """
    def __init__(self, x, y, is_type_a=True):
        super().__init__(x, y, 'resource')
        self.is_type_a = is_type_a # Type A vs Type B
        
        self.signal = torch.zeros(SIGNAL_DIM)
        # Signal is intrinsic to the object (Red vs Blue)
        if is_type_a:
            # "Red" Signal
            self.signal[:8] = torch.rand(8) * 0.8 + 0.2
            self.signal[8:] = torch.rand(8) * 0.1
        else:
            # "Blue" Signal
            self.signal[:8] = torch.rand(8) * 0.1
            self.signal[8:] = torch.rand(8) * 0.8 + 0.2
            
        self.signal = torch.nn.functional.normalize(self.signal, dim=0)

    def get_nutrition(self, current_season):
        """
        The Schrödinger Evaluation:
        Season 0: Red=Food, Blue=Poison
        Season 1: Red=Poison, Blue=Food
        """
        base_val = 20.0
        
        if current_season % 2 == 0:
            return base_val if self.is_type_a else -base_val * 2.0
        else:
            return -base_val * 2.0 if self.is_type_a else base_val

# ============================================================
# 🌍 THE QUANTUM WORLD
# ============================================================
class GenesisWorld:
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = {} 
        self.agents = {} 
        self.time_step = 0
        self.total_energy_consumed = 0.0
        
        self.current_season = 0
        self.season_timer = 0
        
    def spawn_resource(self):
        """Places a localized potential."""
        x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
        if (x, y) not in self.grid:
            # Randomly Type A (Red) or Type B (Blue)
            # 50/50 chance, unlike static world
            is_type_a = random.random() < 0.5
            res = Resource(x, y, is_type_a)
            self.grid[(x, y)] = res

    def get_sensory_input(self, agent):
        """Projects reality to agent + Social Signals."""
        # 1. Local Signal (What am I standing on?)
        loc = (agent.x, agent.y)
        local_signal = torch.zeros(SIGNAL_DIM)
        
        if loc in self.grid:
            local_signal = self.grid[loc].signal
        else:
            local_signal = torch.randn(SIGNAL_DIM) * 0.05
            
        return local_signal

    def move_agent(self, agent, action_idx):
        dx, dy = 0, 0
        if action_idx == 1: dy = -1
        elif action_idx == 2: dy = 1
        elif action_idx == 3: dx = -1
        elif action_idx == 4: dx = 1
        
        new_x = (agent.x + dx) % self.size
        new_y = (agent.y + dy) % self.size
        agent.x, agent.y = new_x, new_y

    def attempt_eat(self, agent):
        loc = (agent.x, agent.y)
        if loc in self.grid:
            entity = self.grid[loc]
            if isinstance(entity, Resource):
                # Critical: Evaluate based on CURRENT SEASON
                energy_gain = entity.get_nutrition(self.current_season)
                
                agent.energy += energy_gain
                agent.energy = min(agent.energy, MAX_ENERGY)
                
                if energy_gain > 0:
                    self.total_energy_consumed += energy_gain
                
                del self.grid[loc]
                return energy_gain 
        return -1.0 

    def step(self):
        """Advances time and Quantum Seasons."""
        self.time_step += 1
        self.season_timer += 1
        
        # QUANTUM FLIP
        if self.season_timer >= SEASON_LENGTH:
            self.current_season += 1
            self.season_timer = 0
            # Entropy injection: massive resource respawn to confuse agents
            for _ in range(20):
                self.spawn_resource()
        
        # Standard Regen
        if self.time_step % 2 == 0:
            for _ in range(5):
                self.spawn_resource()
