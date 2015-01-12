#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: LARA_Process
# FILENAME: lara_process.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/05/14
# LASTMODIFICATION_DATE: 2014/06/13
#
# BRIEF_DESCRIPTION: Process classes for LARA
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
import uuid
import xml.etree.ElementTree as ET

from PyQt4 import Qt, QtCore, QtGui

import lara_material as lam
import lara_devices as lad

class SubProcessInterface(object):
    """ Class doc """
    
    def __init__ (self):
        """ Class initialiser """
        pass

class ContainerInterface(SubProcessInterface):
    """ Class doc """
    
    def __init__ (self):
        """ Class initialiser """
        pass

class ProcessStep(QtGui.QGraphicsItem):
    def __init__(self, parent=None, context_menu = None, step_name="", step_device=None, duration=180.0, lidded="L", orientation="L", description="", container=[]) :
        super(ProcessStep, self).__init__(parent=parent)
        self.container_list = container
        self.step_name = step_name
        self.step_device = step_device 
        self.lidded = lidded
        self.plate_orientation = orientation
        self.item_context_menu = context_menu
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
                
        self.color = "#32CD32"       # default color 
        self.step_duration = duration     # default duration of a step in seconds
        self.start_time = ""
        self.step_name = ""
        
        self.step_uuid = None
        self.step_description = description
             
    def setName(self, name):
        self.step_name = step_name
        
    def name(self):
        return(self.step_name)
        
    def setUUID(self):
        #~ # This assigns a reproducible uuid, but since step_name can be the same for many items, the uuid is not unique 
        #~ self.namespace_id = uuid.UUID('33333333-3333-3333-3333-333333333331')
        #~ self.step_uuid = uuid.uuid3(self.namespace_id, self.step_name)
        self.step_uuid = uuid.uuid4()
                
    def uuid(self):
        return(self.step_uuid)
        
    def duration(self):
        return(self.step_duration)

    def color(self):
        return(self.color)
        
    def setColor(self,color):
        self.color = color

    def containerList(self):
        return(self.container_list)
                
    def containerName(self, index):
        return(self.container_list[index].name())
        
    def container(self, index):
        try:
            return(self.container_list[index])
        except IndexError:
            return(False)
        
    def liddingState(self):
        return(self.lidded)
        
    def lidding(self):
        if self.lidded == "L":
            return("Lidded")
        else :
            return("Unlidded")
    
    def orientation(self):
        return(self.plate_orientation)

    def device(self):
        return(self.step_device)
        
    def description(self):
        return(self.step_description)
                
    def setContextMenu(self, context_menu):
        self.context_menu = context_menu

    def contextMenuEvent(self, event):
        logging.debug("context menu_event")
        self.scene().clearSelection()
        self.setSelected(True)
        
        if self.item_context_menu :
            #self.item_context_menu.exec_(event.screenPos())
            self.item_context_menu.exec_()
            
class LogEntry(ProcessStep):
    def __init__(self, step_name="", description=""):
        super(LogEntry, self).__init__(step_name=step_name, description=description)
        self.step_duration = 0.1
        
class BeginTask(ProcessStep):
    def __init__(self, step_name=""):
        super(BeginTask, self).__init__(step_name=step_name)
        self.step_duration = 0.1

class EndTask(ProcessStep): 
    def __init__(self, step_name=""):
        super(EndTask, self).__init__(step_name=step_name)
        self.step_duration = 0.1

class BeginLockedTask(ProcessStep):
    def __init__(self, step_name="", scope="global"):
        super(BeginLockedTask, self).__init__(step_name=step_name)
        self.step_duration = 0.1
        self.step_name = step_name
        
        self.lock_scope = scope
    
    def scope(self):
        return(self.lock_scope)

class EndLockedTask(ProcessStep): 
    def __init__(self, step_name=""):
        super(EndLockedTask, self).__init__(step_name=step_name)
        self.step_duration = 0.1
        self.step_name = step_name
        
class BeginProcess(ProcessStep):
    def __init__(self, step_name="", description=""):
        super(BeginProcess, self).__init__(step_name=step_name, description=description)
        self.step_duration = 0.1
    
class EndProcess(ProcessStep):
    def __init__(self, step_name=""):
        super(EndProcess, self).__init__(step_name=step_name)
        self.step_duration = 0.1

