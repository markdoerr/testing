#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: SiLAprocessManager
# FILENAME: lara_sila_process_manager.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.3.0
#
# CREATION_DATE: 2013/10/22
# LASTMODIFICATION_DATE: 2014/09/19
#
# BRIEF_DESCRIPTION: SiLA compliant process manager
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

import singledispatch  # will be included in python 3.4 functools library; for python < 3.3 plese use pip install singledispatch

from pysimplesoap.client import SoapClient

from .. import lara_process
from .. import lara_material as lam

class LA_SiLAProcessManager(object):
    """SiLA compliant process manager
    """
    def __init__(self, experiment, automation_sys, container_db=None, container_location_db=None ):
        
        sila_namespace = "http://sila-standard.org"
        service_url = "http://10.0.0.34:8008/" # servic_url = "http://localhost:8008/"

        self.soap_client = SoapClient( location = service_url,
            action = service_url, # SOAPAction
            namespace = sila_namespace, #"http://example.com/sample.wsdl", 
            soap_ns='soap',
            ns = False)
        
        self.requestID = "LARASiLAPMS1"
        
        self.experiment = experiment
        
        self.generate = singledispatch.singledispatch(self.generate)
        self.generate.register(lara_process.BeginSubProcess,self.genBeginSubProcess)
        self.generate.register(lara_process.GetDeviceIdentification,self.genGetDeviceID)
        self.generate.register(lara_process.GetDeviceIdentification,self.genGetStatus)
        self.generate.register(lara_process.OpenDoor,self.genOpenDoor)
        self.generate.register(lara_process.CloseDoor,self.genCloseDoor)
        self.generate.register(lara_process.ExecuteMethod,self.genExecuteMethod)
        self.generate.register(lara_process.EndSubProcess,self.genEndSubProcess)
        
        for step in self.experiment:
            self.generate(step)

    def genBeginSubProcess(self, process_step):
        logging.debug("Sila process started")

    def genEndSubProcess(self, process_step):
        logging.debug("Sila process ended")
        #~ self.addSubProcessDefinition()

    def genGetDeviceID(self, process_step):
        response = self.soap_client.GetDeviceIdentification(requestID=process_step.requestID())
        print(response.SiLA_DeviceClass)
        print(response.DeviceName)

    def genGetStatus(self, process_step):
        response = self.soap_client.GetStatus(requestID=process_step.requestID())
        #~ print(response.SiLA_DeviceClass)
        #~ print(response.DeviceName)

    def genOpenDoor(self, process_step):
        response = self.soap_client.OpenDoor(requestID=process_step.requestID(), lockID=process_step.lockID())

    def genCloseDoor(self, process_step):
        response = self.soap_client.CloseDoor(requestID=process_step.requestID(), lockID=process_step.lockID())

    def genExecuteMethod(self, process_step):
        response = self.soap_client.ExecuteMethod(requestID=process_step.requestID(),
                                                  lockID=process_step.lockID(),
                                                  methodName=process_step.methodName(),
                                                  priority=process_step.priority())
        print(response.complexResponse)

    def generate(self,item):
        logging.debug("SiLA process manager: generic item")
