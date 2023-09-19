#!/usr/bin/env python3

import time
import paramiko
import threading
import yaml

class task_thread(threading.Thread):
    def __init__(self, host, port, user, keys):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.user = user
        self.keys = keys
    def run(self):
        load_metrics(self.host, self.port, self.user, self.keys)

def read_config():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)

def string_to_float(data):
    return float(data.strip().split(' ', 2)[0].strip())

def parse_top_string(data):
    rows = data.splitlines()

    load = rows[0].split('load average: ', 2)[1]

    cpu_data = rows[1].split(':', 2)[1].strip().split(',')
    cpu_percent = 100.0 - float(cpu_data[3].strip().split(' ', 2)[0].strip()) - float(cpu_data[7].strip().split(' ', 2)[0].strip())
    if (cpu_percent < 0):
        cpu_percent = 0

    ram_unit, ram_data = rows[2].split(':', 2)
    ram_factor = 1
    if ram_unit[0] == 'K':
        ram_factor = 1024 * 1024
    elif ram_unit[0] == 'M':
        ram_factor = 1024
    elif ram_unit[0] == 'G':
        ram_factor = 1
    ram_data = ram_data.strip().split(',')
    ram_total = float(ram_data[0].strip().split(' ', 2)[0].strip()) / ram_factor
    ram_free = float(ram_data[1].strip().split(' ', 2)[0].strip()) / ram_factor

    return load, cpu_percent, ram_total, ram_free

def load_metrics(host, port, user, host_length):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(host, port = port, username = user, timeout = 1)

        stdin, stdout, stderr = client.exec_command('top -bn1 | grep "^top\\|^%Cpu\\|^.iB Mem"')
        stdin.close()

        data = stdout.read().decode('utf-8').strip()
        client.close()

        load, cpu_percent, ram_total, ram_free = parse_top_string(data)
        ram_used = ram_total - ram_free

        print(('✅ ' + host).ljust(host_length + 5) + load + ' (' + '{:3.1f}'.format(cpu_percent).rjust(5) + '%)   ' + '{:3.1f}'.format(ram_used).rjust(5) + ' / ' + '{:3.1f}'.format(ram_total).rjust(5) + ' GiB (' + '{:3.1f}'.format(ram_used / ram_total * 100).rjust(5) + '%)')

    except:
       time.sleep(1)
       print('❌ ' + host)

def main():
    config = read_config()

    host_length = 0
    for host in config['hosts']:
        for user in host['users'].keys():
            if len(user) + len(host['host']) > host_length:
                host_length = len(host['host'])

    print('Host'.center(host_length + 3) + '   ' + 'Load'.center(25) + '   ' + 'Ram Usage'.center(26))

    for host in config['hosts']:
        for user_name, user_data in host['users'].items():
            if user_name != 'root':
                continue
            host_keys = []
            if 'groups' in user_data.keys():
                for group in user_data['groups']:
                    if group not in config['groups'].keys():
                        print('WARNING: Key-group "' + group + '" not found!')
                        continue
                    for key_name in config['groups'][group]:
                        host_keys.append(config['keys'][key_name])
            if 'keys' in user_data.keys():
                for key_name in user_data['keys']:
                    if key_name not in config['keys'].keys():
                        print('WARNING: Key "' + key_name + '" not found!')
                        continue
                    host_keys.append(config['keys'][key_name])
            host_keys = list(set(host_keys)) # Filter duplicates
            if not host_keys:
                continue
            if not 'port' in host:
                host['port'] = 22
            try:
                thread = task_thread(host['host'], host['port'], user_name, host_length)
                thread.start()
            except:
                time.sleep(1)
                print('❌ ' + host['host'])

if __name__ == '__main__':
    main()
