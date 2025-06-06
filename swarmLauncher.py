import random
import string
import subprocess
import sys
import os
import threading
import logging
from typing import List

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        env['CELERY_LOG_LEVEL'] = 'INFO'  # 改为 INFO 级别
        
        # 构建 Celery worker 命令
        cmd = [
            "celery",
            "-A", "celery_worker",
            "worker",
            "--loglevel=INFO",  # 改为 INFO 级别
            f"--hostname={worker_name}",
            "--pool=solo",
            # 监听所有队列
            "-Q", "dispatcher,transcription,nextbestaction,cache,summary",
            "--events",  # 启用事件监控
            "--concurrency=1",  # 限制并发数
            "--without-gossip",  # 禁用 gossip
            "--without-mingle",  # 禁用 mingle
            "--without-heartbeat"  # 禁用心跳
        ]
        
        logger.info(f"Starting worker {worker_name} with command: {' '.join(cmd)}")
        
        # 启动进程，不捕获输出
        process = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        logger.info(f"✅ Worker {worker_name} 已启动 (PID: {process.pid})")
        return process
        
    except Exception as e:
        logger.error(f"❌ 启动 worker {worker_name} 失败: {str(e)}")
        return None

def main():
    # 工作进程列表
    workers: List[subprocess.Popen] = []
    
    try:
        # 启动 worker
        worker_name = f"agent-{generate_random_string(8)}"
        process = start_celery_worker(worker_name)
        if process:
            workers.append(process)
        
        logger.info(f"\nWorker 已启动")
        logger.info("按 Ctrl+C 停止所有 worker")
        
        # 等待所有进程
        for worker in workers:
            worker.wait()
            
    except KeyboardInterrupt:
        logger.info("\n正在停止所有 worker...")
        for worker in workers:
            if worker and worker.poll() is None:
                worker.terminate()
        logger.info("所有 worker 已停止")
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        # 确保清理所有进程
        for worker in workers:
            if worker and worker.poll() is None:
                worker.terminate()

if __name__ == "__main__":
    main()
