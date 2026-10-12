import sys
import re
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, 
                             QLabel, QGroupBox, QFormLayout, QCheckBox, QHeaderView, 
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt

class LogidEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LogiD Config GUI Editor")
        self.resize(850, 650)
        
        # 核心变量：记录当前打开的文件路径
        self.current_file_path = None
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top Bar: File Selection ---
        file_group = QGroupBox("File Management")
        file_layout = QHBoxLayout()
        
        self.lbl_file_path = QLabel("No file selected")
        self.lbl_file_path.setStyleSheet("color: gray; font-style: italic;")
        
        btn_open = QPushButton("Open logid.cfg")
        btn_open.clicked.connect(self.open_file_dialog)
        
        file_layout.addWidget(btn_open)
        file_layout.addWidget(self.lbl_file_path, 1) # 权重为1，占据剩余空间
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # --- Device Settings Group ---
        device_group = QGroupBox("Device Settings (Wireless Mobile Mouse MX Anywhere 2S)")
        self.device_form = QFormLayout()
        
        self.edit_dpi = QLineEdit()
        self.edit_smartshift_on = QCheckBox("Smartshift On")
        self.edit_smartshift_threshold = QLineEdit()
        self.edit_smartshift_torque = QLineEdit()
        self.edit_hires_on = QCheckBox("Hiresscroll On")
        self.edit_hires_invert = QCheckBox("Invert Scroll")

        self.device_form.addRow("DPI:", self.edit_dpi)
        self.device_form.addRow(self.edit_smartshift_on)
        self.device_form.addRow("Smartshift Threshold:", self.edit_smartshift_threshold)
        self.device_form.addRow("Smartshift Torque:", self.edit_smartshift_torque)
        self.device_form.addRow(self.edit_hires_on)
        self.device_form.addRow(self.edit_hires_invert)
        
        device_group.setLayout(self.device_form)
        main_layout.addWidget(device_group)

        # --- Buttons Table ---
        button_group = QGroupBox("Button Mapping (CID -> Keys)")
        button_layout = QVBoxLayout()
        self.btn_table = QTableWidget(0, 3)
        self.btn_table.setHorizontalHeaderLabels(["CID (Hex)", "Description", "Keys (Comma separated)"])
        self.btn_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        button_layout.addWidget(self.btn_table)
        
        btn_ctrl_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Button")
        self.del_btn = QPushButton("Delete Selected")
        btn_ctrl_layout.addWidget(self.add_btn)
        btn_ctrl_layout.addWidget(self.del_btn)
        button_layout.addLayout(btn_ctrl_layout)
        
        button_group.setLayout(button_layout)
        main_layout.addWidget(button_group)

        # --- Bottom Buttons ---
        bottom_layout = QHBoxLayout()
        self.save_btn = QPushButton("SAVE CHANGES")
        self.save_btn.setEnabled(False) # 初始状态不可点击，直到加载了文件
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        bottom_layout.addWidget(self.save_btn)
        main_layout.addLayout(bottom_layout)

        # Signals
        self.save_btn.clicked.connect(self.save_config)
        self.add_btn.clicked.connect(self.add_button_row)
        self.del_btn.clicked.connect(self.delete_button_row)

    def open_file_dialog(self):
        """弹出文件选择对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select logid.cfg", "", "Config Files (*.cfg);;All Files (*)"
        )
        if file_path:
            self.current_file_path = file_path
            self.lbl_file_path.setText(os.path.basename(file_path))
            self.lbl_file_path.setStyleSheet("color: black; font-style: normal;")
            self.load_config()
            self.save_btn.setEnabled(True)

    def load_config(self):
        try:
            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析逻辑 (保持与之前一致，使用正则)
            self.edit_dpi.setText(re.search(r'dpi:\s*(\d+);', content).group(1))
            self.edit_smartshift_on.setChecked('smartshift:\s*{\s*on:\s*true' in content)
            self.edit_smartshift_threshold.setText(re.search(r'threshold:\s*(\d+);', content).group(1))
            self.edit_smartshift_torque.setText(re.search(r'torque:\s*(\d+);', content).group(1))
            self.edit_hires_on.setChecked('hiresscroll:\s*{\s*hires:\s*true' in content)
            self.edit_hires_invert.setChecked('invert:\s*true' in content)

            # 解析按钮
            button_pattern = re.compile(r'cid:\s*(0x[0-9a-fA-F]+);.*?keys:\s*\[(.*?)\]', re.DOTALL)
            buttons = button_pattern.findall(content)
            
            self.btn_table.setRowCount(0)
            for cid, keys in buttons:
                row = self.btn_table.rowCount()
                self.btn_table.insertRow(row)
                self.btn_table.setItem(row, 0, QTableWidgetItem(cid))
                
                # 简单的描述逻辑
                desc = "Button"
                if "back" in content.lower() and cid == "0x053": desc = "Back"
                elif "front" in content.lower() and cid == "0x056": desc = "Front"
                self.btn_table.setItem(row, 1, QTableWidgetItem(desc))
                
                clean_keys = keys.replace('"', '').replace("'", "").strip()
                self.btn_table.setItem(row, 2, QTableWidgetItem(clean_keys))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load config:\n{str(e)}")

    def add_button_row(self):
        row = self.btn_table.rowCount()
        self.btn_table.insertRow(row)
        self.btn_table.setItem(row, 0, QTableWidgetItem("0x000"))
        self.btn_table.setItem(row, 1, QTableWidgetItem("New Button"))
        self.btn_table.setItem(row, 2, QTableWidgetItem("KEY_A"))

    def delete_button_row(self):
        current_row = self.btn_table.currentRow()
        if current_row >= 0:
            self.btn_table.removeRow(current_row)

    def save_config(self):
        if not self.current_file_path:
            return

        try:
            # 构建新的文件内容 (严格遵循原始格式)
            new_content = f"""devices: (
{{
    name: "Wireless Mobile Mouse MX Anywhere 2S";
    smartshift:
    {{
        on: {"true" if self.edit_smartshift_on.isChecked() else "false"};
        threshold: {self.edit_smartshift_threshold.text()};
        torque: {self.edit_smartshift_torque.text()};
    }};
    hiresscroll:
    {{
        hires: {"true" if self.edit_hires_on.isChecked() else "false"};
        invert: {"true" if self.edit_hires_invert.isChecked() else "false"};
        target: false;
    }};
    dpi: {self.edit_dpi.text()};

    buttons: (
"""
            for i in range(self.btn_table.rowCount()):
                cid = self.btn_table.item(i, 0).text()
                keys_raw = self.btn_table.item(i, 2).text()
                key_list = [k.strip() for k in keys_raw.split(',')]
                keys_formatted = ", ".join([f'"{k}"' for k in key_list])
                
                new_content += f"""        {{
            cid: {cid};
            action =
            {{
                type: "Keypress";
                keys: [{keys_formatted}];
            }};
        }},\n"""

            # 移除最后一个逗号并闭合括号
            new_content = new_content.rstrip(",\n") + """
    );
}
);
"""
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            QMessageBox.information(self, "Success", f"Saved to:\n{self.current_file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局样式，让它看起来现代一点
    app.setStyle("Fusion") 
    window = LogidEditor()
    window.show()
    sys.exit(app.exec())

