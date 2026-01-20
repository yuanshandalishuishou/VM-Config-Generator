#!/usr/bin/env python3
"""
虚拟机配置生成器
支持从conf/xml导入、编辑配置、生成一键脚本
"""

import os
import json
import tempfile
import uuid
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
import xmltodict
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vm-config-generator-secret-2024')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# 支持的配置类型
CONFIG_TYPES = {
    'pve': {
        'name': 'Proxmox VE (.conf)',
        'extensions': ['.conf'],
        'template': 'config_templates/pve_default.conf'
    },
    'libvirt': {
        'name': 'Libvirt (.xml)',
        'extensions': ['.xml'],
        'template': 'config_templates/libvirt_default.xml'
    }
}

# PVE配置选项分类
PVE_CONFIG_SECTIONS = {
    'basic': {
        'name': '基本配置',
        'options': [
            {'key': 'vmid', 'type': 'number', 'label': '虚拟机ID', 'default': 100, 'min': 100, 'max': 999999},
            {'key': 'name', 'type': 'text', 'label': '虚拟机名称', 'default': 'vm-default'},
            {'key': 'memory', 'type': 'number', 'label': '内存(MB)', 'default': 2048, 'min': 256, 'step': 256},
            {'key': 'balloon', 'type': 'number', 'label': 'Balloon内存(MB)', 'default': 0, 'min': 0},
            {'key': 'cores', 'type': 'number', 'label': 'CPU核心数', 'default': 2, 'min': 1, 'max': 128},
            {'key': 'sockets', 'type': 'number', 'label': 'CPU插槽数', 'default': 1, 'min': 1, 'max': 4},
            {'key': 'cpu', 'type': 'select', 'label': 'CPU类型', 'default': 'host', 
             'options': ['host', 'qemu64', 'kvm64', 'core2duo', 'pentium3', 'qemu32']},
            {'key': 'numa', 'type': 'checkbox', 'label': '启用NUMA', 'default': '0'},
            {'key': 'ostype', 'type': 'select', 'label': '操作系统类型', 'default': 'l26',
             'options': ['l26', 'win11', 'win10', 'win8', 'win7', 'solaris', 'other']},
            {'key': 'onboot', 'type': 'checkbox', 'label': '开机自启', 'default': '1'},
            {'key': 'startup', 'type': 'text', 'label': '启动顺序', 'default': 'order=1'},
            {'key': 'agent', 'type': 'checkbox', 'label': 'QEMU Guest Agent', 'default': '1'},
        ]
    },
    'boot': {
        'name': '启动设置',
        'options': [
            {'key': 'boot', 'type': 'text', 'label': '启动设备顺序', 'default': 'order=scsi0;ide2;net0'},
            {'key': 'bios', 'type': 'select', 'label': 'BIOS', 'default': 'ovmf', 'options': ['ovmf', 'seabios']},
            {'key': 'machine', 'type': 'select', 'label': '机器类型', 'default': 'q35', 
             'options': ['q35', 'pc', 'pc-i440fx']},
            {'key': 'acpi', 'type': 'checkbox', 'label': '启用ACPI', 'default': '1'},
            {'key': 'kvm', 'type': 'checkbox', 'label': '启用KVM硬件虚拟化', 'default': '1'},
        ]
    },
    'disks': {
        'name': '磁盘配置',
        'options': [
            {'key': 'scsi0', 'type': 'text', 'label': 'SCSI磁盘0', 
             'default': 'local-lvm:vm-100-disk-0,size=32G', 'placeholder': '存储:ID,size=大小'},
            {'key': 'scsi1', 'type': 'text', 'label': 'SCSI磁盘1', 'default': ''},
            {'key': 'virtio0', 'type': 'text', 'label': 'VirtIO磁盘0', 'default': ''},
            {'key': 'ide0', 'type': 'text', 'label': 'IDE磁盘0', 'default': ''},
            {'key': 'ide2', 'type': 'text', 'label': 'CD/DVD驱动器', 'default': 'none,media=cdrom'},
            {'key': 'scsihw', 'type': 'select', 'label': 'SCSI控制器类型', 'default': 'virtio-scsi-pci',
             'options': ['virtio-scsi-pci', 'virtio-scsi-single', 'lsi', 'lsi53c895a', 'megasas', 'pvscsi']},
            {'key': 'discard', 'type': 'checkbox', 'label': '启用TRIM', 'default': 'on'},
            {'key': 'cache', 'type': 'select', 'label': '磁盘缓存', 'default': 'writeback',
             'options': ['none', 'writeback', 'writethrough', 'directsync', 'unsafe']},
        ]
    },
    'network': {
        'name': '网络配置',
        'options': [
            {'key': 'net0', 'type': 'text', 'label': '网络接口0', 
             'default': 'virtio=62:7C:6B:3A:32:1D,bridge=vmbr0,firewall=1'},
            {'key': 'net1', 'type': 'text', 'label': '网络接口1', 'default': ''},
            {'key': 'net2', 'type': 'text', 'label': '网络接口2', 'default': ''},
            {'key': 'net3', 'type': 'text', 'label': '网络接口3', 'default': ''},
            {'key': 'bridge', 'type': 'text', 'label': '默认网桥', 'default': 'vmbr0'},
            {'key': 'firewall', 'type': 'checkbox', 'label': '启用防火墙', 'default': '1'},
            {'key': 'mtu', 'type': 'number', 'label': 'MTU大小', 'default': 1500, 'min': 576, 'max': 9000},
        ]
    },
    'display': {
        'name': '显示设置',
        'options': [
            {'key': 'vga', 'type': 'select', 'label': '显卡类型', 'default': 'std',
             'options': ['std', 'cirrus', 'vmware', 'qxl', 'virtio', 'none']},
            {'key': 'memory', 'type': 'number', 'label': '显存大小(MB)', 'default': 16, 'min': 4, 'max': 512},
            {'key': 'serial0', 'type': 'text', 'label': '串口0', 'default': 'socket'},
            {'key': 'usb0', 'type': 'text', 'label': 'USB控制器', 'default': 'host'},
            {'key': 'keyboard', 'type': 'select', 'label': '键盘布局', 'default': 'en-us',
             'options': ['en-us', 'de', 'fr', 'es', 'jp']},
        ]
    },
    'advanced': {
        'name': '高级选项',
        'options': [
            {'key': 'smbios1', 'type': 'text', 'label': 'SMBIOS设置', 
             'default': 'uuid=4c4c4544-004b-1010-8032-b3c04f4e3132'},
            {'key': 'vmgenid', 'type': 'text', 'label': 'VM Generation ID', 
             'default': '4c4c4544-004b-1010-8032-b3c04f4e3132'},
            {'key': 'hugepages', 'type': 'select', 'label': '大页内存', 'default': '',
             'options': ['', '2', '1024', '2048', 'any']},
            {'key': 'hotplug', 'type': 'checkbox', 'label': '启用热插拔', 'default': '1'},
            {'key': 'protection', 'type': 'checkbox', 'label': '防止删除', 'default': '0'},
            {'key': 'tags', 'type': 'text', 'label': '标签', 'default': ''},
            {'key': 'description', 'type': 'textarea', 'label': '描述', 'default': ''},
        ]
    }
}

