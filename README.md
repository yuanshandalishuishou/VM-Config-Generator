# VM-Config-Generator

# VM配置生成器 (VM Config Generator)

一个功能强大的虚拟机配置生成器，支持PVE (.conf) 和 Libvirt (.xml) 格式的配置文件创建、编辑和转换，并生成一键部署脚本。

## 🌟 功能特点

### 1. **全功能配置编辑**
- **完整配置选项**：覆盖所有虚拟机配置参数（基本、启动、磁盘、网络、显示、高级）
- **智能默认值**：为每个配置项提供合理的默认值
- **实时预览**：编辑时实时预览生成的配置文件
- **配置分类**：按功能模块组织配置项，便于查找和编辑

### 2. **灵活的导入功能**
- **PVE配置导入**：从现有的Proxmox VE (.conf) 文件导入
- **Libvirt配置导入**：从现有的Libvirt (.xml) 文件导入
- **智能解析**：自动解析配置文件中的关键参数
- **配置继承**：导入后可在原配置基础上修改

### 3. **多种导出格式**
- **PVE配置文件**：生成适用于Proxmox VE的.conf文件
- **Libvirt配置文件**：生成适用于KVM/QEMU的.xml文件
- **一键部署脚本**：生成自动化的Bash部署脚本

### 4. **一键脚本功能**
- **自动化部署**：自动创建虚拟机配置和磁盘
- **错误处理**：完善的错误检查和异常处理
- **详细日志**：执行过程详细记录，便于排错
- **环境检查**：自动检查系统依赖和环境配置

### 5. **用户友好界面**
- **响应式设计**：适配桌面和移动设备
- **直观操作**：向导式界面，操作简单直观
- **实时保存**：自动保存配置更改
- **配置预览**：实时预览生成的配置文件

## 🚀 快速开始

### 环境要求
- Docker 20.10+
- 现代Web浏览器（Chrome 90+, Firefox 88+, Edge 90+）

### Docker部署

```bash
# 1. 克隆或下载项目代码
git clone https://github.com/yuanshandalishuishou/VM-Config-Generator.git
cd VM-Config-Generator

# 2. 构建Docker镜像
docker build -t vm-config-generator .

# 3. 运行容器
docker run -d \
  --name vm-config-generator \
  -p 34567:34567 \
  -v $(pwd)/configs:/app/configs \
  -e SECRET_KEY=your-secret-key-here \
  vm-config-generator

# 4. 访问应用
# 打开浏览器访问：http://localhost:34567
```

### 快速测试
```bash
# 使用示例配置快速测试
docker run -d \
  --name vm-config-generator-test \
  -p 34567:34567 \
  vm-config-generator
```

## 📋 详细使用方法

### 1. 创建新配置
1. 访问应用首页，点击"创建新配置"
2. 选择配置类型（PVE或Libvirt）
3. 在编辑器中填写或修改配置参数
4. 实时预览生成的配置文件
5. 选择导出格式并下载

### 2. 导入现有配置
1. 在首页点击"导入配置文件"
2. 选择配置文件类型（PVE .conf 或 Libvirt .xml）
3. 上传配置文件
4. 系统自动解析并显示预览
5. 在编辑器中修改配置后导出

### 3. 生成一键脚本
1. 在编辑器页面完成配置编辑
2. 切换到"导出选项"标签页
3. 选择"一键部署脚本 (.sh)"
4. 选择目标平台（PVE或Libvirt）
5. 下载生成的脚本文件

### 4. 执行部署脚本
```bash
# 给脚本执行权限
chmod +x vm-deploy.sh

# 执行脚本（需要root权限）
sudo ./vm-deploy.sh

# 查看执行日志
tail -f /var/log/vm-deploy.log
```

## 🔧 配置选项说明

### 基本配置
- **虚拟机ID** (vmid): PVE中虚拟机的唯一标识
- **虚拟机名称** (name): 虚拟机显示名称
- **内存** (memory): 分配给虚拟机的内存大小（MB）
- **CPU核心数** (cores): 虚拟CPU核心数量
- **CPU插槽数** (sockets): CPU插槽数量
- **操作系统类型** (ostype): 虚拟机操作系统类型

### 磁盘配置
- **SCSI磁盘** (scsi0, scsi1): SCSI接口磁盘配置
- **VirtIO磁盘** (virtio0): VirtIO接口磁盘配置
- **IDE磁盘** (ide0): IDE接口磁盘配置
- **CD/DVD驱动器** (ide2): 光盘驱动器配置
- **磁盘缓存** (cache): 磁盘缓存策略
- **启用TRIM** (discard): 是否启用TRIM支持

### 网络配置
- **网络接口** (net0, net1): 虚拟网络接口配置
- **MAC地址**: 虚拟网卡MAC地址
- **网桥** (bridge): 连接的物理网桥
- **防火墙** (firewall): 是否启用防火墙
- **MTU大小**: 网络最大传输单元

### 显示设置
- **显卡类型** (vga): 虚拟显卡类型
- **显存大小**: 分配给虚拟显卡的显存
- **VNC配置**: 远程桌面访问设置
- **SPICE支持**: 是否启用SPICE协议

