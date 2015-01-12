#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: expression
# FILENAME: expression.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/12/07
# LASTMODIFICATION_DATE: 2014/11/21
#
# BRIEF_DESCRIPTION: expression
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
        self.icon_text = "Expression" 
        self.item_name = "Expression"
        self.diagram_class = ExpressionProcess
        self.icon = QtGui.QIcon(':/linux/cultivation/expression')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)
        
class ExpressionProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None ):
        super(ExpressionProcess, self).__init__(sp_name="Expression", experiment=experiment, position=position)

        #~ logging.debug("I am expressing - my name is: %s" %self.name() )
        self.incubation_expr_device = ""
        self.num_expr_plates = 4
        self.max_expr_cycles = 1
        
        growth_anchit = self.createAnchorItem("Expression")
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
        
        if name == "Expression" :
            info_item_hlout1 = QtGui.QHBoxLayout()  # important it that it has no parent !
            self.expr_temp_dsb = QtGui.QDoubleSpinBox(info_gb)
            self.expr_temp_dsb.setRange(15.0, 50.0)
            self.expr_temp_dsb.setValue(20.0)
            info_item_hlout1.addWidget(QtGui.QLabel("Temp.:"))
            info_item_hlout1.addWidget(self.expr_temp_dsb)
            info_item_hlout1.addWidget(QtGui.QLabel(" C"))
                      
            self.expr_temp_dsb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout2 = QtGui.QHBoxLayout()
            self.expr_dur_sb = QtGui.QSpinBox(info_gb)
            self.expr_dur_sb.setRange(1, 9900)
            self.expr_dur_sb.setValue(120)
            self.expr_dur_lab = QtGui.QLabel("min")
            info_item_hlout2.addWidget(QtGui.QLabel("Expr. dur.:\n(per cycle)"))
            info_item_hlout2.addWidget(self.expr_dur_sb)
            info_item_hlout2.addWidget(self.expr_dur_lab)
            
            self.expr_dur_sb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout3 = QtGui.QHBoxLayout()
            self.induct_type = QtGui.QComboBox(info_gb)
            self.induct_type.addItem("IPTG")
            self.induct_type.addItem("Rhamnose")
            info_item_hlout3.addWidget(QtGui.QLabel("Inductor:"))
            info_item_hlout3.addWidget(self.induct_type)
            info_item_hlout3.addWidget(QtGui.QLabel(" "))
            
            self.induct_type.currentIndexChanged.connect(self.updateAll) 
            
            info_item_hlout4 = QtGui.QHBoxLayout()
            self.induct_vol_dsb = QtGui.QDoubleSpinBox(info_gb)
            self.induct_vol_dsb.setRange(1.0, 220.0)
            self.induct_vol_dsb.setValue(20.0)
            info_item_hlout4.addWidget(QtGui.QLabel("Ind. vol.:"))
            info_item_hlout4.addWidget(self.induct_vol_dsb)
            info_item_hlout4.addWidget(QtGui.QLabel("ul/well"))
            
            self.induct_vol_dsb.valueChanged.connect(self.updateAll) 
            
            info_item_hlout5 = QtGui.QHBoxLayout()
            self.num_expr_cyc_sb = QtGui.QSpinBox(info_gb)
            self.num_expr_cyc_sb.setRange(1, 64)
            self.num_expr_cyc_sb.setValue(6)
            info_item_hlout5.addWidget(QtGui.QLabel("Expr. cycles:"))
            info_item_hlout5.addWidget(self.num_expr_cyc_sb)
            info_item_hlout5.addWidget(QtGui.QLabel(" "))
            
            self.num_expr_cyc_sb.valueChanged.connect(self.setExprCycles)
        
            #~ mon_expr_cb = QtGui.QCheckBox("Monitor expression ?")
            #~ info_item_hlout5.addWidget(mon_expr_cb)            
            #~ 
            #~ self.inc_temp_dsb.valueChanged.connect(self.updateAll)    
            
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
        #logging.debug(" expression - total duration =%f" %self.totalDuration())
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
            self.expr_temp_dsb.setValue(float(curr_temp))

    def initLMLNodes(self):
        """ Function doc """
        self.lml_parms = ET.SubElement(self.lml_node, "Parameters")
        self.lml_temp_parm = ET.SubElement(self.lml_parms, "Temperature")
        logging.debug("temp parameter created")
        print(self.lml_temp_parm)
        #self.setUUID()
        
    def updateLMLNodes(self):
        self.lml_temp_parm.set("temperature",str(self.expr_temp_dsb.value() ))
        pass
        
    def updateOverview(self):
        inoc_descr ="""The Expression subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","exp1",inoc_descr)
        
        par_text = "Inductor type : %s" % self.induct_type.currentText()
        self.exp.exp_ov.newPragraph("description","exp2",par_text)
        
        par_text = "Inductor volume: \t%d ul/well" % self.induct_vol_dsb.value()
        self.exp.exp_ov.newPragraph("description","exp3", par_text)
        
        par_text = "Expression time: \t%d min" % self.expr_dur_sb.value()
        self.exp.exp_ov.newPragraph("description","exp4", par_text)
        
        #self.exp.exp_ov.newPragraph("substances","sp2","Expr. L.B./Kan Medium %d ml + 12 ml dead vol. (fridge)" % self.inoc_vol_dsb.value() )
        
        total_inductor_vol = self.induct_vol_dsb.value() * 96.0 / 1000.0 * self.num_expression_plates #+ 10.0 # dead volume
        self.exp.exp_ov.newPragraph("substances","s1","Inductor %s : %d ml + 10 ml dead vol. (fridge)" % (self.induct_type.currentText(), total_inductor_vol) )
        
        #~ inoc_cond1 = "Num of plates to inoculate : \t%d" % self.num_plates_sb.value()
        #~ self.exp.exp_ov.newPragraph("description","p2",inoc_cond1)
        
        self.exp.exp_ov.newPragraph("devices","expdev1","Incubator %s" % self.incubation_expr_device )
   
    def setExprPlatesNum(self, num_plates):
        """ slot for changing number of expression plates (used by details dialog) """
        self.num_expr_plates = num_plates
        self.updateAll()
        
    def setExprCycles(self, num_cycles):
        """ slot for changing number of expression cycles (used by details dialog) """
        self.max_expr_cycles = num_cycles
        self.updateAll()
     
    def initSubProcessCode(self):
        # preparing containers and locations at system starting conditions
     
        # request required devices
        # required_devices = ["Thermo_carousel", "Thermo_cytomat_2"] 
        # self.requestDevices(required_devices)
        pass
        
    def updateSubProcessCode(self):
        self.expr_dur_lab.setText("("+ str(self.expr_dur_sb.value() * self.num_expr_cyc_sb.value() ) + ") min")
        self.steps_list = []                # resetting steps_list 
        # request plates
        self.tr_type = "ThermoTroughDw"
        self.exp.requestContainerFromStream(container_function="InductorTrough", container_type=self.tr_type, lidding_state="U", min_num = 1)
        self.expl_type = "Greiner96NwFb"
        self.exp.requestContainerFromStream(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", min_num = self.num_expr_plates) # max 6 plates ! - to be set by GUI
        
        curr_expl_func = "ExpressionPlate" + self.expl_type +"L"
        self.num_expression_plates =  self.exp.container_stream[curr_expl_func]
        
        if ( (self.num_expression_plates  % 2) > 0 ) and ( self.num_expression_plates != 1 ) :
            logging.error("expression process: !!!! wrong number of expression plates")
            
        # place in default location (device, stack, first_pos, int/ext)
        
        self.exp.defDefaultStartLocation(container_function="ExpressionPlate", container_type=self.expl_type, lidding_state="L", dev_pos=("Carousel",1,1,"ext"))
        self.exp.defDefaultStartLocation(container_function="InductorTrough", container_type=self.tr_type, lidding_state="U", dev_pos=("Cytomat_2",2,1,"int"))
        
        indtr_name = "InductorTrough%s%s%i" %(self.tr_type, "U", 1)
        
        # plates are now in place to do the first steps:

        if self.expr_temp_dsb.value() > 30.0 :
            self.incubation_expr_device = "Cytomat1550_1"
        elif self.expr_temp_dsb.value() > 20.0:
            self.incubation_expr_device = "Cytomat470"
        else :
            self.incubation_expr_device = "Cytomat1550_2"            
        
        self.steps_list += [ lap.BeginSubProcess(step_name="expression", \
                                            interpreter=lap.LA_ProcessElement.momentum32, \
                                            description="induction and expression of cultures") ]
        # induction
        self.steps_list += [lap.BeginLockedTask(step_name="Bravo"),lap.MovePlate(target_device="Bravo", position=4, container=[indtr_name])]
        curr_position = 6
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(i+1)
            self.steps_list += [ lap.MovePlate(target_device="Bravo", position=curr_position, container=[cont_name]) ]
            curr_position += 1 
        self.steps_list += [lap.RunExternalProtocol(target_device="Bravo", protocol="MDO_Induction4plates.pro")]
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(self.num_expression_plates-i)
            self.steps_list += [ lap.MovePlate(target_device="BufferNestsLBravo", lidded="L", container=[cont_name]) ]
        self.steps_list += [lap.MovePlate(target_device="Cytomat_2", container=[indtr_name])]
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(i+1)
            self.steps_list += [ lap.MovePlate(target_device=self.incubation_expr_device, lidded="L", container=[cont_name]) ]
        self.steps_list += [lap.EndLockedTask(step_name="Bravo")]
        
        # expression
        self.steps_list += [ lap.BeginLoop(max_iterations=self.max_expr_cycles, description="monitoring expression loop")]
        self.steps_list += [ lap.LogEntry(description="expression OD measurement")]
        self.steps_list += [ lap.BeginParallel()]
        for i in range(self.num_expression_plates):
            cont_name = curr_expl_func + str(i+1)
            self.steps_list += [ lap.BeginThread(), 
                                 lap.BeginLockedTask(step_name="OD"),
                                 lap.MovePlate(target_device="Omega", container=[cont_name]),
                                 lap.RunExternalProtocol(target_device="Omega", protocol="SPabsMW_600_660", container=[cont_name]),
                                 lap.MovePlate(target_device=self.incubation_expr_device, lidded="L", container=[cont_name]),
                                 lap.EndLockedTask(step_name="OD"),
                                 lap.Incubate(device=self.incubation_expr_device, incubation_duration=self.expr_dur_sb.value(), container=[cont_name] ), 
                                 lap.EndThread() ]
        self.steps_list += [ lap.EndParallel(), lap.EndLoop() ]
                                             
        self.steps_list +=  [ lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        self.incub_diag = ExpressionParameterDialog(parent_qgw=self)
        
class ExpressionParameterDialog(QtGui.QDialog):
    def __init__(self, parent_qgw = None, parent=None ):
        super(ExpressionParameterDialog, self).__init__(parent)
        self.parent_qgw = parent_qgw
        
        tabWidget = QtGui.QTabWidget()
        tabWidget.addTab(self.createGeneralTab(), "General")
        tabWidget.addTab(self.createExpressionDetailsTab(), "Expression Details")

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
        self.num_expr_plates_sb = QtGui.QSpinBox(container_gb)
        self.num_expr_plates_sb.setRange(2, 32)
        self.num_expr_plates_sb.setValue(4)
        info_item_hlout1.addWidget(QtGui.QLabel("Num. of plates:"))
        info_item_hlout1.addWidget(self.num_expr_plates_sb)
        info_item_hlout1.addWidget(QtGui.QLabel("96 well MTPs"))
        
        self.num_expr_plates_sb.valueChanged.connect(self.parent_qgw.setExprPlatesNum)
        
        container_layout.addLayout(info_item_hlout1)
        container_gb.setLayout(container_layout)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(container_gb)
        mainLayout.addStretch(1)
        general_tabw.setLayout(mainLayout)
        
        return(general_tabw)
            
    def createExpressionDetailsTab(self):
        details_tabw = QtGui.QWidget(self)
        
        expression_gb = QtGui.QGroupBox("Expression Details")
        expression_layout = QtGui.QVBoxLayout()
        
        logging.info("change status when unchecked - activation")
        info_item_hlout1 = QtGui.QHBoxLayout()
        self.num_expr_cyc_sb = QtGui.QSpinBox(expression_gb)
        self.num_expr_cyc_sb.setRange(1, 64)
        self.num_expr_cyc_sb.setValue(7)
        info_item_hlout1.addWidget(QtGui.QLabel("Expr. cycles:"))
        info_item_hlout1.addWidget(self.num_expr_cyc_sb)
        info_item_hlout1.addWidget(QtGui.QLabel(" "))
        
        self.num_expr_cyc_sb.valueChanged.connect(self.parent_qgw.setExprCycles)
        
        expression_layout.addLayout(info_item_hlout1)
        expression_gb.setLayout(expression_layout)
            
        #~ self.num_growth_cyc_sb.valueChanged.connect(self.updateAll)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(expression_gb)
        mainLayout.addStretch(1)
        details_tabw.setLayout(mainLayout)
        return(details_tabw)        
