# Network Visualizer

A lightweight, Python-powered tool to visualize and analyze your network using data from an Excel file. Each sheet represents a device, and your entire network map is just a few clicks away!

## 🚀 Features

- **Excel-Powered:** Scrape network data from an Excel file where each sheet represents a device.
- **Instant Visualization:** Compose a full HTML report of your network in seconds.
- **Interactive Analysis:** Start the Flask app, tweak parameters, and instantly explore your network topology.
- **Device Isolation:** Zoom in or select any device to see its direct connections.
- **Detailed Info:** View device names, connection ports, IP addresses, and MAC addresses.
- **Easy to Use:** Simple setup with Python and Flask.

## 🛠 Getting Started

1. **Clone this repository:**
   ```bash
   git clone https://github.com/aljaz2008/network-visualizer.git
   cd network-visualizer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare your Excel file:**
   #### In your excel file you have sheets(representing your devices) and the parameters in the sheets
   ##### Example of a sheet(LOOK IN EXAMPLES_XLSX folder)(also in screenshots)
   | Port | connected | Type | IP | Vlan | Trunk | Protocol | geoloc |
   |------|-----------|------|----| -----| ----- | ---------| -------|
   |port on device|name of device connecting to|type of this device|ip of this device| vlan this device is in | Tunk yes/no | Protocol of the device(only in honeypot sheet) | geoloc(only in honeypot sheet)  |
   
   | Type    | Meaning |
   | -------- | ------- |
   | S  | Switch    |
   | SR | Server   |
   | R    | Router   |
   | U  | User    |
   | P  | Patch |
   | H  | Honeypot |


6. **Start the Flask app:**
   ```bash
   flask run
   ```

7. **Open your browser and explore your network!**

## 📸 Screenshots

#### WebUI

<img width="1352" alt="Screenshot 2025-05-28 at 15 18 09" src="https://github.com/user-attachments/assets/f586eb2d-4947-4494-bfd6-872f50b5303f" />

#### in this example we have a device(End_device_3) that has a connection on port 1 connected to Switch1 and this end device has an ip 192.168.10.1

<img width="1440" alt="Screenshot 2025-05-28 at 14 45 53" src="https://github.com/user-attachments/assets/d95e4cc3-f89f-49bb-a5e9-105c7eaf52cc" />
Example of a simple topology
<img width="1440" alt="Screenshot 2025-05-28 at 14 46 36" src="https://github.com/user-attachments/assets/c47ac493-2985-4a1c-8d93-15e5296f24a6" />
Example of a more complex topology
<img width="1440" alt="Screenshot 2025-05-28 at 14 47 08" src="https://github.com/user-attachments/assets/1f0ed9f5-79fd-4f37-a589-d488dcbb35fb" />


## 🤝 Credits

Created by [aljaz2008](https://github.com/aljaz2008) & [Meej-sudo](https://github.com/Meej-sudo)

---

> Analyze. Visualize. Optimize your network in seconds!
