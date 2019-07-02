from ._filetypehandler_abstract import Abstract_FileHandler
from tools import dict2xml

class JSON_FileHandler(Abstract_FileHandler):
    class Meta:
        mimetypes = ("application/json",)

    def process(path):
        with p.open("r", encoding='utf8') as fl:
            jdata = json.load(fl)
            newtree = ET.Element('jsondata')
            dict2xml(jdata, newtree)
            return newtree