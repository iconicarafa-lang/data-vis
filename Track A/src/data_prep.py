import os
import pandas as pd

def prepare_data():
    # Define directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print("Generating Game of Thrones Character Interaction Network dataset...")
    
    # 1. Define Nodes (Characters)
    # Factions: Stark, Lannister, Targaryen, Night's Watch, Baratheon
    nodes_data = [
        # --- House Stark & North ---
        {"Id": "Ned_Stark", "Label": "Ned Stark", "Faction": "House Stark"},
        {"Id": "Catelyn_Stark", "Label": "Catelyn Stark", "Faction": "House Stark"},
        {"Id": "Robb_Stark", "Label": "Robb Stark", "Faction": "House Stark"},
        {"Id": "Sansa_Stark", "Label": "Sansa Stark", "Faction": "House Stark"},
        {"Id": "Arya_Stark", "Label": "Arya Stark", "Faction": "House Stark"},
        {"Id": "Bran_Stark", "Label": "Bran Stark", "Faction": "House Stark"},
        {"Id": "Hodor", "Label": "Hodor", "Faction": "House Stark"},
        {"Id": "The_Hound", "Label": "The Hound (Sandor Clegane)", "Faction": "Independent"},
        
        # --- House Lannister & Allies ---
        {"Id": "Tyrion_Lannister", "Label": "Tyrion Lannister", "Faction": "House Lannister"},
        {"Id": "Cersei_Lannister", "Label": "Cersei Lannister", "Faction": "House Lannister"},
        {"Id": "Jaime_Lannister", "Label": "Jaime Lannister", "Faction": "House Lannister"},
        {"Id": "Tywin_Lannister", "Label": "Tywin Lannister", "Faction": "House Lannister"},
        {"Id": "Joffrey_Baratheon", "Label": "Joffrey Baratheon", "Faction": "House Lannister"},
        {"Id": "Bronn", "Label": "Bronn", "Faction": "House Lannister"},
        {"Id": "Shae", "Label": "Shae", "Faction": "House Lannister"},
        {"Id": "The_Mountain", "Label": "The Mountain (Gregor Clegane)", "Faction": "House Lannister"},
        {"Id": "Littlefinger", "Label": "Petyr Baelish (Littlefinger)", "Faction": "Independent"},
        {"Id": "Varys", "Label": "Varys (The Spider)", "Faction": "Independent"},
        
        # --- House Targaryen & Essos ---
        {"Id": "Daenerys_Targaryen", "Label": "Daenerys Targaryen", "Faction": "House Targaryen"},
        {"Id": "Jorah_Mormont", "Label": "Jorah Mormont", "Faction": "House Targaryen"},
        {"Id": "Khal_Drogo", "Label": "Khal Drogo", "Faction": "House Targaryen"},
        {"Id": "Missandei", "Label": "Missandei", "Faction": "House Targaryen"},
        {"Id": "Grey_Worm", "Label": "Grey Worm", "Faction": "House Targaryen"},
        {"Id": "Daario_Naharis", "Label": "Daario Naharis", "Faction": "House Targaryen"},
        {"Id": "Barristan_Selmy", "Label": "Barristan Selmy", "Faction": "House Targaryen"},
        
        # --- The Night's Watch & Beyond ---
        {"Id": "Jon_Snow", "Label": "Jon Snow", "Faction": "Night's Watch"},
        {"Id": "Samwell_Tarly", "Label": "Samwell Tarly", "Faction": "Night's Watch"},
        {"Id": "Jeor_Mormont", "Label": "Jeor Mormont", "Faction": "Night's Watch"},
        {"Id": "Maester_Aemon", "Label": "Maester Aemon", "Faction": "Night's Watch"},
        {"Id": "Ygritte", "Label": "Ygritte", "Faction": "Wildlings"},
        {"Id": "Tormund", "Label": "Tormund Giantsbane", "Faction": "Wildlings"},
        {"Id": "Mance_Rayder", "Label": "Mance Rayder", "Faction": "Wildlings"},
        {"Id": "Gilly", "Label": "Gilly", "Faction": "Wildlings"},
        
        # --- House Baratheon & Dragonstone ---
        {"Id": "Stannis_Baratheon", "Label": "Stannis Baratheon", "Faction": "House Baratheon"},
        {"Id": "Melisandre", "Label": "Melisandre", "Faction": "House Baratheon"},
        {"Id": "Davos_Seaworth", "Label": "Davos Seaworth", "Faction": "House Baratheon"},
        {"Id": "Renly_Baratheon", "Label": "Renly Baratheon", "Faction": "House Baratheon"},
        {"Id": "Robert_Baratheon", "Label": "Robert Baratheon", "Faction": "House Baratheon"},
        {"Id": "Brienne_of_Tarth", "Label": "Brienne of Tarth", "Faction": "Independent"}
    ]
    
    # Create DataFrame and save
    df_nodes = pd.DataFrame(nodes_data)
    nodes_file = os.path.join(data_dir, 'nodes.csv')
    df_nodes.to_csv(nodes_file, index=False)
    print(f"Saved {len(df_nodes)} nodes to {nodes_file}")

    # 2. Define Edges (Interactions & Dialogue Co-occurrence)
    # Weights define the strength of the tie (1 to 10 scale)
    edges_data = [
        # --- House Stark Core ---
        {"Source": "Ned_Stark", "Target": "Catelyn_Stark", "Weight": 8},
        {"Source": "Ned_Stark", "Target": "Robb_Stark", "Weight": 6},
        {"Source": "Ned_Stark", "Target": "Sansa_Stark", "Weight": 7},
        {"Source": "Ned_Stark", "Target": "Arya_Stark", "Weight": 8},
        {"Source": "Ned_Stark", "Target": "Bran_Stark", "Weight": 6},
        {"Source": "Ned_Stark", "Target": "Jon_Snow", "Weight": 7},
        {"Source": "Ned_Stark", "Target": "Robert_Baratheon", "Weight": 9},
        {"Source": "Ned_Stark", "Target": "Cersei_Lannister", "Weight": 6},
        {"Source": "Ned_Stark", "Target": "Littlefinger", "Weight": 5},
        
        {"Source": "Catelyn_Stark", "Target": "Robb_Stark", "Weight": 8},
        {"Source": "Catelyn_Stark", "Target": "Bran_Stark", "Weight": 5},
        {"Source": "Catelyn_Stark", "Target": "Sansa_Stark", "Weight": 4},
        {"Source": "Catelyn_Stark", "Target": "Brienne_of_Tarth", "Weight": 7},
        {"Source": "Catelyn_Stark", "Target": "Tyrion_Lannister", "Weight": 6},
        
        {"Source": "Robb_Stark", "Target": "Bran_Stark", "Weight": 5},
        {"Source": "Robb_Stark", "Target": "Jon_Snow", "Weight": 5},
        
        {"Source": "Sansa_Stark", "Target": "Arya_Stark", "Weight": 6},
        {"Source": "Sansa_Stark", "Target": "Joffrey_Baratheon", "Weight": 8},
        {"Source": "Sansa_Stark", "Target": "Cersei_Lannister", "Weight": 7},
        {"Source": "Sansa_Stark", "Target": "Tyrion_Lannister", "Weight": 7},
        {"Source": "Sansa_Stark", "Target": "Littlefinger", "Weight": 9},
        {"Source": "Sansa_Stark", "Target": "The_Hound", "Weight": 6},
        {"Source": "Sansa_Stark", "Target": "Brienne_of_Tarth", "Weight": 8},
        
        {"Source": "Arya_Stark", "Target": "The_Hound", "Weight": 9},
        {"Source": "Arya_Stark", "Target": "Brienne_of_Tarth", "Weight": 5},
        {"Source": "Arya_Stark", "Target": "Jon_Snow", "Weight": 6},
        
        {"Source": "Bran_Stark", "Target": "Hodor", "Weight": 10},
        
        # --- House Lannister Core ---
        {"Source": "Tyrion_Lannister", "Target": "Cersei_Lannister", "Weight": 8},
        {"Source": "Tyrion_Lannister", "Target": "Jaime_Lannister", "Weight": 9},
        {"Source": "Tyrion_Lannister", "Target": "Tywin_Lannister", "Weight": 9},
        {"Source": "Tyrion_Lannister", "Target": "Joffrey_Baratheon", "Weight": 7},
        {"Source": "Tyrion_Lannister", "Target": "Bronn", "Weight": 9},
        {"Source": "Tyrion_Lannister", "Target": "Shae", "Weight": 9},
        {"Source": "Tyrion_Lannister", "Target": "Varys", "Weight": 8},
        {"Source": "Tyrion_Lannister", "Target": "Littlefinger", "Weight": 6},
        
        {"Source": "Cersei_Lannister", "Target": "Jaime_Lannister", "Weight": 10},
        {"Source": "Cersei_Lannister", "Target": "Tywin_Lannister", "Weight": 8},
        {"Source": "Cersei_Lannister", "Target": "Joffrey_Baratheon", "Weight": 9},
        {"Source": "Cersei_Lannister", "Target": "Robert_Baratheon", "Weight": 7},
        {"Source": "Cersei_Lannister", "Target": "Littlefinger", "Weight": 6},
        {"Source": "Cersei_Lannister", "Target": "Varys", "Weight": 5},
        
        {"Source": "Jaime_Lannister", "Target": "Tywin_Lannister", "Weight": 7},
        {"Source": "Jaime_Lannister", "Target": "Brienne_of_Tarth", "Weight": 9},
        {"Source": "Jaime_Lannister", "Target": "Bronn", "Weight": 6},
        
        {"Source": "Tywin_Lannister", "Target": "Joffrey_Baratheon", "Weight": 6},
        {"Source": "Tywin_Lannister", "Target": "The_Mountain", "Weight": 5},
        
        {"Source": "Joffrey_Baratheon", "Target": "The_Hound", "Weight": 5},
        
        # --- House Targaryen Core ---
        {"Source": "Daenerys_Targaryen", "Target": "Jorah_Mormont", "Weight": 9},
        {"Source": "Daenerys_Targaryen", "Target": "Khal_Drogo", "Weight": 10},
        {"Source": "Daenerys_Targaryen", "Target": "Missandei", "Weight": 9},
        {"Source": "Daenerys_Targaryen", "Target": "Grey_Worm", "Weight": 8},
        {"Source": "Daenerys_Targaryen", "Target": "Daario_Naharis", "Weight": 8},
        {"Source": "Daenerys_Targaryen", "Target": "Barristan_Selmy", "Weight": 7},
        
        {"Source": "Jorah_Mormont", "Target": "Barristan_Selmy", "Weight": 5},
        {"Source": "Missandei", "Target": "Grey_Worm", "Weight": 8},
        
        # --- Night's Watch & Beyond the Wall ---
        {"Source": "Jon_Snow", "Target": "Samwell_Tarly", "Weight": 9},
        {"Source": "Jon_Snow", "Target": "Jeor_Mormont", "Weight": 8},
        {"Source": "Jon_Snow", "Target": "Maester_Aemon", "Weight": 6},
        {"Source": "Jon_Snow", "Target": "Ygritte", "Weight": 10},
        {"Source": "Jon_Snow", "Target": "Tormund", "Weight": 8},
        {"Source": "Jon_Snow", "Target": "Mance_Rayder", "Weight": 7},
        
        {"Source": "Samwell_Tarly", "Target": "Gilly", "Weight": 9},
        {"Source": "Samwell_Tarly", "Target": "Maester_Aemon", "Weight": 7},
        {"Source": "Samwell_Tarly", "Target": "Jeor_Mormont", "Weight": 6},
        
        {"Source": "Jeor_Mormont", "Target": "Maester_Aemon", "Weight": 5},
        {"Source": "Ygritte", "Target": "Tormund", "Weight": 6},
        {"Source": "Tormund", "Target": "Mance_Rayder", "Weight": 8},
        {"Source": "Gilly", "Target": "Jeor_Mormont", "Weight": 3},
        
        # --- House Baratheon ---
        {"Source": "Stannis_Baratheon", "Target": "Melisandre", "Weight": 9},
        {"Source": "Stannis_Baratheon", "Target": "Davos_Seaworth", "Weight": 9},
        {"Source": "Stannis_Baratheon", "Target": "Renly_Baratheon", "Weight": 6},
        {"Source": "Davos_Seaworth", "Target": "Melisandre", "Weight": 6},
        {"Source": "Renly_Baratheon", "Target": "Robert_Baratheon", "Weight": 5},
        {"Source": "Renly_Baratheon", "Target": "Brienne_of_Tarth", "Weight": 8},
        
        # --- CRITICAL BRIDGES (Connecting Factions) ---
        {"Source": "Jon_Snow", "Target": "Daenerys_Targaryen", "Weight": 8},   # North <-> Essos
        {"Source": "Tyrion_Lannister", "Target": "Daenerys_Targaryen", "Weight": 7}, # Lannister/KL <-> Essos
        {"Source": "Tyrion_Lannister", "Target": "Jon_Snow", "Weight": 6},     # Lannister/KL <-> North/Night's Watch
        {"Source": "Littlefinger", "Target": "Varys", "Weight": 8},             # Schemer bridge in KL
        {"Source": "Brienne_of_Tarth", "Target": "Jaime_Lannister", "Weight": 8}, # KL <-> Stark/Baratheon
        {"Source": "Varys", "Target": "Daenerys_Targaryen", "Weight": 6},        # KL <-> Essos
        {"Source": "Robert_Baratheon", "Target": "Stannis_Baratheon", "Weight": 4} # Baratheon Brothers
    ]
    
    # Create DataFrame and save
    df_edges = pd.DataFrame(edges_data)
    edges_file = os.path.join(data_dir, 'edges.csv')
    df_edges.to_csv(edges_file, index=False)
    print(f"Saved {len(df_edges)} edges to {edges_file}")

if __name__ == "__main__":
    prepare_data()
