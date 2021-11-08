import tkinter as tk

class MyDialog:

	choice = False	
	
	def __init__(self, parent):
	
		top = self.top = tk.Toplevel(parent)
		
		# Set position
		x = parent.winfo_x()
		y = parent.winfo_y()
		w = parent.winfo_width()
		h = parent.winfo_height()
		#print(x,y,w,h)
		top.geometry("+%d+%d" % (x+w/2-200, y+h/2-200))
		
		self.labelFrame = tk.Frame(top)
		self.myLabel = tk.Label(self.labelFrame, text='Load images from this folder?\n(Note: Large image stacks may take long time.)')

		self.buttonFrame = tk.Frame(top)
		self.myOkButton = tk.Button(self.buttonFrame, text='Ok', command=self.choiceTrue)
		self.myCancelButton = tk.Button(self.buttonFrame, text='Cancel', command=self.choiceFalse)


		self.labelFrame.grid(row=0)
		self.myLabel.grid(row=0)
		
		self.buttonFrame.grid(row=1)
		self.myOkButton.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
		self.myCancelButton.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

	def choiceTrue(self):
		self.choice = True
		self.top.destroy()
		#return(True)

	def choiceFalse(self):
		self.choice = False
		self.top.destroy()
		#return(False)

def showDialog(root):
	inputDialog = MyDialog(root)
	root.wait_window(inputDialog.top)
	print('Chosen: ', inputDialog.choice)
	return(inputDialog.choice)

def onclick():
	r = showDialog(root)
	print(r)


### Uncomment the following for testing
"""
root = tk.Tk()

mainLabel = tk.Label(root, text='Example for pop up input box')
mainLabel.pack()


mainButton = tk.Button(root, text='Click me', command=onclick)
mainButton.pack()

root.mainloop()
"""
