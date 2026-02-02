import numpy as np
import torch
import random

# ============================================================
# 🌌 ZERO POINT PHYSICS CONSTANTS
# ============================================================
GRID_SIZE = 64
SIGNAL_DIM = 16  # The "Spectrum" of reality (Abstract Vectors)
MAX_ENERGY = 100.0
METABOLIC_COST = 0.5  # Cost of just existing per tick

# ============================================================
# ⚛️ ENTITIES (The Objects of Reality)
# ============================================================
class Entity:
    """Base class for anything that exists in the grid."""
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.type = entity_type  # 'agent', 'food', 'hazard'
        self.exists = True

class Resource(Entity):
    """Energy packets (Food/Hazards) emitted as Abstract Vectors."""
    def __init__(self, x, y, nutrition):
        super().__init__(x, y, 'resource')
        self.nutrition = nutrition
        
        # 🧬 THE SIGNAL: Agents see this, not "Apple"
        # Food = High frequency in first half, Hazard = High in second half
        # But we add Noise so they MUST learn general features.
        self.signal = torch.zeros(SIGNAL_DIM)
        
        if nutrition > 0:
            # "Edible" Signal Pattern (Positive High)
            self.signal[:8] = torch.rand(8) * 0.8 + 0.2 
            self.signal[8:] = torch.rand(8) * 0.1
        else:
            # "Toxic" Signal Pattern (Negative/Warning High)
            self.signal[:8] = torch.rand(8) * 0.1
            self.signal[8:] = torch.rand(8) * 0.8 + 0.2
            
        # Normalize signal (Physically conserved)
        self.signal = torch.nn.functional.normalize(self.signal, dim=0)

# ============================================================
# 🌍 THE WORLD (The Simulation Container)
# ============================================================
class GenesisWorld:
    """The Grid Container. Handles physics, collision, and sensory projection."""
    def __init__(self, size=GRID_SIZE):
        self.size = size
        self.grid = {} # {(x,y): Entity} - Sparse storage
        self.agents = {} # {id: AgentObj} - External reference
        self.time_step = 0
        self.total_energy_consumed = 0.0
        
    def spawn_resource(self):
        """Randomly places a resource (Food or Poison)."""
        x, y = random.randint(0, self.size-1), random.randint(0, self.size-1)
        if (x, y) not in self.grid:
            # 80% Food, 20% Poison (To force learning discrimination)
            if random.random() < 0.8:
                res = Resource(x, y, nutrition=20.0) # Calories
            else:
                res = Resource(x, y, nutrition=-50.0) # Poison
            self.grid[(x, y)] = res

    def get_sensory_input(self, agent):
        """
        Project the local reality into the Agent's sensors.
        Returns: Tensor [Signal_Dim]
        Current Logic: The agent actively 'scans' the cell it is standing on.
        """
        # 1. Proprioception (Internal State) - handled by Agent Class
        
        # 2. Exteroception (External World)
        # Check current cell
        loc = (agent.x, agent.y)
        if loc in self.grid:
            entity = self.grid[loc]
            if isinstance(entity, Resource):
                # Agents see the object they are standing on
                return entity.signal
        
        # If nothing, return "Void" signal (Gaussian Noise)
        return torch.randn(SIGNAL_DIM) * 0.05

    def move_agent(self, agent, action_idx):
        """
        Physics of movement.
        0: Stay, 1: Up, 2: Down, 3: Left, 4: Right
        """
        dx, dy = 0, 0
        if action_idx == 1: dy = -1
        elif action_idx == 2: dy = 1
        elif action_idx == 3: dx = -1
        elif action_idx == 4: dx = 1
        
        # Toroidal Geometry (World wraps around like Pac-Man)
        new_x = (agent.x + dx) % self.size
        new_y = (agent.y + dy) % self.size
        
        agent.x, agent.y = new_x, new_y

    def attempt_eat(self, agent):
        """Interacts with the object at current location."""
        loc = (agent.x, agent.y)
        reward = 0.0
        
        if loc in self.grid:
            entity = self.grid[loc]
            if isinstance(entity, Resource):
                # Consume it
                energy_gain = entity.nutrition
                agent.energy += energy_gain
                agent.energy = min(agent.energy, MAX_ENERGY)
                
                # Update World Stats
                if energy_gain > 0:
                    self.total_energy_consumed += energy_gain
                
                # Remove resource
                del self.grid[loc]
                return energy_gain # Real Physical Reward (Calories)
                
        return -1.0 # Wasted effort penalty

    def step(self):
        """Advances the laws of physics by one tick."""
        self.time_step += 1
        
        # Resource Regeneration (Entropy reverses locally)
        if self.time_step % 2 == 0:
            for _ in range(5):
                self.spawn_resource()
