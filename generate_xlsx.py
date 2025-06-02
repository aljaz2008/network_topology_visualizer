import pandas as pd

devices = [
    {"name": "Router1", "Type": "R", "IP": "10.0.0.1", "Vlan": "1", "Trunk": "No"},
    {"name": "Router2", "Type": "R", "IP": "10.0.0.2", "Vlan": "1", "Trunk": "No"},
    {"name": "Switch1", "Type": "S", "IP": "10.0.1.1", "Vlan": "10", "Trunk": "Yes"},
    {"name": "Switch2", "Type": "S", "IP": "10.0.1.2", "Vlan": "20", "Trunk": "Yes"},
    {"name": "Switch3", "Type": "S", "IP": "10.0.1.3", "Vlan": "30", "Trunk": "Yes"},
    {"name": "PC1", "Type": "U", "IP": "10.0.10.1", "Vlan": "10", "Trunk": "No"},
    {"name": "PC2", "Type": "U", "IP": "10.0.10.2", "Vlan": "10", "Trunk": "No"},
    {"name": "PC3", "Type": "U", "IP": "10.0.20.1", "Vlan": "20", "Trunk": "No"},
    {"name": "PC4", "Type": "U", "IP": "10.0.20.2", "Vlan": "20", "Trunk": "No"},
    {"name": "PC5", "Type": "U", "IP": "10.0.30.1", "Vlan": "30", "Trunk": "No"},
    {"name": "PC6", "Type": "U", "IP": "10.0.30.2", "Vlan": "30", "Trunk": "No"},
    {"name": "Server1", "Type": "SR", "IP": "10.0.100.1", "Vlan": "100", "Trunk": "No"},
    {"name": "Server2", "Type": "SR", "IP": "10.0.100.2", "Vlan": "100", "Trunk": "No"},
    {"name": "Router3", "Type": "R", "IP": "10.0.0.3", "Vlan": "1", "Trunk": "No"},
    {"name": "Switch4", "Type": "S", "IP": "10.0.1.4", "Vlan": "40", "Trunk": "Yes"},
]

connections = {
    "Router1": [("G0/0", "Switch1"), ("G0/1", "Router2")],
    "Router2": [("G0/0", "Switch2"), ("G0/1", "Router1"), ("G0/2", "Router3")],
    "Router3": [("G0/0", "Switch3"), ("G0/1", "Router2")],
    "Switch1": [("F0/1", "Router1"), ("F0/2", "PC1"), ("F0/3", "PC2"), ("F0/4", "Switch2")],
    "Switch2": [("F0/1", "Router2"), ("F0/2", "PC3"), ("F0/3", "PC4"), ("F0/4", "Switch1")],
    "Switch3": [("F0/1", "Router3"), ("F0/2", "PC5"), ("F0/3", "PC6"), ("F0/4", "Switch4")],
    "Switch4": [("F0/1", "Switch3"), ("F0/2", "Server1"), ("F0/3", "Server2")],
    "PC1": [("eth0", "Switch1")],
    "PC2": [("eth0", "Switch1")],
    "PC3": [("eth0", "Switch2")],
    "PC4": [("eth0", "Switch2")],
    "PC5": [("eth0", "Switch3")],
    "PC6": [("eth0", "Switch3")],
    "Server1": [("eth0", "Switch4")],
    "Server2": [("eth0", "Switch4")],
}

sheets = {}
for dev in devices:
    rows = []
    dev_name = dev["name"]
    for port, target in connections.get(dev_name, []):
        rows.append({
            "Port": port,
            "Conected_to": target,
            "Type": dev["Type"],
            "IP": dev["IP"],
            "Vlan": dev["Vlan"],
            "Trunk": dev["Trunk"]
        })
    # Add a row with just Type/IP/Vlan/Trunk if no connections (for completeness)
    if not rows:
        rows.append({
            "Port": "",
            "Conected_to": "",
            "Type": dev["Type"],
            "IP": dev["IP"],
            "Vlan": dev["Vlan"],
            "Trunk": dev["Trunk"]
        })
    sheets[dev_name] = pd.DataFrame(rows)

with pd.ExcelWriter("network_sample.xlsx") as writer:
    for name, df in sheets.items():
        df.to_excel(writer, sheet_name=name, index=False)

print("network_sample.xlsx generated with 15 devices.")