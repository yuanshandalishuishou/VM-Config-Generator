#!/usr/bin/env python3
"""
Libvirt XML配置文件解析器
"""

import xml.etree.ElementTree as ET
import xmltodict
import re

def parse_libvirt_xml(content):
    """
    解析Libvirt XML配置文件
    
    Args:
        content (str): XML配置文件内容
        
    Returns:
        dict: 解析后的配置字典
    """
    try:
        # 使用xmltodict转换为字典
        xml_dict = xmltodict.parse(content)
        
        config = {}
        
        # 获取domain元素
        domain = xml_dict.get('domain', {})
        
        # 基本信息
        config['name'] = domain.get('name', '')
        
        # 内存配置
        memory = domain.get('memory', {})
        if isinstance(memory, dict):
            config['memory'] = memory.get('#text', '2048')
            config['memory_unit'] = memory.get('@unit', 'MiB')
        else:
            config['memory'] = memory
        
        # 当前内存
        current_memory = domain.get('currentMemory', {})
        if isinstance(current_memory, dict):
            config['current_memory'] = current_memory.get('#text', '2048')
        else:
            config['current_memory'] = current_memory
        
        # CPU配置
        config['vcpu'] = domain.get('vcpu', '2')
        
        cpu = domain.get('cpu', {})
        if isinstance(cpu, dict):
            config['cpu_mode'] = cpu.get('@mode', '')
            config['cpu_check'] = cpu.get('@check', '')
        
        # 操作系统配置
        os_config = domain.get('os', {})
        if isinstance(os_config, dict):
            os_type = os_config.get('type', {})
            if isinstance(os_type, dict):
                config['ostype'] = os_type.get('#text', '')
                config['arch'] = os_type.get('@arch', '')
                config['machine'] = os_type.get('@machine', '')
            
            # 启动顺序
            boot = os_config.get('boot', [])
            if not isinstance(boot, list):
                boot = [boot]
            
            boot_order = []
            for boot_dev in boot:
                if isinstance(boot_dev, dict):
                    dev = boot_dev.get('@dev', '')
                    boot_order.append(dev)
            
            if boot_order:
                config['boot'] = 'order=' + ';'.join(boot_order)
        
        # 设备配置
        devices = domain.get('devices', {})
        if isinstance(devices, dict):
            parse_devices(devices, config)
        
        # 特性
        features = domain.get('features', {})
        if isinstance(features, dict):
            config['acpi'] = '1' if features.get('acpi') else '0'
            config['apic'] = '1' if features.get('apic') else '0'
        
        return config
        
    except Exception as e:
        print(f"解析XML错误: {e}")
        return {}

def parse_devices(devices, config):
    """
    解析设备配置
    
    Args:
        devices (dict): 设备字典
        config (dict): 配置字典
    """
    # 磁盘设备
    disks = devices.get('disk', [])
    if not isinstance(disks, list):
        disks = [disks]
    
    disk_index = 0
    for disk in disks:
        if isinstance(disk, dict):
            parse_disk_device(disk, config, disk_index)
            disk_index += 1
    
    # 网络设备
    interfaces = devices.get('interface', [])
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    
    net_index = 0
    for iface in interfaces:
        if isinstance(iface, dict):
            parse_network_device(iface, config, net_index)
            net_index += 1
    
    # 显示设备
    graphics = devices.get('graphics', {})
    if isinstance(graphics, dict):
        config['vga'] = graphics.get('@type', 'vnc')
    
    video = devices.get('video', {})
    if isinstance(video, dict):
        model = video.get('model', {})
        if isinstance(model, dict):
            config['vga'] = model.get('@type', 'qxl')

def parse_disk_device(disk, config, index):
    """
    解析磁盘设备
    
    Args:
        disk (dict): 磁盘配置字典
        config (dict): 配置字典
        index (int): 磁盘索引
    """
    device_type = disk.get('@device', '')
    disk_type = disk.get('@type', '')
    
    if device_type == 'disk':
        # 源文件
        source = disk.get('source', {})
        if isinstance(source, dict):
            source_file = source.get('@file', '')
        
        # 目标设备
        target = disk.get('target', {})
        if isinstance(target, dict):
            target_dev = target.get('@dev', '')
        
        # 驱动程序
        driver = disk.get('driver', {})
        if isinstance(driver, dict):
            driver_type = driver.get('@type', '')
            driver_cache = driver.get('@cache', '')
        
        # 构建配置字符串
        config_str = source_file
        
        # 添加格式
        if driver_type:
            config_str += f",format={driver_type}"
        
        # 添加缓存
        if driver_cache:
            config_str += f",cache={driver_cache}"
        
        # 根据设备类型设置不同的key
        if 'vda' in target_dev or 'vdb' in target_dev:
            key = f"virtio{index}"
        elif 'sda' in target_dev or 'sdb' in target_dev:
            key = f"scsi{index}"
        elif 'hda' in target_dev or 'hdb' in target_dev:
            key = f"ide{index}"
        else:
            key = f"disk{index}"
        
        config[key] = config_str

