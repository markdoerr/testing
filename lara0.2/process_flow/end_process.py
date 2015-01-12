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
# VERSION: 0.2.0
#
# CREATION_DATE: 2013/11/07
# LASTMODIFICATION_DATE: 2013/11/29
#
# BRIEF_DESCRIPTION: The end
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
        self.text = "End" 
        self.item_name = "EndProcess"
        self.diagram_class = EndProcess
        self.icon = QtGui.QIcon(':/linux/flow/end')
        super(InitItem, self).__init__(self.text, self.icon, parent)
        
class EndProcess(QtGui.QGraphicsEllipseItem, lap.LA_ProcessElement):
    def __init__(self, experiment=None, position=None ):
        super(EndProcess, self).__init__(sp_name = "EndProcess", experiment=experiment,position=position)
        
        self.setAcceptHoverEvents(True)        
        
        #self.setZValue(3.0)
        self.width = 90.0
        self.height = 90.0
        
        self.setRect(QtCore.QRectF(0.0,0.0,self.width,self.height) )
        self.setBrush(QtCore.Qt.red)
        self.setAcceptHoverEvents(True)

        text_item = QtGui.QGraphicsTextItem("End", self )
        text_item.setFont(QtGui.QFont("Helvetica",18, QtGui.QFont.Bold) )
        text_item.setPos(15.0,25.0)
        text_item.setDefaultTextColor(QtCore.Qt.yellow)
        
        # the actual steps of the process
        
        self.steps_list = [lap.EndProcess()]
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
        self.setBrush(QtCore.Qt.red)
