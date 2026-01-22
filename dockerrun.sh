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
