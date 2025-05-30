import pandas as pd
import sys

def load_excel(filename):
    use_naprave = pd.read_excel(filename, sheet_name=None)
    slovar = dict()
    for sheet_name, df in use_naprave.items():
        sheet_name = sheet_name.strip()
        df = df.dropna(how='all')
        tempdict = {}
        for _, row in df.iterrows():
            port = str(row["Port"]).strip()
            ip = str(row.get("IP", "")).strip()
            connected_to = str(row["Conected_to"]).strip()
            if pd.notna(connected_to) and connected_to.lower() != "nan":
                tempdict[port] = connected_to
            if str(row["Type"]).lower() != "nan":
                tempdict['Type'] = str(row['Type']).strip()
            if ip:
                tempdict["IP"] = ip
        slovar[sheet_name] = tempdict
    return slovar

def check_types(slovar):
    errors = []
    for device, props in slovar.items():
        if "Type" not in props or not props["Type"]:
            errors.append(f"Device '{device}' is missing a Type.")
    return errors

def check_bidirectional(slovar):
    errors = []
    for device, props in slovar.items():
        for port, connected_device in props.items():
            if port == "Type" or port == "IP":
                continue
            if connected_device not in slovar:
                errors.append(f"Device '{device}' (port '{port}') is connected to unknown device '{connected_device}'.")
                continue
            # Check if the reverse connection exists
            reverse_found = False
            for rev_port, rev_connected in slovar[connected_device].items():
                if rev_port == "Type" or rev_port == "IP":
                    continue
                if rev_connected == device:
                    reverse_found = True
                    break
            if not reverse_found:
                errors.append(
                    f"Device '{device}' (port '{port}') is connected to '{connected_device}', "
                    f"but '{connected_device}' does not have a connection back to '{device}'."
                )
    return errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tester.py <excel_file.xlsx>")
        sys.exit(1)
    filename = sys.argv[1]
    slovar = load_excel(filename)
    errors = check_types(slovar) + check_bidirectional(slovar)
    if errors:
        print("Errors found:")
        for err in errors:
            print("-", err)
    else:
        print("All devices have a type and all connections are bidirectional!")