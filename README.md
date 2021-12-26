test for generating stylized circuit traces from images
=======================================================
Author: Miller Hooks - 12.26.2021

Concept
-------
image -> split into plates via dithering -> make image positives, negatives and masks -> halftone as needed -> voronoi stippling -> make traces - rinse/repeat

Source
------
Some python for doing some dithering and a dockerfile to make a CUDA docker container as a start, just in case GPU is needed.

Voronoi Stippling and Tracefinding
----------------------------------

### StippleGen2
https://github.com/evil-mad/stipplegen/releases/tag/v2.31

Dithering
---------
https://scipython.com/blog/floyd-steinberg-dithering/
https://en.wikipedia.org/wiki/Floyd%E2%80%93Steinberg_dithering
Example in Source directory

TODO
====
Meshroom Workflow and Interface
-------------------------------
This seems to mirror functionally, how I see a good process for doing this working. Also it's open source and python 
with a QT interface so it could be aped entirely or just make the tool a plugin for Meshroom or somethign.

https://meshroom-manual.readthedocs.io/en/latest/feature-documentation/gui/index.html

Halftones
--------
https://github.com/philgyford/python-halftone

Traces
-----
https://github.com/vygr/Python-PCB

### SKiDL
https://hackaday.com/2016/12/28/skidl-script-your-circuits-in-python/
https://devbisme.github.io/skidl/
https://github.com/devbisme/skidl
https://xess.com/blog/are-you-in-an-abusive-relationship-with-your-schematic-editor/

### SAT Router
monosat_router.py - https://gist.github.com/nmz787/10c60e76941a8e5de624454666ea65b3
cryptominisat_router.py - https://gist.github.com/nmz787/ae4a6121ce4aa42c2caed5b062b97c70#file-cryptominisat_router-py 
Based on this paper "Scalable, High-Quality, SAT-Based Multi-Layer Escape Routing" - https://dl.acm.org/doi/10.1145/2966986.2967072

### PCBFlow
Looks nice. Based on CuFlow
https://github.com/michaelgale/pcbflow

### CuFlow looks promising
https://excamera.com/sphinx/article-cuflow-crossbar.html

### Visolate: Voronoi Toolpaths for PCB Etching
https://groups.csail.mit.edu/drl/wiki/index.php?title=Visolate:_Voronoi_Toolpaths_for_PCB_Mechanical_Etch

### KiCAD... Just use KiCAD. It's made by CERN
https://www.kicad.org/

Nice Containerized KiCAD for scripting. https://github.com/productize/kicad-automation-scripts
https://github.com/devbisme/kicad-3rd-party-tools#layout-tools

This looks like the business
https://forum.kicad.info/t/announcing-kicad-freerouting-plugin/16799


### or use PCBModE. It's Pretty
https://boldport.com/pcbmode
https://pcbmode.com/
https://hackaday.com/tag/pcbmode/

### Selecting Via Points to Join
* Select a region via layer mask
* Select via points as a pseudo-random distrobution as FROM vias
* Select TO viasvia some sort of drunkards walk to a f(x) of min/mean/max neighbors
* Route paths
* group new joined traces and vias and ignore
* repeat until no vias remain. If number of vias is odd, drop the last one

Image Example Assets
====================
Big Wave Vector PDF and some process files from a test run.

