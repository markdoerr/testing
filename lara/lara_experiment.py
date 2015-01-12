#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: LA_Experiment
# FILENAME: lara_experiment.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.3
#
# CREATION_DATE: 2013/05/14
# LASTMODIFICATION_DATE: 2014/06/23
#
# BRIEF_DESCRIPTION: Experiment classes for LARA - an experiment is a set of processes
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
import math
import datetime
import xml.etree.ElementTree as ET

import generators.lara_html5_generator as lht5
import generators.momentum_code_generator as mcg
import generators.vworks11_code_generator as vw11cg
import generators.lara_svg_generator as lsvg

import lara_process as lap
import lara_material as lam
import lara_devices as lad

from PyQt4 import Qt, QtCore, QtGui, QtXml

class LA_ExperimentView(QtGui.QGraphicsView):
    InsertItem, LineConnect, InsertText, MoveItem  = range(4)
    """Subclassed QGraphicsView because of draMoveEvent and settings
    """
    def __init__(self, parent):
        super(LA_ExperimentView, self).__init__(parent)
        
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        #self.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.centerOn(50.0,50.0)
        #self.setObjectName(self.experiment_name + "_gv")
        #self.setFocusPolicy(QtGui.Qt.NoFocus)
        self.setAcceptDrops(True)
        self.current_mouse_mode = LA_ExperimentView.MoveItem
        
        parent.pointerTypeSig.connect(self.setMode)

    def setMode(self, mode):
        logging.debug("changing to %s mode" % mode)
        self.current_mouse_mode = mode   

    # might be omitted
    def dragEnterEvent(self, event): 
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            event.acceptProposedAction()
        else:
            event.ignore()
        super(LA_ExperimentView, self).dragEnterEvent(event)

    def dragMoveEvent(self, event): 	# very important for dragging
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def mousePressEvent(self, event):
        """ Function doc """
        if self.current_mouse_mode == LA_ExperimentView.MoveItem:
            modifiers = QtGui.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier:
                self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
            else :
                self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)   # mode, when clicked into scene
            event.ignore()
        super(LA_ExperimentView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QtGui.QGraphicsView.NoDrag)
        event.ignore()
        super(LA_ExperimentView, self).mouseReleaseEvent(event)
        
