from ._filetypehandler_abstract import Abstract_FileHandler
from csv import DictReader as csvreader
from lxml import etree as ET
import re

class CSV_FileHandler(Abstract_FileHandler):
    class Meta:
        mimetypes = ("text/csv",)
    
    def process(path, _):
        with path.open("r", encoding='utf8') as fl:
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
        
            return newtree