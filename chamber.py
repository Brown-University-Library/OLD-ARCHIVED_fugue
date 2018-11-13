#TODO: Enable git updates for the data sources.
#TODO: Enable pulling the config from a git repo.
#TODO: Make this a simple command line script.
#TODO: Comments

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml
from lxml import etree as ET
import mimetypes
from importlib import reload, import_module
from distutils.dir_util import copy_tree
import shutil
from subprocess import run
import click


from tidylib import tidy_document

#Look in this script's directory.
#TODO: Also try user's home.
conf_file = Path(os.path.dirname(os.path.realpath(sys.argv[0])), '.fugue.conf.yaml')
try:
    with open(conf_file, 'r') as f:
        fconfig = yaml.load(f)
except FileNotFoundError:
    fconfig = {}


proj_file = Path('.', 'fugue.project.yaml')
#TODO: Throw a more specific exception if there's no project file.
with open(proj_file, 'r') as f:
    settings = yaml.load(f)


mimetypes.init('./mime.types')

def dict2xml(thing, targ = None):
    if targ == None:
        targ = ET.Element('data')
    
    if dict == type(thing):
        for k, v in thing.items():    
            newel = ET.SubElement(targ, k)
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

def _git(sourcerepo, targetrepo, action="pull", **kwargs):
    gits = settings.get('git', {})
    vend = gits.get('vendor', False)
    keyf = gits.get('key_filename', False)
    
    if not keyf:
        raise KeyError('You must set git: key_filename in .fugue.conf.yaml.')
    
    #Have we set a custom vendor in config.yaml? Tell dulwich to use it.
    if bool(vend):
        src = gits.get('srcclass', 'dulwich.client')
        
        from dulwich import client as _mod_client
        src = import_module(src)
        vend = getattr(src, vend)
        _mod_client.get_ssh_vendor = vend
    
    dothis = getattr(porcelain, action)
    dothis(sourcerepo, targetrepo,  **kwargs)

def prepost(before=True):
    if before:
        commands = settings.get('preprocess', [])
        print('preprocessing')
    else:
        commands = settings.get('postprocess', [])
        print('postprocessing')
    
    if commands:
        for command in commands:
            print(' '.join(command))
            run(command)

prepost()


#TODO: Logging.
reload(logging)
if 'logging' in settings:
    if settings['logging']['target'] == 'file':
        logfile = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), settings['logging']['location']))
        logging.basicConfig(filename = logfile,
                            level = settings['logging']['level'])
    else:
        logging.basicConfig(level=logging.WARNING)

#TODO: Put separate phases in separate modules.
def handle_filesystem_datasource(ds, dsroot):
    print('handle_filesystem_datasource', ds['directory'])
    dr = Path(ds['directory'])
    files = sorted(dr.glob(ds['filemask']))
    #TODO handle non-XML (markdown, txt, json...)
    
    for p in files:
        sta = p.stat()

        datumroot = ET.SubElement(dsroot, 'file')
        datumroot.set('filename', p.name)
        datumroot.set('pathname', str(p.parent))
        datumroot.set('fullpath', str(p))
        datumroot.set('extension', p.suffix[1:])

        try:
            datumroot.set('mime-type', mimetypes.guess_type(p.name)[0])
        except TypeError:
            pass
        #datumroot.set()
        datumroot.set('mtime', datetime.utcfromtimestamp(sta.st_mtime).isoformat())
        datumroot.set('atime', datetime.utcfromtimestamp(sta.st_atime).isoformat())
        datumroot.set('size', str(sta.st_size))

        with p.open("rb") as fl:
            xmldat = fl.read()
        
        try: 
            newtree = ET.fromstring(xmldat)
        except ET.XMLSyntaxError: 
            xmldat, tidyerr = tidy_document(xmldat, options={'output-xml': 1, 'indent': 0, 'tidy-mark':0})
            newtree = ET.fromstring(xmldat)
        
        #TODO: Need to look for id or xml:id attributes and kill them (infile-id?).
        #TODO: Need to do this better--somehow preserve namespaces.
        ideds = newtree.xpath('//*[@*[local-name()="id"]]')
        for ided in ideds:
            nsurl = ided.xpath('namespace-uri(@*[local-name()="id"])')
            attname = '{{{nsurl}}}id'.format(nsurl=nsurl)
            attrval = ided.attrib.pop(attname)
            ided.attrib['origfile-id'] = attrval
        datumroot.append(newtree)

