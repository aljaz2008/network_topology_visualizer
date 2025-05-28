import argparse
from pyvis.network import Network
import networkx as nx
import webbrowser
import pandas as pd

parser = argparse.ArgumentParser(description="Visualize network topology from Excel.")
parser.add_argument("--font-size", type=int, default=18, help="Font size for node labels")
parser.add_argument("--excel", type=str, default="text_sheet.xlsx", help="Path to the Excel file")
parser.add_argument("--size-user", type=int, default=20, help="Size of user nodes")
parser.add_argument("--size-router", type=int, default=20, help="Size of router nodes")
parser.add_argument("--size-switch", type=int, default=20, help="Size of switch nodes")
parser.add_argument("--size-server", type=int, default=20, help="Size of server nodes")
args = parser.parse_args()

use_naprave = pd.read_excel(args.excel, sheet_name=None)

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

G = nx.MultiDiGraph()
edges_added = set()

for device, ports in slovar.items():
    for port, connected_device in ports.items():
        if port == "Type" or connected_device not in slovar:
            continue
        key_out = (device, connected_device, port)
        if key_out not in edges_added:
            G.add_edge(device, connected_device, label=port)
            edges_added.add(key_out)
        for other_port, target in slovar[connected_device].items():
            if other_port == "Type":
                continue
            if target == device:
                key_in = (connected_device, device, other_port)
                if key_in not in edges_added:
                    G.add_edge(connected_device, device, label=other_port)
                    edges_added.add(key_in)
                break

net = Network(height="750px", width="100%", bgcolor="#222", font_color="white", directed=True)
net.force_atlas_2based(gravity=-50, central_gravity=0.005, spring_length=150, damping=0.8)
net.from_nx(G)

for i, node in enumerate(net.nodes):
    node_id = node["id"]
    node_type = slovar.get(node_id, {}).get("Type", "")

    net.nodes[i]["font"] = {"size": args.font_size, "color": "white"}

    if node_type == "U":
        size = args.size_user
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_computer.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "R":
        size = args.size_router
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_router.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "S":
        size = args.size_switch
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/cisco_switch.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })
    elif node_type == "SR":
        size = args.size_server
        net.nodes[i].update({
            "shape": "image",
            "image": "Imgs/server.png",
            "label": node_id,
            "shapeProperties": {"useImageSize": False},
            "size": size,
            "font": {"size": int(size * 0.6), "color": "white"}
        })

filename = "graph.html"
net.write_html(filename)
webbrowser.open(filename)
