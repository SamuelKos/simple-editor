#TODO:

# show i/num in title in normal state
# shortcut for: (do last search from cur pos, show next, select, exit)
# 	because current search is not too useful
#	ctrl-backspace, then easy to delete and ctrl-v and continue 
# check shortcuts
# check copy paste indentation problem

# from standard library
import tkinter.scrolledtext
import tkinter.filedialog
import tkinter.font
import tkinter
import random
import json
import os

# from current directory
import changefont

# for executing edited file in the same env than this editor, which is nice:
# It means you have your installed dependencies available. By self.run()
import subprocess

class Tab:
	'''	Represents a tab-page of an Editor-instance
	'''
	
	def __init__(self, **entries):
		self.active = True
		self.filepath = None
		self.contents = ''
		self.position = '1.0'
		self.type = 'newtab'
		
		self.__dict__.update(entries)
		
		
	def __str__(self):
	
		return	'\nfilepath: %s\nactive: %s\ntype: %s\nposition: %s' % (
				str(self.filepath),
				str(self.active),
				self.type,
				self.position
				)
				
	
###############################################################################
# config(**options) Modifies one or more widget options. If no options are
# given, method returns a dictionary containing all current option values.
#
# https://www.tcl.tk/man/tcl8.6/TkCmd/event.htm
# https://docs.python.org/3/library/tkinter.html
#
# If you are about to use tkinter Python-module, consider
# using some other GUI-library like Qt, GTK
# or completely different language like Tcl to name one. 
###############################################################################

ICONPATH = r"./icons/editor.png"
CONFPATH = r"./editor.cnf"
HELPTEXT = '''		Keyboard shortcuts:

		Ctrl-f  Search
		Ctrl-r  Replace
		Ctrl-R  Replace all
		Ctrl-g  Gotoline
				
		Ctrl-C  Comment
		Ctrl-X  Uncomment
		Ctrl->  Indent
		Ctrl-<  Unindent
		
		Ctrl-a  Select all
		Ctrl-c  Copy
		Ctrl-v  Paste
		Ctrl-z  Undo
		Ctrl-Z  Redo
		
		Ctrl-p  Font setting
		Ctrl-s  Color setting
		Ctrl-t  Toggle color setting
		
		Ctrl-n  Open new tab
		Ctrl-d  Close current tab
		Ctrl-w  Walk tabs
		
		Ctrl-plus 	Increase scrollbar-width
		Ctrl-minus	Decrease scrollbar-width

		While searching:
		Alt-n  Next match
		Alt-p  Prev match
		
		Is my file Saved? It is when:
		- closing program, also configurations
		- closing tab
		- creating a new tab
		- changing tabs (walking)
		- pressing save-button:
			If a file was already open and user changed filename in entry,
			old file is first saved and then new file with same content
			is created in current tab. Old file is closed from opened tabs.
		- it also should be saved when loading file
		  
		'''

			
