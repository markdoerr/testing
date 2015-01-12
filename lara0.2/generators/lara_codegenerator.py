#!/usr/bin/env python
# -*- coding: utf-8 -*-

#_____________________________________________________________________________
#
# PROJECT: LARA
# CLASS: LA_CodeGenerator
# FILENAME: lara_codegenerator.py
#
# CATEGORY:
#
# AUTHOR: mark doerr
# EMAIL: mark@ismeralda.org
#
# VERSION: 0.2.1
#
# CREATION_DATE: 2013/11/25
# LASTMODIFICATION_DATE: 2013/12/08
#
# BRIEF_DESCRIPTION: Codegenerator base class for LARA
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

class LA_CodeGenerator(object):
    """ LARA Codegenerator base class """
    
    def __init__ (self, object_to_parse):
        """ Class initialiser """
        self.object_to_parse = object_to_parse
        
        
    def traverse(self):
        self.steps_list = []

        next_subprocess = self.object_to_parse.exp_begin_item
        logging.info("new traversing - traversing could be nicer !! e.g. by defining experiment as iterator -> ver 0.3")
        while next_subprocess :
            #~ print(next_subprocess)
            self.steps_list += next_subprocess.steps()
            try:
                if next_subprocess == self.object_to_parse.exp_end_item :
                    break
                else :
                    #~ #print(next_subprocess.flowCon().endItem())
                    #~ logging.debug("next ---")
                    
                    next_subprocess = next_subprocess.flowNext()
            except:
                break

        #~ print(self.steps_list)        
        for step in self.steps_list:
            self.generate(step)
