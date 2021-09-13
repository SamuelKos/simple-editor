from tkinter import (
TclError, Menu, Toplevel, Image, font, Tk, Button, Entry,
BOTTOM, BOTH, LEFT, X, END, INSERT, SEL_FIRST, SEL_LAST
)
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import FileDialog
from tkinter.font import Font
from os.path import abspath

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
# If you are about to use tkinter Python-module in a program with complexity
# similar or larger than in this editor, consider using some other GUI-library
# like Qt or completely other language like Tcl to name one. 
###############################################################################
#
#TODO:

# Below is short example from one book about how to use option database. I
# am not using option database in this editor.

##	A typical option database text file may look like the following:

##	*font: Arial 10
##	*Label*font: Times 12 bold
##	*background: AntiqueWhite1
##	*Text*background: #454545
##	*Button*foreground:gray55
##	*Button*relief: raised
##	*Button*width: 3

##	The asterisk ( * ) symbol here means that the particular style applies to all instances of
##	the given widget.
##	These entries are placed in an external text (.txt) file. To apply this styling to a
##	particular piece of code, you simply call it using the option_readfile() call early in
##	your code, as shown here:
##	root.option_readfile('optionDB.txt')
##


class Editor(Toplevel):

	def __init__(self, root, file=None, hdpi=True):
		super().__init__(root, class_='Simple Editor')
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		self.titletext = 'Simple Editor'
		self.title(self.titletext)
		self.filename = None
		self.hdpi_screen = hdpi

		if self.hdpi_screen == False:
			self.font = Font(family='Noto Mono', size=12)
			self.menufont = Font(family='Noto Mono', size=10)
		else:
			self.font = Font(family='Noto Mono', size=24)
			self.menufont = Font(family='Noto Mono', size=20)
		
		self.tab_width = self.font.measure(4*' ')
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
		self.old_word = ''
		self.new_word = ''
		self.errlines = None
		self.err_count = 0
		self.err_index = 0
		self.state = 'normal'
