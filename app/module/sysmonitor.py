#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: mark.hsieh
# System Monitor with Docker Network API Client

import requests
import psutil
import os
from typing import Optional, Dict, Any
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime


class DockerNetworkClient:
    """Docker 网络中的服务访问客户端"""
    
    def __init__(self, container_name: str, port: int, timeout: int = 5):
        """
        初始化容器服务客户端
        
        Args:
            container_name: Docker 容器名称（同一网络内可直接访问）
            port: 容器服务端口
            timeout: 请求超时时间（秒）
        """
        self.container_name = container_name
        self.port = port
        self.base_url = f"http://{container_name}:{port}"
        self.timeout = timeout
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的 Session"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        发送 GET 请求
        
        Args:
            endpoint: API 端点（如 "/api/data"）
            params: 查询参数
            
        Returns:
            JSON 响应或 None（失败时）
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ GET {self.container_name}:{self.port}{endpoint} 失败: {e}")
            return None
    
    def post(self, endpoint: str, json: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """发送 POST 请求"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.post(url, json=json, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ POST {self.container_name}:{self.port}{endpoint} 失败: {e}")
            return None
    
    def health_check(self, endpoint: str = "/health") -> bool:
        """
        检查服务健康状态
        
        Args:
            endpoint: 健康检查端点
            
        Returns:
            True 表示健康，False 表示不健康
        """
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_service(self, max_retries: int = 30, delay: int = 1) -> bool:
        """
        等待服务启动（用于容器启动初期）
        
        Args:
            max_retries: 最大重试次数
            delay: 重试间隔（秒）
            
        Returns:
            True 表示服务已启动，False 表示超时
        """
        for attempt in range(max_retries):
            if self.health_check():
                print(f"✓ {self.container_name} 服务已启动（第 {attempt + 1} 次尝试）")
                return True
            
            print(f"⏳ 等待 {self.container_name} 启动... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
        
        print(f"❌ {self.container_name} 服务启动失败（超过 {max_retries} 次尝试）")
        return False
    
    def fetch_data(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """获取数据"""
        return self.get(endpoint)
    
    def push_data(self, endpoint: str, data: Dict) -> Optional[Dict[str, Any]]:
        """推送数据"""
        return self.post(endpoint, json=data)


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        """初始化系统监控"""
        self.start_time = datetime.now()
    
    def get_cpu_usage(self) -> float:
        """获取 CPU 使用率（%）"""
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        memory = psutil.virtual_memory()
        return {
            "total_mb": round(memory.total / (1024 ** 2), 2),
            "used_mb": round(memory.used / (1024 ** 2), 2),
            "available_mb": round(memory.available / (1024 ** 2), 2),
            "percent": memory.percent
        }
    
    def get_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """获取磁盘使用情况"""
        disk = psutil.disk_usage(path)
        return {
            "total_gb": round(disk.total / (1024 ** 3), 2),
            "used_gb": round(disk.used / (1024 ** 3), 2),
            "free_gb": round(disk.free / (1024 ** 3), 2),
            "percent": disk.percent
        }
    
    def get_process_count(self) -> int:
        """获取进程数"""
        return len(psutil.pids())
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统完整信息"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int((datetime.now() - self.start_time).total_seconds()),
            "cpu_percent": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "process_count": self.get_process_count(),
            "platform": {
                "system": psutil.os.uname().sysname,
                "release": psutil.os.uname().release,
                "machine": psutil.os.uname().machine
            }
        }
    
    def is_healthy(self, cpu_threshold: float = 90.0, memory_threshold: float = 90.0) -> bool:
        """
        检查系统是否健康
        
        Args:
            cpu_threshold: CPU 使用率阈值（%）
            memory_threshold: 内存使用率阈值（%）
            
        Returns:
            True 表示系统健康，False 表示存在问题
        """
        cpu = self.get_cpu_usage()
        memory = self.get_memory_usage()
        
        if cpu > cpu_threshold:
            print(f"⚠️  CPU 使用率过高: {cpu}%")
            return False
        
        if memory["percent"] > memory_threshold:
            print(f"⚠️  内存使用率过高: {memory['percent']}%")
            return False
        
        return True


class DockerServiceMonitor:
    """Docker 容器服务监控器"""
    
    def __init__(self):
        """初始化服务监控"""
        self.services: Dict[str, DockerNetworkClient] = {}
        self.system_monitor = SystemMonitor()
    
    def register_service(self, service_name: str, container_name: str, port: int) -> None:
        """
        注册一个 Docker 服务
        
        Args:
            service_name: 服务别名
            container_name: Docker 容器名称
            port: 容器端口
        """
        self.services[service_name] = DockerNetworkClient(container_name, port)
        print(f"✓ 已注册服务: {service_name} ({container_name}:{port})")
    
    def check_service_health(self, service_name: str) -> bool:
        """检查单个服务是否健康"""
        if service_name not in self.services:
            print(f"❌ 服务不存在: {service_name}")
            return False
        
        return self.services[service_name].health_check()
    
    def check_all_services(self) -> Dict[str, bool]:
        """检查所有已注册服务的健康状态"""
        results = {}
        for service_name, client in self.services.items():
            is_healthy = client.health_check()
            results[service_name] = is_healthy
            status = "✓ 正常" if is_healthy else "❌ 离线"
            print(f"  {service_name}: {status}")
        
        return results
    
    def get_service_data(self, service_name: str, endpoint: str) -> Optional[Dict]:
        """获取服务数据"""
        if service_name not in self.services:
            print(f"❌ 服务不存在: {service_name}")
            return None
        
        return self.services[service_name].fetch_data(endpoint)
    
    def push_service_data(self, service_name: str, endpoint: str, data: Dict) -> Optional[Dict]:
        """推送数据到服务"""
        if service_name not in self.services:
            print(f"❌ 服务不存在: {service_name}")
            return None
        
        return self.services[service_name].push_data(endpoint, data)
    
    def get_full_status(self) -> Dict[str, Any]:
        """获取完整系统状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_monitor.get_system_info(),
            "services": self.check_all_services(),
            "system_healthy": self.system_monitor.is_healthy()
        }


# ──────────────────────────────────────
# 使用示例
# ──────────────────────────────────────
if __name__ == "__main__":
    # 初始化监控器
    monitor = DockerServiceMonitor()
    
    # 注册服务（容器名称来自 docker-compose）
    monitor.register_service("linebot_api", "linebot-webhook", 168)
    monitor.register_service("redis_server", "redis", 6379)
    
    # 检查所有服务健康状态
    print("\n📋 检查服务状态:")
    monitor.check_all_services()
    
    # 获取系统信息
    print("\n💾 系统信息:")
    system_info = monitor.system_monitor.get_system_info()
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    
    # 获取完整状态
    print("\n🔍 完整系统状态:")
    full_status = monitor.get_full_status()
    print(full_status)