class BeginSubProcess(ProcessStep):    
    def __init__(self, device=None, step_name="", interpreter=0, description=""):
        super(BeginSubProcess, self).__init__(step_name=step_name, description=description)
        self.step_duration = 0.1
        
        self.sbproc_interpreter = interpreter
        logging.debug("init subprocess")

    def interpreter(self):
        return(self.sbproc_interpreter)
    
class EndSubProcess(ProcessStep):    
    def __init__(self, device=None, step_name=""):
        super(EndSubProcess, self).__init__(step_device=device, step_name=step_name)
        self.step_duration = 0.1
    
class BeginIf(ProcessStep):
    def __init__(self, step_name="", condition=""):
        super(BeginIf, self).__init__()
        self.step_duration = 0.1
        self.if_condition = condition
        
    def condition(self):
        return(self.if_condition)
        
class EndIf(ProcessStep):
    def __init__(self, step_name=""):
        super(EndIf, self).__init__()
        self.step_duration = 0.1
    
class While(ProcessStep):
    def __init__(self, step_name=""):
        super(While, self).__init__()
        self.step_duration = 0.1 
        
class BeginLoop(ProcessStep):
    def __init__(self, step_name="", max_iterations=1, description=""):
        super(BeginLoop, self).__init__(step_name=step_name, description=description)
        self.step_duration = 0.1
        
        self.max_iterations = max_iterations
    def maxIterations(self):
        return(self.max_iterations)
    
class EndLoop(ProcessStep):
    def __init__(self, step_name=""):
        super(EndLoop, self).__init__(step_name=step_name)
        self.step_duration = 0.1

class BeginParallel(ProcessStep):
    def __init__(self, step_name=""):
        super(BeginParallel, self).__init__(step_name=step_name)
        self.step_duration = 0.1
    
class EndParallel(ProcessStep):
    def __init__(self, step_name=""):
        super(EndParallel, self).__init__(step_name=step_name)
        self.step_duration = 0.1
        
class BeginThread(ProcessStep):
    def __init__(self, step_name=""):
        super(BeginThread, self).__init__(step_name=step_name)
        self.step_duration = 0.1
    
class EndThread(ProcessStep):
    def __init__(self, step_name=""):
        super(EndThread, self).__init__(step_name=step_name)
        self.step_duration = 0.1
    
class Delay(ProcessStep):
    def __init__(self, step_name=""):
        super(Delay, self).__init__(step_name=step_name)
        self.step_duration = 0.1
    
class ReadBarcode(ProcessStep):
    def __init__(self, lidded="U", container=[]):
        super(ReadBarcode, self).__init__(lidded=lidded, container=container)
        self.step_duration = 90.0
             
class Shake(ProcessStep):    
    def __init__(self, device=None, duration=60.0, mode="Shake", container=None):
        super(Shake, self).__init__(step_device=device, lidded=False, container=container)
        
        self.step_duration = duration
        
class LoadTips(ProcessStep):
    def __init__(self, target_device=None, position=0, lidded="U", orientation="L", columns=12, rows=8, column_pos=0, row_pos=0, static=0, container=[]):
        super(LoadTips, self).__init__(step_device=target_device,  lidded=lidded, orientation=orientation, container=container)
        self.plate_pos = position
        self.pos_static = static
        
        self.step_duration = 20.0
        
        self.column_pos = column_pos
        self.row_pos = row_pos

        self.columns_to_load = columns
        self.rows_to_load = rows
        
    def columnPos(self):
        return(self.column_pos)
        
    def rowPos(self):
        return(self.row_pos)
        
    def columns(self):
        return(self.columns_to_load)
        
    def rows(self):
        return(self.rows_to_load)
        
        
class UnloadTips(ProcessStep):
    def __init__(self, target_device=None, position=0, lidded="U", orientation="L", columns=12, rows=8, column_pos=0, row_pos=0, static=0, container=[]):
        super(UnloadTips, self).__init__(step_device=target_device,  lidded=lidded, orientation=orientation, container=container)
        self.plate_pos = position
        self.pos_static = static
        
        self.step_duration = 20.0

        self.column_pos = column_pos
        self.row_pos = row_pos
        
        self.columns_to_unload = columns
        self.rows_to_load = rows
        
    def columnPos(self):
        return(self.column_pos)
        
    def rowPos(self):
        return(self.row_pos)
        
    def columns(self):
        return(self.columns_to_unload)
        
    def rows(self):
        return(self.rows_to_unload)
        
