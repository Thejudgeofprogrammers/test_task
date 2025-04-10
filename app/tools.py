import subprocess
import os

class ToolsAnsible:
    def __init__(self):
        self.filename = 'inventory.ini'
        self.key_path = os.path.abspath("ssh_key.pem")
    
    def generate_inventory_file(self, ip1: str, ip2: str):
        content = f"""[debian]
{ip1} ansible_user=root ansible_ssh_private_key_file={self.key_path}

[centos]
{ip2} ansible_user=root ansible_ssh_private_key_file={self.key_path}

[all:vars]
ansible_python_interpreter=/usr/bin/python3
"""
        with open(self.filename, "w") as f:
            f.write(content)
    
    def ping_servers(self):
        x = subprocess.Popen(["ansible", "all", "-i", self.filename, "-m", "ping"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = x.communicate()
        
        return stdout if stdout else stderr
    
    def get_load_avg(self, ip):
        cmd = f"ssh -i {self.key_path} root@{ip} \"awk '{{print $1}}' /proc/loadavg\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    
    def get_os_realize(self, ip):
        cmd = f"ssh -i {self.key_path} root@{ip} \"awk -F'=' '/^ID=/ {{print $2}}' /etc/os-release\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    
    def run_playbook_to_install_postgre(self, system_min_avg):
        if "debian" in system_min_avg:
            system = "debian"
            playbook_install = os.path.abspath("app/ansible/install_postgres_deb.yml")
        else:
            system = "centos"
            playbook_install = os.path.abspath("app/ansible/install_postgres_cent_os.yml")
        
        print(f'\nThe least loaded server is selected: {system}')
        print(f'\nStarting the PostgreSQL installation on the server: {system}...')
        
        cmd = f"ansible-playbook -i {self.filename} -l {system} {playbook_install}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        print(proc.stdout)
        
        if proc.returncode == 0:
            print(f"PostgreSQL has been successfully installed on the server {system}")
            return system
        else:
            print(f"PostgreSQL installation error:\n{proc.stderr}")
            return False
    
    def generate_vars(self, ip):
        content = f"""---
db_user: student
db_password: password
ip_student: {ip}
"""
        os.makedirs('./ansible/group_vars', mode=0o777, exist_ok=True)

        with open('./ansible/group_vars/vars.yml', "w") as f:
            f.write(content)
            
    def run_playbook_to_check_student(self, system):
        if "debian" in system:
            playbook_check = os.path.abspath("app/ansible/check_user_cent_os.yml")
        else:
            playbook_check = os.path.abspath("app/ansible/check_user_deb.yml")
        
        print('\nCheck student in PostgreSQL...')
        cmd = f"ansible-playbook -i {self.filename} -l {system} {playbook_check}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        print(proc.stdout)
        
        if proc.returncode == 0:
            print(f"PostgreSQL has been successfully installed on the server {system}")
            return system
        else:
            print(f"PostgreSQL installation error:\n{proc.stderr}")
            return False
