import gradio as gr
import os
import socket
import subprocess
import platform
import sys
import psutil


def find_available_port(start_port=7860, max_attempts=20):
    """查找可用端口，从指定端口开始尝试"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    return start_port


def get_python_info():
    """获取Python环境信息"""
    info = {}
    
    info["Python版本"] = platform.python_version()
    info["Python路径"] = sys.executable
    info["Python架构"] = platform.architecture()[0]
    
    packages = ["vllm", "sglang", "torch", "transformers", "gradio", "psutil"]
    for pkg in packages:
        try:
            __import__(pkg)
            import importlib.metadata
            try:
                version = importlib.metadata.version(pkg)
                info[f"{pkg}版本"] = version
            except importlib.metadata.PackageNotFoundError:
                info[f"{pkg}版本"] = "已安装但无法获取版本"
        except ImportError:
            info[f"{pkg}版本"] = "未安装"
    
    return info


def get_cpu_info():
    """获取CPU信息"""
    info = {}
    
    info["CPU型号"] = platform.processor()
    info["CPU核心数"] = f"物理核心: {psutil.cpu_count(logical=False)}, 逻辑核心: {psutil.cpu_count(logical=True)}"
    info["CPU频率"] = f"{psutil.cpu_freq().current:.1f} MHz (最大: {psutil.cpu_freq().max:.1f} MHz)"
    info["CPU使用率"] = f"{psutil.cpu_percent(interval=0.5)}%"
    
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ["lscpu"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Model name' in line or 'model name' in line:
                        info["CPU详细型号"] = line.split(':')[1].strip()
                    elif 'Architecture' in line:
                        info["CPU架构"] = line.split(':')[1].strip()
                    elif 'CPU(s)' in line and 'Core' not in line:
                        info["CPU总数"] = line.split(':')[1].strip()
    except Exception:
        pass
    
    return info


def get_memory_info():
    """获取内存信息"""
    info = {}
    
    mem = psutil.virtual_memory()
    info["总内存"] = f"{mem.total / (1024**3):.2f} GB"
    info["可用内存"] = f"{mem.available / (1024**3):.2f} GB"
    info["已用内存"] = f"{mem.used / (1024**3):.2f} GB"
    info["内存使用率"] = f"{mem.percent}%"
    
    swap = psutil.swap_memory()
    info["交换分区"] = f"总计: {swap.total / (1024**3):.2f} GB, 已用: {swap.used / (1024**3):.2f} GB"
    
    return info


def get_gpu_info():
    """获取GPU信息"""
    info = {}
    
    try:
        result = subprocess.run(
            ["amd-smi"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            output = result.stdout
            info["AMD GPU信息"] = output[:1000]
        else:
            info["AMD GPU信息"] = f"amd-smi执行失败: {result.stderr[:200]}"
    except Exception as e:
        info["AMD GPU信息"] = f"amd-smi未找到或执行失败: {str(e)}"
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            info["NVIDIA GPU信息"] = result.stdout.strip()
        else:
            info["NVIDIA GPU信息"] = f"nvidia-smi执行失败: {result.stderr[:200]}"
    except Exception as e:
        info["NVIDIA GPU信息"] = f"nvidia-smi未找到或执行失败: {str(e)}"
    
    try:
        import torch
        if torch.cuda.is_available():
            info["PyTorch GPU"] = f"可用, 设备数: {torch.cuda.device_count()}"
            for i in range(torch.cuda.device_count()):
                info[f"GPU {i}"] = torch.cuda.get_device_name(i)
        else:
            info["PyTorch GPU"] = "不可用"
    except ImportError:
        info["PyTorch GPU"] = "PyTorch未安装"
    except Exception as e:
        info["PyTorch GPU"] = f"检测失败: {str(e)}"
    
    try:
        result = subprocess.run(
            ["rocminfo"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            output = result.stdout
            gpu_lines = []
            for line in output.split('\n')[:30]:
                if 'Name' in line or 'Brand' in line or 'gfx' in line.lower():
                    gpu_lines.append(line.strip())
            info["ROCm GPU详情"] = '\n'.join(gpu_lines) if gpu_lines else output[:500]
        else:
            info["ROCm GPU详情"] = f"rocminfo执行失败: {result.stderr[:200]}"
    except Exception as e:
        info["ROCm GPU详情"] = f"rocminfo未找到或执行失败: {str(e)}"
    
    return info


def get_system_info():
    """获取系统信息"""
    info = {}
    
    info["系统平台"] = platform.platform()
    info["操作系统"] = platform.system()
    info["操作系统版本"] = platform.version()
    info["主机名"] = platform.node()
    info["内核版本"] = platform.release()
    
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ["cat", "/etc/os-release"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'PRETTY_NAME' in line:
                        info["发行版"] = line.split('=')[1].strip().strip('"')
                    elif 'VERSION_ID' in line:
                        info["发行版版本"] = line.split('=')[1].strip().strip('"')
    except Exception:
        pass
    
    return info


def rocm_probe():
    """探测ROCm环境信息"""
    results = {}
    
    results.update(get_system_info())
    results.update(get_cpu_info())
    results.update(get_memory_info())
    results.update(get_gpu_info())
    results.update(get_python_info())
    
    return "\n".join([f"{k}: {v}" for k, v in results.items()])


with gr.Blocks(title="ROCmDockerProbe") as demo:
    gr.Markdown("# ROCmDockerProbe")
    gr.Markdown("## 探测ROCm环境")
    
    output = gr.Textbox(label="探测结果", lines=30, max_lines=50)
    
    gr.Button("开始探测").click(
        fn=rocm_probe,
        outputs=output
    )


if __name__ == "__main__":
    default_port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    available_port = find_available_port(default_port)
    if available_port != default_port:
        print(f"端口 {default_port} 已被占用，使用可用端口 {available_port}")
    demo.launch(server_port=available_port, server_name="0.0.0.0")
