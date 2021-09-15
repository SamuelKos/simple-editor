# Simple PYthon Development Editor
GUI-editor for Python.
Tested to work with Debian Buster and Bullseye.
It is meant to be used from Python console rather than standalone.

# Featuring
* Indent - Unindent
* Comment - Uncomment
* Search - Replace
* Auto-indent
* Run current file
* Click to open errors
* etc

# Lacking and not going to implement
* Autocompletion
* Hinting
* Linenumbering
* Syntax highlighting

# Maybe TODO
* Multicursor edit or something similar

# Installing and running
debian-packages required: python3-tk

```console
foo@bar:~$ sudo apt install python3-tk
```

Download spyde.py and run with:

```console
foo@bar:~$ python3 spyde.py
```

Running from Python console:

```console
>>> import spyde
>>> from tkinter import Tk
>>> root=Tk().withdraw()
>>> e=spyde.Editor(root)
```

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
