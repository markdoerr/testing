#!/usr/bin/env python
# -*- coding: utf-8 -*-
#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: TALE_generator
# FILENAME: TALE_generator.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/10/24
# LASTMODIFICATION_DATE: 2014/04/31
#
# BRIEF_DESCRIPTION: Code Generator for creation of TALES
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

import logging
import re

from PyQt4 import Qt, QtCore, QtGui
import xml.etree.ElementTree as ET

from .. import lara_toolbox_item as ltbi
from .. import lara_process as lap
from .. import lara_material as lam
from ..generators import lara_html5_generator as lht5

class InitItem(ltbi.LA_ToolBoxItem):
    def __init__(self,parent=None):
        self.icon_text = "TALE" 
        self.item_name = "TALE"
        self.diagram_class = GenerateTALENProcess
        self.icon = QtGui.QIcon(':/linux/tasks/talen_jfk')
        super(InitItem, self).__init__(self.icon_text, self.icon, parent)

class GenerateTALENProcess(lap.LA_SubProcess):
    def __init__(self, experiment=None, position=None):
        super(GenerateTALENProcess, self).__init__(sp_name="TALE", experiment=experiment, position=position)
        
        self.TALE_sequence_nice = ""
        
        self.source_wells = []
        
        self.max_TALE_len = 24
        
        minSize = QtCore.QSizeF(10, 80)
        prefSize = QtCore.QSizeF(230, 100)
        maxSize = QtCore.QSizeF(250, 260)

        temp_item1 = self.createItem(minSize, prefSize, maxSize, "Sequence")
        #temp_item2 = self.createItem(minSize, prefSize, maxSize, "Inoculation")
        
        self.anchor_layout.addAnchor(temp_item1, QtCore.Qt.AnchorTop,self.anchor_layout , QtCore.Qt.AnchorTop)
        #anchor_layout.addAnchor(temp_item2, QtCore.Qt.AnchorTop,anchor_layout , QtCore.Qt.AnchorTop)
        
        # the description items are generated here
        self.updateOverview("")
        
        self.TALE_sequence_led.textChanged.connect(self.gen_seq)

    def createItem(self,minimum, preferred, maximum, name):
        # to handle line draw events make a move to connection pin during press and connect from there ...
        pw = QtGui.QGraphicsProxyWidget()
        
        w = QtGui.QGroupBox(name)
        w_vlayout = QtGui.QVBoxLayout(w)
        
        w_hlayout = QtGui.QVBoxLayout()
        self.TALE_sequence_led = QtGui.QLineEdit()
        #reg_exp = QtCore.QRegExp("[n]([+-][0-9]{1,3}){0,5}");
        self.TALE_sequence_led.setMaxLength(self.max_TALE_len)
        reg_exp = QtCore.QRegExp("[c,g,a,t,C,G,A,T]*");
        self.TALE_sequence_led.setValidator( QtGui.QRegExpValidator(reg_exp, self.TALE_sequence_led))
        self.TALE_sequence_lab = QtGui.QLabel()

        w_seq_descr_lab = QtGui.QLabel("TALEs")
        
        w_hlayout.addWidget(self.TALE_sequence_led)
        w_hlayout.addWidget(w_seq_descr_lab)
        w_hlayout.addWidget(self.TALE_sequence_lab)
        w_vlayout.addLayout(w_hlayout)
        
        #w.setWidget(QtGui.QPushButton(name))
        pw.setWidget(w)
        pw.setMinimumSize(minimum)
        pw.setPreferredSize(preferred)
        pw.setMaximumSize(maximum)
        pw.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        return(pw)
        
    def gen_seq(self, text=""):
        self.TALE_sequence_nice = self.TALE_sequence_led.text().toUpper()
        
        offset = 1
        for index in range(7,self.TALE_sequence_nice.length(),8):
            logging.debug("tale index %i" %index)
            self.TALE_sequence_nice.insert(index+1*offset, QtCore.QString(" ") )
            offset += 1
            
        self.TALE_sequence_lab.setText(self.TALE_sequence_nice)

        gt = LA_GenerateTALEN(self.TALE_sequence_led.text().toUpper().toAscii())
        
        self.updateOverview(gt.currentTALESequence())
        
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
        logging.debug("temp parameter created")
        print(self.lml_temp_parm)
       
    def updateOverview(self, curr_TALE_sequence):
        
        inoc_descr ="""The TALE design subprocess parameters are: """
        self.exp.exp_ov.newPragraph("description","p12",inoc_descr)
        
        inoc_cond1 = "Current TALE sequence : \t%s" % self.TALE_sequence_nice
        self.exp.exp_ov.newPragraph("description","p13",inoc_cond1)
        
        TALE_pipetting_scheme = "Pipetting Scheme for pipetting robot : \t%s" % curr_TALE_sequence
        self.exp.exp_ov.newPragraph("process","p14",TALE_pipetting_scheme)

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
                    lap.LoadTips(target_device="Bravo", columns=1, rows=1, column_pos=0, row_pos=7) ]
        
        target_row = 0
        for target_col in range(length(self.source_wells)/8 ):
            for source_well in self.source_wells: 
                self.steps_list += [
                    lap.Aspirate(device="Bravo", volume=10, column_pos=source_well[0], row_pos=source_well[0], container=[src_cont_name]),
                    lap.Dispense(device="Bravo", volume=10, column_pos=target_col, row_pos=target_row, container=[target_cont_name])]
        self.steps_list += [lap.UnloadTips(target_device="Bravo", columns=1, rows=1, column_pos=0, row_pos=7) ]
        
        # liquid transfer
       
        self.steps_list +=  [ lap.EndSubProcess()] 

    def mouseDoubleClickEvent(self, event):
        #self.incub_diag = TransferParameterDialog(parent_qgw=self)
        pass
       
