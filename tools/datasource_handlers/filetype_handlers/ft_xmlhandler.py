from lxml import etree as ET
from tidylib import tidy_document
from ._filetypehandler_abstract import Abstract_FileHandler

class XML_FileHandler(Abstract_FileHandler):
    """Default FileHandler. If nothing else matches, we assume the file is XML/HTML 
       and use this."""
    class Meta:
        default = True

    def process(path):
        with path.open("rb") as fl:
            filedata = fl.read()
            hugeparser = ET.XMLParser(huge_tree=True)
            
            try: 
                newtree = ET.fromstring(filedata, hugeparser)
            except ET.XMLSyntaxError: 
                #Run the input through Tidy.
                #TODO: Try with these options (They successfully load the Atalanta data files, but I don't know if the finished site still works.):
                #xmldat, tidyerr = tidy_document(filedata, options={'input-xml': 0, 'output-xhtml': 1, 'indent': 0, 'tidy-mark':0, 'quote-nbsp': 1, 'char-encoding': 'utf8', 'numeric-entities': 1})
                xmldat, tidyerr = tidy_document(filedata, options={'input-xml': 1, 'output-xml': 1, 'indent': 0, 'tidy-mark':0})
                try:
                    newtree = ET.fromstring(xmldat, hugeparser)
                except ET.XMLSyntaxError:
                    xmldat = xmldat.decode('utf8')
                    xmldat = '<xml>{xmldat}</xml>'.format(xmldat=xmldat)
                    newtree = ET.fromstring(xmldat, hugeparser)
            
            #All id attributes must be unique, across the entire document. So rename them.
            #We can change them back later in XSLT.
            ideds = newtree.xpath('//*[@*[local-name()="id"]]')
            for ided in ideds:
                nsurl = ided.xpath('namespace-uri(@*[local-name()="id"])')
                attname = '{{{nsurl}}}id'.format(nsurl=nsurl)
                attrval = ided.attrib.pop(attname)
                ided.attrib['origfile-id'] = attrval
            
            return newtree