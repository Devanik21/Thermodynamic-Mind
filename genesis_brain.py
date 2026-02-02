import torch
import torch.nn as nn
import torch.optim as optim
import random
import uuid
import copy

# ============================================================
# 🧠 THERMODYNAMIC CONSTANTS
# ============================================================
COST_REFLEX = 0.1      
COST_THOUGHT = 5.0     
LEARNING_THRESHOLD = 0.6 

# ============================================================
# 🕸️ THE CAUSAL SUBSTRATE (Recurrent Neural Network)
# ============================================================
class CausalBrain(nn.Module):
    """
    A Recurrent Brain (GRU).
    Input: Sensory Vector (16) + Energy State (1) = 17
    Hidden: 32 (Short-term Memory / Context)
    Output: Action (6) + Plasticity (1)
    """
    def __init__(self, input_dim=16, hidden_dim=32, output_dim=6):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Feature Extraction
        self.encoder = nn.Linear(input_dim + 1, hidden_dim)
        
        # The Core (GRU Cell) - Explicit Time Awareness
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        
        # Decoders
        self.actor = nn.Linear(hidden_dim, output_dim) # Action
        self.critic = nn.Linear(hidden_dim, 1) # Plasticity Gate
        
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x, energy_level, hidden_state):
        # 1. Preprocess
        e = torch.tensor([energy_level / 100.0]).float()
        if x.dim() == 1:
            x = torch.cat([x, e], dim=0).unsqueeze(0) # [1, 17]
        else:
            e = e.unsqueeze(0).expand(x.size(0), -1)
            x = torch.cat([x, e], dim=1)
        
        if hidden_state is None:
            hidden_state = torch.zeros(x.size(0), self.hidden_dim)
            
        # 2. Encode
        features = self.relu(self.encoder(x))
        
        # 3. Time Step (Recurrence)
        new_hidden = self.gru(features, hidden_state)
        
        # 4. Decode
        action_logits = self.actor(new_hidden)
        plasticity_gate = self.sigmoid(self.critic(new_hidden))
        
        return action_logits, plasticity_gate, new_hidden

# ============================================================
# 🧬 THE ADAPTIVE AGENT
# ============================================================
class GenesisAgent:
    def __init__(self, x, y, uid=None, genome=None, generation=0):
        self.id = uid if uid else str(uuid.uuid4())[:8]
        self.x = x
        self.y = y
        self.energy = 50.0 
        self.age = 0
        self.generation = generation
        
        # The Causal Brain
        self.brain = CausalBrain()
        
        # GENETIC INHERITANCE
        if genome:
            self.brain.load_state_dict(genome)
            self._mutate() # Evolution requires variation
            
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)
        
        # Memory State (The "Mind")
        self.hidden_state = None
        
        # RL Buffer
        self.current_log_prob = None
        self.decided_to_learn = False
        
        # Stats
        self.thoughts_had = 0      
        self.reflexes_used = 0    
    
    def _mutate(self, rate=0.02):
        """Randomly alters synaptic weights (Darwinian Drift)"""
        with torch.no_grad():
            for param in self.brain.parameters():
                noise = torch.randn_like(param) * rate
                param.add_(noise)

    def decide(self, signal_vector):
        """
        The Choice with Context.
        """
        self.energy -= COST_REFLEX 
        self.reflexes_used += 1
        self.age += 1 # Every decision is a moment lived
        
        # Detach hidden state 
        if self.hidden_state is not None:
            self.hidden_state = self.hidden_state.detach()

        with torch.no_grad():
             pass

        logits, plasticity_score, new_hidden = self.brain(signal_vector, self.energy, self.hidden_state)
        self.hidden_state = new_hidden 
        
        # Sample Action
        probs = torch.nn.functional.softmax(logits, dim=1) 
        distribution = torch.distributions.Categorical(probs)
        action = distribution.sample()
        
        self.current_log_prob = distribution.log_prob(action)
        self.decided_to_learn = False
        
        # Intelligent Gating: Only learn if confused AND have energy
        if plasticity_score.item() > 0.7 and self.energy > 30.0:
            self.decided_to_learn = True
        
        return action.item()

    def metabolize_outcome(self, reward):
        # Physical Reward
        if self.decided_to_learn:
            self.energy -= COST_THOUGHT
            self.thoughts_had += 1
            
            loss = -self.current_log_prob * reward
            
            # RNN Backprop 
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.brain.parameters(), 1.0) 
            self.optimizer.step()
            
            return True 
            
        return False

    def get_genome(self):
        """Returns the crystallized weight matrix for reproduction."""
        return copy.deepcopy(self.brain.state_dict())
