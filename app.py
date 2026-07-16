import gradio as gr
import os
import socket


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


def rocm_probe():
    """探测ROCm环境信息"""
    import subprocess
    import platform
    
    info = {
        "系统平台": platform.platform(),
        "Python版本": platform.python_version(),
    }
    
    try:
        result = subprocess.run(
            ["rocminfo"], capture_output=True, text=True, timeout=30
        )
        info["ROCm信息"] = result.stdout[:500] if result.stdout else result.stderr[:500]
    except Exception as e:
        info["ROCm信息"] = f"rocminfo未找到或执行失败: {str(e)}"
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            info["NVIDIA信息"] = result.stdout.strip()
    except Exception:
        info["NVIDIA信息"] = "nvidia-smi未找到"
    
    return "\n".join([f"{k}: {v}" for k, v in info.items()])


with gr.Blocks(title="ROCmDockerProbe") as demo:
    gr.Markdown("# ROCmDockerProbe")
    gr.Markdown("## 探测ROCm环境")
    
    output = gr.Textbox(label="探测结果", lines=15)
    
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
