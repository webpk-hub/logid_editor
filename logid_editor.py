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
        
        # 核心变量
        self.current_file_path = None
        self.device_name = "Unknown Device"  # 用于存储从文件读取到的设备名称
        
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
        file_layout.addWidget(self.lbl_file_path, 1) 
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # --- Device Settings Group (动态标题) ---
        self.device_group_box = QGroupBox("Device Settings")
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
        
        self.device_group_box.setLayout(self.device_form)
        main_layout.addWidget(self.device_group_box)

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
        self.save_btn.setEnabled(False) 
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
            
            # 1. 解析设备名称 (核心修改点)
            name_match = re.search(r'name:\s*"([^"]+)";', content)
            if name_match:
                self.device_name = name_match.group(1)
                self.device_group_box.setTitle(f"Device Settings ({self.device_name})")
            else:
                self.device_name = "Unknown Device"
                self.device_group_box.setTitle("Device Settings (Unknown)")

            # 2. 解析其他参数 (增加安全性检查)
            dpi_match = re.search(r'dpi:\s*(\d+);', content)
            self.edit_dpi.setText(dpi_match.group(1) if dpi_match else "0")

            self.edit_smartshift_on.setChecked('smartshift:\s*{\s*on:\s*true' in content)
            
            threshold_match = re.search(r'threshold:\s*(\d+);', content)
            self.edit_smartshift_threshold.setText(threshold_match.group(1) if threshold_match else "0")
            
            torque_match = re.search(r'torque:\s*(\d+);', content)
            self.edit_smartshift_torque.setText(torque_match.group(1) if torque_match else "0")

            self.edit_hires_on.setChecked('hiresscroll:\s*{\s*hires:\s*true' in content)
            self.edit_hires_invert.setChecked('invert:\s*true' in content)

            # 3. 解析按钮
            button_pattern = re.compile(r'cid:\s*(0x[0-9a-fA-F]+);.*?keys:\s*\[(.*?)\]', re.DOTALL)
            buttons = button_pattern.findall(content)
            
            self.btn_table.setRowCount(0)
            for cid, keys in buttons:
                row = self.btn_table.rowCount()
                self.btn_table.insertRow(row)
                self.btn_table.setItem(row, 0, QTableWidgetItem(cid))
                
                # 简单的描述逻辑
                desc = "Button"
                if cid == "0x053": desc = "Back"
                elif cid == "0x056": desc = "Front"
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
            # 使用 self.device_name 构建新的文件内容 (核心修改点)
            new_content = f"""devices: (
{{
    name: "{self.device_name}";
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
                cid_item = self.btn_table.item(i, 0)
                keys_item = self.btn_table.item(i, 2)
                
                if not cid_item or not keys_item:
                    continue

                cid = cid_item.text()
                keys_raw = keys_item.text()
                key_list = [k.strip() for k in keys_raw.split(',') if k.strip()]
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
    app.setStyle("Fusion") 
    window = LogidEditor()
    window.show()
    sys.exit(app.exec())
