#!/usr/bin/env python

# This is only needed for Python v2 but is harmless for Python v3.
import sip, struct, sys, codecs, os, zipfile, binascii
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui


def module_path():
    """This will get us the program's directory, even if we are frozen using py2exe"""
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None


def GetIcon(name):
    """Helper function to grab a specific icon"""
    return QtGui.QIcon('bobdata/icon_%s.png' % name)


class Window(QtGui.QMainWindow):
    """Main Window"""
    
    def CreateAction(self, shortname, function, icon, text, statustext, shortcut, toggle=False):
        """Helper function to create an action"""
        
        if icon != None:
            act = QtGui.QAction(icon, text, self)
        else:
            act = QtGui.QAction(text, self)
        
        if shortcut != None: act.setShortcut(shortcut)
        if statustext != None: act.setStatusTip(statustext)
        if toggle:
            act.setCheckable(True)
        act.triggered.connect(function)
        
        self.actions[shortname] = act

    def __init__(self):
        QtGui.QMainWindow.__init__(self, None)
        #super(Window, self).__init__()
        self.savename = ''

        # create the actions
        self.actions = {}
        self.CreateAction('open', self.HandleOpen, GetIcon('open'), 'Open...', 'Open a script file', QtGui.QKeySequence.Open)
        self.CreateAction('save', self.HandleSave, GetIcon('save'), 'Save', 'Save a script file', QtGui.QKeySequence.Save)
        self.CreateAction('saveas', self.HandleSaveAs, GetIcon('saveas'), 'Save as...', 'Save a copy of the script file', QtGui.QKeySequence.SaveAs)
        self.CreateAction('import', self.HandleImport, None, 'Import', 'Import a txt to the current displayed script', QtGui.QKeySequence('Ctrl+I'))
        self.CreateAction('export', self.HandleExport, None, 'Export', 'Export a txt from the current displayed script', QtGui.QKeySequence('Ctrl+E'))

        # create a menubar        
        self.fileMenu = QtGui.QMenu("&File", self)
        self.fileMenu.addAction(self.actions['open'])
        self.fileMenu.addAction(self.actions['save'])
        self.fileMenu.addAction(self.actions['saveas'])
        self.fileMenu.addAction(self.actions['import'])
        self.fileMenu.addAction(self.actions['export'])
        self.menuBar().addMenu(self.fileMenu)


        self.proxyModel = QtGui.QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)

        self.ScriptBox = QtGui.QGroupBox("Script")
        self.FilterBox = QtGui.QGroupBox("Filter Modes")

        self.proxyView = QtGui.QTreeView()
        self.proxyView.setRootIsDecorated(False)
        self.proxyView.setAlternatingRowColors(True)
        self.proxyView.setModel(self.proxyModel)
        self.proxyView.setSortingEnabled(True)

        self.sortCaseSensitivityCheckBox = QtGui.QCheckBox("Case sensitive sorting")
        self.filterCaseSensitivityCheckBox = QtGui.QCheckBox("Case sensitive filter")

        self.filterPatternLineEdit = QtGui.QLineEdit()
        self.filterPatternLabel = QtGui.QLabel("&Filter pattern:")
        self.filterPatternLabel.setBuddy(self.filterPatternLineEdit)

        self.filterSyntaxComboBox = QtGui.QComboBox()
        self.filterSyntaxComboBox.addItem("Regular expression",QtCore.QRegExp.RegExp)
        self.filterSyntaxComboBox.addItem("Wildcard", QtCore.QRegExp.Wildcard)
        self.filterSyntaxComboBox.addItem("Fixed string", QtCore.QRegExp.FixedString)
        self.filterSyntaxLabel = QtGui.QLabel("Filter &syntax:")
        self.filterSyntaxLabel.setBuddy(self.filterSyntaxComboBox)

        self.filterColumnComboBox = QtGui.QComboBox()
        self.filterColumnComboBox.addItem("ID")
        self.filterColumnComboBox.addItem("Japanese")
        self.filterColumnComboBox.addItem("English")
        self.filterColumnLabel = QtGui.QLabel("Filter &column:")
        self.filterColumnLabel.setBuddy(self.filterColumnComboBox)

        self.filterScriptFile = QtGui.QComboBox()
        self.filterScriptLabel = QtGui.QLabel("Script File:")
        self.filterScriptLabel.setBuddy(self.filterScriptFile)

        self.filterPatternLineEdit.textChanged.connect(self.filterRegExpChanged)
        self.filterSyntaxComboBox.currentIndexChanged.connect(self.filterRegExpChanged)
        self.filterScriptFile.currentIndexChanged.connect(self.filterScriptChanged)
        self.filterCaseSensitivityCheckBox.toggled.connect(self.filterRegExpChanged)
        self.sortCaseSensitivityCheckBox.toggled.connect(self.sortChanged)
        self.filterColumnComboBox.currentIndexChanged.connect(self.filterColumnChanged)

        sourceLayout = QtGui.QHBoxLayout()
        sourceLayout.addWidget(self.proxyView)
        self.ScriptBox.setLayout(sourceLayout)

        proxyLayout = QtGui.QGridLayout()
        proxyLayout.addWidget(self.filterPatternLabel, 0, 0)
        proxyLayout.addWidget(self.filterPatternLineEdit, 0, 1, 1, 2)
        proxyLayout.addWidget(self.filterSyntaxLabel, 1, 0)
        proxyLayout.addWidget(self.filterSyntaxComboBox, 1, 1, 1, 2)
        proxyLayout.addWidget(self.filterScriptLabel, 2, 0)
        proxyLayout.addWidget(self.filterScriptFile, 2, 1, 1, 2)
        proxyLayout.addWidget(self.filterColumnLabel, 3, 0)
        proxyLayout.addWidget(self.filterColumnComboBox, 3, 1, 1, 2)
        proxyLayout.addWidget(self.filterCaseSensitivityCheckBox, 4, 0, 1, 2)
        proxyLayout.addWidget(self.sortCaseSensitivityCheckBox, 4, 2)
        self.FilterBox.setLayout(proxyLayout)

        centralWidget = QtGui.QWidget()
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.ScriptBox)
        mainLayout.addWidget(self.FilterBox)
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        self.setWindowTitle('Blood of Bahamut Script Editor')
        self.setWindowIcon(QtGui.QIcon('bobdata/icon.png'))
        self.resize(800, 600)

        self.proxyView.sortByColumn(0, QtCore.Qt.AscendingOrder)

        self.filterPatternLineEdit.setText("")
        self.filterCaseSensitivityCheckBox.setChecked(True)
        self.sortCaseSensitivityCheckBox.setChecked(True)


    def filterColumnChanged(self):
        self.proxyModel.setFilterKeyColumn(self.filterColumnComboBox.currentIndex())        
        
    def setSourceModel(self, model):
        self.proxyModel.setSourceModel(model)

    def filterRegExpChanged(self):
        syntax_nr = self.filterSyntaxComboBox.itemData(self.filterSyntaxComboBox.currentIndex())
        syntax = QtCore.QRegExp.PatternSyntax(syntax_nr)

        if self.filterCaseSensitivityCheckBox.isChecked():
            caseSensitivity = QtCore.Qt.CaseSensitive
        else:
            caseSensitivity = QtCore.Qt.CaseInsensitive

        regExp = QtCore.QRegExp(self.filterPatternLineEdit.text(),
                caseSensitivity, syntax)
        self.proxyModel.setFilterRegExp(regExp)

    def filterScriptChanged(self):
        if self.filterScriptFile.currentIndex() == 0:
            window.setSourceModel(window.ability)             
        elif self.filterScriptFile.currentIndex() == 1:
            window.setSourceModel(window.beast)             
        elif self.filterScriptFile.currentIndex() == 2:
            window.setSourceModel(window.chara)             
        elif self.filterScriptFile.currentIndex() == 3:
            window.setSourceModel(window.general)             
        elif self.filterScriptFile.currentIndex() == 4:
            window.setSourceModel(window.honor)
        elif self.filterScriptFile.currentIndex() == 5:
            window.setSourceModel(window.input)
        elif self.filterScriptFile.currentIndex() == 6:
            window.setSourceModel(window.item)
        elif self.filterScriptFile.currentIndex() == 7:
            window.setSourceModel(window.log)
        elif self.filterScriptFile.currentIndex() == 8:
            window.setSourceModel(window.lot)
        elif self.filterScriptFile.currentIndex() == 9:
            window.setSourceModel(window.menu)
        elif self.filterScriptFile.currentIndex() == 10:
            window.setSourceModel(window.quest)
        elif self.filterScriptFile.currentIndex() == 11:
            window.setSourceModel(window.tutorial)
        elif self.filterScriptFile.currentIndex() == 12:
            window.setSourceModel(window.unlock)
        elif self.filterScriptFile.currentIndex() == 13:
            window.setSourceModel(window.win)

    def sortChanged(self):
        if self.sortCaseSensitivityCheckBox.isChecked():
            caseSensitivity = QtCore.Qt.CaseSensitive
        else:
            caseSensitivity = QtCore.Qt.CaseInsensitive

        self.proxyModel.setSortCaseSensitivity(caseSensitivity)


    def HandleImport(self):
        """Import a txt"""
         
        # File Dialog        
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Choose a script file', '', 'Plain Text File (*.txt);;All Files(*)')
        if fn == '': return
        fn = str(fn)
        
        self.proxyView.sortByColumn(0, QtCore.Qt.AscendingOrder)

        f = open(fn, 'rb')
        lineslist = f.readlines()
                
        x = 0
        for line in lineslist:
            self.proxyModel.setData(self.proxyModel.index(x, 2), unicode(line.decode('utf-8', 'replace').strip()))
            x += 1
        
   
    def HandleExport(self):
        """Export a txt"""
        
        # File Dialog
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', 'Plain Text File (*.txt);;All Files(*)')
        if fn == '': return
        fn = str(fn)
        
        newfile = open(fn, 'wb')
        
        self.proxyView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        
        for x in xrange(self.proxyModel.rowCount()):
            writestr = unicode(self.proxyModel.data(self.proxyModel.index(x,2))).encode('utf-8', 'replace') + '\n'
            newfile.write(writestr)
    
    

    def HandleOpen(self):
        """Open a level using the filename"""

        # File Dialog        
        fn = QtGui.QFileDialog.getOpenFileName(self, 'Choose a script file', '', 'Script archives (*.zip);;All Files(*)')
        if fn == '': return
        fn = str(fn)
        i = 0

        # Set up lists
        fileout = ['ability','beast','chara','general','honor','input','item','log','lot','menu','quest','tutorial','unlock','win']
        fileoutvars = [window.ability,window.beast,window.chara,window.general,window.honor,window.input,window.item,window.log,window.lot,window.menu,window.quest,window.tutorial,window.unlock,window.win]

        self.proxyView.sortByColumn(0, QtCore.Qt.AscendingOrder)


        # Open Files from zip
        zf = zipfile.ZipFile(fn)
        
        
        # loop through zip contents
        for filename in fileout:
            try:
                tmpf = zf.read('txt_' + filename + '.dtx')
            except KeyError:
                print 'ERROR: Did not find %s in zip file' % filename
            
            
            print filename
