import argparse
from pyvis.network import Network
import networkx as nx
import webbrowser
import pandas as pd
from flask import Flask, render_template, request, redirect, send_file, session
import os
import tempfile 
from datetime import datetime
import shutil
import uuid






app = Flask(__name__)
app.secret_key = "your_secret_key"  

edge_type_colors = {
    ("U", "U"): "blue",
    ("U", "R"): "orange",
    ("U", "S"): "blue",
    ("U", "SR"): "purple",

    ("R", "U"): "orange",
    ("R", "R"): "red",
    ("R", "S"): "red",
    ("R", "SR"): "brown",

    ("S", "U"): "blue",
    ("S", "R"): "red",
    ("S", "S"): "green",
    ("S", "SR"): "green",

    ("SR", "U"): "purple",
    ("SR", "R"): "brown",
    ("SR", "S"): "green",
    ("SR", "SR"): "black",

    ("P", "S"): "green",
    ("S", "P"): "green",
}



@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/patch_panels", methods=["GET"])
def get_patch_panel_sheets():
    excel_path = session.get("excel_path")
    if not excel_path or not os.path.exists(excel_path):
        return {"error": "Excel file not found. Please upload first."}, 400

    try:
        xl = pd.ExcelFile(excel_path)
        patch_sheets = [sheet for sheet in xl.sheet_names if "patch" in sheet.lower()]
        if not patch_sheets:
            return {"message": "No patch panel sheets found."}, 404

        patch_data = {}
        for sheet in patch_sheets:
            df = xl.parse(sheet).fillna("")
            patch_data[sheet] = df.to_dict(orient="records")
        
        return render_template("patch.html", patch_data=patch_data)

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/isolation", methods=['POST'])
def isolation():
    file = request.files["excel"]
    if not file:
        return "No file uploaded", 400
    filename = os.path.splitext(file.filename)[0]

    if os.path.isdir(filename):
        shutil.rmtree(filename)
    UPLOAD_DIR = os.path.join(os.getcwd(), filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    excel_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{datetime.today().strftime('%Y-%m-%d')}_{file.filename}")

    file.save(excel_path)
    session["excel_path"] = excel_path
    session["font_size"] = int(request.form.get("font_size", 18))
    session["size_user"] = int(request.form.get("size_user", 20))
    session["size_router"] = int(request.form.get("size_router", 20))
    session["size_switch"] = int(request.form.get("size_switch", 20))
    session["size_server"] = int(request.form.get("size_server", 20))
    session["theme"] = request.form.get("theme", "dark")

    use_naprave = pd.read_excel(excel_path, sheet_name=None)
    device_names = [sheet_name.strip() for sheet_name in use_naprave.keys()]

    return render_template("isolation.html", device_names=device_names)

@app.route("/upload", methods=["POST"])
def show_network():
    excel_path = session.get("excel_path")
    font_size = session.get("font_size", 18)
    size_user = session.get("size_user", 20)
    size_router = session.get("size_router", 20)
    size_switch = session.get("size_switch", 20)
    size_server = session.get("size_server", 20)
    device_isolate = str(request.form.get("device_isolate", ""))
    theme = request.form.get("theme", session.get("theme", "dark"))

    if theme == "light":
        bgcolor = "#fff"
        font_color = "black"
    else:
        bgcolor = "#000"  
        font_color = "white"

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
            vlan = str(row.get("Vlan", "")).strip()
            trunk = str(row.get("Trunk", "")).strip()
            if pd.notna(connected_to) and connected_to.lower() != "nan":
                tempdict[port] = connected_to
            if str(row["Type"]).lower() != "nan":
                tempdict['Type'] = str(row['Type']).strip()
            if ip:
                tempdict["IP"] = ip
            if vlan:
                tempdict["Vlan"] = vlan
            if trunk:
                tempdict["Trunk"] = trunk
        slovar[sheet_name] = tempdict

    print("Devices in network:", list(slovar.keys()))
    for device, ports in slovar.items():
        for port, connected_device in ports.items():
            if port != "Type":
                print(f"{device} ({port}) -> {connected_device}")

    G = nx.MultiDiGraph()
    edges_added = set()
    if device_isolate == "":

        for device, ports in slovar.items():
            for port, connected_device in ports.items():
                if port == "Type" or connected_device not in slovar:
                    continue
                key_out = (device, connected_device, port)
                if key_out not in edges_added:
                    type1 = slovar.get(device, {}).get("Type", "")
                    type2 = slovar.get(connected_device, {}).get("Type", "")
                    edge_color = edge_type_colors.get((type1, type2), "gray")
                    trunk_status = slovar.get(device, {}).get("Trunk", "")
                    G.add_edge(
                        device,
                        connected_device,
                        label=port,
                        color=edge_color,
                        title=f"Trunk: {trunk_status if trunk_status else 'No'}"
                    )
                    edges_added.add(key_out)
                for other_port, target in slovar[connected_device].items():
                    if other_port == "Type":
                        continue
                    if target == device:
                        key_in = (connected_device, device, other_port)
                        if key_in not in edges_added:
                            type1 = slovar.get(connected_device, {}).get("Type", "")
                            type2 = slovar.get(device, {}).get("Type", "")
                            edge_color = edge_type_colors.get((type1, type2), "gray")
                            G.add_edge(connected_device, device, label=other_port, color=edge_color)
                            edges_added.add(key_in)
                        break

        net = Network(height="750px", width="100%", bgcolor=bgcolor, font_color=font_color, directed=True)
        net.force_atlas_2based(gravity=-50, central_gravity=0.005, spring_length=150, damping=0.8)
        net.from_nx(G)

        for i, node in enumerate(net.nodes):
            node_id = node["id"]
            node_type = slovar.get(node_id, {}).get("Type", "")
            ip = slovar.get(node_id, {}).get("IP", "")
            vlan = slovar.get(node_id, {}).get("Vlan", "")
            trunk = slovar.get(node_id, {}).get("Trunk", "")
            net.nodes[i]["font"] = {"size": font_size, "color": font_color}

            # General info
            tooltip = f"Device: {node_id}\nType: {node_type}\nIP: {ip}\nVlan: {vlan}\nTrunk: {trunk}"

            # --- NEW LOGIC ---
            # Find all unique devices this node connects to
            connected_devices = set(
                d for p, d in slovar.get(node_id, {}).items() if p not in ["Type", "IP", "Vlan", "Trunk"]
            )
            for remote in connected_devices:
                if remote not in slovar:
                    continue
                # All local ports to this remote
                local_ports = [p for p, d in slovar[node_id].items() if d == remote and p not in ["Type", "IP", "Vlan", "Trunk"]]
                # All remote ports to this node
                remote_ports = [p for p, d in slovar[remote].items() if d == node_id and p not in ["Type", "IP", "Vlan", "Trunk"]]
                # Pair in order
                for idx, local_port in enumerate(local_ports):
                    remote_port = remote_ports[idx] if idx < len(remote_ports) else ""
                    tooltip += f"\nPort: {local_port} -> {remote}"
                    if remote_port:
                        tooltip += f" | {remote_port}"

            # Node rendering logic
            if node_type == "P":
                size = size_switch  # Or define a separate size_patchpanel if you want
                net.nodes[i].update({
                    "shape": "image",
                    "image": "static/Imgs/patch_panel.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip
                })
            elif node_type == "U":
                size = size_user
                net.nodes[i].update({
                    "shape": "image",
                    "image": "static/Imgs/cisco_computer.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip
                })
            elif node_type == "R":
                size = size_router
                net.nodes[i].update({
                    "shape": "image",
                    "image": "static/Imgs/cisco_router.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip
                })
            elif node_type == "S":
                size = size_switch
                net.nodes[i].update({
                    "shape": "image",
                    "image": "static/Imgs/cisco_switch.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip
                })
            elif node_type == "SR":
                size = size_server
                net.nodes[i].update({
                    "shape": "image",
                    "image": "static/Imgs/server.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip
                })


        edge_stroke_color = "#fff" if font_color == "black" else "#000"
        for edge in net.edges:
            edge["font"] = {
                "color": font_color,
                "strokeWidth": 4,
                "strokeColor": edge_stroke_color
            }

        filename = "graph.html"
        unique_filename = f"network_{uuid.uuid4().hex}.html"
        file_path = os.path.join("static", "graphs", unique_filename)
        net.save_graph(file_path)
        return send_file(file_path)

    else:
        i = 1
        vsi_connected_devici = []
        for key, value in slovar[device_isolate].items():
            if key not in ["Type", "IP", "Vlan", "Trunk"]:
                type1 = slovar.get(device_isolate, {}).get("Type", "")
                type2 = slovar.get(value, {}).get("Type", "")
                edge_color = edge_type_colors.get((type1, type2), "gray")
                trunk_status = slovar.get(device_isolate, {}).get("Trunk", "")
                G.add_edge(
                    device_isolate,
                    value,
                    label=key,
                    color=edge_color,
                    title=f"Trunk: {trunk_status if trunk_status else 'No'}"
                )
                if value in slovar and value not in vsi_connected_devici:
                    vsi_connected_devici.append(value)
        for device in vsi_connected_devici:
            if device not in slovar:
                continue
            for key, value in slovar[device].items():
                if key not in ["Type", "IP", "Vlan", "Trunk"] and value == device_isolate:
                    type1 = slovar.get(device, {}).get("Type", "")
                    type2 = slovar.get(device_isolate, {}).get("Type", "")
                    edge_color = edge_type_colors.get((type1, type2), "gray")
                    trunk_status = slovar.get(device, {}).get("Trunk", "")
                    G.add_edge(
                        device,
                        device_isolate,
                        label=key,
                        color=edge_color,
                        title=f"Trunk: {trunk_status if trunk_status else 'No'}"
                    )

    net = Network(height="750px", width="100%", bgcolor=bgcolor, font_color=font_color, directed=True)
    net.force_atlas_2based(gravity=-50, central_gravity=0.005, spring_length=150, damping=0.8)
    net.from_nx(G)

    for i, node in enumerate(net.nodes):
        node_id = node["id"]
        node_type = slovar.get(node_id, {}).get("Type", "")
        ip = slovar.get(node_id, {}).get("IP", "")
        vlan = slovar.get(node_id, {}).get("Vlan", "")
        trunk = slovar.get(node_id, {}).get("Trunk", "")
        net.nodes[i]["font"] = {"size": font_size, "color": font_color}

        # General info
        tooltip = f"Device: {node_id}\nType: {node_type}\nIP: {ip}\nVlan: {vlan}\nTrunk: {trunk}"

        # --- NEW LOGIC ---
        # Find all unique devices this node connects to
        connected_devices = set(
            d for p, d in slovar.get(node_id, {}).items() if p not in ["Type", "IP", "Vlan", "Trunk"]
        )
        for remote in connected_devices:
            if remote not in slovar:
                continue
            # All local ports to this remote
            local_ports = [p for p, d in slovar[node_id].items() if d == remote and p not in ["Type", "IP", "Vlan", "Trunk"]]
            # All remote ports to this node
            remote_ports = [p for p, d in slovar[remote].items() if d == node_id and p not in ["Type", "IP", "Vlan", "Trunk"]]
            # Pair in order
            for idx, local_port in enumerate(local_ports):
                remote_port = remote_ports[idx] if idx < len(remote_ports) else ""
                tooltip += f"\nPort: {local_port} -> {remote}"
                if remote_port:
                    tooltip += f" | {remote_port}"

        # Node rendering logic
        if node_type == "P":
            size = size_switch  # Or define a separate size_patchpanel if you want
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/patch_panel.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip
            })
        elif node_type == "U":
            size = size_user
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_computer.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip
            })
        elif node_type == "R":
            size = size_router
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_router.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip
            })
        elif node_type == "S":
            size = size_switch
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/cisco_switch.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip
            })
        elif node_type == "SR":
            size = size_server
            net.nodes[i].update({
                "shape": "image",
                "image": "static/Imgs/server.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip
            })
        

    edge_stroke_color = "#fff" if font_color == "black" else "#000"
    for edge in net.edges:
        edge["font"] = {
            "color": font_color,
            "strokeWidth": 4,
            "strokeColor": edge_stroke_color
        }

    filename = "graph.html"
    unique_filename = f"network_{uuid.uuid4().hex}.html"
    file_path = os.path.join("static", "graphs", unique_filename)
    net.save_graph(file_path)
    return send_file(file_path)


def key_for_patch_panel_port(device_dict, patch_panel_name, dev_port):
    """
    Returns the patch panel port name that this device port connects to, if any.
    """
    for port, target in device_dict.items():
        if port == dev_port and target == patch_panel_name:
            return port
    return ""


def get_patchpanel_port_mapping(slovar, patchpanel_name, device_name):
    """
    Returns a list of (patch_port, device_port) tuples for all connections between patchpanel and device,
    paired in order of appearance.
    """
    patch_ports = [p for p, d in slovar[patchpanel_name].items() if d == device_name and p not in ["Type", "IP", "Vlan", "Trunk"]]
    device_ports = [p for p, d in slovar[device_name].items() if d == patchpanel_name and p not in ["Type", "IP", "Vlan", "Trunk"]]
    return list(zip(patch_ports, device_ports))


if __name__ == "__main__":
    app.run(debug=True)