def load_default_config(config_type='pve'):
    """加载默认配置"""
    config = {}
    
    if config_type == 'pve':
        # 从模板文件加载
        try:
            with open(CONFIG_TYPES['pve']['template'], 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            config[key.strip()] = value.strip()
        except:
            # 如果文件不存在，使用硬编码的默认值
            for section in PVE_CONFIG_SECTIONS.values():
                for opt in section['options']:
                    config[opt['key']] = opt.get('default', '')
    
    return config

def parse_pve_config(content):
    """解析PVE配置文件"""
    config = {}
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            config[key] = value
        elif '=' in line:
            # 处理boot=order=scsi0这样的格式
            parts = line.split('=', 1)
            if len(parts) == 2:
                config[parts[0]] = parts[1]
    
    return config

def parse_libvirt_xml(content):
    """解析Libvirt XML配置文件"""
    try:
        # 使用xmltodict转换为字典
        xml_dict = xmltodict.parse(content)
        
        config = {}
        domain = xml_dict.get('domain', {})
        
        # 基本信息
        config['name'] = domain.get('name', '')
        config['memory'] = domain.get('memory', {}).get('#text', '2048')
        config['memory_unit'] = domain.get('memory', {}).get('@unit', 'MiB')
        config['vcpu'] = domain.get('vcpu', '2')
        
        # CPU配置
        cpu = domain.get('cpu', {})
        if isinstance(cpu, dict):
            config['cpu_mode'] = cpu.get('@mode', '')
            config['cpu_check'] = cpu.get('@check', '')
        
        # 操作系统
        os_config = domain.get('os', {})
        if isinstance(os_config, dict):
            os_type = os_config.get('type', {})
            if isinstance(os_type, dict):
                config['ostype'] = os_type.get('#text', '')
                config['arch'] = os_type.get('@arch', '')
                config['machine'] = os_type.get('@machine', '')
        
        # 设备
        devices = domain.get('devices', {})
        if isinstance(devices, dict):
            # 磁盘
            disks = devices.get('disk', [])
            if not isinstance(disks, list):
                disks = [disks]
            
            for i, disk in enumerate(disks):
                if isinstance(disk, dict):
                    device = disk.get('@device', '')
                    disk_type = disk.get('@type', '')
                    source = disk.get('source', {})
                    target = disk.get('target', {})
                    
                    if device == 'disk':
                        source_file = source.get('@file', '')
                        target_dev = target.get('@dev', '')
                        driver = disk.get('driver', {})
                        if isinstance(driver, dict):
                            driver_type = driver.get('@type', '')
                        
                        if 'vda' in target_dev:
                            config['virtio0'] = f"{source_file},format={driver_type}"
                        elif 'sda' in target_dev:
                            config['scsi0'] = f"{source_file},format={driver_type}"
            
            # 网络
            interfaces = devices.get('interface', [])
            if not isinstance(interfaces, list):
                interfaces = [interfaces]
            
            for i, iface in enumerate(interfaces):
                if isinstance(iface, dict):
                    iface_type = iface.get('@type', '')
                    mac = iface.get('mac', {}).get('@address', '')
                    source = iface.get('source', {})
                    model = iface.get('model', {})
                    
                    bridge = source.get('@bridge', '')
                    model_type = model.get('@type', '') if isinstance(model, dict) else ''
                    
                    config[f'net{i}'] = f"{model_type}={mac},bridge={bridge}"
        
        return config
    except Exception as e:
        print(f"解析XML错误: {e}")
        return {}

def generate_pve_config(config_data):
    """生成PVE配置文件内容"""
    lines = []
    
    # 基本配置
    lines.append(f"# Proxmox VE 配置文件")
    lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"# 虚拟机ID: {config_data.get('vmid', '100')}")
    lines.append("")
    
    # 按类别组织配置
    for section_name, section in PVE_CONFIG_SECTIONS.items():
        section_has_content = False
        
        for opt in section['options']:
            key = opt['key']
            value = config_data.get(key, '')
            if value or value == 0:
                lines.append(f"{key}: {value}")
                section_has_content = True
        
        if section_has_content:
            lines.append("")
    
    # 添加未分类的配置项
    for key, value in config_data.items():
        if key not in [opt['key'] for section in PVE_CONFIG_SECTIONS.values() for opt in section['options']]:
            if value or value == 0:
                lines.append(f"{key}: {value}")
    
    return '\n'.join(lines)

