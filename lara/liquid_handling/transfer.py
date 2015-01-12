#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: transfer
# FILENAME: transfer.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2014/02/21
# LASTMODIFICATION_DATE: 2014/05/02
#
# BRIEF_DESCRIPTION: transfer
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
        self.icon_text = "Transfer" 
        self.item_name = "Transfer"
        self.diagram_class = TransferProcess
        self.icon = QtGui.QIcon(':/linux/liquid_handling/transfer')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)
        
class TransferProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None ):
        super(TransferProcess, self).__init__(sp_name="Transfer", experiment=experiment, position=position)

        logging.debug("I am transfer - my name is: %s" %self.name() )
        self.incubation_growth_device = ""
        self.num_expr_plates = 4
        
        transfer_anchit = self.createAnchorItem("Transfer")
                
        self.anchor_layout.addAnchor(transfer_anchit, QtCore.Qt.AnchorTop, self.anchor_layout, QtCore.Qt.AnchorTop)
        #~ self.anchor_layout.addAnchor(expr_anchit, QtCore.Qt.AnchorTop, transfer_anchit, QtCore.Qt.AnchorBottom)
        
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
        
        if name == "Transfer" :
            info_item_hlout1 = QtGui.QHBoxLayout()  # important it that it has no parent !
            self.growth_temp_dsb = QtGui.QDoubleSpinBox(info_gb)
            self.growth_temp_dsb.setRange(15.0, 50.0)
            self.growth_temp_dsb.setValue(37.0)
            info_item_hlout1.addWidget(QtGui.QLabel("Temp.:"))
            info_item_hlout1.addWidget(self.growth_temp_dsb)
            info_item_hlout1.addWidget(QtGui.QLabel(" C"))
                      
            self.growth_temp_dsb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout2 = QtGui.QHBoxLayout()
            self.growth_dur_sb = QtGui.QSpinBox(info_gb)
            self.growth_dur_sb.setRange(1, 9900)
            self.growth_dur_sb.setValue(60)
            self.growth_dur_lab = QtGui.QLabel("min")
            info_item_hlout2.addWidget(QtGui.QLabel("Transfer dur.:\n(per cycle)"))
            info_item_hlout2.addWidget(self.growth_dur_sb)
            info_item_hlout2.addWidget(self.growth_dur_lab)
            
            self.growth_dur_sb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout3 = QtGui.QHBoxLayout()
            #~ mon_growth_cb = QtGui.QCheckBox("Monitor Transfer ?")
            #~ info_item_hlout3.addWidget(mon_growth_cb)
            
            logging.info("change status when unchecked - activation")
            info_item_hlout4 = QtGui.QHBoxLayout()
            self.num_growth_cyc_sb = QtGui.QSpinBox(info_gb)
            self.num_growth_cyc_sb.setRange(1, 64)
            self.num_growth_cyc_sb.setValue(7)
            info_item_hlout4.addWidget(QtGui.QLabel("Growth. cycles:"))
            info_item_hlout4.addWidget(self.num_growth_cyc_sb)
            info_item_hlout4.addWidget(QtGui.QLabel(" "))
            
            self.num_growth_cyc_sb.valueChanged.connect(self.updateAll)
            
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
        #logging.debug(" transfer - total duration =%f" %self.totalDuration())
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
            self.growth_temp_dsb.setValue(float(curr_temp))

    def initLMLNodes(self):
        """ Function doc """
        self.lml_parms = ET.SubElement(self.lml_node, "Parameters")
        self.lml_temp_parm = ET.SubElement(self.lml_parms, "Temperature")
        logging.debug("temp parameter created")
        print(self.lml_temp_parm)
        
    def updateLMLNodes(self):
        self.lml_temp_parm.set("temperature",str(self.growth_temp_dsb.value() ))
        pass
        
    def updateOverview(self):
        inoc_descr ="""The Transfer and Expression subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","gep1",inoc_descr)

        par_text = "Growth temperature : \t%d C" % self.growth_temp_dsb.value()
        self.exp.exp_ov.newPragraph("description","gep2",par_text)

        par_text = "Growth Time (pre expression) : \t%d min" % self.growth_dur_sb.value()
        self.exp.exp_ov.newPragraph("description","gep3",par_text)
        
        #~ inoc_cond1 = "Num of plates to inoculate : \t%d" % self.num_plates_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","p2",inoc_cond1)
        
        self.exp.exp_ov.newPragraph("devices","dev1","Incubator %s" % self.incubation_growth_device )

    def initSubProcessCode(self):
        # preparing containers and locations at system starting conditions
     
        # request required devices
        # required_devices = ["Thermo_carousel", "Thermo_cytomat_2"] 
        # self.requestDevices(required_devices)
        pass
        
    def updateSubProcessCode(self):
        self.growth_dur_lab.setText("("+ str(self.growth_dur_sb.value() * self.num_growth_cyc_sb.value() ) + ") min")
		
        self.steps_list = []                # resetting steps_list
        # request plates
        self.tr_type = "ThermoTroughDw"
        self.exp.requestContainerFromStream(container_function="InductorTrough", container_type=self.tr_type, lidding_state="U", min_num = 0) 
        self.expl_type = "Greiner96NwFb"
        self.exp.requestContainerFromStream(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", min_num = self.num_expr_plates) # max 6 plates ! - to be set by GUI
        
        #~ curr_mapl_func = "MasterPlate" + self.mp_type +"L"
        #~ self.num_master_plates =  self.exp.container_stream[curr_mapl_func]

        curr_expl_func = "ExpressionPlate" + self.expl_type +"L"
        self.num_expression_plates =  self.exp.container_stream[curr_expl_func]
        
        if ( (self.num_expression_plates  % 2) > 0 ) and ( self.num_expression_plates != 1 ) :
            logging.error("transfer process: !!!! wrong number of expression plates")
            
        # place in default location (device, stack, first_pos, int/ext)
        
        #~ self.exp.defDefaultStartLocation(container_function="MasterPlate", container_type=self.mp_type, lidding_state="L", dev_pos=("Thermo_carousel",1,1,"ext"))
        self.exp.defDefaultStartLocation(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", dev_pos=("Carousel",1,1,"ext"))
        
        # plates are now in place to do the first steps:

        self.steps_list += [ lap.BeginSubProcess(step_name="transfer", \
                                            interpreter=lap.LA_ProcessElement.vworks11, \
                                            description="Transfer of a liquid in liquid handling robot") ]
        # place plates
        src_cont_name = curr_expl_func + str(1)
        target_cont_name = "target_" + curr_expl_func + str(1)
        
        # lap.MovePlate(target_device="Bravo", position=1, static="1", container_type="BravoWashDw", container=["wash"]), 
        self.steps_list += [
                    lap.MovePlate(target_device="Bravo", position=3, static="1", container_type="TipBoxDw", container=["tip_box"]),
                    lap.MovePlate(target_device="Bravo", position=5, static="1", container=[src_cont_name]),
                    lap.MovePlate(target_device="Bravo", position=6, container=[target_cont_name]), 
                    lap.LoadTips(target_device="Bravo", columns=1, rows=1, column_pos=0, row_pos=7), 
                    lap.Aspirate(device="Bravo", volume=10, column_pos=0, row_pos=1, container=[src_cont_name]),
                    lap.Dispense(device="Bravo", volume=10, column_pos=1, row_pos=6, container=[target_cont_name]),  
                    lap.UnloadTips(target_device="Bravo", columns=1, rows=1, column_pos=0, row_pos=7) ]
        
        # liquid transfer
       
        self.steps_list +=  [ lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = TransferParameterDialog(parent_qgw=self)
        
class TransferParameterDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, parent=None ):
        super(TransferParameterDialog, self).__init__(parent)
        self.parent_qgw = parent_qgw
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.createGeneralTab(), "General")
        tabWidget.addTab(self.createTransferDetailsTab(), "Transfer Details")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Transfer Dialog")
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
        
    def createTransferDetailsTab(self):
        details_tabw = QtGui.QWidget(self)
        
        growth_gb = QtGui.QGroupBox("Transfer Details")
        growth_layout = QtGui.QVBoxLayout()
        
        info_item_hlout1 = QtGui.QHBoxLayout()
        
        #~ temp_lab = QtGui.QLabel("Volume:")
        #~ temp_lab.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        
        #~ self.num_expr_cyc_sb.valueChanged.connect(self.parent_qgw.setExprCycles)
        
        growth_layout.addLayout(info_item_hlout1)
        growth_gb.setLayout(growth_layout)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(growth_gb)
        mainLayout.addStretch(1)
        details_tabw.setLayout(mainLayout)
        return(details_tabw)        