class Editor(tkinter.Toplevel):

	def __init__(self):
		self.root = tkinter.Tk().withdraw()
		super().__init__(self.root, class_='Simple Editor')
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		self.titletext = 'Simple Editor'
		self.title(self.titletext)
		self.tabs = list()
		self.tabindex = None
		
		self.bgdaycolor = r'#D3D7CF'
		self.fgdaycolor = r'#000000'
		self.bgnightcolor = r'#000000'
		self.fgnightcolor = r'#D3D7CF'
		self.fgcolor = self.fgdaycolor
		self.bgcolor = self.bgdaycolor
		self.curcolor = 'day'

		self.replace_overlap_index = None
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
		self.old_word = ''
		self.new_word = ''
		self.errlines = list()
		self.state = 'normal'
		
		if ICONPATH:
			try:
				self.pic = tkinter.Image("photo", file=ICONPATH)
				self.tk.call('wm','iconphoto', self._w, self.pic)
			except tkinter.TclError as e:
				print(e)
		
		self.helptxt = HELPTEXT
		
		# Layout Begin:
		####################################################
		# IMPORTANT if binding to 'root': 
		# https://stackoverflow.com/questions/54185434/python-tkinter-override-default-ctrl-h-binding
		# Found this when wondering what is happening when ctrl-t was used.
		# It did the callback but also something unwanted..
		# https://unix.stackexchange.com/questions/330414/intended-use-of-ctrlt-in-bash
		# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/binding-levels.html
		# I use this with ctrl-t after self.contents is packed below.
		# But with ctrl-U this did not work, so changed to ctrl-X
		 
		self.bind("<Control-minus>", self.decrease_scrollbar_width)
		self.bind("<Control-plus>", self.increase_scrollbar_width)
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Control-R>", self.replace_all)
		self.bind("<Button-3>", self.raise_popup)
		self.bind("<Control-g>", self.gotoline)
		self.bind("<Control-r>", self.replace)
		self.bind("<Control-f>", self.search)
		self.bind("<Control-p>", self.font_choose)
		self.bind("<Control-s>", self.color_choose)
		self.bind("<Control-n>", self.new_tab)
		self.bind("<Control-d>", self.del_tab)
		self.bind("<Alt-l>", self.show_debug)
		self.bind("<Control-w>", self.walk_files)
		
		self.contents = tkinter.scrolledtext.ScrolledText(self, background=self.bgcolor, foreground=self.fgcolor, insertbackground=self.fgcolor, blockcursor=True, tabstyle='wordprocessor', undo=True, maxundo=-1, autoseparators=True)
		
		self.contents.tag_config('match', background='lightyellow', foreground='black')
		self.contents.tag_config('found', background='lightgreen')
		
		self.contents.bind("<Return>", self.return_override)
		self.contents.bind("<Control-C>", self.comment)
		self.contents.bind("<Control-X>", self.uncomment)
		self.contents.bind("<Control-greater>", self.indent)
		self.contents.bind("<Control-less>", self.unindent)
		self.contents.bind("<Control-a>", self.select_all)
		self.contents.bind("<Control-z>", self.undo_override)
		self.contents.bind("<Control-Z>", self.redo_override)
		
		self.contents.pack(side=tkinter.BOTTOM, expand=True, fill=tkinter.BOTH)
		
		bindtags = self.contents.bindtags()
		self.contents.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3]))
		self.bind("<Control-t>", self.toggle_color)
		
		self.popup_whohasfocus = None
		self.popup = tkinter.Menu(self, tearoff=0, bd=0, activeborderwidth=0)
		self.popup.bind("<FocusOut>", self.popup_focusOut) # to remove popup when clicked outside
		self.popup.add_command(label="        copy", command=self.copy)
		self.popup.add_command(label="       paste", command=self.paste)
		self.popup.add_command(label="<<  unindent", command=self.unindent)
		self.popup.add_command(label=">>    indent", command=self.indent)
		self.popup.add_command(label="##   comment", command=self.comment)
		self.popup.add_command(label="   uncomment", command=self.uncomment)
		self.popup.add_command(label="      errors", command=self.show_errors)
		self.popup.add_command(label="         run", command=self.run)
		self.popup.add_command(label="        help", command=self.help)
		
		self.entry = tkinter.Entry(self)
		self.entry.bind("<Return>", self.load)
		self.entry.pack(side=tkinter.LEFT, expand=True, fill=tkinter.X)
		self.btn_open=tkinter.Button(self, text='Open', command=self.load)
		self.btn_open.pack(side=tkinter.LEFT)
		self.btn_save=tkinter.Button(self, text='Save', command=self.save)
		self.btn_save.pack(side=tkinter.LEFT)
		
		# Set Font Begin ##################################################
		self.fontname = None
		self.randfont = False
		
		self.goodfonts = [
					'Noto Mono',
					'Bitstream Vera Sans Mono',
					'Liberation Mono',
					'Inconsolata'
					]
		
		self.badfonts = [
					'Standard Symbols PS',
					'OpenSymbol',
					'Noto Color Emoji',	# This one is really bad, causes segfault and hard crash (killed by OS)
					'FontAwesome',
					'Droid Sans Fallback',
					'D050000L'
					]
					
		fontfamilies = [f for f in tkinter.font.families() if f not in self.badfonts]
		random.shuffle(fontfamilies)
		
		for fontname in self.goodfonts:
			if fontname in fontfamilies:
				self.fontname = fontname
				break
		
		if self.fontname == None: 
			self.fontname = fontfamilies[0]
			self.randfont = True
		
		# Initialize rest of configurables
		self.font = tkinter.font.Font(family=self.fontname, size=12)
		self.menufont = tkinter.font.Font(family=self.fontname, size=10)
		self.scrollbar_width = 30
		self.elementborderwidth = 4	
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)
		
		self.tab_width = self.font.measure(4*' ') #############################
		self.contents.config(font=self.font, foreground=self.fgcolor,
			background=self.bgcolor, insertbackground=self.fgcolor, 
			tabs=(self.tab_width, ))
		self.entry.config(font=self.menufont)
		self.btn_open.config(font=self.menufont)
		self.btn_save.config(font=self.menufont)
		self.popup.config(font=self.menufont)
		
		# Try to apply saved configurations:
		try:
			with open(CONFPATH, 'r', encoding='utf-8') as f:
				self.load_config(f)
				self.randfont = False
		except FileNotFoundError: pass
		except EnvironmentError as e:
			print(e.__str__())	# __str__() is for user (print to screen)
			#print(e.__repr__())	# __repr__() is for developer (log to file)
			print('\n Could not load existing configuration file %s' % CONFPATH)
			
		if self.randfont == True:
			print(f'WARNING: RANDOM FONT NAMED "{self.fontname.upper()}" IN USE. Select a better font with: ctrl-p')
		
		# if no conf:
		if self.tabindex == None:
			self.tabindex = -1
			self.new_tab()

		############################# init End ######################
		

	def do_nothing(self, event=None):
		self.bell()
		return 'break'
		
		
	def quit_me(self):
		self.save(forced=True)
		self.save_config()
		self.quit()
		self.destroy()
		
		
	def show_debug(self, event=None):
		tmptop = tkinter.Toplevel()
		tmptop.title('Show Debug')
		tmptop.label = tkinter.Label(tmptop, text='LABEL', font=('TkDefaultFont', 16))
		tmptop.label.pack()

############## Tab Related Begin

	def new_tab(self, event=None, error=False):
		#print(
		#event.char,
		#event.keycode,
		#event.keysym,
		#event.keysym_num,
		#event.num,
		#event.type
		#)
		
		# event == None when clicked hyper-link in tag_link()
		if self.state != 'normal' and event != None:
			self.bell()
			return
	
		if len(self.tabs) > 0  and not error:
			tmp = self.contents.get('1.0', tkinter.END)
			self.tabs[self.tabindex].contents = tmp
			
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
				
			self.tabs[self.tabindex].position = pos
		
		
		self.contents.delete('1.0', tkinter.END)
		self.entry.delete(0, tkinter.END)
		
		if len(self.tabs) > 0:
			self.tabs[self.tabindex].active = False
			
		newtab = Tab(active=True, filepath=None, contents='', position='1.0', type='newtab')
		
		self.tabindex += 1
		self.tabs.insert(self.tabindex, newtab)
		
		self.contents.focus_set()
		self.contents.see('1.0')
		self.contents.mark_set('insert', '1.0')
		
		return 'break'
		
		
	def del_tab(self, event=None):

		if ((len(self.tabs) == 1) and self.tabs[self.tabindex].type == 'newtab') or (self.state != 'normal'):
			self.bell()
			return 'break'

		if self.tabs[self.tabindex].type == 'normal':
			self.save(deltab=True)
			
		self.tabs.pop(self.tabindex)
		self.contents.delete('1.0', tkinter.END)
		self.entry.delete(0, tkinter.END)
			
		if (len(self.tabs) == 0):
			newtab = Tab(active=True, filepath=None, contents='', position='1.0', type='newtab')
			self.tabs.append(newtab)
	
		if self.tabindex > 0:
			self.tabindex -= 1
	
		self.tabs[self.tabindex].active = True

		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)

		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
			
		self.contents.edit_reset()
		
		return 'break'

		
	def walk_files(self, event=None):
	
		if self.state != 'normal' or len(self.tabs) < 2:
			self.bell()
			return "break"
			
		self.tabs[self.tabindex].active = False
		
		tmp = self.contents.get('1.0', tkinter.END)
		self.tabs[self.tabindex].contents = tmp
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
			
		self.tabs[self.tabindex].position = pos

		idx = self.tabindex
		if idx == len(self.tabs) - 1:
			idx = -1
		idx += 1
		
		self.tabindex = idx
		self.tabs[self.tabindex].active = True

		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.entry.delete(0, tkinter.END)
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			self.contents.mark_set('insert', line)
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
			
		self.contents.edit_reset()
		
		return 'break'

