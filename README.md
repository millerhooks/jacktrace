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
### CuFlow looks promising
https://excamera.com/sphinx/article-cuflow-crossbar.html

### Visolate: Voronoi Toolpaths for PCB Etching
https://groups.csail.mit.edu/drl/wiki/index.php?title=Visolate:_Voronoi_Toolpaths_for_PCB_Mechanical_Etch

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