def parse_network_device(iface, config, index):
    """
    解析网络设备
    
    Args:
        iface (dict): 网络接口配置字典
        config (dict): 配置字典
        index (int): 网络接口索引
    """
    iface_type = iface.get('@type', '')
    mac = iface.get('mac', {})
    if isinstance(mac, dict):
        mac_address = mac.get('@address', '')
    
    source = iface.get('source', {})
    model = iface.get('model', {})
    
    # 获取网桥
    bridge = ''
    if iface_type == 'bridge' and isinstance(source, dict):
        bridge = source.get('@bridge', '')
    elif iface_type == 'network' and isinstance(source, dict):
        bridge = source.get('@network', '')
    
    # 获取模型
    model_type = ''
    if isinstance(model, dict):
        model_type = model.get('@type', '')
    
    # 构建配置字符串
    config_str = f"{model_type}={mac_address},bridge={bridge}"
    
    # 防火墙
    if iface.get('filterref'):
        config_str += ",firewall=1"
    
    config[f"net{index}"] = config_str

def generate_libvirt_xml(config_dict):
    """
    根据配置字典生成Libvirt XML配置文件
    
    Args:
        config_dict (dict): 配置字典
        
    Returns:
        str: Libvirt XML配置文件内容
    """
    # 创建根元素
    root = ET.Element('domain')
    root.set('type', 'kvm')
    
    # 名称
    name = ET.SubElement(root, 'name')
    name.text = config_dict.get('name', 'vm-default')
    
    # UUID
    uuid = ET.SubElement(root, 'uuid')
    uuid.text = config_dict.get('smbios1', '').split('=')[-1] if 'uuid=' in config_dict.get('smbios1', '') else '4c4c4544-004b-1010-8032-b3c04f4e3132'
    
    # 内存
    memory = ET.SubElement(root, 'memory')
    memory.set('unit', 'MiB')
    memory.text = str(config_dict.get('memory', 2048))
    
    current_memory = ET.SubElement(root, 'currentMemory')
    current_memory.set('unit', 'MiB')
    current_memory.text = str(config_dict.get('memory', 2048))
    
    # VCPU
    vcpu = ET.SubElement(root, 'vcpu')
    vcpu.set('placement', 'static')
    vcpu.text = str(int(config_dict.get('cores', 2)) * int(config_dict.get('sockets', 1)))
    
    # 操作系统
    os = ET.SubElement(root, 'os')
    os_type = ET.SubElement(os, 'type')
    os_type.set('arch', 'x86_64')
    os_type.set('machine', 'pc-q35-5.1')
    os_type.text = 'hvm'
    
    boot = ET.SubElement(os, 'boot')
    boot.set('dev', 'hd')
    
    # 特性
    features = ET.SubElement(root, 'features')
    if config_dict.get('acpi', '1') == '1':
        ET.SubElement(features, 'acpi')
    if config_dict.get('apic', '1') == '1':
        ET.SubElement(features, 'apic')
    
    # CPU
    cpu = ET.SubElement(root, 'cpu')
    cpu.set('mode', 'host-passthrough')
    cpu.set('check', 'none')
    
    # 设备
    devices = ET.SubElement(root, 'devices')
    
    # 模拟器
    emulator = ET.SubElement(devices, 'emulator')
    emulator.text = '/usr/bin/qemu-system-x86_64'
    
    # 磁盘设备
    parse_disk_configs(config_dict, devices)
    
    # 网络设备
    parse_network_configs(config_dict, devices)
    
    # 其他标准设备
    add_standard_devices(devices)
    
    # 转换为XML字符串
    xml_str = ET.tostring(root, encoding='unicode')
    
    # 美化输出
    from xml.dom import minidom
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')
    
    return pretty_xml