########## Tab Related End
########## Configuration Related Begin

	def save_config(self, event=None):
		try:
			with open(CONFPATH, 'w', encoding='utf-8') as f:
				data = self.get_config()
				string_representation = json.dumps(data)
				f.write(string_representation)
		except EnvironmentError as e:
			print(e.__str__())
			print('\nCould not save configuration')

	
	def load_config(self, fileobject):
		string_representation = fileobject.read()
		data = json.loads(string_representation)
		self.set_config(data)
		self.apply_config()
		
		
	def get_config(self):
		dictionary = dict()
		
		dictionary['fgcolor'] = self.contents.cget('foreground')
		dictionary['bgcolor'] = self.contents.cget('background')
		dictionary['fgdaycolor'] = self.fgdaycolor
		dictionary['bgdaycolor'] = self.bgdaycolor
		dictionary['fgnightcolor'] = self.fgnightcolor
		dictionary['bgnightcolor'] = self.bgnightcolor
		dictionary['curcolor'] = self.curcolor
		dictionary['font'] = self.font.config()
		dictionary['menufont'] = self.menufont.config()
		dictionary['scrollbar_width'] = self.scrollbar_width
		dictionary['elementborderwidth'] = self.elementborderwidth
		
		for tab in self.tabs:
			tab.contents = ''
			
		tmplist = [ tab.__dict__ for tab in self.tabs ]
		dictionary['tabs'] = tmplist
		
		return dictionary
		
		
	def set_config(self, dictionary):
		self.fgnightcolor = dictionary['fgnightcolor']
		self.bgnightcolor = dictionary['bgnightcolor']
		self.fgdaycolor = dictionary['fgdaycolor'] 
		self.bgdaycolor = dictionary['bgdaycolor'] 
		self.fgcolor = dictionary['fgcolor']
		self.bgcolor = dictionary['bgcolor']
		self.curcolor = dictionary['curcolor']
		
		self.font.config(**dictionary['font'])
		self.menufont.config(**dictionary['menufont'])
		self.scrollbar_width 	= dictionary['scrollbar_width']
		self.elementborderwidth	= dictionary['elementborderwidth']
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)

		self.tabs = [ Tab(**item) for item in dictionary['tabs'] ]
		
		for tab in self.tabs:
			if tab.type == 'normal':
				try:
					with open(tab.filepath, 'r', encoding='utf-8') as f:
						tab.contents = f.read()
				except EnvironmentError as e:
					print(e.__str__())
					self.tabs.remove(tab)
					
					
		for i,tab in enumerate(self.tabs):
			if tab.type == 'normal' and tab.active == True:
				self.tabindex = i
				break
				

	def apply_config(self):
	
		self.tab_width = self.font.measure(4*' ') #############################
		self.contents.config(font=self.font, foreground=self.fgcolor,
			background=self.bgcolor, insertbackground=self.fgcolor, 
			tabs=(self.tab_width, ))
		self.entry.config(font=self.menufont)
		self.btn_open.config(font=self.menufont)
		self.btn_save.config(font=self.menufont)
		self.popup.config(font=self.menufont)

		if self.tabindex == None:
			if len(self.tabs) == 0:
				self.tabindex = -1
				self.new_tab()
				
			# only newtab(s) open:
			else:
				self.tabindex = 0
				self.tabs[self.tabindex].active = True
			
		if self.tabs[self.tabindex].type == 'normal':
			self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
			self.contents.focus_set()
			self.contents.see('1.0')
			self.contents.mark_set('insert', '1.0')
		
