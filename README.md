VisWeek 2013 Contest Scripts
============================

Use the scripts in this repository to download the developing mouse data for the VisWeek 2013 visualization contest.

A full description of this data set can be found at the official site for the contest:

http://sciviscontest.visweek.org/2013

To download the data set, simply run:

$ python download_data.py

This will probably take multiple hours.  Files will be downloaded into the current working directory with the following structure:

* energy/ - a directory full of expression energy Meta images, one for each probe in 6 development stages chosen for this contest.
* meta/ - a directory containing meta data on probes (data_sets.csv) and structures (structures.csv).
* atlas/ - a directory containing reference atlas volumes, one for each developmental stage.
* annotation/ - a directory containing grid annotation volumes, one for each developmental stage.  Voxel values are structure ids.
* structure_unionizes/ - a directory containing one CSV per probe.  Each CSV contains a set of rows describing the expression energy for a probe within an entire structure.

Note: this python script has only been tested with python 2.7.2.  