def generate_libvirt_xml(config_data):
    """生成Libvirt XML配置文件内容"""
    
    # 生成UUID
    vm_uuid = config_data.get('smbios1', '').split('=')[-1] if 'uuid=' in config_data.get('smbios1', '') else str(uuid.uuid4())
    
    # 从PVE配置映射到Libvirt
    vm_name = config_data.get('name', 'vm-default')
    memory_mb = int(config_data.get('memory', 2048))
    vcpus = int(config_data.get('cores', 2)) * int(config_data.get('sockets', 1))
    
    # 磁盘配置
    disk_config = ""
    disk_bus = "virtio"
    
    # 解析磁盘配置
    for key in ['scsi0', 'scsi1', 'virtio0', 'ide0']:
        if key in config_data and config_data[key]:
            disk_value = config_data[key]
            if ',' in disk_value:
                disk_parts = disk_value.split(',')
                disk_path = disk_parts[0]
                disk_size = '32G'
                for part in disk_parts:
                    if 'size=' in part:
                        disk_size = part.split('=')[1]
                
                if key.startswith('scsi'):
                    disk_bus = 'scsi'
                    target_dev = 'sda' if key == 'scsi0' else 'sdb'
                elif key.startswith('virtio'):
                    disk_bus = 'virtio'
                    target_dev = 'vda' if key == 'virtio0' else 'vdb'
                else:
                    disk_bus = 'ide'
                    target_dev = 'hda'
                
                disk_config = f'''
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="{disk_path}"/>
      <target dev="{target_dev}" bus="{disk_bus}"/>
      <address type="pci" domain="0x0000" bus="0x04" slot="0x00" function="0x0"/>
    </disk>'''
                break
    
    # 网络配置
    net_config = ""
    if 'net0' in config_data:
        net_value = config_data['net0']
        # 解析MAC地址和网桥
        mac_match = re.search(r'([0-9A-Fa-f:]{17})', net_value)
        bridge_match = re.search(r'bridge=([^,]+)', net_value)
        
        mac = mac_match.group(1) if mac_match else '52:54:00:12:34:56'
        bridge = bridge_match.group(1) if bridge_match else 'virbr0'
        
        net_config = f'''
    <interface type="bridge">
      <mac address="{mac}"/>
      <source bridge="{bridge}"/>
      <model type="virtio"/>
      <address type="pci" domain="0x0000" bus="0x01" slot="0x00" function="0x0"/>
    </interface>'''
    
    # 生成XML
    xml_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<domain type="kvm">
  <name>{vm_name}</name>
  <uuid>{vm_uuid}</uuid>
  <memory unit="MiB">{memory_mb}</memory>
  <currentMemory unit="MiB">{memory_mb}</currentMemory>
  <vcpu placement="static">{vcpus}</vcpu>
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
    <emulator>/usr/bin/qemu-system-x86_64</emulator>{disk_config}{net_config}
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
    <controller type="virtio-serial" index="0">
      <address type="pci" domain="0x0000" bus="0x03" slot="0x00" function="0x0"/>
    </controller>
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
    <video>
      <model type="qxl" ram="65536" vram="65536" vgamem="16384" heads="1" primary="yes"/>
      <address type="pci" domain="0x0000" bus="0x00" slot="0x01" function="0.0"/>
    </video>
    <memballoon model="virtio">
      <address type="pci" domain="0x0000" bus="0x05" slot="0x00" function="0.0"/>
    </memballoon>
  </devices>
