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

### Visolate: Voronoi Toolpaths for PCB Etching
https://groups.csail.mit.edu/drl/wiki/index.php?title=Visolate:_Voronoi_Toolpaths_for_PCB_Mechanical_Etch

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

Image Example Assets
====================
Big Wave Vector PDF and some process files from a test run.

