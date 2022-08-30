""" Removes all hidden filled regions from selected views or just active view"""

from pyrevit import revit, DB
from pyrevit import script


output = script.get_output()
output.set_width(1100)

# collect filled regions
fregions = DB.FilteredElementCollector(revit.doc)\
          .OfClass(DB.FilledRegion)\
          .WhereElementIsNotElementType()\
          .ToElements()
fregions_deleted = []

def del_hidden_filled_regions(f):     
    fviewid = f.OwnerViewId
    v = revit.doc.GetElement(fviewid)
    if f.IsHidden(v):
        with revit.Transaction('Delete Hidden Filled Regions'):
            fregions_deleted.append(f)
            revit.doc.Delete(f.Id)
    else:
        return
        
print('Found {} filled regions to check...  '.format(len(fregions)))
with revit.TransactionGroup('Delete Hidden Filled Regions'):
    for idx, fr in enumerate(fregions):
        del_hidden_filled_regions(fr)
        output.update_progress(idx+1, len(fregions))

print('{} Hidden filled regions where deleted...'.format(len(fregions_deleted)))