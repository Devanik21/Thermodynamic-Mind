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
SEASON_LENGTH = 50 

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
    def __init__(self, x, y, is_type_a=True):
        super().__init__(x, y, 'resource')
        self.is_type_a = is_type_a 
        
        self.signal = torch.zeros(SIGNAL_DIM)
        if is_type_a:
            self.signal[:8] = torch.rand(8) * 0.8 + 0.2
            self.signal[8:] = torch.rand(8) * 0.1
        else:
            self.signal[:8] = torch.rand(8) * 0.1
            self.signal[8:] = torch.rand(8) * 0.8 + 0.2
            
        self.signal = torch.nn.functional.normalize(self.signal, dim=0)

    def get_nutrition(self, current_season):
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
            is_type_a = random.random() < 0.5
            res = Resource(x, y, is_type_a)
            self.grid[(x, y)] = res

    def move_resources(self):
        """
        BROWNIAN MOTION: Resources drift!
        This creates a dynamic, fluid-like environment.
        """
        # Snapshot keys to avoid runtime error
        keys = list(self.grid.keys())
        for loc in keys:
            if random.random() < 0.1: # 10% chance to drift
                res = self.grid.pop(loc)
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                new_x = (res.x + dx) % self.size
                new_y = (res.y + dy) % self.size
                
                # Only move if empty
                if (new_x, new_y) not in self.grid:
                    res.x, res.y = new_x, new_y
                    self.grid[(new_x, new_y)] = res
                else:
                    # Bounce back
                    self.grid[loc] = res

    def get_sensory_input(self, agent):
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
            # Entropy injection
            for _ in range(20):
                self.spawn_resource()
        
        # Standard Regen
        if self.time_step % 2 == 0:
            for _ in range(5):
                self.spawn_resource()
                
        # DYNAMIC DRIFT
        self.move_resources()
