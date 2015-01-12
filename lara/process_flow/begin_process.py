#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: begin
# FILENAME: begin_process.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.0
#
# CREATION_DATE: 2013/11/07
# LASTMODIFICATION_DATE: 2013/11/29
#
# BRIEF_DESCRIPTION: bengin 
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
        self.text = "Begin" 
        self.item_name = "BeginProcess"
        self.diagram_class = BeginProcess
        self.icon = QtGui.QIcon(':/linux/flow/begin')
        super(InitItem, self).__init__(self.text, self.icon, parent)
        
class BeginProcess(QtGui.QGraphicsEllipseItem, lap.LA_ProcessElement):
    def __init__(self, experiment=None, position=None ):
        super(BeginProcess, self).__init__(sp_name="BeginProcess", experiment=experiment, position=position)
        
        self.setAcceptHoverEvents(True)        
        
        #self.setZValue(3.0)
        self.width = 90.0
        self.height = 90.0
        
        self.setRect(QtCore.QRectF(0.0,0.0,self.width,self.height) )
        self.setBrush(QtCore.Qt.green)
        self.setAcceptHoverEvents(True)

        text_item = QtGui.QGraphicsTextItem("Begin", self)
        text_item.setFont(QtGui.QFont("Helvetica",18, QtGui.QFont.Bold) )
        text_item.setPos(8.0,25.0)
        
        # the actual steps of the process
        
        self.steps_list = [lap.BeginProcess()]
        self.setPos(position)

    def initNewSubProcess(self):
        """ call this for a new sub process """
        #self.initLMLNodes()
        self.setUUID()
        
    def initParameters(self):
        """ init """
        pass
 
    def hoverEnterEvent(self, event):
        self.setBrush(QtCore.Qt.yellow)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QtCore.Qt.green)

        
