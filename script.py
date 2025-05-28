import argparse
from pyvis.network import Network
import networkx as nx
import webbrowser
import pandas as pd
from flask import Flask, render_template, request, redirect, send_file
import os
import tempfile
from datetime import datetime
import shutil




""" parser = argparse.ArgumentParser(description="Visualize network topology from Excel.")
parser.add_argument("--font-size", type=int, default=18, help="Font size for node labels")
parser.add_argument("--excel", type=str, default="text_sheet.xlsx", help="Path to the Excel file")
parser.add_argument("--size-user", type=int, default=20, help="Size of user nodes")
parser.add_argument("--size-router", type=int, default=20, help="Size of router nodes")
parser.add_argument("--size-switch", type=int, default=20, help="Size of switch nodes")
parser.add_argument("--size-server", type=int, default=20, help="Size of server nodes")
args = parser.parse_args()

use_naprave = pd.read_excel(args.excel, sheet_name=None) """

app = Flask(__name__)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getpartial/{id}", methods = ["POST"])
def getpartial_info(id):
    return

@app.route("/upload", methods = ["POST"])
def show_network():
   
    file = request.files["excel"]
    if not file:
        return "No file uploaded", 400
    filename = os.path.splitext(file.filename)[0]
    
    
    if os.path.isdir(filename):
        shutil.rmtree(filename)
        UPLOAD_DIR = os.path.join(os.getcwd(), filename)
        os.makedirs(UPLOAD_DIR, exist_ok=False)
        app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
        excel_path = os.path.join(app.config["UPLOAD_FOLDER"],f"{datetime.today().strftime('%Y-%m-%d')}_{file.filename}")
        
    else:
        UPLOAD_DIR = os.path.join(os.getcwd(), filename)
        os.makedirs(UPLOAD_DIR, exist_ok=False)
        app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
        excel_path = os.path.join(app.config["UPLOAD_FOLDER"],f"{datetime.today().strftime('%Y-%m-%d')}_{file.filename}")
          

    file.save(excel_path)
    font_size = int(request.form.get("font_size", 18))
    size_user = int(request.form.get("size_user", 20))
    size_router = int(request.form.get("size_router", 20))
    size_switch = int(request.form.get("size_switch", 20))
    size_server = int(request.form.get("size_server", 20))

    use_naprave = pd.read_excel(excel_path, sheet_name=None)
    
    slovar = dict()
    for sheet_name, df in use_naprave.items():
        sheet_name = sheet_name.strip()
        df = df.dropna(how='all')
        tempdict = {}
        for _, row in df.iterrows():
            port = str(row["Port"]).strip()
            ip = str(row.get("IP","")).strip()
            connected_to = str(row["Conected_to"]).strip()
            if pd.notna(connected_to) and connected_to.lower() != "nan":
                tempdict[port] = connected_to
            if str(row["Type"]).lower() != "nan":
                tempdict['Type'] = str(row['Type']).strip()
            if ip:
                tempdict["IP"] = ip
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
        ip = slovar.get(node_id, {}).get("IP", "")
        net.nodes[i]["font"] = {"size": font_size, "color": "white"}
        tooltip = f"Device: {node_id}\nIP:{ip}"
        

        if node_type == "U":
            size = size_user
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_computer.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": "white"},
                "title":tooltip
                
            })
        elif node_type == "R":
            size = size_router
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_router.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": "white"}
            })
        elif node_type == "S":
            size = size_switch
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_switch.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": "white"}
            })
        elif node_type == "SR":
            size = size_server
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/server.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": "white"}
            })

    filename = "graph.html"
    net.save_graph("templates/network.html")
    #net.write_html(filename)
    #webbrowser.open(filename)
    return render_template("network.html")

if __name__ == "__main__":
    app.run(debug=True)