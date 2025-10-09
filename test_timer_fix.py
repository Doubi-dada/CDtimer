#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计时器修复测试脚本
用于验证计时器bug修复效果
"""

import sys
import time
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from timer_manager import TimerManager
from config_manager import ConfigManager

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.timer_manager = TimerManager(self)
        self.init_ui()
        self.setup_test_tasks()
        
    def init_ui(self):
        self.setWindowTitle("计时器修复测试")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # 状态显示
        self.status_label = QLabel("测试状态: 准备就绪")
        layout.addWidget(self.status_label)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # 测试按钮
        self.test1_btn = QPushButton("测试1: 短时间计时器 (5秒)")
        self.test1_btn.clicked.connect(self.test_short_timer)
        layout.addWidget(self.test1_btn)
        
        self.test2_btn = QPushButton("测试2: 多个计时器同时运行")
        self.test2_btn.clicked.connect(self.test_multiple_timers)
        layout.addWidget(self.test2_btn)
        
        self.test3_btn = QPushButton("测试3: 快速启停测试")
        self.test3_btn.clicked.connect(self.test_rapid_start_stop)
        layout.addWidget(self.test3_btn)
        
        self.stop_all_btn = QPushButton("停止所有计时器")
        self.stop_all_btn.clicked.connect(self.stop_all_timers)
        layout.addWidget(self.stop_all_btn)
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(self.clear_log_btn)
        
        self.setLayout(layout)
        
        # 状态更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)
        
    def setup_test_tasks(self):
        """设置测试任务"""
        # 清空现有任务
        self.config_manager.clear_all_tasks()
        
        # 添加测试任务
        test_tasks = [
            {
                'name': '测试任务1',
                'duration': 5,
                'hotkey_enabled': False,
                'hotkey': '',
                'popup_reminder': True,
                'voice_reminder': True,
                'custom_voice': '测试任务1完成'
            },
            {
                'name': '测试任务2',
                'duration': 8,
                'hotkey_enabled': False,
                'hotkey': '',
                'popup_reminder': True,
                'voice_reminder': True,
                'custom_voice': '测试任务2完成'
            },
            {
                'name': '测试任务3',
                'duration': 3,
                'hotkey_enabled': False,
                'hotkey': '',
                'popup_reminder': True,
                'voice_reminder': True,
                'custom_voice': '测试任务3完成'
            }
        ]
        
        self.test_task_ids = []
        for task_data in test_tasks:
            task_id = self.config_manager.add_task(task_data)
            self.test_task_ids.append(task_id)
            
        self.log(f"创建了 {len(self.test_task_ids)} 个测试任务")
        
    def test_short_timer(self):
        """测试短时间计时器"""
        self.log("开始测试: 短时间计时器 (5秒)")
        if self.test_task_ids:
            task_id = self.test_task_ids[0]
            success = self.timer_manager.start_timer(task_id)
            self.log(f"启动计时器结果: {success}")
            
    def test_multiple_timers(self):
        """测试多个计时器同时运行"""
        self.log("开始测试: 多个计时器同时运行")
        for i, task_id in enumerate(self.test_task_ids):
            success = self.timer_manager.start_timer(task_id)
            self.log(f"启动计时器 {i+1} 结果: {success}")
            time.sleep(0.1)  # 稍微延迟避免冲突
            
    def test_rapid_start_stop(self):
        """测试快速启停"""
        self.log("开始测试: 快速启停测试")
        if self.test_task_ids:
            task_id = self.test_task_ids[0]
            
            # 快速启动和停止
            for i in range(3):
                self.log(f"第 {i+1} 轮快速启停")
                self.timer_manager.start_timer(task_id)
                time.sleep(0.5)
                self.timer_manager.stop_timer(task_id)
                time.sleep(0.5)
                
    def stop_all_timers(self):
        """停止所有计时器"""
        self.log("停止所有计时器")
        for task_id in self.test_task_ids:
            if self.timer_manager.is_timer_running(task_id):
                self.timer_manager.stop_timer(task_id)
                
    def update_status(self):
        """更新状态显示"""
        running_count = 0
        status_info = []
        
        tasks = self.config_manager.get_tasks()
        for task in tasks:
            if self.timer_manager.is_timer_running(task['id']):
                running_count += 1
                remaining = self.timer_manager.get_remaining_time(task['id'])
                status_info.append(f"{task['name']}: {remaining}秒")
                
        if running_count > 0:
            status_text = f"运行中的计时器: {running_count}个\n" + "\n".join(status_info)
        else:
            status_text = "没有运行中的计时器"
            
        self.status_label.setText(status_text)
        
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.log_text.append(log_message)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        
    def show_notification(self, title, message):
        """显示通知 (供timer_manager调用)"""
        self.log(f"通知: {title} - {message}")
        
    def closeEvent(self, event):
        """关闭事件"""
        self.timer_manager.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())