class LA_Experiment(QtGui.QGraphicsScene):
    InsertItem, LineConnect, InsertText, MoveItem  = range(4)

    #itemInserted = QtCore.pyqtSignal(lap.LA_SubProcess)
    #textInserted = QtCore.pyqtSignal(QtGui.QGraphicsTextItem)
    #itemSelected = QtCore.pyqtSignal(QtGui.QGraphicsItem)
    valueChanged = QtCore.pyqtSignal()

    def __init__(self, xml_fileinfo, experiment_gv):
        super(LA_Experiment, self).__init__(experiment_gv)
        
        self.xml_fileinfo = xml_fileinfo 
        self.experiment_name = self.xml_fileinfo.baseName()
        
        self.experiment_gv = experiment_gv
        self.lara_mainwindow = experiment_gv.parent()
        self.tool_item_lst = self.lara_mainwindow.tool_item_lst
    
        self.lara_mainwindow.central_tw.addTab(self.experiment_gv, self.experiment_name)
        
        logging.info("exp overview could be subclassed in textedit in future versions")
        self.exp_ov = lht5.LA_Html5Generator(self.experiment_name + "_overview")
        self.overview_te = LA_ExperimentOverview(self.lara_mainwindow, self.exp_ov)
        self.lara_mainwindow.central_tw.addTab(self.overview_te, self.experiment_name + "_overview")
        self.exp_ov.insertImage("timeline","timeline1","/tmp/timeline.svg", "Timeline of experiment")
    
        self.scene_def_width = 3062
        self.scene_def_height = 1600
        
        self.process_list = {}
        self.container_stream = {}
        
        self.current_mouse_mode = LA_Experiment.MoveItem
        
        logging.warning("size should be set by experiment settings dialog / LML ")
        self.setSceneRect(QtCore.QRectF(0, 0, self.scene_def_width, self.scene_def_height))
        
        self.connecting_line = None
        self.curr_line_colour = QtCore.Qt.red
                
        self.diag_item_previous = None
        self.exp_begin_item = None
        self.exp_end_item = None
        self.current_mouse_mode = LA_Experiment.MoveItem

        self.initExperiment()
        
        self.setObjectName(self.experiment_name + "_gs") 
        experiment_gv.setObjectName(self.experiment_name + "_gs")
         
        self.lara_mainwindow.pointerTypeSig.connect(self.setMode)
        self.lara_mainwindow.editCutSig.connect(self.cutItems)
        
        self.valueChanged.connect(self.updateInfoViews)
        
        experiment_gv.setScene(self)
        
    def name(self):
        return(self.experiment_name)
        
    def containerDBModel(self):
        """ Function doc """
        return(self.newcontainer_db)
        
    def xmlFileInfo(self):
        return(self.xml_fileinfo)
        
    def initExperiment(self):        
        # devices
        self.automation_sys = lad.LabAutomationSystem()
        
        logging.info("automation system needs to be moved into lml file")
        self.automation_sys["Carousel"] = lad.PlateHotel("Carousel", ext_nests=[{"stacks_num": 4, "nests_num":25,"stack_hight":35,"orientation":'l', "plates_per_nest":1},
                                                        {"stacks_num": 4, "nests_num":15,"stack_hight":45,"orientation":'l', "plates_per_nest":1},
                                                        {"stacks_num": 1, "nests_num":8,"stack_hight":45,"orientation":'l', "plates_per_nest":1} ])
        self.automation_sys["Combi"] =  lad.Dispenser("Combi", ext_nests=[{"stacks_num": 1,"nests_num":1,"stack_hight":45,"orientation":'l', "plates_per_nest":1}])
        self.automation_sys["Bravo"] =  lad.Dispenser("Bravo", ext_nests=[{"stacks_num": 1,"nests_num":9,"stack_hight":45,"orientation":'l', "plates_per_nest":1}])
        self.automation_sys["CombiHotel"] = lad.PlateHotel("CombiHotel", ext_nests=[{"stacks_num": 1, "nests_num":6,"stack_hight":35,"orientation":"pl", "plates_per_nest":1} ]) 
        self.automation_sys["BufferNestsLBravo"] = lad.PlateHotel("BufferNestsLBravo", ext_nests=[{"stacks_num": 1, "nests_num":6,"stack_hight":35,"orientation":"pl", "plates_per_nest":1} ]) 
        self.automation_sys["BufferNestsRBravo"] = lad.PlateHotel("BufferNestsRBravo", ext_nests=[{"stacks_num": 1, "nests_num":6,"stack_hight":35,"orientation":"pl", "plates_per_nest":1} ]) 
        self.automation_sys["Tip_Storage"] = lad.PlateHotel("Tip_Storage", ext_nests=[{"stacks_num": 1, "nests_num":6,"stack_hight":45,"orientation":"pl", "plates_per_nest":1} ]) 
        self.automation_sys["Cytomat1550_1"] = lad.PlateHotel("Cytomat1550_1", ext_nests=[{"stacks_num": 1, "nests_num":1,"stack_hight":45,"orientation":'p', "plates_per_nest":1}],
                                                            int_nests=[{"stacks_num": 1, "nests_num":20,"stack_hight":30,"orientation":'p', "plates_per_nest":1},
                                                                        {"stacks_num": 1, "nests_num":10,"stack_hight":45,"orientation":'p', "plates_per_nest":1} ])
        self.automation_sys["Cytomat1550_2"] = lad.PlateHotel("Cytomat1550_2", ext_nests=[{"stacks_num": 1, "nests_num":1,"stack_hight":45,"orientation":'p', "plates_per_nest":1}],
                                                            int_nests=[{"stacks_num": 1, "nests_num":20,"stack_hight":30,"orientation":'p', "plates_per_nest":1},
                                                                        {"stacks_num": 1, "nests_num":10,"stack_hight":45,"orientation":'p', "plates_per_nest":1} ])
        self.automation_sys["Cytomat470"] = lad.PlateHotel("Cytomat470", ext_nests=[{"stacks_num": 1, "nests_num":1,"stack_hight":45,"orientation":'p', "plates_per_nest":1}],
                                                            int_nests=[{"stacks_num": 1, "nests_num":20,"stack_hight":30,"orientation":'p', "plates_per_nest":1},
                                                                        {"stacks_num": 1, "nests_num":10,"stack_hight":45,"orientation":'p', "plates_per_nest":1} ])
        self.automation_sys["Cytomat_2"] = lad.PlateHotel("Cytomat_2", ext_nests=[{"stacks_num": 1, "nests_num":1,"stack_hight":45,"orientation":'p', "plates_per_nest":1}],
                                                            int_nests=[{"stacks_num": 1, "nests_num":20,"stack_hight":30,"orientation":'p', "plates_per_nest":1},
                                                                        {"stacks_num": 1, "nests_num":10,"stack_hight":45,"orientation":'p', "plates_per_nest":1} ])
        self.automation_sys["Omega"] =  lad.Dispenser("Omega", ext_nests=[{"stacks_num": 1,"nests_num":1,"stack_hight":45,"orientation":'l', "plates_per_nest":1}])
        self.automation_sys["Varioskan"] =  lad.Dispenser("Varioskan", ext_nests=[{"stacks_num": 1,"nests_num":1,"stack_hight":45,"orientation":'l', "plates_per_nest":1}])
        self.automation_sys["Rotanta"] = lad.PlateHotel("Rotanta", ext_nests=[{"stacks_num": 1, "nests_num":4,"stack_hight":35,"orientation":"l", "plates_per_nest":1} ]) 
        self.automation_sys["Tool_Hotel"] =  lad.Dispenser("Tool_Hotel", ext_nests=[{"stacks_num": 1,"nests_num":1,"stack_hight":45,"orientation":'l', "plates_per_nest":1}])
        
        # containers        
        self.newcontainer_db = lam.newContainerDB(experiment=self)
        self.container_location_db = lam.ContainerLocationDB(self.automation_sys)
    
        self.exp_timeline = LA_ExperimentTimeline(experiment=self, time_line_filename="timeline")
        
    def initExpLML(self):
        # preparing experiment XML structure
        self.exp_lml_root = ET.Element("LARA", version="0.1", filetype="Experiment", md5sum="000000000000000000000000000000")
        self.exp_lml_param = ET.SubElement(self.exp_lml_root, "Parameters")
        self.exp_lml_proc = ET.SubElement(self.exp_lml_root, "Process")

    def initNewExp(self):
        # LML file
        self.initExpLML()
        
        #  creating a begin item
        tool_item_class = self.tool_item_lst["BeginProcess"].diagramClass()
        def_item_pos = QtCore.QPointF(30.0,200.0)
        
        subprocess_item = tool_item_class(experiment=self, position=def_item_pos )
        subprocess_item.setContextMenu(self.lara_mainwindow.itemMenu)

        self.process_list[self.diag_item_previous] = subprocess_item
        self.diag_item_previous = subprocess_item
        lml_sp = ET.SubElement(self.exp_lml_proc, "SubProcess", name=self.diag_item_previous.name(), 
                                x_pos=str(def_item_pos.x()),y_pos=str(def_item_pos.y()) )
        subprocess_item.setLMLNode(lml_sp)
        subprocess_item.initNewSubProcess()
        lml_sp.set("uuid",str(subprocess_item.uuid()) )
        self.exp_begin_item = subprocess_item
        self.addItem(subprocess_item)

        # End process
        tool_item_class = self.tool_item_lst["EndProcess"].diagramClass()
        end_item_pos = def_item_pos + QtCore.QPointF(2224.0,0.0)
        
        subprocess_item = tool_item_class(experiment=self, position=end_item_pos )
        lml_sp_end = ET.SubElement(self.exp_lml_proc, "SubProcess", name=subprocess_item.name(),
                                x_pos=str(end_item_pos.x()),y_pos=str(end_item_pos.y()) )
        subprocess_item.setLMLNode(lml_sp_end)
        subprocess_item.initNewSubProcess()
        lml_sp_end.set("uuid",str(subprocess_item.uuid()) )
        self.exp_end_item = subprocess_item
        self.addItem(subprocess_item)
                
        # Container manager
        tool_item_class = self.tool_item_lst["ContainerManager"].diagramClass()
        cm_item_pos = def_item_pos + QtCore.QPointF(0.0,-150.0)
        subprocess_item = tool_item_class(experiment=self, position=cm_item_pos )
        lml_sp_cm = ET.SubElement(self.exp_lml_proc, "SubProcess", name=subprocess_item.name(), 
                        x_pos=str(cm_item_pos.x()),y_pos=str(cm_item_pos.y()) )
        subprocess_item.setLMLNode(lml_sp_cm)
        subprocess_item.initNewSubProcess()
        lml_sp_cm.set("uuid",str(subprocess_item.uuid()) )
        self.addItem(subprocess_item)      
                
        ET.SubElement(self.exp_lml_param, "ExperimentView", width=str(self.scene_def_width), height=str(self.scene_def_height) )
        
    def delSubProcess(self, sub_process_to_del):
        """ deleting a sub process from process list"""
        
        if isinstance(sub_process_to_del, lap.LA_ProcessElement):
                sub_process_to_del.removeFlowConnectors()
            
        proc_lst_keys = self.process_list.itervalues()
        previous_subprocess = None
        next_subprocess = proc_lst_keys.next()
        
        while next_subprocess :
            if  next_subprocess == sub_process_to_del:
                if sub_process_to_del in self.process_list:     # req. for the last item in dict 
                    temp_next_sp = self.process_list[sub_process_to_del]
                    self.exp_lml_proc.remove(sub_process_to_del.LMLNode())
                    del self.process_list[sub_process_to_del]
                    del self.process_list[previous_subprocess]
                    self.process_list[previous_subprocess] = temp_next_sp
                else :
                    del self.process_list[previous_subprocess]  # last item
                    self.exp_lml_proc.clear()
                break
            if next_subprocess in self.process_list :
                previous_subprocess = next_subprocess
                next_subprocess = self.process_list[next_subprocess]
            else:
                break
        
    def cutItems(self):
        """ Function doc """
        for item in self.selectedItems():
            if isinstance(item, lap.LA_ProcessElement):
                self.exp_lml_proc.remove(item.LMLNode())
                item.removeFlowConnectors()
            self.removeItem(item)
        
    def openExpLMLfile(self, new_lml_filename=""):
        self.exp_lml_tree = ET.parse( new_lml_filename )
        #ET.dump(self.exp_lml_tree)
        
        sp_uuid_dict = {}
        uuid_parent_dict = {}
        
        for subprocess in self.exp_lml_tree.findall( 'Process/SubProcess' ):
            logging.debug("reading lml file sp %s" % subprocess)
            
            name_sp = subprocess.get("name")
            x_pos = float(subprocess.get("x_pos") )
            y_pos = float(subprocess.get("y_pos") )
            
            curr_uuid = subprocess.get("uuid")
            parent_uuid = subprocess.get("parent")
            
            tb_item = self.tool_item_lst[name_sp]
            
            if tb_item :
                subprocess_class = tb_item.diagramClass()
                subprocess_item = subprocess_class(experiment=self, position=QtCore.QPointF(x_pos,y_pos))
                subprocess_item.setLMLNode(subprocess)
                #subprocess_item.initNewSubProcess()
                subprocess_item.initParameters()
                self.addItem(subprocess_item)
                self.process_list[self.diag_item_previous] = subprocess_item
                
                sp_uuid_dict[curr_uuid] = subprocess_item
                
                if subprocess_item.name() == "BeginProcess": 
                    self.exp_begin_item = subprocess_item
                if subprocess_item.name() == "EndProcess": 
                    self.exp_end_item = subprocess_item
                
                if parent_uuid :
                    uuid_parent_dict[curr_uuid] = parent_uuid
                
                if False: # switching off arrow connection self.diag_item_previous :
                    flow_con = ProcFlowConnector(start_item=self.diag_item_previous, end_item=subprocess_item)
                    flow_con.setColour(self.curr_line_colour)
                    self.diag_item_previous.addFlowCon(flow_con)
                    subprocess_item.addFlowCon(flow_con)
                    
                    flow_con.setZValue(+1000.0)
                    self.addItem(flow_con)     # adding arrow to graphics scene 
                    flow_con.updatePosition()
                
                self.diag_item_previous = subprocess_item
            else :
                logging.error("key not in list")
            
        self.exp_lml_root = self.exp_lml_tree.getroot()
        self.exp_lml_proc = self.exp_lml_tree.find( 'Process' )

        # now creating all connections
        
        for to_connect in uuid_parent_dict.keys():
            try: 
                start_item = sp_uuid_dict[uuid_parent_dict[to_connect]]
                end_item = sp_uuid_dict[to_connect]
                flow_con = ProcFlowConnector(start_item=start_item, end_item=end_item)
                flow_con.setColour(self.curr_line_colour)
                
                start_item.addFlowCon(flow_con)
                end_item.addFlowCon(flow_con)
                start_item.setNextStep(end_item)
            
                flow_con.setZValue(+1000.0)
                self.addItem(flow_con)     # adding arrow to graphics scene 
                flow_con.updatePosition()
                
            except KeyError:
                logging.error("KE: %s " % to_connect)
                
        self.valueChanged.emit()
            
    def beginOfExperiment(self):
        return(self.exp_begin_item)
        
    def containerStream(self):
        return(self.container_stream)
        
    def requestContainerFromStream(self, container_function="", container_type="Greiner96NwFb", lidding_state="U", min_num = 1):
        cont_function = container_function + container_type + lidding_state
        
        try :
            curr_min_num = self.container_stream[cont_function]
        
            # there are containers in the stream
            if min_num > curr_min_num:
                  self.newcontainer_db.add( container_function=cont_function, container_type=container_type, lidding_state=lidding_state, num = min_num - curr_min_num)
                  self.container_stream[cont_function] = min_num
                  
        except KeyError :
            self.newcontainer_db.add( container_function=cont_function, container_type=container_type, lidding_state=lidding_state, num = min_num)
            self.container_stream[cont_function] = min_num
            
    def defDefaultStartLocation(self, container_function="MasterPlate", container_type="Greiner96NwFb", lidding_state="L", dev_pos=()):
        # ("Thermo_carousel",1,1,"int")
        cont_function = container_function + container_type + lidding_state
        logging.info("this info could later be used to generate a watcher or experiment")
        try :
            num = self.container_stream[cont_function]
            for i in range(num) :
                cont_name = cont_function + str(i+1)
                # adds only a new location, if the location is not alredy defined
                if cont_name not in self.container_location_db : 
                    self.container_location_db.update({cont_name: (self.automation_sys[dev_pos[0]],(dev_pos[1],dev_pos[2]+i),dev_pos[3]) })
                  
        except KeyError :
            logging.error("default cont location ERROR")
                    
    def compile_experiment(self):
        if len(self.process_list) > 0:
            logging.debug("now compiling momentum files %s" % self.experiment_name)
            
            mcg.LA_GenerateMomentumCode(self, self.automation_sys, self.newcontainer_db, self.container_location_db)        
            logging.debug("done, now compiling vworks 11 files %s" % self.experiment_name)
            vwc = vw11cg.LA_GenerateVWorks11Code(self, self.automation_sys, self.newcontainer_db, self.container_location_db)
            logging.debug("la_exp: compiling vworks 11 file %s done" % self.experiment_name)
        else:
            logging.debug("no processes found")

    def updateInfoViews(self):
        self.exp_timeline.updateTimeline()
            
    def setMode(self, mode):
        logging.debug("changing to %s mode" % mode)
        self.current_mouse_mode = mode
        
    def setLineConnectMode(self):
        logging.debug("changing to line mode")
        self.current_mouse_mode = self.LineConnect
    
    def setItemMoveMode(self):
        logging.debug("changing to item move mode")
        self.current_mouse_mode = self.MoveItem
        
    def setLineColour(self, colour):
        self.curr_line_colour = colour
        if self.isItemChange(ProcFlowConnector):
            item = self.selectedItems()[0]
            item.setColour(self.curr_line_colour)
            self.update()
            
    def itemSelected(self, item):
        """ handler for selections """
        #~ font = item.font()
        #~ color = item.defaultTextColor()
        #~ self.fontCombo.setCurrentFont(font)
        #~ self.fontSizeCombo.setEditText(str(font.pointSize()))
        #~ self.boldAction.setChecked(font.weight() == QtGui.QFont.Bold)
        #~ self.italicAction.setChecked(font.italic())
        #~ self.underlineAction.setChecked(font.underline())
        #~ 
        pass
        
    def mousePressEvent(self, mouseEvent):
        # left button required for context menue
        #~ if (mouseEvent.button() != QtCore.Qt.LeftButton):
            #~ return

        if self.current_mouse_mode == self.InsertItem:
            pass
        elif self.current_mouse_mode == self.LineConnect:
            #logging.debug("line drawing")
            self.connecting_line = QtGui.QGraphicsLineItem(QtCore.QLineF(mouseEvent.scenePos(),
                                        mouseEvent.scenePos()))
            self.connecting_line.setPen(QtGui.QPen(self.curr_line_colour, 5.0))
            self.addItem(self.connecting_line)

        super(LA_Experiment, self).mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        if self.current_mouse_mode == self.LineConnect and self.connecting_line:
            #logging.debug("line drawing move")
            newLine = QtCore.QLineF(self.connecting_line.line().p1(), mouseEvent.scenePos())
            self.connecting_line.setLine(newLine)
        elif self.current_mouse_mode == self.MoveItem:
            super(LA_Experiment, self).mouseMoveEvent(mouseEvent)
            #logging.debug("moving item")

    def mouseReleaseEvent(self, mouseEvent):
        if self.connecting_line and self.current_mouse_mode == self.LineConnect:
            startItems = self.items(self.connecting_line.line().p1(), QtCore.Qt.IntersectsItemShape, QtCore.Qt.DescendingOrder )  # selects all items of graphicscene at this point 
            if len(startItems) and startItems[0] == self.connecting_line:
                startItems.pop(0)
                
            endItems = self.items(self.connecting_line.line().p2(), QtCore.Qt.IntersectsItemShape, QtCore.Qt.AscendingOrder)
            if len(endItems) and endItems[0] == self.connecting_line:
                endItems.pop(0)

            self.removeItem(self.connecting_line)
            self.connecting_line = None

            if len(startItems) and len(endItems) and \
                    isinstance(startItems[0], lap.LA_ProcessElement) and \
                    isinstance(endItems[0], lap.LA_ProcessElement) and \
                    startItems[0] != endItems[0]:

                startItem = startItems[0]
                endItem = endItems[0]

                flow_con = ProcFlowConnector(start_item=startItem, end_item=endItem)
                flow_con.setColour(self.curr_line_colour)
                
                startItem.addFlowCon(flow_con)
                endItem.addFlowCon(flow_con)
                endItem.setParentUUID(flow_con)
                startItem.setNextStep(endItem)
                
                flow_con.setZValue(+1000.0)
                self.addItem(flow_con)     # adding arrow to graphics scene 
                flow_con.updatePosition()
                
        elif self.current_mouse_mode == self.MoveItem:
            pass
                
        self.connecting_line = None
        
        # very important for signal flow - preventing counting bug of spinbox widget
        super(LA_Experiment, self).mouseReleaseEvent(mouseEvent)
        
    def dragEnterEvent(self, event):
        #logging.debug("drag enter Diagram scene")
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            if event.source() == self:
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()
        super(LA_Experiment, self).dragEnterEvent(event)
        
    def dragMoveEvent(self, event):
        #logging.debug("drag enter Diagram scene")
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            if event.source() == self:
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                event.acceptProposedAction()
        else:
            event.ignore()
        super(LA_Experiment, self).dragMoveEvent(event)
        
    def dropEvent(self, event):
        logging.debug("diagram scene: item dropped")
        if event.mimeData().hasFormat('application/lara-dnditemdata'):
            itemData = event.mimeData().data('application/lara-dnditemdata')
            dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.ReadOnly)

            diagram_class = dataStream.readQVariant().toPyObject()
            logging.warning("Converting PyObjects could be different in different operation systems")

            curr_mouse_pos = event.scenePos()

            logging.debug("event pos = %s-%s"% (curr_mouse_pos.x(), curr_mouse_pos.y()) ) 
            
            if len(self.process_list) == 0:
               # self.initNewExp()
               pass
                
            subprocess_item = diagram_class(experiment=self, position=curr_mouse_pos)
                                    
            self.addItem(subprocess_item)
            
            lml_sp = ET.SubElement(self.exp_lml_proc, "SubProcess", name=subprocess_item.name(),
                                    x_pos=str(curr_mouse_pos.x()),y_pos=str(curr_mouse_pos.y())  )
            subprocess_item.setLMLNode(lml_sp)
            subprocess_item.initNewSubProcess()
            lml_sp.set("uuid",str(subprocess_item.uuid()) )

            self.process_list[self.diag_item_previous] = subprocess_item
            
            if self.diag_item_previous :
                flow_con = ProcFlowConnector(start_item=self.diag_item_previous, end_item=subprocess_item)
                flow_con.setColour(self.curr_line_colour)
                
                self.diag_item_previous.addFlowCon(flow_con)
                subprocess_item.addFlowCon(flow_con)
                subprocess_item.setParentUUID(flow_con)
                self.diag_item_previous.setNextStep(subprocess_item)
                
                flow_con.setZValue(+1000.0)
                self.addItem(flow_con)     # adding arrow to graphics scene 
                flow_con.updatePosition()
            
            self.diag_item_previous = subprocess_item
            
            #newIcon.setAttribute(QtCore.Qt.WA_DeleteOnClose)

            if event.source() == self:
                event.setDropAction(QtCore.Qt.MoveAction)
                event.accept()
            else:
                #event.accept()
                event.acceptProposedAction()
        else:
            logging.debug("mime data not correct")
            event.ignore()
        super(LA_Experiment, self).dropEvent(event)
        logging.debug("ds: item finally dropped")
        
