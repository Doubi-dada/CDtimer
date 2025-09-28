import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QMessageBox, QSystemTrayIcon,
    QMenu, QAction, QHeaderView, QFrame, QGroupBox, QGridLayout,
    QAbstractItemView, QStyledItemDelegate
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QKeySequence
from timer_manager import TimerManager
from config_manager import ConfigManager


class ModernButton(QPushButton):
    """现代化按钮样式"""

    def __init__(self, text, color="#4CAF50"):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
        """)

    def darken_color(self, color, factor=0.9):
        """使颜色变暗"""
        if color.startswith('#'):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        return color


class HotkeyEdit(QLineEdit):
    """热键编辑控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("点击后按下热键，Delete删除")
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.clear()
            return

        # 获取按键组合
        key_sequence = QKeySequence(event.key() | int(event.modifiers()))
        hotkey_text = key_sequence.toString()

        if hotkey_text and hotkey_text != "":
            self.setText(hotkey_text)

        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)


class TaskEditDialog(QWidget):
    """任务编辑对话框"""
    task_saved = pyqtSignal(dict)

    def __init__(self, task_data=None, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.init_ui()
        if task_data:
            self.load_task_data()

    def init_ui(self):
        self.setWindowTitle("编辑任务" if self.task_data else "添加任务")
        self.setFixedSize(550, 520)  # 调整窗口大小
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        # ========== 最简化样式 - 确保正常显示 ==========
        self.setStyleSheet("")  # 先清空所有样式

        # 设置基本字体
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        self.setFont(font)

        # ========== 主布局设置 - 每行独立间距 ==========
        layout = QVBoxLayout()
        layout.setSpacing(25)  # 各个GroupBox之间的垂直间距
        layout.setContentsMargins(30, 30, 30, 30)  # 整个对话框的内边距

        # ========== 基本信息组 ==========
        basic_group = QGroupBox("基本信息")
        basic_layout = QVBoxLayout()
        basic_layout.setSpacing(0)  # 设为0，手动控制间距
        basic_layout.setContentsMargins(25, 30, 25, 25)

        # 任务名称行
        name_row_layout = QHBoxLayout()
        name_row_layout.setSpacing(15)
        name_row_layout.addWidget(QLabel("任务名称:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入任务名称，如：回风斩")
        name_row_layout.addWidget(self.name_edit)
        basic_layout.addLayout(name_row_layout)

        # 添加分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("QFrame { color: #cccccc; margin: 10px 0; }")
        basic_layout.addWidget(line1)

        # 倒计时行
        duration_row_layout = QHBoxLayout()
        duration_row_layout.setSpacing(15)
        duration_row_layout.addWidget(QLabel("倒计时(秒):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" 秒")
        duration_row_layout.addWidget(self.duration_spin)
        basic_layout.addLayout(duration_row_layout)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # ========== 热键设置组 ==========
        hotkey_group = QGroupBox("热键设置")
        hotkey_layout = QVBoxLayout()
        hotkey_layout.setSpacing(0)  # 设为0，手动控制间距
        hotkey_layout.setContentsMargins(25, 30, 25, 25)

        # 启用热键复选框
        self.hotkey_enabled = QCheckBox("启用热键")
        self.hotkey_enabled.setChecked(True)
        hotkey_layout.addWidget(self.hotkey_enabled)

        # 添加分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("QFrame { color: #cccccc; margin: 10px 0; }")
        hotkey_layout.addWidget(line2)

        # 热键输入行
        hotkey_input_layout = QHBoxLayout()
        hotkey_input_layout.setSpacing(15)
        hotkey_input_layout.addWidget(QLabel("热键:"))
        self.hotkey_edit = HotkeyEdit()
        hotkey_input_layout.addWidget(self.hotkey_edit)
        hotkey_layout.addLayout(hotkey_input_layout)

        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        # ========== 提醒设置组 ==========
        reminder_group = QGroupBox("提醒设置")
        reminder_layout = QVBoxLayout()
        reminder_layout.setSpacing(0)  # 设为0，手动控制间距
        reminder_layout.setContentsMargins(30, 35, 30, 30)  # 增加内边距

        # 弹窗提醒行
        popup_row_layout = QHBoxLayout()
        popup_row_layout.setSpacing(20)  # 增加水平间距
        popup_label = QLabel("弹窗提醒:")
        popup_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 12px 0;")  # 只增大字体，增加上下padding
        popup_row_layout.addWidget(popup_label)
        self.popup_combo = QComboBox()
        self.popup_combo.addItems(["是", "否"])
        self.popup_combo.setCurrentText("是")
        self.popup_combo.setStyleSheet("font-size: 16px;")  # 只增大字体，不改变高度
        popup_row_layout.addWidget(self.popup_combo)
        reminder_layout.addLayout(popup_row_layout)

        # 添加分隔线
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        line3.setStyleSheet("QFrame { color: #cccccc; margin: 20px 0; }")  # 进一步增加上下间距
        reminder_layout.addWidget(line3)

        # 语音提醒行
        voice_row_layout = QHBoxLayout()
        voice_row_layout.setSpacing(20)  # 增加水平间距
        voice_label = QLabel("语音提醒:")
        voice_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 12px 0;")  # 只增大字体，增加上下padding
        voice_row_layout.addWidget(voice_label)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["是", "否"])
        self.voice_combo.setCurrentText("是")
        self.voice_combo.setStyleSheet("font-size: 16px;")  # 只增大字体，不改变高度
        voice_row_layout.addWidget(self.voice_combo)
        reminder_layout.addLayout(voice_row_layout)

        # 添加分隔线
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Sunken)
        line4.setStyleSheet("QFrame { color: #cccccc; margin: 20px 0; }")  # 进一步增加上下间距
        reminder_layout.addWidget(line4)

        # 自定义语音行
        custom_voice_row_layout = QHBoxLayout()
        custom_voice_row_layout.setSpacing(20)  # 增加水平间距
        custom_voice_label = QLabel("自定义语音:")
        custom_voice_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 12px 0;")  # 只增大字体，增加上下padding
        custom_voice_row_layout.addWidget(custom_voice_label)
        self.custom_voice_edit = QLineEdit()
        self.custom_voice_edit.setPlaceholderText("留空使用默认语音，如：回风斩时间到了")
        self.custom_voice_edit.setStyleSheet("font-size: 16px;")  # 只增大字体，不改变高度
        custom_voice_row_layout.addWidget(self.custom_voice_edit)
        reminder_layout.addLayout(custom_voice_row_layout)

        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = ModernButton("保存", "#28a745")
        self.save_btn.clicked.connect(self.save_task)

        self.cancel_btn = ModernButton("取消", "#dc3545")
        self.cancel_btn.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_task_data(self):
        """加载任务数据到界面"""
        if self.task_data:
            self.name_edit.setText(self.task_data.get('name', ''))
            self.duration_spin.setValue(self.task_data.get('duration', 60))
            self.hotkey_enabled.setChecked(self.task_data.get('hotkey_enabled', True))
            self.hotkey_edit.setText(self.task_data.get('hotkey', ''))

            # 设置下拉框
            popup_text = "是" if self.task_data.get('popup_reminder', True) else "否"
            self.popup_combo.setCurrentText(popup_text)

            voice_text = "是" if self.task_data.get('voice_reminder', True) else "否"
            self.voice_combo.setCurrentText(voice_text)

            self.custom_voice_edit.setText(self.task_data.get('custom_voice', ''))

    def save_task(self):
        """保存任务"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "请输入任务名称")
            return

        task_data = {
            'id': self.task_data.get('id') if self.task_data else None,
            'name': name,
            'duration': self.duration_spin.value(),
            'hotkey_enabled': self.hotkey_enabled.isChecked(),
            'hotkey': self.hotkey_edit.text().strip(),
            'popup_reminder': self.popup_combo.currentText() == "是",
            'voice_reminder': self.voice_combo.currentText() == "是",
            'custom_voice': self.custom_voice_edit.text().strip()
        }

        self.task_saved.emit(task_data)
        self.close()


class EditableTableWidget(QTableWidget):
    """可编辑的表格控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            current_item = self.currentItem()
            if current_item and current_item.column() == 2:  # 热键列
                current_item.setText("")
                self.save_current_row()
        super().keyPressEvent(event)

    def save_current_row(self):
        """保存当前行的修改"""
        if hasattr(self.parent_window, 'save_table_changes'):
            self.parent_window.save_table_changes()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.timer_manager = TimerManager(self)
        self.init_ui()
        self.init_tray()
        self.load_tasks()

    def init_ui(self):
        self.setWindowTitle("技能倒计时管理器 v2.0")
        self.setGeometry(100, 100, 800, 600)

        # 设置现代化样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                gridline-color: #dee2e6;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            QLabel {
                color: #495057;
                font-weight: bold;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # 标题
        title_label = QLabel("技能倒计时管理器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px 0;
            }
        """)
        layout.addWidget(title_label)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.add_btn = ModernButton("添加任务", "#28a745")
        self.add_btn.clicked.connect(self.add_task)

        self.edit_btn = ModernButton("编辑任务", "#17a2b8")
        self.edit_btn.clicked.connect(self.edit_task)

        self.delete_btn = ModernButton("删除任务", "#dc3545")
        self.delete_btn.clicked.connect(self.delete_task)

        self.start_btn = ModernButton("开始计时", "#28a745")
        self.start_btn.clicked.connect(self.start_timer)

        self.stop_btn = ModernButton("停止计时", "#ffc107")
        self.stop_btn.clicked.connect(self.stop_timer)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

        # 任务表格
        self.task_table = EditableTableWidget(self)
        self.task_table.setColumnCount(7)
        self.task_table.setHorizontalHeaderLabels([
            "任务名称", "倒计时(秒)", "热键", "状态", "弹窗提醒", "语音提醒", "剩余时间"
        ])

        # 设置表格列宽
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)

        # 连接表格编辑信号
        self.task_table.itemChanged.connect(self.on_table_item_changed)
        self.task_table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        layout.addWidget(self.task_table)

        central_widget.setLayout(layout)

        # 状态更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_table_status)
        self.update_timer.start(1000)  # 每秒更新一次

    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("技能倒计时管理器")

        # 设置托盘图标（使用默认图标）
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        self.tray_icon.show()

    def closeEvent(self, event):
        """关闭事件 - 最小化到托盘"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "技能倒计时管理器",
            "程序已最小化到系统托盘",
            QSystemTrayIcon.Information,
            2000
        )

    def add_task(self):
        """添加任务"""
        dialog = TaskEditDialog(parent=self)
        dialog.task_saved.connect(self.save_task)
        dialog.show()

    def edit_task(self):
        """编辑任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请选择要编辑的任务")
            return

        tasks = self.config_manager.get_tasks()
        if current_row < len(tasks):
            task_data = tasks[current_row]
            dialog = TaskEditDialog(task_data, parent=self)
            dialog.task_saved.connect(self.save_task)
            dialog.show()

    def delete_task(self):
        """删除任务"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请选择要删除的任务")
            return

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除选中的任务吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            tasks = self.config_manager.get_tasks()
            if current_row < len(tasks):
                task = tasks[current_row]
                # 停止计时器
                self.timer_manager.stop_timer(task['id'])
                # 删除任务
                self.config_manager.delete_task(task['id'])
                self.load_tasks()

    def save_task(self, task_data):
        """保存任务"""
        if task_data['id'] is None:
            # 新任务
            self.config_manager.add_task(task_data)
        else:
            # 更新任务
            self.config_manager.update_task(task_data)

        self.load_tasks()
        self.timer_manager.update_hotkeys()

    def load_tasks(self):
        """加载任务到表格"""
        tasks = self.config_manager.get_tasks()
        self.task_table.setRowCount(len(tasks))

        # 暂时断开信号连接，避免加载时触发保存
        self.task_table.itemChanged.disconnect()

        for row, task in enumerate(tasks):
            # 任务名称 - 可编辑
            name_item = QTableWidgetItem(task['name'])
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.task_table.setItem(row, 0, name_item)

            # 倒计时 - 可编辑
            duration_item = QTableWidgetItem(str(task['duration']))
            duration_item.setFlags(duration_item.flags() | Qt.ItemIsEditable)
            self.task_table.setItem(row, 1, duration_item)

            # 热键 - 特殊编辑方式
            hotkey_text = task['hotkey'] if task['hotkey_enabled'] and task['hotkey'] else ""
            hotkey_item = QTableWidgetItem(hotkey_text)
            hotkey_item.setFlags(hotkey_item.flags() | Qt.ItemIsEditable)
            self.task_table.setItem(row, 2, hotkey_item)

            # 状态 - 完全只读
            status = "运行中" if self.timer_manager.is_timer_running(task['id']) else "停止"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 只允许选择，不允许编辑
            self.task_table.setItem(row, 3, status_item)

            # 弹窗提醒 - 下拉选择
            popup_text = "是" if task['popup_reminder'] else "否"
            popup_combo = QComboBox()
            popup_combo.addItems(["是", "否"])
            popup_combo.setCurrentText(popup_text)
            popup_combo.currentTextChanged.connect(lambda text, r=row: self.on_popup_changed(r, text))
            self.task_table.setCellWidget(row, 4, popup_combo)

            # 语音提醒 - 下拉选择
            voice_text = "是" if task['voice_reminder'] else "否"
            voice_combo = QComboBox()
            voice_combo.addItems(["是", "否"])
            voice_combo.setCurrentText(voice_text)
            voice_combo.currentTextChanged.connect(lambda text, r=row: self.on_voice_changed(r, text))
            self.task_table.setCellWidget(row, 5, voice_combo)

            # 剩余时间 - 只读
            remaining = self.timer_manager.get_remaining_time(task['id'])
            remaining_text = f"{remaining}秒" if remaining > 0 else "-"
            remaining_item = QTableWidgetItem(remaining_text)
            remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemIsEditable)
            self.task_table.setItem(row, 6, remaining_item)

        # 重新连接信号
        self.task_table.itemChanged.connect(self.on_table_item_changed)

    def update_table_status(self):
        """更新表格状态"""
        tasks = self.config_manager.get_tasks()
        for row, task in enumerate(tasks):
            if row < self.task_table.rowCount():
                # 更新状态 - 确保只读
                status = "运行中" if self.timer_manager.is_timer_running(task['id']) else "停止"
                status_item = QTableWidgetItem(status)
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 只允许选择，不允许编辑
                self.task_table.setItem(row, 3, status_item)

                # 更新剩余时间 - 确保只读
                remaining = self.timer_manager.get_remaining_time(task['id'])
                remaining_text = f"{remaining}秒" if remaining > 0 else "-"
                remaining_item = QTableWidgetItem(remaining_text)
                remaining_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # 只允许选择，不允许编辑
                self.task_table.setItem(row, 6, remaining_item)

    def start_timer(self):
        """开始计时"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请选择要开始计时的任务")
            return

        tasks = self.config_manager.get_tasks()
        if current_row < len(tasks):
            task = tasks[current_row]
            self.timer_manager.start_timer(task['id'])

    def stop_timer(self):
        """停止计时"""
        current_row = self.task_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请选择要停止计时的任务")
            return

        tasks = self.config_manager.get_tasks()
        if current_row < len(tasks):
            task = tasks[current_row]
            self.timer_manager.stop_timer(task['id'])

    def on_cell_double_clicked(self, row, column):
        """处理单元格双击事件"""
        if column == 2:  # 热键列
            self.edit_hotkey(row)

    def on_popup_changed(self, row, text):
        """弹窗提醒改变"""
        tasks = self.config_manager.get_tasks()
        if row < len(tasks):
            task = tasks[row]
            task['popup_reminder'] = (text == "是")
            self.config_manager.update_task(task)

    def on_voice_changed(self, row, text):
        """语音提醒改变"""
        tasks = self.config_manager.get_tasks()
        if row < len(tasks):
            task = tasks[row]
            task['voice_reminder'] = (text == "是")
            self.config_manager.update_task(task)

    def edit_hotkey(self, row):
        """编辑热键"""
        current_item = self.task_table.item(row, 2)
        if current_item:
            # 创建临时的热键编辑器
            hotkey_editor = HotkeyEdit()
            hotkey_editor.setText(current_item.text())

            # 设置为表格的编辑器
            self.task_table.setCellWidget(row, 2, hotkey_editor)
            hotkey_editor.setFocus()

            # 当失去焦点时保存
            def save_hotkey():
                new_hotkey = hotkey_editor.text()
                self.task_table.removeCellWidget(row, 2)
                current_item.setText(new_hotkey)
                self.save_table_changes()

            hotkey_editor.editingFinished.connect(save_hotkey)

    def on_table_item_changed(self, item):
        """处理表格项目改变事件"""
        if item.column() in [0, 1, 2]:  # 只处理可编辑的列
            self.save_table_changes()

    def save_table_changes(self):
        """保存表格修改"""
        tasks = self.config_manager.get_tasks()

        for row in range(self.task_table.rowCount()):
            if row < len(tasks):
                task = tasks[row]

                # 更新任务名称
                name_item = self.task_table.item(row, 0)
                if name_item:
                    new_name = name_item.text().strip()
                    if new_name:
                        task['name'] = new_name

                # 更新倒计时
                duration_item = self.task_table.item(row, 1)
                if duration_item:
                    try:
                        new_duration = int(duration_item.text())
                        if new_duration > 0:
                            task['duration'] = new_duration
                    except ValueError:
                        # 恢复原值
                        duration_item.setText(str(task['duration']))

                # 更新热键
                hotkey_item = self.task_table.item(row, 2)
                if hotkey_item:
                    new_hotkey = hotkey_item.text().strip()
                    task['hotkey'] = new_hotkey
                    task['hotkey_enabled'] = bool(new_hotkey)

                # 保存任务
                self.config_manager.update_task(task)

        # 更新热键绑定
        self.timer_manager.update_hotkeys()

    def show_notification(self, title, message):
        """显示通知"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())