########## Configuration Related End
########## Theme Related Begin

	def increase_scrollbar_width(self, event=None):
		'''	Change width of scrollbar of self.contents and of 
			tkinter.filedialog.FileDialog which is used in self.load().
			Shortcut: Ctrl-plus
		'''
		if self.scrollbar_width >= 100:
			self.bell()
			return 'break'
			
		self.scrollbar_width += 7
		self.elementborderwidth += 1
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)
			
		return 'break'
		
		
	def decrease_scrollbar_width(self, event=None):
		'''	Change width of scrollbar of self.contents and of 
			tkinter.filedialog.FileDialog which is used in self.load().
			Shortcut: Ctrl-minus
		'''
		if self.scrollbar_width <= 0:
			self.bell()
			return 'break'
			
		self.scrollbar_width -= 7
		self.elementborderwidth -= 1
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)
			
		return 'break'
		

	def toggle_color(self, event=None):
		if self.curcolor == 'day':
			self.fgcolor = self.fgnightcolor
			self.bgcolor = self.bgnightcolor
		else:
			self.fgcolor = self.fgdaycolor
			self.bgcolor = self.bgdaycolor
			
		if self.curcolor == 'day':
			self.curcolor = 'night'
		else:
			self.curcolor = 'day'
			
		self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
			
		return 'break'
		
			
	def font_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.choose = changefont.FontChooser([self.font, self.menufont])
		return 'break'
		
		
	def color_choose(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		# I am not sure why this works but it is possibly related
		# to fact that there can only be one root window,
		# or actually one Tcl-interpreter in single python-program or -console.
		tmptop = tkinter.Toplevel()
		tmptop.title('Choose Color')
		tmptop.btnfg = tkinter.Button(tmptop, text='Change foreground color', font=('TkDefaultFont', 16), command=lambda args=['fg']: self.chcolor(args))
		tmptop.btnfg.pack(padx=10, pady=10)
		
		tmptop.btnbg = tkinter.Button(tmptop, text='Change background color', font=('TkDefaultFont', 16), command=lambda args=['bg']: self.chcolor(args))
		tmptop.btnbg.pack(padx=10, pady=10)
		
		tmptop.lb = tkinter.Listbox(tmptop, font=('TkDefaultFont', 12), selectmode=tkinter.SINGLE)
		tmptop.lb.pack(pady=10)
		tmptop.choiseslist = ['day', 'night']
		
		for item in tmptop.choiseslist:
			tmptop.lb.insert('end', item)
		
		idx = tmptop.choiseslist.index(self.curcolor)
		tmptop.lb.select_set(idx)
		tmptop.lb.see(idx)
		tmptop.lb.bind('<ButtonRelease-1>', lambda event, args=[tmptop]: self.choose_daynight(args, event))
		
		
	def choose_daynight(self, args, event=None):
		parent = args[0]
		oldcolor = self.curcolor
		self.curcolor = parent.lb.get(parent.lb.curselection())
		
		if self.curcolor != oldcolor:
		
			if self.curcolor == 'day':
			
				self.fgcolor = self.fgdaycolor
				self.bgcolor = self.bgdaycolor
			
			else:
				self.fgcolor = self.fgnightcolor
				self.bgcolor = self.bgnightcolor
			
			self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
		
		
	def chcolor(self, args, event=None):
		
		if args[0] == 'bg':
			tmpcolorbg = tkinter.colorchooser.askcolor(initialcolor=self.bgcolor)[1]
			if tmpcolorbg in [None, '']:
				return 'break'
			
			if self.curcolor == 'day':
				self.bgdaycolor = tmpcolorbg
				self.bgcolor = self.bgdaycolor
			else:
				self.bgnightcolor = tmpcolorbg
				self.bgcolor = self.bgnightcolor
		else:
			tmpcolorfg = tkinter.colorchooser.askcolor(initialcolor=self.fgcolor)[1]
			if tmpcolorfg in [None, '']:
				return 'break'
			
			if self.curcolor == 'day':
				self.fgdaycolor = tmpcolorfg
				self.fgcolor = self.fgdaycolor
			else:
				self.fgnightcolor = tmpcolorfg
				self.fgcolor = self.fgnightcolor
			
		self.contents.config(foreground=self.fgcolor, background=self.bgcolor,
			insertbackground=self.fgcolor)
		
		return 'break'
		
########## Theme Related End
########## Run file Related Begin

	def enter(self, tagname, event=None):
		''' Used in error-page, when mousecursor enters hyperlink tagname.
		'''
		self.contents.config(cursor="hand2")
		self.contents.tag_config(tagname, underline=1)


	def leave(self, tagname, event=None):
		''' Used in error-page, when mousecursor leaves hyperlink tagname.
		'''
		self.contents.config(cursor="")
		self.contents.tag_config(tagname, underline=0)


	def lclick(self, tagname, event=None):
		'''	Used in error-page, when hyperlink tagname is clicked.
		
			self.taglinks is dict with tagname as key
			and function (self.taglink) as value.
		'''
		
		# passing tagname-string as argument to function self.taglink()
		# which in turn is a value of tagname-key in dictionary taglinks: 
		self.taglinks[tagname](tagname)
		

	def tag_link(self, tagname, event=None):
		''' Used in error-page, executed when hyperlink tagname is clicked.
		'''
		
		i = int(tagname.split("-")[1])
		filepath, errline = self.errlines[i]
		
		openfiles = [tab.filepath for tab in self.tabs]
		
		if filepath == self.tabs[self.tabindex].filepath:
			pass
			
		elif filepath in openfiles:
			for i,tab in enumerate(self.tabs):
				if tab.filepath == filepath:
					self.tabs[self.tabindex].active = False
					self.tabindex = i
					self.tabs[self.tabindex].active = True
					break
		else:
			try:
				with open(filepath, 'r', encoding='utf-8') as f:
					self.new_tab(error=True)
					self.tabs[self.tabindex].filepath = filepath
					self.tabs[self.tabindex].contents = f.read()
					self.tabs[self.tabindex].type = 'normal'
			except EnvironmentError as e:
				print(e.__str__())
				print('\n Could not open file %s' % filepath)
				self.bell()
				return

		
		self.entry.delete(0, tkinter.END)
		self.entry.insert(0, self.tabs[self.tabindex].filepath)
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.contents.edit_reset()
		self.contents.focus_set()
		
		line = errline + '.0'
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % line)
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % line)
		self.contents.mark_set('insert', line)
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.state = 'normal'
		

	def run(self):
		'''	Run file currently being edited. This can not catch errlines of
			those exceptions that are catched. Like:
			
			try:
				code we know sometimes failing with SomeError
				(but might also fail with other error-type)
			except SomeError:
				some other code but no raising error
				
			Note: 	Above code will raise an error in case
			 		code in try-block raises some other error than SomeError.
					In that case those errlines will be of course catched.
			
			What this means: If you self.run() with intention to spot possible 
			errors in your program, you should use logging (in except-block)
			if you are not 100% sure about your code in except-block.
		'''
		if (self.state != 'normal') or (self.tabs[self.tabindex].type == 'newtab'):
			self.bell()
			return
			
		self.save(forced=True)
		res = subprocess.run(['python', self.tabs[self.tabindex].filepath], text=True, capture_output=True)
		print(res.stdout)
		
		if res.returncode != 0:
			self.bind("<Escape>", self.stop_show_errors)
			self.bind("<Button-3>", self.do_nothing)
			self.state = 'error'
			
			self.taglinks = dict()
			self.errlines = list()
			
			self.contents.delete('1.0', tkinter.END)
			
			for tag in self.contents.tag_names():
				if 'hyper' in tag:
					self.contents.tag_delete(tag)
				
			self.err = res.stderr.splitlines()
			
			for line in self.err:
				print(line)
				tmp = line

				tagname = "hyper-%s" % len(self.errlines)
				self.contents.tag_config(tagname)
				
				# Why ButtonRelease instead of just Button-1:
				# https://stackoverflow.com/questions/24113946/unable-to-move-text-insert-index-with-mark-set-widget-function-python-tkint
				
				self.contents.tag_bind(tagname, "<ButtonRelease-1>", 
					lambda event, arg=tagname: self.lclick(arg, event))
				
				self.contents.tag_bind(tagname, "<Enter>", 
					lambda event, arg=tagname: self.enter(arg, event))
				
				self.contents.tag_bind(tagname, "<Leave>", 
					lambda event, arg=tagname: self.leave(arg, event))
				
				self.taglinks[tagname] = self.tag_link
				
				# parse filepath and linenums from errors
				if 'File ' in line and 'line ' in line:
					data = line.split(',')[:2]
					linenum = data[1][6:]
					filepath = data[0][8:-1]
					self.errlines.append((filepath, linenum)) 
					self.contents.insert(tkinter.INSERT, tmp +"\n", tagname)
				else:
					self.contents.insert(tkinter.INSERT, tmp +"\n")
				

	def show_errors(self):
		''' Show traceback from last run with added hyperlinks.
		'''
		
		if len(self.errlines) != 0:
			self.bind("<Escape>", self.stop_show_errors)
			self.bind("<Button-3>", self.do_nothing)
			self.state = 'error'
			
			tmp = self.contents.get('1.0', tkinter.END)
			self.tabs[self.tabindex].contents = tmp
			
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
				
			self.tabs[self.tabindex].position = pos
			
			self.contents.delete('1.0', tkinter.END)
			
			i = 0
			for line in self.err:
				tmp = line
				
				# parse filepath and linenums from errors
				if 'File ' in line and 'line ' in line:
					data = line.split(',')[:2]
					linenum = data[1][6:]
					filepath = data[0][8:-1]
					self.errlines.append((filepath, linenum)) 
					self.contents.insert(tkinter.INSERT, tmp +"\n", 'hyper-%d' % i)
					i += 1
				else:
					self.contents.insert(tkinter.INSERT, tmp +"\n")

									
	def stop_show_errors(self, event=None):
		self.state = 'normal'
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		self.entry.delete(0, tkinter.END)
		
		if self.tabs[self.tabindex].type == 'normal':
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
			
		self.contents.edit_reset()
		self.contents.focus_set()

		# ensure we see something before and after
		pos = self.tabs[self.tabindex].position
		self.contents.see('%s - 2 lines' % pos)
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % pos)
		self.contents.mark_set('insert', pos)
		
