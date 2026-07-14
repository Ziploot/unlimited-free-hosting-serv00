import os
import sys
import re
import time

# 1. Failsafe Paramiko Installation
try:
    import paramiko
except ImportError:
    print("[INFO] Paramiko SSH library not found. Installing via pip...")
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"], check=True)
        import paramiko
        print("[SUCCESS] Paramiko installed successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to install paramiko automatically: {e}")
        print("Please run: pip install paramiko")
        sys.exit(1)

def sftp_upload_dir(sftp, local_dir, remote_dir):
    # Recursively create remote folders and upload files
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass # Directory already exists
        
    for item in os.listdir(local_dir):
        local_path = os.path.join(local_dir, item)
        remote_path = remote_dir + "/" + item
        
        if os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)
        else:
            print(f"Uploading: {item} -> {remote_path}")
            sftp.put(local_path, remote_path)

def main():
    print("==============================================")
    print("   ⚡ ZIPLOOT SERV00 AUTOMATED DEPLOYER")
    print("==============================================")
    print("   Node.js + Free Databases + Lifetime Host")
    print("==============================================")
    print()

    # Get user inputs
    host = input("[INPUT] Serv00 Host (e.g. s3.serv00.com): ").strip()
    username = input("[INPUT] Serv00 Username: ").strip()
    password = input("[INPUT] Serv00 Password: ").strip()
    domain = input(f"[INPUT] Subdomain/Domain to use (e.g. {username}.serv00.net): ").strip()

    if not host or not username or not password or not domain:
        print("[ERROR] All inputs are required!")
        sys.exit(1)

    print()
    print("[INFO] Connecting to Serv00 via SSH...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=username, password=password, timeout=15)
        print("[SUCCESS] Connected to SSH server successfully!")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    # 1. Get or Reserve Port
    print()
    print("[INFO] Configuring port reservation on Serv00...")
    
    # Try to add a new random port
    stdin, stdout, stderr = ssh.exec_command("devil port add tcp random")
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    
    port = None
    # Parse port number
    match = re.search(r'Port\s+(\d+)\s+added', out)
    if match:
        port = match.group(1)
        print(f"[SUCCESS] Reserved new port: {port}")
    else:
        # Check if port addition failed because limit reached, find existing port
        print("[WARN] Failed to reserve new random port. Fetching existing ports...")
        stdin, stdout, stderr = ssh.exec_command("devil port list")
        list_out = stdout.read().decode('utf-8', errors='ignore')
        
        # Extract first TCP port from list
        ports = re.findall(r'(\d+)\s+tcp', list_out)
        if ports:
            port = ports[0]
            print(f"[SUCCESS] Using existing open port: {port}")
        else:
            print("[ERROR] No ports available. Please delete a port in DevilWeb panel and run again.")
            ssh.close()
            sys.exit(1)

    # 2. Configure Website Type in Devil CLI
    print()
    print(f"[INFO] Setting up website configuration for '{domain}'...")
    
    # Check if domain exists
    stdin, stdout, stderr = ssh.exec_command("devil www list")
    www_out = stdout.read().decode('utf-8', errors='ignore')
    
    if domain in www_out:
        print(f"[WARN] Website {domain} already exists. Deleting configuration first to override...")
        stdin, stdout, stderr = ssh.exec_command(f"devil www del {domain}")
        stdout.read() # Wait for completion
        time.sleep(1)

    # Add website with Node.js type
    node_path = "/usr/local/bin/node"
    app_dir = f"/home/{username}/public_nodejs/{domain}"
    
    cmd = f"devil www add {domain} nodejs {node_path} {app_dir} {port}"
    print(f"Executing: {cmd}")
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    add_out = stdout.read().decode('utf-8', errors='ignore')
    add_err = stderr.read().decode('utf-8', errors='ignore')
    
    if "added" in add_out or "created" in add_out or www_out:
        print(f"[SUCCESS] Website {domain} configured as Node.js app!")
    else:
        print(f"[ERROR] Failed to configure website: {add_out} {add_err}")
        ssh.close()
        sys.exit(1)

    # 3. Upload project files via SFTP
    print()
    print("[INFO] Uploading files to Serv00...")
    sftp = ssh.open_sftp()
    
    local_app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    if not os.path.exists(local_app_dir):
        print(f"[ERROR] Local app folder not found at: {local_app_dir}")
        sftp.close()
        ssh.close()
        sys.exit(1)
        
    try:
        sftp_upload_dir(sftp, local_app_dir, app_dir)
        print("[SUCCESS] All files uploaded successfully!")
    except Exception as e:
        print(f"[ERROR] SFTP Upload failed: {e}")
        sftp.close()
        ssh.close()
        sys.exit(1)
    finally:
        sftp.close()

    # 4. Install NPM dependencies and restart app jail
    print()
    print("[INFO] Installing npm dependencies on Serv00 (this may take a moment)...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {app_dir} && npm install")
    npm_out = stdout.read().decode('utf-8', errors='ignore')
    npm_err = stderr.read().decode('utf-8', errors='ignore')
    
    print("[INFO] npm install log:")
    print(npm_out)
    if npm_err:
        print(npm_err)

    print("[INFO] Restarting Node.js application jail...")
    stdin, stdout, stderr = ssh.exec_command(f"devil www restart {domain}")
    restart_out = stdout.read().decode('utf-8', errors='ignore')
    
    print("==============================================")
    print("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("==============================================")
    print(f"🔗 Live Proof Subdomain: http://{domain}")
    print(f"⚙️ Running on Node.js Port: {port}")
    print("==============================================")
    print()
    
    ssh.close()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
