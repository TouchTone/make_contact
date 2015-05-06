
# GUI for make_contact

import json
import traceback
import time

from PySide.QtCore import *
from PySide.QtGui import *

from PIL import ImageColor

import mc_main

import make_contact
import progressdialog



class MCWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
    
        QMainWindow.__init__(self, *args)        
        
        self.ui = mc_main.Ui_mc_main()
        self.ui.setupUi(self)
    
        self.options = kwargs["options"]

        self.pd = None

        # Set up routes to my methods

        self.ui.fileHeightT.stateChanged.connect(self.ui.fileHeightE.setDisabled)
        self.ui.fileDirT.stateChanged.connect(self.ui.fileDirE.setDisabled)
        self.ui.fileDirE.clicked.connect(self.pickOutDir)

        for wid in [ self.ui.labelSizeE, self.ui.labelColorB ]:
            self.ui.labelEnableC.stateChanged.connect(getattr(wid, "setEnabled"))

        self.ui.titleT.stateChanged.connect(self.ui.titleE.setDisabled)
        for wid in [ self.ui.titleSizeE, self.ui.titleStatsC, self.ui.titleT, self.ui.titleColorB ]:
            self.ui.titleEnableC.stateChanged.connect(getattr(wid, "setEnabled"))

        self.ui.thumbCoverModeC.activated.connect(self.enableCoverE)

        self.ui.fileBackgroundB.clicked.connect(self.pickBackgroundColor)
        self.ui.titleColorB.clicked.connect(self.pickTitleColor)
        self.ui.labelColorB.clicked.connect(self.pickLabelColor)

        self.ui.dirsSubdirImagesB.stateChanged.connect(self.ui.dirsSubdirContactsB.setDisabled)
        self.ui.dirsSubdirContactsB.stateChanged.connect(self.ui.dirsSubdirImagesB.setDisabled)

        self.ui.dirsAddB.clicked.connect(self.addDirs)
        self.ui.runB.clicked.connect(self.run)

        self.ui.actionLoad_Config.triggered.connect(self.loadConfig)
        self.ui.actionSave_Config.triggered.connect(self.saveConfig)

        self.setFromOptions(self.options)
        
            
    def quit(self):        
        qApp.quit()


    def loadConfig(self):
        fileName = QFileDialog.getOpenFileName(self, "Load Config", "", "Config Files (*.conf)")

        if fileName[0] == '':
            return

        fh = open(fileName[0], "r")
        opt = json.load(fh)
        fh.close()

        self.options = opt
        self.setFromOptions(opt)


    def saveConfig(self):
        fileName = QFileDialog.getSaveFileName(self, "Save Config", "", "Config Files (*.conf)")

        if fileName[0] == '':
            return

        fh = open(fileName[0], "w")
        json.dump(self.options, fh, indent=4)
        fh.close()


    def setFromOptions(self, options):

        # Sheet Specs
        self.ui.fileExtE.setText(options['outputtype'])
        if options['outdir'] == "auto":
            self.ui.fileDirE.setText("")
            self.ui.fileDirE.setDisabled(True)
            self.ui.fileDirT.setChecked(True)
        else:
            self.ui.fileDirE.setText(options['outdir'])
            self.ui.fileDirE.setEnabled(True)
            self.ui.fileDirT.setChecked(False)

        self.ui.fileQualE.setText("%d" % options['quality'])
        self.ui.fileWidthE.setText("%d" % options['width'])  
        if options['height'] == -1:
            self.ui.fileHeightE.setText("")
            self.ui.fileHeightT.setChecked(True)
        else:
            self.ui.fileHeightE.setText("%d" % options['height'])
            self.ui.fileHeightT.setChecked(False)       
        self.ui.fileOverwriteC.setCurrentIndex(options['nooverwrite'] != True)
        self.ui.fileOrderC.setCurrentIndex(options['random'] == True)

        # Thumbnail Specs
        if options['title'] == "auto":
            self.ui.fileHeightE.setText("")
            self.ui.fileHeightT.setChecked(True)
        else:
            self.ui.fileHeightE.setText("%d" % options['height'])
            self.ui.fileHeightT.setChecked(False)
        self.ui.thumbHeightE.setText("%d" % options['thumbheight'])
        self.ui.thumbBorderE.setText("%d" % options['border'])
        if options['cover'] == "none":
            self.ui.thumbCoverModeC.setCurrentIndex(0)
            self.ui.thumbCoverE.setText("")
            self.ui.thumbCoverE.setEnabled(False)
        elif options['cover'] == "auto":
            self.ui.thumbCoverModeC.setCurrentIndex(1)
            self.ui.thumbCoverE.setText("")
            self.ui.thumbCoverE.setEnabled(False)
        else:
            self.ui.thumbCoverModeC.setCurrentIndex(2)
            self.ui.thumbCoverE.setText(options['cover'])
            self.ui.thumbCoverE.setEnabled(True)
        if options['coverscale'] == 0:
            self.ui.thumbCoverScaleS.setCurrentIndex(self.ui.thumbCoverScaleS.count() - 1)
        else:
            self.ui.thumbCoverScaleS.setCurrentIndex(options['coverscale'] - 1)

        # Title Specs
        self.ui.titleEnableC.setChecked(options['title'] != "none")
        if options['title'] == "auto":
            self.ui.titleE.setText("")
            self.ui.fileHeightT.setChecked(True)
        else:
            self.ui.titleE.setText(options['title'])
            self.ui.fileHeightT.setChecked(False)
        self.ui.titleSizeE.setText("%d" % options['fontsize'])
        self.ui.titleStatsC.setCurrentIndex(options['tstats'] != False)

        # Label Specs
        self.ui.labelEnableC.setChecked(options['labels'])
        self.ui.labelSizeE.setText("%d" % options['labelsize'])

        # Color Selections
        for opt, wid in [(options['background'], self.ui.fileBackgroundB), (options['titlecolor'], self.ui.titleColorB), (options["labelcolor"], self.ui.labelColorB)]:
            rgb = ImageColor.getrgb(opt)
            col = QColor(rgb[0], rgb[1], rgb[2])
            wid.setStyleSheet("background-color: %s" % col.name());

        # Dirs list
        if options["folders"]:
            for d in options["folders"]:
                self.ui.dirsL.addItem(d)

        self.ui.dirsSubdirContactsB.setChecked(options["subdircontacts"])
        self.ui.dirsSubdirImagesB.setChecked(options["recursive"])
        self.ui.dirsArchivesB.setChecked(options["archives"])


    def setOptions(self):

        try:
            var = "Border Width"
            self.options['border'] = int(self.ui.thumbBorderE.text())
            var = "Cover Mode"
            if self.ui.thumbCoverModeC.currentIndex() == 0:
                self.options['cover'] = "none"
            elif self.ui.thumbCoverModeC.currentIndex() == 1:
                self.options['cover'] = "auto"
            else:
                self.options['cover'] = self.ui.thumbCoverE.text()
            var = "Cover Scale"
            if self.ui.thumbCoverScaleS.currentIndex() == self.ui.thumbCoverScaleS.count() - 1:
                self.options['coverscale'] = 0
            else:
                self.options['coverscale'] = int(self.ui.thumbCoverScaleS.currentIndex() + 1)
            var = "Font Size"
            self.options['fontsize'] = int(self.ui.titleSizeE.text())
            var = "Sheet Height"
            if self.ui.fileHeightT.isChecked():
                self.options['height'] = -1
            else:
                self.options['height'] = int(self.ui.fileHeightE.text())
            var = "Label Enable"
            self.options['labels'] = self.ui.fileHeightT.isChecked()
            var = "Label Size"
            self.options['labelsize'] = int(self.ui.labelSizeE.text())
            var = "Overwrite"
            self.options['nooverwrite'] = self.ui.fileOverwriteC.currentIndex() == 0
            var = "File Type"
            self.options['outputtype'] = self.ui.fileExtE.text()
            var = "Output Directory"
            self.options['outdir'] = self.ui.fileDirE.text()
            var = "Quality"
            self.options['quality'] = int(self.ui.fileQualE.text())
            var = "Image Order"
            self.options['random'] = self.ui.fileOrderC.currentIndex() == 1
            var = "Thumb Height"
            self.options['thumbheight'] = int(self.ui.thumbHeightE.text())
            var = "Title Enable"
            if self.ui.titleEnableC.isChecked():
                if self.ui.titleT.isChecked():
                    self.options['title'] = "auto"
                else:
                    self.options['title'] = self.ui.titleE.text()
            else:
                self.options['title'] = "none"
            var = "Title Stats"
            self.options['tstats'] = self.ui.titleStatsC.currentIndex() == 1
            var = "Sheet Width"
            self.options['width'] = int(self.ui.fileWidthE.text())
            var = "Subdir Contacts"
            self.options['subdircontacts'] = self.ui.dirsSubdirContactsB.isChecked()
            var = "Subdir Images"
            self.options['recursive'] = self.ui.dirsSubdirImagesB.isChecked()
            var = "Archives"
            self.options['archives'] = self.ui.dirsArchivesB.isChecked()

        except Exception, e:
            print "Caught %s setting %s, please correct" % (e, var)


    def enableCoverE(self):
        if self.ui.thumbCoverModeC.currentIndex() != 2:
            self.ui.thumbCoverE.setEnabled(False)
        else:
            self.ui.thumbCoverE.setEnabled(True)


    def pickBackgroundColor(self):
        rgb = ImageColor.getrgb(self.options['background'])       
        col = QColorDialog(QColor(rgb[0], rgb[1], rgb[2]) ).getColor()
        self.options['background'] = col.name()
        self.ui.fileBackgroundB.setStyleSheet("background-color: %s" % col.name());

  
    def pickTitleColor(self):
        rgb = ImageColor.getrgb(self.options['titlecolor'])        
        col = QColorDialog(QColor(rgb[0], rgb[1], rgb[2]) ).getColor()
        self.options['titlecolor'] = col.name()
        self.ui.titleColorB.setStyleSheet("background-color: %s" % col.name());


    def pickLabelColor(self):
        rgb = ImageColor.getrgb(self.options['labelcolor'])
        col = QColorDialog(QColor(rgb[0], rgb[1], rgb[2]) ).getColor()
        self.options['labelcolor'] = col.name()
        self.ui.labelColorB.setStyleSheet("background-color: %s" % col.name());


    def pickOutDir(self):
        dia = QFileDialog()
        dia.setFileMode(QFileDialog.DirectoryOnly)
        dia.setViewMode(QFileDialog.List)
        dia.setOption(QFileDialog.ShowDirsOnly, True)

        if dia.exec_():
            self.options["outdir"] = dia.selectedFiles()[0]
            self.ui.fileDirE.setText(dia.selectedFiles()[0])


    def dropDirs(self, event):
        print "dropDirs:",event


    def addDirs(self):
        dia = QFileDialog()
        dia.setViewMode(QFileDialog.List)
        if not self.ui.dirsArchivesB.isChecked():
            dia.setFileMode(QFileDialog.DirectoryOnly)
            dia.setOption(QFileDialog.ShowDirsOnly, True)
        else:
            dia.setFileMode(QFileDialog.ExistingFiles)
            dia.setNameFilter("Archives (*.zip *.ZIP *.rar *.RAR *.7z *.7Z)")       

        # Hack to allow multi-selection (http://stackoverflow.com/questions/28544425/pyqt-qfiledialog-multiple-directory-selection)
        dia.setOption(QFileDialog.DontUseNativeDialog, True)
        for view in dia.findChildren(QListView) + dia.findChildren(QTreeView):
            if isinstance(view.model(), QFileSystemModel):
                view.setSelectionMode(QAbstractItemView.MultiSelection)

        if dia.exec_():
            newDirs = dia.selectedFiles()

            for d in newDirs:
                self.ui.dirsL.addItem(d)


    def progress(self, layout, compose):
        #print "Progress:",layout,compose

        self.pd.layoutBar.setValue(layout * 100)
        self.pd.composeBar.setValue(compose * 100)

        QCoreApplication.processEvents()

        return self.abort


    def abortButton(self):
        self.pd.logT.insertPlainText("\nAborted...")
        self.abort = True


    def logpipe(self, level, msg):
        if self.pd is None:
            return

        if level > make_contact.LogLevels.INFO:
            return

        self.pd.logT.insertPlainText(msg)


    def run(self):
        self.setOptions()

        pdia = QDialog()
        pd = progressdialog.Ui_ProgressDialog()
        pd.setupUi(pdia)
        pd.abortB.clicked.connect(self.abortButton)
        pdia.show()

        self.pd = pd
        self.abort = False

        start = time.time()
        
        for i in xrange(self.ui.dirsL.count()):
            d = self.ui.dirsL.item(i)
            ## print i,d.text(), self.options

            pd.label.setText("Processing %s..." % d.text())
            pd.dirsBar.setValue((i + 1) * 100. / float(self.ui.dirsL.count()))

            try:
                make_contact.processFolder(self.options, d.text(), progress=self.progress)
            except make_contact.AbortException,e:
                break
            except Exception,e:
                print traceback.format_exc()
                break

        end = time.time()
        if not self.abort:
            pd.logT.insertPlainText("All done, took %.2f secs." % (end-start))

        pd.abortB.setText("Close")
        pd.abortB.clicked.connect(pdia.close)
        pdia.exec_()

        self.pd = None



def run(options):

    global qapp    
    qapp = QApplication([])

    win = MCWindow(options = options)

    make_contact.logpipe = win.logpipe

    QObject.connect(qapp, SIGNAL("lastWindowClosed()"), win, SLOT("quit()"))

    win.show()
    
    qapp.exec_()

