from netmiko import ConnectHandler
import netmiko
import getpass
import time
import pprint
from tabulate import tabulate
import re
import networkx as nx
import matplotlib.pyplot as plt


# get the start time
st = time.time()



username = getpass.getpass('SSH UserID: ')
passwd = getpass.getpass('Password to Jumphost: ')
connection = ConnectHandler(
device_type='linux',
host='jumphost',  
username=username, 
password=passwd, 
) 


devices=[]
file = open("devices.txt","r")
for line in file:
    devices.append(line.strip('\n').split(";"))
pprint.pprint(devices)




def write_channel(command):
    connection.write_channel(command)
    time.sleep(1)
    output = connection.read_channel()
    print(output)

def write_channel2(command):
    connection.write_channel(command)
    time.sleep(5)
    output = connection.read_channel()
    print(output)


def send_command(command):
    devices=connection.send_command(command, use_textfsm=True)
    time.sleep(1)
    output = connection.read_channel()
    print(output)
    return devices

def change_device(device):
    netmiko.redispatch(connection, device_type=device)
    print(connection.find_prompt())

def change_ports(x):
    x=x.replace("TenGigabitEthernet", "Te")
    x=x.replace("TwentyFiveGigE", "Twe")
    x=x.replace("GigabitEthernet", "Gi")
    x=x.replace("Ethernet", "Eth") 
    return x   

neighbors=[]
description=[]
description2=[]

for x in devices:
    
    write_channel("ssh "+x[0]+"@"+x[1]+"\n")
    write_channel2("yes\n")
    write_channel(x[2]+"\n")

    if x[4]!="":
        write_channel("enable \n") 
        write_channel(x[4]+"\n") 
    change_device(x[3])

    interfaces=send_command("show cdp neighbors detail")
    show_desc=send_command("show interface description")
    pprint.pprint(show_desc)
    pprint.pprint(interfaces)


    for y in interfaces:
        y["local_port"]=change_ports(y["local_port"])
        y["remote_port"]=change_ports(y["remote_port"])
        if "dest_host" in y.keys():
            y["destination_host"]=y["dest_host"]
        host=y["destination_host"]
        if "sysname" in y.keys():
            if y["sysname"]!="":
                host=y["sysname"]  
        add=True
        for i in show_desc:
            if i["port"]==y["local_port"]:   
                if "descrip" in i.keys():
                     i["description"]=i["descrip"]          
                desc="**** Uplink to "+host+ " "+y["remote_port"]+" ****"
                description.append([x[1],y["local_port"],y["remote_port"],i["description"],desc])
                add=False
        if add:
            desc="**** Uplink to "+host+ " "+y["remote_port"]+" ****"
            description.append([x[1],y["local_port"],y["remote_port"],"",desc])
    for y in interfaces:
        if "dest_host" in y.keys():
            y["destination_host"]=y["dest_host"]
        host=y["destination_host"]
        if "sysname" in y.keys():
            if y["sysname"]!="":
                host=y["sysname"]   
        neighbors.append([x[1],y["local_port"],host,y["remote_port"]])
    output=write_channel("exit\n")
    
print(tabulate(neighbors, headers=["Device","Local port","Connected with","neighbor port"], tablefmt="grid"))
print(tabulate(description, headers=["Device","Local port","Neighbor port","Actual desc","Generated Desc"], tablefmt="grid"))

connection.disconnect()
et = time.time()
elapsed_time = et - st
print('Execution time:', int(elapsed_time), 'seconds')

