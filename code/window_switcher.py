import sys
import subprocess
from PyQt5.QtCore import Qt, QPoint, QElapsedTimer
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QSizePolicy

# 获取当前所有应用程序的窗口
def get_windows():
    # 使用AppleScript获取当前打开的应用程序及其窗口名称
    script = '''
    set window_list to ""
    tell application "System Events"
        set app_list to (name of every process whose visible is true)
        repeat with app_name in app_list
            set window_list to window_list & app_name & "\n"
        end repeat
    end tell
    return window_list
    '''
    windows = subprocess.check_output(['osascript', '-e', script]).decode('utf-8').splitlines()

    # 过滤掉空的或无效的应用程序名称
    windows = [window for window in windows if window.strip()]  # 只保留非空项
    return windows

# 切换到指定应用程序
def switch_window(app_name):
    script = f'''
    tell application "{app_name}"
        reopen
        activate
    end tell
    '''
    subprocess.run(['osascript', '-e', script])

# 悬浮窗口类
class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.app_map = {}  # Initialize app_map before calling initUI
        self.initUI()
        self._is_dragging = False  # 标记是否正在拖动
        self.oldPos = self.pos()  # 记录窗口的初始位置
        self.press_time = QElapsedTimer()  # 用于记录按下的时间

    def initUI(self):
        # 设置窗口无边框，透明度，可拖动
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(50, 50, 50, 200); border-radius: 10px;")
        self.resize(200, 300)

        # 创建布局和按钮
        layout = QVBoxLayout(self)
        windows = get_windows()

        for i, app_name in enumerate(windows):
            if app_name.strip():
                btn = QPushButton(f"App {i+1}: {app_name}", self)

                # 添加鼠标事件到按钮，用于判断单击和拖动
                btn.mousePressEvent = self.start_drag
                btn.mouseMoveEvent = self.dragging
                btn.mouseReleaseEvent = self.handle_release

                # 将按钮与应用程序名称映射
                self.app_map[btn] = app_name

                # 设置按钮样式
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 128);  /* 50%透明 */
                        color: black;                                
                        margin: 0px;
                        padding: 0px 10px;
                        min-height: 45px;  /* 按钮高度增加到1.5倍 */
                        min-width: 50px;   /* 按钮宽度缩减 */
                        border-radius: 10px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 180);  /* 悬停时稍微减少透明度 */
                    }
                """)
                btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)  # 按钮自适应内容宽度
                layout.addWidget(btn)

        # 调整按钮之间的间距
        layout.setSpacing(5)  # 设置按钮之间的间距为5px，相当于四分之一
        layout.setContentsMargins(0, 0, 0, 0)  # 去除额外的空隙
        self.setLayout(layout)

    # 鼠标按下事件：记录时间并准备拖动
    def start_drag(self, event):
        if event.button() == Qt.LeftButton:
            self.press_time.start()  # 记录按下的时间
            self._is_dragging = True
            self.oldPos = event.globalPos()  # 记录鼠标按下时的位置

    # 鼠标移动事件：拖动窗口
    def dragging(self, event):
        if self._is_dragging:
            delta = QPoint(event.globalPos() - self.oldPos)  # 计算鼠标移动的距离
            self.move(self.x() + delta.x(), self.y() + delta.y())  # 移动窗口
            self.oldPos = event.globalPos()  # 更新当前位置

    # 鼠标释放事件：根据时间差判断是单击还是拖动
    def handle_release(self, event):
        if event.button() == Qt.LeftButton:
            elapsed_time = self.press_time.elapsed()  # 计算时间差
            self._is_dragging = False  # 停止拖动
            if elapsed_time < 200:  # 如果时间差小于200ms，视为单击
                self.clicked_event(event)

    # 按钮点击事件：根据点击的按钮，激活相应的应用程序窗口
    def clicked_event(self, event):
        clicked_button = self.childAt(event.pos())  # 获取点击的按钮
        if clicked_button in self.app_map:
            app_name = self.app_map[clicked_button]  # 找到对应的应用程序名称
            switch_window(app_name)  # 激活对应的应用程序窗口

if __name__ == '__main__':
    app = QApplication(sys.argv)
    floating_window = FloatingWindow()
    floating_window.show()
    sys.exit(app.exec_())
