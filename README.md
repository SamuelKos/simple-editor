# simple-editor
GUI-editor for Python development
Tested to work with Debian Buster and Bullseye.
It is meant to be used from Python console rather than standalone.

# Featuring
* Indent - Unindent
* Comment - Uncomment
* Search - Replace
* Auto-indent
* Run current file
* Click to open errors


# Lacking and not going to implement
* Autocompletion
* Hinting
* Linenumbering
* Syntax highlighting

# Installing and running
debian-packages required: python3-tk

```console
foo@bar:~$ sudo apt install python3-tk
```

Download simple_editor.py and run with:

```console
foo@bar:~$ python3 simple_editor.py
```

Running from Python console:

```console
>>> import simple_editor
>>> from tkinter import Tk
>>> root=Tk().withdraw()
>>> e=simple_editor.Editor(root)
```

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
