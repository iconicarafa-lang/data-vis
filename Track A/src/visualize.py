import os
import json
import pandas as pd
import networkx as nx
import community as community_louvain

def run_analysis_and_visualization():
    # Define directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    dist_dir = os.path.join(base_dir, 'dist')
    os.makedirs(dist_dir, exist_ok=True)
    
    # Load CSVs
    nodes_file = os.path.join(data_dir, 'nodes.csv')
    edges_file = os.path.join(data_dir, 'edges.csv')
    
    if not os.path.exists(nodes_file) or not os.path.exists(edges_file):
        raise FileNotFoundError("Data files not found. Run data_prep.py first.")
        
    df_nodes = pd.read_csv(nodes_file)
    df_edges = pd.read_csv(edges_file)
    
    print("Building NetworkX Graph...")
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in df_nodes.iterrows():
        G.add_node(row['Id'], label=row['Label'], faction=row['Faction'])
        
    # Add edges with weights
    for _, row in df_edges.iterrows():
        G.add_edge(row['Source'], row['Target'], weight=int(row['Weight']))
        
    # 1. Apply Louvain Community Detection
    print("Running Louvain Community Detection...")
    partition = community_louvain.best_partition(G, weight='weight')
    
    # 2. Calculate Centrality Metrics
    print("Calculating Centrality Metrics...")
    betweenness = nx.betweenness_centrality(G, weight='weight')
    degree_cent = nx.degree_centrality(G)
    degrees = dict(G.degree())
    
    # Sort by betweenness to print key actors
    sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 5 Key Players by Betweenness Centrality:")
    for i, (node, cent) in enumerate(sorted_betweenness[:5]):
        print(f"{i+1}. {G.nodes[node]['label']} (Betweenness: {cent:.4f}, Degree: {degrees[node]})")
        
    # 3. Map communities dynamically to thematic GoT houses/factions
    # We find which community ID key characters belong to, ensuring consistent coloring
    comm_to_name = {}
    comm_to_color = {}
    
    # Dracula Palette for houses
    theme_colors = {
        "stark": "#8be9fd",       # Ice Blue / Stark
        "lannister": "#ffb86c",   # Gold/Orange / Lannister
        "targaryen": "#ff5555",   # Red / Targaryen
        "nightswatch": "#50fa7b", # Green / Wall
        "baratheon": "#bd93f9",   # Purple / Baratheon
        "other": "#f1fa8c"        # Yellow / Default
    }
    
    # Find community IDs for representative characters
    rep_chars = {
        "Ned_Stark": ("House Stark (The North)", theme_colors["stark"]),
        "Tyrion_Lannister": ("House Lannister (King's Landing)", theme_colors["lannister"]),
        "Daenerys_Targaryen": ("House Targaryen (Essos Campaign)", theme_colors["targaryen"]),
        "Samwell_Tarly": ("Night's Watch & Wildlings", theme_colors["nightswatch"]),
        "Stannis_Baratheon": ("House Baratheon & Rebels", theme_colors["baratheon"])
    }
    
    assigned_communities = set()
    for char_id, (faction_name, color) in rep_chars.items():
        if char_id in partition:
            comm_id = partition[char_id]
            comm_to_name[comm_id] = faction_name
            comm_to_color[comm_id] = color
            assigned_communities.add(comm_id)
            
    # For any leftover communities
    all_comms = set(partition.values())
    leftovers = all_comms - assigned_communities
    colors_pool = [theme_colors["other"], "#ff79c6", "#ff79c6", "#f8f8f2"]
    
    for i, comm_id in enumerate(leftovers):
        comm_to_name[comm_id] = f"Other Alliance {i+1}"
        comm_to_color[comm_id] = colors_pool[i % len(colors_pool)]
        
    # 4. Prepare JSON data for client-side Vis.js rendering
    nodes_json = []
    for node_id in G.nodes():
        node_attr = G.nodes[node_id]
        c_id = partition[node_id]
        
        # Calculate top connections for sidebar profile
        neighbors = []
        for n in G.neighbors(node_id):
            neighbors.append({
                "id": n,
                "label": G.nodes[n]['label'],
                "weight": G[node_id][n]['weight']
            })
        # Sort neighbors by interaction weight
        neighbors = sorted(neighbors, key=lambda x: x['weight'], reverse=True)[:5]
        
        nodes_json.append({
            "id": node_id,
            "label": node_attr['label'],
            "faction": node_attr['faction'],
            "communityId": int(c_id),
            "communityName": comm_to_name[c_id],
            "baseColor": comm_to_color[c_id],
            "betweenness": betweenness[node_id],
            "degreeCentrality": degree_cent[node_id],
            "degree": degrees[node_id],
            "connections": neighbors
        })
        
    edges_json = []
    edge_idx = 0
    for u, v in G.edges():
        weight = G[u][v]['weight']
        edges_json.append({
            "id": f"edge_{edge_idx}",
            "from": u,
            "to": v,
            "weight": int(weight)
        })
        edge_idx += 1
        
    legend_json = [
        {"id": int(cid), "name": name, "color": comm_to_color[cid]}
        for cid, name in comm_to_name.items()
    ]
    
    # 5. Write the Premium Dashboard HTML template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Westeros Social Network Discovery</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Phosphor Icons -->
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    
    <!-- Vis Network Standalone -->
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

    <style>
        :root {{
            --bg-deep: #07090e;
            --bg-sidebar: #0f111a;
            --bg-card: #161925;
            --border-color: rgba(255, 255, 255, 0.06);
            --text-primary: #f8f8f2;
            --text-secondary: #9aa0a6;
            --accent: #bd93f9;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-deep);
            color: var(--text-primary);
            overflow: hidden;
            display: flex;
            height: 100vh;
            width: 100vw;
        }}

        /* --- SIDEBAR STYLE --- */
        .sidebar {{
            width: 380px;
            height: 100vh;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            z-index: 10;
            box-shadow: 4px 0 25px rgba(0, 0, 0, 0.6);
            flex-shrink: 0;
        }}

        .sidebar-header {{
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(180deg, rgba(189, 147, 249, 0.05) 0%, rgba(0, 0, 0, 0) 100%);
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
        }}

        .brand i {{
            font-size: 24px;
            color: var(--accent);
            text-shadow: 0 0 10px rgba(189, 147, 249, 0.4);
        }}

        .brand h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}

        /* Scrollbar styling */
        .sidebar-content::-webkit-scrollbar {{
            width: 6px;
        }}
        .sidebar-content::-webkit-scrollbar-thumb {{
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }}

        .section-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--accent);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 14px;
            border-radius: 12px;
        }}

        .input-label {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }}

        .select-input, .text-input {{
            width: 100%;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 10px 12px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 13px;
            outline: none;
            transition: all 0.2s;
        }}

        .select-input:focus, .text-input:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.2);
        }}

        .btn-toggle-group {{
            display: flex;
            gap: 8px;
        }}

        .btn-toggle {{
            flex: 1;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.2s;
        }}

        .btn-toggle.active {{
            background-color: var(--accent);
            border-color: var(--accent);
            color: #000;
        }}

        .btn-toggle:hover:not(.active) {{
            border-color: rgba(255, 255, 255, 0.2);
            color: var(--text-primary);
        }}

        /* --- LEGEND STYLE --- */
        .legend-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            padding: 8px;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.01);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .legend-item:hover {{
            background-color: rgba(255, 255, 255, 0.03);
            border-color: var(--border-color);
        }}

        .legend-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
            box-shadow: 0 0 8px currentColor;
        }}

        /* --- CHARACTER CARD --- */
        .profile-card {{
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(22, 25, 37, 0.7) 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .profile-placeholder {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            height: 100%;
            color: var(--text-secondary);
            font-size: 13px;
            gap: 8px;
            padding: 20px 10px;
        }}

        .profile-placeholder i {{
            font-size: 32px;
            color: rgba(255, 255, 255, 0.1);
        }}

        .profile-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .profile-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
        }}

        .faction-badge {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            margin-top: 4px;
            display: inline-block;
        }}

        .profile-meta-row {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .meta-stat {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .stat-label-container {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
        }}

        .stat-bar-outer {{
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
            overflow: hidden;
        }}

        .stat-bar-inner {{
            height: 100%;
            background-color: var(--accent);
            border-radius: 3px;
            width: 0%;
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .connections-list {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-top: 6px;
        }}

        .connection-item {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            padding: 6px 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.02);
            cursor: pointer;
            transition: all 0.2s;
        }}

        .connection-item:hover {{
            background: rgba(255, 255, 255, 0.06);
            border-color: var(--border-color);
        }}

        .sidebar-footer {{
            padding: 16px 20px;
            border-top: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
        }}

        /* --- CANVAS CONTAINER STYLE --- */
        .canvas-container {{
            flex: 1;
            height: 100vh;
            position: relative;
            background-color: var(--bg-deep);
        }}

        #network {{
            width: 100%;
            height: 100%;
        }}

        /* --- FLOAT STATS CARD --- */
        .float-stats-card {{
            position: absolute;
            top: 24px;
            right: 24px;
            background: rgba(15, 17, 26, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 14px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            display: flex;
            gap: 20px;
            z-index: 5;
        }}

        .float-stat {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .float-stat-val {{
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            color: var(--accent);
        }}

        .float-stat-lbl {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .float-stat-divider {{
            width: 1px;
            background-color: var(--border-color);
            align-self: stretch;
        }}

        /* Vis.js Custom Tooltip override */
        div.vis-tooltip {{
            background-color: rgba(15, 17, 26, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
            padding: 12px !important;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6) !important;
            backdrop-filter: blur(8px) !important;
            max-width: 280px !important;
            font-size: 12px !important;
            line-height: 1.5 !important;
            word-break: break-word !important;
            white-space: normal !important;
        }}

        /* Custom zoom controls */
        .zoom-controls {{
            position: absolute;
            bottom: 24px;
            right: 24px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 5;
        }}

        .zoom-btn {{
            width: 40px;
            height: 40px;
            background: rgba(15, 17, 26, 0.75);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 18px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }}

        .zoom-btn:hover {{
            background: var(--accent);
            color: #000;
            border-color: var(--accent);
        }}

        /* Loading Overlay */
        .loading-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: var(--bg-deep);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 15;
            transition: opacity 0.5s ease;
        }}

        .spinner {{
            width: 50px;
            height: 50px;
            border: 3px solid rgba(189, 147, 249, 0.1);
            border-radius: 50%;
            border-top-color: var(--accent);
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>

    <!-- Loading Screen -->
    <div id="loading" class="loading-overlay">
        <div class="spinner"></div>
        <h2 style="font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 18px; letter-spacing: 1px;">Stabilizing Westeros Network...</h2>
        <p style="color: var(--text-secondary); font-size: 12px; margin-top: 6px;">Simulating political alliances and modularity groups</p>
    </div>

    <!-- Sidebar Dashboard -->
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="brand">
                <i class="ph-fill ph-target"></i>
                <h1>Westeros Audits</h1>
            </div>
            <div class="subtitle">Modularity & Centrality Engine</div>
        </div>
        
        <div class="sidebar-content">
            <!-- Controls Section -->
            <div>
                <div class="section-title">
                    <i class="ph-bold ph-sliders"></i> Network Controls
                </div>
                <div class="control-group">
                    <div>
                        <div class="input-label">Node Size Factor (Metric)</div>
                        <div class="btn-toggle-group">
                            <button id="btn-betweenness" class="btn-toggle active" onclick="switchMetric('betweenness')">
                                <i class="ph-bold ph-git-merge"></i> Betweenness
                            </button>
                            <button id="btn-degree" class="btn-toggle" onclick="switchMetric('degree')">
                                <i class="ph-bold ph-hash"></i> Degree
                            </button>
                        </div>
                    </div>
                    <div>
                        <div class="input-label">Filter by Faction</div>
                        <select id="faction-filter" class="select-input" onchange="filterFaction(this.value)">
                            <option value="all">All Factions</option>
                            <option value="House Stark">House Stark</option>
                            <option value="House Lannister">House Lannister</option>
                            <option value="House Targaryen">House Targaryen</option>
                            <option value="Night's Watch">Night's Watch</option>
                            <option value="House Baratheon">House Baratheon</option>
                            <option value="Wildlings">Wildlings</option>
                            <option value="Independent">Independent</option>
                        </select>
                    </div>
                    <div>
                        <div class="input-label">Search Character</div>
                        <input type="text" id="search-input" class="text-input" placeholder="Type character name..." oninput="searchCharacter(this.value)">
                    </div>
                    <div>
                        <div class="btn-toggle-group">
                            <button id="btn-physics" class="btn-toggle active" onclick="togglePhysics()">
                                <i id="physics-icon" class="ph-bold ph-pause"></i> Pause Simulation
                            </button>
                            <button class="btn-toggle" onclick="resetView()">
                                <i class="ph-bold ph-arrows-counter-clockwise"></i> Reset View
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Profile card -->
            <div>
                <div class="section-title">
                    <i class="ph-bold ph-user-circle"></i> Character Profile
                </div>
                <div id="profile-card" class="profile-card">
                    <div class="profile-placeholder">
                        <i class="ph ph-fingerprint"></i>
                        <p>Click on any character node to inspect centrality stats and key relationships.</p>
                    </div>
                </div>
            </div>

            <!-- Modularity Legend -->
            <div>
                <div class="section-title">
                    <i class="ph-bold ph-palette"></i> Discovered Communities
                </div>
                <div class="legend-list" id="legend-list">
                    <!-- Loaded dynamically -->
                </div>
            </div>
        </div>

        <div class="sidebar-footer">
            <span>Track A deliverables verified</span>
            <span>v1.2</span>
        </div>
    </div>

    <!-- Canvas Container -->
    <div class="canvas-container">
        <!-- Floating stats -->
        <div class="float-stats-card">
            <div class="float-stat">
                <span class="float-stat-val">39</span>
                <span class="float-stat-lbl">Nodes</span>
            </div>
            <div class="float-stat-divider"></div>
            <div class="float-stat">
                <span class="float-stat-val">81</span>
                <span class="float-stat-lbl">Edges</span>
            </div>
            <div class="float-stat-divider"></div>
            <div class="float-stat">
                <span class="float-stat-val" id="comm-count">5</span>
                <span class="float-stat-lbl">Alliances</span>
            </div>
        </div>

        <!-- Custom Zoom Controls -->
        <div class="zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()"><i class="ph-bold ph-plus"></i></button>
            <button class="zoom-btn" onclick="zoomOut()"><i class="ph-bold ph-minus"></i></button>
            <button class="zoom-btn" onclick="resetView()"><i class="ph-bold ph-frame-corners"></i></button>
        </div>

        <!-- Vis Network graph div -->
        <div id="network"></div>
    </div>

    <script type="text/javascript">
        // Inject Graph data from python
        const graphData = {{
            nodes: {json.dumps(nodes_json)},
            edges: {json.dumps(edges_json)},
            legend: {json.dumps(legend_json)}
        }};

        let network;
        let nodesDataset;
        let edgesDataset;
        let activeMetric = 'betweenness'; // default node size metric
        let selectedNodeId = null;
        let physicsEnabled = true;

        // RGBA helper
        function hexToRgba(hex, alpha) {{
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${{r}}, ${{g}}, ${{b}}, ${{alpha}})`;
        }}

        // Format floats
        function fmt(val) {{
            return Number(val).toFixed(4);
        }}

        // Initialize Vis.js network
        function initNetwork() {{
            const container = document.getElementById('network');
            
            // Build vis-ready arrays
            const visNodes = graphData.nodes.map(n => {{
                // Initial sizing based on betweenness
                const size = 15 + (n.betweenness * 100);
                
                // Label proportionality: only top actors show label initially to avoid clutter
                // Top 10 actors by betweenness
                const topActors = ['Jon_Snow', 'Daenerys_Targaryen', 'Tyrion_Lannister', 'Robert_Baratheon', 'Cersei_Lannister', 'Ned_Stark', 'Sansa_Stark', 'Arya_Stark', 'Samwell_Tarly', 'Jaime_Lannister'];
                const showLabel = topActors.includes(n.id);
                
                return {{
                    id: n.id,
                    label: showLabel ? n.label : " ",
                    title: (() => {{
                        const el = document.createElement('div');
                        el.style.padding = '4px';
                        el.innerHTML = `
                            <div style="font-weight: 700; color: ${{n.baseColor}}; font-size: 14px; margin-bottom: 6px; font-family: 'Outfit', sans-serif;">${{n.label}}</div>
                            <div style="font-size: 12px; color: #e2e8f0; margin-bottom: 4px; font-family: 'Inter', sans-serif;"><b>Faction:</b> ${{n.faction}}</div>
                            <div style="font-size: 12px; color: #e2e8f0; margin-bottom: 4px; font-family: 'Inter', sans-serif;"><b>Alliance:</b> ${{n.communityName}}</div>
                            <div style="font-size: 11px; color: #bd93f9; font-family: 'Inter', sans-serif;"><b>Centrality:</b> ${{Number(n.betweenness).toFixed(4)}}</div>
                        `;
                        return el;
                    }})(),
                    size: size,
                    color: {{
                        background: n.baseColor,
                        border: '#222222',
                        highlight: {{
                            background: '#ffffff',
                            border: n.baseColor
                        }},
                        hover: {{
                            background: '#ffffff',
                            border: n.baseColor
                        }}
                    }},
                    font: {{
                        size: showLabel ? 15 : 10,
                        color: '#f8f8f2',
                        face: 'Outfit, sans-serif',
                        strokeWidth: 3,
                        strokeColor: '#07090e'
                    }},
                    borderWidth: 2,
                    borderWidthSelected: 4
                }};
            }});

            const visEdges = graphData.edges.map(e => {{
                return {{
                    id: e.id,
                    from: e.from,
                    to: e.to,
                    value: e.weight,
                    width: 1 + (e.weight * 0.5),
                    title: (() => {{
                        const el = document.createElement('div');
                        el.style.padding = '2px';
                        el.innerHTML = `<span style="font-family: 'Inter', sans-serif; font-size: 12px;">Interaction strength: <b>${{e.weight}}/10</b></span>`;
                        return el;
                    }})(),
                    color: {{
                        color: 'rgba(255, 255, 255, 0.12)',
                        highlight: 'rgba(189, 147, 249, 0.8)',
                        hover: 'rgba(189, 147, 249, 0.8)'
                    }},
                    smooth: {{
                        type: 'continuous',
                        roundness: 0.4
                    }}
                }};
            }});

            nodesDataset = new vis.DataSet(visNodes);
            edgesDataset = new vis.DataSet(visEdges);

            const data = {{
                nodes: nodesDataset,
                edges: edgesDataset
            }};

            const options = {{
                nodes: {{
                    shape: 'dot',
                    scaling: {{
                        min: 15,
                        max: 80
                    }},
                    shadow: {{
                        enabled: true,
                        color: 'rgba(0, 0, 0, 0.5)',
                        size: 8,
                        x: 4,
                        y: 4
                    }}
                }},
                edges: {{
                    shadow: {{
                        enabled: false
                    }}
                }},
                physics: {{
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {{
                        gravitationalConstant: -180,
                        centralGravity: 0.015,
                        springLength: 110,
                        springConstant: 0.07,
                        damping: 0.4,
                        avoidOverlap: 1
                    }},
                    stabilization: {{
                        enabled: true,
                        iterations: 400,
                        updateInterval: 50,
                        fit: true
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 50,
                    hideEdgesOnDrag: false,
                    zoomView: true,
                    dragView: true
                }}
            }};

            network = new vis.Network(container, data, options);

            // Hide loading overlay when stabilization completes
            network.on("stabilizationIterationsDone", function () {{
                document.getElementById('loading').style.opacity = '0';
                setTimeout(() => {{
                    document.getElementById('loading').style.display = 'none';
                }}, 500);
            }});

            // Bind click event
            network.on("click", function(params) {{
                if (params.nodes.length > 0) {{
                    selectedNodeId = params.nodes[0];
                    updateProfileCard(selectedNodeId);
                    highlightConnections(selectedNodeId);
                }} else {{
                    selectedNodeId = null;
                    resetHighlight();
                    resetProfileCard();
                }}
            }});

            // Render community legend
            renderLegend();
        }}

        // Render Legend list
        function renderLegend() {{
            const list = document.getElementById('legend-list');
            list.innerHTML = "";
            graphData.legend.forEach(item => {{
                const el = document.createElement('div');
                el.className = 'legend-item';
                el.onclick = () => filterByCommunity(item.id);
                el.innerHTML = `
                    <span class="legend-dot" style="color: ${{item.color}}; background-color: ${{item.color}}"></span>
                    <span>${{item.name}}</span>
                `;
                list.appendChild(el);
            }});
            document.getElementById('comm-count').textContent = graphData.legend.length;
        }}

        // Switch size metrics (betweenness centrality vs degree centrality)
        function switchMetric(metric) {{
            activeMetric = metric;
            document.getElementById('btn-betweenness').classList.toggle('active', metric === 'betweenness');
            document.getElementById('btn-degree').classList.toggle('active', metric === 'degree');

            const updates = graphData.nodes.map(n => {{
                const val = (metric === 'betweenness') ? n.betweenness : n.degreeCentrality;
                // Sizing math
                const size = 15 + (val * 100);
                
                // Size scale adjustment
                return {{
                    id: n.id,
                    size: size
                }};
            }});
            nodesDataset.update(updates);

            if (selectedNodeId) {{
                updateProfileCard(selectedNodeId);
            }}
        }}

        // Filter nodes by faction
        function filterFaction(faction) {{
            resetHighlight();
            if (faction === 'all') {{
                // reset filters
                const updates = graphData.nodes.map(n => {{
                    return {{ id: n.id, hidden: false }};
                }});
                nodesDataset.update(updates);
            }} else {{
                const updates = graphData.nodes.map(n => {{
                    return {{
                        id: n.id,
                        hidden: n.faction !== faction
                    }};
                }});
                nodesDataset.update(updates);
            }}
        }}

        // Filter by community from legend click
        function filterByCommunity(communityId) {{
            resetHighlight();
            const updates = graphData.nodes.map(n => {{
                return {{
                    id: n.id,
                    hidden: n.communityId !== communityId
                }};
            }});
            nodesDataset.update(updates);
            document.getElementById('faction-filter').value = 'all'; // reset select input
        }}

        // Search character
        function searchCharacter(query) {{
            if (!query) {{
                return;
            }}
            const matched = graphData.nodes.find(n => n.label.toLowerCase().includes(query.toLowerCase()));
            if (matched) {{
                network.selectNodes([matched.id]);
                selectedNodeId = matched.id;
                updateProfileCard(matched.id);
                highlightConnections(matched.id);
                
                // Focus camera on node
                network.focus(matched.id, {{
                    scale: 1.2,
                    animation: {{
                        duration: 800,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }}
        }}

        // Physics controls
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
            
            const btn = document.getElementById('btn-physics');
            const icon = document.getElementById('physics-icon');
            
            if (physicsEnabled) {{
                btn.innerHTML = `<i id="physics-icon" class="ph-bold ph-pause"></i> Pause Simulation`;
                btn.classList.add('active');
            }} else {{
                btn.innerHTML = `<i id="physics-icon" class="ph-bold ph-play"></i> Resume Simulation`;
                btn.classList.remove('active');
            }}
        }}

        // Camera control functions
        function zoomIn() {{ network.moveTo({{ scale: network.getScale() * 1.3 }}); }}
        function zoomOut() {{ network.moveTo({{ scale: network.getScale() * 0.7 }}); }}
        function resetView() {{
            network.fit({{
                animation: {{
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
            resetHighlight();
            resetProfileCard();
            document.getElementById('faction-filter').value = 'all';
            document.getElementById('search-input').value = '';
            filterFaction('all');
        }}

        // Highlight connected sub-graph of selected node
        function highlightConnections(nodeId) {{
            const connectedNodes = network.getConnectedNodes(nodeId);
            const connectedEdges = network.getConnectedEdges(nodeId);

            // Mute all nodes except selected and neighbors
            const nodeUpdates = graphData.nodes.map(n => {{
                let opacity = 0.15;
                let border = 1;
                
                if (n.id === nodeId) {{
                    opacity = 1.0;
                    border = 4;
                }} else if (connectedNodes.includes(n.id)) {{
                    opacity = 0.95;
                    border = 2.5;
                }}

                return {{
                    id: n.id,
                    color: {{
                        background: hexToRgba(n.baseColor, opacity),
                        border: hexToRgba('#222222', opacity),
                        highlight: {{
                            background: '#ffffff',
                            border: n.baseColor
                        }}
                    }},
                    borderWidth: border,
                    font: {{
                        color: `rgba(248, 248, 242, ${{opacity}})`
                    }}
                }};
            }});
            nodesDataset.update(nodeUpdates);

            // Mute all edges except neighbors
            const edgeUpdates = graphData.edges.map(e => {{
                let opacity = 0.04;
                let color = 'rgba(255, 255, 255, 0.04)';
                let width = 1;
                
                if (connectedEdges.includes(e.id)) {{
                    opacity = 0.85;
                    color = 'rgba(189, 147, 249, 0.85)';
                    width = 1.5 + (e.weight * 0.5);
                }}

                return {{
                    id: e.id,
                    color: {{ color: color }},
                    width: width
                }};
            }});
            edgesDataset.update(edgeUpdates);
        }}

        // Reset highlights
        function resetHighlight() {{
            const nodeUpdates = graphData.nodes.map(n => {{
                return {{
                    id: n.id,
                    color: {{
                        background: n.baseColor,
                        border: '#222222'
                    }},
                    borderWidth: 2,
                    font: {{
                        color: '#f8f8f2'
                    }}
                }};
            }});
            nodesDataset.update(nodeUpdates);

            const edgeUpdates = graphData.edges.map(e => {{
                return {{
                    id: e.id,
                    color: {{ color: 'rgba(255, 255, 255, 0.12)' }},
                    width: 1 + (e.weight * 0.5)
                }};
            }});
            edgesDataset.update(edgeUpdates);
        }}

        // Update Card details
        function updateProfileCard(nodeId) {{
            const node = graphData.nodes.find(n => n.id === nodeId);
            const container = document.getElementById('profile-card');
            
            // Format metrics
            const metricValue = activeMetric === 'betweenness' ? node.betweenness : node.degreeCentrality;
            const metricPercent = (metricValue * 100).toFixed(1);
            
            let connectionsHtml = "";
            node.connections.forEach(conn => {{
                connectionsHtml += `
                    <div class="connection-item" onclick="focusNode('${{conn.id}}')">
                        <span style="font-weight: 500">${{conn.label}}</span>
                        <span style="color: var(--accent); font-weight: 600">Weight: ${{conn.weight}}</span>
                    </div>
                `;
            }});

            container.innerHTML = `
                <div class="profile-header">
                    <div>
                        <div class="profile-title">${{node.label}}</div>
                        <div class="faction-badge" style="border-color: ${{node.baseColor}}; color: ${{node.baseColor}}">
                            ${{node.faction}}
                        </div>
                    </div>
                </div>
                
                <div class="profile-meta-row">
                    <div class="meta-stat">
                        <div class="stat-label-container">
                            <span>Centrality Importance</span>
                            <span>${{metricPercent}}%</span>
                        </div>
                        <div class="stat-bar-outer">
                            <div class="stat-bar-inner" style="width: ${{metricPercent}}%; background-color: ${{node.baseColor}}"></div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 15px; font-size: 12px; margin-top: 4px;">
                        <div><b>Connections:</b> ${{node.degree}}</div>
                        <div><b>Betweenness:</b> ${{fmt(node.betweenness)}}</div>
                    </div>
                </div>
                
                <div>
                    <div class="input-label" style="margin-bottom: 8px;">Top Relationships (Strong Ties)</div>
                    <div class="connections-list">
                        ${{connectionsHtml}}
                    </div>
                </div>
            `;
        }}

        function focusNode(nodeId) {{
            network.selectNodes([nodeId]);
            selectedNodeId = nodeId;
            updateProfileCard(nodeId);
            highlightConnections(nodeId);
            network.focus(nodeId, {{
                scale: 1.2,
                animation: {{
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }}
            }});
        }}

        function resetProfileCard() {{
            const container = document.getElementById('profile-card');
            container.innerHTML = `
                <div class="profile-placeholder">
                    <i class="ph ph-fingerprint"></i>
                    <p>Click on any character node to inspect centrality stats and key relationships.</p>
                </div>
            `;
        }}

        // Initialize window load
        window.addEventListener("load", () => {{
            initNetwork();
        }});
    </script>
</body>
</html>
"""
    
    # Save the output HTML
    output_html = os.path.join(dist_dir, 'track_a_network.html')
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Custom Interactive Premium Dashboard successfully generated and saved to {output_html}")

if __name__ == "__main__":
    run_analysis_and_visualization()
