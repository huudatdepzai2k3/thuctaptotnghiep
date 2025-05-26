import sys
import pandas as pd
import cv2
from pyzbar import pyzbar
import numpy as np
import time
import os
import requests
import snap7
from snap7.util import set_int
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTextEdit, QFileDialog, QLineEdit)
from PyQt5.QtGui import QPixmap, QImage, QFont

# Định nghĩa thông số kết nối PLC và Webserver
PLC_IP = '192.168.0.1'
RACK = 0
SLOT = 1
DB_NUMBER = 1
WEBSERVER_URL = 'http://127.0.0.1:5000'

# Các biến lưu trạng thái IP và URL hiện tại
plc_ip_current = PLC_IP
webserver_url_current = WEBSERVER_URL

# Khởi tạo kết nối với PLC
client = snap7.client.Client()
stop_threads = False

try:
    client.connect(plc_ip_current, RACK, SLOT)
    print("✅ Kết nối PLC lần đầu thành công.")
except Exception as e:
    print(f"❌ Không thể kết nối PLC lần đầu: {e}")

# Kiểm tra kết nối đến PLC
def is_connected(client):
    try:
        return client.get_connected()
    except:
        return False

# Kiểm tra kết nối đến Webserver
def is_connected_webserver():
    try:
        response = requests.get(webserver_url_current, timeout=3)
        return response.status_code == 200
    except:
        return False

# Lấy vị trí từ dữ liệu Excel và gửi vào PLC
def get_position_from_file(qr_code):
    global window
    try:
        if 'window' not in globals() or not hasattr(window, 'data_dict'):
            window.log_to_terminal("⚠️ Chưa tải dữ liệu Excel.")
            return [243]

        # Kiểm tra mã QR có trong dữ liệu không
        if qr_code not in window.data_dict:
            window.log_to_terminal("⚠️ QR code không tồn tại trong dữ liệu Excel.")
            return [243]

        address = str(window.data_dict[qr_code]).strip()
        window.pos_label.setText(f"📍 Vị trí: {address}")
        words1 = address.lower().split()
        # Tìm vị trí phù hợp từ dữ liệu vị trí
        max_len_max = 0
        for file_address, file_pos in window.address_to_pos_dict.items():
            words2 = file_address.lower().split()
            max_len = 0
            # Kiểm tra sự trùng lặp giữa các cụm từ liên tiếp
            n, m = len(words1), len(words2)
            dp = [[0] * (m + 1) for _ in range(n + 1)]
          
            for i in range(n):
                for j in range(m):
                    if words1[i] == words2[j]:
                        dp[i + 1][j + 1] = dp[i][j] + 1
                        max_len = max(max_len, dp[i + 1][j + 1])
                    else:
                        dp[i + 1][j + 1] = 0

            if max_len_max <= max_len :
                max_len_max = max_len
        
        if max_len_max > 0:
            for file_address, file_pos in window.address_to_pos_dict.items():
                words3 = file_address.lower().split()
                common_phrase = []
                for i in range(len(words1) - 1):
                    phrase1 = ' '.join(words1[i:i+max_len_max]) 
                    if phrase1 in ' '.join(words3):
                        common_phrase.append(phrase1)

                if common_phrase :        
                    pos = int(file_pos)
                    window.log_to_terminal(f"✅ Vị trí phân loại: {pos}")
                    
                    # Gửi vị trí vào PLC nếu kết nối
                    if is_connected(client):
                        try:
                            index = pos - 1  
                            if 0 <= index <= 7:
                                client.db_write(DB_NUMBER, index, 1)
                                time.sleep(0.2)
                                client.db_write(DB_NUMBER, index, 0)
                                window.log_to_terminal(f"📤 Gửi vị trí vào PLC: {pos}")
                            else:
                                window.log_to_terminal(f"⚠️ Vị trí {pos} không hợp lệ")
                        except Exception as e:
                            window.log_to_terminal(f"❌ Lỗi khi gửi vào PLC: {e}")
 

                            window.log_to_terminal(f"📤 Gửi vị trí vào PLC: {pos}")
                        except Exception as e:
                            window.log_to_terminal(f"❌ Lỗi gửi dữ liệu vị trí vào PLC: {e}")
                    else : 
                        window.log_to_terminal(f"❌ Lỗi gửi dữ liệu vào PLC do mất kết nối với PLC")

                    return [pos]
        else :
            window.log_to_terminal(f"❌ Địa chỉ nằm ngoài phạm vi phân loại")
        window.log_to_terminal("⚠️ Không tìm thấy dữ liệu vị trí hệ thống phù hợp.")
        return [243]

    except Exception as e:
        window.log_to_terminal(f"❌ Lỗi đọc file: {e}")
        return [234]


