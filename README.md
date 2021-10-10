# simple-editor
GUI-editor for Python development. 
Tested to work with Debian Buster and Bullseye. 
It is meant to be used from Python console rather than standalone.
* Update: finally fixed search/replace titles, dumped hdpi-hassle, made shortcut for scrollbar width adjustment

# Featuring
* Indent - Unindent
* Comment - Uncomment
* Search - Replace
* Auto-indent
* Run current file
* Click to open errors
* Font Chooser


# Lacking and not going to implement
* Autocompletion
* Hinting
* Linenumbering
* Syntax highlighting

# Installing and running
debian-packages required: python3-tk

```console
foo@bar:~$ sudo apt install python3-tk git
foo@bar:~$ git clone https://github.com/SamuelKos/simple-editor
foo@bar:~$ cd simple-editor
foo@bar:~/simple-editor$ python3 simple_editor.py
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
