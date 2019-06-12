#! python
#TODO: Enable git updates for the data sources.
#TODO: Enable pulling the config from a git repo.
#TODO: Make this a simple command line script.
#TODO: Comments
#TODO: Replace print() statements with click.echo() or logging....

#TODO: Do I actually need all this?
import logging
import os
from sys import argv, executable
from pathlib import Path
from datetime import datetime
import re

#TODO: only needed for loading CSV files.
from csv import DictReader as csvreader

#TODO: only needed for loading one file type--should live in that module when I move it.
import json

import yaml
from lxml import etree as ET
import mimetypes

#Used for static file moving/deleting.
from distutils.dir_util import copy_tree
import shutil

# Used for pre-/post-processing.
import subprocess

# Makes this a nice CLI.
import click

#Should be loaded in a datasource handler plugin.
from tidylib import tidy_document

mimetypes.init('./mime.types')

PYTHON_EXEC = executable
HUGE_PARSER = ET.XMLParser(huge_tree=True)

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

def process(commands):
    """Runs `commands`, an array of arrays. Used by preprocess and postprocess."""
    if commands:
        for command in commands:
            # Make sure we run outside scripts with the same python as furnace.
            cmd = [ PYTHON_EXEC if x == 'python' else x for x in command ]
            logging.info("Running %s" % (' '.join(cmd), ))
            ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ret.returncode == 0:
                logging.debug("Ran '%s'. Result: %s" % (' '.join(ret.args), ret.stdout.decode()))
            else:
                raise RuntimeError("process() command '%s' failed. Error: %s" % (' '.join(ret.args), ret.stderr.decode()))

#TODO: This should be handled in modules.
def handle_filesystem_datasource(ds, dsroot):
    logging.debug('handle_filesystem_datasource, folder: %s' % ds['directory'])
    dr = Path(ds['directory'])
    files = sorted(dr.glob(ds['filemask']))
    
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

    
        #Check mime-type here.
        #TODO: have different file types handled by plugins.
        if "text/csv" == mimetype:
            with p.open("r", encoding='utf8') as fl:
                rdr = csvreader(fl)
                rowcount = 0
                newtree = ET.Element('csvdata')
                
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
        datumroot.append(newtree)

def _load_config(ctx, file):
    logging.debug("Loading configuration file %s." % file)
    if ctx.obj == None: ctx.obj = {}
    with Path(file).open('r') as f:
        ctx.obj['settings'] = yaml.load(f, Loader=yaml.FullLoader)
    
    ctx.obj['project-output'] = Path(ctx.obj['settings']['site']['root']).resolve()
    logging.debug("Loaded configuration file.")

def _output_dir(ctx):
    outp = Path(ctx.obj['project_root']) / ctx.obj['settings']['site']['root']
    outp = outp.resolve()
    logging.debug("Checking for and returning directory at %s" % outp)
    if not outp.exists():
        outp.mkdir(parents=True)
    return outp


HERE = Path().resolve()

@click.group(invoke_without_command=True, chain=True)
@click.option('--log-level', '-L', 
                type=click.Choice(['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']),
                default="WARNING", help="Set logging level. Defaults to WARNING.")
@click.option('--project', '-p', default=Path('.', 'furnace.project.yaml'), 
                type=click.Path(), help=r"Choose the project configuration file. Defaults to ./furnace.project.yaml. Ignored if `furnace build` is called with a repository URL.")
@click.option('--data', '-d',  default=Path('.', 'furnace-data.xml'), 
                type=click.Path(), help=r"Choose the data file furnace will create and use. Defaults to ./furnace-data.xml. Ignored if `furnace build` is called with a repository URL.")
