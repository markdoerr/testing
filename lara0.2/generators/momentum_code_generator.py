#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: momentum_code_generator
# FILENAME: momentum_code_generator.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.4
#
# CREATION_DATE: 2013/05/14
# LASTMODIFICATION_DATE: 2014/11/21
#
# BRIEF_DESCRIPTION: Code Generator for Thermo Scientific Momentum
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
import datetime
import singledispatch  # will be included in python 3.4 functools library; for python < 3.3 plese use pip install singledispatch

import lara_codegenerator as lcg
from .. import lara_process
from .. import lara_material as lam

#import lara_experiment

class LA_GenerateMomentumCode(lcg.LA_CodeGenerator):
    """Code generator class for generating Thermo Fisher Momentum (Ver. 3.2.2) code using the visitor pattern"""

    def __init__(self, experiment, automation_sys, container_db, container_location_db ):
        super(LA_GenerateMomentumCode, self).__init__(experiment)
        
        self.initDefDispatcher()

        self.experiment = experiment
        
        self.automation_sys = automation_sys
        self.container_db = container_db
        self.container_location_db = container_location_db
        
        self.lockset_global = set()
        self.lockset_local = set()
        self.proc_var_dict = {}
        self.loop_counter = 1
        self.curr_loop_lock_var = ""
        self.incubation_counter = 1
        self.centrifugation_counter = 1
        self.primeVolume_counter = 1
        self.dispenseVolume_counter = 1
        self.tool_container = False
        
        self.current_user = "MDO"
        
        self.momentum_loop_containers = ""    
        self.momentum_tool_containers = ""
        
        self.momentum_profileHead = ""
        self.momentum_profileDevices = ""
        self.momentum_profileVariables = ""
        self.momentum_processHead = ""
        self.momentum_processContainers = ""
        self.momentum_process_variables = ""
        self.momentum_process = ""
        
        self.momentum_experiment_head = ""
        self.momentum_experiment_start_end = ""
        self.momentum_nest_restrictions = ""
        self.momentum_experiment_tail = ""
        
        # experiment should be generated before process (with original nest locations) 
        self.experiment_head()
        self.experiment_nest_restrictions()
        self.experiment_start_end()
        self.experimentTail()
        
        self.profileHead()
        self.profileDevices()
        logging.debug("mcg: ps devs" )

        self.processHead()
        logging.debug("mcg: outputfile is %s, now traversing ...", self.experiment.name() )
        # core process generation, traversing trough subprocess list
        self.traverse()
        
        self.process_variables()
        logging.debug("mcg: ps var" )
        
        self.processContainers()
        logging.debug("mcg: ps container" )
        
        self.profileVariables()    # needs to be processed after process !!
        logging.debug("mcg: prof var" )

        self.writeProcess()
        self.writeExperiment()
        logging.debug("mcg: ps write" )
        
    def initDefDispatcher(self):
        self.generate = singledispatch.singledispatch(self.generate)
        self.generate.register(lara_process.LogEntry,self.genLogEntry)
        self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
        self.generate.register(lara_process.BeginProcess,self.genBeginProcess)
        self.generate.register(lara_process.BeginLockedTask,self.genBeginLockedTask)
        self.generate.register(lara_process.EndLockedTask,self.genEndLockedTask)
        self.generate.register(lara_process.BeginLoop,self.genBeginLoop)
        self.generate.register(lara_process.EndLoop,self.genEndLoop)
        self.generate.register(lara_process.BeginParallel,self.genBeginParallel)
        self.generate.register(lara_process.EndParallel,self.genEndParallel)
        self.generate.register(lara_process.BeginThread,self.genBeginThread)
        self.generate.register(lara_process.EndThread,self.genEndThread)
        self.generate.register(lara_process.Delay,self.genDelay)
        self.generate.register(lara_process.ReadBarcode,self.genReadBarcode)
        self.generate.register(lara_process.MovePlate,self.genLoadDevice)
        self.generate.register(lara_process.AutoLoad,self.genAutoLoadDevice)
        self.generate.register(lara_process.Dispense,self.genDispenseCombi)
        self.generate.register(lara_process.Shake,self.genShake)
        self.generate.register(lara_process.Incubate,self.genIncubate)
        self.generate.register(lara_process.RunExternalProtocol,self.genRunProtocol)
        self.generate.register(lara_process.Centrifuge,self.genCentrifuge) 
        self.generate.register(lara_process.EndProcess,self.genEndProcess)
        
    def generate(self,item):
        logging.debug("mcg: generic item")
        #raise TypeError("Type not supported.")

    def switchDispatcher(self, subprocess):
        logging.info("This could be implemented as a stack")
        if subprocess.interpreter() == lara_process.LA_ProcessElement.momentum32 :
            logging.debug("switching to momentum interpreter")
            self.genBeginSubProcess(subprocess)
        else :
            logging.debug("switching off momentum interpreter")
            #self.generate.register(lara_process.BeginSubProcess,self.switchDispatcher)
            
    def insertLogEntry(self, step, log_entry=""):
	self.lockset_global.add("logLock")
        logfile_entry = """\t\tcomment ('"{log_entry}({step_name})::{description}"');
\t\tacquire ({lock_name}) ;\n\n
\t\tset log_entry= '"\\\\""+Experiment + "_" + uid + "\\\\";\\\\"" + Format(Now, "yyMMdd_HHmmss") +"\\\\";\\\\"" + curr_user + "\\\\";\\\\"{step_name}{log_entry}{description} "';\n
\t\tFile_Mgr [Write File]
\t\t\t(InputVariable = 'log_entry', FileType = 'Text File', 
\t\t\tOutputFileRaw = 'status_filename', Header = 'No', FileWriteMode = 'Append', 
\t\t\tDisplayErrors = 'Yes', WaitDuration = '00:00:01', Duration = '00:00:01', 
\t\t\tComments = '', Enabled = 'Yes') ;\n
\t\trelease ({lock_name});\n\n""".format(step_name=step.name(), log_entry=log_entry, description=step.description(), lock_name="logLock")
        return(logfile_entry)
        
    def genLogEntry(self, process_step):
         self.momentum_process += self.insertLogEntry(process_step)

    def genBeginProcess(self, begin_process):
	self.lockset_global.add("logLock")
        logging.debug("This is just the beginning")
        #~ set log_filename = '"C:\\\\Users\\\\Thermo\\\\Documents\\\\MDO\\\\momentum_logfiles\\\\"  + Format(Now, "yyMMdd") +  Experiment +"_log"+ "\\\\"+Format(Now, "yyMMdd_HHmm")+"_log.txt"' ;
        self.momentum_process += """\n\t\t// setting up unique process identifier\n
\t\tacquire ({lock_name}) ;\n\n
\t\tset uid = '""+Format(Now, "yyMMddHHmmss")' ;
\t\tset log_filename = '"C:\\\\\\\\Users\\\\\\\\Thermo\\\\\\\\Documents\\\\\\\\MDO\\\\\\\\momentum_logfiles\\\\\\\\"  + Format(Now, "yyMMdd") +  Experiment +"_log"+ "\\\\\\\\"+Format(Now, "yyMMdd_HHmm")+"_log.txt"' ;
\t\t// set status_filename = '"D:\\\\robot_data\\\\momentum_status\\\\current_momentum_status.txt"' ;
\t\tset status_filename = '"C:\\\\\\\\Users\\\\\\\\Public\\\\\\\\Documents\\\\\\\\MDO\\\\\\\\current_momentum_status.txt"' ;\n
\t\tset log_entry= '"\\\\""+Experiment + "_" + uid + "\\\\";\\\\"" + Format(Now, "yyMMdd_HHmmss") + "\\\\";\\\\"" +  curr_user + "\\\\";\\\\"" +"=== Started at: " + Format(Now, "yy/MM/dd HH:mm:ss") + "===" + "|Profile:" +  Profile';\n              
\t\t//File_Mgr [Write File]
\t\t\t//(InputVariable = 'log_entry', FileType = 'Text File', 
\t\t\t//OutputFileRaw = 'log_filename', Header = 'Yes', FileWriteMode = 'Append', 
\t\t\t//DisplayErrors = 'Yes', WaitDuration = '00:00:01', Duration = '00:00:01', 
\t\t\t//Comments = '', Enabled = 'Yes') ;\n
\t\t//File_Mgr [Write File]
\t\t\t//(InputVariable = 'log_entry', FileType = 'Text File', 
\t\t\t//OutputFileRaw = 'status_filename', Header = 'No', FileWriteMode = 'Append', 
\t\t\t//DisplayErrors = 'Yes', WaitDuration = '00:00:01', Duration = '00:00:01', 
\t\t\t//Comments = '', Enabled = 'Yes') ;\n\n
\t\trelease ({lock_name}) ;\n\n""".format(lock_name="logLock")

    def genEndProcess(self,process_step):
        logging.debug("This is THE END")
        self.momentum_process += self.insertLogEntry(process_step, "========== FIN =============") +"\t}\n}\n" # could generate trouble with locking of other processes ...
        #self.momentum_process += "\t}\n}\n" 

    def genBeginSubProcess(self, begin_process):
        logging.debug("generating begin subprocess - room for logging - name: " )
        self.momentum_process += self.insertLogEntry(begin_process, "=== Begin Subprocess ===")

    def genEndSubProcess(self,process_step):
        logging.debug("End of subprocess - should now switch back to upper subprocess")
        self.momentum_process += self.insertLogEntry(begin_process, "--- End Subprocess ---")
                                
    def genBeginLockedTask(self,process_step):
        lock_name = process_step.name() + "Lock"
        if process_step.scope() == "global":
            self.lockset_global.add(lock_name)
        if process_step.scope() == "local":
            self.lockset_local.add(lock_name)
        self.momentum_process += """\t\tacquire ({lock_name}) ;\n\n""".format(lock_name=lock_name)
    
    def genEndLockedTask(self,process_step):
        lock_name = process_step.name() + "Lock"
        self.momentum_process += """\t\trelease ({lock_name}) ;\n\n""".format(lock_name=lock_name)
        
    def genBeginLoop(self,process_step):
        self.momentum_loop_containers  += """\t\t\tplate counterPlate{loop_counter}
                            ( NumberOfWellRows = '8', NumberOfWellColumns ='12',
                                WellNumberingMethod = 'Rows', BarCodeRegularExpression = '', BarCodeFile = '',
                                BarCodeAutoExpression = '"NC" + Format(Now, "yyMMddHHmmss") + "_" + Format(WallClock, "fff")',
                                GripOffset = 'Identity', GripForce = '0',  MoverLiddingGripOffset = '3.0',
                                Height ='15.0', StackHeight = '13.13', WithLidOffset = '-5', WithLidHeight = '17',
                                Thickness = '1', SealThickness = '0', SetSize = '{max_iterations}',
                                Attributes = '' );\n""".format(loop_counter=self.loop_counter, max_iterations=process_step.maxIterations())
                
        max_loop_var = "max_loop%i" %self.loop_counter
        self.proc_var_dict[max_loop_var] = [str(process_step.maxIterations()), "Integer"]
        self.proc_var_dict["loop_counter"] = ["0", "Integer"]
        loop_lock_var = "loopLock%i" % self.loop_counter
        self.curr_loop_lock_var = loop_lock_var
        self.lockset_local.add(loop_lock_var)
        self.momentum_process += """\t\tcomment ('{comment}') ;\n
\t\tforeach counterPlate{loop_counter} (ReverseContainerSet = 'No', DelayBetweenLoops = '00:00:01')\n\t\t{{
\t\t\tcomment ('forcing into a serial process') ; \n
\t\t\tacquire ({loop_lock_var}) ;\n
\t\t\tif ('loop_counter <  {max_loop_var}')\n\t\t\t{{\n""".format(loop_counter=self.loop_counter, comment=process_step.description(), 
                                                                    loop_lock_var=loop_lock_var, max_loop_var=max_loop_var)
        self.loop_counter += 1

    def genEndLoop(self,process_step):
        self.momentum_process += """\t\t\t}} //if\n\t\t\telse
                                {{\n\t\t\tcomment ('skip when max. number of iterations is reached') ;\t\t\t}}\n
                                set loop_counter = 'loop_counter + 1' ;\n
                                comment ('one reference to a counterPlate is required by the program (=workaround)') ;\n
                                virtualStorage [Load]
                                        (Comments = '', Enabled = 'Yes')
                                        counterPlate{loop_counter} 'Unlidded' ;\n
                                release ({loop_lock_var}) ;\n\t\t}} //end loop/foreach \n\t\tset loop_counter = 'loop_counter = 0';\n\n""".format(loop_counter=self.loop_counter-1,loop_lock_var=self.curr_loop_lock_var)

    def genBeginParallel(self,process_step):
        self.momentum_process += "\t\t\tparallel\n\t\t\t{\n"

    def genEndParallel(self,process_step):
        self.momentum_process += "\t\t\t} //end parallel\n"
        
    def genBeginThread(self,process_step):
        self.momentum_process += "\t\t\t\tbranch\n\t\t\t\t{\n"
        
    def genEndThread(self,process_step):
        self.momentum_process += "\t\t\t\t} //end branch\n"

    def genDelay(self,process_step):
        self.momentum_process += """\t\t\tdelay (MinDelay = '00:00:00', MaxDelaySpecified = 'Yes', RequestedMaxDelay = '00:00:45', 
                SpoilIfMaxDelayExceeded = 'False') ;\n"""

    def genReadBarcode(self,process_step):
        self.momentum_process += "\t\tBCR [Scan Barcode]\n\t\t\t(" \
                                + "NoReadWarningWhenUnattended = 'No', OverrideUnattendedMode = 'No', \n\t\t\t" \
                                + "RunOnAbortedIteration = 'No', Duration = '00:00:20', " \
                                + "Comments = '', Enabled = 'Yes')\n\t\t\t" \
                                + process_step.container(0) + " '%s' in 'Nest' ;\n\n" % process_step.lidding()
                                
                                
    def genShake(self,process_step):
        nest_location = "in 'Nest'"
        self.momentum_process += "\t\t" + process_step.device() + " [Shake]\n\t\t\t(" \
                        + "ShakeDistance = '2', ShakeFrequency = '13', \n\t\t\t\t" \
                                                + "RunOnAbortedIteration = 'No', Duration = '00:01:01',\n\t\t\t\t" \
                        + "Comments = '')\n\t\t\t" \
                        + process_step.container(0) + " '" + process_step.lidding() + "' " + nest_location + ";\n\n"
                                
    def genLoadDevice(self,process_step):
        single_nest_devices = set(["Omega","Varioskan", "Combi"])
        multi_nest_devices = set(["Bravo"])
        
        if process_step.device() in single_nest_devices:
            nest_location = "' in 'Nest"
        elif process_step.device() in multi_nest_devices:
            nest_location = "' in 'Nest " + process_step.platePosition()
        else :
            nest_location = ""
        self.momentum_process += "\t\t" + process_step.device() + " [Load]\n\t\t\t(" \
                        + "Comments = '', Enabled = 'Yes')\n\t\t\t" \
                        + process_step.container(0) + " '" + process_step.lidding() + nest_location + "' ;" \
                        + "\n\n"

    def genAutoLoadDevice(self,process_step):
        nest_location = "' in 'Nest " + self.container_location_db.autoLoad(process_step.container(0),process_step.device(),1,"ext")
        plate_orientation = ""
        if process_step.device() == "CombiHotel":
            plate_orientation = "_" + process_step.orientation()
        elif process_step.device() == "Rotanta":
            nest_location = "' in 'Transfer Nest " + self.container_location_db.autoLoad(process_step.container(0),process_step.device(),1,"ext") + " - System Path"
            
        self.momentum_process += "\t\t" + process_step.device() + " [Load]\n\t\t\t" \
                        + "(Comments = '', Enabled = 'Yes')\n\t\t\t" \
                        + process_step.container(0) + " '"+ process_step.lidding() + nest_location \
                        + plate_orientation +"' ;" \
                        + "\n\n"
                        
    def genDispenseCombi(self,process_step):
        logging.warning("!!! adujust dispense hight depending on container type !!!")
        medium = "medium%s" % process_step.liquidsChannel()
        self.proc_var_dict[medium] = [str(process_step.liquidsChannel()), "String"]
        combi_prime_vol = "combi_prime_vol%s" % self.primeVolume_counter
        self.proc_var_dict[combi_prime_vol] = [str(process_step.primeVolume()), "Double"]
        self.primeVolume_counter += 1
        combi_vol = "combi_vol%s" % self.dispenseVolume_counter
        self.proc_var_dict[combi_vol] = [str(process_step.volume()), "Double"]
        self.dispenseVolume_counter += 1
        if process_step.mode() == "Dispense":
            self.momentum_process += """\t\tCombi [Dispense]\n\t\t\t(
\t\t\tPlateType = '96 standard (15mm)', DispenseOrder = 'No', 
\t\t\tFluid = ${medium}, PrimeVolume = ${combi_prime_vol},
\t\t\tPrimeEnabled = 'Yes', PumpSpeed = '50',
\t\t\tDispenseHeight = '1700', DispenseXOffset = '0',
\t\t\tDispenseYOffset = '0', DefaultToColumn1 = 'Yes',
\t\t\tColumn_1 = ${combi_vol}, Column_2 = ${combi_vol}, Column_3 = ${combi_vol}, 
\t\t\tColumn_4 = ${combi_vol}, Column_5 = ${combi_vol}, Column_6 = ${combi_vol}, 
\t\t\tColumn_7 = ${combi_vol}, Column_8 = ${combi_vol}, Column_9 = ${combi_vol}, 
\t\t\tColumn_10 = ${combi_vol}, Column_11 = ${combi_vol}, Column_12 = ${combi_vol},
\t\t\tRunOnAbortedIteration = 'No', Duration = '00:00:45', 
\t\t\tComments = '', Enabled = 'Yes')
\t\t\t{container} 'Unlidded' in 'Nest' ; \n\n\n""".format(medium=medium,combi_prime_vol=combi_prime_vol, combi_vol=combi_vol, container=process_step.container(0))
        elif process_step.mode() == "Empty":
             self.momentum_process += """\t\tCombi [Empty]
                                                (Volume = '{volume}', Fluid = ${medium}, RunOnAbortedIteration = 'No', 
                                                Duration = '00:00:30', Comments = '', Enabled = 'Yes') ;\n""".format(volume=process_step.emptyVolume(), medium=medium )
        elif process_step.mode() == "Prime":
             self.momentum_process += """\t\tCombi [Prime]
                                                (Volume = '{volume}', Fluid = ${medium}, RunOnAbortedIteration = 'No', 
                                                Duration = '00:00:30', Comments = '', Enabled = 'Yes') ;\n""".format(volume=process_step.primeVolume(), medium=medium )
                               
    def genIncubate(self,process_step):
        curr_time_factor_var = "incubation_duration_factor%i" % self.incubation_counter 
        
        self.proc_var_dict["incubation_duration"] = ["00:01:00", "Duration"]
        self.proc_var_dict["curr_incubation_duration"] = ["00:01:00", "Duration"]
        
        self.proc_var_dict[curr_time_factor_var] = [str(process_step.incubationDuration()), "Integer"]
        
        self.momentum_process += "\t\tset curr_incubation_duration = 'incubation_duration * " + curr_time_factor_var + "' ;\n"
        self.momentum_process += "\t\t" + process_step.device() +" [Incubate]\n\t\t\t(" \
                                + "RunOnAbortedIteration = 'No', Duration = $curr_incubation_duration , MinDelay = '00:00:00', MaxDelaySpecified = 'No',"\
                                + "Comments = '', Enabled = 'Yes')\n\t\t\t" \
                                + process_step.container(0) + " 'Lidded';" \
                                + "\n\n"
        self.incubation_counter += 1
        
    def genRunProtocol(self,process_step):

        if process_step.device() == "Omega":
            omega_outputfile_name = "<BARCODE>" #% self.current_user  # C:\\\\tmp 
            self.proc_var_dict["omega_input_path"] = ["B:\\\\Program Files\\\\BMG\\\\Omega\\\\User\\\\Definit", "String"] # C:\\\\tmp
            omega_out_path = "\\\\\\\\Thermo-pc\\\\bmg\\\\%s\\\\" % self.current_user
            self.proc_var_dict["omega_output_path"] = [omega_out_path, "String"] # C:\\\\tmp
            self.proc_var_dict["omega_outputfile"] = [omega_outputfile_name, "String"] 
            self.momentum_process += """\t\tOmega [Run Protocol]
\t\t\t(ProtocolName = '{protocol_name}', 
\t\t\tInputPath = $omega_input_path, 
\t\t\tOutputPath = $omega_output_path, 
\t\t\tOutputName = $omega_outputfile, 
\t\t\tRunOnAbortedIteration = 'No', Duration = '00:01:01', 
\t\t\tComments = '', Enabled = 'Yes')
\t\t\t{container} 'Unlidded' in 'Nest' ;\n\n""".format(protocol_name=process_step.protocol(), container=process_step.container(0))
        if process_step.device() == "Varioskan":
            varioskan_outputfile_name = "<BC>" #% self.current_user  C:\\\\tmp
            self.proc_var_dict["varioskan_outputfile"] = [varioskan_outputfile_name, "String"]  
            self.momentum_process += """\t\tVarioskan [Run Protocol]
\t\t\t(ProtoName = '{protocol_name}', MaximumReadTime = '00:00:00',
\t\t\tOutputNameFormat = $varioskan_outputfile, 
\t\t\tRunOnAbortedIteration = 'No', Duration = '00:01:01', 
\t\t\tComments = '')
\t\t\t{container} 'Unlidded' in 'Nest' ;\n\n""".format(protocol_name=process_step.protocol(), container=process_step.container(0))
        elif process_step.device() == "Bravo":
            self.momentum_process += """\t\t\tBravo [RunProtocol]
\t\t\t(Protocol = '{protocol_name}', RunOnAbortedIteration = 'No', 
\t\t\tDuration = '00:00:20', Comments = 'remove supernatant', 
\t\t\tEnabled = 'Yes') ;\n\n""".format(protocol_name=process_step.protocol())

    def genCentrifuge(self, process_step):
        if not self.tool_container:
            self.momentum_tool_containers  += """\t\tplate Tool
                                (WithLidOffset = '-5', MoverLiddingGripOffset = '3', 
                                WithLidHeight = '17', Thickness = '1', SealThickness = '0', 
                                NumberOfWellRows = '8', NumberOfWellColumns = '12', 
                                WellNumberingMethod = 'Rows', BarCodeRegularExpression = '', 
                                BarCodeFile = '', BarCodeAutoExpression = '"NC" + Format(Now, "yyMMddHHmmss") + "_" + Format(WallClock, "fff")', 
                                GripOffset = 'Identity', GripForce = '0', Height = '15', 
                                StackHeight = '13.13', SetSize = '1', Attributes = '') ;\n"""
            self.tool_container = True
                
        curr_centr_time_factor_var = "centrifugation_time_factor%i" % self.centrifugation_counter 
        
        self.proc_var_dict["centrifugation_time"] = ["00:01:00", "Duration"]
        self.proc_var_dict["curr_centr_time"] = ["00:01:00", "Duration"]
        
        self.proc_var_dict[curr_centr_time_factor_var] = [str(process_step.duration()), "Integer"]
        
        self.momentum_process += "\t\tset curr_centr_time = 'centrifugation_time * " + curr_centr_time_factor_var + "' ;\n"
        
        self.momentum_process += """\t\t\tRotanta [Load to Rotor Nests]
\t\t\t\t(RunOnAbortedIteration = 'No', Duration = '00:03:01', 
\t\t\t\tComments = '', Enabled = 'Yes')
\t\t\t\tTool 'Unlidded' in 'Tool Nest' ;\n
\t\t\tTool_Hotel [Load]
\t\t\t\t(Comments = '', Enabled = 'Yes')
\t\t\t\tTool ;\n
\t\t\tRotanta [Run]
\t\t\t\t(ProgramRunMode = 'User Defined Run Parameters', 
\t\t\t\tSpinDuration = $curr_centr_time, RPM = '{centr_speed}', 
\t\t\t\tTemperature = '{centr_temp}', AccelerationLevel = '9', 
\t\t\t\tDecelerationLevel = '9', RunOnAbortedIteration = 'No', 
\t\t\t\tDuration = '00:01:00', Comments = '', Enabled = 'Yes') ;\n
\t\t\tRotanta [Unload from Rotor Nests]
\t\t\t\t(RunOnAbortedIteration = 'No', Duration = '00:02:01', 
\t\t\t\tComments = '', Enabled = 'Yes')
\t\t\t\tTool 'Unlidded' in 'Tool Nest' ;\n
\t\t\tTool_Hotel [Load]
\t\t\t\t(Comments = '', Enabled = 'Yes')
\t\t\t\tTool ;\n\n""".format(centr_speed=process_step.speed(), centr_temp=int(process_step.temperature()))
        self.centrifugation_counter += 1

    # now filling the rest of the process        
    def profileHead(self):
        self.momentum_profileHead = """// Generated: {curr_date} by LARA code generator written by mark doerr (mark@ismeralda.org)\n\nprofile UniversityGreifswaldProfile1\n{{\n
\t// Runtime settings\n
        runtime
                (Mode = 'Normal', IsAccelerated = 'Yes', AuditOnSimulate = 'Yes', 
                LogOnSimulate = 'Yes', HibernateOnSimulate = 'No', EnableFixedStartTime = 'Yes', 
                SimulationStartTime = '11/07/2013 12:00 AM', AllowNewIterationsOnDeviceError = 'No', 
                EnableCongestionDetection = 'Yes', CongestionClearQueueTimeThreshold = '00:02:00', 
                MaxQueueTimeThreshold = '00:05:00', EnableVerboseLogging = 'Yes') ;\n\n""".format(curr_date=str(datetime.datetime.now()))
        
    def profileDevices(self):
        """This is the Greifswald automation system - it needs to be adjusted to the particular system"""
        self.momentum_profileDevices = """\t// Devices and settings\n
\tdevices
\t{
        BarCodeReaderMS3 BCR
                        (Mode = 'Normal', Color = '255, 255, 128') ;
                Beacon Beacon
                        (Mode = 'Normal', Color = '128, 0, 255') ;
                Bravo Bravo
                        (ParkProtocol = 'Head_Left.pro', ProtocolPath = 'B:\\\\VWorks Workspace\\\\Protocol Files', 
                        UseAccessProtocol = 'Yes', ParkDuration = '00:00:10', 
                        NestAccessProtocol = 'B:\\\\VWorks Workspace\\\\Protocol Files', 
                        Mode = 'Normal', Color = '192, 192, 192') ;
                Hotel BufferNestsLBravo
                        (Mode = 'Normal', Color = '128, 128, 0') ;
                Hotel BufferNestsRBravo
                        (Mode = 'Normal', Color = '128, 128, 64') ;
                Dim4Carousel Carousel
                        (Speed = '50', Acceleration = '5', Mode = 'Normal', 
                        Color = '154, 205, 50') ;
                MultidropCombi Combi
                        (ValvePortsUI = '6', PrimeWhenIdle = 'Yes', PrimeOnInitialization = 'No', 
                        PrimeVolumeWhenIdle = '10', PrimeIntervalWhenIdle = '5', 
                        CassetteUI = '1', Mode = 'Normal', Color = '0, 128, 255') ;
                Biomek CombiHotel
                        (Project = 'BiomekNXP Span', ParkMethod = 'sim', Mode = 'Simulation', 
                        Color = '255, 105, 180') ;
                ContainerDataDriver Container
                        (SummaryFormat = 'CSV', SummaryFilename = '', SummaryColumns = 'DateTime,Location', 
                        Mode = 'Normal', Color = '0, 128, 128') ;
                Cytomat2C4 Cytomat_2
                        (CO2Deadband = '2', CO2Enable = 'No', CO2HiHiLimit = '55', 
                        CO2HiLimit = '50', CO2LoLimit = '40', CO2LoLoLimit = '35', 
                        HumidityDeadband = '2', HumidityEnable = 'No', HumidityHiHiLimit = '75', 
                        HumidityHiLimit = '70', HumidityLoLimit = '30', HumidityLoLoLimit = '25', 
                        O2Deadband = '2', O2Enable = 'No', O2HiHiLimit = '75', 
                        O2HiLimit = '70', O2LoLimit = '60', O2LoLoLimit = '55', 
                        TemperatureDeadband = '2', TemperatureEnable = 'No', 
                        TemperatureHiHiLimit = '45', TemperatureHiLimit = '39', 
                        TemperatureLoLimit = '35', TemperatureLoLoLimit = '30', 
                        ShakeDuringIncubate = 'No', RPMT1 = '100', RPMT2 = '100', 
                        FAMModeEnabled = 'Yes', SearchMode = 'Allowed Nests Only', 
                        HotelsOccupancyLabel = '<Click to Edit ...>', ContainersParticipationLabel = '<Click to Edit ...>', 
                        Mode = 'Normal', Color = '0, 255, 255') ;
                Cytomat2C4 Cytomat1550_1
                        (CO2Deadband = '2', CO2Enable = 'No', CO2HiHiLimit = '55', 
                        CO2HiLimit = '50', CO2LoLimit = '40', CO2LoLoLimit = '35', 
                        HumidityDeadband = '2', HumidityEnable = 'No', HumidityHiHiLimit = '75', 
                        HumidityHiLimit = '70', HumidityLoLimit = '30', HumidityLoLoLimit = '25', 
                        O2Deadband = '2', O2Enable = 'No', O2HiHiLimit = '75', 
                        O2HiLimit = '70', O2LoLimit = '60', O2LoLoLimit = '55', 
                        TemperatureDeadband = '2', TemperatureEnable = 'No', 
                        TemperatureHiHiLimit = '45', TemperatureHiLimit = '39', 
                        TemperatureLoLimit = '35', TemperatureLoLoLimit = '30', 
                        ShakeDuringIncubate = 'Yes', RPMT1 = '700', RPMT2 = '700', 
                        Mode = 'Normal', Color = '255, 0, 0') ;
                Cytomat2C4 Cytomat1550_2
                        (CO2Deadband = '2', CO2Enable = 'No', CO2HiHiLimit = '55', 
                        CO2HiLimit = '50', CO2LoLimit = '40', CO2LoLoLimit = '35', 
                        HumidityDeadband = '2', HumidityEnable = 'No', HumidityHiHiLimit = '75', 
                        HumidityHiLimit = '70', HumidityLoLimit = '30', HumidityLoLoLimit = '25', 
                        O2Deadband = '2', O2Enable = 'No', O2HiHiLimit = '75', 
                        O2HiLimit = '70', O2LoLimit = '60', O2LoLoLimit = '55', 
                        TemperatureDeadband = '2', TemperatureEnable = 'No', 
                        TemperatureHiHiLimit = '45', TemperatureHiLimit = '39', 
                        TemperatureLoLimit = '35', TemperatureLoLoLimit = '30', 
                        ShakeDuringIncubate = 'Yes', RPMT1 = '720', RPMT2 = '720', 
                        Mode = 'Normal', Color = '255, 128, 0') ;
                Cytomat2C4 Cytomat470
                        (CO2Deadband = '2', CO2Enable = 'No', CO2HiHiLimit = '55', 
                        CO2HiLimit = '50', CO2LoLimit = '40', CO2LoLoLimit = '35', 
                        HumidityDeadband = '2', HumidityEnable = 'No', HumidityHiHiLimit = '75', 
                        HumidityHiLimit = '70', HumidityLoLimit = '30', HumidityLoLoLimit = '25', 
                        O2Deadband = '2', O2Enable = 'No', O2HiHiLimit = '75', 
                        O2HiLimit = '70', O2LoLimit = '60', O2LoLoLimit = '55', 
                        TemperatureDeadband = '2', TemperatureEnable = 'No', 
                        TemperatureHiHiLimit = '45', TemperatureHiLimit = '39', 
                        TemperatureLoLimit = '35', TemperatureLoLoLimit = '30', 
                        ShakeDuringIncubate = 'Yes', RPMT1 = '730', RPMT2 = '730', 
                        Mode = 'Normal', Color = '255, 128, 64') ;
                GenericMover F5T
                        (ParkLocation = 'STDloc:safe', ParkMoverAtEndOfRun = 'Yes', 
                        MotionSettings = 'Velocity: 20%, Acceleration: 15%, Jerk: 10%', 
                        Mode = 'Normal', Color = '221, 160, 221') ;
                FileManager File_Mgr
                        (Mode = 'Normal', Color = '95, 158, 160') ;
                Wtio GPSYSIO_1
                        (Mode = 'Normal', Color = '255, 218, 185') ;
                Wtio GPSYSIO_2
                        (Mode = 'Normal', Color = '255, 160, 122') ;
                Hotel Hotel_1
                        (Mode = 'Normal', Color = '135, 206, 235') ;
                InputMonitoring Inout_Monitor
                        (Mode = 'Normal', Color = '50, 205, 50') ;
                DataMiner Miner
                        (Mode = 'Normal', Color = '186, 85, 211') ;
                Wtio MultiWay
                        (Mode = 'Normal', Color = '240, 128, 128') ;
                Omega Omega
                        (ProtocolPathListUI = '<Click Button to Edit>', Mode = 'Simulation', 
                        Color = '70, 130, 180') ;
                MomentumOperator Operator
                        (Mode = 'Normal', Color = '154, 205, 50') ;
                FreeNest Recovery
                        (Mode = 'Normal', Color = '255, 105, 180') ;
                Regrip Regrip
                        (Mode = 'Normal', Color = '240, 230, 140') ;
                Centrifuge Rotanta
                        (Mode = 'Normal', Color = '210, 180, 140') ;
                Hotel Tip_Hotel
                        (Mode = 'Normal', Color = '143, 188, 139') ;
                SmartStorage Tip_Storage
                        (FAMModeEnabled = 'Yes', SearchMode = 'Entire Device', 
                        HotelsOccupancyLabel = '<Click to Edit ...>', ContainersParticipationLabel = '<Click to Edit ...>', 
                        Mode = 'Normal', Color = '100, 149, 237') ;
                Hotel Tool_Hotel
                        (Mode = 'Normal', Color = '221, 160, 221') ;
                Varioskan Varioskan
                        (Mode = 'Normal', Color = '95, 158, 160') ;
                GenericMover virtualMover
                        (ParkLocation = 'STDloc:safe', ParkMoverAtEndOfRun = 'Yes', 
                        MotionSettings = 'Velocity: 20%, Acceleration: 20%, Jerk: 100%', 
                        Mode = 'Simulation', Color = '255, 218, 185') ;
                Hotel virtualStorage
                        (Mode = 'Normal', Color = '255, 160, 122') ;
                Waste virtualWaste
                        (Mode = 'Simulation', Color = '135, 206, 235') ;
                Waste Waste
                        (Mode = 'Normal', Color = '50, 205, 50') ;
\n\t}\n\n"""

    def profileDevicePools(self):
        """There are no device pools in the Greifswald automation system """   
        self.momentum_profileDevices = """\t// Device Pools\n\tpools\n\t{\n\t}\n\n"""

    def profileVariables(self):
        logging.debug("profile variables")
        self.momentum_profileVariables = """\t// Profile variables\n\tvariables\n\t{"""
        # the lock variables - it is important that they are on profile level
        for lock_name in self.lockset_global :
            self.momentum_profileVariables += \