</domain>'''
    
    return xml_template

def generate_bash_script(config_data, output_format, output_filename):
    """生成一键部署脚本"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format == 'pve':
        config_content = generate_pve_config(config_data)
        config_path = f"/etc/pve/qemu-server/{config_data.get('vmid', '100')}.conf"
        script = f'''#!/bin/bash
# ============================================
# PVE虚拟机一键部署脚本
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 虚拟机ID: {config_data.get('vmid', '100')}
# ============================================

set -euo pipefail

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# 日志函数
log() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}}

log_info() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{BLUE}}INFO${{NC}}: $*"
}}

log_success() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{GREEN}}SUCCESS${{NC}}: $*"
}}

log_warning() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{YELLOW}}WARNING${{NC}}: $*"
}}

log_error() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{RED}}ERROR${{NC}}: $*"
    exit 1
}}

# 检查是否为root用户
check_root() {{
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
    fi
}}

# 检查PVE环境
check_pve_environment() {{
    log_info "检查PVE环境..."
    
    if [ ! -f /etc/pve/version ]; then
        log_error "未检测到PVE环境"
    fi
    
    if ! command -v pvesh &> /dev/null; then
        log_error "未找到pvesh命令"
    fi
    
    log_success "PVE环境检查通过"
}}

# 检查VM ID是否已存在
check_vmid() {{
    local vmid={config_data.get('vmid', '100')}
    
    if [ -f "/etc/pve/qemu-server/$vmid.conf" ]; then
        log_warning "虚拟机ID $vmid 已存在"
        read -p "是否覆盖现有虚拟机? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "操作已取消"
        fi
    fi
}}

