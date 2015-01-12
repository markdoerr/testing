#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: barcode
# FILENAME: barcode.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/12/07
# LASTMODIFICATION_DATE: 2014/05/22
#
# BRIEF_DESCRIPTION: barcode
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
import xml.etree.ElementTree as ET

from .. import lara_toolbox_item as ltbi
from .. import lara_process as lap
from .. import lara_material as lam
from ..generators import lara_html5_generator as lht5

class InitItem(ltbi.LA_ToolBoxItem):
    def __init__(self,parent=None):
        self.icon_text = "Read-\nBarcodes" 
        self.item_name = "ReadBarcode"
        self.diagram_class = ReadBarcodeProcess
        self.icon = QtGui.QIcon(':/linux/flow/read_barcode')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)
        
class ReadBarcodeProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None ):
        super(ReadBarcodeProcess, self).__init__(sp_name="ReadBarcode", experiment=experiment, position=position)

        logging.debug("I am growing and expressing - my name is: %s" %self.name() )
        self.incubation_growth_device = ""
        self.incubation_expr_device = ""
        self.num_expr_plates = 1
        
        growth_anchit = self.createAnchorItem("Barcode")
        #expr_anchit = self.createAnchorItem("Expression")
                
        self.anchor_layout.addAnchor(growth_anchit, QtCore.Qt.AnchorTop, self.anchor_layout, QtCore.Qt.AnchorTop)
        #self.anchor_layout.addAnchor(expr_anchit, QtCore.Qt.AnchorTop, growth_anchit, QtCore.Qt.AnchorBottom)
        
        # here is the actual LARA code constructed
        self.initSubProcessCode()

        self.updateSubProcessCode()
        
        # the description items are generated here
        self.updateOverview()
        
        self.exp.valueChanged.connect(self.updateSubProcessCode)

    def createAnchorItem(self, name=""):
        # to handle line draw events make a move to connection pin during press and connect from there ...
        pw = QtGui.QGraphicsProxyWidget(self)
                
        info_gb = QtGui.QGroupBox(name)
        info_gb_vlout = QtGui.QVBoxLayout(info_gb)
        
        if name == "Barcode" :
            info_item_hlout1 = QtGui.QHBoxLayout()  # important it that it has no parent !
            self.mon_growth_cb = QtGui.QCheckBox("Read all barcodes (including troughs)?")
            info_item_hlout1.addWidget(self.mon_growth_cb)
            
            self.mon_growth_cb.stateChanged.connect(self.updateAll) 
            
            info_item_hlout2 = QtGui.QHBoxLayout()
            info_item_hlout3 = QtGui.QHBoxLayout()
            info_item_hlout4 = QtGui.QHBoxLayout()
            info_item_hlout5 = QtGui.QHBoxLayout()
            
        info_gb_vlout.addLayout(info_item_hlout1)
        info_gb_vlout.addLayout(info_item_hlout2)
        info_gb_vlout.addLayout(info_item_hlout3)
        info_gb_vlout.addLayout(info_item_hlout4)
        info_gb_vlout.addLayout(info_item_hlout5)
    
        pw.setWidget(info_gb)
        pw.setMinimumSize(self.minSize)
        pw.setPreferredSize(self.prefSize)
        pw.setMaximumSize(self.maxSize)
        pw.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        return(pw)
        
    def updateAll(self):
        self.updateSubProcessCode()
        self.updateLMLNodes()
        #logging.debug(" barcode - total duration =%f" %self.totalDuration())
        self.updateOverview()
        logging.info("use general changed signal")
        self.exp.newcontainer_db.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.exp.valueChanged.emit()

    def initNewSubProcess(self):
        """ call this for a new sub process """
        self.initLMLNodes()
        self.setUUID()
        
    def initParameters(self):
        """ init """
        self.step_uuid = self.lml_node.get("uuid")

    def initLMLNodes(self):
        """ Function doc """
        self.lml_parms = ET.SubElement(self.lml_node, "Parameters")
        #self.setUUID()
        
    def updateLMLNodes(self):        
        pass
        
    def updateOverview(self):
        inoc_descr ="""The Barcode subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","rbp1",inoc_descr)

        #~ inoc_cond1 = "Num of plates to inoculate : \t%d" % self.num_plates_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","p2",inoc_cond1)
        
        self.exp.exp_ov.newPragraph("devices","rbdev1","Barcode Reader"  )

    def setExprPlatesNum(self, num_plates):
        """ slot for changing number of expression plates (used by details dialog) """
        self.num_expr_plates = num_plates
        self.updateAll()
        
    def setExprCycles(self, num_cycles):
        """ slot for changing number of expression cycles (used by details dialog) """
        self.updateAll()
     
    def initSubProcessCode(self):
        # preparing containers and locations at system starting conditions
     
        # request required devices
        # required_devices = ["Thermo_carousel", "Thermo_cytomat_2"] 
        # self.requestDevices(required_devices)
        pass
        
    def updateSubProcessCode(self):
        self.steps_list = []                # resetting steps_list 
        
        self.steps_list += [ lap.BeginSubProcess(step_name="readBarcode", \
                                            interpreter=lap.LA_ProcessElement.momentum32, \
                                            description="reading Barcode of all plates in process") ]
        self.steps_list.append( lap.BeginLockedTask(step_name="Barcode") )
        logging.debug("barcode cont str")
        print(self.exp.container_stream)
        print(self.exp.container_location_db)
        for curr_cont_func in self.exp.container_stream:

            if curr_cont_func in ("ExpressionPlateGreiner96NwFbU","ExpressionPlateGreiner96NwFbL", "LysatePlateGreiner96NwFbL", "AssayPlateGreiner96NwFbU", "AssayPlateGreiner96NwFbL" ):
                num_cont = self.exp.container_stream[curr_cont_func]
            
                for i in range(num_cont):
                    cont_name = curr_cont_func + str(i+1)
                    curr_cont_pos = self.exp.container_location_db[cont_name]
                    cont_prop = self.exp.newcontainer_db.properties(cont_name)
                    self.steps_list += [ lap.ReadBarcode( lidded=cont_prop[0], container=[cont_name]) ] \
                                    +  [ lap.MovePlate(curr_cont_pos[0].name(), lidded=cont_prop[0], container=[cont_name]) ]
                
        self.steps_list +=  [ lap.EndLockedTask(step_name="Barcode"), lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = ReadBarcodeParameterDialog(parent_qgw=self)
        
class ReadBarcodeParameterDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, parent=None ):
        super(ReadBarcodeParameterDialog, self).__init__(parent)
        self.parent_qgw = parent_qgw
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.createGeneralTab(), "General")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Incubation Dialog")
        self.show()
        
    def createGeneralTab(self):
        general_tabw = QtGui.QWidget(self)
        
        container_gb = QtGui.QGroupBox("Container")
        container_layout = QtGui.QVBoxLayout()
        
        info_item_hlout1 = QtGui.QHBoxLayout()
       
        #~ self.num_expr_plates_sb.valueChanged.connect(self.parent_qgw.setExprPlatesNum)
        
        container_layout.addLayout(info_item_hlout1)
        container_gb.setLayout(container_layout)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(container_gb)
        mainLayout.addStretch(1)
        general_tabw.setLayout(mainLayout)
        
        return(general_tabw)
        
