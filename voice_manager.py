import threading
import queue
import time
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("警告: pyttsx3 未安装，语音功能将不可用")

class VoiceManager:
    """语音管理器"""
    
    def __init__(self):
        self.engine = None
        self.voice_queue = queue.Queue()
        self.is_speaking = False
        self.worker_thread = None
        
        if PYTTSX3_AVAILABLE:
            self.init_engine()
            self.start_worker()
    
    def init_engine(self):
        """初始化语音引擎"""
        try:
            self.engine = pyttsx3.init()
            
            # 设置语音属性
            self.engine.setProperty('rate', 150)  # 语速
            self.engine.setProperty('volume', 0.9)  # 音量
            
            # 尝试设置中文语音
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            print("语音引擎初始化成功")
        except Exception as e:
            print(f"语音引擎初始化失败: {e}")
            self.engine = None
    
    def start_worker(self):
        """启动工作线程"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
    
    def _worker(self):
        """工作线程，处理语音队列"""
        while True:
            try:
                text = self.voice_queue.get(timeout=1)
                if text is None:  # 退出信号
                    break
                
                self._speak_now(text)
                self.voice_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"语音播放错误: {e}")
    
    def _speak_now(self, text):
        """立即播放语音"""
        if not self.engine:
            print(f"语音播放 (引擎不可用): {text}")
            return
        
        try:
            self.is_speaking = True
            print(f"语音播放: {text}")
            
            self.engine.say(text)
            self.engine.runAndWait()
            
        except Exception as e:
            print(f"语音播放失败: {e}")
        finally:
            self.is_speaking = False
    
    def speak(self, text):
        """添加文本到语音队列"""
        if not text or not text.strip():
            return
        
        if not PYTTSX3_AVAILABLE:
            print(f"语音播放 (功能不可用): {text}")
            return
        
        # 清空队列，只播放最新的语音
        while not self.voice_queue.empty():
            try:
                self.voice_queue.get_nowait()
            except queue.Empty:
                break
        
        self.voice_queue.put(text.strip())
        
        # 确保工作线程在运行
        self.start_worker()
    
    def is_busy(self):
        """检查是否正在播放语音"""
        return self.is_speaking or not self.voice_queue.empty()
    
    def stop(self):
        """停止语音播放"""
        # 清空队列
        while not self.voice_queue.empty():
            try:
                self.voice_queue.get_nowait()
            except queue.Empty:
                break
        
        # 停止引擎
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        
        # 发送退出信号给工作线程
        self.voice_queue.put(None)
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
        
        if self.engine:
            try:
                del self.engine
            except:
                pass
            self.engine = None

# 全局语音管理器实例
_voice_manager = None

def get_voice_manager():
    """获取全局语音管理器实例"""
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceManager()
    return _voice_manager

def speak(text):
    """便捷的语音播放函数"""
    manager = get_voice_manager()
    manager.speak(text)