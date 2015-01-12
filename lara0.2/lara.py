#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: LARA_main
# FILENAME: lara.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.2
#
# CREATION_DATE: 2013/04/24
# LASTMODIFICATION_DATE: 2014/02/21
#
# BRIEF_DESCRIPTION: Main GUI classes for LARA
# DETAILED_DESCRIPTION:
#
# ____________________________________________________________________________
#
#   Copyright:
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This file is provided "AS IS" with NO WARRANTY OF ANY KIND,
#   INCLUDING THE WARRANTIES OF DESIGN, MERCHANTABILITY AND FITNESS FOR
#   A PARTICULAR PURPOSE.
#
#   For further Information see COPYING file that comes with this distribution.
#_______________________________________________________________________________

import sys
import pkgutil
import os
import logging
import xml.etree.ElementTree as ET
from PyQt4 import Qt, QtCore, QtGui

import lara_rc
import lara_experiment as la_exp

LARA_version = "v0.2"

#import lara_process as la_proc

class LA_ToolBoxWidget(QtGui.QListWidget):
    """This QListWidget organizes the tool items in the MainToolBox tabwidget
       to be dragged upon the process editor/experiment tab
    """
    def __init__(self, parent=None):
        super(LA_ToolBoxWidget, self).__init__(parent)

        self.setMaximumWidth(120)        
        self.setIconSize(QtCore.QSize(96, 64))
        
        self.setViewMode(QtGui.QListView.IconMode)
        self.setFlow(QtGui.QListView.LeftToRight)
        self.setWrapping(True)
        self.setDragEnabled(True)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)

    def mousePressEvent(self, mouseEvent):
        #debug.logging("toolbox widget mouse press event")
        if (mouseEvent.button() == QtCore.Qt.LeftButton):
            # it is important that this happens only once at the beginning of the drag action
            child = self.itemAt(mouseEvent.pos())
            if not child:
                logging.error("toolbox-widget: no item clicked")
                return
            pixmap = QtGui.QPixmap(child.pixmap())
            
            itemData = QtCore.QByteArray()
            dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
            dataStream.writeQVariant(child.diagramClass())  # relate class with toolbox item
            mimeData = QtCore.QMimeData()
            mimeData.setData('application/lara-dnditemdata', itemData)
            
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
            
            drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction | QtCore.Qt.TargetMoveAction, QtCore.Qt.MoveAction)
       
        super(LA_ToolBoxWidget, self).mousePressEvent(mouseEvent)

class LA_CentralTabWidget(QtGui.QTabWidget):
    """ Container for all process and process info widgets
    """
    def __init__(self, parent):
        super(LA_CentralTabWidget, self).__init__(parent=None)
        
        self.parent = parent
        self.setTabsClosable(True)
        self.setAcceptDrops(True)

    # this is required for the CentralTabWidget to accept drags and drops
    def dragEnterEvent(self, event): 
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            
            if event.source() == self:  # dragging inside the CentralTabWidget
                event.accept()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()
        super(LA_CentralTabWidget, self).dragEnterEvent(event)

    def dropEvent(self, event): 
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
                        
            # triggering new_action to generate a new tab if no tabs present...
            if self.count() == 0:
                self.parent.new_act.trigger()
                event.acceptProposedAction() # changed from event.accept()
            else:
                logging.info("ctw: new experiment existis ")
        else : 
            event.ignore()

