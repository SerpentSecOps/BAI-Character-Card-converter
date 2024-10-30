import base64
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, QTextEdit, QLabel, QVBoxLayout, QWidget, QPushButton, QMenuBar, QMenu, QSlider)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PIL import Image
from PIL.PngImagePlugin import PngImageFile, PngInfo
import sys

current_file_path = None


def extract_base64_from_image(image_path):
    try:
        image = Image.open(image_path)
        if not isinstance(image, PngImageFile):
            raise ValueError("The selected file is not a valid PNG image.")

        metadata = image.info
        # Extract base64-encoded data from either 'UserComment' or 'exif'
        user_comment_raw = metadata.get("UserComment", None)

        if not user_comment_raw and "exif" in metadata:
            # Try to extract from EXIF data if UserComment is not found
            exif_data = metadata.get("exif")
            try:
                exif_str = exif_data.decode('utf-8', 'ignore')
                start_idx = exif_str.find("ASCII\x00\x00\x00")
                if start_idx != -1:
                    user_comment_raw = exif_str[start_idx + len("ASCII\x00\x00\x00"):]
            except Exception as e:
                print(f"Error decoding EXIF data: {e}")

        if not user_comment_raw:
            raise ValueError("No 'UserComment' or suitable EXIF data found in the image metadata.")

        base64_data = user_comment_raw.split('ASCII\x00\x00\x00')[-1]
        decoded_data = base64.b64decode(base64_data).decode('utf-8', 'ignore')

        return decoded_data

    except Exception as e:
        print(f"Error extracting data from {image_path}: {e}")
        return None


def embed_json_to_image(image_path, json_data, output_image_path):
    try:
        image = Image.open(image_path)

        # Convert JSON to Base64-encoded string
        json_string = json.dumps(json_data, ensure_ascii=False)
        base64_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

        # Create metadata object and add UserComment
        metadata = PngInfo()
        metadata.add_text("UserComment", f"ASCII\x00\x00\x00{base64_data}")

        # Save the new image with the modified metadata
        image.save(output_image_path, "PNG", pnginfo=metadata)
        QMessageBox.information(None, "Success", f"Modified image saved as {output_image_path}")

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to save image with new data: {e}")


def load_image_data():
    global current_file_path
    file_path, _ = QFileDialog.getOpenFileName(None, "Select PNG File", "", "PNG Files (*.png)")
    if not file_path:
        return None, None

    json_data = extract_base64_from_image(file_path)
    if json_data:
        current_file_path = file_path
        return json.loads(json_data), file_path
    else:
        QMessageBox.critical(None, "Error", "Failed to extract or decode data.")
        return None, None


def save_changes(text_area):
    global current_file_path
    if current_file_path:
        updated_data = text_area.toPlainText()
        try:
            json_data = json.loads(updated_data)
            # Save the updated data to a new file
            output_file_path, _ = QFileDialog.getSaveFileName(None, "Save PNG File", "", "PNG Files (*.png)")
            if output_file_path:
                embed_json_to_image(current_file_path, json_data, output_file_path)
        except json.JSONDecodeError:
            QMessageBox.critical(None, "Error", "Invalid JSON format. Please correct the data.")
    else:
        QMessageBox.critical(None, "Error", "No file is currently open.")


def export_data(text_area, file_format):
    export_data = text_area.toPlainText()
    file_extension = file_format.lower()

    export_file, _ = QFileDialog.getSaveFileName(None, f"Export as {file_format.upper()}", "", f"{file_format.upper()} Files (*.{file_extension})")

    if export_file:
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(export_data)
        QMessageBox.information(None, "Success", f"Data exported as {file_format.upper()}.")


class EditorWindow(QMainWindow):
    def __init__(self, json_data, file_path):
        super().__init__()
        self.setWindowTitle("Character Sheet Editor")
        self.setGeometry(100, 100, 800, 600)

        self.text_font = QFont("Helvetica", 12)

        # Set up the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        label = QLabel("Edit Character Sheet")
        layout.addWidget(label)

        self.text_area = QTextEdit()
        self.text_area.setFont(self.text_font)
        self.text_area.setText(json.dumps(json_data, indent=4))
        layout.addWidget(self.text_area)

        zoom_in_button = QPushButton("Zoom In (Ctrl +)")
        zoom_in_button.clicked.connect(self.zoom_in)
        layout.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Zoom Out (Ctrl -)")
        zoom_out_button.clicked.connect(self.zoom_out)
        layout.addWidget(zoom_out_button)

        # Font size slider
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(48)
        self.font_size_slider.setValue(self.text_font.pointSize())
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        layout.addWidget(self.font_size_slider)

        # Set up the menu bar
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        file_menu.addAction("Open", lambda: self.load_new_file())
        file_menu.addAction("Save", lambda: save_changes(self.text_area))

        export_menu = QMenu("Export", self)
        file_menu.addMenu(export_menu)
        export_menu.addAction("Export as JSON", lambda: export_data(self.text_area, "json"))
        export_menu.addAction("Export as MD", lambda: export_data(self.text_area, "md"))
        export_menu.addAction("Export as TXT", lambda: export_data(self.text_area, "txt"))

        file_menu.addAction("Quit", self.close)

        view_menu = QMenu("View", self)
        menu_bar.addMenu(view_menu)
        view_menu.addAction("Zoom In (Ctrl +)", self.zoom_in)
        view_menu.addAction("Zoom Out (Ctrl -)", self.zoom_out)

    def zoom_in(self):
        current_font_size = self.text_font.pointSize()
        self.text_font.setPointSize(current_font_size + 2)
        self.text_area.setFont(self.text_font)
        self.font_size_slider.setValue(current_font_size + 2)

    def zoom_out(self):
        current_font_size = self.text_font.pointSize()
        new_font_size = max(current_font_size - 2, 6)
        self.text_font.setPointSize(new_font_size)
        self.text_area.setFont(self.text_font)
        self.font_size_slider.setValue(new_font_size)

    def update_font_size(self, value):
        self.text_font.setPointSize(value)
        self.text_area.setFont(self.text_font)

    def load_new_file(self):
        json_data, file_path = load_image_data()
        if json_data and file_path:
            self.text_area.setText(json.dumps(json_data, indent=4))


def main():
    app = QApplication(sys.argv)
    json_data, file_path = load_image_data()
    if json_data and file_path:
        editor_window = EditorWindow(json_data, file_path)
        editor_window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
