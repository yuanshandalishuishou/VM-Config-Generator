# 创建项目目录
mkdir -p vm-config-generator/{templates,config_templates,converters}
cd vm-config-generator

# 创建上述所有文件
# app.py, templates/index.html, templates/editor.html, templates/import.html
# requirements.txt, Dockerfile, converters/pve_parser.py, converters/xml_parser.py

# 构建Docker镜像
docker build -t vm-config-generator .

# 查看镜像大小
docker images vm-config-generator


# 运行容器
docker run -d \
  --name vm-config-generator \
  -p 34567:34567 \
  -v $(pwd)/configs:/app/configs \
  -e SECRET_KEY=your-secret-key-here \
  vm-config-generator

# 查看日志
docker logs -f vm-config-generator


#访问应用打开浏览器访问：http://localhost:34567

#功能特点
完整的配置编辑：

按类别组织的配置选项（基本、启动、磁盘、网络、显示、高级）

支持所有常见的虚拟机配置参数

详细的默认值和帮助文本

灵活的导入功能：

支持从PVE .conf文件导入

支持从Libvirt .xml文件导入

智能解析配置参数

多种导出格式：

生成PVE .conf配置文件

生成Libvirt .xml配置文件

生成一键部署Bash脚本

实时预览：

实时预览生成的配置文件

支持两种格式的预览

一键脚本功能：

自动创建虚拟机和配置文件

包含错误处理和详细日志

支持磁盘创建和网络配置

用户友好的界面：

响应式设计，支持移动设备

直观的标签页和折叠面板

自动保存功能

这个虚拟机配置生成器提供了一个完整的解决方案，让用户可以从零开始创建虚拟机配置，也可以从现有配置导入修改，最后生成可以直接使用的配置文件或部署脚本