"""\tBoolean {lock_name}
\t\t\t(DefaultValue = 'No', PromptForValue = 'No', Persist = 'No', 
\t\t\tComments = '') ;\n\t""".format(lock_name=lock_name)
        # now some useful variables
        self.momentum_profileVariables += """\t\t\n\t}\n\n"""

    def processHead(self):
        self.momentum_processHead = """\t// ******************  Version 1  ******************\n
\tprocess {process_name}\n\t{{\n""".format(process_name="P_" + self.experiment.name())
        return()

    def processContainers(self):
        self.momentum_processContainers = "\t\t// Containers\n\t\tcontainers\n\t\t{\n"
        #self.container_db.data(self.container_db.index(i,0)).toString()
        for i in range(self.container_db.rowCount()):
            cont = lam.StandardContainer(container_name=str(self.container_db.data(self.container_db.index(i,0)).toString()),
                                         container_type=str(self.container_db.data(self.container_db.index(i,3)).toString()),
                                         lidding_state=str(self.container_db.data(self.container_db.index(i,4)).toString()) )
            logging.debug(" processing %s" % cont.name())
            if cont.contClass() == "lid":
                self.momentum_processContainers += """\t\t\t{cont_class} {cont_name}
\t\t\t\t( BarCodeRegularExpression = '', BarCodeFile = '',
\t\t\t\tBarCodeAutoExpression = '"AC" + Format(Now, "yyMMdd_HHmmss")',
\t\t\t\tGripOffset = '{{[0, 0, -6], ([0, 0, 0], 1)}}', GripForce = '32',
\t\t\t\tHeight ='{cont_height}', StackHeight = '{cont_stackHeight}',
\t\t\t\tAttributes = '');\n\n""".format( cont_class=cont.contClass(), 
                                         cont_name=cont.name(), cont_height=cont.height(), 
                                         cont_stackHeight = cont.stackHeight() )

                logging.debug("mcg - containers: processing %s done" % cont.name() )
            else:
                if cont.liddingState() == "L":
                    cont_name_lid = " uses_lid %sLid" % cont.name()
                else: 
                    cont_name_lid = ""
                self.momentum_processContainers += """\t\t\t {cont_class} {cont_name} {cont_name_lid}
\t\t\t\t( NumberOfWellRows = '{cont_rowsNum}', NumberOfWellColumns ='{cont_colsNum}',
\t\t\t\tWellNumberingMethod = 'Rows', BarCodeRegularExpression = '', BarCodeFile = '',
\t\t\t\tBarCodeAutoExpression = '{cont_stdBarcodeTemplate}',
\t\t\t\tGripOffset = 'Identity', GripForce = '0',  MoverLiddingGripOffset = '{cont_movLidGripOffset}',
\t\t\t\tHeight ='{cont_height}', StackHeight = '{cont_stackHeight}', WithLidOffset = '-5', WithLidHeight = '17',
\t\t\t\tThickness = '1', SealThickness = '0', SetSize = '1',
\t\t\t\tAttributes = '' );\n\n""".format(cont_class=cont.contClass(), cont_name=cont.name(), 
                                  cont_name_lid=cont_name_lid, cont_rowsNum = cont.rowsNum(), 
                                  cont_colsNum = cont.colsNum(), cont_stdBarcodeTemplate=cont.stdBarcodeTemplate(),
                                  cont_movLidGripOffset=3 + cont.height() - cont.stdContainerHeight('Greiner96NwFb'),
                                  cont_height=cont.height(), cont_stackHeight=cont.stackHeight() )
                cont_name_lid = ""
        self.momentum_processContainers += self.momentum_loop_containers    
        self.momentum_processContainers += self.momentum_tool_containers
        self.momentum_processContainers += "\t\t}\n\n"
        
        
    def process_variables(self):  
        self.momentum_process_variables = """\t\t// Process variables\n\t\tvariables\n\t\t{\n"""
        for var_name, var_parm in self.proc_var_dict.iteritems() :
            self.momentum_process_variables += \
