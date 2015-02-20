
# Helper widget to manage directory list

from PySide.QtCore import *
from PySide.QtGui import *

class DirsList(QListWidget):

    def __init__(self, parent):
        super(DirsList, self).__init__(parent)

        self.initUI()

    def initUI(self):

        del_one = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.connect(del_one, SIGNAL('activated()'), self.delDirs)


    def delDirs(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))


    # DnD Handling from http://stackoverflow.com/questions/4151637/pyqt4-drag-and-drop-files-into-qlistwidget

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                self.addItem(str(url.toLocalFile()))
        else:
            event.ignore()