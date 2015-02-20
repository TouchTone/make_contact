# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'progressdialog.ui'
#
# Created: Fri Feb 20 11:58:05 2015
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ProgressDialog(object):
    def setupUi(self, ProgressDialog):
        ProgressDialog.setObjectName("ProgressDialog")
        ProgressDialog.resize(693, 187)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProgressDialog.sizePolicy().hasHeightForWidth())
        ProgressDialog.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(ProgressDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(ProgressDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(ProgressDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.dirsBar = QtGui.QProgressBar(ProgressDialog)
        self.dirsBar.setProperty("value", 24)
        self.dirsBar.setObjectName("dirsBar")
        self.gridLayout.addWidget(self.dirsBar, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(ProgressDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.layoutBar = QtGui.QProgressBar(ProgressDialog)
        self.layoutBar.setProperty("value", 24)
        self.layoutBar.setObjectName("layoutBar")
        self.gridLayout.addWidget(self.layoutBar, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(ProgressDialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.composeBar = QtGui.QProgressBar(ProgressDialog)
        self.composeBar.setProperty("value", 24)
        self.composeBar.setObjectName("composeBar")
        self.gridLayout.addWidget(self.composeBar, 3, 1, 1, 1)
        self.abortB = QtGui.QPushButton(ProgressDialog)
        self.abortB.setObjectName("abortB")
        self.gridLayout.addWidget(self.abortB, 4, 0, 1, 2)

        self.retranslateUi(ProgressDialog)
        QtCore.QMetaObject.connectSlotsByName(ProgressDialog)

    def retranslateUi(self, ProgressDialog):
        ProgressDialog.setWindowTitle(QtGui.QApplication.translate("ProgressDialog", "Make Contact Sheet Progress", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ProgressDialog", "Contact Sheet Progress...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ProgressDialog", "Directories:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ProgressDialog", "Layout", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("ProgressDialog", "Compose", None, QtGui.QApplication.UnicodeUTF8))
        self.abortB.setText(QtGui.QApplication.translate("ProgressDialog", "Abort", None, QtGui.QApplication.UnicodeUTF8))