"""\t\t\t{var_type} {var_name}
\t\t\t\t(DefaultValue = '{def_value}', PromptForValue = 'No', Persist = 'No', 
\t\t\t\tComments = '') ;\n""".format(var_type=var_parm[1], var_name=var_name, def_value=var_parm[0])
        # the lock variables - special loop lock variables
        for lock_name in self.lockset_local :
            self.momentum_process_variables += \
"""\tBoolean {lock_name}
\t\t\t(DefaultValue = 'No', PromptForValue = 'No', Persist = 'No', 
\t\t\tComments = '') ;\n\t""".format(lock_name=lock_name)
        self.momentum_process_variables += """\t\t\tString uid
\t\t\t\t(DefaultValue = '""', PromptForValue = 'No', Comments = '') ;
\t\t\tString log_entry\n\t\t\t\t(DefaultValue = '', PromptForValue = 'No', Comments = '') ;
\t\t\tString log_filename\n\t\t\t\t(DefaultValue = '', PromptForValue = 'No', Comments = '') ;
\t\t\tString status_filename\n\t\t\t\t(DefaultValue = 'D:\\\\robot_data\\\\momentum_status\\\\current_momentum_status.csv', PromptForValue = 'No', Comments = '') ;
\t\t\tString summary_file\n\t\t\t\t(DefaultValue = '', PromptForValue = 'No', Comments = '') ;
\t\t\tString curr_user\n\t\t\t\t(DefaultValue = '{current_user}', PromptForValue = 'No', Comments = '') ;
\n\t\t}}\n\n""".format(current_user=self.current_user)


    # experiment generation            
    def experiment_head(self):
        self.momentum_experiment_head = """// Generated: {curr_date}\n\nexperiment E_{momentum_process}\n{{
\t// Experiment settings\n\tsettings
                (Process = 'P_{momentum_process}', 
                Iterations = '1', IterationsLockedForWorkUnits = 'No', 
                MinimumDelayBetweenIterations = '0', Priority = '10', ValidForUse = 'Yes', 
                EstimatedDuration = '05:55:14') ;\n\n""".format(curr_date=str(datetime.datetime.now()), momentum_process=self.experiment.name())
        return()
        
    def experiment_start_end(self):    
        self.momentum_experiment_start_end = """\t//  Start/End Instrument\n\n\tstartend\n\t{\n""" 
        logging.debug("experiment start end ------> ")
        
        for plate in self.container_location_db.iterkeys() :
            curr_device = self.container_location_db[plate][0]
            try: 
                curr_device_name = curr_device.name()
                print(curr_device)
                print(curr_device_name)
                self.momentum_experiment_start_end += """\t{plate}\n\t\t(start='{device}') ;\n""".format(plate=plate, device=curr_device_name)
            except AttributeError:
                pass
        self.momentum_experiment_start_end += "\n\t}\n\n" 
            
    def experiment_nest_restrictions(self):    
        self.momentum_nest_restrictions = """\t// Nest Restrictions\n\n\tNests\n\t{"""+ "\n\t}\n"

 #~ + "MasterPlate1 ('Carousel.Column1_Hotel:Nest 1'); \n" \
    #~ + "ExpressionPlate1Dw ('Carousel.Column2_Hotel:Nest 1'); \n" \
    #~ + "InductorTrough1 ('Cytomat_2.Stack 1:Nest 1'); \n" \
        #~ 
        
    def experimentTail(self):    
        self.momentum_experiment_tail = "}\n"
        return()
        
    def writeProcess(self):
        try:
            with open('P_'+ self.experiment.name() + ".cxx", 'w') as file_output:
                file_output.write(self.momentum_profileHead)
                file_output.write(self.momentum_profileDevices)
                file_output.write(self.momentum_profileVariables)
                file_output.write(self.momentum_processHead)
                file_output.write(self.momentum_processContainers)
                file_output.write(self.momentum_process_variables)
                file_output.write(self.momentum_process)
            file_output.close()
            logging.debug("mcg: outputfiel P_%s.cxx written" % self.experiment.name())
        except IOError:
            logging.Error("Cannot write momentum code file %s !!!" % experiment.name())
        
    def writeExperiment(self):
        try:
            with open('E_'+ self.experiment.name() + ".cxx", 'w') as file_output:
                #logging.debug(self.momentum_experiment_head)
                
                file_output.write(self.momentum_experiment_head)
                
                #logging.debug(self.momentum_experiment_head)
                
                file_output.write(self.momentum_experiment_start_end)
                file_output.write(self.momentum_nest_restrictions)
                file_output.write(self.momentum_experiment_tail)
            file_output.close()
            logging.debug("mcg: Experiment outputfiel E_%s.cxx written" % self.experiment.name())
        except IOError:
            logging.Error("Cannot write momentum code file %s !!!" % experiment.name())

