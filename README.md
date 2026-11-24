# Nighty Headless — Pterodactyl 24/7 Hosting

An unofficial, beginner-friendly solution to host your **[Nighty](https://nighty.one)** instance 24/7 on a **Pterodactyl Panel** without needing an expensive dedicated Windows VPS or RDP.

Compatible with the latest **Python 3.14 runtime** and **Wine 10/11 WoW64**. Based on [glowxx/nighty-linux-headless](https://github.com/glowxx/nighty-linux-headless).

> [!WARNING]
> **Disclaimer:** This is an unofficial, community interop/automation tool. It is **not** affiliated with or endorsed by Nighty. It does **not** include, crack, or bypass Nighty licensing — you must supply your own legally obtained copy and valid license. Automating user accounts can violate Discord's Terms of Service. Use at your own risk.

---

##  Features

- **Python 3.14 & Wine 11+ Ready:** Fully updated to support modern CPython bytecode and Windows 10 UCRT APIs.
- **Rootless Headless Repacking:** Uses Astral `uv` to patch the Qt webview stub into `Nighty_stub.exe` directly inside the container.
- **Dynamic Port Allocation:** Reads Pterodactyl's allocated `SERVER_PORT` and dynamically configures the reverse bridge proxy.
- **Always-On Web UI:** Nighty's internal web dashboard is automatically enforced and proxied to your server's public port.
- **Zero Desktop Overhead:** Runs headless under a lightweight virtual framebuffer (`Xvfb`).

---

##  Step-by-Step Installation

### Step 1: Import the Egg
1. Download `egg-nighty-headless.json` from this repository.
2. In your Pterodactyl **Admin Panel**, navigate to **Nests**.
3. Click **Import Egg** (top-right corner).
4. Select `egg-nighty-headless.json` and choose your preferred Nest (e.g., *Generic* or *Bots*).
5. Click **Save**.

### Step 2: Create the Server
1. Go to **Admin → Servers → Create New**.
2. Allocate at least **2048 MB RAM**, **4000 MB Disk**, and **100% CPU**.
3. Under **Allocation**, assign a primary port (this automatically maps to `SERVER_PORT`).
4. Select the **Nighty Headless (Wine)** egg.
5. In the Startup tab, define your desired **Web UI Username** and **Password**.
6. Click **Create Server**.

### Step 3: Upload `Nighty.exe`
1. Open the **File Manager** in Pterodactyl (or connect via SFTP).
2. Upload your official `Nighty.exe` directly into the server root directory (`/home/container/Nighty.exe`).

### Step 4: Start the Server
1. Click **Start** on your Pterodactyl console.
2. The server will:
   - Configure the Windows 10 Wine prefix.
   - Install the Python 3.14 toolchain via `uv`.
   - Build `Nighty_stub.exe`.
   - Start the bridge proxy on your primary port.
3. Once running, open your browser and visit:
