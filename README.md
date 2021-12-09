# simple-editor
GUI-editor for Python development. 
Tested to work with Debian Bullseye. 
* Walk-tabs is now Alt-tab instead of Ctrl-tab. Toggle theme is now Alt-t.
* Windows support plan has raised again, now that I managed to setup Microsoft's own virtual machine image for win7. I previously tried with Wine with strange behaviour (it was related to tkinter.Tk().withdraw() positioning), can not say where was the problem, anyway, it is now gone and I can now test in Windows.

# Featuring
* Auto-indent
* Font Chooser
* Color Chooser
* Tabbed editing
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

# Installing
debian-packages required: python3-tk

```console
foo@bar:~$ sudo apt install python3-tk git
foo@bar:~$ git clone https://github.com/SamuelKos/simple-editor
```

Running from Python-console:

```console
>>> import simple_editor
>>> e=simple_editor.Editor()
```

# Licence
This project is licensed under the terms of the GNU General Public License v3.0.