class LA_ExperimentOverview(QtGui.QTextEdit):
    """ Generates an overview tab in MainCentralTab with details of the experiment 
    """
    textAdded = QtCore.pyqtSignal()
    def __init__(self, parent=None, report=None):
        super(LA_ExperimentOverview, self).__init__(parent)
        
        self.setObjectName(report.name())
        self.setReadOnly(True) 
        
        self.report = report
        
        self.report.textAdded.connect(self.updateText)
        
        self.setHtml(self.report.textHtml() )

    def updateText(self):
        self.setHtml(self.report.textHtml() )
        
class LA_ExperimentTimeline(QtCore.QObject):
    """ Generates a timeline of the experiment - could be extended to timeline browser
    """
    expChanged = QtCore.pyqtSignal()
    def __init__(self, parent=None, experiment=None, time_line_filename=""):
        super(LA_ExperimentTimeline, self).__init__(parent)
        
        self.exp = experiment
        self.tl_filename = time_line_filename
        
        self.event_dict = {}
        
        #self.report.expChanged.connect(self.updateTimeline)
        
    def updateTimeline(self):
        
        start_of_next_subprocess = 0.0

        process_order = ""
        
        next_subprocess = self.exp.exp_begin_item
        logging.info("new traversing - traversing could be nicer !! e.g. by defining experiment as iterator -> ver 0.3")
        while next_subprocess :
            curr_subprocess_name = next_subprocess.name()
            print(curr_subprocess_name)
            # retrieving the totalDuration
            sp_total_duration = next_subprocess.totalDuration()
            
            self.event_dict[curr_subprocess_name] = [start_of_next_subprocess, sp_total_duration]
            
            # process entry in 
            process_order += curr_subprocess_name + " ("+ str(sp_total_duration) + "s) -> "
            self.exp.exp_ov.newPragraph("process","pr_p1",process_order)
            
            start_of_next_subprocess += sp_total_duration
            
            try:
                if next_subprocess == self.exp.exp_end_item :
                    break
                else :
                    #~ #print(next_subprocess.flowCon().endItem())
                    #~ logging.debug("next ---")
                    
                    next_subprocess = next_subprocess.flowNext()
            except:
                break

        #~ self.event_dict = {"inoculation":[2.0,1.0],"incubation":[3.0,3.0],"growth":[4.0,2.0],"induction":[6.0,0.5]} #event_dict
        print(self.event_dict)
        lsvg.GenerateTimeLine(figure_name=self.tl_filename, width=640.0, x_max= start_of_next_subprocess, event_dict=self.event_dict)
        