#            print i
            
            buffer = 0
            offset = 8
            
            sizeStr = struct.unpack_from('<II', tmpf, 0)
            idStruct = struct.Struct('<IcHx')
            lenStruct = struct.Struct('<I')
        
            lengths = []
        
            for x in xrange(int(sizeStr[0])):
                data = idStruct.unpack_from(tmpf,offset)
                #print data
                offset += 8
                
            for x in xrange(int(sizeStr[1])):
                data = lenStruct.unpack_from(tmpf,offset)
                lengths.append(data[0])
                offset += 4
            
            lengths.append(len(tmpf)-offset) 
            #print lengths
         
            codecs.register_error("c.replace", error_handler)
            
            for x in xrange(int(sizeStr[1])):
                data = struct.unpack_from('{0}s'.format(lengths[x+1]-lengths[x]),tmpf,offset+lengths[x])
                
                pnew = controlCharsIn(data[0])
                p = unicode(pnew.decode('shift_jisx0213', 'c.replace'))
                #print p
                
                fileoutvars[i].setData(fileoutvars[i].index(x, 2), p)
            
            i = i + 1
            
        zf.close()
        window.savename = fn
    

    def HandleSave(self):
        """Save a level back to the archive"""
        if not window.savename:
            window.HandleSaveAs()
            return
        
        window.Saving(window.savename)
   
        
    def HandleSaveAs(self):
        """Pack up the level files using the translations if available"""
        fn = QtGui.QFileDialog.getSaveFileName(self, 'Choose a new filename', '', 'Script archives (*.zip);;All Files(*)')
        if fn == '': return
        fn = str(fn)
        window.Saving(fn)
        
        window.savename = fn


    def Saving(parent, fn):
        fileout = ['ability','beast','chara','general','honor','input','item','log','lot','menu','quest','tutorial','unlock','win']
        fileoutvars = [window.ability,window.beast,window.chara,window.general,window.honor,window.input,window.item,window.log,window.lot,window.menu,window.quest,window.tutorial,window.unlock,window.win]

        window.proxyView.sortByColumn(0, QtCore.Qt.AscendingOrder)
        print 'creating archive'
        zf = zipfile.ZipFile(fn, mode='w')

        i=0
        for filename in fileout:
            with open('bobdata/txt_' + filename + '.dtx', 'rb') as f:
                tmpf = f.read()
                sizeStr = struct.unpack_from('<II', tmpf, 0)
                #keep the header data I don't know what to do with yet