def parse_disk_configs(config_dict, devices):
    """
    解析磁盘配置并添加到设备列表
    
    Args:
        config_dict (dict): 配置字典
        devices (ET.Element): 设备元素
    """
    # 扫描磁盘配置
    disk_configs = []
    for key, value in config_dict.items():
        if key.startswith(('scsi', 'virtio', 'ide')) and 'disk' not in key and value:
            disk_configs.append((key, value))
    
    # 添加磁盘设备
    for i, (key, config_str) in enumerate(disk_configs):
        disk = ET.SubElement(devices, 'disk')
        disk.set('type', 'file')
        disk.set('device', 'disk')
        
        # 解析配置字符串
        parts = config_str.split(',')
        source_file = parts[0]
        
        # 源文件
        source = ET.SubElement(disk, 'source')
        source.set('file', source_file)
        
        # 驱动程序
        driver = ET.SubElement(disk, 'driver')
        driver.set('name', 'qemu')
        
        # 检测格式
        for part in parts[1:]:
            if part.startswith('format='):
                driver.set('type', part.split('=')[1])
                break
        else:
            driver.set('type', 'qcow2')
        
        # 目标设备
        target = ET.SubElement(disk, 'target')
        
        if key.startswith('virtio'):
            target.set('dev', f'vd{chr(97 + i)}')  # vda, vdb, etc.
            target.set('bus', 'virtio')
        elif key.startswith('scsi'):
            target.set('dev', f'sd{chr(97 + i)}')  # sda, sdb, etc.
            target.set('bus', 'scsi')
        elif key.startswith('ide'):
            target.set('dev', f'hd{chr(97 + i)}')  # hda, hdb, etc.
            target.set('bus', 'ide')

def parse_network_configs(config_dict, devices):
    """
    解析网络配置并添加到设备列表
    
    Args:
        config_dict (dict): 配置字典
        devices (ET.Element): 设备元素
    """
    # 扫描网络配置
    net_configs = []
    for key, value in config_dict.items():
        if key.startswith('net') and value:
            net_configs.append((key, value))
    
    # 添加网络设备
    for i, (key, config_str) in enumerate(net_configs):
        interface = ET.SubElement(devices, 'interface')
        interface.set('type', 'bridge')
        
        # 解析配置字符串
        parts = config_str.split(',')
        
        # 第一个部分是模型和MAC
        first_part = parts[0]
        if '=' in first_part:
            model, mac = first_part.split('=', 1)
        else:
            model = first_part
            mac = '52:54:00:12:34:56'
        
        # MAC地址
        mac_elem = ET.SubElement(interface, 'mac')
        mac_elem.set('address', mac)
        
        # 源网桥
        source = ET.SubElement(interface, 'source')
        
        # 查找网桥
        bridge = 'virbr0'
        for part in parts[1:]:
            if part.startswith('bridge='):
                bridge = part.split('=')[1]
                break
        
        source.set('bridge', bridge)
        
        # 模型
        model_elem = ET.SubElement(interface, 'model')
        model_elem.set('type', model)
        
        # 防火墙
        for part in parts[1:]:
            if part == 'firewall=1':
                filterref = ET.SubElement(interface, 'filterref')
                filterref.set('filter', 'clean-traffic')
                break

def add_standard_devices(devices):
    """
    添加标准设备
    
    Args:
        devices (ET.Element): 设备元素
    """
    # 串口
    serial = ET.SubElement(devices, 'serial')
    serial.set('type', 'pty')
    target = ET.SubElement(serial, 'target')
    target.set('type', 'isa-serial')
    target.set('port', '0')
    
    # 控制台
    console = ET.SubElement(devices, 'console')
    console.set('type', 'pty')
    target = ET.SubElement(console, 'target')
    target.set('type', 'serial')
    target.set('port', '0')
    
    # 显卡
    video = ET.SubElement(devices, 'video')
    model = ET.SubElement(video, 'model')
    model.set('type', 'qxl')
    model.set('ram', '65536')
    model.set('vram', '65536')
    model.set('vgamem', '16384')
    model.set('heads', '1')
    model.set('primary', 'yes')
    
    # 输入设备
    input1 = ET.SubElement(devices, 'input')
    input1.set('type', 'tablet')
    input1.set('bus', 'usb')
    
    input2 = ET.SubElement(devices, 'input')
    input2.set('type', 'mouse')
    input2.set('bus', 'ps2')
    
    input3 = ET.SubElement(devices, 'input')
    input3.set('type', 'keyboard')
    input3.set('bus', 'ps2')