# Lớp xử lý quét QR Code trong luồng riêng
class QRScannerThread(QThread):
    frame_updated = pyqtSignal(np.ndarray)  # Tín hiệu cập nhật ảnh
    qr_code_detected = pyqtSignal(str)  # Tín hiệu phát hiện mã QR

    def __init__(self):
        super().__init__()
        self.last_detection_time = time.time()
        self.last_qr_code = ""

    def run(self):
        global stop_threads

        # Khởi tạo camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            window.log_to_terminal("❌ Không thể mở camera!")
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            self.frame_updated.emit(blank)
            return

        cap.set(3, 640)  # Đặt chiều rộng của video
        cap.set(4, 480)  # Đặt chiều cao của video

        while not stop_threads:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Chuyển đổi ảnh sang xám để quét QR code
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            qrcodes = pyzbar.decode(gray)

            # Kiểm tra và vẽ các mã QR lên ảnh
            for qrcode in qrcodes:
                (x, y, w, h) = qrcode.rect
                if w > 0 and h > 0:
                    data = qrcode.data.decode('utf-8')
                    # Chỉ cập nhật mã QR mới sau mỗi 0.5s
                    if time.time() - self.last_detection_time > 0.5 and data != self.last_qr_code:
                        self.last_qr_code = data
                        window.log_to_terminal(f"📷 Mã QR mới: {data}")
                        result = get_position_from_file(data)
                        if isinstance(result, list):
                            self.qr_code_detected.emit(data)
                        self.last_detection_time = time.time()
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.putText(frame, f"{data}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 2)

            self.frame_updated.emit(frame)

        cap.release()


# Lớp theo dõi trạng thái kết nối PLC và Webserver
class ConnectionMonitorThread(QThread):
    status_updated = pyqtSignal(bool, bool)
    last_plc_status = None
    last_web_status = None

    def run(self):
        global stop_threads
        while not stop_threads:
            plc_status = is_connected(client)  # Kiểm tra kết nối PLC
            web_status = is_connected_webserver()  # Kiểm tra kết nối Webserver
            if plc_status != self.last_plc_status or web_status != self.last_web_status:
                self.status_updated.emit(plc_status, web_status)  # Cập nhật trạng thái kết nối
                self.last_plc_status = plc_status
                self.last_web_status = web_status
            time.sleep(3)

            if not plc_status:
                window.log_to_terminal("🔄 Mất kết nối PLC. Thử kết nối lại...")
                try:
                    if not client.get_connected():
                        client.connect(plc_ip_current, RACK, SLOT)
                        window.log_to_terminal("✅ Đã kết nối lại PLC thành công.")
                except Exception as e:
                    window.log_to_terminal(f"❌ Lỗi kết nối lại PLC: {e}")


# Lớp giao diện chính ứng dụng
class DemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giao diện đầu vào")
        self.setFixedSize(1800, 600)
        self.setGeometry(100, 100, 1000, 300)

        # Thiết lập giao diện
        main_layout = QHBoxLayout()

        self.excel_btn = QPushButton("📂 Chọn file Excel")
        self.excel_btn.clicked.connect(self.load_excel)  # Nút chọn file Excel
        self.excel_display = QTextEdit()
        self.excel_display.setReadOnly(True)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("🗂 Nhập dữ liệu từ Excel:"))
        left_layout.addWidget(self.excel_btn)
        left_layout.addWidget(self.excel_display)

        # Hiển thị video từ camera
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        self.image_label.setStyleSheet("background-color: lightgray")

        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("🎥 Camera (video trực tiếp):"))
        center_layout.addWidget(self.image_label)

        # Hiển thị thông tin về mã QR và vị trí
        self.qr_label = QLabel("📦 Mã QR: (chưa có)")
        self.pos_label = QLabel("📍 Vị trí: (chưa có)")
        self.plc_status_label = QLabel("🔌 PLC: Đang kiểm tra...")
        self.webserver_status_label = QLabel("🔌 Webserver: Đang kiểm tra...")

        # Đèn báo trạng thái kết nối
        self.plc_status_led = QLabel()
        self.plc_status_led.setFixedSize(20, 20)
        self.webserver_status_led = QLabel()
        self.webserver_status_led.setFixedSize(20, 20)

        # Các layout cho PLC và Webserver
        plc_layout = QHBoxLayout()
        plc_layout.addWidget(self.plc_status_label)
        plc_layout.addWidget(self.plc_status_led)
        web_layout = QHBoxLayout()
        web_layout.addWidget(self.webserver_status_label)
        web_layout.addWidget(self.webserver_status_led)

        self.ip_input = QLineEdit()
        self.ip_input.setText(PLC_IP)
        self.url_input = QLineEdit()
        self.url_input.setText(WEBSERVER_URL)

        self.ip_btn = QPushButton("🔄 Cập nhật IP và URL mới.")
        self.ip_btn.clicked.connect(self.update_plc_webserver_address)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("📤 Thông tin Output:"))
        right_layout.addWidget(self.qr_label)
        right_layout.addWidget(self.pos_label)
        right_layout.addLayout(plc_layout)
        right_layout.addLayout(web_layout)
        right_layout.addWidget(QLabel("🌐 URL Webserver:"))
        right_layout.addWidget(self.url_input)
        right_layout.addWidget(QLabel("🌐 IP PLC:"))
        right_layout.addWidget(self.ip_input)
        right_layout.addWidget(self.ip_btn)
        right_layout.addStretch()

        # Output cho terminal log
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("background-color: black; color: white;")
        font = QFont("Consolas")
        font.setPointSize(9)
        self.terminal_output.setFont(font)

        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(QLabel("🖥 Terminal Output:"))
        terminal_layout.addWidget(self.terminal_output)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(center_layout)
        main_layout.addLayout(right_layout)
        main_layout.addLayout(terminal_layout)

        self.setLayout(main_layout)
        self.data_dict = {}
        self.address_to_pos_dict = {}

        # Khởi tạo các thread
        self.qr_scanner_thread = QRScannerThread()
        self.qr_scanner_thread.frame_updated.connect(self.update_image)
        self.qr_scanner_thread.qr_code_detected.connect(self.update_qr_info)
        self.qr_scanner_thread.start()

        self.connection_thread = ConnectionMonitorThread()
        self.connection_thread.status_updated.connect(self.update_status)
        self.connection_thread.start()

    # Hàm log thông báo vào terminal
    def log_to_terminal(self, msg):
        self.terminal_output.moveCursor(self.terminal_output.textCursor().End)
        self.terminal_output.insertPlainText(msg + '\n')
        self.terminal_output.moveCursor(self.terminal_output.textCursor().End)

    # Hàm tải dữ liệu từ file Excel
    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            try:
                df = pd.read_excel(file_path)
                if not {'QR', 'Address'}.issubset(df.columns):
                    self.excel_display.setText("❌ File Excel cần có cột 'QR' và 'Address'")
                    return
                self.excel_display.setText(str(df))
                self.data_dict = {str(row['QR']).strip(): row['Address'] for _, row in df.iterrows()}
                self.address_to_pos_dict = {}
                file_path_txt = os.path.join(os.getcwd(), "adress_to_position.txt")
                if os.path.exists(file_path_txt):
                    with open(file_path_txt, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split(' | ')
                            if len(parts) >= 2:
                                addr, pos = parts
                                self.address_to_pos_dict[addr.strip()] = int(float(pos))
                else :
                    self.log_to_terminal("❌ Thiếu dữ liệu vị trí setup.")
                self.log_to_terminal("✅ Đã tải dữ liệu Excel và dữ liệu vị trí.")
            except Exception as e:
                self.excel_display.setText(f"Lỗi: {e}")
                self.log_to_terminal(f"❌ Lỗi tải Excel: {e}")

    # Cập nhật hình ảnh từ camera
    def update_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(self.image_label.size(), Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    # Cập nhật thông tin mã QR khi phát hiện
    def update_qr_info(self, qr_code):
        self.qr_label.setText(f"📦 Mã QR: {qr_code}")

    # Cập nhật trạng thái kết nối PLC và Webserver
    def update_status(self, plc_connected, web_connected):
        self.plc_status_label.setText("🔌 PLC: Đã kết nối" if plc_connected else "🔌 PLC: Mất kết nối")
        self.plc_status_led.setStyleSheet("background-color: green;" if plc_connected else "background-color: red;")
        self.webserver_status_label.setText("🔌 Webserver: Đã kết nối" if web_connected else "🔌 Webserver: Mất kết nối")
        self.webserver_status_led.setStyleSheet("background-color: green;" if web_connected else "background-color: red;")

    # Cập nhật lại IP và URL cho PLC và Webserver
    def update_plc_webserver_address(self):
        global plc_ip_current, webserver_url_current
        new_ip = self.ip_input.text().strip()
        new_url = self.url_input.text().strip()
        if not new_ip or not new_url:
            self.log_to_terminal("❌ IP PLC hoặc URL Webserver không được để trống.")
            return
        plc_ip_current = new_ip
        webserver_url_current = new_url
        self.log_to_terminal(f"🔁 Đã cập nhật PLC IP mới : {new_ip} và URL Webserver mới : {new_url}.")

    # Xử lý sự kiện khi đóng cửa sổ
    def closeEvent(self, event):
        global stop_threads
        stop_threads = True
        self.qr_scanner_thread.quit()
        self.connection_thread.quit()
        self.qr_scanner_thread.wait()
        self.connection_thread.wait()
        event.accept()


# Chạy ứng dụng
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoApp()
    window.show()
    sys.exit(app.exec_())
