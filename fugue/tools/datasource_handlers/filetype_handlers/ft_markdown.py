from ._filetypehandler_abstract import Abstract_FileHandler
from fugue.tools import dict2xml

import logging

import markdown2
from lxml import etree as ET

class Markdown_FileHandler(Abstract_FileHandler):
    class Meta:
        mimetypes = ("text/markdown","text/x-markdown")

    def process(path, desc={}):
        #desc is this datasource's description from the config file.
        #It may contain a list of extras to use.
        logging.debug('path %s exists? %s', str(path), path.exists())
        
        with path.open("r", encoding='utf8') as fl:
            newtree = ET.Element('markdown')
            
            extras = desc.get('extras', {'metadata':None})

            html = markdown2.markdown_path(path, extras=extras)
            
            #html.getattr('metadata', {})?
            metadata = ET.SubElement(newtree, 'metadata')
            dict2xml(html.metadata, metadata)
            
            ET.fromstring('<html>%s</html>'%html)
            newtree.append(ET.fromstring('<html>%s</html>'%html))
            
            return newtree