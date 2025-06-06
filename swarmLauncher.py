import random
import string
import subprocess
import sys
import os
import threading
from typing import List

def generate_random_string(length: int) -> str:
    """生成指定长度的随机字符串"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def log_output(process: subprocess.Popen, worker_name: str):
    """实时显示进程的输出"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"[{worker_name}] {output.strip()}")
    
    # 检查是否有错误输出
    error = process.stderr.readline()
    if error:
        print(f"[{worker_name}] ERROR: {error.strip()}")

def start_celery_worker(worker_name: str) -> subprocess.Popen:
    """启动一个 Celery worker 进程"""
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP'] = 'true'
        
        # 构建 Celery worker 命令
        cmd = [
            "celery",
            "-A", "celery_worker",
            "worker",
            "--loglevel=INFO",
            f"--hostname={worker_name}",
            "--pool=solo",  # Windows 上推荐使用 solo 池
            "-Q", "transcription"  # 指定队列
        ]
        
        # 启动进程，不捕获输出
        process = subprocess.Popen(
            cmd,
            stdout=None,  # 直接输出到控制台
            stderr=None,  # 直接输出到控制台
            text=True,
            bufsize=1,  # 行缓冲
            universal_newlines=True,
            env=env  # 使用修改后的环境变量
        )
        
        print(f"✅ Worker {worker_name} 已启动 (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ 启动 worker {worker_name} 失败: {str(e)}")
        return None

def main():
    # 工作进程列表
    workers: List[subprocess.Popen] = []
    
    try:
        # 启动多个 worker
        for _ in range(1):  # 启动 3 个 worker
            worker_name = f"agent-{generate_random_string(8)}"
            process = start_celery_worker(worker_name)
            if process:
                workers.append(process)
        
        print(f"\n总共启动了 {len(workers)} 个 worker")
        print("按 Ctrl+C 停止所有 worker")
        
        # 等待所有进程
        for worker in workers:
            worker.wait()
            
    except KeyboardInterrupt:
        print("\n正在停止所有 worker...")
        for worker in workers:
            if worker and worker.poll() is None:
                worker.terminate()
        print("所有 worker 已停止")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        # 确保清理所有进程
        for worker in workers:
            if worker and worker.poll() is None:
                worker.terminate()

if __name__ == "__main__":
    main()
