# simple-editor
GUI-editor for Python development. 
Tested to work with Debian Buster and Bullseye. 
* Update: Trying to add tabbed editing. State is: in progress..

# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Run current file
* Search - Replace
* Indent - Unindent
* Comment - Uncomment
* Click to open errors
* Persistent configuration

# Lacking and not going to implement
* Auto-completion
* Hinting
* Line numbering
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
