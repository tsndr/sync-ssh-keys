#!/usr/bin/env python3

import paramiko
import threading
import yaml

class task_thread(threading.Thread):
   def __init__(self, host, keys, host_length):
      threading.Thread.__init__(self)
      self.host = host
      self.keys = keys
      self.host_length = host_length
   def run(self):
      update_keys(self.host, self.keys, self.host_length)

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
        ram_factor = 1024
    ram_data = ram_data.strip().split(',')
    ram_total = float(ram_data[0].strip().split(' ', 2)[0].strip()) / ram_factor / 1024
    ram_free = float(ram_data[1].strip().split(' ', 2)[0].strip()) / ram_factor / 1024

    return load, cpu_percent, ram_total, ram_free

def update_keys(host, keys, host_length):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        client.connect(host, username = 'root')

        stdin, stdout, stderr = client.exec_command('top -bn1 | grep "^top\\|^%Cpu\\|^.iB Mem"')
        stdin.close()

        data = stdout.read().decode('utf-8').strip()
        client.close()

        load, cpu_percent, ram_total, ram_free = parse_top_string(data)
        
        print(('✅ ' + host).ljust(host_length + 5) + load + ' (' + '{:3.1f}'.format(cpu_percent).rjust(5) + '%)   ' + '{:3.1f}'.format(ram_total - ram_free).rjust(5) + ' / ' + '{:3.1f}'.format(ram_total).rjust(5) + ' GiB')

    except:
        print('❌ ' + host)

def main():
    config = read_config()

    host_length = 0
    for host in config['hosts']:
        if len(host) > host_length:
            host_length = len(host)

    keys = []
    for key in config['keys']:
        keys.append(key['key'])

    print('Host'.center(host_length + 5) + ' ' + 'Load'.center(25) + '   ' + 'Ram Usage'.center(17))

    for host in config['hosts']:
        try:
            thread = task_thread(host, keys, host_length)
            thread.start()
        except:
            print('❌ ' + host)

if __name__ == '__main__':
    main()