@click.pass_context
def furnace(ctx, log_level, project, data):
    """Static site generator using XSL templates."""

    """By default, looks at furnace.project.yaml in the current directory and completes all tasks
       needed to generate a complete site.
    """
    #TODO: option to not supress stdout and stderr in subprocess.run() calls.
    #TODO: Make logging more configurable.
    logging.basicConfig(level=getattr(logging, log_level))

    click.echo("Starting furnace")

    #Load configuration file.
    ctx.obj = {'data_file': Path(data), 
               'config_file': Path(project),}

    try:
        _load_config(ctx, project)
        
        ctx.obj['project_root'] = Path(project).parent.resolve()
        os.chdir(ctx.obj['project_root'])
        logging.debug('Changed directory to %s' % ctx.obj['project_root'])
    except FileNotFoundError as e:
        logging.debug(r"Loading config file failed. Hopefully we're giving build() a repository on the command line.")
        #Since chain=True, we can't tell which subcommand is being invoked :(.
        if ctx.invoked_subcommand == None:
            #Fail.
            raise RuntimeError("No Furnace configuration file found and we are not building from a git repository.")
    
    if ctx.invoked_subcommand is None:
        logging.debug("No subcommand invoked. Calling build().")
        ctx.invoke(build)

@furnace.command()
@click.pass_context
def update(ctx):
    """`git pull` the project's repository."""
    targ = str(ctx.obj['project_root'])
    cmd = "git -C %s pull origin" % (targ, )
    logging.info("Running '%s'." % cmd)
    ret = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logging.debug("Finished 'git pull': %s" % ret.stdout.decode())
    if ret.returncode != 0:
        raise RuntimeError("Failed to pull repository. Error: %s" % ret.stderr.decode())
    _load_config(ctx, ctx.obj['config_file'])

@furnace.command()
@click.argument("repository", required=False)
@click.option('--no-update', '-n', is_flag=True, 
                help=r"Do not `git pull` this repository.")
@click.option('--no-fetch', '-N', is_flag=True,
                help=r"Do not pull or clone any git repositories. Implies -n.")
@click.option('--no-outside-tasks', '-o', is_flag=True,
                help=r"Do not execute pre- or post-processing tasks.")
@click.pass_context
def build(ctx, repository, no_update, no_fetch, no_outside_tasks):
    """Build the entire site from scratch.
    
    Completes all other steps; this is done by 
    default if no other command is specified.
    
    If <repository> is provided, it is assumed to be the URL of a git repository; it
    will be cloned into a subdirectory of the current directory, then the furnace project
    there will be built. The `project` and `data` arguments provided to `furnace` will be
    interpreted relative to the repository's root."""
    logging.debug("Beginning build()")
    click.echo(r"Running 'furnace build'. (Re)-building entire site.")

    if repository != None:
        logging.debug("cloning %s." % repository)
        localrepo = Path(repository).stem

        logging.debug('local repository directory is %s' % localrepo)
        logging.debug('localrepo:' + str(Path(localrepo)))
        logging.debug('data: ' + str(ctx.obj['data_file']))
        logging.debug('project: ' + str(ctx.obj['config_file']))
        logging.debug('data_file will be %s' % str(Path(localrepo, ctx.obj['data_file'])))
        logging.debug('project config_file will be %s' % str(Path(localrepo, ctx.obj['config_file'])))

        cmd = "git clone %s %s" % (repository, localrepo)
        logging.info("Running '%s'." % cmd)
        ret = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("Finished 'git clone': %s" % ret.stdout.decode())
        if ret.returncode != 0:
            raise RuntimeError("Failed to clone repository. Error: %s" % ret.stderr.decode())
        
        logging.debug('Changing working directory to %s' % localrepo)
        os.chdir(Path(localrepo))
        ctx.obj['config_file'] = ctx.obj['config_file'].resolve()
        _load_config(ctx, ctx.obj['config_file'])
        logging.debug("project config_file '%s' loaded." % str(ctx.obj['config_file']))
        ctx.obj['project_root'] = Path().resolve()
        
        logging.debug("Working directory changed to %s" % str(Path().resolve()))
        
        # Do some error checking before we spend an hour downloading gigabytes of data.
        if not ctx.obj['data_file'].parent.exists():
            #TODO: Should I just make it instead?
            logging.error("Data file %s's parent directory does not exist" % str(ctx.obj['data_file']))
            raise FileNotFoundError("Data file %s's parent directory does not exist.")
        
        #Verify we can touch this file before we go further.
        ctx.obj['data_file'].touch(exist_ok=True)
        logging.debug("Data file: %s" % str(ctx.obj['data_file'].resolve()))
        
        if not Path(ctx.obj['config_file']).exists():
            raise FileNotFoundError("No furnace project found at %s." % str(Path(ctx.obj['config_file'])))
    elif not ctx.obj.get('settings', False):
        raise FileNotFoundError("No furnace project found.")

    logging.debug("Settings: " + str(ctx.obj['settings']))
    logging.debug("Building. Project root: %s" % str(ctx.obj['project_root']))

    if not (no_update or no_fetch or repository):
        ctx.invoke(update)

    #ctx.invoke(clear)

    if not no_fetch:
        ctx.invoke(fetch)
    
    if not no_outside_tasks:
        ctx.invoke(preprocess)
    ctx.invoke(collect)
    ctx.invoke(static)
    ctx.invoke(generate)

    if not no_outside_tasks:
        ctx.invoke(postprocess)
    
    click.echo("Building complete.")
    logging.debug("Ending build()")

