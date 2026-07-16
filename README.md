# ROCmDockerProbe

探测ROCm环境的Gradio应用

## 功能特性

- 检测系统平台信息
- 获取Python版本
- 探测ROCm环境信息（通过rocminfo）
- 探测NVIDIA GPU信息（通过nvidia-smi）
- 自动端口检测，避免端口冲突

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
python app.py
```

默认端口为7860，访问 http://localhost:7860

## 端口配置

可以通过环境变量自定义端口：

```bash
set GRADIO_SERVER_PORT=8080
python app.py
```

## 技术栈

- Python 3.x
- Gradio 4.x
