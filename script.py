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
import scapy






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

@app.route("/download_excel")
def download_excel():
    excel_path = session.get("excel_path")
    if not excel_path or not os.path.exists(excel_path):
        return "No Excel file to download.", 404
    return send_file(excel_path, as_attachment=True)

@app.route("/get_active_devices", methods=["GET"])
def get_active_devices():
    arp = ARP("10.0.0.0/16")
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout = 2, iface=ens160, verbose = 0)[0]
    devices = []
    print("IP Address\t Mac Address")
    print("-" * 40)
    for sent, received in result:
        print(f"{received.psrc}\t{received.hwsrc}")
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    return devices

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
@app.route("/save_patch_panels", methods=["POST"])
def save_patch_panel_changes():
    data = request.get_json()
    excel_path = session.get("excel_path")

    if not excel_path or not os.path.exists(excel_path):
        return "Excel file not found.", 400

    try:
        
        original_excel = pd.ExcelFile(excel_path)
        
        all_sheets = {sheet: original_excel.parse(sheet) for sheet in original_excel.sheet_names}

        
        for sheet_name, rows in data.items():
            df = pd.DataFrame(rows)
            all_sheets[sheet_name] = df

        
        with pd.ExcelWriter(excel_path, engine='openpyxl', mode='w') as writer:
            for sheet, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet, index=False)

        return "Success", 200

    except Exception as e:
        return f"Error saving Excel: {str(e)}", 500

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
            dev_type = str(row.get("Type", "")).strip()
            if pd.notna(connected_to) and connected_to.lower() != "nan":
                tempdict[port] = connected_to
            if dev_type and dev_type.lower() != "nan":
                tempdict['Type'] = dev_type
            if ip:
                tempdict["IP"] = ip
            if vlan:
                tempdict["Vlan"] = vlan
            if trunk:
                tempdict["Trunk"] = trunk
            # Honeypot-specific fields
            if dev_type == "H":
                protocol = str(row.get("Protocol", "")).strip()
                geoloc = str(row.get("geoloc", "")).strip()
                if protocol:
                    tempdict["Protocol"] = protocol
                if geoloc:
                    tempdict["geoloc"] = geoloc
        slovar[sheet_name] = tempdict

    print("Devices in network:", list(slovar.keys()))
    for device, ports in slovar.items():
        for port, connected_device in ports.items():
            if port in ["Type", "IP", "Vlan", "Trunk", "Con_type", "geoloc"] or connected_device not in slovar:
                continue
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

        net = Network(height="900px", width="100%", bgcolor=bgcolor, font_color=font_color, directed=True)
        net.force_atlas_2based(gravity=-50, central_gravity=0.005, spring_length=150, damping=0.8)
        net.from_nx(G)

        for i, node in enumerate(net.nodes):
            node_id = node["id"]
            node_type = slovar.get(node_id, {}).get("Type", "")
            ip = slovar.get(node_id, {}).get("IP", "")
            vlan = slovar.get(node_id, {}).get("Vlan", "")
            trunk = slovar.get(node_id, {}).get("Trunk", "")
            con_type = slovar.get(node_id, {}).get("Con_type", "")
            geoloc = slovar.get(node_id, {}).get("geoloc", "")
            net.nodes[i]["font"] = {"size": font_size, "color": font_color}

            # General info
            tooltip = f"Device: {node_id}\nType: {node_type}\nIP: {ip}\nVlan: {vlan}\nTrunk: {trunk}"
            if node_type == "H":
                protocol = slovar.get(node_id, {}).get("Protocol", "")
                geoloc = slovar.get(node_id, {}).get("geoloc", "")
                if node_type == "H":
                    tooltip += f"\nProtocol: {protocol}\nGeoloc: {geoloc}"

            # Port/connection info (same logic as before)
            connected_devices = set(
                d for p, d in slovar.get(node_id, {}).items() if p not in ["Type", "IP", "Vlan", "Trunk", "Con_type", "geoloc"]
            )
            for remote in connected_devices:
                if remote not in slovar:
                    continue
                local_ports = [p for p, d in slovar[node_id].items() if d == remote and p not in ["Type", "IP", "Vlan", "Trunk", "Con_type", "geoloc"]]
                remote_ports = [p for p, d in slovar[remote].items() if d == node_id and p not in ["Type", "IP", "Vlan", "Trunk", "Con_type", "geoloc"]]
                for idx, local_port in enumerate(local_ports):
                    remote_port = remote_ports[idx] if idx < len(remote_ports) else ""
                    tooltip += f"\nPort: {local_port} -> {remote}"
                    if remote_port:
                        tooltip += f" | {remote_port}"

            # Node rendering logic
            if node_type == "H":
                size = size_user  # Or define a separate size_honeypot if you want
                net.nodes[i].update({
                    "shape": "circularImage",
                    "image": "static/Imgs/honeypot.jpeg",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "title": tooltip,
                    "borderWidth":5,
                    "color": {
                        "border": "#FF0F1B",
                        "background": "#97C2FC",
                        "highlight": {
                            "border": "#00FF1E",     # Glow effect color
                            "background": "#FFFFF",  # Glow background}
                            "borderWidth": 5
                }}
                })
            elif node_type == "P":
                size = size_switch
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
                    "title": tooltip,
                    "color": {
                        "border": "#2B7CE9",
                        "background": "#97C2FC",
                        "highlight": {
                            "border": "#00FF0D",     # Glow effect color
                            "background": "#FFFACD"  # Glow background}
                }}})
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
                    "shape": "circularImage",
                    "image": "static/Imgs/server.png",
                    "label": node_id,
                    "shapeProperties": {"useImageSize": False},
                    "size": size,
                    "font": {"size": int(size * 0.6), "color": font_color},
                    "borderWidth":5,
                    "title": tooltip,
                    "color": {
                        "border": "#F8F8F8",
                        "background": "#97C2FC",
                        "highlight": {
                            "border": "#00FF0D",     # Glow effect color
                            "background": "#0FFFFF",
                            "borderWidth": 5  # Glow background}
                }}
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
            if key not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]:
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
                if key not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"] and value == device_isolate:
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
        protocol = slovar.get(node_id, {}).get("Protocol", "")
        geoloc = slovar.get(node_id, {}).get("geoloc", "")
        net.nodes[i]["font"] = {"size": font_size, "color": font_color}

        tooltip = f"Device: {node_id}\nType: {node_type}\nIP: {ip}\nVlan: {vlan}\nTrunk: {trunk}"
        if node_type == "H":
            tooltip += f"\nProtocol: {protocol}\nGeoloc: {geoloc}"

        connected_devices = set(
            d for p, d in slovar.get(node_id, {}).items() if p not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]
        )
        for remote in connected_devices:
            if remote not in slovar:
                continue
            local_ports = [p for p, d in slovar[node_id].items() if d == remote and p not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]]
            remote_ports = [p for p, d in slovar[remote].items() if d == node_id and p not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]]
            for idx, local_port in enumerate(local_ports):
                remote_port = remote_ports[idx] if idx < len(remote_ports) else ""
                tooltip += f"\nPort: {local_port} -> {remote}"
                if remote_port:
                    tooltip += f" | {remote_port}"

        if node_type == "H":
            size = size_user
            net.nodes[i].update({
                "shape": "circularImage",
                "image": "static/Imgs/honeypot.jpeg",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "title": tooltip,
                 "color": {
                        "border": "#FFFFF",
                        "background": "#97C2FC",
                        "highlight": {
                            "border": "#00FF0D",     # Glow effect color
                            "background": "#FFFFF",  # Glow background}
                            "borderWidth": 5
                }}
            })
        elif node_type == "P":
            size = size_switch
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
                "shape": "circularImage",
                "image": "static/Imgs/server.png",
                "label": node_id,
                "shapeProperties": {"useImageSize": False},
                "size": size,
                "font": {"size": int(size * 0.6), "color": font_color},
                "shadow":{"enabled": False},
                "title": tooltip,
                "color": {
                        "border": "#FFFFF",
                        "background": "#97C2FC",
                        "highlight": {
                            "border": "#00FF0D",     # Glow effect color
                            "background": "#FFFFF",  # Glow background}
                            "borderWidth": 5
                }}
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
    for port, target in device_dict.items():
        if port == dev_port and target == patch_panel_name:
            return port
    return ""


def get_patchpanel_port_mapping(slovar, patchpanel_name, device_name):
    patch_ports = [p for p, d in slovar[patchpanel_name].items() if d == device_name and p not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]]
    device_ports = [p for p, d in slovar[device_name].items() if d == patchpanel_name and p not in ["Type", "IP", "Vlan", "Trunk", "Protocol", "geoloc"]]
    return list(zip(patch_ports, device_ports))


if __name__ == "__main__":
    app.run(debug=True)