class LA_GenerateTALEN():
    def __init__(self, TALE_seq):
        
        logging.warning("keep track of amounts taken from well !")
        
        self.max_TALE_len = 24
        max_subTALE_len = 8
        self.seq_out = ""
       

        if ( len(TALE_seq)  >  self.max_TALE_len ) :
            print("TALE sequence too long ")
            return()
                
        self.TALE_sequence_string = TALE_seq
        
        split_sequence = [list(self.TALE_sequence_string[i:i+max_subTALE_len]) for i in range(0, len(self.TALE_sequence_string), max_subTALE_len)]
        subTALE_num = len(split_sequence)
        
        print(split_sequence)
        
        # explaination of the table:
        # pairs of "Function":"Plate position"
        # Functions are: H = head, T = Tail, #nB = Number of base in octamer n
        # pTL-n = plasmid for generating the octamers
        
        TALE_table = { "HA":"A1",  "HT":"B1",   "HC":"D1", "HG":"C1",  # head
                        "1A":"A2",  "1T":"B2",   "1C":"C2", "1G":"D2",  # interface oligo with PST-F
                        "13A":"E2", "13T":"F2", "13C":"G2", "13G":"H2", # interface oligo with BSr-F for 3rd oligo
                        "2A":"A3",  "2T":"B3", "2C":"C3", "2G":"D3",
                        "3A":"A4",  "3T":"B4", "3C":"C4", "3G":"D4",
                        "4A":"A5",  "4T":"B5", "4C":"C5", "4G":"D5",
                        "5A":"A6",  "5T":"B6", "5C":"C6", "5G":"D6",
                        "6A":"A7",  "6T":"B7", "6C":"C7", "6G":"D7",
                        "7A":"A8",  "7T":"B8", "7C":"C8", "7G":"D8",
                        "8A":"A9",  "8T":"B9", "8C":"C9", "8G":"D9",    # interface oligo with PST-R
                        "82A":"E9", "82T":"F9", "82C":"G9", "82G":"H9", # oligos for 2nd octamer with Bsr-R 
                        "T2":"A10", "T3":"B10", "T4":"C10", "T5":"D10", # Tails with AAtll
                        "T6":"E10", "T7":"F10", "T8":"G10", 
                        "pTL-n":"H1"                                    # plasmid for the octamers
                         }
        
        curr_subTALE_num = 1
        print("\nInfo: '->' means 'take from well', H = head, T: = tail, 1 = interface oligo w. PST-F, 8 = interface oligo with PST-R \n")
        
        for curr_subTALE in split_sequence:
            self.seq_out = ""
            curr_base_pos = 1;
            for base in curr_subTALE:
                if (curr_subTALE_num == 1):
                    if (curr_base_pos == 1) :
                        base_pos = "H"
                    else:
                        base_pos = str(curr_base_pos)
                    source_well = TALE_table[base_pos+base]
                    self.seq_out += base_pos + "/" + base + "->" + source_well + "; "

                    self.source_wells += [ source_well[0]- ord('A'), source_well[1] ]
                    
                elif (curr_subTALE_num == 2):
                    if (curr_base_pos == max_subTALE_len) :
                        base_pos = str(curr_base_pos) + "2"
                    else:
                        base_pos = str(curr_base_pos)
                    self.seq_out += base_pos + "/" + base + "->" + TALE_table[base_pos+base] + "; "
                    
                elif (curr_subTALE_num == subTALE_num):
                    if (curr_base_pos == 1)  :
                        base_pos = str(curr_base_pos) + "3"
                        self.seq_out += base_pos + "/" + base + "->" + TALE_table[base_pos+base] + "; "
                        
                    elif (curr_base_pos == len(curr_subTALE)) :
                        base_pos = str(curr_base_pos)
                        self.seq_out += base_pos + "/" + base + "->" + TALE_table[base_pos+base] + "; " + "T:"+ base_pos + "->" + TALE_table["T"+str(curr_base_pos)] + "; "
                        
                    else:  
                        base_pos = str(curr_base_pos)
                        self.seq_out += base_pos + "/" + base + "->" + TALE_table[base_pos+base] + "; "
                        
                curr_base_pos += 1
                
            print("sub TALE seq. %s pipetting scheme: %s " % (curr_subTALE_num,self.seq_out ) )
            curr_subTALE_num += 1
            
    def currentTALESequence(self):
        return(self.seq_out)

        
        
if __name__ == "__main__":
    
    #logging.basicConfig(filename='lara_code_gen.log',level=logging.DEBUG)
    logging.basicConfig(format='%(levelname)s-%(funcName)s:%(message)s', level=logging.DEBUG)
    
#    app = QtGui.QApplication(sys.argv)
  
    #mc = LA_GenerateMomentumCode("MDO_test_process_V0.1")
    gt = LA_GenerateTALEN("GAACTTCTcTCgtcgATAGCCGTA")
 #   sys.exit(app.exec_())
    exit(0)