#                print ((sizeStr[0]*8)+8)
                keepdata = tmpf[0:(((sizeStr[0]*8)+8))]
            f.close()        
            
            # generate valid SJIS strings
            stringlist = []
            for x in xrange(fileoutvars[i].rowCount()):
                if fileoutvars[i].data(fileoutvars[i].index(x,2)) == '':
                    str = unicode(fileoutvars[i].data(fileoutvars[i].index(x,1))).encode('sjis', 'ignore')
                    newstr = controlCharsOut(str)
                    stringlist.append(newstr)
#                    print newstr
                else:
                    str = unicode(fileoutvars[i].data(fileoutvars[i].index(x,2))).encode('sjis', 'ignore')
                    if str.endswith('\x00\x00') != True:
                        str = str + '\x00\x00'
                    newstr = controlCharsOut(str)
                    stringlist.append(newstr)
#                    print newstr
                    
            
#            print stringlist
            # Generate the length table
            length = 0
            newlenlist = []
            for x in stringlist:
                newlenlist.append(struct.pack('<I', length))
                length += len(x)
                                
            # Generate the concatenated strings
            newlendata = "".join(["%s" % (k) for k in newlenlist])
            stringdata = "".join(["%s" % (k) for k in stringlist])

#            print keepdata
#            print unicode('newlen: ' + newlendata)
#            print unicode('stringdata: ' + stringdata)
            
            
            zf.writestr('txt_' + filename + '.dtx', keepdata + newlendata + stringdata)
            
            i += 1