# 创建配置文件
create_config() {{
    local vmid={config_data.get('vmid', '100')}
    local config_file="/etc/pve/qemu-server/$vmid.conf"
    
    log_info "创建配置文件: $config_file"
    
    cat > "$config_file" << 'EOF'
{config_content}
EOF
    
    if [ $? -eq 0 ]; then
        log_success "配置文件创建成功"
    else
        log_error "配置文件创建失败"
    fi
    
    # 设置权限
    chmod 644 "$config_file"
}}

# 创建虚拟磁盘
create_disk() {{
    local vmid={config_data.get('vmid', '100')}
    
    # 解析磁盘配置
    local disk_config="{config_data.get('scsi0', '')}"
    if [ -z "$disk_config" ]; then
        disk_config="{config_data.get('virtio0', '')}"
    fi
    
    if [ -z "$disk_config" ]; then
        log_warning "未配置虚拟磁盘，跳过创建"
        return
    fi
    
    # 提取存储和大小
    local storage=$(echo "$disk_config" | cut -d':' -f1)
    local size="32G"
    
    if echo "$disk_config" | grep -q "size="; then
        size=$(echo "$disk_config" | grep -o "size=[^,]*" | cut -d'=' -f2)
    fi
    
    log_info "创建虚拟磁盘: storage=$storage, size=$size"
    
    # 创建磁盘
    pvesm alloc "$storage" "$vmid" "vm-$vmid-disk-0" "$size"
    
    if [ $? -eq 0 ]; then
        log_success "虚拟磁盘创建成功"
    else
        log_error "虚拟磁盘创建失败"
    fi
}}

# 验证配置
validate_config() {{
    local vmid={config_data.get('vmid', '100')}
    
    log_info "验证虚拟机配置..."
    
    if pvesh get /nodes/$(hostname)/qemu/$vmid/config --noborder 2>/dev/null | grep -q "error"; then
        log_warning "配置验证发现问题，但可能仍可使用"
    else
        log_success "配置验证通过"
    fi
}}

# 显示虚拟机信息
show_vm_info() {{
    local vmid={config_data.get('vmid', '100')}
    
    echo ""
    echo "============================================"
    echo "虚拟机部署完成！"
    echo "============================================"
    echo "虚拟机ID: $vmid"
    echo "虚拟机名称: {config_data.get('name', '未命名')}"
    echo "内存: {config_data.get('memory', '2048')}MB"
    echo "CPU: {config_data.get('sockets', '1')} sockets × {config_data.get('cores', '2')} cores"
    echo "配置文件: /etc/pve/qemu-server/$vmid.conf"
    echo ""
    echo "管理命令:"
    echo "  启动虚拟机: qm start $vmid"
    echo "  停止虚拟机: qm stop $vmid"
    echo "  查看状态: qm status $vmid"
    echo "  删除虚拟机: qm destroy $vmid"
    echo ""
    echo "注意: 请确保磁盘存储路径和网络配置正确"
    echo "============================================"
}}

# 主函数
main() {{
    log_info "开始部署PVE虚拟机"
    
    # 检查环境
    check_root
    check_pve_environment
    check_vmid
    
    # 创建配置
    create_config
    create_disk
    
    # 验证
    validate_config
    
    # 显示信息
    show_vm_info
    
    log_success "部署脚本执行完成！"
}}

# 执行主函数
main "$@"
'''
    
    elif output_format == 'libvirt':
        config_content = generate_libvirt_xml(config_data)
        vm_name = config_data.get('name', 'vm-default').replace(' ', '_')
        config_path = f"/tmp/{vm_name}.xml"
        
        script = f'''#!/bin/bash
# ============================================
# Libvirt虚拟机一键部署脚本
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 虚拟机名称: {config_data.get('name', 'vm-default')}
# ============================================

set -euo pipefail

# 颜色定义
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# 日志函数
log() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}}

log_info() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{BLUE}}INFO${{NC}}: $*"
}}

log_success() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{GREEN}}SUCCESS${{NC}}: $*"
}}

log_warning() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{YELLOW}}WARNING${{NC}}: $*"
}}

log_error() {{
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${{RED}}ERROR${{NC}}: $*"
    exit 1
}}

