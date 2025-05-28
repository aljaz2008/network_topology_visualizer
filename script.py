from pyvis.network import Network
import networkx as nx
import webbrowser
import pandas as pd

# Adjustable font size variable
FONT_SIZE = 18

# Load all sheets from Excel
use_naprave = pd.read_excel("text_sheet.xlsx", sheet_name=None)

# Build device connection dictionary
slovar = dict()
for sheet_name, df in use_naprave.items():
    sheet_name = sheet_name.strip()
    df = df.dropna(how='all')
    tempdict = {}
    for _, row in df.iterrows():
        port = str(row["Port"]).strip()
        connected_to = str(row["Conected_to"]).strip()
        if pd.notna(connected_to) and connected_to.lower() != "nan":
            tempdict[port] = connected_to
        if str(row["Type"]).lower() != "nan":
            tempdict['Type'] = str(row['Type']).strip()
    slovar[sheet_name] = tempdict

print("Devices in network:", list(slovar.keys()))
for device, ports in slovar.items():
    for port, connected_device in ports.items():
        if port != "Type":
            print(f"{device} ({port}) -> {connected_device}")

# Use MultiDiGraph to allow multiple edges
G = nx.MultiDiGraph()

# Track already added edges using tuples for efficiency
edges_added = set()

# Add edges to the graph
for device, ports in slovar.items():
    for port, connected_device in ports.items():
        if port == "Type" or connected_device not in slovar:
            continue

        # Tuple keys to track edge uniqueness
        key_out = (device, connected_device, port)
        if key_out not in edges_added:
            G.add_edge(device, connected_device, label=port)
            edges_added.add(key_out)

        # Add reverse edge if appropriate
        for other_port, target in slovar[connected_device].items():
            if other_port == "Type":
                continue
            if target == device:
                key_in = (connected_device, device, other_port)
                if key_in not in edges_added:
                    G.add_edge(connected_device, device, label=other_port)
                    edges_added.add(key_in)
                break

# Create Pyvis network
net = Network(height="750px", width="100%", bgcolor="#222", font_color="white", directed=True)

# Use force atlas layout for clearer separation
net.force_atlas_2based(gravity=-50, central_gravity=0.005, spring_length=150, damping=0.8)

# Load graph into pyvis
net.from_nx(G)

# Enhance node visuals and font
for i, node in enumerate(net.nodes):
    node_id = node["id"]
    node_type = slovar.get(node_id, {}).get("Type", "")

    net.nodes[i]["font"] = {"size": FONT_SIZE, "color": "white"}

    if node_type == "U":  # End users group
        size = 20
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_computer.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "R":  # Routers
        size = 20
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_router.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "S":  # Switches
        size = 20
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_switch.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "SR":  # Serversw
        size = 20
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/server.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
# Save and display the visualization
filename = "graph.html"
net.write_html(filename)
webbrowser.open(filename)