charMappings = dict([('\xff\x21', '\x81\xf7'), #newline
                ('\xff\x1f', '\x81\x99'),
                ('\xff\x11', '\x81\x9a'),
                ('\xff\x30', '\x81\x9b'),
                ('\xff\x53', '\x81\x9c'),
                ('\xff\x54', '\x81\x9d'),
                ('\xff\x55', '\x81\x9e'),
                ('\xff\x56', '\x81\x9f'),
                ('\xff\x57', '\x81\xa0'),
                ('\xff\x58', '\x81\xa1'),
                ('\xff\x16', '\x81\xa2'),
                ('\xff\x17', '\x81\xa3'),
                ('\xff\x20', '\x81\xa4')
                ])
                                
def controlCharsOut(string):
    for a, b in charMappings.iteritems():
        string = string.replace(b, a)
    return string

def controlCharsIn(string):
    for a, b in charMappings.iteritems():
        string = string.replace(a, b)
    return string


def addScriptMatch(model, colA, colB, colC):
    model.insertRow(0)
    model.setData(model.index(0, 0), colA)
    model.setData(model.index(0, 1), colB)
    model.setData(model.index(0, 2), colC)


def createDefaultModels(parent):
    window.ability = createScriptModel(parent, 'bobdata/txt_ability.dtx')
    window.filterScriptFile.addItem("Abilities")
    window.beast = createScriptModel(parent, 'bobdata/txt_beast.dtx')
    window.filterScriptFile.addItem("Beasts")
    window.chara = createScriptModel(parent, 'bobdata/txt_chara.dtx')
    window.filterScriptFile.addItem("Characters")
    window.general = createScriptModel(parent, 'bobdata/txt_general.dtx')
    window.filterScriptFile.addItem("General")
    window.honor = createScriptModel(parent, 'bobdata/txt_honor.dtx')
    window.filterScriptFile.addItem("Honours")
    window.input = createScriptModel(parent, 'bobdata/txt_input.dtx')
    window.filterScriptFile.addItem("Input")
    window.item = createScriptModel(parent, 'bobdata/txt_item.dtx')
    window.filterScriptFile.addItem("Items")
    window.log = createScriptModel(parent, 'bobdata/txt_log.dtx')
    window.filterScriptFile.addItem("Logs")
    window.lot = createScriptModel(parent, 'bobdata/txt_lot.dtx')
    window.filterScriptFile.addItem("Lot")
    window.menu = createScriptModel(parent, 'bobdata/txt_menu.dtx')
    window.filterScriptFile.addItem("Menus")
    window.quest = createScriptModel(parent, 'bobdata/txt_quest.dtx')
    window.filterScriptFile.addItem("Quests")
    window.tutorial = createScriptModel(parent, 'bobdata/txt_tutorial.dtx')
    window.filterScriptFile.addItem("Tutorials")
    window.unlock = createScriptModel(parent, 'bobdata/txt_unlock.dtx')
    window.filterScriptFile.addItem("Unlock")
    window.win = createScriptModel(parent, 'bobdata/txt_win.dtx')
    window.filterScriptFile.addItem("Victory")
    
    window.setSourceModel(window.ability) 