#TODO: Finish and test.
'''
@furnace.command()
@click.pass_context
def clear(ctx):
    """Deletes all contents of the output directory.

    Preserves files matching the patterns in settings.clear.exclude"""

    #NOTE: os.walk() is our friend. Maybe also fnmatch.fnmatch().


    outdir = _output_dir(ctx)
    click.echo("Clearing the output directory.")
    excludes = ctx.obj['settings'].get('clear', {}).get('exclude', [])
    logging.debug("Excludes: " + str(excludes))
    def exclude_path(pth):
        """Do any of the patterns match pth?"""
        for pat in excludes:
            if pth.match(pat):
                return True
        return False

    for dr in [x for x in outdir.iterdir() if x.is_dir() and not exclude_path(x.resolve())]:
        shutil.rmtree(str(dr.resolve()))
    
    for fl in [x for x in outdir.iterdir() if x.is_file()]:
        os.unlink(str(fl.resolve()))
'''
        
@furnace.command()
@click.pass_context
def preprocess(ctx):
    """Runs all preprocessing directives."""
    #TODO: Should be an option to supress exceptions here.
    outdir = _output_dir(ctx)
    logging.debug("Preprocess: Output dir: %s" % outdir)
    click.echo("Running preprocess tasks.")
    commands = ctx.obj['settings'].get('preprocess', [])
    process(commands)

@furnace.command()
@click.pass_context
def fetch(ctx):
    """Fetches git repositories."""
    #For now we'll use subprocess.run(). Is there any benefit to dulwich instead?
    #TODO: should probably put this logic in separate modules so we can support svn, fossil, SFTP, etc. sources.
    #TODO: git might should support checking out specific branches/tags.

    click.echo('Fetching repositories.')

    repositories = ctx.obj['settings']['repositories']
    logging.info('Pulling %d repositories.' % len(repositories))

    for repo in repositories:
        if not Path(repo['target']).exists():
            targ = str(Path(repo['target']).resolve())
            rootdir = str(Path(repo['target']).resolve().parent)
            cmd = "git -C %s clone %s %s" % (rootdir, repo['remote'], targ)
            logging.info('%s does not exist; cloning %s into it.' % (repo['target'], repo['remote']))
            logging.debug("Running '%s'." % cmd)
            ret = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.debug("Finished 'git clone': %s" % ret.stdout.decode())
            if ret.returncode != 0:
                raise RuntimeError("Failed to clone repository. Error: %s" % ret.stderr.decode())
        else: 
            targ = str(Path(repo['target']).resolve())
            cmd = "git -C %s pull" % (targ, )
            logging.info("Running '%s'." % cmd)
            ret = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.debug("Finished 'git pull': %s" % ret.stdout.decode())
            if ret.returncode != 0:
                raise RuntimeError("Failed to pull repository. Error: %s" % ret.stderr.decode())