class LA_Connector(object):
    """ Class doc """
    def __init__(self, start_item, end_item):
        """ Class initialiser """
        
        self.curr_start_item = start_item
        self.curr_end_item = end_item

    def startItem(self):
        return(self.curr_start_item)

    def endItem(self):
        return(self.curr_end_item)
        
class SimpleArrow(LA_Connector, QtGui.QGraphicsLineItem):
    """ cos can be removed and replaced by just points ?"""
    def __init__(self, start_item=None, end_item=None, parent=None, scene=None):
        logging.info("init can be nicer")
        QtGui.QGraphicsLineItem.__init__(self,parent=parent, scene=scene)
        super(SimpleArrow, self).__init__(start_item, end_item)

        self.arrowHead_polygon = QtGui.QPolygonF()

        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.arrowColour = QtCore.Qt.black
        self.line_thickness = 6.0
        self.setPen(QtGui.QPen(self.arrowColour, self.line_thickness, QtCore.Qt.SolidLine,
                    QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))

    def setColour(self, colour):
        self.arrowColour = colour

    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0
        p1 = self.line().p1()
        p2 = self.line().p2()
        return QtCore.QRectF(p1, QtCore.QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = super(SimpleArrow, self).shape()
        path.addPolygon(self.arrowHead_polygon)
        return path

    def updatePosition(self):
        # mapping from item to scene coordinate system
        line = QtCore.QLineF(self.mapFromItem(self.curr_start_item, 0, 0), 
                             self.mapFromItem(self.curr_end_item, 0, 0))
        self.setLine(line)

    def paint(self, painter, option, widget=None):
        if (self.curr_start_item.collidesWithItem(self.curr_end_item)):
            return

        curr_pen = self.pen()
        curr_pen.setColor(self.arrowColour)
        arrowSize = 12.0
        painter.setPen(curr_pen)
        painter.setBrush(self.arrowColour)
        
        bnd_rect_sti = self.curr_start_item.boundingRect()
        bnd_rect_endi = self.curr_end_item.boundingRect()

        centerLine = QtCore.QLineF(self.curr_start_item.pos() + QtCore.QPointF(bnd_rect_sti.width(),bnd_rect_sti.height()/2), 
                        self.curr_end_item.pos() + QtCore.QPointF(-15, bnd_rect_endi.height()/2 ) ) 
        self.setLine(centerLine)
        
        # head can be drawn much simpler: select just two points behind the tip and connect them
        
        line = self.line()
        
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (math.pi * 2.0) - angle
        
        # upper arrow point
        arrowP1 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                        math.cos(angle + math.pi / 3.0) * arrowSize)
        # lower arrow point
        arrowP2 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                        math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)
        self.arrowHead_polygon.clear()
        
        for pg_point in [line.p2(), arrowP1, arrowP2]:
            self.arrowHead_polygon.append(pg_point) 
        
        painter.drawLine(line)
        painter.drawPolygon(self.arrowHead_polygon)
        
        if self.isSelected():
            painter.setPen(QtGui.QPen(self.arrowColour, 1, QtCore.Qt.DashLine))
            dash_line = QtCore.QLineF(line)
            dash_line.translate(0, 8.0)
            painter.drawLine(dash_line)
            dash_line.translate(0,-16.0)
            painter.drawLine(dash_line)
            