class Aspirate(ProcessStep):    
    def __init__(self, device=None, mode="Aspirate", volume=0, prime_volume=10, liquids_channel=1, column_pos=12, row_pos=8, container_type="Greiner96NwFb", container=None):
        super(Aspirate, self).__init__(step_device=device, lidded=False, container=container)
        
        self.step_duration = 180.0
        
        # modes = Dispense, Empty, Prime
        self.dispense_mode = mode
        self.container_type = container_type
        self.aspirate_volume = volume
        self.prime_volume = prime_volume
        self.liquids_channel = liquids_channel
        self.std_prime_volume = 3000
        self.std_empty_volume = 3000
        
        logging.info("should be replaced by basis class LiquidHandling")
        self.column_to_aspirate = column_pos
        self.row_to_aspirate = row_pos
        
    def mode(self):
        return(self.dispense_mode)
        
    def contType(self):
        return(self.container_type)
        
    def primeVolume(self):
        return(self.prime_volume)
            
    def emptyVolume(self):
        if self.aspirate_volume :
            return(self.aspirate_volume)
        else:
            return(self.std_empty_volume)    
            
    def volume(self):
        if self.aspirate_volume :
            return(self.aspirate_volume)
        else:
            return(0)

    def liquidsChannel(self):
        return(self.liquids_channel)
        
    def columnPos(self):
        return(self.column_to_aspirate)
        
    def rowPos(self):
        return(self.row_to_aspirate)
        
class Dispense(ProcessStep):    
    def __init__(self, device=None, mode="Dispense", volume=0, prime_volume=10, liquids_channel=1, column_pos=12, row_pos=8,  container_type="Greiner96NwFb", container=None):
        super(Dispense, self).__init__(step_device=device, lidded=False, container=container)
        
        self.step_duration = 180.0
        
        # modes = Dispense, Empty, Prime
        self.dispense_mode = mode
        self.container_type = container_type
        self.dispense_volume = volume
        self.prime_volume = prime_volume
        self.liquids_channel = liquids_channel
        self.std_prime_volume = 3000
        self.std_empty_volume = 3000
        
        
        self.column_to_dispense = column_pos
        self.row_to_dispense = row_pos
        
    def mode(self):
        return(self.dispense_mode)
        
    def contType(self):
        return(self.container_type)
        
    def primeVolume(self):
        return(self.prime_volume)
            
    def emptyVolume(self):
        if self.dispense_volume :
            return(self.dispense_volume)
        else:
            return(self.std_empty_volume)    
            
    def volume(self):
        if self.dispense_volume :
            return(self.dispense_volume)
        else:
            return(0)

    def liquidsChannel(self):
        return(self.liquids_channel)
    
    def columnPos(self):
        return(self.column_to_dispense)
        
    def rowPos(self):
        return(self.row_to_dispense)


class Mix(ProcessStep):    
    def __init__(self, device=None, mode="Dispense", volume=0, prime_volume=10, liquids_channel=1, column_pos=12, row_pos=8, container_type="Greiner96NwFb", container=None):
        super(Mix, self).__init__(step_device=device, lidded=False, container=container)
        
        self.step_duration = 180.0
        
        # modes = Dispense, Empty, Prime
        self.dispense_mode = mode
        self.container_type = cont_type
        self.mix_volume = volume
        self.prime_volume = prime_volume
        self.liquids_channel = liquids_channel
        self.std_prime_volume = 3000
        self.std_empty_volume = 3000
        
        self.column_to_mix = columns
        self.row_to_mix = row_pos
        
    def mode(self):
        return(self.dispense_mode)
        
    def primeVolume(self):
        return(self.prime_volume)
            
    def emptyVolume(self):
        if self.mix_volume :
            return(self.mix_volume)
        else:
            return(self.std_empty_volume)    
            
    def volume(self):
        if self.mix_volume :
            return(self.mix_volume)
        else:
            return(0)

    def liquidsChannel(self):
        return(self.liquids_channel)
        
    def columnPos(self):
        return(self.column_to_mix)
        
    def rowPos(self):
        return(self.row_to_mix)

        
