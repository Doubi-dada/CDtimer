import json
import os
import uuid
from typing import List, Dict, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="tasks_config.json"):
        self.config_file = config_file
        self.tasks = []
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    
                    # 确保每个任务都有ID
                    for task in self.tasks:
                        if 'id' not in task:
                            task['id'] = str(uuid.uuid4())
                    
                    print(f"加载了 {len(self.tasks)} 个任务")
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.tasks = []
        else:
            # 创建默认配置
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置"""
        default_tasks = [
            {
                'id': str(uuid.uuid4()),
                'name': '示例技能1',
                'duration': 60,
                'hotkey_enabled': True,
                'hotkey': 'F1',
                'popup_reminder': True,
                'voice_reminder': True,
                'custom_voice': ''
            },
            {
                'id': str(uuid.uuid4()),
                'name': '示例技能2',
                'duration': 30,
                'hotkey_enabled': True,
                'hotkey': 'F2',
                'popup_reminder': True,
                'voice_reminder': True,
                'custom_voice': ''
            }
        ]
        
        self.tasks = default_tasks
        self.save_config()
        print("创建了默认配置")
    
    def save_config(self):
        """保存配置文件"""
        try:
            config_data = {
                'tasks': self.tasks,
                'version': '2.0'
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print("配置已保存")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return self.tasks.copy()
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """根据ID获取任务"""
        for task in self.tasks:
            if task['id'] == task_id:
                return task.copy()
        return None
    
    def add_task(self, task_data: Dict):
        """添加任务"""
        # 生成新的ID
        task_data['id'] = str(uuid.uuid4())
        
        # 设置默认值
        default_task = {
            'name': '',
            'duration': 60,
            'hotkey_enabled': True,
            'hotkey': '',
            'popup_reminder': True,
            'voice_reminder': True,
            'custom_voice': ''
        }
        
        # 合并数据
        new_task = {**default_task, **task_data}
        
        self.tasks.append(new_task)
        self.save_config()
        
        print(f"添加任务: {new_task['name']}")
        return new_task['id']
    
    def update_task(self, task_data: Dict):
        """更新任务"""
        task_id = task_data.get('id')
        if not task_id:
            return False
        
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                # 保留ID，更新其他数据
                updated_task = {**task, **task_data}
                updated_task['id'] = task_id
                self.tasks[i] = updated_task
                self.save_config()
                
                print(f"更新任务: {updated_task['name']}")
                return True
        
        return False
    
    def delete_task(self, task_id: str):
        """删除任务"""
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                deleted_task = self.tasks.pop(i)
                self.save_config()
                
                print(f"删除任务: {deleted_task['name']}")
                return True
        
        return False
    
    def get_task_by_hotkey(self, hotkey: str) -> Optional[Dict]:
        """根据热键获取任务"""
        for task in self.tasks:
            if (task.get('hotkey_enabled', False) and 
                task.get('hotkey', '').lower() == hotkey.lower()):
                return task.copy()
        return None
    
    def validate_task(self, task_data: Dict) -> List[str]:
        """验证任务数据"""
        errors = []
        
        # 检查必填字段
        if not task_data.get('name', '').strip():
            errors.append("任务名称不能为空")
        
        # 检查倒计时时间
        duration = task_data.get('duration', 0)
        if not isinstance(duration, int) or duration <= 0:
            errors.append("倒计时必须是正整数")
        
        # 检查热键冲突
        if task_data.get('hotkey_enabled', False):
            hotkey = task_data.get('hotkey', '').strip()
            if hotkey:
                current_id = task_data.get('id')
                for task in self.tasks:
                    if (task['id'] != current_id and 
                        task.get('hotkey_enabled', False) and
                        task.get('hotkey', '').lower() == hotkey.lower()):
                        errors.append(f"热键 '{hotkey}' 已被任务 '{task['name']}' 使用")
                        break
        
        return errors