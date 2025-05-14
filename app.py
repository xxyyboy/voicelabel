import os
import sys
import nltk
from spellchecker import SpellChecker
from PyQt5.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, 
                            QTableWidget, QTableWidgetItem, QPushButton, 
                            QLineEdit, QLabel, QFileDialog, QTextEdit,
                            QComboBox, QSpinBox, QMessageBox)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class AudioTextEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_extensions = ['.mp3', '.wav', '.ogg']
        self.text_extensions = ['.txt', '.lrc' , '.normalized.txt']
        self.current_dir = ""
        self.media_player = QMediaPlayer()
        self.current_text_file = None
        self.spell_checker = SpellChecker()
        
        # 下载NLTK数据
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        
        self.initUI()
        self.setWindowSizeToScreenPercentage(0.5)  # 设置为屏幕的50%
        
    def initUI(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 顶部控制栏
        control_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("输入目录路径或点击浏览...")
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_directory)
        load_btn = QPushButton("加载")
        load_btn.clicked.connect(self.load_files)
        
        control_layout.addWidget(QLabel("目录:"))
        control_layout.addWidget(self.dir_input)
        control_layout.addWidget(browse_btn)
        control_layout.addWidget(load_btn)
        
        # 字体控制栏
        font_control_layout = QHBoxLayout()
        self.font_combo = QComboBox()
        self.font_combo.addItems(QFontDatabase().families())
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(12)
        self.font_size.valueChanged.connect(self.change_font)
        self.font_combo.currentTextChanged.connect(self.change_font)
        apply_font_btn = QPushButton("应用字体")
        apply_font_btn.clicked.connect(self.change_font)
        
        font_control_layout.addWidget(QLabel("字体:"))
        font_control_layout.addWidget(self.font_combo)
        font_control_layout.addWidget(QLabel("大小:"))
        font_control_layout.addWidget(self.font_size)
        font_control_layout.addWidget(apply_font_btn)
        
        # 文本检查按钮
        self.check_text_btn = QPushButton("检查文本通顺度")
        self.check_text_btn.clicked.connect(self.check_text_fluency)
        font_control_layout.addWidget(self.check_text_btn)
        
        # 文件显示区域
        file_display_layout = QHBoxLayout()
        
        # 左侧音频表格
        self.audio_table = QTableWidget()
        self.audio_table.setColumnCount(1)
        self.audio_table.setHorizontalHeaderLabels(["音频文件"])
        self.audio_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.audio_table.setSelectionMode(QTableWidget.SingleSelection)
        self.audio_table.cellClicked.connect(self.on_audio_selected)
        
        # 启用键盘选择
        self.audio_table.setFocusPolicy(Qt.StrongFocus)
        self.audio_table.keyPressEvent = self.table_key_press_event
        
        # 右侧文本编辑区
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("选择音频文件后，对应的文本将显示在这里")
        
        # 底部控制按钮
        bottom_controls = QHBoxLayout()
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play_selected_audio)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_audio)
        save_btn = QPushButton("保存文本")
        save_btn.clicked.connect(self.save_text_file)
        
        bottom_controls.addWidget(self.play_btn)
        bottom_controls.addWidget(self.stop_btn)
        bottom_controls.addWidget(save_btn)
        
        file_display_layout.addWidget(self.audio_table, 1)
        file_display_layout.addWidget(self.text_edit, 1)
        
        # 添加到主布局
        main_layout.addLayout(control_layout)
        main_layout.addLayout(font_control_layout)
        main_layout.addLayout(file_display_layout, 1)
        main_layout.addLayout(bottom_controls)
        
        self.setLayout(main_layout)
        self.setWindowTitle("音频文本编辑器")
        
    def setWindowSizeToScreenPercentage(self, percentage):
        """设置窗口大小为屏幕的指定百分比"""
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * percentage)
        height = int(screen.height() * percentage)
        self.resize(width, height)
        
    def table_key_press_event(self, event):
        """处理键盘上下键选择"""
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            # 调用原始按键处理
            QTableWidget.keyPressEvent(self.audio_table, event)
            # 获取当前选中行
            selected = self.audio_table.currentRow()
            if selected >= 0:
                self.on_audio_selected(selected, 0)
        else:
            QTableWidget.keyPressEvent(self.audio_table, event)
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.dir_input.setText(dir_path)
            self.current_dir = dir_path
            self.load_files()
    
    def load_files(self):
        dir_path = self.dir_input.text()
        if not dir_path or not os.path.isdir(dir_path):
            return
            
        self.current_dir = dir_path
        self.audio_table.setRowCount(0)
        
        # 获取所有音频文件
        audio_files = []
        for file in os.listdir(dir_path):
            if any(file.lower().endswith(ext) for ext in self.audio_extensions):
                audio_files.append(file)
        
        # 显示音频文件
        self.audio_table.setRowCount(len(audio_files))
        for i, audio_file in enumerate(audio_files):
            item = QTableWidgetItem(audio_file)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.audio_table.setItem(i, 0, item)
    
    def on_audio_selected(self, row, column):
        """当音频文件被选中时自动播放并加载对应文本"""
        self.play_selected_audio()
        self.load_corresponding_text(self.audio_table.item(row, 0).text())
    
    def play_selected_audio(self):
        selected = self.audio_table.currentRow()
        if selected >= 0:
            audio_file = self.audio_table.item(selected, 0).text()
            audio_path = os.path.join(self.current_dir, audio_file)
            
            # 加载并播放音频
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_path)))
            self.media_player.play()
    
    def stop_audio(self):
        self.media_player.stop()
    
    def load_corresponding_text(self, audio_file):
        """加载与音频文件同名的文本文件"""
        base_name = os.path.splitext(audio_file)[0]
        
        # 查找匹配的文本文件
        for ext in self.text_extensions:
            text_file = base_name + ext
            text_path = os.path.join(self.current_dir, text_file)
            
            if os.path.exists(text_path):
                try:
                    with open(text_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        self.text_edit.setPlainText(content)
                        self.current_text_file = text_path
                    return
                except Exception as e:
                    print(f"读取文本文件出错: {e}")
        
        # 没有找到对应的文本文件
        self.text_edit.setPlainText("")
        self.current_text_file = None
    
    def save_text_file(self):
        if self.current_text_file:
            try:
                with open(self.current_text_file, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
            except Exception as e:
                print(f"保存文本文件出错: {e}")
    
    def change_font(self):
        """更改文本编辑框的字体和大小"""
        font = QFont(self.font_combo.currentText(), self.font_size.value())
        self.text_edit.setFont(font)
    
    def check_text_fluency(self):
        """检查文本通顺度并给出建议"""
        text = self.text_edit.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "提示", "文本内容为空，无法检查通顺度")
            return
        
        # 拼写检查
        words = nltk.word_tokenize(text)
        misspelled = self.spell_checker.unknown(words)
        
        # 基本语法检查（检查词性序列是否合理）
        tagged = nltk.pos_tag(words)
        grammar_issues = self.check_grammar_patterns(tagged)
        
        suggestions = []
        
        # 拼写错误建议
        for word in misspelled:
            corrections = self.spell_checker.correction(word)
            suggestions.append(f"拼写可能错误: '{word}'，建议修改为: '{corrections}'")
        
        # 语法问题建议
        suggestions.extend(grammar_issues)
        
        if not suggestions:
            QMessageBox.information(self, "检查结果", "文本通顺，没有发现明显问题")
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("文本通顺度检查结果")
            msg_box.setText("发现以下可能的问题:")
            msg_box.setDetailedText("\n".join(suggestions))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
    
    def check_grammar_patterns(self, tagged_sentence):
        """检查基本的语法模式"""
        issues = []
        prev_tag = None
        
        for i, (word, tag) in enumerate(tagged_sentence):
            # 检查连续的名词（可能缺少动词）
            if tag.startswith('NN') and prev_tag and prev_tag.startswith('NN'):
                issues.append(f"语法问题: 位置{i-1}-{i}，连续名词 '{tagged_sentence[i-1][0]}' 和 '{word}' 可能缺少动词")
            
            # 检查动词后接名词的情况（中文基本语法）
            if tag.startswith('NN') and prev_tag and prev_tag.startswith('VB'):
                pass  # 这是正常情况
            elif tag.startswith('NN') and prev_tag and not prev_tag.startswith('VB'):
                issues.append(f"语法问题: 位置{i}，名词 '{word}' 前面可能需要动词")
            
            prev_tag = tag
        
        return issues

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioTextEditor()
    window.show()
    sys.exit(app.exec_())
