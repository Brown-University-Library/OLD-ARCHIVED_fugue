import os
from pathlib import Path
from datetime import datetime
import yaml
from lxml import etree as ET
import mimetypes

import shutil

#TODO: Logging.

here = os.path.dirname(os.path.realpath(__file__))
settings_file = os.path.join(here, 'config.yaml')
with open(settings_file, 'r') as f:
    settings = yaml.load(f)

mimetypes.init('./mime.types')

#TODO: Put separate phases in separate modules.
def load_data_sources():
    #TODO: convert config.yaml to XML and insert in this file inside <chamber-config />
    xmlroot = ET.Element('chamber-data')
    dssroot = ET.SubElement(xmlroot, 'data-sources')
    dss = settings['data-sources']
    for dsname, ds in dss.items():
        #TODO: Dynamically load modules to deal with different DS types.
        dsroot = ET.SubElement(dssroot, dsname)
        if 'filesystem' == ds['type']:
            p = Path(ds['directory'])
            files = sorted(p.glob(ds['filemask']))
            for p in files:
                #TODO: Add a wrapper element with file metadata (name, create and modified dates, etc.)
                sta = p.stat()

                datumroot = ET.SubElement(dsroot, 'file')
                datumroot.set('filename', p.name)
                datumroot.set('extension', p.suffix)
                #TODO: Mime-type? 
                datumroot.set('mime-type', mimetypes.guess_type(p.name)[0])
                #datumroot.set()
                datumroot.set('mtime', datetime.utcfromtimestamp(sta.st_mtime).isoformat())
                datumroot.set('atime', datetime.utcfromtimestamp(sta.st_atime).isoformat())
                datumroot.set('size', str(sta.st_size))

                with p.open() as f:
                    newtree = ET.parse(f)
                    datumroot.append(newtree.getroot())

    return xmlroot

outp = load_data_sources()

#TODO: configurable output file with reasonable default.
with open('chamber-data.xml', mode="wb") as outpfile:
    outpfile.write(ET.tostring(outp, pretty_print=True))
    
def copy_static_files():
    #TODO: Also make the directories we need.
    sss = settings['static-sources']
    
    for ssname, ss in sss.items():
        shutil.rmtree(os.path.join(settings['site']['root'], ss['target']))
        shutil.copytree(ss['source'], os.path.join(settings['site']['root'], ss['target']))

copy_static_files()
    
def apply_templates():
    pages = settings['pages']
    dom = ET.parse('chamber-data.xml')
    
    for pagename, page in pages.items():
        print(pagename)
        xslt = ET.parse(page['template'])
        transform = ET.XSLT(xslt)
        
        #TODO: handle pagenum0 in xsl.
        #TODO: Use count and groupsize here.
        for i in range(1, 51):
            print(i)
            result = transform(dom, pagenum=str(i))
            #result.write(os.path.join(settings['site']['root'], 'emblem'+str(i)+'.html'), pretty_print=True)
            #with open(os.path.join(settings['site']['root'], 'emblem'+str(i)+'.html'), mode="wb") as outpfile:
            #    outpfile.write(ET.tostring(result, encoding="utf-8", pretty_print=True))
            result.write_output(os.path.join(settings['site']['root'], 'emblem'+str(i)+'.html'))
            
            
apply_templates()