# 检查依赖
check_dependencies() {{
    log_info "检查系统依赖..."
    
    # 检查virsh
    if ! command -v virsh &> /dev/null; then
        log_error "未找到virsh命令，请安装libvirt-clients"
    fi
    
    # 检查qemu-img
    if ! command -v qemu-img &> /dev/null; then
        log_error "未找到qemu-img命令，请安装qemu-utils"
    fi
    
    # 检查libvirtd服务
    if ! systemctl is-active --quiet libvirtd; then
        log_warning "libvirtd服务未运行，尝试启动..."
        systemctl start libvirtd || log_error "启动libvirtd失败"
    fi
    
    log_success "依赖检查通过"
}}

# 检查虚拟机是否已存在
check_vm_exists() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    
    if virsh list --all --name | grep -q "^$vm_name$"; then
        log_warning "虚拟机 '$vm_name' 已存在"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "操作已取消"
        fi
        
        # 删除现有虚拟机
        log_info "删除现有虚拟机..."
        virsh destroy "$vm_name" 2>/dev/null || true
        virsh undefine "$vm_name" 2>/dev/null || true
    fi
}}

# 创建XML配置文件
create_xml_config() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    local xml_file="/tmp/$vm_name.xml"
    
    log_info "创建XML配置文件: $xml_file"
    
    cat > "$xml_file" << 'EOF'
{config_content}
EOF
    
    if [ $? -eq 0 ]; then
        log_success "XML配置文件创建成功"
    else
        log_error "XML配置文件创建失败"
    fi
}}

# 创建虚拟磁盘
create_virtual_disk() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    local disk_path="/var/lib/libvirt/images/$vm_name.qcow2"
    
    # 检查是否已存在磁盘配置
    local disk_config="{config_data.get('scsi0', config_data.get('virtio0', ''))}"
    if [ -z "$disk_config" ]; then
        log_warning "未配置虚拟磁盘，跳过创建"
        return
    fi
    
    # 提取磁盘大小
    local size="32G"
    if echo "$disk_config" | grep -q "size="; then
        size=$(echo "$disk_config" | grep -o "size=[^,]*" | cut -d'=' -f2)
    fi
    
    log_info "创建虚拟磁盘: $disk_path ($size)"
    
    # 创建目录（如果不存在）
    mkdir -p /var/lib/libvirt/images
    
    # 创建磁盘
    qemu-img create -f qcow2 "$disk_path" "$size"
    
    if [ $? -eq 0 ]; then
        log_success "虚拟磁盘创建成功"
        
        # 设置权限
        chown libvirt-qemu:libvirt-qemu "$disk_path" 2>/dev/null || true
        chmod 660 "$disk_path"
    else
        log_error "虚拟磁盘创建失败"
    fi
}}

# 定义虚拟机
define_virtual_machine() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    local xml_file="/tmp/$vm_name.xml"
    
    log_info "定义虚拟机: $vm_name"
    
    virsh define "$xml_file"
    
    if [ $? -eq 0 ]; then
        log_success "虚拟机定义成功"
    else
        log_error "虚拟机定义失败"
    fi
}}

# 配置自动启动
configure_autostart() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    
    if [ "{config_data.get('onboot', '0')}" = "1" ]; then
        log_info "配置虚拟机开机自启"
        virsh autostart "$vm_name"
        
        if [ $? -eq 0 ]; then
            log_success "开机自启配置成功"
        else
            log_warning "开机自启配置失败"
        fi
    fi
}}

# 显示虚拟机信息
show_vm_info() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    
    echo ""
    echo "============================================"
    echo "Libvirt虚拟机部署完成！"
    echo "============================================"
    echo "虚拟机名称: $vm_name"
    echo "内存: {config_data.get('memory', '2048')}MB"
    echo "CPU: {config_data.get('vcpus', '2')} vCPUs"
    echo "磁盘: /var/lib/libvirt/images/$vm_name.qcow2"
    echo ""
    echo "管理命令:"
    echo "  启动虚拟机: virsh start $vm_name"
    echo "  停止虚拟机: virsh shutdown $vm_name"
    echo "  查看状态: virsh dominfo $vm_name"
    echo "  控制台连接: virsh console $vm_name"
    echo "  删除虚拟机: virsh undefine $vm_name"
    echo ""
    echo "VNC连接: 使用VNC客户端连接到localhost:5900"
    echo "注意: 请确保libvirt网络配置正确"
    echo "============================================"
}}