class AutoLoad(ProcessStep):
    def __init__(self, device=None, lidded="U", orientation="L", container=None):
        super(AutoLoad, self).__init__(step_device=device, lidded=lidded, orientation=orientation, container=container)
        self.step_duration = 20.0
                
class MovePlate(ProcessStep):
    def __init__(self, target_device=None, position=0, lidded="U", orientation="L", static=0, container_type="Greiner96NwFb", container=[]):
        super(MovePlate, self).__init__(step_device=target_device,  lidded=lidded, orientation=orientation, container=container)
        self.plate_pos = position
        self.pos_static = static
        
        self.container_type = container_type
        
        self.step_duration = 20.0
    
    def platePosition(self):
        if self.plate_pos == 0:
            return("")
        else:
            return(str(self.plate_pos))
            
    def isStatic(self):
        return(str(self.pos_static))
        
    def contType(self):
        return(self.container_type)
        
class Incubate(ProcessStep):
    def __init__(self, device=None,container=None, nest_position=None, temperature=37, incubation_duration=0, duration=60.0, OD=0.7):
        super(Incubate, self).__init__(step_device= device, container=container, duration=duration)
        
        self.step_duration = duration + float(incubation_duration * 60)
        self.incubation_duration = incubation_duration
        
    def incubationDuration(self):
        return(self.incubation_duration)
        
class RunExternalProtocol(ProcessStep):
    def __init__(self, target_device=None, nest_position=None, lidded="U", orientation="L", protocol="", duration=30.0, container=[]):
        super(RunExternalProtocol, self).__init__(step_device=target_device,  lidded=lidded, orientation=orientation, container=container, duration=duration)
        
        self.protocol_name = protocol
        
    def protocol(self):
        return(self.protocol_name)

class Centrifuge(ProcessStep):
    def __init__(self, device=None, lidded="U", orientation="L", protocol="", speed=0, duration=180.0, temperature=0.0,  container=[]):
        super(Centrifuge, self).__init__(step_device=device,  lidded=lidded, orientation=orientation, duration=duration, container=container)
         
        self.centr_speed = speed
        self.centr_temperature = temperature
        
    def speed(self):
        return(self.centr_speed)
        
    def temperature(self):
        return(self.centr_temperature)

class TipsOn(ProcessStep):
    def __init__(self, device=None, container=None, nest_position=None):
        super(TipsOn, self).__init__(step_device=device, container=container)
        self.plate_pos = nest_position
        
        self.step_duration = 10.0
                
    def platePosition(self):
        return(self.plate_pos)
        
class TipsOff(ProcessStep):
    def __init__(self, device=None, container=None, nest_position=None):
        super(TipsOff, self).__init__(step_device=device, container=container)
        self.plate_pos = nest_position
        
        self.step_duration = 10.0
                
    def platePosition(self):
        return(self.plate_pos)
        
class PipettePlate(ProcessStep):
    def __init__(self, device=None, container=None, nest_position=None):
        super(PipettePlate, self).__init__(step_device=device, container=container)
        self.plate_pos = nest_position
        self.step_duration = 30.0
    
    def platePosition(self):
        return(self.plate_pos)
        
