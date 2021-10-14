#TODO: 'tabbed' editing with optionmenu
# from standard library
import tkinter.scrolledtext
import tkinter.filedialog
import tkinter.font
import tkinter
import random
import json
import os

# from current directory
import font_chooser

# for executing edited file in the same env than this editor, which is nice:
# It means you have your installed dependencies available. By self.run()
import subprocess

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
		Ctrl-U  Uncomment
		Ctrl->  Indent
		Ctrl-<  Unindent
		
		Ctrl-a  Select all
		Ctrl-c  Copy
		Ctrl-v  Paste
		Ctrl-z  Undo
		Ctrl-Z  Redo
		
		Ctrl-p  Font setting
		Ctrl-W	Save current settings
		
		Ctrl-plus 	Increase scrollbar-width
		Ctrl-minus	Decrease scrollbar-width

		While searching:
		Alt-n  Next match
		Alt-p  Prev match
		
		'''

			
class Editor(tkinter.Toplevel):

	def __init__(self, root):
		super().__init__(root, class_='Simple Editor')
		self.top = root
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		self.titletext = 'Simple Editor'
		self.title(self.titletext)
		
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
		self.bind("<Control-minus>", self.decrease_scrollbar_width)
		self.bind("<Control-plus>", self.increase_scrollbar_width)
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Control-R>", self.replace_all)
		self.bind("<Button-3>", self.raise_popup)
		self.bind("<Control-g>", self.gotoline)
		self.bind("<Control-r>", self.replace)
		self.bind("<Control-f>", self.search)
		self.bind("<Control-p>", self.font_choose)
		self.bind("<Control-W>", self.save_config)
		
		self.contents = tkinter.scrolledtext.ScrolledText(self, background='#000000', foreground='#D3D7CF', insertbackground='#D3D7CF', blockcursor=True, tabstyle='wordprocessor', undo=True, maxundo=-1, autoseparators=True)
		
		self.contents.tag_config('match', background='lightyellow', foreground='black')
		self.contents.tag_config('found', background='lightgreen')
		
		self.contents.bind("<Return>", self.return_override)
		self.contents.bind("<Control-C>", self.comment)
		self.contents.bind("<Control-U>", self.uncomment)
		self.contents.bind("<Control-greater>", self.indent)
		self.contents.bind("<Control-less>", self.unindent)
		self.contents.bind("<Control-a>", self.select_all)
		self.contents.bind("<Control-z>", self.undo_override)
		self.contents.bind("<Control-Z>", self.redo_override)
		
		self.contents.pack(side=tkinter.BOTTOM, expand=True, fill=tkinter.BOTH)
		
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
		self.entry_return_bind_id = self.entry.bind("<Return>", self.load)
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
		
		# Initialize configurables
		self.font = tkinter.font.Font(family=self.fontname, size=12)
		self.menufont = tkinter.font.Font(family=self.fontname, size=10)
		self.scrollbar_width = 30
		self.elementborderwidth = 4	
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)
		self.filename = None
		self.local = None
		
		# Try to apply saved configurations:
		try:
			f = open(CONFPATH)
		except FileNotFoundError: pass
		except OSError as e:
			print(e.__str__())
			os.remove(CONFPATH)
			print('\nConfiguration file removed')
		else:
			self.load_config(f)
			self.randfont = False
			f.close()

		if self.randfont == True:
			print(f'WARNING: RANDOM FONT NAMED "{self.fontname.upper()}" IN USE. Select a better font with: ctrl-p')
		
		# Apply fonts to widgets
		self.tab_width = self.font.measure(4*' ')
		self.contents.config(font=self.font, tabs=(self.tab_width, ))
		self.entry.config(font=self.menufont)
		self.btn_open.config(font=self.menufont)
		self.btn_save.config(font=self.menufont)
		self.popup.config(font=self.menufont)
		# Set Font End ##################################################
		
		if self.local:
			try:
				f = open(self.local)
			except OSError as e:
				print(e)
				self.entry.delete(0, tkinter.END)
				self.filename = None
			else:
				self.contents.insert(tkinter.INSERT, f.read())
				f.close()
				self.filename = self.local
				self.entry.insert(0, self.filename)
				self.flag_init = False
					
		if self.filename == None:
			self.flag_init = True
		############################# init End ######################
		

	def do_nothing(self, event=None):
		pass
		

	def save_config(self, event=None):
		try:
			f = open(CONFPATH, 'w', encoding='utf-8')
		except OSError as e:
			print(e.__str__())
			print('Could not save configuration')
		else:
			data = dict()	
			data['font'] = self.font.config()
			data['menufont'] = self.menufont.config()
			data['scrollbar_width'] = self.scrollbar_width
			data['elementborderwidth'] = self.elementborderwidth
			data['self.local'] = self.filename
	
			string_representation = json.dumps(data)
			f.write(string_representation)
			f.close()

			
	def load_config(self, fileobject):
		string_representation = fileobject.read()
		data = json.loads(string_representation)

		self.font.config(**data['font'])
		self.menufont.config(**data['menufont'])
		
		self.scrollbar_width 	= data['scrollbar_width']
		self.elementborderwidth	= data['elementborderwidth']
		self.contents.vbar.config(width=self.scrollbar_width)
		self.contents.vbar.config(elementborderwidth=self.elementborderwidth)
			
		self.local = data['self.local']

		
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
		
		
	def font_choose(self, event=None):		
		self.choose = font_chooser.Fontchooser(self.top, [self.font, self.menufont])				
		return 'break'
		

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
		
		try:
			f = open(filepath, encoding='utf-8')
		except OSError as e:
			print(e)
		else:
			self.contents.delete('1.0', tkinter.END)

			for line in f.readlines():
				self.contents.insert(tkinter.INSERT, line)

			f.close()
			
			self.filename = filepath
			self.entry.delete(0, tkinter.END)
			self.entry.insert(0, filepath)
			self.contents.edit_reset()
			self.contents.focus_set()
			line = errline + '.0'
			self.contents.see(line)
			self.contents.mark_set('insert', line)
			self.bind("<Escape>", lambda e: self.iconify())
			
			
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
		
		res =  subprocess.run(['python', self.filename], text=True, capture_output=True)
		print(res.stdout)
		
		if res.returncode != 0:
			self.bind("<Escape>", self.stop_show_errors)
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
		''' Show traceback with added hyperlinks from last run.
		'''
		
		self.bind("<Escape>", self.stop_show_errors)

		if len(self.errlines) != 0:
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
		self.bind("<Escape>", lambda e: self.iconify())
		
		try:
			f = open(self.filename, encoding='utf-8')
		except OSError as e:
			print(e)
		else:
			self.contents.delete('1.0', tkinter.END)

			for line in f.readlines():
				self.contents.insert(tkinter.INSERT, line)

			f.close()


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
	

	def copy(self):
		self.popup_whohasfocus.event_generate('<<Copy>>')


	def paste(self):
		self.popup_whohasfocus.event_generate('<<Paste>>')


	def load(self, event=None, no_such_file=False, search=False):
		tmp = self.entry.get()
		save = self.filename
		asked = False
		
		# Check if user entered manually filepath (in entry)
		# before pressing Open, get filepath and open it right away:
		
		if self.flag_init and tmp != '' and tmp != None:
			
			# If trying to open from curdir without full path
			if '/' not in tmp:
				tmp = os.path.abspath('.') + '/' + tmp
				
			self.filename = tmp
			
			try:
				f = open(self.filename)
				
			except OSError as e:
				print(e)
				self.filename = None
			else:
				self.contents.delete('1.0', tkinter.END)
				self.entry.delete(0, tkinter.END)
				self.contents.insert(tkinter.INSERT, f.read())
				f.close()
				self.entry.insert(0, self.filename)
				self.flag_init = False
		
			################################### End of Check
			
		else:
			# Normal cases: get filepath in different normal cases and then
			# try to open. If filename is tmp it means user wants to open
			# another file with pressing open, so we show filechooser menu.
			# no_such_file happens if user has tried to open with entry but
			# file does not exist. Filename can be None if flag_init is true
			# as it is if we have empty editor at startup and press open. It
			# stays None if dialog is closed without selection or error occurs.
			
			if self.filename in (tmp, None) or no_such_file:
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
				
				self.filename = d.go('.')
				
				asked = True
				if self.filename == None:  #pressed close or cancel in filedialog
					self.filename = save
			else:
				# There was no flag_init so something is open and user tries to 
				# be clever and open another file from entry
				# (for the first time because no_such_file=False)
				
				# If trying to open from curdir without full path
				if '/' not in tmp and '.py' in tmp:
					tmp = os.path.abspath('.') + '/' + tmp
				
				if tmp != '' and '.py' in tmp:
					self.filename = tmp
				
			# We now have filepath from one of above cases. Now try to open it.
			# Of course there is a possibility that user opens empty editor,
			# then presses open but does not choose a file.
			# So check that first.
			
			if self.filename != None:
				try:
					f = open(self.filename, encoding='utf-8')
					
				except OSError as e:
					print(e)
					#file tmp does not exist, reverting back to old file and open filedialog
					self.filename = save
	
					if not no_such_file and not asked:
						self.load(no_such_file=True)
				else:
					self.contents.delete('1.0', tkinter.END)
	
					for line in f.readlines():
						self.contents.insert(tkinter.INSERT, line)
	
					f.close()
					self.entry.delete(0, tkinter.END)
					self.entry.insert(0, self.filename)
					self.contents.edit_reset()
					self.flag_init = False
				
	
	def save(self):
		'''	No error catching because user wants to know if file was not
			saved. As error-message in console.
		'''
		tmp = self.contents.get('1.0', tkinter.END).splitlines(True)
				
		# Check indent (tabify):
		tmp[:] = [self.tabify(line) for line in tmp]

		tmp = ''.join(tmp)[:-1]
		# explanation of: [:-1]
		# otherwise there will be extra newline at the end of file
		# so we remove the last symbol which is newline
		fpath_in_entry = self.entry.get()
		f = open(fpath_in_entry, 'w', encoding='utf-8')		
		f.write(tmp)
		f.close()
		self.filename = fpath_in_entry
		self.flag_init = False


	def raise_popup(self, event=None):
		self.popup_whohasfocus = event.widget
		self.popup.post(event.x_root, event.y_root)
		self.popup.focus_set() # Needed to remove popup when clicked outside.
		
		
	def popup_focusOut(self, event=None):
		self.popup.unpost() 
	
	
	def do_gotoline(self, event=None):
		try:
			line = self.entry.get().strip() + '.0'
			self.contents.focus_set()
			self.contents.see(line)
			self.contents.mark_set('insert', line)
			self.stop_gotoline()
		except tkinter.TclError as e:
			print(e)
	
	
	def stop_gotoline(self, event=None):
		self.entry.bind("<Return>", self.load)
		self.bind("<Escape>", lambda e: self.iconify())
		self.entry.delete(0,tkinter.END)
		self.entry.insert(0,self.filename)
		self.title(self.titletext)
		
	
	def gotoline(self, event=None):
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
		if not self.flag_init: self.filename = False
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		if not self.flag_init: self.load()
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.contents.focus_set()
	
	
	def help(self, event=None):
		if not self.flag_init: self.save()
		self.contents.delete('1.0', tkinter.END)
		self.contents.insert(tkinter.INSERT, self.helptxt)
		self.contents.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.bind("<Button-3>", self.do_nothing)
		self.bind("<Escape>", self.stop_help)
		
		
	def undo_override(self, event=None):
		try:
			self.contents.edit_undo()
		except tkinter.TclError:
			self.contents.bell()
			
		return 'break'
		
		
	def redo_override(self, event=None):
		try:
			self.contents.edit_redo()
		except tkinter.TclError:
			self.contents.bell()
			
		return 'break'
	
	
	def indent(self, event=None):
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
		self.contents.see(self.search_idx[0])
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
		self.contents.see(self.search_idx[0])
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
				
				
	def stop_search(self, event=None):
		self.contents.config(state='normal')
		self.entry.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-3>", lambda event: self.raise_popup(event))
		self.contents.tag_remove('match', '1.0', tkinter.END)
		self.contents.tag_remove('found', '1.0', tkinter.END)
		self.entry.bind("<Return>", self.load)
		self.bind("<Escape>", lambda e: self.iconify())
		self.entry.delete(0,tkinter.END)
		self.entry.insert(0,self.filename)
		self.new_word = ''
		self.old_word = ''
		self.search_matches = 0
		self.replace_overlap_index = None
		self.title(self.titletext)
		self.state = 'normal'
		self.contents.focus_set()


	def search(self, event=None):
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
	
	def quit_me(self):
		self.save_config()
		self.quit()
		self.destroy()


if __name__ == '__main__':
	root = tkinter.Tk().withdraw()
	e = Editor(root)
	e.mainloop()


