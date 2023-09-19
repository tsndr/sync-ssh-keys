#!/usr/bin/env python3

import time
import paramiko
import threading
import yaml

out_buf = []

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

class Host(threading.Thread):
    def __init__(self, host, port, host_length, idx):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.host_length = host_length
        self.idx = idx
        self.status = 'none'
        self.done = False

    def render_status(self):
        if self.status == 'none':
            return '[ .. ] '
        elif self.status == 'ok':
            return '[ \033[92mok\033[0m ] '
        elif self.status == 'fail':
            return '[\033[91mfail\033[0m] '

    def render_top(self):
        if self.status != 'ok':
            return ''

        stdin, stdout, stderr = self.client.exec_command('top -bn1 | grep "^top\\|^%Cpu\\|^.iB Mem"')
        stdin.close()

        data = stdout.read().decode('utf-8').strip()
        self.client.close()

        load, cpu_percent, ram_total, ram_free = parse_top_string(data)
        ram_used = ram_total - ram_free

        return load + ' (' + '{:3.1f}'.format(cpu_percent).rjust(5) + '%)   ' + '{:3.1f}'.format(ram_used).rjust(5) + ' / ' + '{:3.1f}'.format(ram_total).rjust(5) + ' GiB (' + '{:3.1f}'.format(ram_used / ram_total * 100).rjust(5) + '%)'

    def render_row(self):
        return self.render_status() + self.host.ljust(self.host_length + 3) + self.render_top()

    def run(self):
        try:
            self.status = 'none'
            out_buf[self.idx] = self.render_row()
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
            self.client.connect(self.host, port = self.port, username = 'root', timeout = 1)
            self.status = 'ok'
            out_buf[self.idx] = self.render_row()
        except Exception as e:
            #print(e)
            self.status = 'fail'
            out_buf[self.idx] = self.render_row()
        self.done = True

def read_config():
    with open('config.yaml', 'r') as stream:
        return yaml.safe_load(stream)

def main():
    config = read_config()
    hosts = []

    host_length = 0
    for host in config['hosts']:
        if len(host['host']) > host_length:
            host_length = len(host['host'])

    print('Host'.center(7 + host_length + 3) + 'Load'.center(25) + '   ' + 'Ram Usage'.center(26))

    config_hosts = config['hosts']
    config_hosts.sort(key=lambda x: x['host'])

    for i, host in enumerate(config_hosts):
        for user_name, user_data in host['users'].items():
            if user_name != 'root':
                continue
            host_keys = []
            if 'groups' in user_data.keys():
                for group in user_data['groups']:
                    if group not in config['groups'].keys():
                        continue
                    for key_name in config['groups'][group]:
                        host_keys.append(config['keys'][key_name])
            if 'keys' in user_data.keys():
                for key_name in user_data['keys']:
                    if key_name not in config['keys'].keys():
                        continue
                    host_keys.append(config['keys'][key_name])
            host_keys = list(set(host_keys)) # Filter duplicates
            if not host_keys:
                continue
            if not 'port' in host:
                host['port'] = 22
            out_buf.append('')
            hosts.append(Host(host['host'], host['port'] or 22, host_length, i))

    for host in hosts:
        host.start()

    end = False
    first = True

    while True:
        screen = []
        for row in out_buf:
            screen.append(row)

        for host in hosts:
            if not host.done:
              break
            end = True

        if first:
            first = False
        else:
            print('\033[' + str(len(screen)) + 'F', end = '')

        print('\n'.join(screen))

        if end:
            break

        time.sleep(0.1)

if __name__ == '__main__':
    main()