class SplineArrow(LA_Connector, QtGui.QGraphicsLineItem):
    def __init__(self, start_item=None, end_item=None, parent=None, scene=None):
        logging.info("init can be nicer")
        QtGui.QGraphicsLineItem.__init__(self,parent=parent, scene=scene)
        super(SimpleArrow, self).__init__(start_item, end_item)

        self.arrowHead_polygon = QtGui.QPolygonF()

        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.arrowColour = QtCore.Qt.black
        self.line_thickness = 6.0
        self.setPen(QtGui.QPen(self.arrowColour, self.line_thickness, QtCore.Qt.SolidLine,
                    QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))

    def setColour(self, colour):
        self.arrowColour = colour

    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0
        p1 = self.line().p1()
        p2 = self.line().p2()
        return QtCore.QRectF(p1, QtCore.QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = super(SimpleArrow, self).shape()
        path.addPolygon(self.arrowHead_polygon)
        return path

    def updatePosition(self):
        # mapping from item to scene coordinate system
        line = QtCore.QLineF(self.mapFromItem(self.curr_start_item, 0, 0), 
                             self.mapFromItem(self.curr_end_item, 0, 0))
        self.setLine(line)

    def paint(self, painter, option, widget=None):
        if (self.curr_start_item.collidesWithItem(self.curr_end_item)):
            return

        curr_pen = self.pen()
        curr_pen.setColor(self.arrowColour)
        arrowSize = 12.0
        painter.setPen(curr_pen)
        painter.setBrush(self.arrowColour)
        
        bnd_rect_sti = self.curr_start_item.boundingRect()
        bnd_rect_endi = self.curr_end_item.boundingRect()

        centerLine = QtCore.QLineF(self.curr_start_item.pos() + QtCore.QPointF(bnd_rect_sti.width(),bnd_rect_sti.height()/2), 
                        self.curr_end_item.pos() + QtCore.QPointF(-15, bnd_rect_endi.height()/2 ) ) 
        self.setLine(centerLine)
        
        # head can be drawn much simpler: select just two points behind the tip and connect them
        
        line = self.line()
        
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (math.pi * 2.0) - angle
        
        # upper arrow point
        arrowP1 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                        math.cos(angle + math.pi / 3.0) * arrowSize)
        # lower arrow point
        arrowP2 = line.p2() - QtCore.QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                        math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)
        self.arrowHead_polygon.clear()
        
        for pg_point in [line.p2(), arrowP1, arrowP2]:
            self.arrowHead_polygon.append(pg_point) 
        
        painter.drawLine(line)
        painter.drawPolygon(self.arrowHead_polygon)
        
        if self.isSelected():
            painter.setPen(QtGui.QPen(self.arrowColour, 1, QtCore.Qt.DashLine))
            dash_line = QtCore.QLineF(line)
            dash_line.translate(0, 8.0)
            painter.drawLine(dash_line)
            dash_line.translate(0,-16.0)
            painter.drawLine(dash_line)

class ProcFlowConnector(SimpleArrow):
    """ Class doc """
    def __init__ (self, start_item=None, end_item=None):
        super(ProcFlowConnector,self).__init__(start_item=start_item, end_item=end_item)
        
        # adjusting the number of containers in the stream
        #~ for container in end_item.container_stream:
            #~ if container in start_item.container_stream:
                #~ # if the number in source is too low, encrease to the number in target:
                #~ logging.debug("container %s : start: %i - end %i" %(container, start_item.container_stream[container], end_item.container_stream[container] ))
                #~ if start_item.container_stream[container] < end_item.container_stream[container] :
                    #~ start_item.container_stream[container] = end_item.container_stream[container]
        #~ 
class ContFlowConnector(LA_Connector):
    """ Class doc """
    
    def __init__ (self, start_item=None, end_item=None):
        """ Class initialiser """
        pass
