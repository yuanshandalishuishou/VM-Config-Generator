# 使用Alpine Linux + Python 3.11 最小化镜像
FROM python:3.11-alpine

# 安装必要的系统依赖
RUN apk add --no-cache \
    bash \
    libxml2 \
    libxslt \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libxml2-dev \
    libxslt-dev \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# 复制应用代码
COPY . .

# 创建配置目录
RUN mkdir -p config_templates converters

# 创建默认PVE配置模板
RUN cat > /app/config_templates/pve_default.conf << 'EOF'
agent: 1
balloon: 0
boot: order=scsi0;ide2;net0
cores: 2
cpu: host
ide2: none,media=cdrom
machine: q35
memory: 2048
name: vm-default
net0: virtio=62:7C:6B:3A:32:1D,bridge=vmbr0,firewall=1
numa: 0
onboot: 1
ostype: l26
scsi0: local-lvm:vm-100-disk-0,size=32G
scsihw: virtio-scsi-pci
smbios1: uuid=4c4c4544-004b-1010-8032-b3c04f4e3132
sockets: 1
vmgenid: 4c4c4544-004b-1010-8032-b3c04f4e3132
EOF

# 创建默认Libvirt配置模板
RUN cat > /app/config_templates/libvirt_default.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<domain type="kvm">
  <name>vm-default</name>
  <uuid>4c4c4544-004b-1010-8032-b3c04f4e3132</uuid>
  <memory unit="MiB">2048</memory>
  <currentMemory unit="MiB">2048</currentMemory>
  <vcpu placement="static">2</vcpu>
  <os>
    <type arch="x86_64" machine="pc-q35-5.1">hvm</type>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <vmport state="off"/>
  </features>
  <cpu mode="host-passthrough" check="none"/>
  <clock offset="utc">
    <timer name="rtc" tickpolicy="catchup"/>
    <timer name="pit" tickpolicy="delay"/>
    <timer name="hpet" present="no"/>
  </clock>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <pm>
    <suspend-to-mem enabled="no"/>
    <suspend-to-disk enabled="no"/>
  </pm>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="/var/lib/libvirt/images/vm-default.qcow2"/>
      <target dev="vda" bus="virtio"/>
      <address type="pci" domain="0x0000" bus="0x04" slot="0x00" function="0x0"/>
    </disk>
    <controller type="usb" index="0" model="qemu-xhci" ports="15">
      <address type="pci" domain="0x0000" bus="0x02" slot="0x00" function="0x0"/>
    </controller>
    <controller type="sata" index="0">
      <address type="pci" domain="0x0000" bus="0x00" slot="0x1f" function="0x2"/>
    </controller>
    <controller type="pci" index="0" model="pcie-root"/>
    <controller type="pci" index="1" model="pcie-root-port">
      <model name="pcie-root-port"/>
      <target chassis="1" port="0x10"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x02" function="0x0" multifunction="on"/>
    </controller>
    <controller type="pci" index="2" model="pcie-root-port">
      <model name="pcie-root-port"/>
      <target chassis="2" port="0x11"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x02" function="0x1"/>
    </controller>
    <controller type="pci" index="3" model="pcie-root-port">
      <model name="pcie-root-port"/>
      <target chassis="3" port="0x12"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x02" function="0x2"/>
    </controller>
    <controller type="pci" index="4" model="pcie-root-port">
      <model name="pcie-root-port"/>
      <target chassis="4" port="0x13"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x02" function="0x3"/>
    </controller>
    <controller type="pci" index="5" model="pcie-root-port">
      <model name="pcie-root-port"/>
      <target chassis="5" port="0x14"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x02" function="0x4"/>
    </controller>
    <controller type="virtio-serial" index="0">
      <address type="pci" domain="0x0000" bus="0x03" slot="0x00" function="0x0"/>
    </controller>
    <interface type="bridge">
      <mac address="52:54:00:12:34:56"/>
      <source bridge="virbr0"/>
      <model type="virtio"/>
      <address type="pci" domain="0x0000" bus="0x01" slot="0x00" function="0x0"/>
    </interface>
    <serial type="pty">
      <target type="isa-serial" port="0">
        <model name="isa-serial"/>
      </target>
    </serial>
    <console type="pty">
      <target type="serial" port="0"/>
    </console>
    <channel type="unix">
      <target type="virtio" name="org.qemu.guest_agent.0"/>
      <address type="virtio-serial" controller="0" bus="0" port="1"/>
    </channel>
    <input type="tablet" bus="usb">
      <address type="usb" bus="0" port="1"/>
    </input>
    <input type="mouse" bus="ps2"/>
    <input type="keyboard" bus="ps2"/>
    <graphics type="vnc" port="-1" autoport="yes" listen="0.0.0.0">
      <listen type="address" address="0.0.0.0"/>
    </graphics>
    <audio id="1" type="none"/>
    <video>
      <model type="qxl" ram="65536" vram="65536" vgamem="16384" heads="1" primary="yes"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x01" function="0x0"/>
    </video>
    <redirdev bus="usb" type="spicevmc">
      <address type="usb" bus="0" port="2"/>
    </redirdev>
    <redirdev bus="usb" type="spicevmc">
      <address type="usb" bus="0" port="3"/>
    </redirdev>
    <memballoon model="virtio">
      <address type="pci" domain="0x0000" bus="0x05" slot="0x00" function="0x0"/>
    </memballoon>
    <rng model="virtio">
      <backend model="random">/dev/urandom</backend>
      <address type="pci" domain="0x0000" bus="0x06" slot="0x00" function="0x0"/>
    </rng>
  </devices>
</domain>
EOF

# 创建解析器文件
RUN cat > /app/converters/pve_parser.py << 'EOF'
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
EOF

RUN cat > /app/converters/xml_parser.py << 'EOF'
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
EOF

# 创建非root用户
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 34567

# 启动应用
CMD ["python", "app.py"]