##		self.pic = Image("photo", file="./icons/text-editor.png")
##		self.tk.call('wm','iconphoto', self._w, self.pic)
		self.bind("<Escape>", lambda e: self.iconify())
		self.HELPTXT = '''Keyboard shortcuts:
		
		Ctrl-f search
		Ctrl-r replace
		Ctrl-R replace_all
		Ctrl-g gotoline
		
		Ctrl-C comment
		Ctrl-U uncomment
		Ctrl-> indent
		Ctrl-< unindent
		
		Ctrl-a select_all
		Ctrl-c copy
		Ctrl-v paste
		Ctrl-z undo
		Ctrl-Z redo


		While searching:
		Alt-n show_next
		Alt-p show_prev
		
		'''
		
		#Layout Begin:
		#####################################################
		self.data = [1,2] # part of next lambda-example, not used.
		self.bind("<Button-3>", lambda event, arg=self.data: self.raise_popup(event, arg))
		self.bind("<Control-f>", lambda event: self.search(event))
		self.bind("<Control-r>", lambda event: self.replace(event))
		self.bind("<Control-R>", lambda event: self.replace_all(event))
		self.bind("<Control-g>", lambda event: self.gotoline(event))
		
		self.contents = ScrolledText(self, background='#000000', foreground='#D3D7CF', insertbackground='#D3D7CF', font=self.font, blockcursor=True, tabs=(self.tab_width, ), tabstyle='wordprocessor', undo=True, maxundo=10, autoseparators=True)
		
		self.contents.tag_config('match', background='lightyellow', foreground='black')
		self.contents.tag_config('found', background='lightgreen')
		
		if hdpi == True: 
			self.contents.vbar.config(width=30)
		else:
			self.contents.vbar.config(width=20)
			
		self.contents.bind("<Return>", self.return_override)
		self.contents.bind("<Control-C>", self.comment)
		self.contents.bind("<Control-U>", self.uncomment)
		self.contents.bind("<Control-greater>", self.indent)
		self.contents.bind("<Control-less>", self.unindent)
		self.contents.bind("<Control-a>", self.select_all)
		self.contents.pack(side=BOTTOM, expand=True, fill=BOTH)
		
		self.popup_whohasfocus = None
		self.popup = Menu(self, font=self.menufont, tearoff=0, bd=0, activeborderwidth=0)
		self.popup.bind("<FocusOut>", self.popup_focusOut) # to remove popup when clicked outside
		self.popup.add_command(label="        copy", command=self.copy)
		self.popup.add_command(label="       paste", command=self.paste)
		self.popup.add_command(label=">>    indent", command=self.indent)
		self.popup.add_command(label="##   comment", command=self.comment)
		self.popup.add_command(label="   uncomment", command=self.uncomment)
		self.popup.add_command(label="<<  unindent", command=self.unindent)
		self.popup.add_command(label="         run", command=self.run)
		self.popup.add_command(label="    nxterror", command=self.next_error)
		self.popup.add_command(label="        undo", command=self.undo_override)
		self.popup.add_command(label="        redo", command=self.redo_override)
		self.popup.add_command(label="        help", command=self.help)
		
		self.entry = Entry(self, font=self.menufont)
		self.entry_return_bind_id = self.entry.bind("<Return>", self.load)
		self.entry.pack(side=LEFT, expand=True, fill=X)
		self.btn_open=Button(self, font=self.menufont, text='Open', command=self.load)
		self.btn_open.pack(side=LEFT)
		self.btn_save=Button(self, font=self.menufont, text='Save', command=self.save)
		self.btn_save.pack(side=LEFT)
		self.local = file

		if self.local:
			# Check if trying to open from curdir without full path
			if '/' not in self.local:
				self.local = abspath('.') + '/' + self.local
				
			try:
				with open(self.local) as file:
					self.contents.insert(INSERT, file.read())
					self.filename = self.local
					self.entry.insert(0, self.filename)
					self.flag_init = False
			except Exception as e:
				print(e)
				self.entry.delete(0, END)
				self.filename = None
		
		if self.filename == None:
			self.flag_init = True


	def do_nothing(self, event=None):
		pass
		
		
	def run(self):
		''' Run file currently being edited. This can not catch errlines of
			those exceptions that are catched but not raised. Like if there is
			this:
			
			try:
				code that fails with SomeError
			except SomeError:
				some other code but no raising error
		'''
		
		res =  subprocess.run(['python', self.filename], text=True, capture_output=True)
		print(res.stdout)
		
		self.err_count = 0
		self.err_index = 0
		
		if res.returncode != 0:
			self.errlines = list()
			err = res.stderr.splitlines()
			
			for line in err:
				print(line)
				
				if self.filename in line:
					# parse linenums from errors
					line = line[:line.rfind(',')]
					line = line[line.rfind('line '):]
					line = line[5:]
					self.errlines.append(line)
			
			self.err_count = len(self.errlines)
				

	def next_error(self):
		''' Show next error from last import.
		'''
		
		if self.errlines:
			self.contents.focus_set()
			line = str(self.errlines[self.err_index]) + '.0'
			self.contents.see(line)
			self.contents.mark_set('insert', line)
			self.err_index += 1
		
		if self.err_index == self.err_count:
			self.err_index = 0
	
	
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
	

	def copy(self, event=None):
		self.popup_whohasfocus.event_generate('<<Copy>>')


	def paste(self, event=None):
		self.popup_whohasfocus.event_generate('<<Paste>>')


	def load(self, event=None, no_such_file=False, search=False):
		tmp = self.entry.get()
		save = self.filename
		asked = False
		
		# Check if user entered manually filepath (in entry)
		# before pressing Open:
		if self.flag_init and tmp != '' and tmp != None:
			
			# If trying to open from curdir without full path
			if '/' not in tmp:
				tmp = abspath('.') + '/' + tmp
				
			self.filename = tmp
			
			try:
				with open(self.filename) as file:
					self.contents.delete('1.0', END)
					self.entry.delete(0, END)
					self.contents.insert(INSERT, file.read())
					self.entry.insert(0, self.filename)
					self.flag_init = False
			except Exception as e:
				print(e)
				self.filename = None
			################################### End of Check
		else:

			if self.filename in (tmp, None) or no_such_file:
				d = FileDialog(self)
				
				d.dirs.configure(font=self.font)
				d.files.configure(font=self.font)
				d.cancel_button.configure(font=self.menufont)
				d.filter.configure(font=self.menufont)
				d.filter_button.configure(font=self.menufont)
				d.ok_button.configure(font=self.menufont)
				d.selection.configure(font=self.menufont)
				
				if self.hdpi_screen == True:
					d.dirsbar.configure(width=20)
					d.filesbar.configure(width=20)
					
				self.filename = d.go('.')
				
				asked = True
				if self.filename == None:  #pressed close or cancel in filedialog
					self.filename = save
			else:
				# If trying to open from curdir without full path
				if '/' not in tmp:
					tmp = abspath('.') + '/' + tmp
					
				self.filename = tmp
	
			try:
				with open(self.filename, encoding='utf-8') as file:
					self.contents.delete('1.0', END)
					for line in file.readlines():
						self.contents.insert(INSERT, line)
					self.entry.delete(0, END)
					self.entry.insert(0, self.filename)
					self.contents.edit_reset()
					self.flag_init = False
			except Exception:
				self.filename = save #file tmp does not exist, reverting back to old file and open filedialog
				if not no_such_file and not asked:
					self.load(no_such_file=True)
		
	
	def save(self):
		tmp = self.contents.get('1.0', END).splitlines(True)
		# Check indent:
		tmp[:] = [self.tabify(line) for line in tmp]
			
		try:
			tmp = ''.join(tmp)[:-1]
			# explanation of: [:-1]
			# otherwise there will be extra newline at the end of file
			# so we remove the last symbol which is newline
			
			with open(self.entry.get(), 'w', encoding='utf-8') as file:
				file.write(tmp)
		except Exception as e:
			print(e)


	def raise_popup(self, event, *args):
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
		except TclError as e:
			print(e)
	
	
	def stop_gotoline(self, event=None):
		self.entry.bind("<Return>", self.load)
		self.bind("<Escape>", lambda e: self.iconify())
		self.entry.delete(0,END)
		self.entry.insert(0,self.filename)
		self.title(self.titletext)
		
	
	def gotoline(self, event=None):
		counter = 0
		for line in self.contents.get('1.0', END).splitlines():
			counter += 1
		self.entry.bind("<Return>", self.do_gotoline)
		self.bind("<Escape>", self.stop_gotoline)
		self.title('Go to line, 1-%s:' % str(counter))
		self.entry.delete(0, END)
		self.entry.focus_set()
		return "break"
	
	
	def stop_help(self, event=None):
		self.filename = False
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.load()
		self.bind("<Escape>", lambda e: self.iconify())
		self.bind("<Button-3>", lambda event, arg=self.data: self.raise_popup(event, arg))
		self.contents.focus_set()
	
	
	def help(self, event=None):
		self.save()
		self.contents.delete('1.0', END)
		self.contents.insert(INSERT, self.HELPTXT)
		self.contents.config(state='disabled')
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.bind("<Button-3>", self.do_nothing)
		self.bind("<Escape>", self.stop_help)
		
		
	def undo_override(self, event=None):
		try:
			self.contents.edit_undo()
		except TclError as e:
			print(e)
		
		
	def redo_override(self, event=None):
		try:
			self.contents.edit_redo()
		except TclError as e:
			print(e)
	
	
	def indent(self, event=None):
		try:
			startline = int(self.contents.index(SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(SEL_LAST).split(sep='.')[0])
			for linenum in range(startline, endline+1):
				self.contents.mark_set(INSERT, '%s.0' % linenum)
				self.contents.insert(INSERT, '\t')
			self.contents.edit_separator()
		except TclError as e:
			print(e)
		return "break"
		

	def unindent(self, event=None):
		try:
			startline = int(self.contents.index(SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(SEL_LAST).split(sep='.')[0])
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
						self.contents.mark_set(INSERT, '%s.0' % linenum)
						self.contents.delete(INSERT, '%s+%dc' % (INSERT, 1))
				self.contents.edit_separator()
		
		except TclError as e:
			print(e)
		return "break"

	
	def comment(self, event=None):
		try:
			startline = int(self.contents.index(SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(SEL_LAST).split(sep='.')[0])
			for linenum in range(startline, endline+1):
				self.contents.mark_set(INSERT, '%s.0' % linenum)
				self.contents.insert(INSERT, '##')
			self.contents.edit_separator()
		except TclError as e:
			print(e)
		return "break"


	def uncomment(self, event=None):
		'''should work even if there are uncommented lines between commented lines'''
		try:
			startline = int(self.contents.index(SEL_FIRST).split(sep='.')[0])
			endline = int(self.contents.index(SEL_LAST).split(sep='.')[0])
			changed = False
			
			for linenum in range(startline, endline+1):
				self.contents.mark_set(INSERT, '%s.0' % linenum)
				tmp = self.contents.get('%s.0' % linenum,'%s.0 lineend' % linenum)
				
				if tmp.lstrip()[:2] == '##':
					tmp = tmp.replace('##', '', 1)
					self.contents.delete('%s.0' % linenum,'%s.0 lineend' % linenum)
					self.contents.insert(INSERT, tmp)
					changed = True
					
			if changed: self.contents.edit_separator()
			
		except TclError as e:
			print(e)
		return "break"
		

	def select_all(self, event):
		self.contents.tag_remove('sel', '1.0', END)
		self.contents.tag_add('sel', 1.0, END)
		return "break"


	def return_override(self, event):
		line = int(self.contents.index(INSERT).split('.')[0])
		#row = int(self.contents.index(INSERT).split('.')[1])
		
		tmp = self.contents.get('%s.0' % line,'%s.0 lineend' % line) + 'a'
		
		# explanation of +'a':
		# We want to know where the first character of the next line (below)
		# should be (we do this because we want 'auto'-indentation).
		# Character should be indented similarly as previous line.
		# So if previous line is not empty, it does not matter that we added
		# 'a' because loop breaks before that. And if the line was empty before
		# adding 'a', well now we avoid index error and get indentation right.
		
		for i in range(len(tmp)):
			if tmp[i] != '\t':
				break

		self.contents.insert(INSERT, '\n') # Manual newline because return is overrided.
		self.contents.insert(INSERT, i*'\t')
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
				
		self.contents.tag_remove('found', '1.0', END)
		self.search_idx = self.contents.tag_nextrange('match', self.search_idx[1])
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		self.contents.see(self.search_idx[0])
		self.search_pos += 1
		self.title('Search: %s/%s' % (str(self.search_pos), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')


	def show_prev(self, event=None):
		self.contents.config(state='normal')
		first = self.contents.tag_ranges('match')[0]
	
		if self.contents.compare(self.search_idx[0], '<=', first):
			self.search_idx = (END, END)
			self.search_pos = self.search_matches + 1

			
		self.contents.tag_remove('found', '1.0', END)
		
		self.search_idx = self.contents.tag_prevrange('match', self.search_idx[0])
		
		# change color
		self.contents.tag_add('found', self.search_idx[0], self.search_idx[1])
		self.contents.see(self.search_idx[0])
		self.search_pos -= 1
		self.title('Search: %s/%s' % (str(self.search_pos), str(self.search_matches)))
		
		if self.search_matches == 1:
			self.bind("<Alt-n>", self.do_nothing)
			self.bind("<Alt-p>", self.do_nothing)
		
		self.contents.config(state='disabled')
			
		
	def start_search(self, event=None):
		self.old_word = self.entry.get()
		self.contents.tag_remove('match', '1.0', END)
		self.contents.tag_remove('found', '1.0', END)
		self.search_idx = ('1.0', '1.0')
		self.search_matches = 0
		self.search_pos = 0
		if len(self.old_word) != 0:      
			self.title('Search:')
			pos = '1.0'
			wordlen = len(self.old_word)
			flag_start = True
			
			while True:
				pos = self.contents.search(self.old_word, pos, END)
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
				self.bind("<Alt-n>", lambda event: self.show_next(event))
				self.bind("<Alt-p>", lambda event: self.show_prev(event))
			else:
				self.bind("<Alt-n>", self.do_nothing)
				self.bind("<Alt-p>", self.do_nothing)

				self.title('Replace %s matches with:' % str(self.search_matches))
				self.entry.bind("<Return>", self.start_replace)
				self.entry.focus_set()
				
				
	def stop_search(self, event=None):
		self.contents.config(state='normal')
		self.btn_open.config(state='normal')
		self.btn_save.config(state='normal')
		self.bind("<Button-3>", lambda event, arg=self.data: self.raise_popup(event, arg))
		self.contents.tag_remove('match', '1.0', END)
		self.contents.tag_remove('found', '1.0', END)
		self.entry.bind("<Return>", self.load)
		self.bind("<Escape>", lambda e: self.iconify())
		self.entry.delete(0,END)
		self.entry.insert(0,self.filename)
		self.new_word = ''
		self.old_word = ''
		self.search_matches = 0
		self.title(self.titletext)
		self.state == 'normal'
		self.contents.focus_set()


	def search(self, event=None):
		self.state = 'normal'
		self.btn_open.config(state='disabled')
		self.btn_save.config(state='disabled')
		self.entry.bind("<Return>", self.start_search)
		self.bind("<Escape>", self.stop_search)
		self.title('Search:')
		self.entry.delete(0, END)
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
		self.entry.delete(0, END)
		self.entry.focus_set()
		return "break"


	def replace_all(self, event=None):
		self.replace(event, state='replace_all')
		
		
	def do_single_replace(self, event=None):
		self.contents.config(state='normal')
		self.search_matches = 0
		wordlen = len(self.old_word)
		pos = '1.0'
		self.contents.tag_remove('match', '1.0', END)
		
		while True:
			pos = self.contents.search(self.old_word, pos, END)
			if not pos: break
			self.search_matches += 1
			lastpos = "%s + %dc" % (pos, wordlen)
			self.contents.tag_add('match', pos, lastpos)
			pos = "%s + %dc" % (pos, wordlen+1)

		self.contents.tag_remove('found', self.search_idx[0], self.search_idx[1])
		self.contents.tag_remove('match', self.search_idx[0], self.search_idx[1])
		self.contents.delete(self.search_idx[0], self.search_idx[1])
		self.contents.insert(self.search_idx[0], self.new_word)
		self.contents.config(state='disabled')
		self.search_matches -= 1
		
		if self.search_matches == 0:
			self.stop_search()

	
	def do_replace_all(self, event=None):
		count = self.search_matches - 1
		
		for i in range(count):
			self.do_single_replace()
			self.show_next()
						
		self.do_single_replace()
				
		
	def start_replace(self, event=None):
		self.new_word = self.entry.get()
		self.bind("<Alt-n>", lambda event: self.show_next(event))
		self.bind("<Alt-p>", lambda event: self.show_prev(event))

		if self.state == 'replace':
			self.entry.bind("<Return>", self.do_single_replace)
			self.title('Replacing %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )
		elif self.state == 'replace_all':
			self.entry.bind("<Return>", self.do_replace_all)
			self.title('Replacing ALL %s matches of %s with: %s' % (str(self.search_matches), self.old_word, self.new_word) )


################ Replace End
	
	def quit_me(self, event=None):
		self.quit()
		self.destroy()


if __name__ == '__main__':
	root = Tk().withdraw()
	e = Editor(root)
	e.mainloop()

