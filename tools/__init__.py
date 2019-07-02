import re
from lxml import etree as ET

# XML tag name fixing:
xmltagnotfirst = r'^([^:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD])'
xmltagnotever  = r'([^-.0-9:A-Z_a-z\u00B7\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u037D\u037F-\u1FFF\u200C-\u200D\u203F\u2040\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD])'

xfirst = re.compile(xmltagnotfirst)
xnever = re.compile(xmltagnotever)

def xml_name(text):
    """Takes an arbitrary string, `text`, and turns it into a valid XML tag name."""
    outp = xnever.sub('_', text)
    outp = xfirst.sub('_', outp)
    return outp


def dict2xml(thing, targ = None):
    """Takes a python dictionary and converts it to XML. `targ` is the parent element, if provided."""
    if targ == None:
        targ = ET.Element('data')
    
    if dict == type(thing):
        for k, v in thing.items():    
            tagname = xml_name(k.lower())
            newel = ET.SubElement(targ, tagname)
            if str == type(v):
                newel.text = v
            elif bytes == type(v):
                newel.text = v.decode()
            else: 
                dict2xml(v, newel)
    elif list == type(thing):
        for v in thing:
            newel = ET.SubElement(targ, 'item')
            dict2xml(v, newel)
    elif bytes == type(thing):
        targ.text = thing.decode()
    else:
        targ.text = str(thing)
    
    return targ