def load_data_sources():
    xmlroot = ET.Element('fugue-data')
    
    projroot = ET.SubElement(xmlroot, 'fugue-config')

    #TODO: convert fugue.project.yaml to XML and insert in this file inside <fugue-config />
    #Need a recursive function that uses an ET.TreeBuilder().
    dict2xml(settings, projroot)

    dssroot = ET.SubElement(xmlroot, 'data-sources')
    dss = settings['data-sources']
    for dsname, ds in dss.items():
        #TODO: Dynamically load modules to deal with different DS types.
        dsroot = ET.SubElement(dssroot, dsname)
        if 'filesystem' == ds['type']:
            handle_filesystem_datasource(ds, dsroot)
        if 'git' == ds['type']:
            #TODO: git pull
            if 'sources' in ds:
                for scname, sc in ds['sources'].items():
                    scroot = ET.SubElement(dsroot, scname)
                    if 'filesystem' == sc['type']:
                        handle_filesystem_datasource(sc, scroot)
    return xmlroot

outp = load_data_sources()

#TODO: configurable output file with #reasonable default.
with open('fugue-data.xml', mode="wb") as outpfile:
    outpfile.write(ET.tostring(outp, pretty_print=True))
    
def copy_static_files():
    sss = settings['static-sources']

    print('copying static files.')
    
    for ssname, ss in sss.items():
        source = Path(ss['source']).resolve()
        target = Path(settings['site']['root'], ss['target']).resolve()
        print(str(source) + ' to ' + str(target))
        
        if ss['target'] != '':
            if os.path.exists(target):
                shutil.rmtree(os.path.join(settings['site']['root'], ss['target']))
        #if not os.path.exists(Path(settings['site']['root'], ss['target'])):
        #    os.makedirs(Path(settings['site']['root'], ss['target']))
        
        copy_tree(str(source), str(target))
        
#TODO: Click should decide whether to do this.
#TODO: Maybe replace this with rsync?
copy_static_files()
    
def apply_templates():
    pages = settings['pages']
    data = ET.parse('fugue-data.xml')
    for pagename, page in pages.items():
        xslt = ET.parse(page['template'])

        transform = ET.XSLT(xslt)

        
        perpage = page.get('perpage', 1)
        items = page.get('items', False)

        if items:
            xitems = data.xpath(page['items'])
            pagecount = int(len(xitems) / perpage)
            if len(xitems) % perpage:
                pagecount += 1
        else: 
            pagecount = 1
            perpage = 1
                
        #TODO: Pagination should be optional.
        for i in range(1, pagecount+1):
            params = {
                'pagenum':      str(i),
                'pagecount':    str(pagecount),
                'perpage':      str(perpage),
                'pagename':     "'{}'".format(pagename),
            }

            for k, v in page.items():
                if k not in params.keys():
                    if type(v) in (int, float):
                        params[k] = str(v)
                    if type(v) == str:
                        if v.startswith('xpath:'):
                            params[k] = v[len('xpath:'):]
                        elif 'items' == k:
                            params[k] = v
                        else: #TODO: This will break stuff if v contains a '
                            params[k] = "'{}'".format(v)
            
            result = transform(data, **params)
            
            #TODO: Make this an option somewhere. 
            pn = str(i).zfill(2)
            flname = page['uri'].replace('{pagenum}', pn)
            target = Path(settings['site']['root'], flname)
            
            if not target.parent.exists():
                target.parent.mkdir(parents=True)
            
            print("Outputting "+str(target))
            #with target.open('wb') as f:
            result.write_output(str(target))

apply_templates()

prepost(False)
            
"""
@click.group(invoke_without_command=True)
@click.argument('config', default=os.path.join(here, 'config.yaml'))
@click.pass_context
def fugue(cxt, config):
    #Load the fugue settings file and the project config.
    click.echo(config)

@fugue.command()
def git():
    pass
    
@fugue.command()
def builddata():
    pass

@fugue.command()
def copystatic():
    pass
    
if __name__ == '__main__':
    fugue()
"""