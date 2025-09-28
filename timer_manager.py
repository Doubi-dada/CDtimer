import threading
import time
import keyboard
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from voice_manager import VoiceManager

class TimerManager(QObject):
    """计时器管理器"""
    timer_finished = pyqtSignal(str)  # 计时器完成信号
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.voice_manager = VoiceManager()
        self.active_timers = {}  # 活动的计时器 {task_id: timer_info}
        self.hotkey_bindings = {}  # 热键绑定 {hotkey: task_id}
        self.timer_finished.connect(self.on_timer_finished)
        
    def start_timer(self, task_id):
        """开始计时"""
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        task = config_manager.get_task_by_id(task_id)
        
        if not task:
            return False
        
        # 如果已经在运行，先停止
        if task_id in self.active_timers:
            self.stop_timer(task_id)
        
        # 创建计时器信息
        timer_info = {
            'task': task,
            'start_time': time.time(),
            'duration': task['duration'],
            'timer': QTimer()
        }
        
        # 设置计时器
        timer_info['timer'].timeout.connect(lambda: self.timer_finished.emit(task_id))
        timer_info['timer'].setSingleShot(True)
        timer_info['timer'].start(task['duration'] * 1000)  # 转换为毫秒
        
        self.active_timers[task_id] = timer_info
        
        # 显示开始提示
        self.show_start_notification(task)
        
        print(f"任务 [{task['name']}] 开始计时: {task['duration']} 秒")
        return True
    
    def stop_timer(self, task_id):
        """停止计时"""
        if task_id in self.active_timers:
            timer_info = self.active_timers[task_id]
            timer_info['timer'].stop()
            del self.active_timers[task_id]
            
            task = timer_info['task']
            print(f"任务 [{task['name']}] 计时已停止")
            
            # 显示停止提示
            if task['popup_reminder']:
                self.main_window.show_notification("计时停止", f"{task['name']} 计时已停止")
            
            if task['voice_reminder']:
                voice_text = task.get('custom_voice', f"{task['name']} 计时已停止")
                if not voice_text:
                    voice_text = f"{task['name']} 计时已停止"
                self.voice_manager.speak(voice_text)
            
            return True
        return False
    
    def is_timer_running(self, task_id):
        """检查计时器是否在运行"""
        return task_id in self.active_timers
    
    def get_remaining_time(self, task_id):
        """获取剩余时间（秒）"""
        if task_id not in self.active_timers:
            return 0
        
        timer_info = self.active_timers[task_id]
        elapsed = time.time() - timer_info['start_time']
        remaining = max(0, timer_info['duration'] - elapsed)
        return int(remaining)
    
    def on_timer_finished(self, task_id):
        """计时器完成处理"""
        if task_id in self.active_timers:
            timer_info = self.active_timers[task_id]
            task = timer_info['task']
            
            # 清理计时器
            del self.active_timers[task_id]
            
            # 显示完成提示
            self.show_finish_notification(task)
            
            print(f"任务 [{task['name']}] 倒计时完成！")
    
    def show_start_notification(self, task):
        """显示开始计时通知"""
        if task['popup_reminder']:
            self.main_window.show_notification("开始计时", f"{task['name']} 开始计时")
        
        if task['voice_reminder']:
            voice_text = task.get('custom_voice', f"{task['name']} 开始计时")
            if not voice_text:
                voice_text = f"{task['name']} 开始计时"
            self.voice_manager.speak(voice_text)
    
    def show_finish_notification(self, task):
        """显示完成通知"""
        if task['popup_reminder']:
            self.main_window.show_notification("时间到了", f"{task['name']} 时间到了！")
        
        if task['voice_reminder']:
            voice_text = task.get('custom_voice', f"{task['name']} 时间到了")
            if not voice_text:
                voice_text = f"{task['name']} 时间到了"
            self.voice_manager.speak(voice_text)
    
    def update_hotkeys(self):
        """更新热键绑定"""
        # 清除所有现有热键
        try:
            keyboard.unhook_all()
        except:
            pass
        
        self.hotkey_bindings.clear()
        
        # 重新绑定热键
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        tasks = config_manager.get_tasks()
        
        for task in tasks:
            if task['hotkey_enabled'] and task['hotkey']:
                try:
                    hotkey = task['hotkey'].lower()
                    self.hotkey_bindings[hotkey] = task['id']
                    keyboard.add_hotkey(hotkey, self.on_hotkey_pressed, args=[task['id']])
                    print(f"绑定热键: {hotkey} -> {task['name']}")
                except Exception as e:
                    print(f"热键绑定失败 {task['hotkey']}: {e}")
    
    def on_hotkey_pressed(self, task_id):
        """热键按下处理"""
        if self.is_timer_running(task_id):
            # 如果正在运行，则停止
            self.stop_timer(task_id)
        else:
            # 如果没有运行，则开始
            self.start_timer(task_id)
    
    def cleanup(self):
        """清理资源"""
        # 停止所有计时器
        for task_id in list(self.active_timers.keys()):
            self.stop_timer(task_id)
        
        # 清除热键绑定
        try:
            keyboard.unhook_all()
        except:
            pass