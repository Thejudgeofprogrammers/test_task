import subprocess
import sys
import re
import os
import socket
from tools import ToolsAnsible


class Tools:
    def __init__(self):
        self.tool_ansible = ToolsAnsible()


    def check_ansible(self) -> bool:
        stdout = subprocess.Popen(["ansible", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ).communicate()

        return True if stdout else False


    def resolve_to_ip(self, host: str) -> str | None:
        try:
            return socket.gethostbyname(host.strip())
        except socket.gaierror:
            return None


    def check_valid_ips(self, arr_ips: list[str]) -> bool:
        ipv4_regex = re.compile(
            r'^((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}'
            r'(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$'
        )

        return all(ipv4_regex.match(ip.strip()) for ip in arr_ips)


    def gen_inventory_file(self, ips: list[str]):
        if len(ips) != 2:
            print('You not write two ips')
            return

        if not self.check_ansible():
            print('Download ansible')
            return

        if not self.check_valid_ips(ips):
            print('You not write two valid ips')
            return

        ip1, ip2 = ips
        self.tool_ansible.generate_inventory_file(ip1, ip2)

        if not os.path.isfile("inventory.ini"):
            print('Inventory file not exists')
            return


    def get_ping_servers(self):
        ans = self.tool_ansible.ping_servers()
        pong_count = ans.count('"pong"')
        if pong_count == 2:
            return 'Calling successful'
        else:
            return ans


    def get_avg(self, arr_ips):
        load_avgs = [
            (ip, self.parse_loadavg_1min(self.tool_ansible.get_load_avg(ip)))
            for ip in arr_ips
        ]
        return load_avgs


    def parse_loadavg_1min(self, loadavg_str):
        parts = loadavg_str.split()
        if not parts:
            print("Не удалось получить loadavg:", loadavg_str)
            return
        return float(parts[0])


if __name__ == "__main__":
    tool = Tools()
    tool_ansible = ToolsAnsible()

    print('\nWrite ip or domen. Example ip1,ip2 or domain1,ip2: ')

    ips = list(sys.stdin.readline().strip().split(','))

    ips = [tool.resolve_to_ip(ips[0]), tool.resolve_to_ip(ips[1])]

    if "debian" not in tool_ansible.get_os_realize(ips[0]):
        ips = [ips[1], ips[0]]

    print('\nGeneration inventory file...')
    tool.gen_inventory_file(ips)
    print('Generation Successful' + '\n')

    print('Servers calling...')
    print(tool.get_ping_servers())

    total_avgs = tool.get_avg(ips)
    print(f"\nLast-minute load on Debian: {total_avgs[0][1]}")
    print(f"Last-minute load on CentOS: {total_avgs[1][1]}")
    
    min_avg = min(total_avgs, key=lambda x: x[1])

    # Процесс получения названия системы с минимальной загруженностью
    system_min_avg = tool_ansible.get_os_realize(min_avg[0])
    
    print('\nGenerate vars.yml...')
    if min_avg[0] == ips[0]:
        tool_ansible.generate_vars(ips[1], ips[0])
    else:
        tool_ansible.generate_vars(ips[0], ips[1])
    print('Generate successful')
    
    # процесс скачивания PostgreSQL на host с min_avg
    install_postgres = tool_ansible.run_playbook_to_install_postgre(system_min_avg)
    tool_ansible.run_playbook_to_check_student(install_postgres)
    print("\nThe program has ended")
     