class LA_MainWindow(QtGui.QMainWindow):
    """Generating the main application window"""
    
    # this signal is used to set the pointer type (move item, arrow draw) 
    pointerTypeSig = QtCore.pyqtSignal(int)
    editCutSig = QtCore.pyqtSignal()
    unselctAllSig = QtCore.pyqtSignal()
        
    def __init__(self):
        super(LA_MainWindow, self).__init__(parent=None)
        
        self.setWindowTitle("LARA" +  LARA_version )
        
        self.lara_default_working_dir = os.getcwd()
        
        logging.debug("curr wd : %s" %self.lara_default_working_dir)
        
        self.experiments = {}
        self.tool_item_lst = {}     
                
        self.createActions()
        self.createMenus()
        self.createToolbars()
        
        self.createLeftToolTabWidget(self)
        
        self.central_tw = LA_CentralTabWidget(self)
        self.setCentralWidget(self.central_tw)

        self.readLARASettings()

        self.central_tw.tabCloseRequested.connect(self.closeTab)
        self.showMaximized()
        
    def createActions(self):
        self.exit_act = QtGui.QAction(QtGui.QIcon(':/linux/quit'),"E&xit", self, shortcut="Ctrl+X",
                statusTip="Quit LARA", triggered=self.close)                
        self.new_act = QtGui.QAction(QtGui.QIcon(':/linux/new'),"&New Experiment", self, shortcut="Ctrl+N",
                statusTip="New LARA project", triggered=lambda new_lml_filename="": self.new_experiment_action(new_lml_filename="" ) )
        self.open_act = QtGui.QAction(QtGui.QIcon(':/linux/open'),"&Open", self, shortcut="Ctrl+O",
                statusTip="Open LARA project", triggered=self.openExperimentAction)
                
        self.pointerTypeGroup = QtGui.QActionGroup(self, enabled=True) # action group is exclusive by default
        self.move_item_act = QtGui.QAction(QtGui.QIcon(':/linux/pointer'),"&Pointer", self.pointerTypeGroup, checkable=True, shortcut="Ctrl+p",
                statusTip="draw connection line", triggered=self.moveItemAction)
        self.line_connect_act = QtGui.QAction(QtGui.QIcon(':/linux/line_connect'),"L&ine", self.pointerTypeGroup, checkable=True,shortcut="Ctrl+L",
                statusTip="draw connection line", triggered=self.connectItemsAction)
                
        self.copy_act = QtGui.QAction(QtGui.QIcon(':/linux/copy'),"&Copy", self, shortcut="Ctrl+c",
                    statusTip="copy item", triggered=self.default_action)
        self.cut_act = QtGui.QAction(QtGui.QIcon(':/linux/cut'),"&Cut", self, shortcut="Ctrl+x",
                    statusTip="cut item", triggered=self.editCutAction)
        self.paste_act = QtGui.QAction(QtGui.QIcon(':/linux/paste'),"&Paste", self, shortcut="Ctrl+v",
                    statusTip="paste item", triggered=self.default_action)
                    
        self.about_act = QtGui.QAction("A&bout", self, shortcut="Ctrl+B",
                triggered=self.about_action)
                
        self.compile_act = QtGui.QAction(QtGui.QIcon(':/linux/compile'),"&Compile", self, shortcut="Ctrl+M",
                statusTip="Generate Code for all devices", triggered=self.compile_action)

    def default_action(self,mode):
        logging.debug("LARA default action")
        return()
    
    def openExperimentAction(self):  

        url1 = QtCore.QUrl("file://")
        url2 = QtCore.QUrl("file:///home")
        urls = [url1,url2]
        new_filname_dia = QtGui.QFileDialog()
        #new_filname_dia.setSidebarUrls(urls);
    
        new_filename_default = self.lara_default_working_dir
        lml_filename = new_filname_dia.getOpenFileName(self, 'Select LARA file to be opened...',new_filename_default,'LML files (*.lml)')
        
        # now generating a new experiment
        if lml_filename != "" :
            logging.debug("opening lml file %s" % lml_filename)
            curr_FI = QtCore.QFileInfo(lml_filename)
            
            self.exp_gv = la_exp.LA_ExperimentView(self)
            curr_exp = la_exp.LA_Experiment(curr_FI, self.exp_gv)
            if os.path.isfile(lml_filename):
                curr_exp.openExpLMLfile(lml_filename)
            else :
                curr_exp.initNewExp()
                
            self.experiments[curr_exp.name()] = curr_exp
            logging.debug(" creating / opening %s " % curr_exp.name())
            self.lara_default_working_dir = curr_FI.absolutePath()
    
    def new_experiment_action(self, new_lml_filename="" ):  
        if new_lml_filename == "" :
            url1 = QtCore.QUrl("file://")
            url2 = QtCore.QUrl("file:///home")
            urls = [url1,url2]
            new_filname_dia = QtGui.QFileDialog()
            #new_filname_dia.setSidebarUrls(urls);
        
            new_filename_default = self.lara_default_working_dir + "/%s_%s.lml" %( QtCore.QDateTime.currentDateTime().toString("yyMMdd_hhmmss"),"process")
            new_lml_filename = new_filname_dia.getSaveFileName(self, 'Select New empty LARA file to be used...',new_filename_default,'LML files (*.lml)')
        
        # now generating a new experiment
        if new_lml_filename != "" :
            print(new_lml_filename)
            logging.debug("creating new file %s" % new_lml_filename)
            curr_FI = QtCore.QFileInfo(new_lml_filename)
            logging.info("try to replace by weak list")
            
            self.exp_gv = la_exp.LA_ExperimentView(self)
            curr_exp = la_exp.LA_Experiment(curr_FI, self.exp_gv)
            if os.path.isfile(new_lml_filename):
                curr_exp.openExpLMLfile(new_lml_filename)
            else :
                curr_exp.initNewExp()
                
            self.experiments[curr_exp.name()] = curr_exp
            logging.debug(" creating / opened %s " % curr_exp.name())
            self.lara_default_working_dir = curr_FI.absolutePath()
            
    def  editCutAction(self):
        """ Function doc """
        self.editCutSig.emit()

    def moveItemAction(self,mode):
        logging.debug("switched to move item")
        self.pointerTypeSig.emit(la_exp.LA_Experiment.MoveItem)
        QtGui.QApplication.restoreOverrideCursor()
        # inselect all items in scene
        self.unselctAllSig.emit()
        
    def connectItemsAction(self,mode):
        logging.debug("switched to line connection")
        self.pointerTypeSig.emit(la_exp.LA_Experiment.LineConnect)
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

    def compile_action(self):
        curr_tabwiget = self.central_tw.currentWidget().scene()
        
        logging.info("could be later packed into a try except box")
        curr_tabwiget.compile_experiment()
        
        #~ try:
            #~ 
        #~ except:
            #~ QtGui.QMessageBox.warning(self,"Code Generator Warning", "Error during compilation of experiment !")
            #~ logging.error("error during compilation of experiment")

    def about_action(self):
        QtGui.QMessageBox.about(self, "About LARA","<b>LARA %s</b> is a Laboratory Automation Robotic Assistant meta programming framework." % LARA_version)

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.new_act)
        self.fileMenu.addAction(self.exit_act)
        
        self.itemMenu = self.menuBar().addMenu("&Item")
        self.itemMenu.addAction(self.cut_act)
        self.itemMenu.addSeparator()
        # property could be added
        
        self.aboutMenu = self.menuBar().addMenu("&Help")
        self.aboutMenu.addAction(self.about_act)

    def createContextMenu(self):
        #~ self.imagesTable.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        #~ self.imagesTable.addAction(self.addImagesAct)
        #~ self.imagesTable.addAction(self.removeAllImagesAct)
        pass

    def createToolbars(self):
        self.file_tb = self.addToolBar("File")
        self.file_tb.addAction(self.exit_act)
        self.file_tb.addAction(self.new_act)
        self.file_tb.addAction(self.open_act)
                
        self.editToolBar = self.addToolBar("Edit")
 
        self.editToolBar.addAction(self.copy_act)
        self.editToolBar.addAction(self.cut_act)
        self.editToolBar.addAction(self.paste_act)
        self.editToolBar.addSeparator()
        
        self.editToolBar.addAction(self.move_item_act)
        self.editToolBar.addAction(self.line_connect_act)

        self.compile_tb = self.addToolBar("Compile")
        self.compile_tb.addAction(self.compile_act)
        
        #~ self.zoom_tb = self.addToolBar("Zoom")
        #~ zoomSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        #~ zoomSlider.setRange(5, 200)
        #~ zoomSlider.setValue(100)
        #~ self.zoom_tb.addWidget(zoomSlider)
        
    def createLeftToolTabWidget(self,parent):
        self.left_docwidget_dw = QtGui.QDockWidget(self)

        main_tooltab_widget = QtGui.QTabWidget(parent)
        main_tooltab_widget.setTabPosition(QtGui.QTabWidget.East)

        main_tooltab_widget.setMaximumWidth(142)  # would be more elegant to calculate the width e.g. iconwidth + offset
     
        # simple "plugin" routine : importing subprocess item modules from  
        self.item_modules = { "cultivation":[], "process_flow":[], "analysis":[], "container":[], "liquid_handling":[],  "XNA_processing":[]  }
        
        try:
            for package_name in sorted(self.item_modules.iterkeys()):     # iterate through all package directories
                package = __import__("lara." + package_name, fromlist=[""])
                prefix = package.__name__ + "."
                itemWidget = LA_ToolBoxWidget(main_tooltab_widget)
                for loader, module_name, ispkg in pkgutil.iter_modules(package.__path__, prefix):
                    logging.debug( "Found submodule %s (is a package: %s)" % (module_name, ispkg) )
                    module = __import__(module_name, fromlist=[""])
                    tool_item = module.InitItem(itemWidget)
                    self.tool_item_lst[tool_item.name()]=tool_item
                    self.item_modules[package_name] = tool_item.diagramClass()
                main_tooltab_widget.addTab(itemWidget, Qt.QString(package_name))
    
        except ImportError:
            error_msg = "failed to import module"
            sys.stderr.write(error_msg)
            
        self.left_docwidget_dw.setWidget(main_tooltab_widget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.left_docwidget_dw )
 
    def closeTab(self,index):
        tab_name = self.central_tw.tabText(index)
        if "_overview" in tab_name:
            experiment_name = tab_name[:-len("_overview")]
            # saving experiment before closing
            experiment = self.experiments[experiment_name]
            self.saveExpXMLFile(experiment)
            del self.experiments[experiment_name]
            self.central_tw.removeTab(index-1)
            self.central_tw.removeTab(index-1)
        else :
            # saving experiment before closing
            experiment = self.experiments[tab_name]
            self.saveExpXMLFile(experiment)
            
            del self.experiments[tab_name]
            self.central_tw.removeTab(index)
            self.central_tw.removeTab(index) 
            
    def saveExpXMLFile(self, experiment):
        exp_out_file = experiment.xmlFileInfo().fileName().toAscii()
        try:
            ET.ElementTree(experiment.exp_lml_root).write(exp_out_file , encoding='UTF-8', xml_declaration=True, method="xml")
            logging.debug("lara: Experiment XML outputfile %s written" % experiment.name())
        except IOError:
            logging.Error("Cannot write Experiment XML outputfile %s !!!" % experiment.name())
            
    def saveAllExpXMLFiles(self):
        for experiment in self.experiments.itervalues() :
            self.saveExpXMLFile(experiment)
                
    def saveOverviews(self):
        for experiment in self.experiments.itervalues() :
            exp_out_file = "Overview_" + experiment.xmlFileInfo().fileName().toAscii() + ".html"
            try:
                with open(exp_out_file, 'w') as f:
                    f.write('<!DOCTYPE html>')
                    ET.ElementTree(experiment.exp_ov.root()).write(f, 'UTF-8',method="html")
                f.close()
                logging.debug("lara: Experiment XML outputfile %s written" % experiment.name())
            except IOError:
                logging.Error("Cannot write Experiment XML outputfile %s !!!" % experiment.name())

    def readLARASettings(self):
        self.settings = QtCore.QSettings("Ismeralda", "lara")
    
        self.lara_default_working_dir = self.settings.value("application/working_dir").toString()
        if not self.lara_default_working_dir :
            self.lara_default_working_dir = os.getcwd()
        recent_files_list = QtCore.QStringList()
        recent_files_list = self.settings.value("files/recent_files").toStringList()
        
        for recent_file_name in recent_files_list: 
            self.new_experiment_action(recent_file_name)
           
    def writeLARASettings(self):
        self.settings.setValue("application/working_dir", self.lara_default_working_dir )
        
        recent_files_list = QtCore.QStringList() # this is freshly generated to contain the latest state
        for experiment in self.experiments.itervalues() :
            recent_files_list << experiment.xmlFileInfo().absoluteFilePath()
        print(recent_files_list)
        self.settings.setValue("files/recent_files", recent_files_list)
        
    def closeEvent(self, event):
        shutdown_message =  'Shutting down LARA, now - but first saving everything ... \n'
        sys.stderr.write(shutdown_message)
        # save all files
        self.saveAllExpXMLFiles()
        # save experiment overview html files
        self.saveOverviews()
        # save settings
        self.writeLARASettings()
        shutdown_message =  '... done, have a nice day :)\n'
        sys.stderr.write(shutdown_message)

class LA_QApplication(Qt.QApplication):
    """LARA global Q-Application"""
    
    def __init__(self,args):
        super(LA_QApplication, self).__init__(args)
        
        self.mw = LA_MainWindow()
        self.exec_()    

def print_help(args):
    help_string = """
LARA %s - planning your robot experiments from a scientist perspective
Usage:

    %s <operation> 

Operations:

    -- help     : prints help string
    -- version  : well, prints the version - or something else ?
    
""" % ( LARA_version, args[0]) 
    sys.stderr.write( help_string )
    return()

def main(*args):
    logging.basicConfig(format='%(levelname)s| %(module)s.%(funcName)s:%(message)s', level=logging.DEBUG)
        
    num_args = len(args)-1  # minus one, because the scriptname is args[0]
    if num_args:
        if args[1] == '--help':
            print_help(args)
        elif args[1] == '--version':
            version_string = "LARA version %s\n" % LARA_version
            sys.stderr.write(version_string)
        else :
            print_help(args)
    else:

        app = LA_QApplication(sys.argv)

if __name__ == '__main__':
    main(*sys.argv) 
