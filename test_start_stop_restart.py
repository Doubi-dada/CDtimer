#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试启动-暂停-重新启动场景的测试脚本
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer
from timer_manager import TimerManager
from config_manager import ConfigManager

class StartStopRestartTest(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.timer_manager = TimerManager(self)
        self.test_task_id = None
        self.init_ui()
        self.setup_test_task()
        
    def init_ui(self):
        self.setWindowTitle("启动-暂停-重新启动测试")
        self.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        # 状态显示
        self.status_label = QLabel("测试状态: 准备就绪")
        layout.addWidget(self.status_label)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(300)
        layout.addWidget(self.log_text)
        
        # 测试按钮
        self.start_btn = QPushButton("1. 启动计时器 (10秒)")
        self.start_btn.clicked.connect(self.start_timer)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("2. 暂停计时器")
        self.stop_btn.clicked.connect(self.stop_timer)
        layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton("3. 重新启动计时器")
        self.restart_btn.clicked.connect(self.restart_timer)
        layout.addWidget(self.restart_btn)
        
        self.auto_test_btn = QPushButton("自动测试: 启动→暂停→重启")
        self.auto_test_btn.clicked.connect(self.auto_test)
        layout.addWidget(self.auto_test_btn)
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(self.clear_log_btn)
        
        self.setLayout(layout)
        
        # 状态更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(500)
        
    def setup_test_task(self):
        """设置测试任务"""
        # 清空现有任务
        self.config_manager.clear_all_tasks()
        
        # 添加测试任务
        test_task = {
            'name': '启停测试任务',
            'duration': 10,  # 10秒，便于测试
            'hotkey_enabled': False,
            'hotkey': '',
            'popup_reminder': True,
            'voice_reminder': True,
            'custom_voice': '启停测试任务完成了！'
        }
        
        self.test_task_id = self.config_manager.add_task(test_task)
        self.log(f"创建测试任务，ID: {self.test_task_id}")
        
    def start_timer(self):
        """启动计时器"""
        self.log("=== 手动启动计时器 ===")
        if self.test_task_id:
            success = self.timer_manager.start_timer(self.test_task_id)
            self.log(f"启动结果: {success}")
            if success:
                self.log("✅ 计时器已启动，等待10秒后应该会有提醒")
            else:
                self.log("❌ 计时器启动失败")
                
    def stop_timer(self):
        """暂停计时器"""
        self.log("=== 手动暂停计时器 ===")
        if self.test_task_id:
            success = self.timer_manager.stop_timer(self.test_task_id)
            self.log(f"暂停结果: {success}")
            if success:
                self.log("✅ 计时器已暂停")
            else:
                self.log("❌ 计时器暂停失败")
                
    def restart_timer(self):
        """重新启动计时器"""
        self.log("=== 手动重新启动计时器 ===")
        if self.test_task_id:
            success = self.timer_manager.start_timer(self.test_task_id)
            self.log(f"重启结果: {success}")
            if success:
                self.log("✅ 计时器已重新启动，等待10秒后应该会有提醒")
                self.log("🔍 这是关键测试：重启后是否能正常提醒？")
            else:
                self.log("❌ 计时器重启失败")
                
    def auto_test(self):
        """自动测试启动→暂停→重启流程"""
        self.log("🤖 === 开始自动测试 ===")
        
        # 第一步：启动
        self.log("步骤1: 启动计时器")
        self.timer_manager.start_timer(self.test_task_id)
        
        # 使用QTimer来安排后续步骤
        QTimer.singleShot(3000, self.auto_test_step2)  # 3秒后暂停
        
    def auto_test_step2(self):
        """自动测试第二步：暂停"""
        self.log("步骤2: 暂停计时器 (运行了3秒)")
        self.timer_manager.stop_timer(self.test_task_id)
        
        # 2秒后重启
        QTimer.singleShot(2000, self.auto_test_step3)
        
    def auto_test_step3(self):
        """自动测试第三步：重启"""
        self.log("步骤3: 重新启动计时器")
        success = self.timer_manager.start_timer(self.test_task_id)
        if success:
            self.log("🔍 关键测试：重启成功，现在等待10秒看是否会提醒")
            self.log("⏰ 如果10秒后没有提醒，说明bug仍然存在")
        else:
            self.log("❌ 重启失败")
        
    def update_status(self):
        """更新状态显示"""
        if self.test_task_id:
            is_running = self.timer_manager.is_timer_running(self.test_task_id)
            remaining = self.timer_manager.get_remaining_time(self.test_task_id)
            
            if is_running:
                status_text = f"🟢 计时器运行中\n剩余时间: {remaining}秒"
            else:
                status_text = "⚫ 计时器已停止"
                
            self.status_label.setText(status_text)
        
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.log_text.append(log_message)
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        
    def show_notification(self, title, message):
        """显示通知 (供timer_manager调用)"""
        self.log(f"🔔 通知: {title} - {message}")
        
        # 如果是完成通知，特别标记
        if "时间到了" in title or "时间到了" in message:
            self.log("🎉 === 计时器完成通知收到！测试成功！ ===")
        
    def closeEvent(self, event):
        """关闭事件"""
        self.timer_manager.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = StartStopRestartTest()
    window.show()
    
    print("=== 启动-暂停-重新启动测试程序 ===")
    print("使用说明：")
    print("1. 点击'启动计时器'开始10秒倒计时")
    print("2. 在倒计时过程中点击'暂停计时器'")
    print("3. 点击'重新启动计时器'，观察是否能正常提醒")
    print("4. 或者直接点击'自动测试'按钮")
    print("=====================================")
    
    sys.exit(app.exec_())