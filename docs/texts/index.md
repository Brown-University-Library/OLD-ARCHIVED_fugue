---
title: Introduction
---

## Overview

_Fugue_ is a Python-based static site generator that uses XSLT as its template language, somewhat inspired by the [Symphony CMS](https://www.getsymphony.com/). The target use case is website creation from a collection of XML documents (e.g. a book written in [DocBook](https://docbook.org/whatis) or [TEI](https://tei-c.org/), or a collection of EAD or EAC-CPF finding aids).

## What it Does

When you run `fugue` in a directory with a git repository and a `fugue.project.yaml` file, it performs a set of tasks as directed by that file. The project directory will generally contain the project settings file, your XSL templates, and any other scripts needed to build your site. 

Each of these tasks can also be performed individually (e.g. `fugue preprocess`). See [todo] for more details.

#### Task `update`

Runs `git pull` from the project directory then and rereads the `fugue.project.yaml` file. 

#### Task `fetch`

`pull`s or `clone`s the repositories listed in the settings under `repositories`. These repos will generally contain the data needed to create your site and any static files needed to build it.

#### Task `preprocess`

Executes the tasks in the settings file under `preprocess`. Anything you need to happen before files are collected into Fugue's data file (the XML document your XSL templates will run against) will go here.

#### Task `collect`

Reads the files in locations listed under `data-sources` in the settings file. In addition to XML files, Fugue can handle CSV, JSON, [todo] YAML, and [todo] Markdown files. All the data in these files is included into the `fugue-data.xml` document, which is provided as the source for your XSLT templates.

#### Task `static`

Copies the directories listed under `static-sources` to their final locations in your site's target directory.

#### Task `generate` 

Uses the XSL templates listed under `pages` to generate their output files.

#### Task `postprocess`

Runs the tasks under `postprocess`. These might rsync your site to a final location, generate a [Lunr](https://lunrjs.com/) search index, create image derivatives required by your finished site, etc.

## Installation

Requires Python 3.6 or newer.

You should be able to install with `pip` [todo: put on pypi]:

`pip install [todo]`