########## Run file Related End
########## Overrides Begin

	def raise_popup(self, event=None):
		self.popup_whohasfocus = event.widget
		self.popup.post(event.x_root, event.y_root)
		self.popup.focus_set() # Needed to remove popup when clicked outside.
		
		
	def popup_focusOut(self, event=None):
		self.popup.unpost() 
	

	def copy(self):
		self.popup_whohasfocus.event_generate('<<Copy>>')


	def paste(self):
		self.popup_whohasfocus.event_generate('<<Paste>>')


	def undo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			self.contents.edit_undo()
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def redo_override(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			self.contents.edit_redo()
		except tkinter.TclError:
			self.bell()
			
		return 'break'
		
		
	def select_all(self, event):
		self.contents.tag_remove('sel', '1.0', tkinter.END)
		self.contents.tag_add('sel', 1.0, tkinter.END)
		return "break"


	def return_override(self, event):
		# Cursor indexes when pressed return:
		line, row = map(int, self.contents.index(tkinter.INSERT).split('.'))			
		# is same as:
		# line = int(self.contents.index(tkinter.INSERT).split('.')[0])
		# row = int(self.contents.index(tkinter.INSERT).split('.')[1])
		
		# First an easy case:
		if row == 0:
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
				
		tmp = self.contents.get('%s.0' % str(line),'%s.0 lineend' % str(line))
		
		# Then one special case: check if cursor is inside indentation,
		# and line is not empty.
		
		if tmp[:row].isspace() and not tmp[row:].isspace():
			self.contents.insert(tkinter.INSERT, '\n')
			self.contents.insert('%s.0' % str(line+1), tmp[:row])
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"
			
		else:		
			for i in range(len(tmp)):
				if tmp[i] != '\t':
					break
	
			self.contents.insert(tkinter.INSERT, '\n') # Manual newline because return is overrided.
			self.contents.insert(tkinter.INSERT, i*'\t')
			self.contents.see(f'{line+1}.0')
			self.contents.edit_separator()
			return "break"

########## Overrides End
########## Save and Load Begin

	def tabify(self, line):
		
		indent_stop_index = 0
		
		for char in line:
			if char in [' ', '\t']: indent_stop_index += 1
			else: break
			
		if indent_stop_index == 0: return line
		
		indent_string = line[:indent_stop_index]
		line = line[indent_stop_index:]
		
		count = 0
		for char in indent_string:
			if char == '\t': 
				count = 0
				continue
			if char == ' ': count += 1
			if count == 4:
				indent_string = indent_string.replace(4*' ', '\t', True)
				count = 0
		
		tabified_line = ''.join([indent_string, line])
		return tabified_line
	
	
	def load(self, event=None):

		if self.state != 'normal':
			self.bell()
			return
		
		# event is button
		if event == None:
			d = tkinter.filedialog.FileDialog(self)
			
			d.dirs.configure(font=self.font)
			d.files.configure(font=self.font)
			d.cancel_button.configure(font=self.menufont)
			d.filter.configure(font=self.menufont)
			d.filter_button.configure(font=self.menufont)
			d.ok_button.configure(font=self.menufont)
			d.selection.configure(font=self.menufont)

			d.dirsbar.configure(width=self.scrollbar_width)
			d.filesbar.configure(width=self.scrollbar_width)
			d.filesbar.configure(elementborderwidth=self.elementborderwidth)
			d.dirsbar.configure(elementborderwidth=self.elementborderwidth)
			
			tmp = d.go('.', pattern='*.py')
			
			# avoid bell when dialog is closed without selection
			if tmp == None:
				return
			
		# event should then be Return
		else:
			tmp = self.entry.get().strip()

		if not isinstance(tmp, str) or tmp.isspace() or '.py' not in tmp:
			self.bell()
			return
		
		# If trying to open from curdir without full path
		if '/' not in tmp:
			tmp = os.path.abspath('.') + '/' + tmp
			
		filename = tmp
		openfiles = [tab.filepath for tab in self.tabs]
		
		if filename in openfiles:
			print('file %s is already open' % filename)
			self.bell()
			return
		
		if self.tabs[self.tabindex].type == 'normal':
			# keyword argument deltab should be renamed
			self.save(deltab=True)
		
		# Using same tab:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				self.contents.delete('1.0', tkinter.END)
				self.entry.delete(0, tkinter.END)
				self.tabs[self.tabindex].filepath = filename
				self.tabs[self.tabindex].contents = f.read()
				self.tabs[self.tabindex].type = 'normal'
				self.tabs[self.tabindex].position = '1.0'
				
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
				self.contents.focus_set()
				self.contents.see('1.0')
				self.contents.mark_set('insert', '1.0')			
				self.entry.insert(0, filename)
				self.contents.edit_reset()
		except EnvironmentError as e:
			print(e.__str__())
			print('\n Could not open file %s' % filename)
			

	def save(self, deltab=False, forced=False):
		''' forced when run( or quit_me(
		'''
		
		if forced:
			# update active tab first
			try:
				pos = self.contents.index(tkinter.INSERT)
			except tkinter.TclError:
				pos = '1.0'
				
			tmp = self.contents.get('1.0', tkinter.END).splitlines(True)
	
			# Check indent (tabify):
			tmp[:] = [self.tabify(line) for line in tmp]
			tmp = ''.join(tmp)[:-1]
			
			self.tabs[self.tabindex].position = pos
			self.tabs[self.tabindex].contents = tmp
			
			# then save tabs to disk
			for tab in self.tabs:
				if tab.type == 'normal':
					try:
						with open(tab.filepath, 'w', encoding='utf-8') as f:
							f.write(tab.contents)
					except EnvironmentError as e:
						print(e.__str__())
						print('\n Could not save file %s' % tab.filepath)
				else:
					tab.position = '1.0'
					
			return

		# if not forced:

		fpath_in_entry = self.entry.get().strip()
		
		if '/' not in fpath_in_entry:
				fpath_in_entry = os.path.abspath('.') + '/' + fpath_in_entry
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
					
		tmp = self.contents.get('1.0', tkinter.END).splitlines(True)
		
		# Check indent (tabify):
		tmp[:] = [self.tabify(line) for line in tmp]
		tmp = ''.join(tmp)[:-1]

		self.tabs[self.tabindex].position = pos
		self.tabs[self.tabindex].contents = tmp

		openfiles = [tab.filepath for tab in self.tabs]
		
		if not isinstance(fpath_in_entry, str) or fpath_in_entry.isspace() or '.py' not in fpath_in_entry:
			print('Give a valid filename')
			self.bell()
			return
		
		# creating new file
		if fpath_in_entry != self.tabs[self.tabindex].filepath:
		
			if fpath_in_entry in openfiles:
				self.bell()
				print('\nFile %s already opened' % fpath_in_entry)
				return
			
			if self.tabs[self.tabindex].type == 'newtab':
			
				# avoiding disk-writes, just checking filepath:
				try:
					with open(fpath_in_entry, 'w', encoding='utf-8') as f:
						self.tabs[self.tabindex].filepath = fpath_in_entry
						self.tabs[self.tabindex].type = 'normal'
				except EnvironmentError as e: 
					print(e.__str__())
					print('\n Could not save file %s' % fpath_in_entry)
					return

			# want to create new file with same contents:
			else:
				self.new_tab()
				self.tabs[self.tabindex].filepath = fpath_in_entry
				self.tabs[self.tabindex].contents = tmp
				self.tabs[self.tabindex].position = pos
				self.tabs[self.tabindex].type = 'normal'
				
				self.entry.delete(0, tkinter.END)
				self.entry.insert(0, self.tabs[self.tabindex].filepath)
				self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
				self.contents.edit_reset()
				
				try:
					line = self.tabs[self.tabindex].position
					self.contents.focus_set()
					# ensure we see something before and after
					self.contents.see('%s - 2 lines' % line)
					self.update_idletasks()
					self.contents.see('%s + 2 lines' % line)
					self.contents.mark_set('insert', line)
				except tkinter.TclError:
					self.tabs[self.tabindex].position = '1.0'
				
		else:
			# skip unnecessary disk-writing silently
			if not deltab:
				return

			# if closing tab or loading file:
			try:
				with open(self.tabs[self.tabindex].filepath, 'w', encoding='utf-8') as f:
					f.write(tmp)
			except EnvironmentError as e:
				print(e.__str__())
				print('\n Could not save file %s' % self.tabs[self.tabindex].filepath)
				return
	
########## Save and Load End
########## Gotoline and Help Begin

	def do_gotoline(self, event=None):
		try:
			line = self.entry.get().strip() + '.0'
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
			self.stop_gotoline()
		except tkinter.TclError as e:
			print(e)
	
	
	def stop_gotoline(self, event=None):
		self.entry.bind("<Return>", self.load)
		self.bind("<Escape>", lambda e: self.iconify())
		self.entry.delete(0, tkinter.END)
		self.entry.insert(0, self.tabs[self.tabindex].filepath)
		self.title(self.titletext)
		
	
	def gotoline(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		counter = 0
		for line in self.contents.get('1.0', tkinter.END).splitlines():
			counter += 1
		self.entry.bind("<Return>", self.do_gotoline)
		self.bind("<Escape>", self.stop_gotoline)
		self.title('Go to line, 1-%s:' % str(counter))
		self.entry.delete(0, tkinter.END)
		self.entry.focus_set()
		return "break"
	
	
	def stop_help(self, event=None):
		self.state = 'normal'
		
		self.entry.config(state='normal')
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.tabs[self.tabindex].contents)
		
		if self.tabs[self.tabindex].filepath:
			self.entry.insert(0, self.tabs[self.tabindex].filepath)
		try:
			line = self.tabs[self.tabindex].position
			self.contents.focus_set()
			# ensure we see something before and after
			self.contents.see('%s - 2 lines' % line)
			self.update_idletasks()
			self.contents.see('%s + 2 lines' % line)
			self.contents.mark_set('insert', line)
		except tkinter.TclError:
			self.tabs[self.tabindex].position = '1.0'
		
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		
		
	def help(self, event=None):
		self.state = 'help'
		
		try:
			pos = self.contents.index(tkinter.INSERT)
		except tkinter.TclError:
			pos = '1.0'
		self.tabs[self.tabindex].position = pos
		self.tabs[self.tabindex].contents = self.contents.get('1.0', tkinter.END)
		
		self.entry.delete(0, tkinter.END)
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.helptxt)
		
		self.entry.config(state='disabled')
		self.contents.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		
		self.bind("<Button-3>", self.do_nothing)
		self.bind("<Escape>", self.stop_help)
			
