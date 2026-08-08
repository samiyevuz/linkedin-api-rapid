import paramiko
import os
import zipfile

# Configuration
VPS_IP = "213.199.36.249"
USERNAME = "root"
PASSWORD = "363658686"
PROJECT_DIR = r"C:\savers\linkedin_api"
VPS_TARGET_DIR = "/opt/linkedin_api"

def create_zip():
    zip_path = "linkedin_api.zip"
    print(f"Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            for file in files:
                if file.endswith(".py") or file.endswith(".txt"):
                    if "deploy.py" in file or "scratch" in file:
                        continue
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, PROJECT_DIR)
                    zipf.write(filepath, arcname)
    return zip_path

def deploy():
    zip_path = create_zip()
    
    print(f"Connecting to {VPS_IP}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_IP, port=22, username=USERNAME, password=PASSWORD)
    
    # Upload
    sftp = ssh.open_sftp()
    print("Uploading zip file...")
    sftp.put(zip_path, "/tmp/linkedin_api.zip")
    sftp.close()
    
    # Extract and setup
    print("Setting up on VPS...")
    commands = [
        f"mkdir -p {VPS_TARGET_DIR}",
        f"unzip -o /tmp/linkedin_api.zip -d {VPS_TARGET_DIR}",
        f"cd {VPS_TARGET_DIR} && python3 -m venv venv",
        f"cd {VPS_TARGET_DIR} && ./venv/bin/pip install -r requirements.txt",
        # Assuming port 8002 for LinkedIn
        f"cd {VPS_TARGET_DIR} && pm2 delete linkedin_api || true",
        f"cd {VPS_TARGET_DIR} && pm2 start ./venv/bin/uvicorn --name 'linkedin_api' -- main:app --host 0.0.0.0 --port 8002",
        "pm2 save"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"Error executing {cmd}:\n{stderr.read().decode()}")
        else:
            print(stdout.read().decode().strip())
            
    ssh.close()
    os.remove(zip_path)
    print("Deployment complete! API should be running on port 8002.")

if __name__ == "__main__":
    deploy()
