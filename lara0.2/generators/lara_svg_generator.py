#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: LA_Html5Generator
# FILENAME: lara_html5_generator.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.0
#
# CREATION_DATE: 2013/12/01
# LASTMODIFICATION_DATE: 2014/09/14
#
# BRIEF_DESCRIPTION: html5 generator classes for LARA - an experiment is a set of processes
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

from PyQt4 import Qt, QtCore, QtGui

class LA_SVGGenerator(QtCore.QObject):
    svgItemAddedSig = QtCore.pyqtSignal()
    def __init__(self, figure_name="", width=1.0, height=1.0, unit="px" ):
        super(LA_SVGGenerator,self).__init__()
        self.figure_name = figure_name
        
        self.width = width
        self.height = height
        
        self.svg_elements = {}
        
        self.initSVGDOM()
        
    def name(self):
        return(self.figure_name)
        
    def initSVGDOM(self):
        style_sheet_name = "lara/lara_report_style.css"
        
        self.svg_dom_root = ET.Element("svg", height=str(self.height), width=str(self.width))
        
        self.svg_elements["root"] = self.svg_dom_root

    def dumpSVG(self):
        return( ET.tostring(self.svg_dom_root, encoding="UTF-8", method="xml") )
        
    def writeSVGFile(self):
        svg_filename = "/tmp/%s.svg" % self.figure_name
        try:
            ET.ElementTree(self.svg_dom_root).write(svg_filename , encoding='UTF-8', xml_declaration=True, method="xml")
            logging.debug("lara: Experiment XML outputfile %s written" % svg_filename)
        except IOError:
            logging.Error("Cannot write Experiment XML outputfile %s !!!" % svg_filename)
    
    def root(self):
        return(self.svg_dom_root)
        
    def genSVGCoordSysCart(self, x_parameter, y_parameter):
        
        self.x_min = x_parameter[0]
        self.x_max = x_parameter[1]
        self.x_tick_interval = x_parameter[2]
        self.x_label = x_parameter[3]

        self.y_min = y_parameter[0]
        self.y_max = y_parameter[1]
        self.y_tick_interval = y_parameter[2]
        self.y_label = y_parameter[3]
                
        self.axis_coord_system = ""
        
        self.generateXAxis()
        self.generateYAxis()
        
    def generateXAxis(self):
        """ Function doc """
        
        x1 = str(self.width * 0.1)                      # starting at 10%
        y1 = str(self.height - (self.height * 0.1))
        
        x2 = str(self.width * 0.1 + self.width * 0.8)
        y2 = str(self.height - (self.height * 0.1))
        
        x_axis = ET.SubElement(self.svg_dom_root, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke="black")
        x_axis.set("stroke-width","4")
        
        x_lab = str(self.width * 0.1 + self.width * 0.75)
        y_lab = str(self.height - (self.height * 0.04))
        
        x_label = ET.SubElement(self.svg_dom_root, "text", stroke="black", x=x_lab, y=y_lab)
        x_label.text = self.x_label
        x_label.set("font-size","12")
        
        # now generating x-tics
        len_x_axis = self.x_max - self.x_min
        num_ticks = int(len_x_axis / self.x_tick_interval)
        x_lab_offset = 0.01
        
        for x_i in range(1,num_ticks-2):
    
            x1 = str(self.width * 0.1 + self.width * float(x_i)/float(num_ticks))
            y1 = str(self.height - (self.height * 0.1))
            
            x2 = str(self.width * 0.1 +  self.width * float(x_i)/float(num_ticks))
            y2 = str(self.height - (self.height * 0.07))
            
            x_axis = ET.SubElement(self.svg_dom_root, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke="black")
            x_axis.set("stroke-width","1")            
            
            
            x_lab = str(self.width * 0.1 + self.width * float(x_i)/ ( float(num_ticks) - float(num_ticks)*x_lab_offset))
            y_lab = str(self.height - (self.height * 0.06))
            
            x_tic_label = ET.SubElement(self.svg_dom_root, "text",  x=x_lab, y=y_lab)
            x_tic_label.text = str(x_i * self.x_tick_interval/1000 )
            
    def generateYAxis(self):
        """ Function doc """
        
        x1 = str(self.width * 0.1)
        y1 = str(self.height - (self.height * 0.1))
        
        x2 = str(self.width * 0.1 )
        y2 = str(self.height - (self.height * 0.8))
        
        y_axis = ET.SubElement(self.svg_dom_root, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke="black")
        y_axis.set("stroke-width","4")
        
        x_lab = str(self.width * 0.065)
        y_lab = str(self.height - (self.height * 0.78))
        
        y_label = ET.SubElement(self.svg_dom_root, "text", stroke="black",  
                                x=x_lab, y=y_lab, style="writing-mode: tb; glyph-orientation-vertical: 90;")
        y_label.set("font-size","12")
        y_label.text = self.y_label
        
class GenerateTimeLine(LA_SVGGenerator):
    """ Class doc """
    
    def __init__ (self, figure_name="", width=1.0, x_max=10, event_dict={}):
        figure_ratio = 0.625
        height = width * figure_ratio 
        super(GenerateTimeLine, self).__init__(figure_name="", width=width, height=height)
        
        self.figure_name = figure_name
        
        logging.debug("in timeline %s" %self.figure_name )
        
        self.event_dict = event_dict    #{"eventname":[start,len], ...}
        
        #x_max_rnd = pow(10,round(math.log(x_max,7)))
        #~ logging.debug("x_max : %s" % x_max )
        x_max_rnd = 10** round(math.log(x_max,7))
        
        # parameters for x and y axis (begin, end , interval, label)
        x_param = (0.0, x_max_rnd, x_max_rnd/10.0, "time [x10E03 sec]") 
        y_param = (0.0, 10.0, 1.0, "process")
        
        self.genSVGCoordSysCart(x_param, y_param)
        
        # now drawing the timeline boxes - very primitive will be improved in later versions 
        i = 1 
        for dkeys in self.event_dict: 
            x = self.width * 0.1 + self.width *  self.event_dict[dkeys][0]/x_param[1] 
            y = self.height * 0.9 - (self.height * 0.1 * i)
            
            bwidth = (self.width - self.width * 0.1) * self.event_dict[dkeys][1]/x_param[1]
            bheight = 20.0
            
            ET.SubElement(self.svg_dom_root, "rect", x=str(x), y=str(y), width=str(bwidth), height=str(bheight), stroke="green", fill="green", rx="5", ry="10")
            
            x_lab = x + 10.0
            y_lab = y + 15.0
            
            y_label = ET.SubElement(self.svg_dom_root, "text",  fill="black", x=str(x_lab), y=str(y_lab))
            y_label.text = dkeys
            i += 1
            
        self.writeSVGFile()
            
        
if __name__ == "__main__":
    
    logging.basicConfig(format='%(levelname)s-%(funcName)s:%(message)s', level=logging.DEBUG)
    
    #app = QtGui.QApplication(sys.argv)
  
    tl = GenerateTimeLine(figure_name = "Timeline", width=800.0)

    #sys.exit(app.exec_())
    exit(0)
