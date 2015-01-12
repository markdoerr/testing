#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: vworks11_code_generator
# FILENAME: vworks11_code_generator.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/10/22
# LASTMODIFICATION_DATE: 2014/06/20
#
# BRIEF_DESCRIPTION: Code Generator for Agilent VWorks V11
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
import logging
import datetime
import xml.etree.ElementTree as ET

import singledispatch  # will be included in python 3.4 functools library; for python < 3.3 plese use pip install singledispatch

import lara_codegenerator as lcg
from .. import lara_process
from .. import lara_material as lam

#import lara_experiment

class LA_GenerateVWorks11Code(lcg.LA_CodeGenerator):
    """Code generator class for generating Agilent VWorks11 code using the visitor pattern"""

    def __init__(self, experiment, automation_sys, container_db, container_location_db ):
        super(LA_GenerateVWorks11Code, self).__init__(experiment)
        
        logging.debug("in v11")
        
        self.initDefDispatcher()

        self.experiment = experiment
        
        self.automation_sys = automation_sys
        self.container_db = container_db
        self.container_location_db = container_location_db

        self.first_dynamic_process = None
        self.static_container_dict = {}
        
        self.row_count = "8"
        self.column_count = "12"
        self.subset_config = "0"
        self.subset_type = "0"
        self.tip_type = "0"
        
        self.newVWorksFile()
        
        logging.debug("vw11: create new ")
        
        logging.debug("vw11: ps ")      
        
        self.traverse()             
        #~ self.processes()
        logging.debug("vw11: ps write ")
        self.writeVWorksXMLFile()
        
    def initDefDispatcher(self):
        self.generate = singledispatch.singledispatch(self.generate)
        self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
        self.generate.register(lara_process.EndSubProcess,self.genEndSubProcess)
        self.generate.register(lara_process.EndProcess,self.genEndProcess)
        self.generate.register(lara_process.MovePlate,self.genPlacePlate)
        self.generate.register(lara_process.LoadTips,self.genLoadTips)
        self.generate.register(lara_process.Aspirate,self.genAspirate)
        self.generate.register(lara_process.Dispense,self.genDispense)
        self.generate.register(lara_process.UnloadTips,self.genUnloadTips)
                
    def switchDispatcher(self, subprocess):
        logging.info("This could be implemented as a stack")
        if subprocess.interpreter() == lara_process.LA_ProcessElement.vworks11 :
            logging.debug("switching to vworks11 interpreter")
            self.vworks11Dispatcher()
            self.genBeginSubProcess(subprocess)
        else :
            logging.debug("switching off momentum interpreter")
            self.othersDispatcher()
            #self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
            
    def vworks11Dispatcher(self):
        self.generate = singledispatch.singledispatch(self.generate)
        self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
        self.generate.register(lara_process.EndSubProcess,self.genEndSubProcess)
        self.generate.register(lara_process.EndProcess,self.genEndProcess)
        self.generate.register(lara_process.MovePlate,self.genPlacePlate)
        self.generate.register(lara_process.LoadTips,self.genLoadTips)
        self.generate.register(lara_process.Aspirate,self.genAspirate)
        self.generate.register(lara_process.Dispense,self.genDispense)
        self.generate.register(lara_process.UnloadTips,self.genUnloadTips)
        
        #~ self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
        #~ self.generate.register(lara_process.BeginProcess,self.genBeginProcess)
        #~ self.generate.register(lara_process.BeginLockedTask,self.genBeginLockedTask)
        #~ self.generate.register(lara_process.EndLockedTask,self.genEndLockedTask)
        #~ self.generate.register(lara_process.ReadBarcode,self.genReadBarcode)
        #~ self.generate.register(lara_process.MovePlate,self.genPlacePlate)
        #~ self.generate.register(lara_process.AutoLoad,self.genAutoLoadDevice)
        #~ self.generate.register(lara_process.Dispense,self.genDispenseCombi)
        #~ self.generate.register(lara_process.EndProcess,self.genEndProcess)

        
    def othersDispatcher(self):
        self.generate = singledispatch.singledispatch(self.generate)
        
    def newVWorksFile(self):
        
        self.docType = "Velocity11"
        
        self.v11_root = ET.Element("Velocity11", version="2.0", md5sum="000000000000000000000000000000")
        self.v11_root.set("file", "Protocol_Data")
        
        #~ url1 = QtCore.QUrl("file://")
        #~ url2 = QtCore.QUrl("file:///home")
        #~ urls = [url1,url2]
        #new_filname_dia = QtGui.QFileDialog()
        #new_filname_dia.setSidebarUrls(urls);
        #self.vworks_xml_filename = new_filname_dia.getSaveFileName(None, 'Select New empty VWorks11 file to be used...','./','XML files (*.xml)')

        #ET.Element("html", lang="en")
        logging.debug("in v11 new file ")
        device_file="C:\VWorks Workspace\Device Files\Bravo96LT no Gripper.dev"
        
        fi_elm = ET.SubElement(self.v11_root, "File_Info", AllowSimultaneousRun="1", AutoLoadRacks="When the main protocol starts", 
                                    AutoUnloadRacks="0", AutomaticallyLoadFormFile="1", Barcodes_Directory="",
                                    DeleteHitpickFiles="1", Description="", Device_File=device_file,
                                    DynamicAssignPlateStorageLoad="0", FinishScript="", Form_File="",
                                    HandlePlatesInInstance="1", Notes="", PipettePlatesInInstanceOrder="0",
                                    Protocol_Alias="", StartScript="", Use_Global_JS_Context="0")
        
        self.procs_elm = ET.SubElement(self.v11_root, "Processes")
        self.mprocs_elm = ET.SubElement(self.procs_elm, "Main_Processes")
        
    def writeVWorksXMLFile(self):
        vworks_out_file_name = self.experiment.name() + ".xpro"
        try:
            ET.ElementTree(self.v11_root).write(vworks_out_file_name , encoding='UTF-8', xml_declaration=True, method="xml")
            logging.debug("lara: Experiment XML outputfile %s written" % vworks_out_file_name)
        except IOError:
            logging.Error("Cannot write Experiment XML outputfile %s !!!" % vworks_out_file_name)
           
    def generate(self,item):
        logging.debug("vw11 cg: generic item")
        #raise TypeError("Type not supported.")

    def genOthers(self, process_step):
        logging.debug("vw11 cg: others")
        
    def genBeginSubProcess(self, process_step):
        self.subprocess_name = process_step.name()
        self.pip_process = ET.SubElement(self.mprocs_elm, "Pipette_Process", Name="pipetting_subprocess1") # later use process_step.name()
        min_elm = ET.SubElement(self.pip_process, "Minimized")
        min_elm.text = "0"
        devs_elm = ET.SubElement(self.pip_process, "Devices")
        dev_elm = ET.SubElement(devs_elm,"Device", Device_Name="Bravo - 1", Location_Name="1")
        
    def addSubProcessDefinition(self):
        task_elm = ET.SubElement(self.first_dynamic_process, "Task", Name="Bravo::SubProcess")
        task_param = ET.SubElement(task_elm,"Parameters")
        ET.SubElement(task_param,"Parameter", Name="Sub-process name", Category="", Value=self.subprocess_name) 
        ET.SubElement(task_param, "Parameter", Category="Static labware configuration", Name="Display confirmation", Value='Don&apos;t display' ) 
        for plate_pos in range(1,9+1):
            try:
                logging.info("later use v11 plate type")
                ET.SubElement(task_param, "Parameter", Category="Static labware configuration", Name=str(plate_pos), Value=self.static_container_dict[plate_pos] ) 
            except KeyError:
                ET.SubElement(task_param, "Parameter", Category="Static labware configuration", Name=str(plate_pos), Value='&lt;use default&gt;' )
                
    def genEndSubProcess(self, process_step):
        #~ self.addSubProcessDefinition()
        self.othersDispatcher()
        
    def genEndProcess(self,process_step):
        logging.debug("This is THE END")

    def genPlacePlate(self,process_step):
        logging.debug("v11 -- placing plate")
        
        std_cont = lam.StandardContainer()
        proc_elm = ET.SubElement(self.mprocs_elm, "Process")

        min_elm = ET.SubElement(proc_elm, "Minimized")
        min_elm.text = "0"
        
        task_elm = ET.SubElement(proc_elm, "Task", Name="BuiltIn::Place Plate")
        devs_elm = ET.SubElement(task_elm, "Devices")
        dev_elm = ET.SubElement(devs_elm,"Device", Device_Name="Bravo - 1", Location_Name=process_step.platePosition())
        en_bakup = ET.SubElement(task_elm, "Enable_Backup")
        en_bakup.text  = "0"
        task_disa = ET.SubElement(task_elm, "Task_Disabled")
        task_disa.text = "0"
        has_breakp = ET.SubElement(task_elm, "Has_Breakpoint")
        has_breakp.text= "0"
        adv_settings = ET.SubElement(task_elm,"Advanced_Settings")
        ET.SubElement(task_elm, "TaskScript", Name="TaskScript", Value="")
        task_param = ET.SubElement(task_elm,"Parameters")
        ET.SubElement(task_param,"Parameter", Name="Device to use", Category="", Value= "Bravo - 1") 
        ET.SubElement(task_param, "Parameter", Name="Location to use", Category="", Value=process_step.platePosition() ) 
        
        plate_params = ET.SubElement(proc_elm,"Plate_Parameters")
        
        ET.SubElement(plate_params, "Parameter", Name="Plate name", Value=process_step.container(0)) 
        ET.SubElement(plate_params, "Parameter", Name="Plate type", Value=std_cont.stdContainerFullName(process_step.contType())) 
        ET.SubElement(plate_params, "Parameter", Name="Simultaneous plates", Value="1") 
        ET.SubElement(plate_params, "Parameter", Name="Plates have lids", Value="0") 
        ET.SubElement(plate_params, "Parameter", Name="Plates enter the system sealed", Value="0") 
        ET.SubElement(plate_params, "Parameter", Name="Use single instance of plate", Value="0") 
        ET.SubElement(plate_params, "Parameter", Name="Automatically update labware", Value=process_step.isStatic()) 
        ET.SubElement(plate_params, "Parameter", Name="Enable timed release", Value="0") 
        ET.SubElement(plate_params, "Parameter", Name="Release time", Value="30") 
        ET.SubElement(plate_params, "Parameter", Name="Barcode filename", Value="No Selection") 
        ET.SubElement(plate_params, "Parameter", Name="Has header", Value="")
        ET.SubElement(plate_params, "Parameter", Name="Barcode or header South", Value="No Selection") 
        ET.SubElement(plate_params, "Parameter", Name="Barcode or header West", Value="No Selection") 
        ET.SubElement(plate_params, "Parameter", Name="Barcode or header North", Value="No Selection") 
        ET.SubElement(plate_params, "Parameter", Name="Barcode or header East", Value="No Selection") 
        quarantine_state = ET.SubElement(proc_elm,"Quarantine_After_Process")
        quarantine_state.text = "0"

        sp_task_elm = ET.SubElement(proc_elm, "Task", Name="Bravo::SubProcess")
        sp_task_param1 = ET.SubElement(sp_task_elm,"Parameters")
        ET.SubElement(sp_task_param1,"Parameter", Name="SubProcess_Name", Pipettor='1', Value= "pipetting_subprocess1", Centrifuge='0')
                             
        if process_step.isStatic() == "1":
            self.static_container_dict[process_step.platePosition()] = std_cont.stdContainerFullName(process_step.contType())
            logging.debug(process_step.container(0) )
        else :      # dynamic container
            self.first_dynamic_process = proc_elm
            sp_task_param2 = ET.SubElement(sp_task_elm,"Parameters")
            ET.SubElement(sp_task_param2,"Parameter", Name='Display confirmation', Category='Static labware configuration',  Value='Don&apos;t display')
            print(self.static_container_dict)
            for i in range(9) :
                if str(i+1) in self.static_container_dict:
                    ET.SubElement(sp_task_param2,"Parameter", Name=str(i+1), Category='Static labware configuration', Value=self.static_container_dict[str(i+1)])
                else :
                    ET.SubElement(sp_task_param2,"Parameter", Name=str(i+1), Category='Static labware configuration', Value='&amp;lt;use default&amp;gt;')

    def genLoadTips(self,process_step):
        logging.debug("v11 -- loading tips") 
        
        self.row_count = str(process_step.rows())
        self.column_count = str(process_step.columns())

        self.row_pos = str(process_step.rowPos())
        self.column_pos = str(process_step.columnPos())
        
        if (process_step.columns() > 1 ) or (process_step.rows() > 1 ):
            self.subset_config = "0"
            self.subset_type = "1"
        elif (process_step.columns() == 1 ) or (process_step.rows() == 1 ):
            self.subset_config = "1"
            self.subset_type = "4"
        else :
            self.subset_config = "0"
            self.subset_type = "0"
        
        self.setHeadMode(process_step)
        tips_on_task = ET.SubElement(self.pip_process, "Task", Name="Bravo::secondary::Tips On", Task_Type="16")
        params = ET.SubElement(tips_on_task, "Parameters")
        param = ET.SubElement(params, "Parameter", Name="Location, plate", Category="",  Value="tip_box" )
        param = ET.SubElement(params, "Parameter", Name="Location, location", Category="",  Value="<auto-select>" )
        param = ET.SubElement(params, "Parameter", Name="Well selection", Category="Properties") #  Value=self.metadata_root)
        param.set("Value",  self.selectTips( self.row_pos, self.column_pos ) )
        
        pipette_head = ET.SubElement(tips_on_task, "PipetteHead", Name="96LT, 200 &x2b5;L Series III", AssayMap="0", Disposable="1", HasTips="1", MaxRange="251", MinRange="-41" )
        ET.SubElement(pipette_head, "PipetteHeadMode", Channels="0", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)

    def genAspirate(self,process_step):
        #~ logging.debug("v11 -- loading tips")

        aspirate_task = ET.SubElement(self.pip_process, "Task", Name="Bravo::secondary::Aspirate", Task_Type="1")
        params = ET.SubElement(aspirate_task, "Parameters")
        param = ET.SubElement(params, "Parameter", Name="Location, plate", Category="",  Value=process_step.container(0) )
        param = ET.SubElement(params, "Parameter", Name="Location, location", Category="",  Value="<auto-select>" )
        param = ET.SubElement(params, "Parameter", Name="Volume", Category="Volume",  Value="10" )
        param = ET.SubElement(params, "Parameter", Name="Distance from well bottom", Category="Properties",  Value="30" )
        param = ET.SubElement(params, "Parameter", Name="Well selection", Category="Properties") #  Value=self.metadata_root)
        param.set("Value",  self.selectTips(str(process_step.columnPos()), str(process_step.rowPos())) )
        
        pipette_head = ET.SubElement(aspirate_task, "PipetteHead", Name="96LT, 200 &x2b5;L Series III", AssayMap="0", Disposable="1", HasTips="1", MaxRange="251", MinRange="-41" )
        ET.SubElement(pipette_head, "PipetteHeadMode", Channels="0", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)

    def genDispense(self,process_step):
        #~ logging.debug("v11 -- loading tips") 
        aspirate_task = ET.SubElement(self.pip_process, "Task", Name="Bravo::secondary::Dispense", Task_Type="2")
        params = ET.SubElement(aspirate_task, "Parameters")
        param = ET.SubElement(params, "Parameter", Name="Location, plate", Category="",  Value=process_step.container(0) )
        param = ET.SubElement(params, "Parameter", Name="Location, location", Category="",  Value="<auto-select>" )
        param = ET.SubElement(params, "Parameter", Name="Volume", Category="Volume",  Value="10" )
        param = ET.SubElement(params, "Parameter", Name="Distance from well bottom", Category="Properties",  Value="30" )
        param = ET.SubElement(params, "Parameter", Name="Well selection", Category="Properties") #  Value=self.metadata_root)
        param.set("Value",  self.selectTips(str(process_step.columnPos()), str(process_step.rowPos())) )
        
        pipette_head = ET.SubElement(aspirate_task, "PipetteHead", Name="96LT, 200 &x2b5;L Series III", AssayMap="0", Disposable="1", HasTips="1", MaxRange="251", MinRange="-41" )
        ET.SubElement(pipette_head, "PipetteHeadMode", Channels="0", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)

    def genUnloadTips(self,process_step):
        logging.debug("v11 -- unloading tips")
        self.row_pos = str(process_step.rowPos())
        self.column_pos = str(process_step.columnPos())
        tips_off_task = ET.SubElement(self.pip_process, "Task", Name="Bravo::secondary::Tips Off", Task_Type="32")
        params = ET.SubElement(tips_off_task, "Parameters")
        param = ET.SubElement(params, "Parameter", Name="Location, plate", Category="",  Value="tip_box" )
        param = ET.SubElement(params, "Parameter", Name="Location, location", Category="",  Value="<auto-select>" )
        param = ET.SubElement(params, "Parameter", Name="Well selection", Category="Properties") #  Value=self.metadata_root)
        param.set("Value",  self.selectTips(self.row_pos, self.column_pos) )
        
        pipette_head = ET.SubElement(tips_off_task, "PipetteHead", Name="96LT, 200 &x2b5;L Series III", AssayMap="0", Disposable="1", HasTips="1", MaxRange="251", MinRange="-41" )
        ET.SubElement(pipette_head, "PipetteHeadMode", Channels="0", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)
            
    def selectTips(self, row_pos="0", column_pos="0"):
        self.metadata_root = ET.Element("Velocity11", version="1.0", md5sum="000000000000000000000000000000")
        self.metadata_root.set("file", "MetaData")
        
        well_selection = ET.SubElement(self.metadata_root, "WellSelection", OnlyOneSelection="1", StartingQuadrant="1")
        wells = ET.SubElement(well_selection, "PipetteHeadMode", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)
        wells = ET.SubElement(well_selection, "Wells")
        well = ET.SubElement(wells, "Well", Column=column_pos, Row=row_pos)
        well_selection = "<?xml version='1.0' encoding='ASCII' >" #"&lt;?xml version=&apos;1.0&apos; encoding=&apos;ASCII&apos; ?&gt;"
        well_selection += ET.tostring(self.metadata_root, method="xml")
        
        print(well_selection)
        return(well_selection)
        
    def setHeadMode(self,process_step):
        set_head_mode_task = ET.SubElement(self.pip_process, "Task", Name="Bravo::secondary::Set Head Mode", Task_Type="512")
        params = ET.SubElement(set_head_mode_task, "Parameters")
        param = ET.SubElement(params, "Parameter", Name="Head mode", Category="") 
        
        self.metadata_root = ET.Element("Velocity11", version="1.0", md5sum="000000000000000000000000000000")
        self.metadata_root.set("file", "MetaData")
        
        ET.SubElement(self.metadata_root, "PipetteHeadMode", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)
        
        hm_param = "<?xml version='1.0' encoding='ASCII' >"
        hm_param += ET.tostring(self.metadata_root, method="xml")
        param.set("Value",  hm_param )
        
        pipette_head = ET.SubElement(set_head_mode_task, "PipetteHead", Name="96LT, 200 &x2b5;L Series III", AssayMap="0", Disposable="1", HasTips="1", MaxRange="251", MinRange="-41" )
        ET.SubElement(pipette_head, "PipetteHeadMode", Channels="0", ColumnCount=self.column_count, RowCount=self.row_count, SubsetConfig=self.subset_config, SubsetType=self.subset_type, TipType=self.tip_type)
                    
if __name__ == "__main__":
    
    #logging.basicConfig(filename='lara_code_gen.log',level=logging.DEBUG)
    logging.basicConfig(format='%(levelname)s-%(funcName)s:%(message)s', level=logging.DEBUG)
    
    app = QtGui.QApplication(sys.argv)
  
    #mc = LA_GenerateMomentumCode("MDO_test_process_V0.1")
    vwcg = LA_GenerateVWorks11Code("MDO_vworks_test.xml")
    sys.exit(app.exec_())
    #exit(0)
