#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: end
# FILENAME: end_process.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.1
#
# CREATION_DATE: 2013/11/30
# LASTMODIFICATION_DATE: 2013/11/07
#
# BRIEF_DESCRIPTION: container manager
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


from PyQt4 import Qt, QtCore, QtGui
import logging

from .. import lara_toolbox_item as ltbi
from .. import lara_process as lap
from .. import lara_material as lam

class InitItem(ltbi.LA_ToolBoxItem):
    def __init__(self,parent=None):
        self.text = "Container\nManager" 
        self.item_name = "ContainerManager"
        self.diagram_class = ContainerManager
        self.icon = QtGui.QIcon(':/linux/container/container_manager')
        super(InitItem, self).__init__(self.text, self.icon, parent)
        
class ContainerManager(QtGui.QGraphicsRectItem, lap.LA_ProcessElement):
    def __init__(self, experiment=None, position=None ):
        super(ContainerManager, self).__init__(sp_name = "ContainerManager", experiment=experiment, position=position)
        
        self.setAcceptHoverEvents(True)        
        
        #self.setZValue(3.0)
        self.width = 120.0
        self.height = 80.0
        
        self.setRect(QtCore.QRectF(0.0,0.0,self.width,self.height) )
        self.setBrush(QtCore.Qt.darkGray)
        self.setAcceptHoverEvents(True)

        text_item = QtGui.QGraphicsTextItem("Container\nManager", self )
        text_item.setFont(QtGui.QFont("Helvetica",16, QtGui.QFont.Bold) )
        text_item.setPos(4.0,6.0)
        text_item.setDefaultTextColor(QtCore.Qt.lightGray)
                
        self.setPos(position)

    def initNewSubProcess(self):
        """ call this for a new sub process """
        #self.initLMLNodes()
        self.setUUID()
        
    def initParameters(self):
        """ init """
        pass
 
    def hoverEnterEvent(self, event):
        self.setBrush(QtCore.Qt.gray)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QtCore.Qt.darkGray)

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = ContainerManagerDialog(parent_qgw=self, experiment=self.exp)

class ContainerManagerDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, experiment=None, parent=None ):
        super(ContainerManagerDialog, self).__init__(parent)
        
        self.parent_qgw = parent_qgw
        self.exp = experiment
        
        self.main_tabw = QtGui.QTabWidget(self)
        
        self.createGeneralTab()
        self.main_tabw.addTab(self.container_tabv, "Container Table")
        #self.main_tabw.addTab(self.createDetailsTab(), "Details")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.main_tabw)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Container Manager")
        self.setMinimumSize(QtCore.QSize(1024,640))
        self.show()
        
    def createGeneralTab(self):
        
        model = self.exp.containerDBModel()

        self.container_tabv = QtGui.QTableView(self.main_tabw)
        
        self.container_tabv.setModel(model)
        # this switches selection of items in table off
        self.container_tabv.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        #self.container_tabv.horizontalHeader().setDefaultSectionSize(90)
        self.container_tabv.setItemDelegate(ContainerTabDelegate(self))
        
        # possible modes are: Stretch, Fixed, ResizeToContents
        self.container_tabv.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setResizeMode(4, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.ResizeToContents)
        self.container_tabv.horizontalHeader().setStretchLastSection(True)

        #~ self.container_tabv.verticalHeader().hide()

        #self.container_tabv.itemChanged.connect(self.changeIcon)

    def createDetailsTab(self):
        details_tabw = QtGui.QWidget(self)
        
        incubation_gb = QtGui.QGroupBox("Incubation Details", details_tabw)
        
        return(details_tabw)        
        
class ContainerTabDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        #logging.debug(" creating editor index col %s" %( index.column()))
        if index.column() == 2:                         # number
            itemEditor = QtGui.QSpinBox(parent)
            itemEditor.setMinimum(1)
            itemEditor.valueChanged.connect(self.emitCommitData)
            
        elif index.column() == 3:                       # type
            itemEditor = QtGui.QComboBox(parent)
            std_cont = lam.StandardContainer()
            for cont_type in std_cont.stdContTypes():
                itemEditor.addItem(cont_type)
            itemEditor.activated.connect(self.emitCommitData)
        elif index.column() == 4:                       # function
            itemEditor = QtGui.QComboBox(parent)
            itemEditor.addItem("U")
            itemEditor.addItem("L")
            itemEditor.activated.connect(self.emitCommitData)
        else :
            # create default editor
            return QtGui.QItemDelegate.createEditor(self,parent, option, index)
            
        return(itemEditor)

    def setEditorData(self, editor, index):
        itemEditor = editor
        #logging.debug(" set e data editor %s, index %s" %(editor, index))
        if not itemEditor:
            return
            
        if index.column() == 2:
            # data retuns tuple (number, bool)
            itemEditor.setValue(index.model().data(index).toInt()[0])
            
        elif index.column() == 3:
            pos = itemEditor.findText(index.model().data(index).toString(),
                    QtCore.Qt.MatchExactly)
            itemEditor.setCurrentIndex(pos)
        elif index.column() == 4:
            pos = itemEditor.findText(index.model().data(index).toString(),
                    QtCore.Qt.MatchExactly)
            itemEditor.setCurrentIndex(pos)
        else :
            itemEditor.setText(index.model().data(index).toString())

    def setModelData(self, editor, model, index):
        itemEditor = editor
        #logging.debug(" set e data model %s, index %s" %(editor, index))
        if not itemEditor:
            return
            
        if index.column() == 2:
            model.setData(index, itemEditor.value())
            
        elif index.column() == 3:
            model.setData(index, itemEditor.currentText())
        elif index.column() == 4:
            model.setData(index, itemEditor.currentText())
        else :
            model.setData(index, itemEditor.text())

    def emitCommitData(self):
        self.commitData.emit(self.sender())
