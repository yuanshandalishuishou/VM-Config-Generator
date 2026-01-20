#!/usr/bin/env python3
"""
PVE配置文件解析器
"""

import re

def parse_pve_config(content):
    """
    解析PVE配置文件内容
    
    Args:
        content (str): PVE配置文件内容
        
    Returns:
        dict: 解析后的配置字典
    """
    config = {}
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        
        # 解析键值对
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            config[key] = value
            
        # 处理特殊格式，如 boot=order=scsi0
        elif '=' in line:
            # 检查是否有多个等号
            if line.count('=') > 1:
                # 第一个等号前是key，后面是value
                first_eq = line.find('=')
                key = line[:first_eq].strip()
                value = line[first_eq + 1:].strip()
                config[key] = value
            else:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    return config

def parse_disk_config(disk_string):
    """
    解析磁盘配置字符串
    
    Args:
        disk_string (str): 磁盘配置字符串，如 "local-lvm:vm-100-disk-0,size=32G"
        
    Returns:
        dict: 解析后的磁盘配置
    """
    disk_config = {}
    
    if not disk_string:
        return disk_config
    
    # 分割存储和参数
    parts = disk_string.split(',')
    
    # 第一个部分是存储路径
    storage_part = parts[0]
    if ':' in storage_part:
        storage_type, storage_path = storage_part.split(':', 1)
        disk_config['storage_type'] = storage_type
        disk_config['storage_path'] = storage_path
    else:
        disk_config['storage_path'] = storage_part
    
    # 解析其他参数
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            disk_config[key] = value
        else:
            disk_config[part] = True
    
    return disk_config

def parse_network_config(net_string):
    """
    解析网络配置字符串
    
    Args:
        net_string (str): 网络配置字符串，如 "virtio=62:7C:6B:3A:32:1D,bridge=vmbr0,firewall=1"
        
    Returns:
        dict: 解析后的网络配置
    """
    net_config = {}
    
    if not net_string:
        return net_config
    
    parts = net_string.split(',')
    
    # 第一个部分是模型和MAC
    first_part = parts[0]
    if '=' in first_part:
        model, mac = first_part.split('=', 1)
        net_config['model'] = model
        net_config['mac'] = mac
    else:
        net_config['model'] = first_part
    
    # 解析其他参数
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            net_config[key] = value
        else:
            net_config[part] = True
    
    return net_config

def generate_pve_config(config_dict):
    """
    根据配置字典生成PVE配置文件内容
    
    Args:
        config_dict (dict): 配置字典
        
    Returns:
        str: PVE配置文件内容
    """
    lines = []
    
    # 基本配置
    basic_keys = ['vmid', 'name', 'memory', 'balloon', 'cores', 'sockets', 
                  'cpu', 'numa', 'ostype', 'onboot', 'startup', 'agent']
    
    for key in basic_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 启动设置
    boot_keys = ['boot', 'bios', 'machine', 'acpi', 'kvm']
    for key in boot_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 磁盘配置
    disk_keys = ['scsi0', 'scsi1', 'virtio0', 'ide0', 'ide2', 'scsihw', 'discard', 'cache']
    for key in disk_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 网络配置
    net_keys = ['net0', 'net1', 'net2', 'net3', 'bridge', 'firewall', 'mtu']
    for key in net_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 显示设置
    display_keys = ['vga', 'memory', 'serial0', 'usb0', 'keyboard']
    for key in display_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 高级选项
    advanced_keys = ['smbios1', 'vmgenid', 'hugepages', 'hotplug', 
                     'protection', 'tags', 'description']
    for key in advanced_keys:
        if key in config_dict and config_dict[key]:
            lines.append(f"{key}: {config_dict[key]}")
    
    lines.append("")
    
    # 其他配置项
    for key, value in config_dict.items():
        if key not in (basic_keys + boot_keys + disk_keys + net_keys + 
                       display_keys + advanced_keys):
            if value:
                lines.append(f"{key}: {value}")
    
    return '\n'.join(lines)