class LA_ProcessElement(ProcessStep):
    momentum32, vworks11 = range(2)
    def __init__(self,  sp_name="", parent=None, experiment=None, position=None):
        super(LA_ProcessElement, self).__init__(parent=parent)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        #self.setHandlesChildEvents(False)
        
        self.exp = experiment
        self.lml_node = None
        
        #self.setObjectName = "LA_Subprocess"
        
        self.subprocess_settings_diag = None # required for communication between dialog and subprocess
        
        self.step_name = sp_name
        
        self.flow_connectors = []
        self.next_step = None
        
        self.steps_list = []
        self.step_duration = 0.1
        self.total_duration = 0.0        

        
    def LMLNode(self):
        return(self.lml_node)

    def setLMLNode(self, lml_node):
        """ entering the lml node for lml addition """
        self.lml_node = lml_node

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsItem.ItemPositionChange:
            #logging.debug("pos changed")
            current_pos = value.toPointF()
            #print(current_pos)
            if self.lml_node is not None :
                self.lml_node.set("x_pos",str(current_pos.x()) )
                self.lml_node.set("y_pos",str(current_pos.y()) )
        return(value)
    
    def upatePosition(self, x_pos, y_pos ):
        pass
        
    def setParentUUID(self, flow_con):
        try:
            print(flow_con.startItem())
            print(flow_con.startItem().uuid())
            parent_uuid = flow_con.startItem().uuid()
            logging.debug("flow connection parent uuid %s" %parent_uuid)
            #~ par_item  = ET.SubElement(self.lml_node, "Parent")
            self.lml_node.set("parent", str(parent_uuid))
            pass
            
        except:
            logging.error("no parent")

    def addFlowCon(self, flow_con):
        self.flow_connectors.append(flow_con)
        
    def removeFlowCon(self, flow_con):
        try:
            self.flow_connectors.remove(flow_con)
        except ValueError:
            pass
            
    def flowCon(self):
        return(self.flow_connectors[-1])
            
    def removeFlowConnectors(self):
        for flow_con in self.flow_connectors[:]:
            flow_con.startItem().removeFlowCon(flow_con)
            flow_con.endItem().removeFlowCon(flow_con)
            self.scene().removeItem(flow_con)

    def setNextStep(self, next_step):
        self.next_step = next_step
            
    def flowNext(self):
        return(self.next_step)

    def steps(self):
        return(self.steps_list)  
                
    def totalDuration(self):
        self.total_duration = 0.0
        #~ logging.debug("tot dur = %d" % self.total_duration)
        for step in self.steps_list :
            #~ logging.debug("step %s (%d)" % (step.name(),step.duration()))
            self.total_duration += step.duration()
            #~ logging.debug("  ++++++++++++++++ tot dur = %d" % self.total_duration)
        return (self.total_duration)
        
class LA_SubProcess(QtGui.QGraphicsWidget,LA_ProcessElement):
    """ !!! use unified naming convention -> SubProcess """
    def __init__(self, sp_name="", experiment=None, position=None ):
        super(LA_SubProcess, self).__init__(sp_name=sp_name, parent=None, experiment=experiment, position=position)
        
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.step_name)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setAcceptHoverEvents(True)

        #self.contextMenu = contextMenu
        self.step_duration = 0.1
        
        self.width = 300
        self.height = 240

        self.pin_width = 20
        self.pin_height = 20

        self.setZValue(2.0)
        
        pin_offset = 3
   
        self.minSize = QtCore.QSizeF(60, 80)
        self.prefSize = QtCore.QSizeF(300, 180)
        self.maxSize = QtCore.QSizeF(300, 600)

        self.anchor_layout = QtGui.QGraphicsAnchorLayout()
        self.anchor_layout.setSpacing(0)
        self.setLayout(self.anchor_layout)
        
        self.input_pin_pos = 1
        self.circ_in = QtGui.QGraphicsEllipseItem(-12, self.height/2+pin_offset, self.pin_width, self.pin_height)
        self.circ_in.setBrush(QtCore.Qt.green)
        self.circ_in.setAcceptHoverEvents(True)
        self.circ_in.setZValue(1.0)
        self.circ_in.setParentItem(self)

        self.output_pin_pos = 1
        self.circ_out = QtGui.QGraphicsEllipseItem(self.width-8, self.height/2+pin_offset, self.pin_width, self.pin_height)
        self.circ_out.setBrush(QtCore.Qt.red)
        self.circ_out.setParentItem(self.circ_in)
        self.circ_out.setAcceptHoverEvents(True)

        self.setGeometry(0,0,self.width,self.height)
        #self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        logging.debug("subprocess window created")
        self.setPos(position)

    def input_pin_pos(self):
        print(self.pos())
        po = self.pos() + QtGui.QPointF(0,float(self.height/2))
        print(po)
        return(self.pos() + QtGui.QPointF(0,float(self.height/2)))
        
    def output_pin_pos(self):
        print("output pin")
        #return(self.pos() + QtGui.QPointF(float(self.width-8),float(self.height/2)))
        
    def hoverEnterEvent(self, event):
        # move pointer to connection pin and start drawing line
        cursor = self.parent_gv.cursor() # or event.getCursor()
        pos = cursor.pos()
        #cursor.setPos( pos.x() + 50, pos.y() + 30 )
        
    def closeEvent(self, close_event):
        logging.info("closing subprocess, removing from list")
        #self.lml_node.clear()
        self.exp.delSubProcess(self)