# 验证配置
validate_configuration() {{
    local vm_name="{config_data.get('name', 'vm-default').replace(' ', '_')}"
    
    log_info "验证虚拟机配置..."
    
    if virsh dominfo "$vm_name" &>/dev/null; then
        log_success "虚拟机配置验证通过"
    else
        log_warning "虚拟机可能未正确定义"
    fi
}}

# 主函数
main() {{
    log_info "开始部署Libvirt虚拟机"
    
    # 检查依赖
    check_dependencies
    
    # 检查虚拟机是否已存在
    check_vm_exists
    
    # 创建虚拟磁盘
    create_virtual_disk
    
    # 创建XML配置
    create_xml_config
    
    # 定义虚拟机
    define_virtual_machine
    
    # 配置自动启动
    configure_autostart
    
    # 验证配置
    validate_configuration
    
    # 显示信息
    show_vm_info
    
    log_success "部署脚本执行完成！"
}}

# 执行主函数
main "$@"
'''
    
    return script

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html', 
                         config_types=CONFIG_TYPES,
                         sections=PVE_CONFIG_SECTIONS)

@app.route('/editor')
def editor():
    """配置编辑器页面"""
    config_type = request.args.get('type', 'pve')
    session['config_type'] = config_type
    
    # 加载默认配置
    config_data = load_default_config(config_type)
    
    return render_template('editor.html',
                         config_type=config_type,
                         config_data=config_data,
                         sections=PVE_CONFIG_SECTIONS)

@app.route('/import', methods=['GET', 'POST'])
def import_config():
    """导入配置文件页面"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        file_type = request.form.get('type', 'pve')
        
        # 读取文件内容
        content = file.read().decode('utf-8', errors='ignore')
        
        # 解析配置文件
        if file_type == 'pve':
            config_data = parse_pve_config(content)
        else:  # libvirt
            config_data = parse_libvirt_xml(content)
        
        return jsonify({
            'success': True,
            'config': config_data,
            'type': file_type
        })
    
    return render_template('import.html', config_types=CONFIG_TYPES)

@app.route('/api/save-config', methods=['POST'])
def save_config():
    """保存配置数据"""
    try:
        config_data = request.json.get('config', {})
        config_type = request.json.get('type', 'pve')
        
        # 保存到session
        session['config_data'] = config_data
        session['config_type'] = config_type
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-default', methods=['GET'])
def load_default():
    """加载默认配置"""
    config_type = request.args.get('type', 'pve')
    config_data = load_default_config(config_type)
    return jsonify({'config': config_data})

@app.route('/generate', methods=['POST'])
def generate():
    """生成配置文件或脚本"""
    try:
        config_data = request.json.get('config', {})
        output_type = request.json.get('output_type', 'script')  # script, pve, libvirt
        output_format = request.json.get('output_format', 'pve')  # pve, libvirt
        
        if output_type == 'script':
            # 生成一键脚本
            script = generate_bash_script(config_data, output_format, 'vm-deploy.sh')
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name='vm-deploy.sh',
                mimetype='application/x-shellscript'
            )
        
        elif output_type == 'pve':
            # 生成PVE配置文件
            config_content = generate_pve_config(config_data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(config_content)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f'vm-{config_data.get("vmid", "100")}.conf',
                mimetype='text/plain'
            )
        
        elif output_type == 'libvirt':
            # 生成Libvirt XML文件
            config_content = generate_libvirt_xml(config_data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(config_content)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f'{config_data.get("name", "vm")}.xml',
                mimetype='application/xml'
            )
        
        else:
            return jsonify({'error': '不支持的输出类型'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview():
    """预览配置文件"""
    try:
        config_data = request.json.get('config', {})
        output_format = request.json.get('format', 'pve')
        
        if output_format == 'pve':
            content = generate_pve_config(config_data)
        else:
            content = generate_libvirt_xml(config_data)
        
        return jsonify({
            'success': True,
            'content': content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=34567, debug=False)