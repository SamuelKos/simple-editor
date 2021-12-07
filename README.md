# simple-editor
GUI-editor for Python development. 
Tested to work with Debian Bullseye. 
* walk-tabs is now Alt-tab instead of Ctrl-tab.
* Filepaths are now saved to disk as relative paths so more flexibility if for example editing in different environments etc.
* They are also changed to pathlib.Path-objects so this might work in Windows, have not tested it yet.
* Because changes in save(), current state might be unsafe
* Other fixes

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
