# dependencies

import os.path as op
import codecs
from collections import namedtuple

from System.Collections.Generic import List
from collections import OrderedDict
from operator import getitem

from pyrevit import HOST_APP
from pyrevit import USER_DESKTOP
from pyrevit import framework
from pyrevit.framework import Windows, Drawing, ObjectModel, Forms
from pyrevit import coreutils
from pyrevit import forms
from pyrevit import revit, DB
from pyrevit import script
import sys
import threading
from pyrevit import EXEC_PARAMS

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.DB.Analysis import *

# find the path of ui.xaml
from pyrevit import UI

doc = __revit__.ActiveUIDocument.Document

#loggers
logger = script.get_logger()
output = script.get_output()

#Collectors
colPrimary = []
colViews = []
viewPortList = []
lbxViewsSorted = []

#setup classes Top Left, Top Right, Bottom Left, Bottom Right, Center locations

#Get all viewports in Document
viewPorts = list(DB.FilteredElementCollector(doc).OfClass(Viewport))


#Get all Views on sheets, their Name, Sheet Number and Box Outline
for vp in viewPorts:
    sheet = doc.GetElement(vp.SheetId)
    view = doc.GetElement(vp.ViewId)
    viewPortList.append([sheet.SheetNumber, view.ViewName, vp])

lbxViewsSorted = sorted(viewPortList, key=lambda x: x[0])

for vp in lbxViewsSorted:
	colViews.append(vp[0] + " , " + vp[1])
	colPrimary.append(vp[0] + " , " + vp[1])

# create alignTypes

cmbAlignType = ["Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"]

class Viewports(forms.Reactive):
    def __init__(self,vpViewName):
        self._vpViewName = vpViewName
   
    @forms.reactive
    def vpViewName(self):
        return self._vpViewName
        
    @vpViewName.setter
    def vpViewName(self, value):
        self._vpViewName = value

class ViewModel(forms.Reactive):
    def __init__(self): 
        self.primaryView = colPrimary 
        self.ViewPorts = colViews
        self.AlignTypes = cmbAlignType

class MyWindow(forms.WPFWindow, forms.Reactive):
    def __init__(self):
        self.vm = ViewModel()
        
    def setup(self):
        self.lbxViews.ItemsSource = self.vm.ViewPorts
        self.cmbPrimary.ItemsSource = self.vm.primaryView
        self.cmbAlignment.ItemsSource = self.vm.AlignTypes

    @property
    def get_primary_view(self):
        return self.cmbPrimary.SelectedItem
   
    def alignviews(self, sender, args):
        selvpviews = []
        selvpsublist = []
        selvpsElements = []
        primaryElement = []

# get selected Views to be aligned
        selviews = [vps for vps in self.lbxViews.SelectedItems]
        for vs in selviews:
            selvpviews.append(vs.split(" , "))
        for vp in selvpviews:
            selvpsublist.append(vp[1::])
# flatten selected Views
        selvps = [item for sublist in selvpsublist for item in sublist]
# match selected Views with all Viewports, create new list
        selvpsmatches = set([item[1] for item in lbxViewsSorted]).intersection(selvps)
        selviewPorts = [view for view in lbxViewsSorted if view[1] in selvpsmatches]
        for el in selviewPorts:
          selvpsElements.append(el[2]) 
          
# get primary View to align with
        primview = (self.cmbPrimary.SelectedItem.split(" , "))
        primviewPort = [view for view in lbxViewsSorted if view[1] in primview]
        primaryElement = [i[2] for i in primviewPort]

# get selected views to align with
        alignType = (self.cmbAlignment.SelectedItem)

# Start a counter of views
        counter = 0

# Align Views to primary viewport dependant on Alignmnet type selected

        for t in selvpsElements:
            counter = counter + 1
            curvbox = t.GetBoxOutline()
            curvctr = t.GetBoxCenter()
            primvbox = primaryElement[0].GetBoxOutline()
            primvctr = primaryElement[0].GetBoxCenter()
            with revit.Transaction("Align Views"):
                if alignType == "Center":
                    alignment = (primvctr)
                elif alignType == "Top Left":
                    d1 = DB.XYZ(primvbox.MinimumPoint.X, primvbox.MaximumPoint.Y, primvbox.MaximumPoint.Z)
                    d2 = DB.XYZ(curvbox.MinimumPoint.X, curvbox.MaximumPoint.Y, curvbox.MaximumPoint.Z)
                    delta = (d2.Subtract(d1))
                    alignment = (curvctr.Subtract(delta))
                elif alignType == "Top Right":
                    d1 = DB.XYZ(primvbox.MaximumPoint.X, primvbox.MaximumPoint.Y, primvbox.MaximumPoint.Z)
                    d2 = DB.XYZ(curvbox.MaximumPoint.X, curvbox.MaximumPoint.Y, curvbox.MaximumPoint.Z)
                    delta = (d1.Subtract(d2))
                    alignment = (curvctr.Add(delta))
                elif alignType == "Bottom Right":
                    d1 = DB.XYZ(primvbox.MaximumPoint.X, primvbox.MinimumPoint.Y, primvbox.MaximumPoint.Z)
                    d2 = DB.XYZ(curvbox.MaximumPoint.X, curvbox.MinimumPoint.Y, curvbox.MaximumPoint.Z)
                    delta = (d1.Subtract(d2))
                    alignment = (curvctr.Add(delta))
                elif alignType == "Bottom Left":
                    d1 = DB.XYZ(primvbox.MinimumPoint.X, primvbox.MinimumPoint.Y, primvbox.MinimumPoint.Z)
                    d2 = DB.XYZ(curvbox.MinimumPoint.X, curvbox.MinimumPoint.Y, curvbox.MinimumPoint.Z)
                    delta = (d2.Subtract(d1))
                    alignment = (curvctr.Subtract(delta))
                else:
                    alignment = (primvctr)
                t.SetBoxCenter(DB.XYZ(alignment.X, alignment.Y, alignment.Z))

        forms.alert("Aligned " + str(counter) + " views successfully")
        
# init ui
ui = script.load_ui(MyWindow(), 'ui.xaml')
# show modal or nonmodal
ui.show_dialog()