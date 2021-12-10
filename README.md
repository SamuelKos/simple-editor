# simple-editor
GUI-editor for Python development. 
Tested to work with Debian Bullseye
* Windows support is dumped. The strange problem with setting an icon comes back with win10, tried both 64 and 32 bit versions.

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