### 高级选项
- **SMBIOS设置** (smbios1): 系统管理BIOS配置
- **VM Generation ID**: 虚拟机生成ID
- **大页内存** (hugepages): 大页内存支持
- **热插拔** (hotplug): 是否启用热插拔
- **描述** (description): 虚拟机描述信息

## 📁 项目结构

```
vm-config-generator/
├── app.py                    # Flask应用主文件
├── requirements.txt          # Python依赖包
├── Dockerfile               # Docker构建文件
├── config_templates/        # 默认配置模板
│   ├── pve_default.conf    # PVE默认配置
│   └── libvirt_default.xml # Libvirt默认配置
├── converters/              # 配置文件转换器
│   ├── pve_parser.py       # PVE配置解析器
│   └── xml_parser.py       # XML配置解析器
├── templates/              # HTML模板文件
│   ├── index.html         # 首页
│   ├── editor.html        # 配置编辑器
│   └── import.html        # 导入页面
└── static/                # 静态资源（可选）
```

## 🔌 API接口

### 获取默认配置
```
GET /api/load-default?type={config_type}
```
- 参数：`config_type` - 配置类型（pve/libvirt）
- 返回：默认配置JSON

### 预览配置
```
POST /api/preview
```
- 请求体：配置数据JSON
- 返回：生成的配置文件内容

### 保存配置
```
POST /api/save-config
```
- 请求体：配置数据和类型
- 返回：保存状态

### 生成配置文件
```
POST /generate
```
- 请求体：配置数据和输出格式
- 返回：配置文件或脚本文件下载

## 🐳 Docker配置选项

### 环境变量
```bash
# 应用密钥（必填）
SECRET_KEY=your-secret-key-here

# 调试模式（可选）
FLASK_DEBUG=false

# 日志级别（可选）
LOG_LEVEL=info
```

### 数据持久化
```bash
# 挂载配置文件目录
-v /host/path/configs:/app/configs

# 挂载日志目录
-v /host/path/logs:/app/logs
```

### Docker Compose示例
```yaml
version: '3.8'
services:
  vm-config-generator:
    build: .
    ports:
      - "34567:34567"
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    environment:
      - SECRET_KEY=your-secret-key-here
      - FLASK_DEBUG=false
    restart: unless-stopped
```

## 🛠️ 开发指南

### 本地开发环境
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/vm-config-generator.git
cd vm-config-generator

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python app.py

# 5. 访问应用
# http://localhost:34567
```

### 添加新配置选项
1. 在 `app.py` 中的 `PVE_CONFIG_SECTIONS` 添加新的配置项
2. 更新相应的解析器（`converters/` 目录）
3. 如果需要，更新前端模板

### 构建和发布
```bash
# 构建Docker镜像
docker build -t vm-config-generator:latest .

# 推送镜像到仓库
docker tag vm-config-generator:latest yourregistry/vm-config-generator:latest
docker push yourregistry/vm-config-generator:latest
```

## 📊 支持的磁盘格式

| 格式 | 描述 | 支持情况 |
|------|------|----------|
| RAW | 原始磁盘镜像 | ✅ 完全支持 |
| QCOW2 | QEMU写时复制格式 | ✅ 完全支持 |
| VMDK | VMware虚拟磁盘 | ✅ 完全支持 |
| VDI | VirtualBox磁盘镜像 | ✅ 完全支持 |
| QCOW | QEMU旧版格式 | ✅ 支持 |

## 🔒 安全性注意事项

1. **生产环境部署**
   - 修改默认的SECRET_KEY
   - 启用HTTPS访问
   - 配置防火墙规则
   - 定期备份配置文件

2. **脚本执行安全**
   - 一键脚本需要root权限，请仔细检查
   - 建议在测试环境验证后再在生产环境执行
   - 脚本会修改系统配置，请确保有备份

3. **网络访问安全**
   - 默认端口34567，建议修改为非标准端口
   - 配置适当的访问控制列表
   - 定期更新依赖包

## ❓ 常见问题

### Q1: 生成的脚本无法执行
**A**: 请确保：
1. 脚本有执行权限：`chmod +x script.sh`
2. 以root用户执行：`sudo ./script.sh`
3. 检查系统依赖是否满足（qemu-img, virsh等）

### Q2: 配置文件导入失败
**A**: 请检查：
1. 配置文件格式是否正确
2. 文件编码是否为UTF-8
3. 文件大小是否超过限制（16MB）

### Q3: 如何修改默认端口？
**A**: 在启动容器时指定：
```bash
docker run -d -p 8080:34567 vm-config-generator
```

### Q4: 如何备份配置数据？
**A**: 建议挂载持久化卷：
```bash
docker run -d -v ./data:/app/data vm-config-generator
```

### Q5: 支持哪些PVE版本？
**A**: 支持PVE 6.x、7.x 和 8.x 版本。

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档
- 编写单元测试

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- 提交Issue: [GitHub Issues](https://github.com/yourusername/vm-config-generator/issues)
- 文档更新: 欢迎提交PR改进文档
- 功能建议: 通过Issue提出新功能建议

## 🏆 致谢

感谢以下开源项目：
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - 前端框架
- [Docker](https://www.docker.com/) - 容器平台
- [QEMU](https://www.qemu.org/) - 虚拟机平台

---

**虚拟机配置生成器** - 简化您的虚拟机配置管理工作流！
