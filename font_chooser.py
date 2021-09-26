from tkinter import (
Toplevel, Tk, Frame, Text, Listbox, Spinbox, SINGLE
)

from tkinter.font import Font
import tkinter

class Fontchooser(Toplevel):
		
	def __init__(self, root, font_instance):
		super().__init__(root)
		self.protocol("WM_DELETE_WINDOW", self.quit_me)
		self.frame = Frame(self, width=480, height=275)
		self.frame.pack(pady=10)
		self.font = font_instance
		
		# Freeze Frame in place
		self.frame.grid_propagate(False)
		self.frame.columnconfigure(0, weight=10)

		self.t = Text(self.frame, font=self.font)
		self.t.grid(row=0, column=0)
		self.t.grid_rowconfigure(0, weight=1)
		self.t.grid_columnconfigure(0, weight=1)
		
		self.lb = Listbox(self, selectmode=SINGLE, width=80)
		self.lb.pack()
		
		self.fontlist = [f for f in tkinter.font.families()]
		
		# remove duplicates then sort
		s = set(self.fontlist)
		self.fontlist = [f for f in s]
		self.fontlist.sort()
		self.max = 24
		self.min = 8
		
		self.sb = Spinbox(self, from_=self.min, to=self.max, increment=2, command=self.change_font)
		self.sb.pack()
		
		# get current fontsize and show it in spinbox
		self.sb.delete(0, 'end')
		fontsize = self.font['size']
		
		if self.min <= fontsize <= self.max:
			self.sb.insert(0, fontsize)
		else:
			self.sb.insert(0, '12')
		
		for i,f in enumerate(self.fontlist):
			# get current fontnames index:
			if f == self.font.actual("family"): fontindex = i
			self.lb.insert('end', f)
		
		# show current fontname in listbox
		self.lb.select_set(fontindex)
		self.lb.see(fontindex)
		
		self.lb.bind('<ButtonRelease-1>', self.change_font)
		
		
	def change_font(self, event=None):
		self.font.config(
			family=self.lb.get(self.lb.curselection()),
			size=self.sb.get()
			)
		
		
	def quit_me(self):
		self.quit()
		self.destroy()