def error_handler(exc):
    if not isinstance(exc, UnicodeDecodeError):
        raise TypeError("Sorry, don't know how to handle %r" % exc)
    print exc
    print exc.start
    print exc.end
    print unicode(exc.object, 'sjis', 'replace')
    l = [u"%s" % hex(ord(exc.object[pos])) for pos in xrange(exc.start, exc.end)]
    return (u"%s" % u"".join(l), exc.end+1) # skip one character
        

def createScriptModel(parent, filename):
    model = QtGui.QStandardItemModel(0, 3, parent)

    model.setHeaderData(0, QtCore.Qt.Horizontal, "ID")
    model.setHeaderData(1, QtCore.Qt.Horizontal, "Japanese")
    model.setHeaderData(2, QtCore.Qt.Horizontal, "English")
    

    print filename

    with open(filename, 'rb') as f:
        tmpf = f.read()
    f.close()
    
    buffer = 0
    offset = 8
    
    sizeStr = struct.unpack_from('<II', tmpf, 0)
    idStruct = struct.Struct('<IcHx')
    lenStruct = struct.Struct('<I')

    lengths = []

    for x in xrange(int(sizeStr[0])):
        data = idStruct.unpack_from(tmpf,offset)
        #print data
        offset += 8
        
    for x in xrange(int(sizeStr[1])):
        data = lenStruct.unpack_from(tmpf,offset)
        lengths.append(data[0])
        offset += 4
    
    lengths.append(len(tmpf)-offset) 
    #print lengths
 
    codecs.register_error("c.replace", error_handler)
    
    for x in xrange(int(sizeStr[1])):
        data = struct.unpack_from('{0}s'.format(lengths[x+1]-lengths[x]),tmpf,offset+lengths[x])
        
        pnew = controlCharsIn(data[0])
        p = unicode(pnew.decode('shift_jisx0213', 'c.replace'))
        #print p
        
        model.appendRow([QtGui.QStandardItem(str(x).zfill(4)), QtGui.QStandardItem(p), QtGui.QStandardItem('')])

    return model


if __name__ == '__main__':

    path = module_path()
    if path != None:
        os.chdir(module_path())


    app = QtGui.QApplication(sys.argv)
    window = Window()
    createDefaultModels(window)
    window.show()
    sys.exit(app.exec_())
