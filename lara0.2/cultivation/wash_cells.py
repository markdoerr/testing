#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: harvest_cells
# FILENAME: wash_cells.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.4
#
# CREATION_DATE: 2013/12/07
# LASTMODIFICATION_DATE: 2014/11/13
#
# BRIEF_DESCRIPTION: wash_cells
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
        self.icon_text = "Wash Cells" 
        self.item_name = "WashCells"
        self.diagram_class = WashCellsProcess
        self.icon = QtGui.QIcon(':/linux/tasks/wash_cells')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)
        
class WashCellsProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None ):
        super(WashCellsProcess, self).__init__(sp_name="WashCells", experiment=experiment, position=position)

        #~ logging.debug("I am expressing - my name is: %s" %self.name() )
        self.incubation_expr_device = ""
        self.num_expr_plates = 4
        self.max_expr_cycles = 1
        
        growth_anchit = self.createAnchorItem("WashCells")
        #~ expr_anchit = self.createAnchorItem("Expression")
                
        self.anchor_layout.addAnchor(growth_anchit, QtCore.Qt.AnchorTop, self.anchor_layout, QtCore.Qt.AnchorTop)
        #~ self.anchor_layout.addAnchor(expr_anchit, QtCore.Qt.AnchorTop, growth_anchit, QtCore.Qt.AnchorBottom)
        
        # here is the actual LARA code constructed
        self.initSubProcessCode()

        self.updateSubProcessCode()
        
        # the description items are generated here
        self.updateOverview()

    def createAnchorItem(self, name=""):
        # to handle line draw events make a move to connection pin during press and connect from there ...
        pw = QtGui.QGraphicsProxyWidget(self)
                
        info_gb = QtGui.QGroupBox(name)
        info_gb_vlout = QtGui.QVBoxLayout(info_gb)
        
        if name == "WashCells" :
            
            # centrifugation duration / rpm
              
            info_item_hlout1 = QtGui.QHBoxLayout()  # important it that it has no parent !
            self.centr_temp_dsb = QtGui.QDoubleSpinBox(info_gb)
            self.centr_temp_dsb.setRange(-8.0, 37.0)
            self.centr_temp_dsb.setValue(4.0)
            info_item_hlout1.addWidget(QtGui.QLabel("Centr. Temp.:"))
            info_item_hlout1.addWidget(self.centr_temp_dsb)
            info_item_hlout1.addWidget(QtGui.QLabel(" C"))
                      
            self.centr_temp_dsb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout2 = QtGui.QHBoxLayout()
            self.centr_dur_sb = QtGui.QSpinBox(info_gb)
            self.centr_dur_sb.setRange(1, 600)
            self.centr_dur_sb.setValue(45)
            info_item_hlout2.addWidget(QtGui.QLabel("Centr. time:"))
            info_item_hlout2.addWidget(self.centr_dur_sb)
            info_item_hlout2.addWidget(QtGui.QLabel("min"))
            
            self.centr_dur_sb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout3 = QtGui.QHBoxLayout()
            
            self.centr_speed_sb = QtGui.QSpinBox(info_gb)
            self.centr_speed_sb.setRange(500, 4500)
            self.centr_speed_sb.setValue(4500)
            info_item_hlout3.addWidget(QtGui.QLabel("Centr. speed:"))
            info_item_hlout3.addWidget(self.centr_speed_sb)
            info_item_hlout3.addWidget(QtGui.QLabel("rpm"))
                      
            self.centr_speed_sb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout4 = QtGui.QHBoxLayout()
            
            self.wash_dur_sb = QtGui.QSpinBox(info_gb)
            self.wash_dur_sb.setRange(1, 9990)
            self.wash_dur_sb.setValue(30)
            info_item_hlout4.addWidget(QtGui.QLabel("Wash. time:"))
            info_item_hlout4.addWidget(self.wash_dur_sb)
            info_item_hlout4.addWidget(QtGui.QLabel("min"))
            
            self.wash_dur_sb.valueChanged.connect(self.updateAll)
            
            info_item_hlout5 = QtGui.QHBoxLayout()
            
            self.dispenser_lysis_cb = QtGui.QComboBox(info_gb)
            self.dispenser_lysis_cb.addItem("Agilent Bravo")
            self.dispenser_lysis_cb.addItem("Thermo Combi")
            info_item_hlout5.addWidget(QtGui.QLabel("Dispenser:"))
            info_item_hlout5.addWidget(self.dispenser_lysis_cb)
            info_item_hlout5.addWidget(QtGui.QLabel(" "))
            
            self.dispenser_lysis_cb.currentIndexChanged.connect(self.updateAll)    
            
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
        #logging.debug(" wash_cells - total duration =%f" %self.totalDuration())
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
        self.lml_temp_parm = self.lml_node.find( 'Parameters/Temperature' )
        curr_temp = self.lml_temp_parm.get("temperature")
        if curr_temp :
            self.centr_temp_dsb.setValue(float(curr_temp))

    def initLMLNodes(self):
        """ Function doc """
        self.lml_parms = ET.SubElement(self.lml_node, "Parameters")
        self.lml_temp_parm = ET.SubElement(self.lml_parms, "Temperature")
        logging.debug("temp parameter created")
        print(self.lml_temp_parm)
        #self.setUUID()
        
    def updateLMLNodes(self):
        self.lml_temp_parm.set("temperature",str(self.centr_temp_dsb.value() ))
        pass
        
    def updateOverview(self):
        inoc_descr ="""The WashCells subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","lysp1",inoc_descr)
                
        par_text = "WashCells time: \t%d min" % self.centr_dur_sb.value()
        self.exp.exp_ov.newPragraph("description","lysp2", par_text)
        
        #~ inoc_cond1 = "Num of plates to inoculate : \t%d" % self.num_plates_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","p2",inoc_cond1)
        
        self.exp.exp_ov.newPragraph("devices","lysdev1","Hettich Rotanta" )
        self.exp.exp_ov.newPragraph("devices","lysdev2","Agilent Bravo" )
   
    def setExprPlatesNum(self, num_plates):
        """ slot for changing number of wash_cells plates (used by details dialog) """
        self.num_expr_plates = num_plates
        self.updateAll()
        
    def setExprCycles(self, num_cycles):
        """ slot for changing number of wash_cells cycles (used by details dialog) """
        self.max_expr_cycles = num_cycles
        self.updateAll()
     
    def initSubProcessCode(self):
        # preparing containers and locations at system starting conditions
     
        # request required devices
        # required_devices = ["Thermo_carousel", "Thermo_cytomat_2"] 
        # self.requestDevices(required_devices)
        pass

    def updateSubProcessCode(self):
        self.steps_list = []                # resetting steps_list 
        
        # request plates

        self.tr_type = "ThermoTroughDw"
        self.exp.requestContainerFromStream(container_function="WashBufferTrough1", container_type=self.tr_type, lidding_state="U", min_num = 1)
        self.exp.requestContainerFromStream(container_function="WashBufferTrough2", container_type=self.tr_type, lidding_state="U", min_num = 1)
        self.expl_type = "Greiner96NwFb"
        self.exp.requestContainerFromStream(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", min_num = self.num_expr_plates) # max 4 plates ! - to be set by GUI
        
        #~ if self.expr_temp_dsb.value() > 30.0 :
            #~ self.incubation_expr_device = "Cytomat1550_1"
        #~ elif self.expr_temp_dsb.value() > 20.0:
            #~ self.incubation_expr_device = "Cytomat1550_2"
        #~ else :
        self.incubation_expr_device = "Cytomat1550_2"     
        
        curr_expl_func = "ExpressionPlate" + self.expl_type +"L"
        self.num_expression_plates =  self.exp.container_stream[curr_expl_func]
        
              
        if ( (self.num_expression_plates  % 2) > 0 ) and ( self.num_expression_plates != 1 ) :
            logging.error("expression process: !!!! wrong number of expression plates")
            
        # place in default location (device, stack, first_pos, int/ext)
        
        self.exp.defDefaultStartLocation(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", dev_pos=("Carousel",1,1,"ext"))
        
        # make checkbox for multiple washing cycles

        self.exp.defDefaultStartLocation(container_function="WashBufferTrough1", container_type=self.tr_type, lidding_state="U", dev_pos=("Cytomat_2",2,2,"int"))
        self.exp.defDefaultStartLocation(container_function="WashBufferTrough2", container_type=self.tr_type, lidding_state="U", dev_pos=("Cytomat_2",2,3,"int"))
        
        washtr1_name = "WashBufferTrough1%s%s%i" %(self.tr_type, "U", 1)
        washtr2_name = "WashBufferTrough2%s%s%i" %(self.tr_type, "U", 1)
        
        # plates are now in place to do the first steps:

        self.steps_list += [ lap.BeginSubProcess(step_name="wash_cells", \
                                            interpreter=lap.LA_ProcessElement.momentum32, \
                                            description="Wash cells") ]
                                            
        # adding wash buffer or osmotic shock buffer
        # resuspension might be useful
        self.steps_list += [lap.BeginLockedTask(step_name="Wash"), lap.MovePlate(target_device="Bravo", position=4, container=[washtr1_name])]
        curr_position = 6
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(i+1)
            self.steps_list += [ lap.MovePlate(target_device="Bravo", position=curr_position, container=[cont_name]) ]
            curr_position += 1
        self.steps_list += [lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_BufferTransfer4plates.pro")] # adding wash buffer
        self.steps_list += [ ]   
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(self.num_expression_plates-i)
            self.steps_list += [ lap.AutoLoad(device="Rotanta", container=[cont_name]) ]
        self.steps_list += [lap.MovePlate(target_device="Carousel", container=[washtr1_name])]
        
        # centrifugation to remove washing solution
         
        self.steps_list += [ lap.Centrifuge(device="Rotanta", speed=self.centr_speed_sb.value(), temperature=self.centr_temp_dsb.value(), duration=self.centr_dur_sb.value() )]
                                                    
        # removal of the washing solution (supernatant) - could be interwoven with wash
        self.steps_list += []
        curr_position = 6
        self.steps_list += [ lap.MovePlate(target_device="Bravo", position=4, container=[washtr2_name]) ]
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(i+1)
            self.steps_list += [ lap.MovePlate(target_device="Bravo", position=curr_position, container=[cont_name]) ]
            curr_position += 1 
        self.steps_list += [ lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_SupRemoval4plates.pro")]
        
        # resuspension (with or without adding wash buffer)
        if (True):  # add checkbox in GUI ! 
            self.steps_list += [lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_lysis4plates.pro")] #head_left.pro
            
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(self.num_expression_plates-i)
            self.steps_list += [ lap.MovePlate(target_device="Cytomat_2", lidded="L", container=[cont_name])]
 
        self.steps_list += [ lap.MovePlate(target_device="Carousel", container=[washtr2_name]) ]
        
        self.steps_list +=  [ lap.EndLockedTask(step_name="Wash"), lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = WashCellsParameterDialog(parent_qgw=self)
        
class WashCellsParameterDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, parent=None ):
        super(WashCellsParameterDialog, self).__init__(parent)
        self.parent_qgw = parent_qgw
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.createGeneralTab(), "General")
        tabWidget.addTab(self.createWashCellsDetailsTab(), "WashCells Details")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Harvest Cells Dialog")
        self.show()
        
    def createGeneralTab(self):
        general_tabw = QtGui.QWidget(self)
        
        container_gb = QtGui.QGroupBox("Container")
        container_layout = QtGui.QVBoxLayout()
        
        info_item_hlout1 = QtGui.QHBoxLayout()
        self.num_expr_plates_sb = QtGui.QSpinBox(container_gb)
        self.num_expr_plates_sb.setRange(2, 32)
        self.num_expr_plates_sb.setValue(4)
        info_item_hlout1.addWidget(QtGui.QLabel("Num. of plates:"))
        info_item_hlout1.addWidget(self.num_expr_plates_sb)
        info_item_hlout1.addWidget(QtGui.QLabel("96 well MTPs"))
        
        #~ self.num_expr_plates_sb.valueChanged.connect(self.parent_qgw.setExprPlatesNum)
        
        container_layout.addLayout(info_item_hlout1)
        container_gb.setLayout(container_layout)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(container_gb)
        mainLayout.addStretch(1)
        general_tabw.setLayout(mainLayout)
        
        return(general_tabw)
            
    def createWashCellsDetailsTab(self):
        details_tabw = QtGui.QWidget(self)
        
        expression_gb = QtGui.QGroupBox("Cell Wash Details")
        expression_layout = QtGui.QVBoxLayout()
        
        # washing: centr duration, speed, temp
        logging.info("change status when unchecked - activation")
        info_item_hlout1 = QtGui.QHBoxLayout()
        self.num_expr_cyc_sb = QtGui.QSpinBox(expression_gb)
        self.num_expr_cyc_sb.setRange(1, 64)
        self.num_expr_cyc_sb.setValue(7)
        info_item_hlout1.addWidget(QtGui.QLabel("Expr. cycles:"))
        info_item_hlout1.addWidget(self.num_expr_cyc_sb)
        info_item_hlout1.addWidget(QtGui.QLabel(" "))
        
        #~ self.num_expr_cyc_sb.valueChanged.connect(self.parent_qgw.setExprCycles)
        
        expression_layout.addLayout(info_item_hlout1)
        expression_gb.setLayout(expression_layout)
            
        #~ self.num_growth_cyc_sb.valueChanged.connect(self.updateAll)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(expression_gb)
        mainLayout.addStretch(1)
        details_tabw.setLayout(mainLayout)
        return(details_tabw)        
