import logging
from pathlib import Path
from lxml import etree as ET
from datetime import datetime
import re

import mimetypes
mimetypes.init('./mime.types')

from .filetype_handlers import _filetypehandler_abstract

#TODO: only needed for loading CSV files.
from csv import DictReader as csvreader

#TODO: only needed for loading one file type--should live in that module when I move it.
import json

from tools import *
from tools.datasource_handlers.filetype_handlers import FTH_Factory

HUGE_PARSER = ET.XMLParser(huge_tree=True)

logging.debug('loaded filesystem_dshandler')

class Filesystem_DSHandler():
    default = True
    
    def __init__(self, desc):
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
            newtree = handler.process(p)

            """
            #TODO: Make new handler implementations and move this stuff into them.
            if "text/csv" == mimetype:
                with p.open("r", encoding='utf8') as fl:
                    rdr = csvreader(fl)
                    rowcount = 0
                    newtree = ET.Element('csvdata')

                    #TODO: Move to ..utils.
                    re_starts_with_digit = re.compile(r'(^[0-9])')
                    re_non_word_chars = re.compile(r'[^\w]+')

                    for row in rdr:
                        rowcount += 1
                        xmlrow = ET.SubElement(newtree, 'item')
                        for k, v in row.items():
                            tagname = re_starts_with_digit.sub(r'_\1', k.lower())
                            tagname = re_non_word_chars.sub('_', tagname)
                            newcell = ET.SubElement(xmlrow, tagname, {'columnname': k})
                            newcell.text=v

            elif "application/json" == mimetype:
                with p.open("r", encoding='utf8') as fl:
                    jdata = json.load(fl)
                    newtree = ET.Element('jsondata')
                    dict2xml(jdata, newtree)

            else: #Default to assuming this is XML or HTML, at least for now.
                with p.open("rb") as fl:
                    filedata = fl.read()
                    try: 
                        newtree = ET.fromstring(filedata, HUGE_PARSER)
                    except ET.XMLSyntaxError: 
                        #Run the input through Tidy.
                        #TODO: Try with these options (They successfully load the Atalanta data files, but I don't know if the finished site still works.):
                        #xmldat, tidyerr = tidy_document(filedata, options={'input-xml': 0, 'output-xhtml': 1, 'indent': 0, 'tidy-mark':0, 'quote-nbsp': 1, 'char-encoding': 'utf8', 'numeric-entities': 1})
                        xmldat, tidyerr = tidy_document(filedata, options={'input-xml': 1, 'output-xml': 1, 'indent': 0, 'tidy-mark':0})
                        try:
                            newtree = ET.fromstring(xmldat, HUGE_PARSER)
                        except ET.XMLSyntaxError:
                            xmldat = xmldat.decode('utf8')
                            xmldat = '<xml>{xmldat}</xml>'.format(xmldat=xmldat)
                            newtree = ET.fromstring(xmldat, HUGE_PARSER)
                    
                    #Look for id or xml:id attributes and kill them.
                    #But preserve the id data as "@origfile-id"
                    ideds = newtree.xpath('//*[@*[local-name()="id"]]')
                    for ided in ideds:
                        nsurl = ided.xpath('namespace-uri(@*[local-name()="id"])')
                        attname = '{{{nsurl}}}id'.format(nsurl=nsurl)
                        attrval = ided.attrib.pop(attname)
                        ided.attrib['origfile-id'] = attrval
            """
            datumroot.append(newtree)
