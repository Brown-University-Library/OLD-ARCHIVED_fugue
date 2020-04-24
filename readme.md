# Fugue: XSLT-based site generator

_Fugue_ is a Python-based static site generator that uses XSLT as 
its template language, somewhat inspired by the [Symphony CMS](https://www.getsymphony.com/). 
The target use case is website creation from a collection of XML documents 
(e.g. a book written in [DocBook](https://docbook.org/whatis) or [TEI](https://tei-c.org/), 
or a collection of EAD or EAC-CPF finding aids).

It was developed at Brown University Library for the 
[Furnace and Fugue](https://library.brown.edu/create/digitalpublications/current-projects/furnace-and-fugue/) 
project.

```
Usage: fugue [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Static site generator using XSL templates.

Options:
  -L, --log-level [CRITICAL|ERROR|WARNING|INFO|DEBUG]
                                  Set logging level. Defaults to WARNING.
  -p, --project PATH              Choose the project configuration file.
                                  Defaults to ./fugue.project.yaml. Ignored
                                  if `fugue build` is called with a
                                  repository URL.
  -d, --data PATH                 Choose the data file fugue will create and
                                  use. Defaults to ./fugue-data.xml. Ignored
                                  if `fugue build` is called with a
                                  repository URL.
  --help                          Show this message and exit.

Commands:
  build        Build the entire site from scratch.
  collect      Collects all datasources.
  fetch        Fetches git repositories.
  generate     Generates pages from XSL templates.
  postprocess  Runs all postprocessing directives.
  preprocess   Runs all preprocessing directives.
  static       Copies static directories into output.
  update       `git pull` the project's repository.
```