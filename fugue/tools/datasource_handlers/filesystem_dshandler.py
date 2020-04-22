import logging
from pathlib import Path
from lxml import etree as ET
from datetime import datetime
import re

import mimetypes
mimetypes.init(['../mime.types'])

#from .filetype_handlers import _filetypehandler_abstract

#TODO: only needed for loading CSV files.
from csv import DictReader as csvreader

#TODO: only needed for loading one file type--should live in that module when I move it.
import json

from fugue.tools import *
from fugue.tools.datasource_handlers.filetype_handlers import FTH_Factory

HUGE_PARSER = ET.XMLParser(huge_tree=True)

logging.debug('loaded filesystem_dshandler')

class Filesystem_DSHandler():
    default = True
    
    def __init__(self, desc):
        self.desc = desc
        self.dir = desc['directory']
        self.glob = desc['filemask']

    def write(self, dsroot):
        logging.debug('handle_filesystem_datasource, folder: %s' % self.dir)
        dr = Path(self.dir)
        files = sorted(dr.glob(self.glob))
        
        for p in files:
            sta = p.stat()

            datumroot = ET.SubElement(dsroot, 'file')
            datumroot.set('filename', p.name)
            #Filename minus the extension:
            datumroot.set('filestem', p.stem)
            datumroot.set('pathname', p.parent.as_posix())
            datumroot.set('fullpath', p.as_posix())
            datumroot.set('extension', p.suffix[1:])


            mimetype = ""
            try:
                mimetype = mimetypes.guess_type(p.name)[0]
                datumroot.set('mime-type', mimetypes.guess_type(p.name)[0])
            except TypeError:
                pass
            
            datumroot.set('mtime', datetime.utcfromtimestamp(sta.st_mtime).isoformat())
            datumroot.set('atime', datetime.utcfromtimestamp(sta.st_atime).isoformat())
            datumroot.set('size', str(sta.st_size))

            handler = FTH_Factory.build(mimetype)
            newtree = handler.process(p, self.desc)

            datumroot.append(newtree)
