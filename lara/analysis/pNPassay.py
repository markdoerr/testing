#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: growth
# FILENAME: AcPhassay.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.2
#
# CREATION_DATE: 2014/05/14
# LASTMODIFICATION_DATE: 2014/05/26
#
# BRIEF_DESCRIPTION: pNPassay
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
        self.icon_text = "pNPassay" 
        self.item_name = "pNPassay"
        self.diagram_class = pNPassayProcess
        self.icon = QtGui.QIcon(':/linux/tasks/assay')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)
        
class pNPassayProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None ):
        super(pNPassayProcess, self).__init__(sp_name="pNPassay", experiment=experiment, position=position)

        logging.debug("I am the pNPXassay - my name is: %s" %self.name() )
        self.num_expr_plates = 4
        
        assay_anchit = self.createAnchorItem("pNPassay")
                
        self.anchor_layout.addAnchor(assay_anchit, QtCore.Qt.AnchorTop, self.anchor_layout, QtCore.Qt.AnchorTop)
        #~ self.anchor_layout.addAnchor(expr_anchit, QtCore.Qt.AnchorTop, assay_anchit, QtCore.Qt.AnchorBottom)
        
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
        
        if name == "pNPassay" :
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
            info_item_hlout2.addWidget(QtGui.QLabel("pNPassay. time:"))
            info_item_hlout2.addWidget(self.growth_dur_sb)
            info_item_hlout2.addWidget(QtGui.QLabel("min"))
            
            self.growth_dur_sb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout3 = QtGui.QHBoxLayout()
            #~ mon_growth_cb = QtGui.QCheckBox("Monitor Growth ?")
            #~ info_item_hlout3.addWidget(mon_growth_cb)
            
            info_item_hlout4 = QtGui.QHBoxLayout()
            
            #~ self.num_growth_cyc_sb.valueChanged.connect(self.updateAll)
            
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
        #logging.debug(" growth - total duration =%f" %self.totalDuration())
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
        inoc_descr ="""The Acetophenone Assay and Expression subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","asp1",inoc_descr)

        #~ par_text = "Growth temperature : \t%d C" % self.growth_temp_dsb.value()
        #~ self.exp.exp_ov.newPragraph("description","asp2",par_text)
#~ 
        #~ par_text = "Growth Time (pre expression) : \t%d min" % self.growth_dur_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","asp3",par_text)
        
        #~ inoc_cond1 = "Num of plates to inoculate : \t%d" % self.num_plates_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","p2",inoc_cond1)
        
        self.exp.exp_ov.newPragraph("devices","dev5","Agilent Bravo" )

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
        self.exp.requestContainerFromStream(container_function="AssayMixTrough", container_type=self.tr_type, lidding_state="U", min_num = 1)
        self.tr_type = "ThermoTroughDw"
        self.exp.requestContainerFromStream(container_function="TipboxTemp", container_type=self.tr_type, lidding_state="U", min_num = 1) 
        self.lyspl_type = "Greiner96NwFb"
        self.exp.requestContainerFromStream(container_function="LysatePlate", container_type=self.lyspl_type, lidding_state="L", min_num = 4) # max 6 plates ! - to be set by GUI
        self.aspl_type = "Greiner96NwFb"
        self.exp.requestContainerFromStream(container_function="AssayPlate", container_type=self.aspl_type, lidding_state="U", min_num = 4) # max 6 plates ! - to be set by GUI
        
        curr_lyspl_func = "LysatePlate" + self.lyspl_type +"L"
        self.num_lysate_plates =  self.exp.container_stream[curr_lyspl_func]
        curr_aspl_func = "AssayPlate" + self.lyspl_type +"U"
        self.num_assay_plates =  self.exp.container_stream[curr_aspl_func]
        
        assaytr_name = "AssayMixTrough%s%s%i" %(self.tr_type, "U", 1)
        tbtemp_name = "TipboxTemp%s%s%i" %(self.tr_type, "U", 1)
        
        #~ if ( (self.num_lysate_plates  % 2) > 0 ) and ( self.num_expression_plates != 1 ) :
            #~ logging.error("growth process: !!!! wrong number of expression plates")
            
        # place in default location (device, stack, first_pos, int/ext)

        self.exp.defDefaultStartLocation(container_function="LysatePlate", container_type=self.lyspl_type, lidding_state="L", dev_pos=("Cytomat_2",1,4,"ext"))
        self.exp.defDefaultStartLocation(container_function="TipboxTemp", container_type=self.tr_type, lidding_state="U", dev_pos=("Tip_Storage",1,6,"ext"))
        self.exp.defDefaultStartLocation(container_function="AssayPlate", container_type=self.aspl_type, lidding_state="U", dev_pos=("Carousel",3,1,"ext"))
        self.exp.defDefaultStartLocation(container_function="AssayMixTrough", container_type=self.tr_type, lidding_state="U", dev_pos=("Cytomat_2",2,3,"int"))
        
        # plates are now in place to do the first steps:
          
        self.steps_list += [ lap.BeginSubProcess(step_name="pNPassay", \
                                            interpreter=lap.LA_ProcessElement.momentum32, \
                                            description="para-Nitrophenol Assay") ]
        
        #self.steps_list += [ lap.BeginLoop(max_iterations=self.num_growth_cyc_sb.value(), description="growth loop before expression")]
        
        for i in range(self.num_lysate_plates):
            lys_cont_name = curr_lyspl_func + str(i+1)
            as_cont_name = curr_aspl_func + str(i+1)
            # dispensing the assay solution Bravo/Combi
            self.steps_list += [lap.BeginLockedTask(step_name="Bravo"),
                                lap.MovePlate(target_device="Bravo", position=2, container=[tbtemp_name]),
                                lap.MovePlate(target_device="Bravo", position=4, container=[assaytr_name])]
            

            curr_position = 6
            self.steps_list += [ lap.MovePlate(target_device="Bravo", position=6, container=[lys_cont_name]),
                                 lap.MovePlate(target_device="Bravo", position=9, container=[as_cont_name]) ]
            self.steps_list += [ lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_EnzymeFastTransfer1plate75ulSubstrTrough.pro"), 
                                lap.Delay(),
                                lap.MovePlate(target_device="Varioskan", container=[as_cont_name])]
            self.steps_list += [ lap.BeginParallel(),  
                                 lap.BeginThread(), lap.RunExternalProtocol(target_device="Varioskan", protocol="IKO_pNP_20min", container=[as_cont_name]), lap.EndThread(),
                                 lap.BeginThread(), lap.MovePlate(target_device="Cytomat_2", lidded="L", container=[lys_cont_name]), 
                                   lap.MovePlate(target_device="Cytomat_2", container=[assaytr_name]),
                                   lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_washTempTips.pro"), 
                                   lap.MovePlate(target_device="Tip_Storage", container=[tbtemp_name]),
                                   lap.EndLockedTask(step_name="Bravo"),
                                   lap.EndThread(), lap.EndParallel()]
            self.steps_list += [lap.MovePlate(target_device="Carousel", container=[as_cont_name])]
                                                         
        self.steps_list +=  [ lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = pNPassayParameterDialog(parent_qgw=self)
        
class pNPassayParameterDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, parent=None ):
        super(pNPassayParameterDialog, self).__init__(parent)
        self.parent_qgw = parent_qgw
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.createGeneralTab(), "General")
        tabWidget.addTab(self.createpNPassayDetailsTab(), "pNPassay Details")

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("pNPassay Dialog")
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
        
    def createpNPassayDetailsTab(self):
        details_tabw = QtGui.QWidget(self)
        
        growth_gb = QtGui.QGroupBox("pNPassay Details")
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

