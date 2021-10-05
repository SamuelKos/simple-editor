import tkinter


class Fontchooser(tkinter.Toplevel):
		
	def __init__(self, root, fontlist):
		''' root is tkinter.Tk instance
			fontlist is list of tkinter.font.Font instances
		'''
		super().__init__(root)
		self.fonts = fontlist
		self.protocol("WM_DELETE_WINDOW", self.quit_me)		
		self.fontnames = [f for f in tkinter.font.families()]
		
		# remove duplicates then sort
		s = set(self.fontnames)
		self.fontnames = [f for f in s]
		self.fontnames.sort()
		self.max = 42
		self.min = 8
		
		# Next, naming fonts to be configured in optionmenu:
		# self.fonts[0] ==> 'FONT 0' 	etc..
		# They are dummy-names used only to distinguish fonts in list
		# user gave as input.
		self.fontdict = dict()
		
		self.option_menu_list = list()
		for i,item in enumerate(self.fonts):
			pattern = f'FONT {i}'
			self.fontdict[pattern] = i
			# Here adding dummy-name to list which is used in optionmenu later:
			self.option_menu_list.append(pattern)
		
		self.var = tkinter.StringVar()
		self.var.set(self.option_menu_list[0])
		self.font = self.fonts[self.fontdict[self.var.get()]]
		
		self.optionmenu = tkinter.OptionMenu(self, self.var, *self.option_menu_list, command=self.optionmenu_command)
		
		# Set font of dropdown button:
		self.optionmenu.config(font=('TkDefaultFont',20))
		
		# Set font of dropdown items:
		menu = self.nametowidget(self.optionmenu.menuname)
		menu.config(font=('TkDefaultFont',20))
		
		# Optionmenu contains font-instances to be configured:
		self.optionmenu.pack(side=tkinter.LEFT)
		self.scrollbar = tkinter.Scrollbar(self)
		
		# Listbox contains font-choises to select from:
		self.lb = tkinter.Listbox(self, font=('TkDefaultFont', 20), selectmode=tkinter.SINGLE, width=80, yscrollcommand=self.scrollbar.set)
		self.lb.pack(pady=10, side='left')
		self.scrollbar.pack(side='left', fill='y')
		self.scrollbar.config(width=30, elementborderwidth=4, command=self.lb.yview)
		
		# With spinbox we set font size: 
		self.sb = tkinter.Spinbox(self, font=('TkDefaultFont', 28), from_=self.min, to=self.max, increment=2, width=3, command=self.change_font)
		self.sb.pack(pady=10)
		
		# Make four checkboxes for other font configurations
		self.bold = tkinter.StringVar()
		self.cb1 = tkinter.Checkbutton(self, font=('TkDefaultFont', 20), offvalue='normal', onvalue='bold', text='Bold', variable=self.bold)
		self.cb1.pack(pady=10, anchor='w')
		self.cb1.config(command=lambda args=[self.bold, 'weight']: self.checkbutton_command(args))
		
		self.italic = tkinter.StringVar()
		self.cb2 = tkinter.Checkbutton(self, font=('TkDefaultFont', 20), offvalue='roman', onvalue='italic', text='Italic', variable=self.italic)
		self.cb2.pack(pady=10, anchor='w')
		self.cb2.config(command=lambda args=[self.italic, 'slant']: self.checkbutton_command(args))
		
		self.underline = tkinter.StringVar()
		self.cb3 = tkinter.Checkbutton(self, font=('TkDefaultFont', 20), offvalue=0, onvalue=1, text='Underline', variable=self.underline)
		self.cb3.pack(pady=10, anchor='w')
		self.cb3.config(command=lambda args=[self.underline, 'underline']: self.checkbutton_command(args))
		
		self.overstrike = tkinter.StringVar()
		self.cb4 = tkinter.Checkbutton(self, font=('TkDefaultFont', 20), offvalue=0, onvalue=1, text='Overstrike', variable=self.overstrike)
		self.cb4.pack(pady=10, anchor='w')
		self.cb4.config(command=lambda args=[self.overstrike, 'overstrike']: self.checkbutton_command(args))
		
		# Get current fontsize and show it in spinbox
		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		self.sb.insert(0, fontsize)
		
		# Populate listbox
		for i,f in enumerate(self.fontnames):
			# get current fontnames index:
			if f == self.font.actual("family"): fontindex = i
			self.lb.insert('end', f)
		
		# Show current fontname in listbox
		self.lb.select_set(fontindex)
		self.lb.see(fontindex)
		
		# Check rest font configurations:
		self.cb1.deselect()
		self.cb2.deselect()
		self.cb3.deselect()
		self.cb4.deselect()
		
		if self.font['weight'] == 'bold': self.cb1.select()
		if self.font['slant'] == 'italic': self.cb2.select()	
		if self.font['underline'] == 1: self.cb3.select()
		if self.font['overstrike'] == 1: self.cb4.select()

		self.lb.bind('<ButtonRelease-1>', self.change_font)
			
		
	def checkbutton_command(self, args, event=None):
		'''	args[0] is tkinter.StringVar instance
			args[1] is string
		'''
		var = args[0]
		key = args[1]
		
		self.font[key] = var.get()
		
		
	def optionmenu_command(self, event=None):
		''' When font(instance) is selected from optionmenu.
		'''
		self.font = self.fonts[self.fontdict[self.var.get()]]
		fontname = self.font.actual("family")
		fontindex = self.fontnames.index(fontname)
		self.selection_clear()
		self.lb.select_set(fontindex)
		self.lb.see(fontindex)
		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		self.sb.insert(0, fontsize)
		
		self.cb1.deselect()
		self.cb2.deselect()
		self.cb3.deselect()
		self.cb4.deselect()
		
		if self.font['weight'] == 'bold': self.cb1.select()
		if self.font['slant'] == 'italic': self.cb2.select()
		if self.font['underline'] == 1: self.cb3.select()
		if self.font['overstrike'] == 1: self.cb4.select()

		
	def change_font(self, event=None):
		''' Change values of current font-instance.
		'''
		try:
			self.font.config(
				family=self.lb.get(self.lb.curselection()),
				size=self.sb.get()
				)
		except tkinter.TclError: pass
		
		
	def quit_me(self):
		self.quit()
		self.destroy()
