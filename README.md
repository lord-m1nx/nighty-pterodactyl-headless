# Nighty Headless — Pterodactyl 24/7 Hosting

An unofficial, beginner-friendly solution to host your **[Nighty](https://nighty.one)** instance 24/7 on a **Pterodactyl Panel** without needing an expensive dedicated Windows VPS or RDP.

---

## 🚀 Features
* **Native Wine 11 & Virtual Display:** Runs headless in Docker without a desktop environment.
* **Custom Pterodactyl Egg:** 1-click import into any Pterodactyl panel.
* **Sleek Console UI:** Centered gradient ASCII logo with live Discord log streaming directly on your panel console.
* **Dynamic Port Handling:** Automatically routes the Web UI bridge to whichever port Pterodactyl allocates to your server.
* **Easy Data Migration:** Transfer your saved accounts, tokens, and macros from Windows PC to the server in minutes.

---

## 📦 Requirements
* A Pterodactyl Panel with Administrator access (or a host that allows custom eggs).
* At least **1.5 GB – 2.0 GB of RAM** allocated to the server.
* A licensed copy of **`Nighty.exe`** (downloaded from the official Nighty dashboard).

---

## 🛠️ Step-by-Step Installation

### Step 1: Import the Egg to Pterodactyl
1. Download `egg-nighty-headless.json` from this repository.
2. In your Pterodactyl **Admin Panel**, navigate to **Nests**.
3. Click **Import Egg** (in the top right corner).
4. Select the downloaded JSON file and choose your desired Nest (e.g., *Generic* or *Bots*).
5. Click **Save**.

### Step 2: Create the Server
1. Go to **Admin → Servers → Create New**.
2. Set your server name (e.g., `Nighty-24/7`).
3. Allocate at least **2048 MB RAM**, **3024 MB Disk storage** and **100% CPU**.
4. Assign a **Primary Port Allocation**. Pterodactyl exposes it automatically to the egg as `SERVER_PORT`.
5. Under **Nest & Egg Configuration**, select the **Nighty Headless (Wine)** egg.
6. Click **Create Server**.

### Step 3: Upload Files
1. This repository is automatically cloned into the server root directory in the installation process. 
2. Upload your official **`Nighty.exe`** into the root directory.
3. You do **not** need to copy the allocated port into `.env`. On startup, `scripts/start.sh` reads Pterodactyl's built-in `SERVER_PORT`, creates `.env` from `.env.example` if necessary, and writes the correct `BRIDGE_PORT` automatically.

### Step 4: Start the Server
1.  Click Start in the Pterodactyl console.
2.  The server will automatically initialize, configure uv, and generate Nighty_stub.exe.
3.  Open your browser and go to the server's primary allocation shown in Pterodactyl: `http://<YOUR_NODE_IP>:<YOUR_PRIMARY_ALLOCATION_PORT>/`
4.  Follow the setup wizard to log in and sync your bot.

---

### 🔄 Migrating Existing Data from Windows PC
If you already have Nighty configured on your Windows machine and want to
migrate your accounts, settings, and macros:

1.  On your Windows PC, press Win + R, type %appdata%, and press Enter.
2.  Locate the folder named Nighty and compress it into a .zip file.
3.  In Pterodactyl, navigate to:
    /.local/share/nighty/prefix/drive_c/users/container/AppData/Roaming/
4.  Upload your zip file, extract it, and replace the existing Nighty folder.
5.  Restart the server in your console.

---

### Made with ❤ by m1nx
- Discord: m1nx.fr
- Feel free to reach out for any bugs!
