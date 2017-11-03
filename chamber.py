import os
from pathlib import Path
from datetime import datetime
import yaml
from lxml import etree
import re

here = os.path.dirname(os.path.realpath(__file__))
settings_file = os.path.join(here, 'config.yaml')
with open(settings_file, 'r') as f:
    settings = yaml.load(f)

p = Path('.')

#TODO: Put separate phases in separate modules.
def load_data_sources():
    xmlroot = etree.Element('chamber-data')
    dssroot = etree.SubElement(xmlroot, 'data-sources')
    dss = settings['data-sources']
    for dsname, ds in dss.items():
        #TODO: Dynamically load modules to deal with different DS types.
        dsroot = etree.SubElement(dssroot, dsname)
        if 'filesystem' == ds['type']:
            p = Path(ds['directory'])
            files = sorted(p.glob(ds['filemask']))
            for p in files:
                #TODO: Add a wrapper element with file metadata (name, create and modified dates, etc.)
                sta = p.stat()

                datumroot = etree.SubElement(dsroot, 'file')
                datumroot.set('filename', p.name)
                datumroot.set('mtime', datetime.utcfromtimestamp(sta.st_mtime).isoformat())
                datumroot.set('atime', datetime.utcfromtimestamp(sta.st_atime).isoformat())
                datumroot.set('size', str(sta.st_size))

                with p.open() as f:
                    newtree = etree.parse(f)
                    datumroot.append(newtree.getroot())

    return xmlroot
            
outp = load_data_sources()

#TODO: configurable output file with reasonable default.
with open('chamber-data.xml', mode="wb") as outpfile:
    outpfile.write(etree.tostring(outp, pretty_print=True))