@furnace.command()
@click.pass_context
def collect(ctx):
    """Collects all datasources.
    
    Collects all data described in furnace.project.yaml under data-sources
    into the xml file specified by --data. Does not imply `fetch`."""
    click.echo("Collecting data")
    outdir = _output_dir(ctx)
    logging.debug("Collecting. Output dir: %s" % outdir)
    xmlroot = ET.Element('furnace-data')
    
    projroot = ET.SubElement(xmlroot, 'furnace-config')

    #Convert our settings file to XML and add to the XML data document.
    dict2xml(ctx.obj['settings'], projroot)

    dssroot = ET.SubElement(xmlroot, 'data-sources')
    dss = ctx.obj['settings']['data-sources']
    for dsname, ds in dss.items():
        logging.info("Collecting datasource '%s'." % dsname)
        #TODO: Dynamically load modules to deal with different DS types.
        dsroot = ET.SubElement(dssroot, dsname)
        if 'filesystem' == ds['type']:
            handle_filesystem_datasource(ds, dsroot)

    data_file = ctx.obj['data_file']

    logging.info('Writing XML data to %s.' % str(data_file))
    data_file.touch(exist_ok=True)
    with data_file.open(mode="wb") as outpfile:
        outpfile.write(ET.tostring(xmlroot, pretty_print=True))
    
    #No need to read this if it's already in memory.
    ctx.obj['xmldata'] = xmlroot
    
@furnace.command()
@click.pass_context
def static(ctx):
    """Copies static directories into output."""
    click.echo("Handling static files.")
    outdir = _output_dir(ctx)
    logging.debug("Moving static files. Output dir: %s" % outdir)
    sss = ctx.obj['settings']['static-sources']
    logging.info('Deleting static directories')
    for ssname, ss in sss.items():
        if ss['target'] != '':
            target = Path(outdir, ss['target']).resolve()
            logging.debug("Deleting %s." % target)
            if target.exists():
                #TODO: Why does this sometimes throw errors if I don't ignore_errors?
                shutil.rmtree(target, ignore_errors=False)

    logging.info('Copying static files.')
    for ssname, ss in sss.items():
        source = Path(ss['source']).resolve()
        target = Path(ctx.obj['project-output'], ss['target']).resolve()
        logging.debug("Moving " + str(source) + ' to ' + str(target) + ".")
        copy_tree(str(source), str(target))

@furnace.command()
@click.pass_context
def generate(ctx):
    """Generates pages from XSL templates. Does not imply `collect` and will fail if the file specified by --data doesn't exist."""
    click.echo('Generating pages.')
    outdir = _output_dir(ctx)
    logging.debug("Generating. Output directory: %s" % str(outdir))

    pages = ctx.obj['settings']['pages']

    data_file = ctx.obj['data_file']
    
    if 'xmldata' in ctx.obj:
        logging.debug("Using previously-loaded data.")
    else:
        logging.debug("Reading data from %s" % str(data_file))
        with  data_file.open("rb") as fl:
            fdata = fl.read()
        ctx.obj['xmldata'] = ET.fromstring(fdata, HUGE_PARSER)
    data = ctx.obj['xmldata']
    
    for pagename, page in pages.items():
        logging.info("Generating page '%s'." % pagename)
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
            target = Path(outdir, flname)
            
            if not target.parent.exists():
                target.parent.mkdir(parents=True)
            
            logging.debug("Outputting "+str(target))
            #with target.open('wb') as f:
            result.write_output(str(target))

@furnace.command()
@click.pass_context
def postprocess(ctx):
    """Runs all postprocessing directives."""
    #TODO: Should be an option to supress exceptions here.
    outdir = _output_dir(ctx)
    logging.debug("Postprocessing. Output dir: %s" % outdir)
    click.echo("Running postprocess tasks.")
    commands = ctx.obj['settings'].get('postprocess', [])
    process(commands)

if __name__ == '__main__':
    STARTED_IN = Path().resolve()
    furnace()
    os.chdir(STARTED_IN)