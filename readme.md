## Requirements

- **Python 3.9+** (latest version recommended)  
  Download Python from: https://www.python.org/

---

## Quick Guide

Follow the steps below from the **root directory of the project**.

---

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environement

- On (Linux / macOS)
```bash
source venv/bin/activate
```

- On Windows PowerShell
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip3 install textual
```

### 4. Start the Server
```bash
# Default configuration (localhost:3000)
python3 -m server.server

# Custom address and port
python3 -m server.server --addr 0.0.0.0 --port 6667

# Enable debug logs
python3 -m server.server --debug

# Full example
python3 -m server.server --addr 0.0.0.0 --port 6667 --debug

# CTRL+C to stop the server

### 5. Start any client
```bash
python3 -m client.client
```
