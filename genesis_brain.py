import torch
import torch.nn as nn
import torch.optim as optim
import random
import uuid
import copy
import math

# ============================================================
# 🧠 THERMODYNAMIC CONSTANTS
# ============================================================
COST_REFLEX = 0.1      
COST_THOUGHT = 2.0  
LEARNING_THRESHOLD = 0.4 

# ============================================================
# 🕸️ THE CAUSAL SUBSTRATE (Recurrent Neural Network)
# ============================================================
class CausalBrain(nn.Module):
    """
    A Recurrent Brain (GRU) adapted for Quantum Physics.
    Input: Sensory(16) + Energy(1) + Grid(4) + Smell(1) = 22
    Hidden: 32 (Context)
    Output: Reality(21) + Emit(1) + Mate(1) = 23 (+ Plasticity Gate)
    """
    def __init__(self, input_dim=16, hidden_dim=32, output_dim=21):
        super().__init__()
        self.hidden_dim = hidden_dim
        
        # Feature Extraction
        # Input dim is 16. +1 Energy + 4 Spatial + 1 Smell = +6 total additional inputs
        self.encoder = nn.Linear(input_dim + 6, hidden_dim)
        
        # The Core (GRU Cell)
        self.gru = nn.GRUCell(hidden_dim, hidden_dim)
        
        # Decoders
        # Output is 21 (Reality) + 1 (Emit Strength) + 1 (Mate Desire) = 23
        self.actor = nn.Linear(hidden_dim, output_dim + 2) 
        self.critic = nn.Linear(hidden_dim, 1) 
        
        # Free Energy Predictor
        self.predictor = nn.Linear(hidden_dim, 1) 
        
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        self.tanh = nn.Tanh() 
        
    def forward(self, x, energy_level, hidden_state):
        # 1. Preprocess
        e = torch.tensor([energy_level / 100.0]).float()
        
        # If x is 1D:
        if x.dim() == 1:
            # x is [21] (16 Sig + 4 Grid + 1 Smell)
            features_in = torch.cat([x, e], dim=0).unsqueeze(0)
        else:
            # x is [B, 21]
            e = e.unsqueeze(0).expand(x.size(0), -1)
            features_in = torch.cat([x, e], dim=1)
        
        if hidden_state is None:
            hidden_state = torch.zeros(features_in.size(0), self.hidden_dim)
            
        # 2. Encode
        linear_out = self.encoder(features_in)
        features = self.relu(linear_out)
        
        # Lifetime Plasticity (Oja's Rule)
        if self.training: 
            with torch.no_grad():
                eta = 0.001
                y = features.unsqueeze(2) 
                _x = features_in.unsqueeze(1) 
                w = self.encoder.weight
                hebbian = torch.bmm(y, _x)
                decay = (y ** 2) * w.unsqueeze(0)
                delta_w = torch.mean(hebbian - decay, dim=0)
                self.encoder.weight += eta * delta_w

        # 3. Time Step
        new_hidden = self.gru(features, hidden_state)
        
        # 4. Decode
        raw_output = self.actor(new_hidden)
        
        # Split Output: 
        # First 21: Reality Vector
        # 21: Emit Strength
        # 22: Mate Desire
        action_vector = self.tanh(raw_output[:, :21]) 
        emit_strength = self.sigmoid(raw_output[:, 21]) # 0 to 1
        mate_desire = self.sigmoid(raw_output[:, 22]) # 0 to 1
        
        plasticity_gate = self.sigmoid(self.critic(new_hidden))
        prediction = self.predictor(new_hidden)
        
        return action_vector, emit_strength, mate_desire, plasticity_gate, new_hidden, prediction

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
            # 🔮 MIGRATION LOGIC (Phase 14 Compatibility)
            # Old Encoder (Phase 13): [32, 22] (Matches Phase 14 inputs)
            # Old Actor (Phase 13): [22, 32]
            # New Actor (Phase 14): [23, 32]
            
            # 1. ACTOR MIGRATION
            if 'actor.weight' in genome:
                old_act = genome['actor.weight']
                old_dim = old_act.shape[0]
                
                # If coming from Phase 13 (22 outputs)
                if old_dim == 22:
                    new_act = self.brain.actor.weight.clone()
                    # Copy Reality (21) + Emit (1) = 22
                    new_act[:22, :] = old_act
                    # Last row (Mate) is random
                    genome['actor.weight'] = new_act
                    
                    if 'actor.bias' in genome:
                        old_bias = genome['actor.bias']
                        new_bias = self.brain.actor.bias.clone()
                        new_bias[:22] = old_bias
                        genome['actor.bias'] = new_bias
                        
            # (Encoder is compatible from Phase 13 to 14, both use 22 inputs)

            try:
                self.brain.load_state_dict(genome, strict=False)
            except Exception as e:
                pass
            
            self._mutate() 
            
        self.optimizer = optim.Adam(self.brain.parameters(), lr=0.005)

        # 🌐 PHASE 12: "GRID CELL" UPGRADE (Spatial Resonance)
        fx = (self.x / 40.0) * (2 * 3.14159)
        fy = (self.y / 40.0) * (2 * 3.14159)
        
        self.grid_embedding = torch.tensor([
            math.sin(fx), math.cos(fx), 
            math.sin(fy), math.cos(fy)
        ])
        
        self.hidden_state = None 
        self.last_vector = None 
        self.last_prediction = None 
        self.decided_to_learn = False 
        
        self.reflexes_used = 0
        self.thoughts_had = 0

    def _mutate(self, mutation_rate=0.05, mutation_strength=0.1):
        for param in self.brain.parameters():
            if len(param.shape) > 1: 
                if random.random() < mutation_rate:
                    with torch.no_grad():
                        noise = torch.randn(param.shape) * mutation_strength
                        param.add_(noise)

    def decide(self, signal_vector, smell_intensity=0.0):
        """
        The Choice: Outputting the Reality Vector.
        """
        self.energy -= COST_REFLEX 
        self.reflexes_used += 1
        self.age += 1 
        
        # 🛡️ GRAPH ISOLATION
        if self.hidden_state is not None:
            self.hidden_state = self.hidden_state.detach().clone()

        # 🌐 GRID CELL UPDATE
        fx = (self.x / 40.0) * (2 * 3.14159)
        fy = (self.y / 40.0) * (2 * 3.14159)
        grid_embedding = torch.tensor([
            math.sin(fx), math.cos(fx), math.sin(fy), math.cos(fy)
        ])
        
        # 🧪 SMELL INPUT
        smell_tensor = torch.tensor([float(smell_intensity)])
        
        # Concatenate: Signal(16) + Grid(4) + Smell(1) = 21 (Brain adds Energy to make 22)
        total_input = torch.cat([signal_vector, grid_embedding, smell_tensor], dim=0)

        # Forward Pass
        action_vector, emit_tensor, mate_tensor, plasticity_score, new_hidden, prediction = self.brain(total_input, self.energy, self.hidden_state)
        self.hidden_state = new_hidden 
        
        # Exploration Noise
        exploration_noise = torch.randn_like(action_vector) * 0.3
        final_vector = torch.clamp(action_vector + exploration_noise, -1.0, 1.0)
        
        self.last_vector = final_vector
        self.last_prediction = prediction 
        self.decided_to_learn = False 
        
        # Intelligent Gating
        if plasticity_score.item() > LEARNING_THRESHOLD and self.energy > 30.0:
            self.decided_to_learn = True
        
        # Convert outputs to scalar
        emit_value = emit_tensor.item()
        mate_value = mate_tensor.item()
        
        return final_vector, emit_value, mate_value

    def metabolize_outcome(self, reward):
        # Physical Reward
        if self.decided_to_learn and self.last_vector is not None and self.last_prediction is not None:
            self.energy -= COST_THOUGHT
            self.thoughts_had += 1
            
            # 🔮 SCHRÖDINGER'S REWARD (Free Energy Principle)
            prediction_val = self.last_prediction.item()
            surprise = abs(prediction_val - reward)
            effective_reward = reward - surprise
            
            # Target Vector Logic
            target = self.last_vector.detach().clone()
            if effective_reward < 0:
                target = -target 
                
            loss_actor = nn.MSELoss()(self.last_vector, target) * abs(effective_reward)
            
            target_pred = torch.tensor([reward], dtype=torch.float32)
            loss_predictor = nn.MSELoss()(self.last_prediction.squeeze(), target_pred)
            
            total_loss = loss_actor + loss_predictor
            
            self.optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.brain.parameters(), 1.0) 
            self.optimizer.step()
            
            self.last_vector = None
            self.last_prediction = None
            return True 
            
        return False
    
    def get_genome(self):
        return copy.deepcopy(self.brain.state_dict())