########## Gotoline and Help End
########## Indent and Comment Begin

	def indent(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '\t')
			self.contents.edit_separator()
		except tkinter.TclError as e:
			print(e)
		return "break"
		

	def unindent(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			# Check there is enough space in every line:
			flag_continue = True
			
			for linenum in range(startline, endline+1):
				tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)
				
				if len(tmp) != 0 and tmp[0] != '\t':
					flag_continue = False
					break
				
			if flag_continue:
				for linenum in range(startline, endline+1):
					tmp = self.contents.get('%s.0' % linenum, '%s.0 lineend' % linenum)
				
					if len(tmp) != 0:
						self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
						self.contents.delete(tkinter.INSERT, '%s+%dc' % (tkinter.INSERT, 1))
				self.contents.edit_separator()
		
		except tkinter.TclError as e:
			print(e)
		return "break"

	
	def comment(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				self.contents.insert(tkinter.INSERT, '##')
			
			self.contents.edit_separator()
		
		except tkinter.TclError as e:
			print(e)
		return "break"


	def uncomment(self, event=None):
		'''should work even if there are uncommented lines between commented lines'''
		if self.state != 'normal':
			self.bell()
			return "break"
			
		try:
			startline = int(self.contents.index(tkinter.SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(tkinter.SEL_LAST).split(sep='.')[0])
			changed = False
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(tkinter.INSERT, '%s.0' % linenum)
				tmp = self.contents.get('%s.0' % linenum,'%s.0 lineend' % linenum)
				
				if tmp.lstrip()[:2] == '##':
					tmp = tmp.replace('##', '', 1)
					self.contents.delete('%s.0' % linenum,'%s.0 lineend' % linenum)
					self.contents.insert(tkinter.INSERT, tmp)
					changed = True
					
			if changed: self.contents.edit_separator()
			
		except tkinter.TclError as e:
			print(e)
		return "break"
		
########## Indent and Comment End
################ Search Begin

	def show_next(self, event=None):
		self.contents.config(state='normal')
		
		# check if at last match or beyond:
		i = len(self.contents.tag_ranges('match')) - 2
		last = self.contents.tag_ranges('match')[i]
	
		if self.contents.compare(self.search_idx[0], '>=', last):
			self.search_idx = ('1.0', '1.0')
			self.search_pos = 0
				
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.search_idx = self.contents.tag_nextrange('match', self.search_idx[1])
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % self.search_idx[0])
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % self.search_idx[0])

		self.search_pos += 1
		
		# compare found to match
		num_matches = int(len(self.contents.tag_ranges('match'))/2)
		ref = self.contents.tag_ranges('found')[0]
		
		for c in range(num_matches):
			tmp = self.contents.tag_ranges('match')[c*2]
			if self.contents.compare(ref, '==', tmp): break
		
		self.title('Search: %s/%s' % (str(c+1), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')


	def show_prev(self, event=None):
		self.contents.config(state='normal')
		first = self.contents.tag_ranges('match')[0]
	
		if self.contents.compare(self.search_idx[0], '<=', first):
			self.search_idx = (tkinter.END, tkinter.END)
			self.search_pos = self.search_matches + 1

			
		self.contents.tag_remove('found', '1.0', tkinter.END)
		
		self.search_idx = self.contents.tag_prevrange('match', self.search_idx[0])
		
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		
		# ensure we see something before and after
		self.contents.see('%s - 2 lines' % self.search_idx[0])
		self.update_idletasks()
		self.contents.see('%s + 2 lines' % self.search_idx[0])
		
		self.search_pos -= 1
		
		# compare found to match
		num_matches = int(len(self.contents.tag_ranges('match'))/2)
		ref = self.contents.tag_ranges('found')[0]
		
		for c in range(num_matches):
			tmp = self.contents.tag_ranges('match')[c*2]
			if self.contents.compare(ref, '==', tmp): break
			
		self.title('Search: %s/%s' % (str(c+1), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')
			
		
	def start_search(self, event=None):
		self.old_word = self.entry.get()
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
		if len(self.old_word) != 0:      
			self.title('Search:')
			pos = '1.0'
			wordlen = len(self.old_word)
			flag_start = True
			
			while True:
				pos = self.contents.search(self.old_word, pos, tkinter.END)
				if not pos: break
				self.search_matches += 1
				lastpos = "%s + %dc" % (pos, wordlen)
				self.contents.tag_add('match', pos, lastpos)
				if flag_start:
					flag_start = False
					self.contents.focus_set()
					self.show_next()
				pos = "%s + %dc" % (pos, wordlen+1)
				
		if self.search_matches > 0:
			self.contents.config(state='disabled')
			self.bind("<Button-3>", self.do_nothing)
			
			if self.state == 'normal':
				self.title('Found: %s matches' % str(self.search_matches))
				self.bind("<Alt-n>", self.show_next)
				self.bind("<Alt-p>", self.show_prev)
			else:
				self.bind("<Alt-n>", self.do_nothing)
				self.bind("<Alt-p>", self.do_nothing)

				self.title('Replace %s matches with:' % str(self.search_matches))
				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
		else:
			self.bell()
				
				
	def stop_search(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.bind("<Escape>", lambda e: self.iconify())
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.entry.bind("<Return>", self.load)
		self.entry.delete(0, tkinter.END)
		self.entry.insert(0, self.tabs[self.tabindex].filepath)
		self.new_word = ''
		self.old_word = ''
		self.search_matches = 0
		self.replace_overlap_index = None
		self.title(self.titletext)
		self.state = 'normal'
		self.contents.focus_set()


	def search(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.state = 'normal'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.title('Search:')
		self.entry.delete(0, tkinter.END)
		self.entry.focus_set()
		return "break"
			

################ Search End
################ Replace Begin

	def replace(self, event=None, state='replace'):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.state = state
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.title('Replace this:')
		self.entry.delete(0, tkinter.END)
		self.entry.focus_set()
		return "break"


	def replace_all(self, event=None):
		if self.state != 'normal':
			self.bell()
			return "break"
			
		self.replace(event, state='replace_all')
		
		
	def do_single_replace(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='disabled')
		self.search_matches = 0
		wordlen = len(self.old_word)
		wordlen2 = len(self.new_word)
		pos = '1.0'
		self.contents.tag_remove('match', '1.0', tkinter.END)
		
		# Next while-loop tags matches again, this is the main reason why
		# there is a problem if new_word contains old_word:it will be rematched.
		# This is why when there is a match, we move 
		# replace_overlap_index characters back and check if there already is
		# new_word. If so, it means there have already happened a replacement
		# and therefore search pos must be recalculated over this manifestation
		# of new_word. 
		 
		while True:
			pos = self.contents.search(self.old_word, pos, tkinter.END)
			if not pos: break
			 
			if self.replace_overlap_index != None:
				# find the startpos (pos2) and lastpos of new_word:
				tmp = int(pos.split('.')[1]) - self.replace_overlap_index
				pos2 = pos.split('.')[0] +'.'+ str(tmp)
				lastpos = "%s + %dc" % (pos2, wordlen2)
				
				if self.contents.get(pos2, lastpos) == self.new_word:
					# skip this match
					pos = "%s + %dc" % (pos2, wordlen2+1)
				else:
					lastpos = "%s + %dc" % (pos, wordlen)
					self.contents.tag_add('match', pos, lastpos)
					pos = "%s + %dc" % (pos, wordlen+1)
					self.search_matches += 1
			else:
				lastpos = "%s + %dc" % (pos, wordlen)
				self.contents.tag_add('match', pos, lastpos)
				pos = "%s + %dc" % (pos, wordlen+1)
				self.search_matches += 1

		self.contents.tag_remove('found', self.search_idx[0], self.search_idx[1])
		self.contents.tag_remove('match', self.search_idx[0], self.search_idx[1])
		self.contents.delete(self.search_idx[0], self.search_idx[1])
		self.contents.insert(self.search_idx[0], self.new_word)
		self.contents.config(state='disabled')
		
		self.search_matches -= 1
		
		if self.search_matches == 0:
			self.stop_search()

	
	def do_replace_all(self, event=None):
		count = self.search_matches
		
		for i in range(count):
			self.do_single_replace()
			if i < (count - 1): self.show_next()
				
		
	def start_replace(self, event=None):
		self.new_word = self.entry.get()
		
		if self.old_word == self.new_word:
			return
		else:
		
			self.replace_overlap_index = None
			self.bind("<Alt-n>", self.show_next)
			self.bind("<Alt-p>", self.show_prev)
			
			# Check if new_word contains old_word, if so:
			# record its overlap-index, which we need in do_single_replace()
			# (explanation for why this is needed is given there)
			if self.old_word in self.new_word:
				self.replace_overlap_index = self.new_word.index(self.old_word)
				
			if self.state == 'replace':
				self.entry.bind("<Return>", self.do_single_replace)
				self.title('Replacing %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )
			elif self.state == 'replace_all':
				self.entry.bind("<Return>", self.do_replace_all)
				self.title('Replacing ALL %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )


################ Replace End
