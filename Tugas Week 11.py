import sys
import sqlite3
import csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

DB_BUKU = 'books.db'

class EditDialog(QDialog):
    def __init__(self, field_name, current_value):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(f"Edit {field_name}")
        self.setFixedSize(320, 150)

        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.input = QLineEdit(current_value)
        self.input.setStyleSheet("padding: 6px; font-size: 14px;")
        form_layout.addRow(QLabel(f"{field_name}:"), self.input)

        layout.addLayout(form_layout)
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: green; color: white; font-weight: bold")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_value(self):
        return self.input.text()

class BookManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manajemen Buku")
        self.resize(900, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.initUI()
        self.initDB()
        self.loadData()
        self.initStatusBar()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.initMenuBar()
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setAlignment(Qt.AlignCenter)

        self.data_btn = QPushButton("Data Buku")
        self.export_btn = QPushButton("Ekspor")
        for btn in [self.data_btn, self.export_btn]:
            btn.setFixedWidth(100)
            btn.setCheckable(True)
            btn.clicked.connect(self.switchTab)
        self.data_btn.setChecked(True)
        self.updateTabStyles()

        self.tab_layout.addWidget(self.data_btn)
        self.tab_layout.addWidget(self.export_btn)
        self.main_layout.addLayout(self.tab_layout)

        self.stacked_layout = QStackedLayout()
        self.data_widget = QWidget()
        data_layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_widget = QWidget()
        form_widget.setFixedWidth(300)

        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.year_input = QLineEdit()
        for input_field in [self.title_input, self.author_input, self.year_input]:
            input_field.setFixedWidth(200)

        form_layout.addRow("Judul:", self.title_input)
        form_layout.addRow("Pengarang:", self.author_input)
        form_layout.addRow("Tahun:", self.year_input)
        form_widget.setLayout(form_layout)

        simpan_btn = QPushButton("Simpan")
        simpan_btn.setFixedWidth(100)
        simpan_btn.clicked.connect(self.saveData)

        salin_btn = QPushButton("Salin")
        salin_btn.setFixedWidth(100)
        salin_btn.clicked.connect(self.copyToClipboard)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(simpan_btn)
        btn_layout.addWidget(salin_btn)

        form_container = QWidget()
        form_container_layout = QVBoxLayout()
        form_container_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        form_container_layout.addWidget(form_widget)
        form_container_layout.addLayout(btn_layout)
        form_container.setLayout(form_container_layout)
        data_layout.addWidget(form_container)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari judul ...")
        self.search_input.setStyleSheet("font-size: 14px; padding: 6px; font-weight: bold;")
        self.search_input.textChanged.connect(self.searchData)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Pengarang", "Tahun"])
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.editCell)
        self.table.setStyleSheet("""
            QHeaderView::section {
                font-weight: bold;
                border: 1px solid black;
            }
            QTableWidget::item {
                border: 1px solid gray;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #a8d5ff;
                color: black;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.delete_btn = QPushButton("Hapus Data")
        self.delete_btn.setStyleSheet("background-color: orange")
        self.delete_btn.setFixedWidth(120)
        self.delete_btn.clicked.connect(self.deleteData)

        data_layout.addWidget(self.search_input)
        data_layout.addWidget(self.table)
        data_layout.addWidget(self.delete_btn, alignment=Qt.AlignLeft)

        self.data_widget.setLayout(data_layout)

        self.export_widget = QWidget()
        export_layout = QVBoxLayout()
        export_layout.setAlignment(Qt.AlignCenter)
        export_btn = QPushButton("Ekspor ke CSV")
        export_btn.setFixedWidth(150)
        export_btn.clicked.connect(self.showExportDialog)
        export_layout.addWidget(export_btn)
        self.export_widget.setLayout(export_layout)

        self.stacked_layout.addWidget(self.data_widget)
        self.stacked_layout.addWidget(self.export_widget)

        self.main_layout.addLayout(self.stacked_layout)
        self.central_widget.setLayout(self.main_layout)

    def copyToClipboard(self):
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        year = self.year_input.text().strip()

        if not title and not author and not year:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data buku yang disalin !")
            return

        text_to_copy = f"Judul: {title}\nPengarang: {author}\nTahun: {year}"

        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)
        QMessageBox.information(self, "Sukses", "Data buku berhasil disalin ke clipboard !")

    def initMenuBar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Simpan", self.saveData)
        file_menu.addAction("Ekspor ke CSV", self.showExportDialog)
        file_menu.addAction("Keluar", self.close)

        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction("Cari Judul", lambda: self.search_input.setFocus())
        edit_menu.addAction("Hapus Data", self.deleteData)
        edit_menu.addAction("AutoFill")
        edit_menu.addAction("Start Dictation...")
        edit_menu.addAction("Emoji & Symbols")

        tutorial_menu = menu_bar.addMenu("Tutorial")
        tutorial_menu.addAction("Tampilkan tutorial", self.showTutorialDock)

    def initStatusBar(self):
        status_bar = self.statusBar()
        self.status_label = QLabel("MUHAMMAD FIQRI JORDY ARDIANTO | F1D022145")
        self.status_label.setStyleSheet("font-weight: bold; color:#4DA8DA ; font-family: Robotto; font-size: 16px;")
        status_bar.addPermanentWidget(self.status_label)

    def showTutorialDock(self):
        dock = QDockWidget("Tutorial Penggunaan Aplikasi", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        tutorial_text = QTextEdit()
        tutorial_text.setReadOnly(True)
        tutorial_text.setPlainText("""
1. Masukkan data buku berupa judul, pengarang, tahun terbit buku.
2. Klik tombol "Simpan" untuk menyimpan data buku yang seblumnya telah diisi.
3. Gunakan kotak pencarian untuk mencari buku berdasarkan judul.
4. Klik dua kali pada baris tabel untuk mengedit isinya.
5. Pilih baris pada tabel kemudian klik "Hapus Data" untuk menghapus buku yang dipilih.
6. Gunakan tab "Ekspor" untuk menyimpan data ke file CSV.
        """)
        dock.setWidget(tutorial_text)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def updateTabStyles(self):
        self.data_btn.setStyleSheet("background-color: green; color: white;" if self.data_btn.isChecked() else "")
        self.export_btn.setStyleSheet("background-color: green; color: white;" if self.export_btn.isChecked() else "")

    def switchTab(self):
        if self.sender() == self.data_btn:
            self.data_btn.setChecked(True)
            self.export_btn.setChecked(False)
            self.stacked_layout.setCurrentIndex(0)
        else:
            self.data_btn.setChecked(False)
            self.export_btn.setChecked(True)
            self.stacked_layout.setCurrentIndex(1)
        self.updateTabStyles()

    def initDB(self):
        conn = sqlite3.connect(DB_BUKU)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS books (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        author TEXT NOT NULL,
                        year TEXT NOT NULL
                    )''')
        conn.commit()
        conn.close()

    def loadData(self):
        self.table.setRowCount(0)
        conn = sqlite3.connect(DB_BUKU)
        c = conn.cursor()
        rows = c.execute("SELECT * FROM books").fetchall()
        conn.close()

        if not rows:
            return

        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))

    def saveData(self):
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        year = self.year_input.text().strip()

        if not title or not author or not year:
            QMessageBox.warning(self, "Peringatan", "Lengkapi semua data sebelum menyimpan !")
            return

        conn = sqlite3.connect(DB_BUKU)
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)", (title, author, year))
        conn.commit()
        conn.close()

        self.title_input.clear()
        self.author_input.clear()
        self.year_input.clear()
        self.loadData()

    def deleteData(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Peringatan", "Pilih baris yang ingin dihapus !")
            return

        book_id = self.table.item(selected, 0).text()
        conn = sqlite3.connect(DB_BUKU)
        c = conn.cursor()
        c.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        conn.close()
        self.loadData()

    def editCell(self, row, col):
        if col == 0:
            return

        field_map = {1: "Judul", 2: "Pengarang", 3: "Tahun"}
        column_map = {1: "title", 2: "author", 3: "year"}

        current_value = self.table.item(row, col).text()
        dialog = EditDialog(field_map[col], current_value)
        if dialog.exec_():
            new_value = dialog.get_value()
            book_id = self.table.item(row, 0).text()
            conn = sqlite3.connect(DB_BUKU)
            c = conn.cursor()
            c.execute(f"UPDATE books SET {column_map[col]}=? WHERE id=?", (new_value, book_id))
            conn.commit()
            conn.close()
            self.loadData()

    def searchData(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            self.table.setRowHidden(row, text not in item.text().lower())

    def showExportDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog if sys.platform != 'darwin' else QFileDialog.Options()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan File CSV",
            "",
            "CSV Files (*.csv)",
            options=options
        )

        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            self.exportToCSV(file_path)

    def exportToCSV(self, path):
        with open(path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)
            for row in range(self.table.rowCount()):
                writer.writerow([self.table.item(row, col).text() for col in range(self.table.columnCount())])
        QMessageBox.information(self, "Sukses", "Data berhasil diekspor !")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BookManager()
    window.show()
    sys.exit(app.exec_())
