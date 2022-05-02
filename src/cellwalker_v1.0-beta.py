import os
import shutil
import random
import copy
import time

# Use this to check matplotlib backend. It could be TkAgg, Qt4Agg or Qt5Agg etc.
#import matplotlib
#print(matplotlib.get_backend())

import tkinter as tk
from tkinter import *
#from tkinter.tix import *
from tkinter import filedialog
from tkinter import colorchooser
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from CollapsiblePane import CollapsiblePane as cp

# Implement the default Matplotlib key bindings.
#from matplotlib.backend_bases import key_press_handler
import matplotlib.pyplot as plt
from matplotlib import cm

from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import proj3d

# Set custome path for importing cloudvolume
import sys
sys.path.insert(0, '../packages/cloud-volume_harsh/build/lib')
import cloudvolume

# Set custome path for importing kimimaro
import sys
sys.path.insert(0, '../packages/kimimaro_harsh/build/lib.linux-x86_64-3.7')
import kimimaro

import math
import numpy as np
import scipy.ndimage
from scipy.spatial.transform import Rotation
from PIL import Image, ImageTk
import cv2

import networkx as nx


#import simple_pick_info.pick_info
from mpldatacursor import datacursor

from skimage import measure
from sklearn.decomposition import PCA
from sklearn import svm
from sklearn.utils import shuffle

# For orthogonal distance regression
from skspatial.objects import Line
from skspatial.objects import Points

# For least squares regression
from sklearn.linear_model import LinearRegression


from CreateToolTip import CreateToolTip

#from MyDialog import MyDialog
from MyDialog import showDialog

###################################################################################
def sorted_nicely(l): 
	""" Sort the given iterable in the way that humans expect."""
	"""Taken from: http://stackoverflow.com/questions/2669059/how-to-sort-alpha-numeric-set-in-python"""
	convert = lambda text: int(text) if text.isdigit() else text 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanum_key)
###END FUNCTION sorted_nicely(l)


bg_color_1 = "#222222"
active_bg_color_1 = "#888888"
bg_color_2 = "#666666"
bg_color_2_button = "#DD9611"
bg_color_3_entry = "#333333"
fg_color_1 = "#FFEBEB"
fg_color_2 = "#EBEBEB"
fg_color_3 = "#222222"

"""
style = ttk.Style()
style.theme_use("alt")
style.configure("TNotebook", tabmargins=[2, 5, 2, 1], background=bg_color_1)
style.configure("TNotebook.Tab", padding=[5, 1], background=bg_color_3_entry, foreground=fg_color_1, focuscolor="#999999")
style.map("TNotebook.Tab", background=[("selected", "#555555")],
																		expand=[("selected", [1, 1, 1, 0])],
																		font=[("selected", ['Arial',10,'bold'])],
																		borderwidth=[("selected", 0)])
style.configure("TSeparator", background=bg_color_1)
style.configure('Dark.TFrame', background='#444444')
style.configure('Dark.Vertical.TScrollbar', background='#FF4444', troughcolor='#6666FF', arrowcolor='#CCFFCC')
"""

class ScrollableFrame(ttk.Frame):
	#Taken from https://blog.tecladocode.com/tkinter-scrollable-frames/
	def __init__(self, container, *args, **kwargs):
		super().__init__(container, *args, **kwargs)

		#s = ttk.Style()
		#s.theme_use("alt")
		#s.configure('Dark.TFrame', background='#444444')
		#s.configure('Dark.Vertical.TScrollbar', background='#4444FF', troughcolor='#666666', arrowcolor='#FF0000')


		canvas = tk.Canvas(self, width=kwargs['width'], height=kwargs['height'], bg=bg_color_1, highlightthickness=0)
		scrollbar = ttk.Scrollbar(self, orient="vertical", style='Dark.Vertical.TScrollbar', command=canvas.yview)
		#scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)


		self.scrollable_frame = ttk.Frame(canvas, style='Dark.TFrame')#, name="scroll")#, style=ttk.Style().configure('TFrame.Frame1', background="#00FF00"))

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(
				scrollregion=canvas.bbox("all")
			)
		)

		canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

		canvas.configure(yscrollcommand=scrollbar.set)

		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

###################################################################################

class Root(Tk):
	def __init__(self):
		super(Root, self).__init__()

		# Initialize variables
		self.dirname = "./"
		self.uniq_labels = []
		self.matrices = []
		self. matrices_original = []
		self.labels = None
		self.threeDmatrix = None
		self.image_num_cur = 0
		#self.image_num_lbl_text = StringVar('asdf')

		self.uniq_labels = None

		self.segment_vars = []
		self.segment_btns = []
		self.segment_color_btns = []
		#self.segment_color_btn_image=PhotoImage(file="chooseColorIcon1.png").subsample(10)


		self.images_outdir = None
		self.anis = 1

		self.image_canvas_width = int(self.winfo_screenheight()/2)#300
		self.image_canvas_height = int(self.winfo_screenheight()/2)#300
		self.image_width = 100
		self.image_height = 100

		self.colormap = {}
		self.colormapHex = {}

		self.default_downsample = '10'

		self.mip_dict = {
		"none": [1.,1.,1.],
		"0": [4.,4.,30.],
		"1": [8.,8.,30.],
		"2": [16.,16.,30.],
		"3": [32.,32.,30.],
		"4": [64.,64.,30.],
		"5": [128.,128.,30.],
		"6": [256.,256.,30.],
		"7": [512.,512.,30.]
		}

		self.skels = None
		self.skel_full = None
		self.skel = None
		self.canvas = None
		self.ax = None
		self.f = None

		self.selectedNodes = []
		
		#self.skeleton_canvas_width = 250
		#self.skeleton_canvas_height = 250

		w = 300#680 # width for the Tk root
		h = 820 # height for the Tk root

		# get screen width and height
		ws = self.winfo_screenwidth() # width of the screen
		hs = self.winfo_screenheight() # height of the screen

		# calculate x and y coordinates for the Tk root
		x = (ws/2) - (w/2)
		y = (hs/2) - (h/2)

		# set the dimensions of the screen and where it is placed
		#self.geometry('%dx%d+%d+%d' % (w, h, x, y))
		
		# Set position
		self.geometry("+%d+%d" % (x, y))
		# Set minimum size
		self.minsize(400,400)#640,400)
		# Set icon
		#self.wm_iconbitmap('icon.ico')
		# Set background color
		#self.configure(background='#4D4D4D')
		self.configure(background=bg_color_1)
		# Set title
		self.title("CellWalker v0.3-beta")


############################## Define ttk style ##################################
		"""
		self.style = ttk.Style()

		self.style.theme_create( "style1",
												parent="default")
												settings={"TNotebook":     {"configure": {"tabmargins": [2, 5, 2, 1], "background": bg_color_1} },
																	"TNotebook.Tab": {"configure": {"padding": [5, 1], "background": bg_color_3_entry, "foreground": fg_color_1, "focuscolor":"#999999"},
																										"map":			 {"background": [("selected", "#555555")],
																																	"expand":     [("selected", [1, 1, 1, 0])],
																																	"font":       [("selected", ['Arial',10,'bold'])]
#																																	"borderwidth":[("selected", 0)]
																																 }},
																	"TSeparator": {"configure": {"background": bg_color_1}}
#																	"Dark.TFrame": {"configure": {"background": bg_color_1}},
#																	"Dark.Vertical.TScrollbar": {"configure": {"background": bg_color_1, troughcolor: '#666666', arrowcolor: '#CCCCCC'}}
#																	"TNotebook.label": {"configure": {"foreground": fg_color_1}}
																 } )
		self.style.theme_use("style1")

		#self.style.theme_use("classic")
		"""

		#"""
		self.style = ttk.Style()
		self.style.theme_use("alt")
		self.style.configure("TNotebook", tabmargins=[2, 5, 2, 1], background=bg_color_1)
		self.style.configure("TNotebook.Tab", padding=[5, 1], background=bg_color_1, foreground=fg_color_2, focuscolor="#999999")
		self.style.map("TNotebook.Tab", background=[("selected", "#5680C2")],
																		expand=[("selected", [1, 1, 1, 0])],
																		font=[("selected", ['Arial',10,'bold'])],
																		borderwidth=[("selected", 1)])
		#self.style.configure("TNotebook.Tab", padding=[5, 1], background=bg_color_3_entry, foreground=fg_color_1, focuscolor="#999999")
		#self.style.map("TNotebook.Tab", background=[("selected", "#555555")],
		#																expand=[("selected", [1, 1, 1, 0])],
		#																font=[("selected", ['Arial',10,'bold'])],
		#																borderwidth=[("selected", 1)])
		self.style.configure("TSeparator", background=bg_color_1)
		self.style.configure('Dark.TFrame', background=bg_color_1)
		self.style.configure('Vertical.TScrollbar', arrowcolor='#000000', troughcolor=bg_color_2, background=bg_color_1)
		self.style.configure('TButton', background=bg_color_1, foreground=fg_color_1)
		self.style.map('TButton', foreground=[('pressed', fg_color_1),
																					('active', fg_color_1)],
															background=[('pressed', bg_color_2),
																					('active', bg_color_2)])
																					
		#self.style.configure('TCheckbutton', background=bg_color_1, foreground=fg_color_1, activebackground='#FF0000')
		self.style.configure('TFrame', background=bg_color_1)
		#self.style.configure("Dark.Vertical.TScrollbar", gripcount=0,
		#											background="Green", darkcolor="DarkGreen", lightcolor="LightGreen",
		#											troughcolor="gray", bordercolor="blue", arrowcolor="white")
		#self.style.configure('Dark.Vertical.TScrollbar', background="#00FF00")
		#self.style.configure('Dark.Vertical.TScrollbar', troughcolor='#FF6666')
		#"""
#Style().configure("TNotebook", background=self.d["tcolor"]); #This line isn't technically part of the answer, but people seeing this will likely want to know this, too (it changes the color of the tab bar portion without tabs on it).
#Style().map("TNotebook.Tab", background=[("selected", self.d["atbgcolor"])], foreground=[("selected", self.d["atfgcolor"])]);
#Style().configure("TNotebook.Tab", background=self.d["tbgcolor"], foreground=self.d["tfgcolor"]);

############################## Define widgets ##################################

		#Top frame
		self.settings_frame = Frame(self, bg=bg_color_1, height=50)
		self.browsedir_btn = Button(self.settings_frame, text="Choose directory", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_dir)
		#self.loaddata_btn = Button(self.settings_frame, text="Load data", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.load_data)
		self.erosion = BooleanVar()
		self.erosion_chk = Checkbutton(self.settings_frame, text="", variable=self.erosion, bg=bg_color_1, activebackground=bg_color_2, fg=fg_color_3, activeforeground=fg_color_1, highlightthickness=0)
		self.erosion_lbl = Label(self.settings_frame, anchor=E, text="Apply erosion, iterations: ", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))
		self.erosioniter_entry = Entry(self.settings_frame, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.translate_lbl = Label(self.settings_frame, anchor=E, text="  Translations (X, Y, Z):", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))
		self.translate_entry = Entry(self.settings_frame, width=20, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.translate_entry.insert(END, "0, 0, 0")
		self.selecteddir_lbl = Label(self.settings_frame, width=50, anchor=E, text="No directory chosen, please choose directory.", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))

		self.sep1 = ttk.Separator(self, orient="horizontal")

		#Viewer frame
		self.viewer_frame = Frame(self, bg=bg_color_1)

		#Image viewer frame
		self.image_frame = Frame(self.viewer_frame, bg=bg_color_1)
		self.image_top_frame = Frame(self.image_frame, bg=bg_color_1)
		#self.image_middle_frame = Frame(self.image_frame, bg=bg_color_1)
		self.image_bottom_frame = Frame(self.image_frame, bg=bg_color_1)
		self.image_canvas = Canvas(self.image_top_frame, width=self.image_canvas_width, height=self.image_canvas_height, bg=bg_color_1, highlightthickness=0)


		self.image_next_btn = Button(self.image_top_frame, text=">", bg=bg_color_2, activebackground=active_bg_color_1, highlightthickness=0, command=self.image_next)
		self.image_slider = Scale(self.image_top_frame, from_=0, to=200, length=self.image_canvas_width-80, width=12, orient=HORIZONTAL, bg=bg_color_2, activebackground=active_bg_color_1, fg=fg_color_1, highlightthickness=0, command=self.update_image)
		#self.image_slider.bind('Button-1',self.image_)
		#self.image_num_lbl = Label(self.image_top_frame, width=10, anchor=CENTER, text="0", bg=bg_color_1, font=("Arial", 10))
		self.image_prev_btn = Button(self.image_top_frame, text="<", bg=bg_color_2, activebackground=active_bg_color_1, highlightthickness=0, command=self.image_prev)

		# Bind events to buttons or keys.
		#self.image_next_btn.bind('<ButtonPress-1>',self.image_next2)
		#self.image_prev_btn.bind('<ButtonPress-1>',self.image_prev2)
		self.image_canvas.bind('<Right>',self.image_next_key)
		self.image_canvas.bind('<Left>',self.image_prev_key)

		self.image_canvas.bind('<Button-1>',lambda e: self.image_canvas.focus_set())


		#####self.sep2 = ttk.Separator(self.image_frame, orient="horizontal")

		#self.images_outdir_entry = Entry(self.image_bottom_frame, width=20, bg=bg_color_1)
		#self.images_outdir_entry.insert(END, "Specify output directory")
		#####self.images_outdir_lbl = Label(self.image_bottom_frame, width=30, anchor=W, text="Choose output directory", bg=bg_color_1, fg=fg_color_1)
		#####self.images_outdir_browse_btn = Button(self.image_bottom_frame, text="Browse", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_images_outdir)

		#####self.images_anis_lbl = Label(self.image_bottom_frame, width=10, anchor=W, text="Anisotropy", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))
		#####self.images_anis_entry = Entry(self.image_bottom_frame, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		#####self.images_anis_entry.insert(END, "1")

		#####self.images_save_btn = Button(self.image_bottom_frame, text="Save images", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.save_images)

		self.save_surface_btn = Button(self.image_bottom_frame, text="Save Surface", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.save_surface)



		self.annotation_frame = Frame(self.viewer_frame, bg=bg_color_1)#, height=400
		self.annotation_top_frame = ScrollableFrame(self.annotation_frame, width=170, height=self.image_canvas_height)#, bg=bg_color_1)#, bg="blue")
		self.annotation_bottom_frame = Frame(self.annotation_frame, bg=bg_color_1)


		#???CAUTION: FOR TESTING
		self.l = []
		for i in range(0,200):
			self.l.append(tk.Label(self.annotation_top_frame.scrollable_frame, text='', bg=bg_color_1))


		self.merge_segments_btn = Button(self.annotation_bottom_frame, text="Add to merge list", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.merge_segments)
		self.merge_list_txt = Text(self.annotation_bottom_frame, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0, height=5, width=26)

		self.skel_notebook = ttk.Notebook(self.viewer_frame)

		self.frame1 = Frame(self.skel_notebook, bg=bg_color_1, padx=10)#, height=400

		self.skel_frame1 = LabelFrame(self.frame1, text="Generate skeleton", padx = 10, bg=bg_color_1, fg=fg_color_1)

		self.skel_params_lbl = Label(self.skel_frame1, width=25, anchor=W, text="Skeletonization parameters", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.reset_skel_params_btn = Button(self.skel_frame1, text="Reset", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.reset_skel_params)

		self.kimimaro_param_cpane = cp(self.skel_frame1, 'Hide advanced options', 'Show advanced options')

		self.kimimaro_param_standard = {'mip_level':                 {'srno':1,  'type':'numeric', 'width':5, 'default':3,     'step':1},
													 					'scale':                     {'srno':2,  'type':'numeric', 'width':5, 'default':1,     'step':1},
													 					'const':                     {'srno':3,  'type':'numeric', 'width':5, 'default':500,   'step':100}}
		self.kimimaro_param_advanced = {'pdrf_exponent':             {'srno':4,  'type':'numeric', 'width':5, 'default':4,     'step':1},
													 					'pdrf_scale':                {'srno':5,  'type':'numeric', 'width':5, 'default':100000,'step':10000},
												 						'soma_detection_threshold':  {'srno':6,  'type':'numeric', 'width':5, 'default':1100,  'step':500},
												 						'soma_acceptance_threshold': {'srno':7,  'type':'numeric', 'width':5, 'default':3500,  'step':1000},
												 						'soma_invalidation_scale':   {'srno':8,  'type':'numeric', 'width':5, 'default':1.0,   'step':1},
											 							'soma_invalidation_const':   {'srno':9,  'type':'numeric', 'width':5, 'default':300,   'step':100},
											 							'dust_threshold':            {'srno':10, 'type':'numeric', 'width':5, 'default':1000,  'step':100},
												 						'fix_branching':             {'srno':11, 'type':'boolean', 'width':0, 'default':True},
												 						'fix_borders' :              {'srno':12, 'type':'boolean', 'width':0, 'default':True},
												 						'parallel':                  {'srno':13, 'type':'numeric', 'width':5, 'default':1},
												 						'parallel_chunk_size':       {'srno':14, 'type':'numeric', 'width':5, 'default':100}}

		self.skel_widgets = {}
		self.skel_widgets_vars = {}

		def create_kimimaro_param_widgets(params=None, parent=None):
			for srno, param in sorted([(v['srno'], k) for k,v in params.items()]):
				#print(srno, param)
				print("Creating widget for kimimaro parameter", srno, "-", param)
				self.skel_widgets[param] = {}
				if params[param]['type'] == 'numeric':
					self.skel_widgets[param] = {'label': Label(parent, width=25, anchor=W, text=param, bg=bg_color_1, fg=fg_color_1, font=("Arial", 10)),
																			'entry': Entry(parent, width=params[param]['width'], bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)}
					self.skel_widgets[param]['entry'].insert(END, params[param]['default'])
				
				elif params[param]['type'] == 'boolean':
					self.skel_widgets_vars[param] = BooleanVar()
					self.skel_widgets[param] = {'label': Label(parent, width=25, anchor=W, text=param, bg=bg_color_1, fg=fg_color_1, font=("Arial", 10)),
																			'entry': Checkbutton(parent, text="", variable=self.skel_widgets_vars[param], bg=bg_color_1, activebackground=bg_color_2, fg=fg_color_3, activeforeground=fg_color_1, highlightthickness=0)}
					self.skel_widgets_vars[param].set(params[param]['default'])

				else:
					pass

		create_kimimaro_param_widgets(params=self.kimimaro_param_standard, parent=self.skel_frame1)
		create_kimimaro_param_widgets(params=self.kimimaro_param_advanced, parent=self.kimimaro_param_cpane.frame)


		self.calc_skeleton_btn = Button(self.skel_frame1, text="Skeletonize", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.skeletonize)
		self.open_skeleton_btn = Button(self.skel_frame1, text="Open Skeleton", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.open_skeleton)


		self.downsample_lbl = Label(self.skel_frame1, width=25, anchor=W, text="Downsample", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))
		
		self.downsample_entry = Entry(self.skel_frame1, width=5, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.downsample_entry.insert(END, self.default_downsample)

		self.colorby_var = StringVar(self, 'radius')
		self.colorby_lbl = Label(self.skel_frame1, width=25, anchor=W, text="Color by:", bg=bg_color_1, fg=fg_color_1, font=("Arial", 10))
		self.colorby_radius_rbtn = Radiobutton(self.skel_frame1,     text="radius",    value='radius', variable=self.colorby_var, bg=bg_color_1, activebackground=bg_color_2, fg=fg_color_1, activeforeground=fg_color_1, highlightthickness=0, selectcolor="#555555")#, indicatoron=1, borderwidth=0, selectcolor="white", font=("Arial", 10)) #width=12,
		self.colorby_components_rbtn = Radiobutton(self.skel_frame1, text="component", value='components', variable=self.colorby_var, bg=bg_color_1, activebackground=bg_color_2, fg=fg_color_1, activeforeground=fg_color_1, highlightthickness=0, selectcolor="#555555")#, indicatoron=1, borderwidth=0, selectcolor="white", activebackground="white", font=("Arial", 10)) #width=12,

		#self.view_skeleton_btn = Button(self.skel_frame1, text="View skeleton", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.view_skeleton)
		self.draw_skeleton_btn = Button(self.skel_frame1, text="Draw skeleton", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.draw_skeleton)
		self.save_skeleton_btn = Button(self.skel_frame1, text="Save Skeleton", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.save_skeleton)

		self.cylinder_radius_entry = Entry(self.skel_frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.cylinder_radius_entry.insert(END, "0.01")
		self.sphere_radius_entry = Entry(self.skel_frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.sphere_radius_entry.insert(END, "0.04")
		
		
		self.skel_frame2 = LabelFrame(self.frame1, text="Skeleton-based analysis", padx=10, pady=10, width=150, bg=bg_color_1, fg=fg_color_1)



		icon1 = PhotoImage(file="./icon_ruler.png")
		#icon1 = icon1.subsample(30, 30)# Not needed if icon image is of correct size
		icon2 = PhotoImage(file="./icon_cross-section.png")
		icon3 = PhotoImage(file="./icon_curvature.png")
		self.length_btn = Button(self.skel_frame2, image=icon1, bg=bg_color_1, highlightthickness=0, activebackground=active_bg_color_1, fg=fg_color_3, command=self.length_analysis)#  , bg=bg_color_2_button
		self.length_btn.image = icon1
		self.length_btn_ttp = CreateToolTip(self.length_btn, "Calculate length\n(Select two nodes on the skeleton first)")
		
		self.crossSection_btn = Button(self.skel_frame2, image=icon2, bg=bg_color_1, highlightthickness=0, activebackground=active_bg_color_1, fg=fg_color_3, command=self.crossSection_analysis)
		self.crossSection_btn.image = icon2
		self.crossSection_btn_ttp = CreateToolTip(self.crossSection_btn, "Create cross-sections\n(Select two nodes on the skeleton first)")

		self.curvature_btn = Button(self.skel_frame2, image=icon3, bg=bg_color_1, highlightthickness=0, activebackground=active_bg_color_1, fg=fg_color_3, command=self.curvature_analysis)
		self.curvature_btn.image = icon3
		self.curvature_btn_ttp = CreateToolTip(self.curvature_btn, "Calculate curvature\n(Select two nodes on the skeleton first)")
		
		#self.tip = Balloon(self)
		# bind btn with balloon instance 
		#self.tip.bind_widget(self.length_btn, balloonmsg = "This is Button widget")


		#self.translate_x_entry = Entry(self.frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		#self.translate_x_entry.insert(END, "0")
		#self.translate_y_entry = Entry(self.frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		#self.translate_y_entry.insert(END, "0")
		#self.translate_z_entry = Entry(self.frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		#self.translate_z_entry.insert(END, "0")
		#self.translate_entry = Entry(self.frame1, width=8, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		#self.translate_entry.insert(END, "0, 0, 0")




		### Mitochondria analysis settings in frame3
		self.frame3 = Frame(self.skel_notebook, bg=bg_color_1)#, height=400

		self.frame3_note = Frame(self.frame3, bg=bg_color_1)
		self.mito_note_lbl = Label(self.frame3_note, anchor=W, wraplength=500, text="Note: Mark the segments that you want to exclude.", bg=bg_color_1, fg=fg_color_1, font='Arial 10')#font=("Arial", BOLD, 10))

		self.frame3_run = Frame(self.frame3, bg=bg_color_1)
		self.mito_miplevel_lbl = Label(self.frame3_run, anchor=W, text="Mip level", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mito_miplevel_entry = Entry(self.frame3_run, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mito_miplevel_entry.insert(END, "3")
		self.mito_outfile_lbl = Label(self.frame3_run, anchor=W, text="Output file", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mito_outfile_entry = Entry(self.frame3_run, width=20, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mito_outfile_browse_btn = Button(self.frame3_run, text="Browse", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_file_mito)
		self.mito_analysis_btn = Button(self.frame3_run, text="Analyse mitochondria", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.analyse_mito)
		self.mito_analysis_status_lbl = Label(self.frame3_run, anchor=W, text="Analysis not running", bg=bg_color_1, fg="#EA9429", font='Arial 10 bold')#font=("Arial", BOLD, 10))



		### Draw maximum margin seperation plane (mmsp) between two selected obj files using SVM: frame4
		### Assumes that the coordinates of vertices in the two obj files are absolute (not relative).
		### No scaling will be done. The coordinates will treated as is.
		self.frame4 = Frame(self.skel_notebook, bg=bg_color_1)#, height=400

		self.frame4_note = Frame(self.frame4, bg=bg_color_1)
		self.mmsp_note_lbl = Label(self.frame4_note, anchor=W, wraplength=500, text="Select two obj files to build Maximum Margin Separating Plane (MMSP).", bg=bg_color_1, fg=fg_color_1, font='Arial 10')#font=("Arial", BOLD, 10))

		self.frame4_run = Frame(self.frame4, bg=bg_color_1)

		self.mmsp_objfile1_lbl = Label(self.frame4_run, anchor=W, text="OBJ file 1", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mmsp_objfile1_entry = Entry(self.frame4_run, width=20, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mmsp_objfile1_browse_btn = Button(self.frame4_run, text="Browse", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_objfile1)
		self.mmsp_objfile2_lbl = Label(self.frame4_run, anchor=W, text="OBJ file 2", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mmsp_objfile2_entry = Entry(self.frame4_run, width=20, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mmsp_objfile2_browse_btn = Button(self.frame4_run, text="Browse", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_objfile2)

		self.mmsp_outfile_lbl = Label(self.frame4_run, anchor=W, text="MMSP output file", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mmsp_outfile_entry = Entry(self.frame4_run, width=20, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mmsp_outfile_browse_btn = Button(self.frame4_run, text="Browse", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.browse_file_mmsp)

		self.mmsp_percent_vertices_lbl = Label(self.frame4_run, anchor=W, text="Percent of vertices to be used", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.mmsp_percent_vertices_entry = Entry(self.frame4_run, width=4, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.mmsp_percent_vertices_entry.insert(END, "100")
		self.mmsp_btn = Button(self.frame4_run, text="Calculate MMSP", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.calculate_mmsp)
		self.mmsp_status_lbl = Label(self.frame4_run, anchor=W, text="Calculation not running", bg=bg_color_1, fg="#EA9429", font='Arial 10 bold')#font=("Arial", BOLD, 10))


		# Find protrusions of cells using erosion-dilation algorithm
		self.frame5 = Frame(self.skel_notebook, bg=bg_color_1)#, height=400

		self.frame5_note = Frame(self.frame5, bg=bg_color_1)
		self.protr_note_lbl = Label(self.frame5_note, anchor=W, wraplength=500, text="All selected labels will be merged before finding protrusions.", bg=bg_color_1, fg=fg_color_1, font='Arial 10')#font=("Arial", BOLD, 10))

		self.frame5_run = Frame(self.frame5, bg=bg_color_1)
		
		self.protr_miplevel_lbl = Label(self.frame5_run, anchor=W, text="Mip level", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.protr_miplevel_entry = Entry(self.frame5_run, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.protr_miplevel_entry.insert(END, "3")

		self.protr_setlabels_lbl = Label(self.frame5_run, anchor=W, text="Use previously set labels", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.use_previously_set_labels = BooleanVar()
		self.protr_setlabels_chk = Checkbutton(self.frame5_run, text="", variable=self.use_previously_set_labels, bg=bg_color_1, activebackground=bg_color_2, fg=fg_color_3, activeforeground=fg_color_1, highlightthickness=0)

		self.protr_erosioniter_lbl = Label(self.frame5_run, anchor=W, text="Erosion iterations", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.protr_erosioniter_entry = Entry(self.frame5_run, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.protr_erosioniter_entry.insert(END, "10")

		self.protr_dilationiter_lbl = Label(self.frame5_run, anchor=W, text="Dilation iterations", bg=bg_color_1, fg=fg_color_1, font='Arial 10 bold')#font=("Arial", BOLD, 10))
		self.protr_dilationiter_entry = Entry(self.frame5_run, width=3, bg=bg_color_3_entry, fg=fg_color_1, highlightthickness=0)
		self.protr_dilationiter_entry.insert(END, "30")

		self.protr_analysis_btn = Button(self.frame5_run, text="Find & save protrusions and soma", bg=bg_color_2_button, activebackground=active_bg_color_1, fg=fg_color_3, highlightthickness=0, command=self.findCellProtrusions)
		self.protr_analysis_status_lbl = Label(self.frame5_run, anchor=W, text="Analysis not running", bg=bg_color_1, fg="#EA9429", font='Arial 10 bold')#font=("Arial", BOLD, 10))


		self.skel_notebook.add(self.frame1, text="Skeletonize")
		self.skel_notebook.add(self.frame5, text="Find protrusions")
		self.skel_notebook.add(self.frame3, text="Segment properties")
		self.skel_notebook.add(self.frame4, text="MMSP")

####################### Place widgets in the root ############################

		self.settings_frame.grid(row=0, column=0, padx=10, pady=10)
		self.browsedir_btn.grid(row=0, column=0, sticky=W)
		#self.loaddata_btn.grid(row=0, column=0, sticky=E)
		self.erosion_chk.grid(row=0, column=1)
		self.erosion_lbl.grid(row=0, column=2)
		self.erosioniter_entry.grid(row=0, column=3)
		self.translate_lbl.grid(row=0, column=4, padx=10)
		self.translate_entry.grid(row=0, column=5, pady=10, sticky=W)
		self.selecteddir_lbl.grid(row=1, column=0, sticky=W)
		#self.settings_frame.grid_propagate(0)

		self.sep1.grid(row=1, column=0, sticky="we", padx=10)

		self.viewer_frame.grid(row=2,column=0)#, padx=10, pady=10)

		self.image_frame.grid(row=0, column=0, sticky=NW)
		self.image_top_frame.grid(row=0, column=0, padx=10, sticky=N)
		#self.image_middle_frame.grid(row=1, column=0, padx=10, sticky=SW)
		#####self.sep2.grid(row=2, column=0, sticky="we", padx=10, pady=10)
		self.image_bottom_frame.grid(row=3, column=0, padx=10, sticky=SW)

		self.image_canvas.grid(row=0, column=0, columnspan=3, pady=10, sticky=NW)


		self.image_prev_btn.grid(row=1, column=0, sticky=W)
		self.image_slider.grid(row=1, column=1, sticky=W)
		#self.image_num_lbl.grid(row=0, column=1)
		self.image_next_btn.grid(row=1, column=2, sticky=E)


		#self.images_outdir_entry.grid(row=1, column=0, pady=10, sticky=W)
		self.save_surface_btn.grid(row=0, column=0, pady=10, sticky=W)
		#####self.images_outdir_lbl.grid(row=0, column=0, pady=10, sticky=W)
		#####self.images_outdir_browse_btn.grid(row=0, column=1, padx=10, sticky=W)
		#####self.images_anis_lbl.grid(row=1, column=0, sticky=W)
		#####self.images_anis_entry.grid(row=1, column=1, padx=10, sticky=W)
		#####self.images_save_btn.grid(row=2, column=0, pady=10, sticky=W)


		self.annotation_frame.grid(row=0, column=1, sticky=NE, padx=10, pady=10)
		self.annotation_top_frame.grid(row=0, column=0, sticky=N)
		#self.annotation_top_frame.grid_propagate(0)
		self.annotation_bottom_frame.grid(row=1, column=0, pady=10, sticky=W)


		#???CAUTION: FOR TESTING
		for i in range(0,50):
			self.l[i].grid(row=i, column=0)


		self.merge_segments_btn.grid(row=0, column=0, pady=10, sticky=NW)
		self.merge_list_txt.grid(row=1, column=0, sticky=NW)

		self.skel_notebook.grid(row=0, column=2, sticky=NW)
		### No need to grid sub-frames of the notebook separately.
		#self.frame1.grid(row=0, column=2, sticky=NE, padx=10, pady=10)


		# Single skeleton calculation
		
		self.skel_frame1.grid(row=0, column=0, pady=5, sticky=W)

		self.skel_params_lbl.grid(row=0, column=0, pady=10, sticky=W)
		self.reset_skel_params_btn.grid(row=0, column=1, pady=10, sticky=E)

		row = 1
		for srno, param in sorted([(v['srno'], k) for k,v in self.kimimaro_param_standard.items()]):
			self.skel_widgets[param]['label'].grid(row=row, column=0, pady=2, sticky=W)
			self.skel_widgets[param]['entry'].grid(row=row, column=1, sticky=W)
			row += 1

		self.kimimaro_param_cpane.grid(row=row, column=0, sticky=NW)
		
		r = 0
		for srno, param in sorted([(v['srno'], k) for k,v in self.kimimaro_param_advanced.items()]):
			self.skel_widgets[param]['label'].grid(row=r, column=0, pady=2, sticky=W)
			self.skel_widgets[param]['entry'].grid(row=r, column=1, sticky=W)
			r += 1

		row = row + 1
		self.calc_skeleton_btn.grid(row=row, column=0, pady=10, sticky=W)
		self.open_skeleton_btn.grid(row=row, column=1, pady=10, sticky=W)

		row = row + 1
		self.downsample_lbl.grid(row=row, column=0, sticky=W)
		self.downsample_entry.grid(row=row, column=1, sticky=W)

		row = row + 1
		self.colorby_lbl.grid(row=row, column=0, sticky=W)
		self.colorby_radius_rbtn.grid(row=row, column=0, sticky=W)
		self.colorby_components_rbtn.grid(row=row, column=1, sticky=W)

		row = row + 1
		#self.view_skeleton_btn.grid(row=row, column=0, pady=10, sticky=W)
		self.draw_skeleton_btn.grid(row=row, column=0, pady=10, sticky=W)
		self.save_skeleton_btn.grid(row=row, column=1, pady=10, sticky=W)
		self.cylinder_radius_entry.grid(row=row, column=2, pady=10, sticky=W)
		self.sphere_radius_entry.grid(row=row, column=3, pady=10, sticky=W)


		self.skel_frame2.grid(row=1, column=0, pady=5, sticky=W)
		
		self.length_btn.grid(row=0, column=0, padx=5)
		self.crossSection_btn.grid(row=0, column=1, padx=5)
		self.curvature_btn.grid(row=0, column=2, padx=5)

		#self.translate_x_entry.grid(row=row+5, column=1, pady=10, sticky=W)
		#self.translate_y_entry.grid(row=row+5, column=2, pady=10, sticky=W)
		#self.translate_z_entry.grid(row=row+5, column=3, pady=10, sticky=W)
		#self.translate_entry.grid(row=row+5, column=1, pady=10, sticky=W)




		self.frame3_note.grid(row=0, column=0, columnspan=4, padx=5, sticky=W)
		self.mito_note_lbl.grid(row=0, column=0, pady=10, sticky=W)

		self.frame3_run.grid(row=1, column=0, columnspan=4, padx=5, sticky=W)
		self.mito_miplevel_lbl.grid(row=0, column=0, pady=10, sticky=W)
		self.mito_miplevel_entry.grid(row=0, column=1, pady=10, sticky=W)
		self.mito_outfile_lbl.grid(row=1, column=0, pady=10, sticky=W)
		self.mito_outfile_entry.grid(row=1, column=1, pady=10, sticky=W)
		self.mito_outfile_browse_btn.grid(row=1, column=2, padx=10, pady=10, sticky=W)
		self.mito_analysis_btn.grid(row=2, column=0, pady=10, sticky=W)
		self.mito_analysis_status_lbl.grid(row=2, column=1, padx=10, pady=10, sticky=W)





		self.frame4_note.grid(row=0, column=0, columnspan=4, padx=5, sticky=W)
		self.mmsp_note_lbl.grid(row=0, column=0, pady=10, sticky=W)

		self.frame4_run.grid(row=1, column=0, columnspan=4, padx=5, sticky=W)
		self.mmsp_objfile1_lbl.grid(row=0, column=0, pady=10, sticky=W)
		self.mmsp_objfile1_entry.grid(row=0, column=1, pady=10, sticky=W)
		self.mmsp_objfile1_browse_btn.grid(row=0, column=2, padx=10, pady=10, sticky=W)
		self.mmsp_objfile2_lbl.grid(row=1, column=0, pady=10, sticky=W)
		self.mmsp_objfile2_entry.grid(row=1, column=1, pady=10, sticky=W)
		self.mmsp_objfile2_browse_btn.grid(row=1, column=2, padx=10, pady=10, sticky=W)
		self.mmsp_outfile_lbl.grid(row=2, column=0, pady=10, sticky=W)
		self.mmsp_outfile_entry.grid(row=2, column=1, pady=10, sticky=W)
		self.mmsp_outfile_browse_btn.grid(row=2, column=2, padx=10, pady=10, sticky=W)

		self.mmsp_percent_vertices_lbl.grid(row=3, column=0, pady=10, sticky=W)
		self.mmsp_percent_vertices_entry.grid(row=3, column=1, pady=10, sticky=W)
		self.mmsp_btn.grid(row=4, column=0, pady=10, sticky=W)
		self.mmsp_status_lbl.grid(row=4, column=1, padx=10, pady=10, sticky=W)




		self.frame5_note.grid(row=0, column=0, columnspan=4, padx=5, sticky=W)
		self.protr_note_lbl.grid(row=0, column=0, pady=10, sticky=W)

		self.frame5_run.grid(row=1, column=0, columnspan=4, padx=5, sticky=W)
		self.protr_miplevel_lbl.grid(row=0, column=0, pady=10, sticky=W)
		self.protr_miplevel_entry.grid(row=0, column=1, pady=10, sticky=W)
		self.protr_setlabels_lbl.grid(row=1, column=0, pady=10, sticky=W)
		self.protr_setlabels_chk.grid(row=1, column=1, pady=10, sticky=W)
		self.protr_erosioniter_lbl.grid(row=2, column=0, pady=10, sticky=W)
		self.protr_erosioniter_entry.grid(row=2, column=1, pady=10, sticky=W)
		self.protr_dilationiter_lbl.grid(row=3, column=0, pady=10, sticky=W)
		self.protr_dilationiter_entry.grid(row=3, column=1, pady=10, sticky=W)
		self.protr_analysis_btn.grid(row=4, column=0, pady=10, sticky=W)
		self.protr_analysis_status_lbl.grid(row=4, column=1, padx=10, pady=10, sticky=W)


		### Ttk styles can also be cofigured like this.
		#self.style.configure('TNotebook.Tab', focuscolor=self.cget("background"))
		#self.style.configure('TNotebook.Tab', activebackground=self.cget("background"))
		#self.style.configure('TNotebook.Tab', background=self.cget("background"))


#########################################################################################################

	def skeletonize(self):

		self.calc_skeleton(mip_level=self.skel_widgets['mip_level']['entry'].get(),
											 scale=float(self.skel_widgets['scale']['entry'].get()),
											 const=float(self.skel_widgets['const']['entry'].get()),
											 pdrf_exponent=int(self.skel_widgets['pdrf_exponent']['entry'].get()),
											 pdrf_scale=float(self.skel_widgets['pdrf_scale']['entry'].get()),
											 soma_detection_threshold=float(self.skel_widgets['soma_detection_threshold']['entry'].get()),
											 soma_acceptance_threshold=float(self.skel_widgets['soma_acceptance_threshold']['entry'].get()),
											 soma_invalidation_scale=float(self.skel_widgets['soma_invalidation_scale']['entry'].get()),
											 soma_invalidation_const=float(self.skel_widgets['soma_invalidation_const']['entry'].get()),
											 dust_threshold=float(self.skel_widgets['dust_threshold']['entry'].get()),
											 fix_branching=bool(self.skel_widgets_vars['fix_branching'].get()),
											 progress=False, # rogress: default False, show progress bar
											 fix_borders=bool(self.skel_widgets_vars['fix_borders'].get()), # default True
											 parallel=int(self.skel_widgets['parallel']['entry'].get()), # <= 0 all cpu, 1 single process, 2+ multiprocess
											 parallel_chunk_size=int(self.skel_widgets['parallel_chunk_size']['entry'].get())) # how many skeletons to process before updating progress bar


	def browse_file_mito(self):
		#Open new file
		fname = self.dirname.split("/")[-1] + "_mito"
		self.filename_mito = filedialog.asksaveasfilename(initialdir=self.dirname,#'/'.join(self.dirname.split("/")[:-1]),
																											initialfile=fname+'.csv',
																											defaultextension='.csv',
																											title="Choose file to save mitochordria analysis",
																											filetypes=[('csv files', '.csv'),
																																 ('All files', '*')])

		self.mito_outfile_entry.delete(0, END)
		self.mito_outfile_entry.insert(END, self.filename_mito)
		print("Selected output file for mitochondria analysis:",self.filename_mito)
	### END ###

	def analyse_mito(self):
		print("Analysing mitochondria")
		self.mito_analysis_status_lbl.configure(text="Analysis running...")
		self.mito_analysis_status_lbl.update_idletasks()

		if self.mito_outfile_entry.get().strip() == "":
			print("Output file not specified.")
			self.mito_analysis_status_lbl.configure(text="Output file not specified.")
			return(1)

		# Get user specified mip level
		mip_level = self.mito_miplevel_entry.get()

		#print(self.uniq_labels)
		f = open(self.mito_outfile_entry.get(), 'w')
		f.write("Segment,Length_PC1_nm,Length_PC2_nm,Length_PC3_nm,SurfaceArea_nm^2,Volume_nm^3,SurfaceArea_pixel^2,Volume_voxels\n")

		ignore_segments = []
		i = 0
		for var in self.segment_vars:
			if var.get():
				l = self.uniq_labels[1:][i]
				print("Adding segment", l, "to ignore_segments list.")
				ignore_segments.append(l)
			i += 1

		for l in self.uniq_labels[1:]:
			if l in ignore_segments:
				continue
			self.mito_analysis_status_lbl.configure(text="Analysing Segment " + str(l))
			self.mito_analysis_status_lbl.update_idletasks()

			volume = np.sum(self.threeDmatrix == l)
			volume_nm3 = volume * self.mip_dict[mip_level][0] * self.mip_dict[mip_level][1] * self.mip_dict[mip_level][2]
			
			img = np.copy(self.threeDmatrix)
			img[img!=l] = 0
			x,y,z = np.where(img)
			X = np.array(list(zip(x,y,z)))
			X_nm = X * self.mip_dict[mip_level]#Convert to nanometer scale, ex. multiply by [32,32,30] if mip level is 3
			
			# Perform PCA and transform coordinates to rotated space
			pca = PCA(n_components=3)
			pca.fit(X_nm)
			X_nm_transformed = pca.transform(X_nm)
			
			# Get lengths along principal components
			l1 = X_nm_transformed[:,0].max() - X_nm_transformed[:,0].min()
			l2 = X_nm_transformed[:,1].max() - X_nm_transformed[:,1].min()
			l3 = X_nm_transformed[:,2].max() - X_nm_transformed[:,2].min()

			#X_nm_projected = np.matmul(pca.components_,X_nm.transpose()).transpose() # This is same as calling transform method, but without translating origin to mean
			#v1,v2,v3 = pca.explained_variance_
			
			#prop = measure.regionprops(img)# Not required right now

			verts, faces, normals, values = measure.marching_cubes_lewiner(img, 0, step_size=1)
			verts_nm = verts * self.mip_dict[mip_level]#Convert to nanometer scale, ex. multiply by [32,32,30] if mip level is 3
			surface_area = measure.mesh_surface_area(verts, faces)
			surface_area_nm2 = measure.mesh_surface_area(verts_nm, faces)

			f.write(str(l)+","+str(l1)+","+str(l2)+","+str(l3)+","+str(surface_area_nm2)+","+str(volume_nm3)+","+str(surface_area)+","+str(volume)+"\n")

		f.close()
		self.mito_analysis_status_lbl.configure(text="Analysis complete")
		print("Analysis complete")

	def browse_objfile1(self):
		#Get obj file name
		fname =  filedialog.askopenfilename(initialdir=self.dirname,#'/'.join(self.dirname.split("/")[:-1]),
																				title="Select obj file",
																				filetypes=[("obj files","*.obj"),("All files","*.*")])
		#fname = "/home/harsh/work/chiaraZurzoloLab/skeletonization/skeletonViewer/segmentedImages/P7/MATLABexports_stephen_v2/Segment__0039_max_connection3.nucleus1.obj"
		#fname = "/home/harsh/work/chiaraZurzoloLab/skeletonization/skeletonViewer/segmentedImages/P7/MATLABexports_stephen_v2/Segment__0094_max_connection3.Cell_1.obj"
		self.dirname = os.path.dirname(fname)

		self.mmsp_objfile1_entry.delete(0, END)
		self.mmsp_objfile1_entry.insert(END, fname)
		print("Selected objfile1 for MMSP calculation:", fname)
	### END ###

	def browse_objfile2(self):
		#Get obj file name
		fname =  filedialog.askopenfilename(initialdir=self.dirname,#'/'.join(self.dirname.split("/")[:-1]),
																				title="Select obj file",
																				filetypes=[("obj files","*.obj"),("All files","*.*")])
		#fname = "/home/harsh/work/chiaraZurzoloLab/skeletonization/skeletonViewer/segmentedImages/P7/MATLABexports_stephen_v2/Segment__0040_max_connection3.nucleus2.obj"
		#fname = "/home/harsh/work/chiaraZurzoloLab/skeletonization/skeletonViewer/segmentedImages/P7/MATLABexports_stephen_v2/Segment__0062_max_connection3.Cell_2.obj"
		self.dirname = os.path.dirname(fname)

		self.mmsp_objfile2_entry.delete(0, END)
		self.mmsp_objfile2_entry.insert(END, fname)
		print("Selected objfile2 for MMSP calculation:", fname)
	### END ###

	def browse_file_mmsp(self):
		#Open new file
		fname = "new_mmsp"
		fname = filedialog.asksaveasfilename(initialdir=self.dirname,#'/'.join(self.dirname.split("/")[:-1]),
																				 initialfile=fname+'.obj',
																				 defaultextension='.obj',
																				 title="Choose file to save MMSP",
																				 filetypes=[('obj files', '.obj'), ('All files', '*')])
		self.dirname = os.path.dirname(fname)
		self.mmsp_outfile_entry.delete(0, END)
		self.mmsp_outfile_entry.insert(END, fname)
		print("Selected output file for MMSP calculation:", fname)
	### END ###

	def calculate_mmsp(self):
		# Set seed for numpy random number generator
		seed = 123
		np.random.seed(seed)
		# Set fraction to select from the total number of vertices read from obj files
		frac = float(self.mmsp_percent_vertices_entry.get())/100.0
		#frac = 1.0
		print("Using fraction:", frac)
		
		#Read objfiles
		X = []
		y = []
		with open(self.mmsp_objfile1_entry.get(),'r') as f:
			for line in f:
				if line.startswith('v '):
					X.append([float(x) for x in line.strip().split()[1:]])
					y.append(0)
		obj1 = np.array(X)
		obj1_label = np.array(y)
		
		X = []
		y = []
		with open(self.mmsp_objfile2_entry.get(),'r') as f:
			for line in f:
				if line.startswith('v '):
					X.append([float(x) for x in line.strip().split()[1:]])
					y.append(1)
		obj2 = np.array(X)
		obj2_label = np.array(y)
		
		print("Object 1 shapes:", obj1.shape, obj1_label.shape)
		print("Object 2 shapes:", obj2.shape, obj2_label.shape)
		
		X = np.concatenate((obj1, obj2), axis=0)
		y = np.concatenate((obj1_label, obj2_label), axis=0)
		
		#X, y = shuffle(X, y)
		
		print("X shape:", X.shape)
		print("y shape:", y.shape)

		if frac == 1:
			idx = np.array(range(0,X.shape[0]))
			np.random.shuffle(idx)
		else:
			idx = np.random.choice(np.array(range(1,X.shape[0])),size=int(X.shape[0]*frac),replace=False)
			np.random.shuffle(idx)
			
		print("idx shape:", idx.shape)
		
		# Fit model
		#model = svm.SVC(kernel='linear', cache_size=200, tol=0.001, random_state=seed)
		model = svm.LinearSVC(random_state=seed)
		clf = model.fit(X[idx,:], y[idx])

		print(clf.coef_)
		print(clf.intercept_)

		plane_coef = clf.coef_
		plane_intercept = clf.intercept_

		#Find parametric equation of line joining centroids of two objects
		c1 = np.array([obj1[:,0].mean(),obj1[:,1].mean(),obj1[:,2].mean()])
		c2 = np.array([obj2[:,0].mean(),obj2[:,1].mean(),obj2[:,2].mean()])
		# Direction vector v = c2 - c1
		# Equation of line is (x,y,z) = (x1 + t*x_v, y1 + t*y_v, z1 + t*z_v)
		L = lambda c1,c2,t: [c1[0]+t*(c2[0]-c1[0]), c1[1]+t*(c2[1]-c1[1]), c1[2]+t*(c2[2]-c1[2])]
		print(c1)
		print(c2)
		
		#Intersection point of line and the plane
		[[a,b,c]] = clf.coef_
		[d] = clf.intercept_
		x1,y1,z1 = c1
		x2,y2,z2 = c2
		t = -(a*x1 + b*y1 + c*z1 + d)/(a*(x2-x1) + b*(y2-y1) + c*(z2-z1))
		#t = -(np.dot(clf.coef_,c1)+clf.intercept_)/np.dot(clf.coef_,c2)# Above equation can also be written like this.
		intersection = L(c1,c2,t)
		
		print(t)
		print(intersection)		

		verts, edges, faces = self.square(side=20,orientation=clf.coef_[0],location=intersection,verbose=True)

		# Write obj file representing the MMSP
		out = open(self.mmsp_outfile_entry.get(), 'w')
		for v in verts:
			out.write("v "+" ".join([str(x) for x in v])+"\n")
		for f in faces:
			out.write("f "+" ".join([str(x) for x in f])+"\n")
		out.close()

		# Write details of the MMSP
		fname = os.path.basename(self.mmsp_outfile_entry.get())
		dirname = os.path.dirname(self.mmsp_outfile_entry.get())
		if fname.endswith(".obj"):
			out = open(dirname + "/" + re.sub('.obj$','.txt',fname), 'w')
		else:
			out = open(dirname + "/" + fname+".txt", 'w')

		out.write("Object1:" + self.mmsp_objfile1_entry.get() + "\n")
		out.write("Object2:" + self.mmsp_objfile2_entry.get() + "\n\n")
		out.write("Number of vertices found in Object1: " + str(y[y == 0].shape[0]) + "\n")
		out.write("Number of vertices found in Object2: " + str(y[y == 1].shape[0]) + "\n\n")
		out.write("Total number of vertices found: " + str(y.shape[0]) + "\n\n")
		out.write("Fraction of vertices chosen: " + str(frac) + "\n\n")
		out.write("Number of vertices chosen from Object1: " + str(y[idx][y[idx] == 0].shape[0]) + "\n")
		out.write("Number of vertices chosen from Object2: " + str(y[idx][y[idx] == 1].shape[0]) + "\n\n")
		out.write("Total number of vertices used in MMSP calculation: " + str(y[idx].shape[0]) + "\n\n")
		out.write("Random seed: " + str(seed) + "\n\n")
		out.write("Centroid of Object1 (C1):\n" + str(c1) + "\n\n")
		out.write("Centroid of Object2 (C2):\n" + str(c2) + "\n\n")
		out.write("Distance between C1 and C2:\n" + str(np.linalg.norm(c2-c1))+"\n\n")
		out.write("Vector C1C2:\n" + str(c2-c1) + "\n\n")
		out.write("MMSP (Maximum Margin Separating Plane) calculated using Support Vector Machine (sklearn.svm.SVC):\n")
		out.write("Plane equation is of the form, Wx + b = 0:\n")
		out.write("Plane coefficients (W): " + str(clf.coef_) + "\n")
		out.write("Plane intercept (b): " + str(clf.intercept_) + "\n\n")
		out.write("Angle between vector C1C2 and MMSP (degrees):\n")
		out.write(str(np.degrees(np.arccos(np.dot(c2-c1,clf.coef_[0])/(np.linalg.norm(c2-c1)*np.linalg.norm(clf.coef_[0]))))) + "\n\n")
		out.close()

		print("DONE")


	def standard_square(self,side):
		a = side/2
		verts = [[a,0,0],[0,-a,0],[-a,0,0],[0,a,0]]
		edges = [[1,2],[2,3],[3,4],[4,1]]
		faces = [[1,2,3,4]]
		return(verts,edges,faces)

	def square(self,side=None,orientation=None,location=None,verbose=False):
		verts, edges, faces = self.standard_square(side)
		sqr = np.array(verts)

		orientation = np.array(orientation)
		location = np.array(location)
		p = orientation
		print(p)
		
		alpha = np.arccos(p[2]/np.linalg.norm(p))
		#print(p2, p1, l, p, math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)))
		#theta = np.arccos(p[1] / math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) )
		theta = np.arccos(p[1] / (math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) + 0.0000000000001) )

		rotvec_alpha = alpha * np.array([-1,0,0])
		rotvec_theta = theta * np.array([0,0,-1])

		rotation_alpha = Rotation.from_rotvec(rotvec_alpha)
		rotation_theta = Rotation.from_rotvec(rotvec_theta)
		rotation = rotation_theta * rotation_alpha	
		
		sqr_rotated = rotation.apply(sqr)
		sqr_rotated_translated = np.add(sqr_rotated, location)

		if verbose:
			print("side =", side)
			print("Square:")
			print("verts:")
			print(verts)
			print("edges:")
			print(edges)
			print("faces:")
			print(faces)
			print("orientation =", orientation)
			print("location =", location)
			print("alpha (around X-axis) =", alpha)
			print("theta (around Z-axis) =", theta)
			print("rotvec_alpha =", rotvec_alpha)
			print("rotvec_theta =", rotvec_theta)
			print("rotation matrix =\n", rotation.as_matrix())
			print("sqr_rotated:")
			print(sqr_rotated)
			print("\nsqr_rotated_translated:")
			print(sqr_rotated_translated)
		
		return(list(sqr_rotated_translated), edges, faces)


	def open_skeleton(self):
		self.skelfile =  filedialog.askopenfilename(initialdir=self.dirname,#'/'.join(self.dirname.split("/")[:-1]),
																								title="Select swc file",
																								filetypes=[("swc files","*.swc"),("All files","*.*")])
		#self.dirname = os.path.dirname(self.skelfile)
		with open(self.skelfile,'r') as f:
			swc = ''.join([line for line in f])
		try:
			skel = cloudvolume.Skeleton.from_swc(swc)
		except ValueError as err:
			print("Error: Could not read SWC file correctly. ValueError:",err)
			return(0)

		self.skels = {}
		self.skels[1] = skel
		self.skel_full = skel

		#print(type(self.skels))
		#print(len(self.skels))
		#print(self.skels)
		print("Skeleton read from file:",self.skelfile)
		#print(self.skel_full.radius)

		# Trial: Turn this on when findConnections() function is completed
		#self.findConnections()

	def save_skeleton(self, outdir=None):
		if not self.skel_full:#self.skels:	
			print("Skeleton not found")
			return(0)

		if outdir is None:
			outdir = self.dirname

		#self.skel = self.skels[1]
		swc = self.skel_full.to_swc(contributors="Harsh")
		#print(swc)

		###??? REMAINING: File name can contain which segments were used to build the skeleton.
		fname = outdir.split("/")[-1]+\
					  '-m'  +self.skel_widgets['mip_level']['entry'].get()+\
					  '_s'  +self.skel_widgets['scale']['entry'].get()+\
					  '_c'  +self.skel_widgets['const']['entry'].get()+\
					  '_pe' +self.skel_widgets['pdrf_exponent']['entry'].get()+\
					  '_ps' +self.skel_widgets['pdrf_scale']['entry'].get()+\
					  '_sdt'+self.skel_widgets['soma_detection_threshold']['entry'].get()+\
					  '_sat'+self.skel_widgets['soma_acceptance_threshold']['entry'].get()+\
					  '_sis'+self.skel_widgets['soma_invalidation_scale']['entry'].get()+\
					  '_sic'+self.skel_widgets['soma_invalidation_const']['entry'].get()+\
					  '_dt' +self.skel_widgets['dust_threshold']['entry'].get()+\
					  '_fbr'+str(int(self.skel_widgets_vars['fix_branching'].get()))+\
					  '_fbo'+str(int(self.skel_widgets_vars['fix_borders'].get()))

		self.skelfile = filedialog.asksaveasfilename(initialdir=outdir,#'/'.join(self.dirname.split("/")[:-1]),
																								 initialfile=fname+'.swc',
																								 defaultextension='.swc',
																								 title="Save skeleton in SWC format (also saves 3D model in Wavefront OBJ format)",
																								 filetypes=[('swc files', '.swc'),
																													 ('All files', '*')])
		if not self.skelfile:
			print("False")
			return(False)
		with open(self.skelfile,'w') as f:
			f.write(swc)

		print("Saved skeleton to file:",self.skelfile)

		# Write obj files for surface and skeleton
		#obj_skel_fname = "/".join(self.skelfile.split("/")[:-1]) + "/" + fname + '_skel.obj'
		#obj_skel_line_fname = "/".join(self.skelfile.split("/")[:-1]) + "/" + fname + '_line_skel.obj'
		obj_skel_fname = "/".join(self.skelfile.split("/")[:-1]) + "/" + ".".join(self.skelfile.split("/")[-1].split(".")[:-1]) + ".obj"
		obj_skel_line_fname = "/".join(self.skelfile.split("/")[:-1]) + "/" + ".".join(self.skelfile.split("/")[-1].split(".")[:-1]) + ".line.obj"

		(translate_x, translate_y, translate_z) = (int(x) for x in self.translate_entry.get().split(","))

		self.saveSkeletonObjFile(fname=obj_skel_fname, translate_x=translate_x, translate_y=translate_y, translate_z=translate_z)
		print("Saved skeleton object to file:",obj_skel_fname)

		#self.saveSkeletonObjFile_line(fname=obj_skel_line_fname, translate_x=translate_x, translate_y=translate_y, translate_z=translate_z)
		#print("Saved skeleton object to file:",obj_skel_fname)


	def save_surface(self):
		###??TEMPORARY
		#self.saveSkeletonObjFile(fname="temp_skel.obj")
		#self.saveSkeletonObjFile_line(fname="temp_skel_line.obj")
		#return(0)

		(translate_x, translate_y, translate_z) = (int(x) for x in self.translate_entry.get().split(","))

		# Write obj files for surface
		obj_surf_fname = self.dirname + "/" + self.merge_list_txt.get("1.0",END).strip().replace("\n","+") + '_surf.obj'
		if self.saveSurfaceObjFile(fname=obj_surf_fname, translate_x=translate_x, translate_y=translate_y, translate_z=translate_z, embed_skeleton=False):
			print("Saved surface object to file:",obj_surf_fname)
		path_obj_files=self.dirname + "/" 
		print(path_obj_files) 
		path_script=os.getcwd()+'/import_obj_blender.txt'
		print(path_script) 
		lines = ['import bpy','import os','import glob','model_dir = '+'"'+path_obj_files+'"','model_files = glob.glob(os.path.join(model_dir, "*.obj"))','for f in model_files:','    head, tail = os.path.split(f)','    collection_name = tail.replace(".obj", "")','    bpy.ops.import_scene.obj(filepath=f, axis_forward="Y",axis_up="Z")']

		with open(path_script, 'w') as f:
			for line in lines:
				f.write(line)
				f.write('\n')
		os.system('cmd /c "blender --python '+path_script)

	def saveSurfaceObjFile(self,fname=None, translate_x=0, translate_y=0, translate_z=0, embed_skeleton=False):
		### WRITE VERTICES AND EDGES FOR WAVEFRONT OBJ FILE
		### OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)
		### NOTE: ALL THESE CALCULATIONS WILL GIVE COORDINATES IN MICROMETERS. NOT IN PIXEL UNITS.
		
		"""
		if self.labels is None or len(self.labels) == 0:
			if self.merge_list_txt.get("1.0",END).strip() == "":
				print("WARNING: Segment selection not available. Checking if full surface is available.")
				if self.threeDmatrix is None or len(self.threeDmatrix) == 0:
					print("WARNING: Full surface not available. Not writing sufrace obj file.")
					return(0)
				else:
					print("WARNING: Writing obj file for surface of all segments. File size can be very large.")
					#Calculate surface triangulation using marching cubes
					verts, faces, normals, values = measure.marching_cubes_lewiner(self.threeDmatrix, 0, step_size=1)
			else:
				print("Writing obj file for surface of labels as in the merge list.")
				self.set_labels() # This creates self.labels with merged segments
				verts, faces, normals, values = measure.marching_cubes_lewiner(self.labels, 0, step_size=1)
				self.labels = None
		else:
			print("Writing obj file for surface of selected segments.")
			#Calculate surface triangulation using marching cubes
			verts, faces, normals, values = measure.marching_cubes_lewiner(self.labels, 0, step_size=1)
		"""
		
		if self.merge_list_txt.get("1.0",END).strip() == "":
			print("WARNING: Segment selection not available. Checking if full surface is available.")
			if self.threeDmatrix is None or len(self.threeDmatrix) == 0:
				print("WARNING: Full surface not available. Not writing sufrace obj file.")
				return(0)
			else:
				print("WARNING: Writing obj file for surface of all segments. File size can be very large.")
				#Calculate surface triangulation using marching cubes
				verts, faces, normals, values = measure.marching_cubes_lewiner(self.threeDmatrix, 0, step_size=1)
		else:
			print("Writing obj file for surface of labels as in the merge list.")
			self.set_labels() # This creates self.labels with merged segments
			verts, faces, normals, values = measure.marching_cubes_lewiner(self.labels, 0, step_size=1)
			self.labels = None
		

		if embed_skeleton:
			print(self.skel_full)
			components = self.skel_full.components()
			#print("Components:", type(components))
			#print(components)

		#print("self.labels:", np.unique(self.labels.shape), self.labels.shape)


		# Scale translation parameters according to the mip level.
		# translate_x = translate_x/(2^miplevel)
		print("Translations before:" ,translate_x,translate_y,translate_z)
		mip_level = self.skel_widgets['mip_level']['entry'].get()
		translate_x = translate_x / (2**int(mip_level))
		translate_y = translate_y / (2**int(mip_level))
		# ??? MAY BE DO NOT DO FOR transate_z
		#translate_z = translate_z / (2**int(mip_level))
		print("Translations after:" ,translate_x,translate_y,translate_z)

		# ???This scaling factor is to convert from nano meters to micrometers
		s = 0.001

		faces = faces+1
		objfile = open(fname, "w")
		objfile.write("mtllib materials.mtl\n")
		#Write vertices and vertex normals for surface
		for item in verts:
			#objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
			# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
			# -1 is for inverting z axis.
			objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((item[0]+translate_y)*self.mip_dict[mip_level][0]*s),
																						 '{:.6f}'.format((item[1]+translate_x)*self.mip_dict[mip_level][1]*s),
																						 '{:.6f}'.format((item[2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))

		#Surface smoothing inside blender works better than writing vertex normals to obj file. Hence not writing vertex normals.
		#for item in normals:
		#	objfile.write("vn {0} {1} {2}\n".format(item[0],item[1],item[2]))

		#Write vertices for skeleton
		if embed_skeleton:
			for skel in components:
				for item in skel.vertices:
					#objfile.write("v {0} {1} {2}\n".format(item[0]/32.0,item[1]/32.0,item[2]/30.0))
					# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
					# -1 is for inverting z axis.
					objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format(((item[0]/self.mip_dict[mip_level][0])+translate_y)*self.mip_dict[mip_level][0]*s),
																								 '{:.6f}'.format(((item[1]/self.mip_dict[mip_level][1])+translate_x)*self.mip_dict[mip_level][1]*s),
																								 '{:.6f}'.format(((item[2]/self.mip_dict[mip_level][2])+translate_z)*self.mip_dict[mip_level][2]*s*-1)))

		objfile.write("usemtl cellmembrane\n")

		#Write faces for surface
		for item in faces:
			#Surface smoothing inside blender works better than writing vertex normals to obj file. Hence not writing vertex normals.
			#objfile.write("f {0}//{0} {1}//{1} {2}//{2}\n".format(item[0],item[1],item[2]))
			objfile.write("f {0} {1} {2}\n".format(item[0],item[1],item[2]))
		v_num_offset = len(verts)+1
		
		#Write lines for skeleton
		if embed_skeleton:
			for skel in components:
				for item in skel.edges:
					objfile.write("l {0} {1}\n".format(item[0]+v_num_offset,item[1]+v_num_offset))

				v_num_offset += len(skel.vertices)

		objfile.close()
		return(1)

	
	def saveSkeletonObjFile_line(self, fname=None, translate_x=0, translate_y=0, translate_z=0):
		### THIS FUNCTION IS NOT BEING USED.
		### OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)
		### NOTE: ALL THESE CALCULATIONS WILL GIVE COORDINATES IN MICROMETERS. NOT IN PIXEL UNITS.

		print(self.skel_full)

		components = self.skel_full.components()
		print("Components:", type(components))
		print(components)

		# Scale translation parameters according to the mip level.
		# translate_x = translate_x/(2^miplevel)
		mip_level = self.skel_widgets['mip_level']['entry'].get()
		translate_x = translate_x / (2**int(mip_level))
		translate_y = translate_y / (2**int(mip_level))
		# ??? MAY BE DO NOT DO FOR transate_z
		#translate_z = translate_z / (2**int(mip_level))

		# ???This scaling factor is to convert from nano meters to micrometers
		s = 0.001

		objfile = open(fname,"w")
		
		v_num_offset = 1#len(verts)+1

		i = 1
		for skel in components:
			skel = skel.downsample(int(self.downsample_entry.get()))
			objfile.write("#Skeleton "+str(i)+"\n")

			#print("skel.edges:", type(skel.edges))
			#lines = skel.edges+1

			#print(skel.vertices)
			for item in skel.vertices:
				#objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
				#print("vert", item)
				#print("vert", np.array([item[0]/32.0,item[1]/32.0,item[2]/30.0]))
				#objfile.write("v {0} {1} {2}\n".format(item[0]/32.0,item[1]/32.0,item[2]/30.0))
				# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
				# -1 is for inverting z axis.
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format(((item[0]/self.mip_dict[mip_level][0])+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format(((item[1]/self.mip_dict[mip_level][1])+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format(((item[2]/self.mip_dict[mip_level][2])+translate_z)*self.mip_dict[mip_level][2]*s*-1)))


			#print(skel.edges)
			for item in skel.edges:
				#print("edge", item)
				objfile.write("l {0} {1}\n".format(item[0]+v_num_offset,item[1]+v_num_offset))

			v_num_offset += len(skel.vertices)
			i += 1

		objfile.close()


	def transform_coordinates(self, coord=None, mip_level=None, translate_x=0, translate_y=0, translate_z=0, scale=1.0):
		# mip_level is the input mip_level at which the coord data is provided.
		# Translation parameters are always in pixel units at mip0. They are typically obtained when the segmentation images were exported from VAST.
		mip_dict = {
		"none": [1.,1.,1.],
		"0": [4.,4.,30.],
		"1": [8.,8.,30.],
		"2": [16.,16.,30.],
		"3": [32.,32.,30.],
		"4": [64.,64.,30.],
		"5": [128.,128.,30.],
		"6": [256.,256.,30.],
		"7": [512.,512.,30.]
		}

		# Scale translation parameters according to the mip level.
		# translate_x = translate_x/(2^miplevel)
		#mip_level = 3
		#translate_x = translate_x / (2**int(mip_level))
		#translate_y = translate_y / (2**int(mip_level))
		# ??? MAY BE DO NOT DO FOR transate_z
		#translate_z = translate_z / (2**int(mip_level))

		coord_transformed = []
		for p in coord:
			
			p_transformed = np.zeros(p.shape)
			
			p_transformed[0] = (p[0]+translate_x)*mip_dict[mip_level][0]*scale
			p_transformed[1] = (p[1]+translate_y)*mip_dict[mip_level][1]*scale
			p_transformed[2] = (p[2]+translate_z)*mip_dict[mip_level][2]*scale*-1

			coord_transformed.append(p_transformed)

		return(coord_transformed)


	def get_obj(self, obj_name='default_obj', verts=None, edges=None, faces=None, v_num_offset=0, material_class='default'):

		obj = "o " + str(obj_name) + "\n"
		
		for item in verts:
			# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
			# -1 is for inverting z axis.is_close_to_OOB
			#obj_lines += "v {0} {1} {2}\n".format('{:.6f}'.format(((item[0]/mip_dict[mip_level][0])+translate_y)*mip_dict[mip_level][0]*scale),
			#																			 '{:.6f}'.format(((item[1]/mip_dict[mip_level][1])+translate_x)*mip_dict[mip_level][1]*scale),
			#																			 '{:.6f}'.format(((item[2]/mip_dict[mip_level][2])+translate_z)*mip_dict[mip_level][2]*scale*-1))

			#obj_lines += "v {0} {1} {2}\n".format('{:.6f}'.format((item[0]+translate_y)*mip_dict[mip_level][0]*scale),
			#																			'{:.6f}'.format((item[1]+translate_x)*mip_dict[mip_level][1]*scale),
			#																			'{:.6f}'.format((item[2]+translate_z)*mip_dict[mip_level][2]*scale*-1))

			obj += "v {0} {1} {2}\n".format('{:.6f}'.format(item[0]),
																						'{:.6f}'.format(item[1]),
																						'{:.6f}'.format(item[2]))

		if material_class.strip() == '':
			material_class = 'default'
		obj += "usemtl " + material_class + "\n"
		
		for item in faces:
			obj += "f " + " ".join([str(x+v_num_offset) for x in item]) + "\n"
		v_num_offset += len(verts)

		return(obj, v_num_offset)

	def nm_to_pixels(self, coord=None, target_mip_level=None):
		mip_dict = {
		"none": [1.,1.,1.],
		"0": [4.,4.,30.],
		"1": [8.,8.,30.],
		"2": [16.,16.,30.],
		"3": [32.,32.,30.],
		"4": [64.,64.,30.],
		"5": [128.,128.,30.],
		"6": [256.,256.,30.],
		"7": [512.,512.,30.]
		}
		
		#print(target_mip_level)
		return(np.array([coord[0]/mip_dict[target_mip_level][0], coord[1]/mip_dict[target_mip_level][1], coord[2]/mip_dict[target_mip_level][2]]))

	def saveSkeletonObjFile(self,fname=None, translate_x=0, translate_y=0, translate_z=0):
		# Writing skeleton to obj file: One cylinder per edge
		# OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)
		### NOTE: ALL THESE CALCULATIONS WILL GIVE COORDINATES IN MICROMETERS. NOT IN PIXEL UNITS.

		#####components = self.skel_full.components()
		#print("Components:", type(components))
		#print(components)

		radius_min = min(self.skel_full.radius)
		radius_range = max(self.skel_full.radius) - radius_min
		if radius_range == 0:
			radius_range = 1

		# Scale translation parameters according to the mip level.
		# translate_x = translate_x/(2^miplevel)
		# For P7 dataset, this will give translation parameters in nanometers
		mip_level = self.skel_widgets['mip_level']['entry'].get()
		translate_x = translate_x / (2**int(mip_level))
		translate_y = translate_y / (2**int(mip_level))
		# ??? MAY BE DO NOT DO FOR transate_z
		#translate_z = translate_z / (2**int(mip_level))

		# ???This scaling factor is to convert from nano meters to micrometers
		s = 0.001

		skeleton_mtl_filename = "skeleton_materials.mtl"
		objfile = open(fname,"w")
		objfile.write("mtllib " + skeleton_mtl_filename + "\n")
		
		v_num_offset = 0
		#####component_cnt = 0
		#####for skel in components:
		if self.downsample_entry.get().isnumeric():
			skel = self.skel_full.downsample(int(self.downsample_entry.get()))
		else:
			skel = self.skel_full
		
		edge_cnt = 0
		node_cnt = 0
		for edge in skel.edges:
			#print("Cylinder along", edge[0], "and", edge[1], "::", skel.vertices[edge[0]]/np.array([32.0,32.0,30.0]), skel.vertices[edge[1]]/np.array([32.0,32.0,30.0]))

			#print(skel.vertices[edge[0]], type(skel.vertices[edge[0]]))
			#cyl_verts, cyl_edges, cyl_faces = self.cylinder(0.4,#0.07,#0.5,
			#																								skel.vertices[edge[0]]/np.array([32.0,32.0,30.0]),
			#																								skel.vertices[edge[1]]/np.array([32.0,32.0,30.0]), verbose=False)

			coord = [ self.nm_to_pixels(coord=skel.vertices[edge[0]], target_mip_level=mip_level),
								self.nm_to_pixels(coord=skel.vertices[edge[1]], target_mip_level=mip_level)]
			coord = self.transform_coordinates(coord=coord, mip_level=mip_level, translate_x=translate_y, translate_y=translate_x, translate_z=translate_z, scale=s)

			cyl_verts, cyl_edges, cyl_faces = self.cylinder(float(self.cylinder_radius_entry.get()),#8.0,#16.0,#0.07,#0.5,
																											coord[0],
																											coord[1], verbose=False)

			#####obj, v_num_offset = self.get_obj(obj_name='skel-'+str(component_cnt)+'_edge-'+str(edge_cnt), verts=cyl_verts, faces=cyl_faces, v_num_offset=v_num_offset, material_class='skeleton_edge')
			obj, v_num_offset = self.get_obj(obj_name='edge-'+str(edge_cnt), verts=cyl_verts, faces=cyl_faces, v_num_offset=v_num_offset, material_class='skeleton_edge')
			objfile.write(obj)
			edge_cnt += 1

		"""
		print("\nskel_full")
		print(self.skel_full.downsample(10))
		print("\nskel_full.vertices")
		print(self.skel_full.downsample(10).vertices)
		print("\nskel")
		print(skel)
		print("\nskel.vertices")
		print(skel.vertices)
		print()
		print("type(skel.vertices)", type(skel.vertices))
		print(len(skel.vertices))
		"""
		
		for vert in skel.vertices:
			#sph_verts, sph_faces = self.sphere(1.2,#0.2,#1.5,
			#																	 vert/np.array([32.0,32.0,30.0]))
			
			coord = [ self.nm_to_pixels(coord=vert, target_mip_level=mip_level)]
			coord = self.transform_coordinates(coord=coord, mip_level=mip_level, translate_x=translate_y, translate_y=translate_x, translate_z=translate_z, scale=s)

			sph_verts, sph_faces = self.sphere(float(self.sphere_radius_entry.get()),#25.0,#75.0,#0.2,#1.5,
																				 coord[0])

			#Write line to change material
			material_class = "radius" + str(math.floor(10*(skel.radius[node_cnt]-radius_min)/radius_range))

			#####obj, v_num_offset = self.get_obj(obj_name='skel-'+str(component_cnt)+'_node-'+str(node_cnt), verts=sph_verts, faces=sph_faces, v_num_offset=v_num_offset, material_class=material_class)
			obj, v_num_offset = self.get_obj(obj_name='node-'+str(node_cnt), verts=sph_verts, faces=sph_faces, v_num_offset=v_num_offset, material_class=material_class)
			objfile.write(obj)
			node_cnt += 1

		#####component_cnt += 1
			
		objfile.close()
		
		self.write_mtl(mtl_filename="/".join(fname.split("/")[:-1]) + "/" + skeleton_mtl_filename)
		

	def saveSkeletonObjFile_asSingleObject(self,fname=None, translate_x=0, translate_y=0, translate_z=0):
		# Writing skeleton to obj file: One cylinder per edge
		# OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)
		### NOTE: ALL THESE CALCULATIONS WILL GIVE COORDINATES IN MICROMETERS. NOT IN PIXEL UNITS.

		components = self.skel_full.components()
		#print("Components:", type(components))
		#print(components)

		radius_min = min(self.skel_full.radius)
		radius_range = max(self.skel_full.radius) - radius_min
		if radius_range == 0:
			radius_range = 1

		# Scale translation parameters according to the mip level.
		# translate_x = translate_x/(2^miplevel)
		mip_level = self.skel_widgets['mip_level']['entry'].get()
		translate_x = translate_x / (2**int(mip_level))
		translate_y = translate_y / (2**int(mip_level))
		# ??? MAY BE DO NOT DO FOR transate_z
		#translate_z = translate_z / (2**int(mip_level))

		# ???This scaling factor is to convert from nano meters to micrometers
		s = 0.001

		v_num_offset = 0
		v_lines = ""
		f_lines = ""
		for skel in components:
			skel = skel.downsample(int(self.downsample_entry.get()))

			f_lines += "usemtl skeleton\n"
			for edge in skel.edges:
				#print("Cylinder along", edge[0], "and", edge[1], "::", skel.vertices[edge[0]]/np.array([32.0,32.0,30.0]), skel.vertices[edge[1]]/np.array([32.0,32.0,30.0]))

				#print(skel.vertices[edge[0]], type(skel.vertices[edge[0]]))
				#cyl_verts, cyl_edges, cyl_faces = self.cylinder(0.4,#0.07,#0.5,
				#																								skel.vertices[edge[0]]/np.array([32.0,32.0,30.0]),
				#																								skel.vertices[edge[1]]/np.array([32.0,32.0,30.0]), verbose=False)
				cyl_verts, cyl_edges, cyl_faces = self.cylinder(float(self.cylinder_radius_entry.get()),#8.0,#16.0,#0.07,#0.5,
																												skel.vertices[edge[0]],
																												skel.vertices[edge[1]], verbose=False)
				
				for item in cyl_verts:
					#objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
					#v_lines += "v {0} {1} {2}\n".format(item[0],item[1],item[2])
					#v_lines += "v {0} {1} {2}\n".format(item[0]+translate_x,item[1]+translate_y,item[2]+translate_z)
					# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
					# -1 is for inverting z axis.
					v_lines += "v {0} {1} {2}\n".format('{:.6f}'.format(((item[0]/self.mip_dict[mip_level][0])+translate_y)*self.mip_dict[mip_level][0]*s),
																							'{:.6f}'.format(((item[1]/self.mip_dict[mip_level][1])+translate_x)*self.mip_dict[mip_level][1]*s),
																							'{:.6f}'.format(((item[2]/self.mip_dict[mip_level][2])+translate_z)*self.mip_dict[mip_level][2]*s*-1))


				for item in cyl_faces:
					#objfile.write("f " + " ".join([str(x+v_num_offset) for x in item]) + "\n")
					f_lines += "f " + " ".join([str(x+v_num_offset) for x in item]) + "\n"
				v_num_offset += len(cyl_verts)
			
			cnt = 0
			for vert in skel.vertices:
				#sph_verts, sph_faces = self.sphere(1.2,#0.2,#1.5,
				#																	 vert/np.array([32.0,32.0,30.0]))
				sph_verts, sph_faces = self.sphere(float(self.sphere_radius_entry.get()),#25.0,#75.0,#0.2,#1.5,
																					 vert)

				for item in sph_verts:
					#objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
					#v_lines += "v {0} {1} {2}\n".format(item[0],item[1],item[2])
					#v_lines += "v {0} {1} {2}\n".format(item[0]+translate_x,item[1]+translate_y,item[2]+translate_z)
					# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
					# -1 is for inverting z axis.
					v_lines += "v {0} {1} {2}\n".format('{:.6f}'.format(((item[0]/self.mip_dict[mip_level][0])+translate_y)*self.mip_dict[mip_level][0]*s),
																							'{:.6f}'.format(((item[1]/self.mip_dict[mip_level][1])+translate_x)*self.mip_dict[mip_level][1]*s),
																							'{:.6f}'.format(((item[2]/self.mip_dict[mip_level][2])+translate_z)*self.mip_dict[mip_level][2]*s*-1))

				#Write line to change material
				f_lines += "usemtl radius" + str(math.floor(10*(skel.radius[cnt]-radius_min)/radius_range)) + "\n"
				for item in sph_faces:
					#objfile.write("f " + " ".join([str(x+v_num_offset) for x in item]) + "\n")
					f_lines += "f " + " ".join([str(x+v_num_offset) for x in item]) + "\n"
				v_num_offset += len(sph_verts)
				cnt += 1

		objfile = open(fname,"w")
		objfile.write("mtllib materials.mtl\n"+v_lines + f_lines)
		objfile.close()


	def write_mtl(self, mtl_filename='materials.mtl'):
		print("Writing material file-", mtl_filename)
		
		mtl_str = """newmtl cellmembrane
Ka  0.1985  0.0000  0.0000
Kd  0.5921  0.0167  0.0000
Ks  0.5973  0.2083  0.2083
illum 2
Ns 100.2235

newmtl skeleton
Ka  0.0394  0.0394  0.3300
Kd  0.8420  0.8420  0.8420
illum 1
Tr 0.4300

newmtl radius0
Ka  0.0394  0.0394  0.3300
Kd  0.0000  0.0000  1.0000
illum 1
Tr 0.4300

newmtl radius1
Ka  0.0394  0.0394  0.3300
Kd  0.0000  0.4431  1.0000
illum 1
Tr 0.4300

newmtl radius2
Ka  0.0394  0.0394  0.3300
Kd  0.0000  0.8863  1.0000
illum 1
Tr 0.4300

newmtl radius3
Ka  0.0394  0.0394  0.3300
Kd  0.0000  1.0000  0.6627
illum 1
Tr 0.4300

newmtl radius4
Ka  0.0394  0.0394  0.3300
Kd  0.0000  1.0000  0.2196
illum 1
Tr 0.4300

newmtl radius5
Ka  0.0394  0.0394  0.3300
Kd  0.2196  1.0000  0.0000
illum 1
Tr 0.4300

newmtl radius6
Ka  0.0394  0.0394  0.3300
Kd  0.6667  1.0000  0.0000
illum 1
Tr 0.4300

newmtl radius7
Ka  0.0394  0.0394  0.3300
Kd  1.0000  0.8863  0.0000
illum 1
Tr 0.4300

newmtl radius8
Ka  0.0394  0.0394  0.3300
Kd  1.0000  0.4431  0.0000
illum 1
Tr 0.4300

newmtl radius9
Ka  0.0394  0.0394  0.3300
Kd  1.0000  0.0000  0.0000
illum 1
Tr 0.4300

"""
		with open(mtl_filename,"w") as o:
			o.write(mtl_str)

			
	def standard_cylinder_4(self,r,l,verbose=False):
		verts = [	[ r, 0, 0],
							[ 0, r, 0],
							[-r, 0, 0],
							[ 0,-r, 0],
							[ r, 0, l],
							[ 0, r, l],
							[-r, 0, l],
							[ 0,-r, l]]

		edges = [ [1,2],
							[2,3],
							[3,4],
							[4,1],
							[1,5],
							[2,6],
							[3,7],
							[4,8],
							[5,6],
							[6,7],
							[7,8],
							[8,5]]

		faces = [ [1,2,3,4],
							[1,2,6,5],
							[2,3,7,6],
							[3,4,8,7],
							[4,1,5,8],
							[5,6,7,8]]

		if verbose:
			print("OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)")
			for vert in verts:
				print("v " + " ".join(str(v) for v in vert))
			for face in faces:
				print("f " + " ".join(str(f) for f in face))
			print("")

		return(verts,edges,faces)

	def standard_cylinder_6(self,r,l,verbose=False):
		rcos60 = r * 0.5
		rsin60 = r * 0.866
		
		verts = [ [      r,      0, 0],
							[ rcos60, rsin60, 0],
							[-rcos60, rsin60, 0],
							[     -r,      0, 0],
							[-rcos60,-rsin60, 0],
							[ rcos60,-rsin60, 0],
							[      r,      0, l],
							[ rcos60, rsin60, l],
							[-rcos60, rsin60, l],
							[     -r,      0, l],
							[-rcos60,-rsin60, l],
							[ rcos60,-rsin60, l]]

		edges = [ [1,2],
							[2,3],
							[3,4],
							[4,5],
							[5,6],
							[6,1],
							[1,7],
							[2,8],
							[3,9],
							[4,10],
							[5,11],
							[6,12],
							[7,8],
							[8,9],
							[9,10],
							[10,11],
							[11,12],
							[12,7]]

		faces = [ [1,2,3,4,5,6],
							[1,2,8,7],
							[2,3,9,8],
							[3,4,10,9],
							[4,5,11,10],
							[5,6,12,11],
							[6,1,7,12],
							[7,8,9,10,11,12]]

		if verbose:
			print("OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)")
			for vert in verts:
				print("v " + " ".join(str(v) for v in vert))
			for face in faces:
				print("f " + " ".join(str(f) for f in face))
			print("")

		return(verts,edges,faces)

	def standard_cylinder_12(self,r,l,verbose=False):
		rcos30 = r * 0.866
		rsin30 = r * 0.5
		rcos60 = r * 0.5
		rsin60 = r * 0.866
		
		verts = [ [      r,      0, 0],
							[ rcos30, rsin30, 0],
							[ rcos60, rsin60, 0],
							[       0,     r, 0],
							[-rcos60, rsin60, 0],
							[-rcos30, rsin30, 0],
							[     -r,      0, 0],
							[-rcos30,-rsin30, 0],
							[-rcos60,-rsin60, 0],
							[      0,     -r, 0],
							[ rcos60,-rsin60, 0],
							[ rcos30,-rsin30, 0],
							[      r,      0, l],
							[ rcos30, rsin30, l],
							[ rcos60, rsin60, l],
							[       0,     r, l],
							[-rcos60, rsin60, l],
							[-rcos30, rsin30, l],
							[     -r,      0, l],
							[-rcos30,-rsin30, l],
							[-rcos60,-rsin60, l],
							[      0,     -r, l],
							[ rcos60,-rsin60, l],
							[ rcos30,-rsin30, l]]

		edges = [ [1,2], [2,3], [3,4], [4,5], [5,6], [6,7], [7,8], [8,9], [9,10], [10,11], [11,12], [12,1],
							[1,13], [2,14], [3,15], [4,16], [5,17], [6,18], [7,19], [8,20], [9,21], [10,22], [11,23], [12,24],
							[13,14], [14,15], [15,16], [16,17], [17,18], [18,19], [19,20], [20,21], [21,22], [22,23], [23,24]]

		faces = [ [1,2,3,4,5,6,7,8,9,10,11,12],
							[1,2,14,13],
							[2,3,15,14],
							[3,4,16,15],
							[4,5,17,16],
							[5,6,18,17],
							[6,7,19,18],
							[7,8,20,19],
							[8,9,21,20],
							[9,10,22,21],
							[10,11,23,22],
							[11,12,24,23],
							[12,1,13,24],							
							[13,14,15,16,17,18,19,20,21,22,23,24]]

		if verbose:
			print("OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)")
			for vert in verts:
				print("v " + " ".join(str(v) for v in vert))
			for face in faces:
				print("f " + " ".join(str(f) for f in face))
			print("")

		return(verts,edges,faces)


	def standard_sphere_24(self,rsph,verbose=False):
		sin0 = 0.0
		sin15 = 0.259
		sin30 = 0.5
		sin45 = 0.707
		sin60 = 0.866
		sin75 = 0.966
		sin90 = 1.0

		cos0= 1.0
		cos15 = 0.966
		cos30 = 0.866
		cos45 = 0.707
		cos60 = 0.5
		cos75 = 0.259
		cos90 = 0.0
		
		verts_slice = np.array([[ 1, 0, 0], [ cos15, sin15, 0], [ cos30, sin30, 0],	[ cos45, sin45, 0], [ cos60, sin60, 0],	[ cos75, sin75, 0],
														[ 0, 1, 0], [-cos75, sin75, 0], [-cos60, sin60, 0], [-cos45, sin45, 0], [-cos30, sin30, 0], [-cos15, sin15, 0],
														[-1, 0, 0],	[-cos15,-sin15, 0], [-cos30,-sin30, 0],	[-cos45,-sin45, 0], [-cos60,-sin60, 0],	[-cos75,-sin75, 0],
														[ 0,-1, 0], [ cos75,-sin75, 0], [ cos60,-sin60, 0], [ cos45,-sin45, 0], [ cos30,-sin30, 0], [ cos15,-sin15, 0]])

		verts = []
		i = 1
		for (z,r) in [( rsph*sin90,rsph*cos90), ( rsph*sin75,rsph*cos75), ( rsph*sin60,rsph*cos60), ( rsph*sin45,rsph*cos45), ( rsph*sin30,rsph*cos30), ( rsph*sin15,rsph*cos15),
									(rsph*sin0,rsph*cos0),
									(-rsph*sin15,rsph*cos15), (-rsph*sin30,rsph*cos30), (-rsph*sin45,rsph*cos45), (-rsph*sin60,rsph*cos60), (-rsph*sin75,rsph*cos75), (-rsph*sin90,rsph*cos90)]:
			
			#print(z, r)
			if r == 0.0:
				i += 1
				verts += list(np.array([[0,0,z]]))
			else:
				for v in verts_slice:
					i += 1
				verts += list((np.array([0,0,z]) + r*verts_slice))

		faces = [ [1,2,3], [1,3,4], [1,4,5], [1,5,6], [1,6,7], [1,7,8], [1,8,9], [1,9,10], [1,10,11], [1,11,12], [1,12,13], [1,13,14], [1,14,15], [1,15,16], [1,16,17], [1,17,18], [1,18,19], [1,19,20], [1,20,21], [1,21,22], [1,22,23], [1,23,24], [1,24,25], [1,25,2], 
							[2,26,27,3], [3,27,28,4], [4,28,29,5], [5,29,30,6], [6,30,31,7], [7,31,32,8], [8,32,33,9], [9,33,34,10], [10,34,35,11], [11,35,36,12], [12,36,37,13], [13,37,38,14], [14,38,39,15], [15,39,40,16], [16,40,41,17], [17,41,42,18], [18,42,43,19], [19,43,44,20], [20,44,45,21], [21,45,46,22], [22,46,47,23], [23,47,48,24], [24,48,49,25], [25,49,26,2], 
							[26,50,51,27], [27,51,52,28], [28,52,53,29], [29,53,54,30], [30,54,55,31], [31,55,56,32], [32,56,57,33], [33,57,58,34], [34,58,59,35], [35,59,60,36], [36,60,61,37], [37,61,62,38], [38,62,63,39], [39,63,64,40], [40,64,65,41], [41,65,66,42], [42,66,67,43], [43,67,68,44], [44,68,69,45], [45,69,70,46], [46,70,71,47], [47,71,72,48], [48,72,73,49], [49,73,50,26], 
							[50,74,75,51], [51,75,76,52], [52,76,77,53], [53,77,78,54], [54,78,79,55], [55,79,80,56], [56,80,81,57], [57,81,82,58], [58,82,83,59], [59,83,84,60], [60,84,85,61], [61,85,86,62], [62,86,87,63], [63,87,88,64], [64,88,89,65], [65,89,90,66], [66,90,91,67], [67,91,92,68], [68,92,93,69], [69,93,94,70], [70,94,95,71], [71,95,96,72], [72,96,97,73], [73,97,74,50], 
							[74,98,99,75], [75,99,100,76], [76,100,101,77], [77,101,102,78], [78,102,103,79], [79,103,104,80], [80,104,105,81], [81,105,106,82], [82,106,107,83], [83,107,108,84], [84,108,109,85], [85,109,110,86], [86,110,111,87], [87,111,112,88], [88,112,113,89], [89,113,114,90], [90,114,115,91], [91,115,116,92], [92,116,117,93], [93,117,118,94], [94,118,119,95], [95,119,120,96], [96,120,121,97], [97,121,98,74], 
							[98,122,123,99], [99,123,124,100], [100,124,125,101], [101,125,126,102], [102,126,127,103], [103,127,128,104], [104,128,129,105], [105,129,130,106], [106,130,131,107], [107,131,132,108], [108,132,133,109], [109,133,134,110], [110,134,135,111], [111,135,136,112], [112,136,137,113], [113,137,138,114], [114,138,139,115], [115,139,140,116], [116,140,141,117], [117,141,142,118], [118,142,143,119], [119,143,144,120], [120,144,145,121], [121,145,122,98], 
							[122,146,147,123], [123,147,148,124], [124,148,149,125], [125,149,150,126], [126,150,151,127], [127,151,152,128], [128,152,153,129], [129,153,154,130], [130,154,155,131], [131,155,156,132], [132,156,157,133], [133,157,158,134], [134,158,159,135], [135,159,160,136], [136,160,161,137], [137,161,162,138], [138,162,163,139], [139,163,164,140], [140,164,165,141], [141,165,166,142], [142,166,167,143], [143,167,168,144], [144,168,169,145], [145,169,146,122], 
							[146,170,171,147], [147,171,172,148], [148,172,173,149], [149,173,174,150], [150,174,175,151], [151,175,176,152], [152,176,177,153], [153,177,178,154], [154,178,179,155], [155,179,180,156], [156,180,181,157], [157,181,182,158], [158,182,183,159], [159,183,184,160], [160,184,185,161], [161,185,186,162], [162,186,187,163], [163,187,188,164], [164,188,189,165], [165,189,190,166], [166,190,191,167], [167,191,192,168], [168,192,193,169], [169,193,170,146], 
							[170,194,195,171], [171,195,196,172], [172,196,197,173], [173,197,198,174], [174,198,199,175], [175,199,200,176], [176,200,201,177], [177,201,202,178], [178,202,203,179], [179,203,204,180], [180,204,205,181], [181,205,206,182], [182,206,207,183], [183,207,208,184], [184,208,209,185], [185,209,210,186], [186,210,211,187], [187,211,212,188], [188,212,213,189], [189,213,214,190], [190,214,215,191], [191,215,216,192], [192,216,217,193], [193,217,194,170], 
							[194,218,219,195], [195,219,220,196], [196,220,221,197], [197,221,222,198], [198,222,223,199], [199,223,224,200], [200,224,225,201], [201,225,226,202], [202,226,227,203], [203,227,228,204], [204,228,229,205], [205,229,230,206], [206,230,231,207], [207,231,232,208], [208,232,233,209], [209,233,234,210], [210,234,235,211], [211,235,236,212], [212,236,237,213], [213,237,238,214], [214,238,239,215], [215,239,240,216], [216,240,241,217], [217,241,218,194], 
							[218,242,243,219], [219,243,244,220], [220,244,245,221], [221,245,246,222], [222,246,247,223], [223,247,248,224], [224,248,249,225], [225,249,250,226], [226,250,251,227], [227,251,252,228], [228,252,253,229], [229,253,254,230], [230,254,255,231], [231,255,256,232], [232,256,257,233], [233,257,258,234], [234,258,259,235], [235,259,260,236], [236,260,261,237], [237,261,262,238], [238,262,263,239], [239,263,264,240], [240,264,265,241], [241,265,242,218], 
							[242,266,243], [243,266,244], [244,266,245], [245,266,246], [246,266,247], [247,266,248], [248,266,249], [249,266,250], [250,266,251], [251,266,252], [252,266,253], [253,266,254], [254,266,255], [255,266,256], [256,266,257], [257,266,258], [258,266,259], [259,266,260], [260,266,261], [261,266,262], [262,266,263], [263,266,264], [264,266,265], [265,266,242] ]

		if verbose:
			print("OBJ file: (Importing in Blender: Select transformation Y Forward, Z up)")
			for vert in verts:
				print("v " + " ".join(str(v) for v in vert))
			for face in faces:
				print("f " + " ".join(str(f) for f in face))
			print("")

		return(verts,faces)


	def sphere(self,r,p1,verbose=False):
		p1 = np.array(p1)
		verts, faces = self.standard_sphere_24(r)
		sph = np.array(verts)
		sph_translated = np.add(sph, p1)
		return(list(sph_translated), faces)


	def cylinder(self,r,p1,p2,verbose=False):
		p1 = np.array(p1)
		p2 = np.array(p2)

		l = np.linalg.norm(p2-p1)

		verts, edges, faces = self.standard_cylinder_12(r,l)
		cyl = np.array(verts)

		init_vec = np.array([0,0,1])

		p = p2-p1

		alpha = np.arccos(p[2]/np.linalg.norm(p))
		#print(p2, p1, l, p, math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)))
		#theta = np.arccos(p[1] / math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) )
		theta = np.arccos(p[1] / (math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) + 0.0000000000001) )

		rotvec_alpha = alpha * np.array([-1,0,0])
		rotvec_theta = theta * np.array([0,0,-1])

		rotation_alpha = Rotation.from_rotvec(rotvec_alpha)
		rotation_theta = Rotation.from_rotvec(rotvec_theta)
		rotation = rotation_theta * rotation_alpha	
		
		cyl_rotated = rotation.apply(cyl)
		cyl_rotated_translated = np.add(cyl_rotated, p1)

		if verbose:
			print("l =", l)
			print("Cylinder:")
			print("verts:")
			print(verts)
			print("edges:")
			print(edges)
			print("faces:")
			print(faces)
			print("init_vec =", init_vec)
			print("p1 =", p1)
			print("p2 =", p2)
			print("p =", p)
			print("alpha (around X-axis) =", alpha)
			print("theta (around Z-axis) =", theta)
			print("rotvec_alpha =", rotvec_alpha)
			print("rotvec_theta =", rotvec_theta)
			print("rotation matrix =\n", rotation.as_matrix())
			print("cyl_rotated:")
			print(cyl_rotated)
			print("\ncyl_rotated_translated:")
			print(cyl_rotated_translated)
		
		return(list(cyl_rotated_translated), edges, faces)


	def findCellProtrusions(self):

		###??? This is a trial. If successful, it will be useful to automate tnt-finding to some extent.
		# Use sequential Erosion-Dialation to identify thin regions.
		# Number of Erosion and Dialation iterations depend upon the thickness of the cell protrusions to be identified.
		#(80+107)+(81+108)+109

		print("Finding protrusions and soma")
		
		self.protr_analysis_status_lbl.configure(text="Finding protrusions...")
		self.protr_analysis_status_lbl.update_idletasks()

		# Set lables matrix using the selected labels
		self.protr_analysis_status_lbl.configure(text="Setting labels...")
		self.protr_analysis_status_lbl.update_idletasks()
		if bool(self.use_previously_set_labels.get()):
			print("Using previously set labels")
		else:
			self.set_labels(final_erosion=False)
		
		if self.labels is None:
			self.protr_analysis_status_lbl.configure(text="Labels not set.")
			print("Labels not set.")
			return(0)
		
		# Get 1/0 image (1 = True, 0 = False)
		img = (self.labels != 0)*1

		# Erode
		self.protr_analysis_status_lbl.configure(text="Performing erosion...")
		self.protr_analysis_status_lbl.update_idletasks()
		img_eroded = scipy.ndimage.binary_erosion(img, iterations=int(self.protr_erosioniter_entry.get()))#, structure=np.ones((3,3,3)))
		print(np.unique(img_eroded))
		
		#Dilate. Dilation needs to be done for more number of erosion iterations.
		#For usual mip3 images, number of dilation iter = 40 * number of erosion iter was found to be working well.
		self.protr_analysis_status_lbl.configure(text="Performing dilation...")
		self.protr_analysis_status_lbl.update_idletasks()
		img_dilated = scipy.ndimage.binary_dilation(img_eroded, iterations=int(self.protr_dilationiter_entry.get()))#, structure=np.ones((3,3,3)))
		print(np.unique(img_dilated))
		
		# Clear unwanted variables
		del(img_eroded)

		# Generate protrusions and soma images
		self.protr_analysis_status_lbl.configure(text="Generating protrusions and soma...")
		self.protr_analysis_status_lbl.update_idletasks()

		# Protrusions = original image - eroded+dilated image
		protrusions = ((img-img_dilated)==1)*1
		print("protrusions dtype:", type(protrusions[0,0,0]), np.unique(protrusions))

		# Clear unwanted variables
		del(img_dilated)
		
		# Soma = original image - protrusions
		soma = img - protrusions
		print("protrusions dtype:", type(soma[0,0,0]), np.unique(soma))

		# Clear unwanted variables
		del(img)

		# Get list of selected labels
		selected_labels = []
		merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())
		for m in merge_list:
			selected_labels += [x for x in re.split('\+|\(|\)|\[|\]', m) if x.isdigit()]
		selected_labels = "+".join(selected_labels)

		# MAKE OUTPUT DIRECTORIES
		outdir = self.dirname + "/protrusions-and-soma"
		try:
			os.makedirs(outdir)
		except OSError as exc:
			print("Directory already exists. Existing files will be overwritten. Target directory:", outdir)
			#return(0)

		# Save surface obj files
		self.protr_analysis_status_lbl.configure(text="Saving obj files...")
		self.protr_analysis_status_lbl.update_idletasks()
		fname_protrusions = outdir+'/protrusions_selected-labels-'+selected_labels+'.obj'
		fname_soma = outdir+'/soma_selected-labels-'+selected_labels+'.obj'
		#obj_cellprotrusions_surf_fname = self.dirname + "/" + self.merge_list_txt.get("1.0",END).strip().replace("\n","+") + '_cellprotrusions_surf.obj'

		(translate_x, translate_y, translate_z) = (int(x) for x in self.translate_entry.get().split(","))

		if self.saveProtrusionsSomaSurfaceObjFile(protrusions=protrusions, soma=soma, fname_protrusions=fname_protrusions, fname_soma=fname_soma,
																							translate_x=translate_x, translate_y=translate_y, translate_z=translate_z):
			print("Saved protrusions to file:",fname_protrusions)
			print("Saved soma to file:",fname_soma)

		# Clear unwanted variables
		del(protrusions)
		del(soma)

		self.protr_analysis_status_lbl.configure(text="Finished")
		

	def saveProtrusionsSomaSurfaceObjFile(self, protrusions=None, soma=None, fname_protrusions=None, fname_soma=None, translate_x=0, translate_y=0, translate_z=0):		
		
		def writeObj(mat,fname=None,translate_x=0,translate_y=0,translate_z=0):
			verts, faces, normals, values = measure.marching_cubes_lewiner(mat, 0, step_size=1)

			# Scale translation parameters according to the mip level.
			# translate_x = translate_x/(2^miplevel)
			print("Translations before:" ,translate_x,translate_y,translate_z)
			mip_level = self.protr_miplevel_entry.get()
			translate_x = translate_x / (2**int(mip_level))
			translate_y = translate_y / (2**int(mip_level))
			# ??? MAY BE DO NOT DO FOR transate_z
			#translate_z = translate_z / (2**int(mip_level))
			print("Translations after:" ,translate_x,translate_y,translate_z)

			# ???This scaling factor is to convert from nano meters to micrometers
			s = 0.001

			faces = faces+1
			objfile = open(fname, "w")
			objfile.write("mtllib materials.mtl\n")
			#Write vertices and vertex normals for surface
			for item in verts:
				#objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
				# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
				# -1 is for inverting z axis.
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((item[0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((item[1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((item[2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))

			#Surface smoothing inside blender works better than writing vertex normals to obj file. Hence not writing vertex normals.
			#for item in normals:
			#	objfile.write("vn {0} {1} {2}\n".format(item[0],item[1],item[2]))

			objfile.write("usemtl cellmembrane\n")

			#Write faces for surface
			for item in faces:
				#Surface smoothing inside blender works better than writing vertex normals to obj file. Hence not writing vertex normals.
				#objfile.write("f {0}//{0} {1}//{1} {2}//{2}\n".format(item[0],item[1],item[2]))
				objfile.write("f {0} {1} {2}\n".format(item[0],item[1],item[2]))
			
			objfile.close()
		
		
		writeObj(protrusions,fname=fname_protrusions,translate_x=translate_x,translate_y=translate_y,translate_z=translate_z)
		writeObj(soma,fname=fname_soma,translate_x=translate_x,translate_y=translate_y,translate_z=translate_z)
		#writeObj(img_eroded,fname=self.dirname+"/eroded.obj",translate_x=translate_x,translate_y=translate_y,translate_z=translate_z)
		#writeObj(img_dilated,fname=self.dirname+"/dilated.obj",translate_x=translate_x,translate_y=translate_y,translate_z=translate_z)
		

		#self.labels = None
		return(1)


	def reset_skel_params(self):
		for srno, param in sorted([(v['srno'], k) for k,v in self.kimimaro_param_standard.items()]):
			print("Resetting value of widget for kimimaro parameter", srno, "-", param)
			if self.kimimaro_param_standard[param]['type'] == 'numeric':
				self.skel_widgets[param]['entry'].delete(0, END)
				self.skel_widgets[param]['entry'].insert(END, self.kimimaro_param_standard[param]['default'])
			
			elif self.kimimaro_param_standard[param]['type'] == 'boolean':
				self.skel_widgets_vars[param].set(self.kimimaro_param_standard[param]['default'])

			else:
				pass

		for srno, param in sorted([(v['srno'], k) for k,v in self.kimimaro_param_advanced.items()]):
			print("Resetting value of widget for kimimaro parameter", srno, "-", param)
			if self.kimimaro_param_advanced[param]['type'] == 'numeric':
				self.skel_widgets[param]['entry'].delete(0, END)
				self.skel_widgets[param]['entry'].insert(END, self.kimimaro_param_advanced[param]['default'])
			
			elif self.kimimaro_param_advanced[param]['type'] == 'boolean':
				self.skel_widgets_vars[param].set(self.kimimaro_param_advanced[param]['default'])

			else:
				pass


	def save_images(self):
		self.images_outdir = self.images_outdir
		self.anis = int(self.images_anis_entry.get())
		print("Saving images to",self.images_outdir)
		print("Applying anisotropy factor of",self.anis)

		"""
		###MAKE OUTPUT DIRECTORY
		try:
			os.mkdir(self.images_outdir)
		except OSError as exc: 
			if exc.errno == errno.EEXIST and os.path.isdir(self.images_outdir):
				print("Directory",self.images_outdir,"exists. Please specify another directory.")
				return(0)
		"""
		
		print(len(self.threeDmatrix))
		print(self.threeDmatrix.shape)

		#"""
		# Save original images
		cnt = 0
		for k in range(0,self.threeDmatrix.shape[2]):
			img = Image.fromarray(self.threeDmatrix[:,:,k])
			for i in range(0,self.anis):
				img.save(self.images_outdir+"/img"+str(cnt)+"_"+str(i)+".png")
			cnt += 1
		#"""


		"""
		# Save images preserving colors
		cnt = 0
		for mat in self.matrices:
			#img = ImageTk.PhotoImage(image=Image.fromarray(mat)#.resize((new_width,new_height)))
			img = Image.fromarray(mat)
			for i in range(0,self.anis):
				img.save(self.images_outdir+"/img"+str(cnt)+"_"+str(i)+".png")
			cnt += 1
		"""

		"""
		# Save images as single gray color
		cnt = 0
		for mat in self.matrices:
			#img = ImageTk.PhotoImage(image=Image.fromarray(mat)#.resize((new_width,new_height)))
			mat[mat != 0] = 200
			img = Image.fromarray(mat)
			for i in range(0,self.anis):
				img.save(self.images_outdir+"/img"+str(cnt)+"_"+str(i)+".png")
			cnt += 1
		"""

		print("Saved",cnt*self.anis,"images.")


	def update_image(self,event):
		#print(">>>", self.image_slider.get())
		if self.matrices != []:
			#print(self.image_num_cur)
			#if self.image_num_cur < len(self.matrices)-1:
			#	self.image_num_cur += 1
			self.image_num_cur = self.image_slider.get()
			self.show_image()
		else:
			print("No data loaded.")


	def image_next(self):
		if self.matrices != []:
			#print(self.image_num_cur)
			if self.image_num_cur < len(self.matrices)-1:
				self.image_num_cur += 1
			self.image_slider.set(self.image_num_cur)
			#self.show_image()
		else:
			print("No data loaded.")

	def image_prev(self):
		if self.matrices != []:
			#print(self.image_num_cur)
			if self.image_num_cur > 0:
				self.image_num_cur -= 1
			self.image_slider.set(self.image_num_cur)
			#self.show_image()
		else:
			print("No data loaded.")


	def image_next_key(self,event):
		if self.matrices != []:
			# Identical to function image_next, except for second argument 'event'.
			#print(self.image_num_cur)
			if self.image_num_cur < len(self.matrices)-1:
				self.image_num_cur += 1
			self.image_slider.set(self.image_num_cur)
			#self.show_image()
		else:
			print("No data loaded.")

	def image_prev_key(self,event):
		if self.matrices != []:
			# Identical to function image_prev, except for second argument 'event'.
			#print(self.image_num_cur)
			if self.image_num_cur > 0:
				self.image_num_cur -= 1
			self.image_slider.set(self.image_num_cur)
			#self.show_image()
		else:
			print("No data loaded.")

	def show_image(self):
		rc = self.image_canvas_width/self.image_canvas_height
		ri = self.image_width/self.image_height

		if rc < ri:
			#Fit width
			new_width = self.image_canvas_width
			new_height = int((self.image_height * self.image_canvas_width)/self.image_width)
		else:
			#Fit height
			new_height = self.image_canvas_height
			new_width = int((self.image_width * self.image_canvas_height)/self.image_height)

		#print("New w,h:",new_width,new_height)
		self.img =  ImageTk.PhotoImage(image=Image.fromarray(self.matrices[self.image_num_cur]).resize((new_width,new_height)))
		#self.image_canvas.create_image((0,0), anchor=NW, image=self.img)
		self.image_canvas.create_image((self.image_canvas_width/2,self.image_canvas_height/2), anchor=CENTER, image=self.img)

		#self.image_num_lbl_text = 
		#self.image_num_lbl.configure(text=str(self.image_num_cur))
		print("Showing image", self.image_num_cur)


	def choose_segment_color(self,btn_id):
		label = self.uniq_labels[1:][btn_id]
		print(btn_id, label, self.colormapHex[label])
		rgbcolor, hexcolor = colorchooser.askcolor(initialcolor=self.colormapHex[label], title="Choose color")
		print(list(rgbcolor), hexcolor)

		original_rgbcolor = self.colormap[label]
		print(original_rgbcolor)

		#Update colormaps
		self.colormap[label] = list(rgbcolor)
		self.colormapHex[label] = hexcolor
		print(self.colormap)
		print(self.colormapHex)

		#Update colors
		self.segment_color_btns[btn_id].configure(bg=self.colormapHex[label], activebackground='#'+''.join([hex(x)[2:] if x<=255 else "eb" for x in [int(self.colormapHex[label][i:i+2],base=16)+20 for i in range(1,6,2)]]))

		i = 0
		for i in range(0,len(self.matrices)):
			print(i, self.matrices[i].shape)
			for ch in [0,1,2]:
				#print(im[:,:,ch].shape)
				self.matrices[i][:,:,ch][self.matrices_original[i][:,:,ch] == label] = self.colormap[label][ch]
				#self.matrices[i][:,:,ch][self.threeDmatrix[:,:,i] == label] = self.colormap[label][ch]
			i += 1

		self.show_image()


	def merge_segments(self):
		#This function is for merging selected segments
		i = 0
		merge_seg = []
		for var in self.segment_vars:
			if var.get():
				l = self.uniq_labels[1:][i]
				print("Adding segment", l, "to merge list.")
				merge_seg.append(l)
			i += 1

		if merge_seg == []:
			return(0)

		merge_list = re.split('\+|\n|,', self.merge_list_txt.get("1.0",END))
		print(merge_list)
		for s in merge_seg:
			if str(s) in merge_list:
				print("Error: Segment",s,"already present in the merge list. Please refine selection.")
				return(0)

		self.merge_list_txt.insert(END,'+'.join([str(x) for x in merge_seg])+'\n')

		for var in self.segment_vars:
			var.set(0)


	def browse_images_outdir(self):
		#Get directory name that contains all images
		self.images_outdir = filedialog.askdirectory(parent=root, initialdir='./', title='Select output directory')
		#self.images_outdir_entry.delete(0, END)
		#self.images_outdir_entry.insert(END, self.images_outdir)

		#"""
		dname = self.images_outdir
		if len(dname) > 50:
			arr = dname.split("/")
			#print(arr)
			dname = "/".join(arr[0:3])+"/.../"+arr[-1]
		self.images_outdir_lbl.configure(text=dname)
		print("Selected output directory:",dname)
		#"""
	### END ###


	def browse_dir(self):
		#Get directory name that contains all images
		self.dirname = filedialog.askdirectory()
		
		"""
		# This is not useful because some of the background colors cannot be adjusted easily.
		answer = tk.messagebox.askokcancel(title="Confirmation", message="Load images from this folder?", icon=tk.messagebox.WARNING)
		if answer:
			print("YES", answer)
		else:
			print("NO", answer)
		"""

		# Using custom message box
		ok = showDialog(self)

		if not ok:
			print("Directory not selected.")
			return(0)
				
		self.dirname_show = self.dirname
		if len(self.dirname) > 50:
			arr = self.dirname.split("/")
			#print(arr)
			self.dirname_show = "/".join(arr[0:3])+"/.../"+arr[-1]
		self.selecteddir_lbl.configure(text=self.dirname_show)
		print("Selected directory:",self.dirname)

		self.load_data()

	### END ###


	def browse_file(self):
		self.filename =  filedialog.askopenfilename(initialdir = "./",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))


	def view_skeleton(self):
		### Deprecated
		if not self.skel_full:#self.skels:
			print("Skeleton not found")
			return(0)

		#??? CAUTION Start new array. May be not necessary? Check if needs to be removed.
		self.selectedNodes = []


		#??? CAUTION: Change downsampling to required value
		#self.skel = self.skels[1]
		if self.downsample_entry.get().isnumeric() and int(self.downsample_entry.get()) != 0:
			#self.skel = self.skels[1].downsample(int(self.downsample_entry.get()))#10)
			self.skel = self.skel_full.downsample(int(self.downsample_entry.get()))#10)
		else:
			self.skel = self.skel_full


		"""
		# This is an old usage where skeleton.py file from the CloudVolume package was edited to return the Axes3D object with skeleton drawn on it.
		ax,f = self.skel.get_view(
			 draw_vertices=True,
			 draw_edges=True,
			 units='nm',
			 color_by=self.colorby_var.get()
			 #color_by='radius', # aka 'r' or 'components' aka 'c'
			 #color_by='components', # aka 'r' or 'components' aka 'c'
		)
		print(type(ax), type(f))
		"""
		
		# Set skeleton drawing parameters
		draw_vertices=True
		draw_edges=True
		units='nm'
		color_by=self.colorby_var.get()
		#color_by='radius', # aka 'r' or 'components' aka 'c'
		#color_by='components', # aka 'r' or 'components' aka 'c'

		# Draw skeleton
		################################################################################################

		RADII_KEYWORDS = ('radius', 'radii', 'r')
		COMPONENT_KEYWORDS = ('component', 'components', 'c')

		newTk = Tk()
		fig = plt.figure()#figsize=(10,10))
		canvas = FigureCanvasTkAgg(fig, newTk)
		ax = Axes3D(fig)
		ax.set_xlabel(units)
		ax.set_ylabel(units)
		ax.set_zlabel(units)

		# Set plot axes equal. Matplotlib doesn't have an easier way to
		# do this for 3d plots.
		X = self.skel.vertices[:,0]
		Y = self.skel.vertices[:,1]
		Z = self.skel.vertices[:,2]

		max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0

		mid_x = (X.max()+X.min()) * 0.5
		mid_y = (Y.max()+Y.min()) * 0.5
		mid_z = (Z.max()+Z.min()) * 0.5
		ax.set_xlim(mid_x - max_range, mid_x + max_range)
		ax.set_ylim(mid_y - max_range, mid_y + max_range)
		ax.set_zlim(mid_z - max_range, mid_z + max_range)
		### END EQUALIZATION CODE ###

		component_colors = ['k', 'deeppink', 'dodgerblue', 'mediumaquamarine', 'gold' ]

		def draw_component(i, skel):
			component_color = component_colors[ i % len(component_colors) ]

			if draw_vertices:
				xs = skel.vertices[:,0]
				ys = skel.vertices[:,1]
				zs = skel.vertices[:,2]

				if color_by in RADII_KEYWORDS:
					colmap = cm.ScalarMappable(cmap=cm.get_cmap('rainbow'))
					colmap.set_array(skel.radii)

					normed_radii = skel.radii / np.max(skel.radii)
					yg = ax.scatter(xs, ys, zs, c=cm.rainbow(normed_radii), marker='o', picker=True)
					cbar = fig.colorbar(colmap)
					cbar.set_label('radius (' + units + ')', rotation=270)
				elif color_by in COMPONENT_KEYWORDS:
					yg = ax.scatter(xs, ys, zs, color=component_color, marker='.', picker=True)
				else:
					yg = ax.scatter(xs, ys, zs, color='k', marker='.', picker=True)

			if draw_edges:
				for e1, e2 in skel.edges:
					pt1, pt2 = skel.vertices[e1], skel.vertices[e2]
					ax.plot(	
						[ pt1[0], pt2[0] ],
						[ pt1[1], pt2[1] ],
						zs=[ pt1[2], pt2[2] ],
						color=(component_color if not draw_vertices else 'silver'),
						linewidth=1,
					)

		if color_by in COMPONENT_KEYWORDS:
			for i, skel in enumerate(self.skel.components()):
				draw_component(i, skel)
		else:
			draw_component(0, self.skel)

		#END Draw skeleton
		################################################################################################
		
		
		#datacursor()# Use this for testing the data cursor

		canvas.draw()

		Axes3D.mouse_init(ax)

		toolbar = NavigationToolbar2Tk(canvas, newTk)
		toolbar.update()

		canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
		canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

		#f.canvas.mpl_connect('pick_event', self.onpick)

		def distance(point, event):
			"""Return distance between mouse position and given data point

			Args:
				point (np.array): np.array of shape (3,), with x,y,z in data coords
				event (MouseEvent): mouse event (which contains mouse position in .x and .xdata)
			Returns:
				distance (np.float64): distance (in screen coords) between mouse pos and data point
			"""
			assert point.shape == (3,), "distance: point.shape is wrong: %s, must be (3,)" % point.shape

			# Project 3d data space to 2d data space
			x2, y2, _ = proj3d.proj_transform(point[0], point[1], point[2], plt.gca().get_proj())
			# Convert 2d data space to 2d screen space
			x3, y3 = ax.transData.transform((x2, y2))

			return np.sqrt ((x3 - event.x)**2 + (y3 - event.y)**2)


		def calcClosestDatapoint(X, event):
			""""Calculate which data point is closest to the mouse position.

			Args:
				X (np.array) - array of points, of shape (numPoints, 3)
				event (MouseEvent) - mouse event (containing mouse position)
			Returns:
				smallestIndex (int) - the index (into the array of points X) of the element closest to the mouse position
			"""
			distances = [distance (X[i, 0:3], event) for i in range(X.shape[0])]
			return np.argmin(distances)


		def annotatePlot(X, index):
			"""Create popover label in 3d chart

			Args:
				X (np.array) - array of points, of shape (numPoints, 3)
				index (int) - index (into points array X) of item which should be printed
			Returns:
				None
			"""
			# If we have previously displayed another label, remove it first
			if hasattr(annotatePlot, 'label'):
				annotatePlot.label.remove()
			# Get data point from array of points X, at position index
			x2, y2,_ = proj3d.proj_transform(X[index, 0], X[index, 1], X[index, 2], ax.get_proj())
			annotatePlot.label = plt.annotate("Index: "+str(index)+"\nRadius: "+str(self.skel.radius[index]),
																				xy = (x2, y2), xytext = (-20,20), textcoords = 'offset points', ha = 'right', va = 'bottom',
																				bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
																				arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
			fig.canvas.draw()


		def onMouseMotion(event):
			"""Event that is triggered when mouse is moved. Shows text annotation over data point closest to mouse."""
			closestIndex = calcClosestDatapoint(self.skel.vertices, event)
			annotatePlot(self.skel.vertices, closestIndex)


		fig.canvas.mpl_connect('motion_notify_event', onMouseMotion)  # on mouse motion
		#fig.canvas.mpl_connect('button_press_event', onMouseButtonPress)  # on mouse button press



	def draw_skeleton(self):
		# Get skeletons
		#self.calc_skeleton()

		if not self.skel_full:#self.skels:
			print("Skeleton not found")
			return(0)

		#??? CAUTION Start new array. May be not necessary? Check if needs to be removed.
		self.selectedNodes = []


		# Create a skeleton object with user defined downsampling.
		# This downsampled skeleton is also used later by skeleton analysis functions.
		#??? CAUTION: Change downsampling to required value
		#self.skel = self.skels[1]
		if self.downsample_entry.get().isnumeric() and int(self.downsample_entry.get()) != 0:
			#self.skel = self.skels[1].downsample(int(self.downsample_entry.get()))#10)
			self.skel = self.skel_full.downsample(int(self.downsample_entry.get()))#10)
		else:
			self.skel = self.skel_full


		# Create a skeleton graph. This is used by skeleton analysis functions later.
		self.skel_graph = nx.Graph()
		self.skel_graph.add_nodes_from(list(range(0,len(self.skel.vertices))))
		self.skel_graph.add_edges_from([tuple(x) for x in self.skel.edges])

		print(self.skel_graph.nodes())
		print(self.skel_graph.edges())


		"""
		print(type(self.skel))
		print("")
		print(self.skels)
		print(len(self.skels))
		print("")
		print(self.skel.vertices[0], self.skel.radius[0], self.skel.components())
		print("---")
		print(len(self.skel.vertices), len(self.skel.radius))
		"""

		print("---")
		print(type(self.skel), type(self.skels))
		print(self.skels)
		print("---")
		for i in self.skels:
			print(self.skels[i])
			print("#")
			print(self.skels[i].components())
			print("#")
			for skel in self.skels[i].components():
				print(type(skel))
				print(skel)
				print("------------------")

		print("===")

		#for i in range(0,len(self.skel.vertices)):
		#	print(i, self.skel.vertices[i], self.skel.radius[i], self.skel.vertex_types[i])

		"""
		# This is an old usage where skeleton.py file from the CloudVolume package was edited to return the Axes3D object with skeleton drawn on it.
		ax,f = self.skel.get_view(
			 draw_vertices=True,
			 draw_edges=True,
			 units='nm',
			 color_by=self.colorby_var.get()
			 #color_by='radius', # aka 'r' or 'components' aka 'c'
			 #color_by='components', # aka 'r' or 'components' aka 'c'
		)
		print(type(ax), type(f))
		"""
		
		# Set skeleton drawing parameters
		draw_vertices=True
		draw_edges=True
		units='nm'
		color_by=self.colorby_var.get()
		#color_by='radius', # aka 'r' or 'components' aka 'c'
		#color_by='components', # aka 'r' or 'components' aka 'c'

		# Draw skeleton
		################################################################################################

		RADII_KEYWORDS = ('radius', 'radii', 'r')
		COMPONENT_KEYWORDS = ('component', 'components', 'c')

		newTk = Tk()
		fig = plt.figure()#figsize=(10,10))
		canvas = FigureCanvasTkAgg(fig, newTk)
		ax = Axes3D(fig)
		ax.set_xlabel(units)
		ax.set_ylabel(units)
		ax.set_zlabel(units)

		# Set plot axes equal. Matplotlib doesn't have an easier way to
		# do this for 3d plots.
		X = self.skel.vertices[:,0]
		Y = self.skel.vertices[:,1]
		Z = self.skel.vertices[:,2]

		max_range = np.array([X.max()-X.min(), Y.max()-Y.min(), Z.max()-Z.min()]).max() / 2.0

		mid_x = (X.max()+X.min()) * 0.5
		mid_y = (Y.max()+Y.min()) * 0.5
		mid_z = (Z.max()+Z.min()) * 0.5
		ax.set_xlim(mid_x - max_range, mid_x + max_range)
		ax.set_ylim(mid_y - max_range, mid_y + max_range)
		ax.set_zlim(mid_z - max_range, mid_z + max_range)
		### END EQUALIZATION CODE ###

		component_colors = ['k', 'deeppink', 'dodgerblue', 'mediumaquamarine', 'gold' ]

		def draw_component(i, skel):
			component_color = component_colors[ i % len(component_colors) ]

			if draw_vertices:
				xs = skel.vertices[:,0]
				ys = skel.vertices[:,1]
				zs = skel.vertices[:,2]

				if color_by in RADII_KEYWORDS:
					colmap = cm.ScalarMappable(cmap=cm.get_cmap('rainbow'))
					colmap.set_array(skel.radii)

					normed_radii = skel.radii / np.max(skel.radii)
					yg = ax.scatter(xs, ys, zs, c=cm.rainbow(normed_radii), marker='o', picker=True)
					cbar = fig.colorbar(colmap)
					cbar.set_label('radius (' + units + ')', rotation=270)
				elif color_by in COMPONENT_KEYWORDS:
					yg = ax.scatter(xs, ys, zs, color=component_color, marker='.', picker=True)
				else:
					yg = ax.scatter(xs, ys, zs, color='k', marker='.', picker=True)

			if draw_edges:
				for e1, e2 in skel.edges:
					pt1, pt2 = skel.vertices[e1], skel.vertices[e2]
					ax.plot(	
						[ pt1[0], pt2[0] ],
						[ pt1[1], pt2[1] ],
						zs=[ pt1[2], pt2[2] ],
						color=(component_color if not draw_vertices else 'silver'),
						linewidth=1,
					)

		if color_by in COMPONENT_KEYWORDS:
			for i, skel in enumerate(self.skel.components()):
				draw_component(i, self.skel)
		else:
			draw_component(0, self.skel)

		#END Draw skeleton
		################################################################################################
		
		
		#datacursor()# Use this for testing the data cursor

		canvas.draw()

		Axes3D.mouse_init(ax)

		toolbar = NavigationToolbar2Tk(canvas, newTk)
		toolbar.update()

		canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
		canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

		#f.canvas.mpl_connect('pick_event', self.onpick)


		def distance(point, event):
			"""Return distance between mouse position and given data point

			Args:
				point (np.array): np.array of shape (3,), with x,y,z in data coords
				event (MouseEvent): mouse event (which contains mouse position in .x and .xdata)
			Returns:
				distance (np.float64): distance (in screen coords) between mouse pos and data point
			"""
			assert point.shape == (3,), "distance: point.shape is wrong: %s, must be (3,)" % point.shape

			# Project 3d data space to 2d data space
			x2, y2, _ = proj3d.proj_transform(point[0], point[1], point[2], plt.gca().get_proj())
			# Convert 2d data space to 2d screen space
			x3, y3 = ax.transData.transform((x2, y2))

			return np.sqrt ((x3 - event.x)**2 + (y3 - event.y)**2)


		def calcClosestDatapoint(X, event):
			""""Calculate which data point is closest to the mouse position.

			Args:
				X (np.array) - array of points, of shape (numPoints, 3)
				event (MouseEvent) - mouse event (containing mouse position)
			Returns:
				smallestIndex (int) - the index (into the array of points X) of the element closest to the mouse position
			"""
			distances = [distance (X[i, 0:3], event) for i in range(X.shape[0])]
			return np.argmin(distances)


		def annotatePlot(X, index):
			"""Create popover label in 3d chart

			Args:
				X (np.array) - array of points, of shape (numPoints, 3)
				index (int) - index (into points array X) of item which should be printed
			Returns:
				None
			"""
			# If we have previously displayed another label, remove it first
			if hasattr(annotatePlot, 'label'):
				annotatePlot.label.remove()
			# Get data point from array of points X, at position index
			x2, y2,_ = proj3d.proj_transform(X[index, 0], X[index, 1], X[index, 2], ax.get_proj())
			annotatePlot.label = plt.annotate("Index: "+str(index)+"\nRadius: "+str(self.skel.radius[index]),
																				xy = (x2, y2), xytext = (-20,20), textcoords = 'offset points', ha = 'right', va = 'bottom',
																				bbox = dict(boxstyle = 'round,pad=0.5', fc = 'yellow', alpha = 0.5),
																				arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'))
			fig.canvas.draw()


		def onMouseMotion(event):
			"""Event that is triggered when mouse is moved. Shows text annotation over data point closest to mouse."""
			closestIndex = calcClosestDatapoint(self.skel.vertices, event)
			annotatePlot(self.skel.vertices, closestIndex)

		def onMouseButtonPress(event):
			
			if len(self.selectedNodes) == 2:
				self.selectedNodes = []
				
			# Set two nodes as selected nodes and return.
			if event.button == 2:
				#Setting the picker function:
				closestIndex = calcClosestDatapoint(self.skel.vertices, event)
				print("*", closestIndex, self.skel.radius[closestIndex])
				
				if len(self.selectedNodes) < 2:
					self.selectedNodes.append(closestIndex)
				else:
					print(self.selectedNodes)
    
				if len(self.selectedNodes) == 2:
					print("Downsample:",self.downsample_entry.get())
					print("Selected Nodes:", self.selectedNodes)
					print("Now choose an action for these two nodes in the main CellWalker window.")
 
		fig.canvas.mpl_connect('motion_notify_event', onMouseMotion)  # on mouse motion
		fig.canvas.mpl_connect('button_press_event', onMouseButtonPress)  # on mouse button press


	def length_analysis(self):
		# This is for Thea. Calculates distance between two selected nodes. Shortest path and the path length.
		try:
			###MAKE OUTPUT DIRECTORIES
			##############outdir = self.dirname + "/cross-sections_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2])
			#name_suffix = "curvature-analysis_downsample-" + self.downsample_entry.get() + "_nodes-" + str(self.selectedNodes[0]) + "-" + str(self.selectedNodes[1])
			#outdir = self.dirname + "/" + name_suffix
			# Delete directory and its contents if exists
			#if os.path.exists(outdir):
			#	try:
			#		shutil.rmtree(outdir)
			#		print("Warning: Cross-sections will be overwritten.")
			#	except OSError as e:
			#		print("Could not remove directory tree: %s : %s" % (outdir, e.strerror))
			#try:
			#	os.makedirs(outdir)
			#except OSError as exc:
				#if exc.errno == errno.EEXIST and os.path.isdir(self.images_outdir):
			#	print("Directory already exists. Existing files will be overwritten. Target directory:", outdir)
				#return(0)

			print("\n\n------------------------------------------------")
			print("Downsample:",self.downsample_entry.get())
			print("------------------------------------------------")

			#print("Selected nodes:")
			#print(self.selectedNodes[0], ','.join([str(x) for x in self.skel.vertices[self.selectedNodes[0]]]))
			#print(self.selectedNodes[1], ','.join([str(x) for x in self.skel.vertices[self.selectedNodes[1]]]))
			#print("------------------------------------------------")
			
			d = np.linalg.norm(self.skel.vertices[self.selectedNodes[0]]-self.skel.vertices[self.selectedNodes[1]])
			print("Straight Length =", d)
			print("------------------------------------------------")

			#from SkeletonRadiusPlot import SkeletonRadiusPlot
			shortest_path = nx.dijkstra_path(self.skel_graph,self.selectedNodes[0],self.selectedNodes[1])
			
			#print("Path",cnt)
			path_length = 0
			for node_id in range(0,len(shortest_path)-1):
				path_length += np.linalg.norm(self.skel.vertices[shortest_path[node_id]]-self.skel.vertices[shortest_path[node_id+1]])
			print("Path length =",path_length)
			print("------------------------------------------------")
			print("Shortest path:\n")
			print("Node\tCoordinates\tRadius")
			for node in shortest_path:
				print(str(node)+"\t"+','.join([str(x) for x in self.skel.vertices[node]])+"\t"+str(self.skel.radius[node]))
			print("------------------------------------------------\n\n")

		except:
			print("Exception occurred during linear fitting")
			self.selectedNodes = []
			print(sys.exc_info()[0])
			raise

	def curvature_analysis(self):
	# Curvature calculation
	# Linear fit- This is for calculating linear fit for the nodes on the shortest path between selected nodes
	# A good linear fit will tell that it is most likely a skeleton of a non-curved object.
	# Menger curvature- Calculates average Menger curvature
		try:
			###MAKE OUTPUT DIRECTORIES
			##############outdir = self.dirname + "/cross-sections_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2])
			name_suffix = "curvature-analysis_downsample-" + self.downsample_entry.get() + "_nodes-" + str(self.selectedNodes[0]) + "-" + str(self.selectedNodes[1])
			try:
				outdir = os.path.dirname(self.skelfile)
			except:
				outdir = self.dirname
			outdir = filedialog.askdirectory(initialdir=outdir, title="Select a folder for curvature analysis")

			# Delete directory and its contents if exists
			#if os.path.exists(outdir):
			#	try:
			#		shutil.rmtree(outdir)
			#		print("Warning: Cross-sections will be overwritten.")
			#	except OSError as e:
			#		print("Could not remove directory tree: %s : %s" % (outdir, e.strerror))
			try:
				os.makedirs(outdir)
			except OSError as exc:
				#if exc.errno == errno.EEXIST and os.path.isdir(self.images_outdir):
				print("Directory already exists. Existing files will be overwritten. Target directory:", outdir)
				#return(0)

			#from SkeletonRadiusPlot import SkeletonRadiusPlot
			shortest_path = nx.dijkstra_path(self.skel_graph,self.selectedNodes[0],self.selectedNodes[1])
			
			#print("Path",cnt)
			print("Nodes:", self.selectedNodes[0], "-", self.selectedNodes[1])
			print("Downsample:",self.downsample_entry.get())
			#path_length = 0
			#for node_id in range(0,len(shortest_path)-1):
			#	path_length += np.linalg.norm(self.skel.vertices[shortest_path[node_id]]-self.skel.vertices[shortest_path[node_id+1]])
			#print("Path length:",path_length)
			#print("Shortest path and radii along the path:")
			#print("Vertex", ' '.join([str(x) for x in shortest_path]))
			#print("Radius", ' '.join([str(self.skel.radius[i]) for i in shortest_path]))


			# Calculate metrics to infer straightness of the skeleton of the connection
			
			# Choose points on the skeleton of the connection
			#print(skel.vertices.shape)
			#print(len(shortest_path))
			#print(shortest_path)
			points = self.skel.vertices[shortest_path]

			# Linear least square regression.
			# NOTE: This is not an appropriate way because in 3D, linear least square regression becomes a planar regression.
			#       We do not want to minimize the error in Z. Instead we want to minimize the orthogonal distance from the line.
			#       This can be done by Orthogonal Distance Regression (ODR). See below.
			X = points[:,:2]
			y = points[:,2]
			#print(shortest_path)
			#print(points)
			print("Linear regression:")
			print("X, y shapes:", X.shape, y.shape)
			reg = LinearRegression().fit(X, y)
			rsquared = reg.score(X,y)
			print("R-squared =", rsquared)
			
			
			# Orthogonal Distance Regression (ODR)
			pts = Points(points)
			line_fit = Line.best_fit(pts)
			distance = np.array([line_fit.distance_point(p)**2 for p in pts])
			sum_distance = np.sum(distance)
			avg_distance = np.mean(distance)
			std_distance = np.std(distance)

			
			# Curvature calculations
			# 1. Menger curvature with respect to start and end points calculated at all other points
			# 2. Angle subtended by start and end points at all other points
			# Menger curvature calculation details:
			# Let p1, p2, p3, ... pn be n points on the skeleton.
			# m2 = MengerCurvature(p1,p2,pn), m3 = MengerCurvature(p1,p3,pn) ... etc.
			# Aerage Menger Curvature, M = avg(m2, m3, ... m(n-1))
			def menger_curvature(A,B,C):
				AB = np.linalg.norm(A-B)
				BC = np.linalg.norm(B-C)
				AC = np.linalg.norm(A-C)
				s = (AB+BC+AC)/2
				area = (s*(s-AB)*(s-BC)*(s-AC)) ** 0.5
				return((4*area)/(AB*BC*AC))
			
			curvature = []
			angle = []
			for i in range(1,len(points)-1):
				#print(points[0],points[i],points[-1])
				curvature.append(menger_curvature(points[0],points[i],points[-1]))
				angle.append(np.degrees(np.arccos(np.dot(points[0]-points[i],points[-1]-points[i])/(np.linalg.norm(points[0]-points[i])*np.linalg.norm(points[-1]-points[i])))))
			avg_curvature = np.mean(curvature)
			std_curvature = np.std(curvature)
			avg_angle = np.mean(angle)
			std_angle = np.std(angle)
			# Add NA values for the first and last point, useful while priting to the output file.
			curvature = ["NA"] + curvature + ["NA"]
			angle = ["NA"] + angle + ["NA"]

			
			print("R-squared sum-distance avg-distance std-distance avg-curvature std-curvature avg-angle std-angle")
			print(rsquared, sum_distance, avg_distance, std_distance, avg_curvature, std_curvature, avg_angle, std_angle)

			
			with open(outdir + "/" + name_suffix + ".csv", 'w') as o:
				o.write("Sum-of-orthogonal-distances,"+str(sum_distance) + "\n")
				o.write("Avg-of-orthogonal-distances,"+str(avg_distance) + "\n")
				o.write("Std-of-orthogonal-distances,"+str(std_distance) + "\n")
				o.write("Avg-of-curvature," + str(avg_curvature) + "\n")
				o.write("Std-of-curvature," + str(std_curvature) + "\n")
				o.write("Avg-of-angle," + str(avg_angle) + "\n")
				o.write("Std-of-angle," + str(std_angle) + "\n")
				o.write("R-squared_least-square-regression," + str(rsquared) + "\n")
				o.write("Node_ID,X,Y,Z,Orthogonal_distance,Curvature,Angle\n")
				for i in range(0,len(points)):
					o.write(str(shortest_path[i]) + "," + ",".join([str(c) for c in points[i]]))
					o.write("," + str(distance[i]))
					o.write("," + str(curvature[i]))
					o.write("," + str(angle[i]) + "\n")
			
			self.save_skeleton(outdir=outdir)

		except:
			print("Exception occurred during linear fitting")
			self.selectedNodes = []
			print(sys.exc_info()[0])
			raise


	def crossSection_analysis(self):
		### This works
		### This is for calculating multiple cross-sections along the line passing through 2 selected nodes.
			try:
				print("Downsample:",self.downsample_entry.get())
				print("Selected Nodes:", self.selectedNodes)
				# Calculate cross-section
				### Note that coordinates are not converted to integers in this section. No image rotation is done here, so coordinates of p1 and p2 can be fractional.
				### In fact, converting the coordinates to integers introduces slight error in alignment of actual skeleton trace with the centerline.
				### Coordinates p1 and p2 obtained here are in voxel space.
				p1 = [x for x in self.skel.vertices[self.selectedNodes[0]] / np.array([32.0,32.0,30.0])]
				p2 = [x for x in self.skel.vertices[self.selectedNodes[1]] / np.array([32.0,32.0,30.0])]
				print("p1:", p1, " p2:", p2)

				###MAKE OUTPUT DIRECTORIES
				##############outdir = self.dirname + "/cross-sections_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2])
				outdir = self.dirname + "/cross-sections_downsample-" + self.downsample_entry.get() + "_nodes-" + str(self.selectedNodes[0]) + "-" + str(self.selectedNodes[1])
				# Delete directory and its contents if exists
				#if os.path.exists(outdir):
				#	try:
				#		shutil.rmtree(outdir)
				#		print("Warning: Cross-sections will be overwritten.")
				#	except OSError as e:
				#		print("Could not remove directory tree: %s : %s" % (outdir, e.strerror))
				try:
					os.makedirs(outdir)
				except OSError as exc:
					#if exc.errno == errno.EEXIST and os.path.isdir(self.images_outdir):
					print("Directory already exists. Existing files will be overwritten. Target directory:", outdir)
					#return(0)

				# The centerline coordinates obtained will be in voxel space.
				num_crosssections = 200 # Half of this number of cross sections will be created on each side of the starting point.
				d_nm = 50 # Distance between consecutive cross sections in nanometers
				# d_voxelunits is the distance between consecutive cross sections in voxel units
				centerline, d_voxelunits = self.get_centerline(p1=p1, p2=p2, n=int(num_crosssections/2), d=d_nm, outputdir=outdir, verbose=True)
				print(len(centerline))
				print(centerline)

				### Write OBJ file that contains following objects-
				### 1) Line representing vertices
				### translation parameters are in voxel units
				(translate_x, translate_y, translate_z) = (int(x) for x in self.translate_entry.get().split(","))

				print("Translations before:" ,translate_x,translate_y,translate_z)
				mip_level = self.skel_widgets['mip_level']['entry'].get()
				translate_x = translate_x / (2**int(mip_level))
				translate_y = translate_y / (2**int(mip_level))
				# ??? MAY BE DO NOT DO FOR transate_z
				#translate_z = translate_z / (2**int(mip_level))
				print("Translations after:" ,translate_x,translate_y,translate_z)

				# ???This scaling factor is to convert from nano meters to micrometers
				s = 0.001

				objfile = open(outdir + "/centerline.obj", "w")
				objfile.write("mtllib materials.mtl\n")

				# Write line
				objfile.write("o centerline\n")
				for p in centerline:
					#print("v", '{:.6f}'.format(p_rotated_orig[0]), '{:.6f}'.format(p_rotated_orig[1]), '{:.6f}'.format(p_rotated_orig[2]))
					# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
					# -1 is for inverting z axis.
					objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((p[0]+translate_y)*self.mip_dict[mip_level][0]*s),
																								 '{:.6f}'.format((p[1]+translate_x)*self.mip_dict[mip_level][1]*s),
																								 '{:.6f}'.format((p[2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				for i in range(1,len(centerline)):
					objfile.write("l " + str(i) + " " + str(i+1) + "\n")

				objfile.close()
				
				print("---------------DONE---------------\n")

				### Adding new functionality: Calculating pixel intensities projected on the centerline
				# Get centerline's first and last points in real space.
				# Read EM stack as 3D image.
				# Read mask as 3D image.
				# Remove membrane region from the mask using either of the two ways-
				#   1) Erode the mask by fixed amount and apply to the EM stack
				#   2) Apply the mask to the EM stack then Threshold + close
				# Apply mask to the EM stack, make everything else white

				# P => List of points (voxels) of a selected label
				# V => List of values of voxels P
				# P and V are corresponding lists.


				def read_image_stack(dirname="", znorm=False, minmax_scaling=False, read_as_gray=False):
					### When znorm=True, Z-normalization is done before minmax_scaling.
					
					if dirname == "":
						print("No image directory selected.")
						return(None)

					# Read PNGs from EM directory and construct 3D matrix
					print ("Loading voxel data from images (assuming that the data is at the same mip level as the segmentation data) ...")
					voxels = []
					for fn in sorted_nicely(os.listdir(dirname)):
						if fn.endswith(".png"):
							#print(os.path.join(dirname, fn))
							if read_as_gray:
								image = cv2.imread(os.path.join(dirname, fn), 0)
							else:
								image = cv2.imread(os.path.join(dirname, fn))
								image = image.sum(axis=2)

							if znorm:
								m = np.mean(image)
								s = np.std(image)
								image = (image-m)/s

							if minmax_scaling:
								minimum = np.min(image)
								max_min_diff = np.max(image) - minimum
								image = (image-minimum)/max_min_diff
							voxels.append(image)
								
					print("len(voxels) before dstack:", len(voxels))
					if len(voxels) == 0:
						return(None)
					voxels = np.dstack(voxels)
					print("voxels.shape:", voxels.shape)
					print()
					return(voxels)
				
				def voxel_intensity_histogram_along_centerline(voxels=None, mask=None, centerline=None, weighted=False, erosion_iter=0, num_bins=10, voxel_min=0.0, voxel_max=255.0, invert=False):
					print("voxels.shape:", voxels.shape)
					print("mask.shape:", mask.shape)
					
					if erosion_iter > 0:
						mask = scipy.ndimage.binary_erosion(mask, iterations=2).astype(mask.dtype)
					
					if invert:
						voxels = voxel_max-voxels# * (mask>0) # Inverted voxel values
					#else:
					#	voxels = voxels * (mask>0) # Original voxel values

					P = []
					v = []
					for index,val in np.ndenumerate(voxels):
						#print(index, val)
						if mask[index] > 0:
							P.append(list(index))
							v.append(val)
					#print("type(val):", type(val))

					P = np.array(P)
					v = np.array(v).astype(np.float64)
					
					print("P.shape:", P.shape)
					print("v.shape:", v.shape, v.sum())
	
					A = centerline[0]
					B = centerline[-1]
					print("Center line:", "A =", A, " B =", B)
					AP = P-A
					AB = B-A
					d = np.dot(AP,AB)/np.linalg.norm(AB)
					print("Distances from A of projections of P's on line AB are stored in d. d.shape =", d.shape)
					
					print("Histogram of d weighted by v:")
					binsize = np.linalg.norm(AB)/num_bins
					print("binsize =", binsize, "voxels")
					bins = [i*binsize for i in range(0, num_bins+2)]
					print("len(bins):", len(bins))
					print("bins =", bins)
					if weighted:
						hist = np.histogram(d, bins=bins, weights=v)
					else:
						hist = np.histogram(d, bins=bins)
					print("hist:", hist)
					print()
					return(hist)


				# Read EM data
				voxels = read_image_stack(dirname=os.path.dirname(self.dirname) + "/EM", znorm=True, minmax_scaling=True, read_as_gray=True)
				
				print(voxels[:,:,0])
				print(voxels[:,:,0].dtype)

				# Set selected labels, so that self.labels can be used as mask.
				self.set_labels(final_erosion=False)
				labels_mask = np.copy(self.labels)
				print("labels_mask sum (before) =", np.sum(labels_mask))

				if os.path.exists(os.path.dirname(self.dirname) + "/exclusion"):
					exclusion_mask = read_image_stack(dirname=os.path.dirname(self.dirname) + "/exclusion", read_as_gray=False)
					if exclusion_mask is not None:
						exclusion_mask[exclusion_mask>0] = 1
						print("exclusion_mask sum =", np.sum(exclusion_mask))
						labels_mask = labels_mask * (exclusion_mask==0) # Apply exclusion mask on selected labels

				print("labels_mask sum (after) =", np.sum(labels_mask))

				# Calculate voxel intensity histogram of voxels of masked selected labels
				hist1, bins = voxel_intensity_histogram_along_centerline(voxels=voxels, mask=labels_mask, centerline=centerline,
																																erosion_iter=2, num_bins=num_crosssections, weighted=False, voxel_min=0.0, voxel_max=1.0, invert=True)
				hist1_weighted, bins = voxel_intensity_histogram_along_centerline(voxels=voxels, mask=labels_mask, centerline=centerline,
																																				 erosion_iter=2, num_bins=num_crosssections, weighted=True, voxel_min=0.0, voxel_max=1.0, invert=True)
				#hist, bins = voxel_intensity_histogram_along_centerline(voxels=voxels, mask=self.labels, centerline=centerline, erosion_iter=2, num_bins=num_crosssections, invert=True)
				print(hist1.shape, bins.shape)
				print(hist1.dtype, hist1_weighted.dtype)
				
				# Get list of selected labels
				selected_labels = []
				merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())
				for m in merge_list:
					selected_labels += [x for x in re.split('\+|\(|\)|\[|\]', m) if x.isdigit()]
				selected_labels = "+".join(selected_labels)
				
				# Divide hist by number of voxels in that bin
				hist1_weighted_normalized = hist1_weighted/hist1
				print("hist1_weighted_normalized.dtype", hist1_weighted_normalized.dtype)

				f = open(outdir+'/centerline-histogram_selected-labels-'+selected_labels+'.csv', 'w')

				f.write("BIN,VOXELS-CNT,VOXELS-CNT_WEIGHTED-BY-INTENSITY,VOXELS-CNT_WEIGHTED-BY-INTENSITY_NORMALIZED-BY-SLICE-VOLUME\n")
				for i in range(0,len(hist1)):
					f.write(str(bins[i])+","+str(hist1[i])+","+str(hist1_weighted[i])+","+str(hist1_weighted_normalized[i])+"\n")
				f.close()
				
				
				# Calculate voxel intensity histogram of voxels of cargo labels
				cargo_mask = read_image_stack(dirname=os.path.dirname(self.dirname) + "/cargo_segmentation", read_as_gray=False)
				cargo_mask[cargo_mask>0] = 1
				hist2, bins = voxel_intensity_histogram_along_centerline(voxels=voxels, mask=cargo_mask, centerline=centerline,
																																erosion_iter=0, num_bins=num_crosssections, weighted=False, voxel_min=0.0, voxel_max=1.0, invert=True)
				hist2_weighted, bins = voxel_intensity_histogram_along_centerline(voxels=voxels, mask=cargo_mask, centerline=centerline,
																																				 erosion_iter=0, num_bins=num_crosssections, weighted=True, voxel_min=0.0, voxel_max=1.0, invert=True)
				print(hist2.shape, bins.shape)
				
				# Divide hist by number of voxels in that bin.
				# IMPORTANT: Note that hist2_weighted is divided by hist1, NOT by hist2.
				# This is because we have to divide by total number of voxels in the cross-section of the connection.
				hist2_weighted_normalized = hist2_weighted/hist1
				
				f = open(outdir+'/centerline-histogram_cargo.csv', 'w')

				f.write("BIN,VOXELS-CNT,VOXELS-CNT_WEIGHTED-BY-INTENSITY_NORMALIZED-BY-SLICE-VOLUME\n")
				for i in range(0,len(hist1)):
					f.write(str(bins[i])+","+str(hist2[i])+","+str(hist2_weighted_normalized[i])+"\n")
				f.close()

				print("Cargo volume =", np.sum(hist2)*32*32*30, "\n")

				print('DONE\n')
				
			except:
				print("Can not calculate shortest path.")
				print(sys.exc_info()[0])
				raise
	
	
	def printSelectedNodes(self):
		print(self.selectedNodes)
		self.selectedNodes = []



	def crossSection_analysis_old(self):
		###??? THIS WORKS, change 100 to 2 to activate
		### This is for calculating multiple cross-sections along the line passing through 2 selected nodes.
		try:
			print("Downsample:",self.downsample_entry.get())
			print("Selected Nodes:", self.selectedNodes)
			# Calculate cross-section
			p1 = [int(x) for x in self.skel.vertices[self.selectedNodes[0]] / np.array([32.0,32.0,30.0])]
			p2 = [int(x) for x in self.skel.vertices[self.selectedNodes[1]] / np.array([32.0,32.0,30.0])]
			print("p1:", p1, " p2:", p2)

			###MAKE OUTPUT DIRECTORIES
			##############outdir = self.dirname + "/cross-sections_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2])
			outdir = self.dirname + "/cross-sections_downsample-" + self.downsample_entry.get() + "_nodes-" + str(self.selectedNodes[0]) + "-" + str(self.selectedNodes[1])
			# Delete directory and its contents if exists
			if os.path.exists(outdir):
				try:
					shutil.rmtree(outdir)
					print("Warning: Cross-sections will be overwritten.")
				except OSError as e:
					print("Could not remove directory tree: %s : %s" % (outdir, e.strerror))
			try:
				os.makedirs(outdir+"/bw")
				os.makedirs(outdir+"/color")
			except OSError as exc:
				if exc.errno == errno.EEXIST and os.path.isdir(self.images_outdir):
					print("Could not create one/more directories:",outdir)
					return(0)

			cross_sections = self.getCrossSection_multiple(voxels=np.copy(self.threeDmatrix), p1=p1, p2=p2, n=50, d=5, outputdir=outdir, verbose=True)
			print("Number of cross sections:", len(cross_sections))


			# Calculate parameters for label in each cross section. A separate table will be created for each parameter.
			# Example: For parameter1
			#               | label1 | label2 | label3 |
			# crosssection1 |        |        |        |
			# crosssection2 |        |        |        |
			# crosssection3 |        |        |        |
			# crosssection4 |        |        |        |
			# crosssection5 |        |        |        |
			cross_section_prop = {}
			cnt = 0
			print(self.uniq_labels)
			for cross_section, p_rotated, p_rotated_orig, plane in cross_sections:
				if cnt not in cross_section_prop:
					cross_section_prop[cnt] = {}
				for l in self.uniq_labels[1:]:
					if l not in cross_section_prop[cnt]:
						cross_section_prop[cnt][l] = None

					img = np.copy(cross_section)
					img[img!=l] = 0
					
					print(l, np.sum(img))
					prop = measure.regionprops(img)
					print(prop, len(prop))
					if len(prop) != 0:
						#print({'AREA':prop[0].area, 'CONVEX_AREA':prop[0].convex_area, 'PERIMETER':prop[0].perimeter,
						#	     'MAJOR_AXIS_LENGTH':prop[0].major_axis_length, 'MINOR_AXIS_LENGTH':prop[0].minor_axis_length,
						#				'EXTENT':prop[0].extent, 'EQUIVALENT_DIAMETER':prop[0].equivalent_diameter})
																					
						cross_section_prop[cnt][l] = {'AREA':prop[0].area, 'CONVEX_AREA':prop[0].convex_area, 'PERIMETER':prop[0].perimeter,
							                            'MAJOR_AXIS_LENGTH':prop[0].major_axis_length, 'MINOR_AXIS_LENGTH':prop[0].minor_axis_length,
																					'EXTENT':prop[0].extent, 'EQUIVALENT_DIAMETER':prop[0].equivalent_diameter}
					else:
						cross_section_prop[cnt][l] = {'AREA':0, 'CONVEX_AREA':0, 'PERIMETER':0,
							                            'MAJOR_AXIS_LENGTH':0, 'MINOR_AXIS_LENGTH':0,
																					'EXTENT':0, 'EQUIVALENT_DIAMETER':0}
				cnt += 1

			with open(outdir + "/AREA.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['AREA']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]
						
			with open(outdir + "/CONVEX_AREA.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['CONVEX_AREA']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]

			with open(outdir + "/PERIMETER.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['PERIMETER']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]

			with open(outdir + "/MAJOR_AXIS_LENGTH.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['MAJOR_AXIS_LENGTH']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]
						
			with open(outdir + "/MINOR_AXIS_LENGTH.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['MINOR_AXIS_LENGTH']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]


			with open(outdir + "/EXTENT.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['EXTENT']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]

			with open(outdir + "/EQUIVALENT_DIAMETER.csv", 'w') as f:
				f.write("CROSS_SECTION," + ",".join([str(l) for l in sorted(self.uniq_labels[1:])]) + "\n")
				[f.write(str(cs) + "," + ",".join([str(cross_section_prop[cs][l]['EQUIVALENT_DIAMETER']) for l in sorted(cross_section_prop[cs].keys())]) + "\n") for cs in sorted(cross_section_prop.keys())]


			cnt = 0
			for cross_section, p_rotated, p_rotated_orig, plane in cross_sections:
				print("Writing cross-section", cnt)

				#print(self.colormap,self.colormapHex)
				im = np.dstack(np.array(3*[cross_section]))
				for ch in [0,1,2]:
					#print(im[:,:,ch].shape)
					for l in self.uniq_labels[1:]:
						im[:,:,ch][im[:,:,ch] == l] = self.colormap[l][ch]
				#print(im.shape)

				# Write black and white cross section to file
				cross_section_bw_fname = outdir + "/bw/img_" + str(cnt) + ".png"
				Image.fromarray(np.where(cross_section>0,255,0).astype('uint8')).save(cross_section_bw_fname)

				# Write colored cross section to file
				cross_section_color_fname = outdir + "/color/img_" + str(cnt) + ".png"
				Image.fromarray(im.astype('uint8')).save(cross_section_color_fname)
				
				# Write cross section as csv
				#cross_section_fname = self.dirname + "/section_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2]) + ".csv"
				#np.savetxt(cross_section_fname, cross_section, delimiter=",", fmt='%d')

				cnt += 1


			### Write OBJ file that contains following objects-
			### 1) Line representing vertices
			### 2) Planes at all vertices (as separate objects)
			(translate_x, translate_y, translate_z) = (int(x) for x in self.translate_entry.get().split(","))

			print("Translations before:" ,translate_x,translate_y,translate_z)
			mip_level = self.skel_widgets['mip_level']['entry'].get()
			translate_x = translate_x / (2**int(mip_level))
			translate_y = translate_y / (2**int(mip_level))
			# ??? MAY BE DO NOT DO FOR transate_z
			#translate_z = translate_z / (2**int(mip_level))
			print("Translations after:" ,translate_x,translate_y,translate_z)

			# ???This scaling factor is to convert from nano meters to micrometers
			s = 0.001

			objfile = open(outdir + "/cross-sections.obj", "w")
			objfile.write("mtllib materials.mtl\n")

			# Write line
			objfile.write("o line\n")
			for cross_section, p_rotated, p_rotated_orig, plane in cross_sections:
				#print("v", '{:.6f}'.format(p_rotated_orig[0]), '{:.6f}'.format(p_rotated_orig[1]), '{:.6f}'.format(p_rotated_orig[2]))
				# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
				# -1 is for inverting z axis.
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((p_rotated_orig[0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((p_rotated_orig[1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((p_rotated_orig[2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
			for i in range(1,len(cross_sections)):
				objfile.write("l " + str(i) + " " + str(i+1) + "\n")
			v_num_offset = i + 1

			# Write planes
			"""
			### When planes have 4 points (Next section deals with planes as flattened cubes, represented by 8 points)
			plane_cnt = 0
			for cross_section, p_rotated, p_rotated_orig, plane in cross_sections:
				# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
				# -1 is for inverting z axis.
				objfile.write("o plane."+str(plane_cnt)+"\n")
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[0][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[0][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[0][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[1][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[1][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[1][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[2][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[2][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[2][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[3][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[3][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[3][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				
				objfile.write("f " + str(v_num_offset+1) + " " + str(v_num_offset+2) + " " + str(v_num_offset+3) + " " + str(v_num_offset+4) + "\n")
				v_num_offset += 4
				plane_cnt += 1

			"""
			
			### When planes have 8 points (Planes as flattened cubes, represented by 8 points)
			plane_cnt = 0
			for cross_section, p_rotated, p_rotated_orig, plane in cross_sections:
				# NOTE: Swap translation offsets x and y. This is because the X and Y axes considered by VAST are Y and X respectively in numpy ndarrays.
				# -1 is for inverting z axis.
				objfile.write("o plane."+str(plane_cnt)+"\n")
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[0][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[0][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[0][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[1][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[1][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[1][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[2][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[2][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[2][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[3][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[3][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[3][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[4][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[4][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[4][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[5][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[5][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[5][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[6][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[6][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[6][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				objfile.write("v {0} {1} {2}\n".format('{:.6f}'.format((plane[7][0]+translate_y)*self.mip_dict[mip_level][0]*s),
																							 '{:.6f}'.format((plane[7][1]+translate_x)*self.mip_dict[mip_level][1]*s),
																							 '{:.6f}'.format((plane[7][2]+translate_z)*self.mip_dict[mip_level][2]*s*-1)))
				
				objfile.write("f " + str(v_num_offset+1) + " " + str(v_num_offset+4) + " " + str(v_num_offset+3) + " " + str(v_num_offset+2) + "\n")
				objfile.write("f " + str(v_num_offset+5) + " " + str(v_num_offset+6) + " " + str(v_num_offset+7) + " " + str(v_num_offset+8) + "\n")
				objfile.write("f " + str(v_num_offset+1) + " " + str(v_num_offset+2) + " " + str(v_num_offset+6) + " " + str(v_num_offset+5) + "\n")
				objfile.write("f " + str(v_num_offset+2) + " " + str(v_num_offset+3) + " " + str(v_num_offset+7) + " " + str(v_num_offset+6) + "\n")
				objfile.write("f " + str(v_num_offset+3) + " " + str(v_num_offset+4) + " " + str(v_num_offset+8) + " " + str(v_num_offset+7) + "\n")
				objfile.write("f " + str(v_num_offset+4) + " " + str(v_num_offset+1) + " " + str(v_num_offset+5) + " " + str(v_num_offset+8) + "\n")

				v_num_offset += 8
				plane_cnt += 1

			objfile.close()
			
			print("---------------DONE---------------\n")

		except:
			print("Can not calculate shortest path.")
			self.selectedNodes = []
			print(sys.exc_info()[0])
			raise





	def crossSection_analysis_old_withRegionGrowing(self):
		def region_grow(img, seed):
			l = img[tuple(seed)]
			#print("Label of seed:", l)
			if l == 0:
				#return(np.zeros((img.shape)).astype(np.uint8))
				return(None)
			img[img!=l] = 0
			properties = measure.regionprops(img)
			#print("Original image shape:", img.shape)
			bbox = properties[0].bbox
			img = img[bbox[0]:bbox[2],bbox[1]:bbox[3]]
			#print("Cropped image shape:", img.shape)
			#print(img)
			seed = seed - np.array(bbox[0:2])
			#print("New seed coordinates:", seed)
			
			visited = np.zeros((img.shape))

			seeds = [seed]# add first seed to seeds
			while(seeds != []):
				seed = seeds.pop()
				neighbors = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]])
				for neighbor in neighbors:
					n = seed + neighbor
					if n[0]>=0 and n[0]<img.shape[0] and n[1]>=0 and n[1]<img.shape[1]:# check image bounds
						if img[tuple(n)] == l:# if neighbor is of same label
							if visited[tuple(n)] == 0:# if neighbor not yet visited, add it to seeds
								seeds.append(n)
							visited[tuple(n)] = 1# add neighbor to visited

			#print(visited)
			return(visited.astype(np.uint8))

		try:
			#from SkeletonRadiusPlot import SkeletonRadiusPlot
			shortest_path = nx.dijkstra_path(G,self.selectedNodes[0],self.selectedNodes[1])
			
			#print("Path",cnt)
			print("Nodes:", self.selectedNodes[0], "-", self.selectedNodes[1])
			print("Downsample:",self.downsample_entry.get())
			path_length = 0
			for node_id in range(0,len(shortest_path)-1):
				path_length += np.linalg.norm(self.skel.vertices[shortest_path[node_id]]-self.skel.vertices[shortest_path[node_id+1]])
			print("Path length:",path_length)
			print("Shortest path and radii along the path:")
			#print("Vertex", ' '.join([str(x) for x in shortest_path]))
			#print("Radius", ' '.join([str(self.skel.radius[i]) for i in shortest_path]))
			print("Node\tLabel_ROI\tLabel_p1_rotated\tRadius\tDegree\tZ\t", end="")
			#print("Area_ROI\tConvex_Area_ROI\tMajor_Axis_Length_ROI\tMinor_Axis_Length_ROI\tPerimeter_ROI\tExtent_ROI\tEquiv_Diameter_ROI\t", end="")
			print("Area_All\tConvex_Area_All\tMajor_Axis_Length_All\tMinor_Axis_Length_All\tPerimeter_All\tExtent_All\tEquiv_Diameter_All\n", end="")
			for i in range(0,len(shortest_path)):
				area_pixels = 0.0
				perimeter = 0.0
				if i < len(shortest_path) - 1:
					# Calculate cross-section
					p1 = [int(x) for x in self.skel.vertices[shortest_path[i]]  / np.array([32.0,32.0,30.0])]
					p2 = [int(x) for x in self.skel.vertices[shortest_path[i+1]]/ np.array([32.0,32.0,30.0])]
					cross_sections = self.getCrossSection(voxels=np.copy(self.threeDmatrix), p1=p1, p2=p2, verbose=False)
					#cross_sections = self.getCrossSection_multiple(voxels=np.copy(self.threeDmatrix), p1=p1, p2=p2, n=50, d=5, verbose=False)
					print("Number of cross sections:", len(cross_sections))
					for cross_section, p1_rotated in cross_sections:
						l = self.threeDmatrix[tuple(p1)]
						l_p1_rotated = cross_section[int(p1_rotated[0]), int(p1_rotated[1])]

						cross_section_fname = self.dirname + "/section_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2]) + ".csv"
						np.savetxt(cross_section_fname, cross_section, delimiter=",", fmt='%d')

						#print(p1_rotated)
						#print("Label of p1:", l)

						#if l == cross_section[(int(p1_rotated[0]), int(p1_rotated[1]))]:
						#roi = region_grow(np.copy(cross_section),np.array([int(p1_rotated[0]), int(p1_rotated[1])]))
						#prop_roi = measure.regionprops(roi)
						
						img = np.copy(cross_section)
						img[img!=0] = 1
						#print(img.shape)
						print("l before erosion:", img[int(p1_rotated[0]), int(p1_rotated[1])])
						img = scipy.ndimage.binary_erosion(img, iterations=2, structure=np.ones((3,3))).astype(np.uint8)
						#img2 = img
						print("l after erosion:", img[int(p1_rotated[0]), int(p1_rotated[1])])
						img2 = region_grow(img,np.array([int(p1_rotated[0]), int(p1_rotated[1])]))
						#print(img2.shape)
						img2 = scipy.ndimage.binary_dilation(img2, iterations=2, structure=np.ones((3,3))).astype(np.uint8)
						if img2 is None:
							prop_all = measure.regionprops(img)
						else:
							prop_all = measure.regionprops(img2)

						###??? DOUBT: Check area and perimeter values given by skimage. Do they match with your calculation?
						print(str(shortest_path[i])+"\t"+str(l)+"\t"+str(l_p1_rotated)+"\t"+str(self.skel.radius[shortest_path[i]])+"\t"+str(G.degree[shortest_path[i]])+"\t"+str(p1_rotated[2])+"\t", end="")
						#print("\t".join([str(x) for x in [prop_roi[0].area, prop_roi[0].convex_area, prop_roi[0].major_axis_length, prop_roi[0].minor_axis_length,
						#																	prop_roi[0].perimeter, prop_roi[0].extent, prop_roi[0].equivalent_diameter]])+"\t", end="")
						if prop_all == []:
							print("")
						else:
							print("\t".join([str(x) for x in [prop_all[0].area, prop_all[0].convex_area, prop_all[0].major_axis_length, prop_all[0].minor_axis_length,
																								prop_all[0].perimeter, prop_all[0].extent, prop_all[0].equivalent_diameter]]))

						"""
						# For testing
						print(str(shortest_path[i])+"\t"+str(l)+"\t"+str(self.skel.radius[shortest_path[i]])+"\t"+str(G.degree[shortest_path[i]])+"\t"+
									"\t".join([str(x) for x in [prop_roi[0].area, prop_roi[0].convex_area]])+"\t"+
									"\t".join([str(x) for x in [prop_all[0].area, prop_all[0].convex_area]]))
						"""
			print("")

			"""
			# Area
			area_pixels = np.sum(cross_section==l)
			# Perimeter
			cross_section_l = cross_section==l
			cross_section_l_eroded = scipy.ndimage.binary_erosion(cross_section_l, iterations=1)
			perimeter = np.sum(np.logical_xor(cross_section_l, cross_section_l_eroded))
			"""

			"""
			# Calculate area of cross-section.
			# Cross-section at first node clicked and normal to the vector joining first and second node clicked.
			print(self.skel.vertices[self.selectedNodes[0]], type(self.skel.vertices[self.selectedNodes[0]]))
			print(self.skel.vertices[self.selectedNodes[0]]/np.array([32.0,32.0,30.0]))
			print([int(x) for x in self.skel.vertices[self.selectedNodes[0]]/np.array([32.0,32.0,30.0])])
			p1 = [int(x) for x in self.skel.vertices[self.selectedNodes[0]]/np.array([32.0,32.0,30.0])]
			p2 = [int(x) for x in self.skel.vertices[self.selectedNodes[1]]/np.array([32.0,32.0,30.0])]
			cross_section = self.getCrossSection(voxels=np.copy(self.threeDmatrix), p1=p1, p2=p2, verbose=True)
			#print("Cross-section shape:", cross_section.shape)

			# Cross-section area and perimeter
			print("Total cross-section area (all labels) =", np.sum(cross_section!=0), "pixels OR", np.sum(cross_section!=0)*32.0*32.0, "nm^2")
			uniq_labels_cross_section = np.unique(cross_section)
			for l in uniq_labels_cross_section[1:]:
				# Area
				area_pixels = np.sum(cross_section==l)
				print("Cross-section area of label", l, "=", area_pixels, "pixels OR", area_pixels*32.0*32.0, "nm^2")

				# Perimeter
				cross_section_l = cross_section==l
				cross_section_l_eroded = scipy.ndimage.binary_erosion(cross_section_l, iterations=1)
				perimeter = np.sum(np.logical_xor(cross_section_l, cross_section_l_eroded))
				np.savetxt(self.dirname+"/section_"+str(l)+".csv", np.logical_xor(cross_section_l, cross_section_l_eroded), delimiter=",", fmt='%d')
				print("Perimeter of label", l, "=", perimeter, "pixels OR", perimeter*32.0, "nm")

			# Save cross-section to file as 2D array.
			#cross_section_fname = self.dirname + "/section_" + ",".join([str(x) for x in p1]) + "_" + ",".join([str(x) for x in p2]) + ".csv"
			#np.savetxt(cross_section_fname, cross_section, delimiter=",", fmt='%d')
									
			###??? NEEDS TO BE DONE:
			### 1. REGION GROWING TO IDENTIFY AREA OF INTEREST
			### 2. AREA AND PERIMETER OF ALL NODES ALONG THE SHORTEST PATH
			### 3. SURFACE FEATURES OF THE SEGMENT REPRESENTED BY THE SHORTEST PATH (Convex hull ratio, concavity/convexity, mean curvature,
			###    gaussian curvature, # of branches, lobes/compartments, volume, surface area)
			"""
						
			###??? CAUTION: Some problem with the following. It updates the existing figure in use.
			#ax_1, fig_1 = SkeletonRadiusPlot([self.skel.radius[i] for i in shortest_path])
			#newTk_1 = Tk()
			#canvas_1 = FigureCanvasTkAgg(fig_1, newTk_1)
			#canvas_1.draw()
		except:
			print("Can not calculate shortest path.")
			self.selectedNodes = []
			print(sys.exc_info()[0])
			raise


	def crossSection_analysis_old_trial(self):
		###??? THIS IS TRIAL, change 100 to 2 to activate
		if event.button == 100:
			#Setting the picker function:
			closestIndex = calcClosestDatapoint(self.skel.vertices, event)
			print("*", closestIndex, self.skel.radius[closestIndex])
			
			if len(self.selectedNodes) < 4:
				self.selectedNodes.append(closestIndex)
			else:
				print(self.selectedNodes)

			if len(self.selectedNodes) == 4:
				try:
					#from SkeletonRadiusPlot import SkeletonRadiusPlot
					shortest_path = nx.dijkstra_path(G,self.selectedNodes[0],self.selectedNodes[3])
					
					#print("Path",cnt)
					print("Nodes:", self.selectedNodes[0], "-", self.selectedNodes[3])
					print("Downsample:",self.downsample_entry.get())
					path_length = 0
					for node_id in range(0,len(shortest_path)-1):
						path_length += np.linalg.norm(self.skel.vertices[shortest_path[node_id]]-self.skel.vertices[shortest_path[node_id+1]])
					print("Path length:",path_length)
					print("Shortest path and radii along the path:")
					print("Vertex", ' '.join([str(x) for x in shortest_path]))
					print("Radius", ' '.join([str(self.skel.radius[i]) for i in shortest_path]))
					p1 = [int(x) for x in self.skel.vertices[self.selectedNodes[1]] / np.array([32.0,32.0,30.0])]
					p2 = [int(x) for x in self.skel.vertices[self.selectedNodes[2]] / np.array([32.0,32.0,30.0])]
					print(p1)
					print(p2)
					"""
					points = []
					for i in range(0,len(shortest_path)):
						print(self.skel.vertices[shortest_path[i]])
						points.append([int(x) for x in self.skel.vertices[shortest_path[i]] / np.array([32.0,32.0,30.0])])
					cross_sections = self.getCrossSections_alongPath(voxels=np.copy(self.threeDmatrix), p1=p1, p2=p2, points=points, verbose=False)
					print("Number of cross-sections:", len(cross_sections), len(shortest_path))

					print("Node\tLabel_q\tLabel_q_rotated\tRadius\tDegree\tZ\t", end="")
					#print("Area_ROI\tConvex_Area_ROI\tMajor_Axis_Length_ROI\tMinor_Axis_Length_ROI\tPerimeter_ROI\tExtent_ROI\tEquiv_Diameter_ROI\t", end="")
					print("Area_All\tConvex_Area_All\tMajor_Axis_Length_All\tMinor_Axis_Length_All\tPerimeter_All\tExtent_All\tEquiv_Diameter_All\n", end="")
					i = 0
					for cross_section, q, q_rotated in cross_sections:
						l = self.threeDmatrix[tuple(q)]
						l_q_rotated = cross_section[int(q_rotated[0]), int(q_rotated[1])]

						img = np.copy(cross_section)
						img[img!=0] = 1

						imgout = np.dstack(3*[img])
						imgout[imgout==1]=200
						imgout[int(q_rotated[0]), int(q_rotated[1]), 0] = 255
						imgout[int(q_rotated[0]), int(q_rotated[1]), 1] = 0
						imgout[int(q_rotated[0]), int(q_rotated[1]), 2] = 0
						Image.fromarray(imgout.astype('uint8')).save("img_"+str(shortest_path[i])+".png")

						#print(img.shape)
						#print("l before erosion:", img[int(q_rotated[0]), int(q_rotated[1])])
						img = scipy.ndimage.binary_erosion(img, iterations=2, structure=np.ones((3,3))).astype(np.uint8)

						imgout = np.dstack(3*[img])
						imgout[int(q_rotated[0]), int(q_rotated[1]), 0] = 255
						imgout[int(q_rotated[0]), int(q_rotated[1]), 1] = 0
						imgout[int(q_rotated[0]), int(q_rotated[1]), 2] = 0
						Image.fromarray(imgout.astype('uint8')).save("img_eroded_"+str(shortest_path[i])+".png")

						#img2 = img
						#print("l after erosion:", img[int(q_rotated[0]), int(q_rotated[1])])
						img2 = region_grow(img,np.array([int(q_rotated[0]), int(q_rotated[1])]))
													
						if img2 is None:
							print("*** img2 is None ***")
						#print(img2.shape)
						#img2 = scipy.ndimage.binary_dilation(img2, iterations=1, structure=np.ones((3,3))).astype(np.uint8)
						if img2 is None:
							prop_all = measure.regionprops(img)
						else:
							prop_all = measure.regionprops(img2)

						###??? DOUBT: Check area and perimeter values given by skimage. Do they match with your calculation?
						print(str(shortest_path[i])+"\t"+str(l)+"\t"+str(l_q_rotated)+"\t"+str(self.skel.radius[shortest_path[i]])+"\t"+str(G.degree[shortest_path[i]])+"\t"+str(q_rotated[2])+"\t", end="")
						#print("\t".join([str(x) for x in [prop_roi[0].area, prop_roi[0].convex_area, prop_roi[0].major_axis_length, prop_roi[0].minor_axis_length,
						#																	prop_roi[0].perimeter, prop_roi[0].extent, prop_roi[0].equivalent_diameter]])+"\t", end="")
						if prop_all == []:
							print("")
						else:
							print("\t".join([str(x) for x in [prop_all[0].area, prop_all[0].convex_area, prop_all[0].major_axis_length, prop_all[0].minor_axis_length,
																								prop_all[0].perimeter, prop_all[0].extent, prop_all[0].equivalent_diameter]]))
						i += 1

					"""
				except:
					print("Can not calculate shortest path.")
					self.selectedNodes = []
					print(sys.exc_info()[0])
					raise
					



	"""
	### Not necessary to calculate multiple cross sections individually.
	def getParallelCrossSections(self, voxels=None, p1=None, p2=None, d=None, n=None, verbose=False):
		print("Calculating parallel cross-sections")

		p1 = np.array(p1)
		p2 = np.array(p2)
		if verbose: print("p1:", p1)
		if verbose: print("p2:", p2)

		v = p2-p1
		if verbose: print("v:", v)

		u = v/np.linalg.norm(v)
		if verbose: print("u:", u)
		
		for i in range(0,n):
			p = p1 + (i+1)*d*u
			q = p1 - (i+1)*d*u
			print(i,":",p, q, "Distances:", (i+1)*d, np.linalg.norm(p-p1), np.linalg.norm(q-p1))
			# Cross sections at p and q
			getCrossSection(voxels=np.copy(self.threeDmatrix), p1=p, p2=p1, verbose=False)
			getCrossSection(voxels=np.copy(self.threeDmatrix), p1=q, p2=p1, verbose=False)
	"""

	def getCrossSections_alongPath(self, voxels=None, p1=None, p2=None, points=[], verbose=False):
		# Returns cross sections of a 3D image (represented by voxels, a 3D numpy array) at all points (given in the list 'points'), normal to vector p = p2-p1.
		# Rotates the 3D image such that vector p aligns with Z-axis.
		# Applies same rotations to all points in the list 'points'.
		# Returns xy slices at z = z coordinate of rotated points.

		p1 = np.array(p1)
		p2 = np.array(p2)
		if verbose: print("p1:", p1)
		if verbose: print("p2:", p2)

		# Invert p if Y-coordinate of p is positive.
		# Rotations calculated for vector p with positive Y-coordinate seems to result in rotated p which does not align with Z-axis.
		# Inverting p in such cases seems to solve the problem. I have some idea why this happens, but need to understand more.
		p = p2 - p1
		if verbose: print("p original:", p)
		if p[1] > 0:
			p = -p
			if verbose: print("p inverted:", p)

		# Calculate length of vector p		
		l = np.linalg.norm(p)
		if verbose: print("l =", l)

		# Calculate original center of the 3D image
		org_center = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("org_center:", org_center)

		# Calculate sequential rotations theta and alpha.
		# theta: rotation around Z-axis
		# alpha: rotation around Y-axis
		theta = np.arccos(p[0] / (math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) + 0.0000000000001) )
		alpha = np.arccos(p[2] / np.linalg.norm(p))
		if verbose: print("theta =", math.degrees(theta), "alpha =", math.degrees(alpha))

		# Rotate 3D image by theta around Z-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(theta), axes=(0,1), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		rot_center1 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		# Rotate 3D image by alpha around Y-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(alpha), axes=(0,2), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		rot_center2 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])

		cross_sections = []
		for q in points:
			# Translate point q
			q_trans = q - org_center
			if verbose: print("q_trans:", q_trans)
			# Rotate point q (Note the rotation around positive Z-axis)
			rotvec_theta = theta * np.array([0,0,1])
			rotation_theta = Rotation.from_rotvec(rotvec_theta)
			q_trans_rot = rotation_theta.apply(q_trans)
			if verbose: print("q_trans_rot:", q_trans_rot)
			# Translate point q
			if verbose: print("rot_center1:", rot_center1)
			q_trans_rot_trans = q_trans_rot + rot_center1
			if verbose: print("q after theta:", q_trans_rot_trans, "\n")

			# Translate point q
			q_trans = q_trans_rot_trans - rot_center1
			if verbose: print("q_trans:", q_trans)
			# Rotate point q (Note the rotation around negative Y-axis)
			rotvec_alpha = alpha * np.array([0,-1,0])
			rotation_alpha = Rotation.from_rotvec(rotvec_alpha)
			q_trans_rot = rotation_alpha.apply(q_trans)
			if verbose: print("q_trans_rot:", q_trans_rot)
			# Translate point q
			if verbose: print("rot_center2:", rot_center2)
			q_trans_rot_trans = q_trans_rot + rot_center2
			if verbose: print("q after alpha:", q_trans_rot_trans)

			cross_sections.append( (voxels[:,:,int(q_trans_rot_trans[2])], q, q_trans_rot_trans) )
		
		"""
		# Write obj file which shows the 3D object along with the plane of cross-section and the vector from origin indicating the point p1.
		# The cross-section is calculated at p1.
		objfile = open(self.dirname + "/test_obj.obj","w")
		verts, faces, normals, values = measure.marching_cubes_lewiner(voxels, 0, step_size=1)
		# Write vertices of the object
		for item in verts:
			objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
		# Write vertices of the plane of cross-section
		objfile.write("v 0 0" + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v " + str(voxels.shape[0]) + " 0 " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v " + str(voxels.shape[0]) + " " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v 0 " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		# Write vertices of the vector from origin indicating the point p1
		objfile.write("v 0 0 0\n")
		objfile.write("v " + str(p1_trans_rot_trans[0]) + " " + str(p1_trans_rot_trans[1]) + " " + str(p1_trans_rot_trans[2]) + "\n")

		# Write faces of the object
		faces = faces+1
		for item in faces:
			objfile.write("f {0} {1} {2}\n".format(item[0],item[1],item[2]))
		# Write faces of the plane of cross-section
		num_verts = len(verts)
		objfile.write("f " + str(num_verts+1) + " " + str(num_verts+2) + " " + str(num_verts+3) + " " + str(num_verts+4) + "\n")
		# Write faces of the vector from origin indicating the point p1
		objfile.write("l " + str(num_verts+5) + " " + str(num_verts+6) + "\n")

		objfile.close()
		"""
		
		# Return xy-slice of the rotated 3D image at p1
		#return([(voxels[:,:,int(p1_trans_rot_trans[2])], p1_trans_rot_trans)])
		return(cross_sections)

	def getCrossSection(self, voxels=None, p1=None, p2=None, verbose=False):
		# Returns cross section of a 3D image (represented by voxels, a 3D numpy array) at point p1, normal to vector p = p2-p1.
		# Rotates the 3D image such that vector p aligns with Z-axis.
		# Applies same rotations to the point p1.
		# Returns xy slice at z = z coordinate of rotated p1.

		p1 = np.array(p1)
		p2 = np.array(p2)
		if verbose: print("p1:", p1)
		if verbose: print("p2:", p2)

		# Invert p if Y-coordinate of p is positive.
		# Rotations calculated for vector p with positive Y-coordinate seems to result in rotated p which does not align with Z-axis.
		# Inverting p in such cases seems to solve the problem. I have some idea why this happens, but need to understand more.
		p = p2 - p1
		if verbose: print("p original:", p)
		if p[1] > 0:
			p = -p
			if verbose: print("p inverted:", p)

		# Calculate length of vector p		
		l = np.linalg.norm(p)
		if verbose: print("l =", l)

		# Calculate original center of the 3D image
		org_center = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("org_center:", org_center)

		# Calculate sequential rotations theta and alpha.
		# theta: rotation around Z-axis
		# alpha: rotation around Y-axis
		theta = np.arccos(p[0] / (math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) + 0.0000000000001) )
		alpha = np.arccos(p[2] / np.linalg.norm(p))
		if verbose: print("theta =", math.degrees(theta), "alpha =", math.degrees(alpha))

		# Rotate 3D image by theta around Z-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(theta), axes=(0,1), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		# Translate point p1
		p1_trans = p1 - org_center
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around positive Z-axis)
		rotvec_theta = theta * np.array([0,0,1])
		rotation_theta = Rotation.from_rotvec(rotvec_theta)
		p1_trans_rot = rotation_theta.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point p1
		rot_center1 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("rot_center1:", rot_center1)
		p1_trans_rot_trans = p1_trans_rot + rot_center1
		if verbose: print("p1 after theta:", p1_trans_rot_trans, "\n")

		# Rotate 3D image by alpha around Y-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(alpha), axes=(0,2), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		# Translate point p1
		p1_trans = p1_trans_rot_trans - rot_center1
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around negative Y-axis)
		rotvec_alpha = alpha * np.array([0,-1,0])
		rotation_alpha = Rotation.from_rotvec(rotvec_alpha)
		p1_trans_rot = rotation_alpha.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point p1
		rot_center2 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("rot_center2:", rot_center2)
		p1_trans_rot_trans = p1_trans_rot + rot_center2
		if verbose: print("p1 after alpha:", p1_trans_rot_trans)

		# Write obj file which shows the 3D object along with the plane of cross-section and the vector from origin indicating the point p1.
		# The cross-section is calculated at p1.
		objfile = open(self.dirname + "/test_obj.obj","w")
		verts, faces, normals, values = measure.marching_cubes_lewiner(voxels, 0, step_size=1)
		# Write vertices of the object
		for item in verts:
			objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
		# Write vertices of the plane of cross-section
		objfile.write("v 0 0" + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v " + str(voxels.shape[0]) + " 0 " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v " + str(voxels.shape[0]) + " " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		objfile.write("v 0 " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2])) + "\n")
		# Write vertices of the vector from origin indicating the point p1
		objfile.write("v 0 0 0\n")
		objfile.write("v " + str(p1_trans_rot_trans[0]) + " " + str(p1_trans_rot_trans[1]) + " " + str(p1_trans_rot_trans[2]) + "\n")

		# Write faces of the object
		faces = faces+1
		for item in faces:
			objfile.write("f {0} {1} {2}\n".format(item[0],item[1],item[2]))
		# Write faces of the plane of cross-section
		num_verts = len(verts)
		objfile.write("f " + str(num_verts+1) + " " + str(num_verts+2) + " " + str(num_verts+3) + " " + str(num_verts+4) + "\n")
		# Write faces of the vector from origin indicating the point p1
		objfile.write("l " + str(num_verts+5) + " " + str(num_verts+6) + "\n")

		objfile.close()

		# Return xy-slice of the rotated 3D image at p1
		return([(voxels[:,:,int(p1_trans_rot_trans[2])], p1_trans_rot_trans)])


	def get_centerline(self, p1=None, p2=None, n=None, d=None, outputdir=None, verbose=False):
		### Input coordinates p2 and p2 are in voxel space.
		### d is to be given in nanomenters.

		mip_level = np.array(self.mip_dict[self.skel_widgets['mip_level']['entry'].get()])
		#mip_level = np.array([32.0,32.0,32.0])# Test for isotropic voxels
		if verbose: print("mip level:", mip_level)
		
		p1 = np.array(p1)
		p2 = np.array(p2)
		if verbose: print("p1:", p1)
		if verbose: print("p2:", p2)

		p = p2 - p1
		if verbose: print("p original:", p)
		pcap = p / np.linalg.norm(p)

		mod_pcap = np.linalg.norm(pcap)
		pcap_scaled = mip_level*pcap
		mod_pcap_scaled = np.linalg.norm(mip_level*pcap)

		if verbose: print("p_unit:", pcap, ", |p_unit| =", mod_pcap, "voxel units OR |",pcap_scaled, "| =", mod_pcap_scaled, "nm")
		if verbose: print("p1 next:", p1 + 2 * d/mod_pcap_scaled * p)

		d_voxelunits = d/mod_pcap_scaled # Use this d in voxel units to get equidistant points along vector p

		if verbose: print("d =", d, "nm, d_voxelunits =", d_voxelunits)
		
		centerline = []
		for i in range(-n,n+1):
			q = p1 + i * d_voxelunits * pcap
			#print(q)
			centerline.append(q)
		
		# The centerline coordinates are in voxel space.
		return(centerline, d_voxelunits)
		
		

	def getCrossSection_multiple(self, voxels=None, p1=None, p2=None, n=None, d=None, outputdir=None, verbose=False):
		# Returns n cross sections of a 3D image (represented by voxels, a 3D numpy array) placed at distance d on each side of p1 and normal to vector p = p2-p1.
		# Rotates the 3D image such that vector p aligns with Z-axis.
		# Applies same rotations to the point p1.
		# Returns xy slice at z = z coordinate of rotated p1 as well as n slices on each side of p1 placed at distance d from each other.

		p1 = np.array(p1)
		p2 = np.array(p2)
		if verbose: print("p1:", p1)
		if verbose: print("p2:", p2)

		# Invert p if Y-coordinate of p is positive.
		# Rotations calculated for vector p with positive Y-coordinate seems to result in rotated p which does not align with Z-axis.
		# Inverting p in such cases seems to solve the problem. I have some idea why this happens, but need to understand more.
		p = p2 - p1
		if verbose: print("p original:", p)
		if p[1] > 0:
			p = -p
			if verbose: print("p inverted:", p)

		# Calculate length of vector p
		l = np.linalg.norm(p)
		if verbose: print("l =", l)

		# Calculate original center of the 3D image
		org_center = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("org_center:", org_center)

		# Calculate sequential rotations theta and alpha.
		# theta: rotation around Z-axis
		# alpha: rotation around Y-axis
		theta = np.arccos(p[0] / (math.sqrt(math.pow(p[0],2) + math.pow(p[1],2)) + 0.0000000000001) )
		alpha = np.arccos(p[2] / np.linalg.norm(p))
		if verbose: print("theta =", math.degrees(theta), "alpha =", math.degrees(alpha))

		# Rotate 3D image by theta around Z-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(theta), axes=(0,1), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		# Translate point p1
		p1_trans = p1 - org_center
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around positive Z-axis)
		rotvec_theta = theta * np.array([0,0,1])
		rotation_theta = Rotation.from_rotvec(rotvec_theta)
		p1_trans_rot = rotation_theta.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point p1
		rot_center1 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("rot_center1:", rot_center1)
		p1_trans_rot_trans = p1_trans_rot + rot_center1
		if verbose: print("p1 after theta:", p1_trans_rot_trans, "\n")

		# Rotate 3D image by alpha around Y-axis
		voxels = scipy.ndimage.rotate(voxels, math.degrees(alpha), axes=(0,2), reshape=True, output=None, order=0, mode='constant', cval=0.0, prefilter=True)
		if verbose: print("Resized:", voxels.shape)
		# Translate point p1
		p1_trans = p1_trans_rot_trans - rot_center1
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around negative Y-axis)
		rotvec_alpha = alpha * np.array([0,-1,0])
		rotation_alpha = Rotation.from_rotvec(rotvec_alpha)
		p1_trans_rot = rotation_alpha.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point p1
		rot_center2 = np.array([voxels.shape[0]/2, voxels.shape[1]/2, voxels.shape[2]/2])
		if verbose: print("rot_center2:", rot_center2)
		p1_trans_rot_trans = p1_trans_rot + rot_center2
		if verbose: print("p1 after alpha:", p1_trans_rot_trans)

		# Write obj file which shows the 3D object along with the plane of cross-section and the vector from origin indicating the point p1.
		# The cross-section is calculated at p1.
		objfile = open(outputdir + "/cross-sections_rotated.obj","w")
		verts, faces, normals, values = measure.marching_cubes_lewiner(voxels, 0, step_size=1)
		# Write vertices of the object
		for item in verts:
			objfile.write("v {0} {1} {2}\n".format(item[0],item[1],item[2]))
		for i in range(-n,n+1):#(0,n):
			# Write vertices of the plane of cross-section
			if 0 <= int(p1_trans_rot_trans[2]+i*d) < voxels.shape[2]:
				objfile.write("v 0 0" + " " + str(int(p1_trans_rot_trans[2]+i*d)) + "\n")
				objfile.write("v " + str(voxels.shape[0]) + " 0 " + str(int(p1_trans_rot_trans[2]+i*d)) + "\n")
				objfile.write("v " + str(voxels.shape[0]) + " " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2]+i*d)) + "\n")
				objfile.write("v 0 " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2]+i*d)) + "\n")
				# Write vertices of the vector from origin indicating the point p1
				objfile.write("v 0 0 0\n")
				objfile.write("v " + str(p1_trans_rot_trans[0]) + " " + str(p1_trans_rot_trans[1]) + " " + str(p1_trans_rot_trans[2]+i*d) + "\n")
			"""
			if i > 0:
				objfile.write("v 0 0" + " " + str(int(p1_trans_rot_trans[2]-i*d)) + "\n")
				objfile.write("v " + str(voxels.shape[0]) + " 0 " + str(int(p1_trans_rot_trans[2]-i*d)) + "\n")
				objfile.write("v " + str(voxels.shape[0]) + " " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2]-i*d)) + "\n")
				objfile.write("v 0 " + str(voxels.shape[1]) + " " + str(int(p1_trans_rot_trans[2]-i*d)) + "\n")
				# Write vertices of the vector from origin indicating the point p1
				objfile.write("v 0 0 0\n")
				objfile.write("v " + str(p1_trans_rot_trans[0]) + " " + str(p1_trans_rot_trans[1]) + " " + str(p1_trans_rot_trans[2]-i*d) + "\n")
			"""

		# Write faces of the object
		faces = faces+1
		for item in faces:
			objfile.write("f {0} {1} {2}\n".format(item[0],item[1],item[2]))

		# Write faces of the plane of cross-section and of the vector from origin indicating the point p1
		num_verts = len(verts)
		for i in range(-n,n+1):#(0,n):
			if 0 <= int(p1_trans_rot_trans[2]+i*d) < voxels.shape[2]:
				objfile.write("f " + str(num_verts+1) + " " + str(num_verts+2) + " " + str(num_verts+3) + " " + str(num_verts+4) + "\n")
				objfile.write("l " + str(num_verts+5) + " " + str(num_verts+6) + "\n")
				num_verts += 6
			"""
			if i > 0:
				objfile.write("f " + str(num_verts+1) + " " + str(num_verts+2) + " " + str(num_verts+3) + " " + str(num_verts+4) + "\n")
				objfile.write("l " + str(num_verts+5) + " " + str(num_verts+6) + "\n")
				num_verts += 6
			"""

		objfile.close()


		###??? Write planes as multi object obj file.
		###??? Remember to get coordinates in original frame of reference.
		###??? May be, the planes can be written as thinned cube so that a 3D printing addon can calculate area.
		### TO BE DONE

		"""
		### Old block: creates only cross-section and the point of intersection in rotated coordinate system.
		cross_sections = []
		for i in range(0,n):
			if 0 <= int(p1_trans_rot_trans[2]+i*d) <= voxels.shape[2]:
				cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]+i*d)], p1_trans_rot_trans+np.array([0,0,i*d])))
			if i > 0:
				if 0<= int(p1_trans_rot_trans[2]-i*d) <= voxels.shape[2]:
					cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]-i*d)], p1_trans_rot_trans+np.array([0,0,-i*d])))
		"""

		"""
		### Cross-sections and parallel planes (Planes defined by 4 points. Next section is similar, but represents planes by flattened cubes.)
		### Create a data structure cross_sections that contains-
		### > Cross-section
		### > Original point at which cross-section was created (rotated back to original coordinate system)
		### > A set of planes parallel to the cross-section (these can be used to create more cross-sections in blender)
		cross_sections = []
		for i in range(-n,n+1):
			if 0 <= int(p1_trans_rot_trans[2]+i*d) < voxels.shape[2]:
				# Get coordinates of p1_trans_rot_trans at specific z (i.e. cross-section) in original coordinate system.
				# Use reverse translations and rotations to get coordinates in original system.
				p_trans_rot_trans_original = self.trans_rot_trans_rot(point=p1_trans_rot_trans+np.array([0,0,i*d]),
																															angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																															angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																															verbose=False)
				#print("p_trans_rot_trans_original: ", p_trans_rot_trans_original)

				# Get coordinates of end points of plane in original coordinate system.
				# Consider that plane is represented by four points- p1, p2, p3 and p4
				# Use reverse translations and rotations to get coordinates in original system.
				p1 = [0,               0,               p1_trans_rot_trans[2]+i*d]
				p2 = [voxels.shape[0], 0,               p1_trans_rot_trans[2]+i*d]
				p3 = [voxels.shape[0], voxels.shape[1], p1_trans_rot_trans[2]+i*d]
				p4 = [0,               voxels.shape[1], p1_trans_rot_trans[2]+i*d]

				p1_original = self.trans_rot_trans_rot(point=p1,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p2_original = self.trans_rot_trans_rot(point=p2,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p3_original = self.trans_rot_trans_rot(point=p3,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p4_original = self.trans_rot_trans_rot(point=p4,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
																							 
				plane = [p1_original,p2_original,p3_original,p4_original]


				cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]+i*d)], p1_trans_rot_trans+np.array([0,0,i*d]), p_trans_rot_trans_original, plane))
				#cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]+i*d)], p1_trans_rot_trans+np.array([0,0,i*d])))
		"""

		### Cross-sections and parallel planes (Planes defined by 8 points of a flattened cube.)
		### Create a data structure cross_sections that contains-
		### > Cross-section
		### > Original point at which cross-section was created (rotated back to original coordinate system)
		### > A set of flattened cubes (that represent planes) parallel to the cross-section (these can be used to create more cross-sections in blender)
		cross_sections = []
		for i in range(-n,n+1):
			if 0 <= int(p1_trans_rot_trans[2]+i*d) < voxels.shape[2]:
				# Get coordinates of p1_trans_rot_trans at specific z (i.e. cross-section) in original coordinate system.
				# Use reverse translations and rotations to get coordinates in original system.
				p_trans_rot_trans_original = self.trans_rot_trans_rot(point=p1_trans_rot_trans+np.array([0,0,i*d]),
																															angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																															angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																															verbose=False)
				#print("p_trans_rot_trans_original: ", p_trans_rot_trans_original)

				# Get coordinates of end points of plane in original coordinate system.
				# Consider that plane is represented by four points- p1, p2, p3 and p4
				# Use reverse translations and rotations to get coordinates in original system.
				p1 = [0,               0,               p1_trans_rot_trans[2]+i*d]
				p2 = [voxels.shape[0], 0,               p1_trans_rot_trans[2]+i*d]
				p3 = [voxels.shape[0], voxels.shape[1], p1_trans_rot_trans[2]+i*d]
				p4 = [0,               voxels.shape[1], p1_trans_rot_trans[2]+i*d]
				p5 = [0,               0,               p1_trans_rot_trans[2]+i*d + 0.1]
				p6 = [voxels.shape[0], 0,               p1_trans_rot_trans[2]+i*d + 0.1]
				p7 = [voxels.shape[0], voxels.shape[1], p1_trans_rot_trans[2]+i*d + 0.1]
				p8 = [0,               voxels.shape[1], p1_trans_rot_trans[2]+i*d + 0.1]

				p1_original = self.trans_rot_trans_rot(point=p1,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p2_original = self.trans_rot_trans_rot(point=p2,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p3_original = self.trans_rot_trans_rot(point=p3,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p4_original = self.trans_rot_trans_rot(point=p4,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p5_original = self.trans_rot_trans_rot(point=p5,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p6_original = self.trans_rot_trans_rot(point=p6,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p7_original = self.trans_rot_trans_rot(point=p7,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
				p8_original = self.trans_rot_trans_rot(point=p8,
																							 angle1=-alpha, center11=-rot_center2, center12=rot_center1, axis1=np.array([0,-1,0]),
																							 angle2=-theta, center21=-rot_center1, center22=org_center,  axis2=np.array([0,0,1]),
																							 verbose=False)
																							 
				plane = [p1_original,p2_original,p3_original,p4_original,p5_original,p6_original,p7_original,p8_original]


				cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]+i*d)], p1_trans_rot_trans+np.array([0,0,i*d]), p_trans_rot_trans_original, plane))
				#cross_sections.append((voxels[:,:,int(p1_trans_rot_trans[2]+i*d)], p1_trans_rot_trans+np.array([0,0,i*d])))

		return(cross_sections)


		# Return xy-slice of the rotated 3D image at p1
		#return([(voxels[:,:,int(p1_trans_rot_trans[2])], p1_trans_rot_trans)])

	def trans_rot_trans_rot(self, point=None, angle1=None, center11=None, center12=None, axis1=None, angle2=None, center21=None, center22=None, axis2=None, verbose=False):
		### THIS FUNCTION PERFORMS TWO SETS OF TRANSLATION-ROTATION-TRANSLATION SEQUENTIALLY.
		### USEFUL TO GET BACK COORDINATES OF POINTS IN THE ORIGINAL FRAME OF REFERENCE. TO DO SO, PROVIDE TWO TRANSLATION-ROTATION-TRANSLATION SETS IN REVERSE ORDER.
		### THIS REVERSE CALCULATION COULD BE USEFUL TO EMBED POINTS IN ORIGINAL .OBJ FILES.
		
		# Translate point to bring it at center
		p1_trans = point + center11
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around positive Z-axis)
		rotvec_angle1 = angle1 * axis1
		rotation_angle1 = Rotation.from_rotvec(rotvec_angle1)
		p1_trans_rot = rotation_angle1.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point back to take it away from new center
		if verbose: print("center12:", center12)
		p1_trans_rot_trans = p1_trans_rot + center12
		if verbose: print("p1 after angle1:", p1_trans_rot_trans, "\n")

		# Translate point to bring it at center
		p1_trans = p1_trans_rot_trans + center21
		if verbose: print("p1_trans:", p1_trans)
		# Rotate point p1 (Note the rotation around negative Y-axis)
		rotvec_angle2 = angle2 * axis2#np.array([0,-1,0])
		rotation_angle2 = Rotation.from_rotvec(rotvec_angle2)
		p1_trans_rot = rotation_angle2.apply(p1_trans)
		if verbose: print("p1_trans_rot:", p1_trans_rot)
		# Translate point p1
		if verbose: print("rot_center2:", center22)
		p1_trans_rot_trans = p1_trans_rot + center22
		if verbose: print("p1 after alpha:", p1_trans_rot_trans)

		return(p1_trans_rot_trans)

	def get_skeleton_linearfit(self):
		
		if self.downsample_entry.get().isnumeric() and int(self.downsample_entry.get()) != 0:
			self.skel = self.skel_full.downsample(int(self.downsample_entry.get()))#10)
		else:
			self.skel = self.skel_full
		
		print(self.skel.vertices)
		

	def findConnections(self, radius=1000.0, ignore_within=5):
		# Function to find all connections in the self.skel_full.
		# Scans for nodes of high radius in the skeleton and tries to find shortest paths between them.
		# A closeness parameter is necessary so that the algorithm does not consider nodes within a high-radius cluster.

		if self.downsample_entry.get().isnumeric() and int(self.downsample_entry.get()) != 0:
			self.skel = self.skel_full.downsample(int(self.downsample_entry.get()))#10)
		else:
			self.skel = self.skel_full

		def neighborhood(G, node, n):
			# Calculate n-degree neighborhood of a node.
			# Returns list of nodes within the neighborhood (n) of the given node in graph G.
			# NOTE: This function can also be modified to calculate nth degree neighborhood of a node,
			# i.e. nodes that are exactly n steps away from a given node. Just change length <= n to length == n.
			# Similarly if length > n is used as the condition, the function will return complement of the neighborhood.
			# Just modify the condition to get whatever is required.
			path_lengths = nx.single_source_dijkstra_path_length(G, node)
			return [node for node, length in path_lengths.items() if length <= n]

		G = nx.Graph()
		G.add_nodes_from([(i,{'radius':self.skel.radius[i]}) for i in range(0,len(self.skel.vertices))])
		#G.add_nodes_from(list(range(0,len(self.skel.vertices))))
		G.add_edges_from([tuple(x) for x in self.skel.edges])
		
		nodes_selected = {}
		nodes_flagged = set()
		for (r,n) in sorted([(G.node[n]['radius'], n) for n in G.nodes()], reverse=True):
			if r > radius and n not in nodes_flagged:
				s = set(neighborhood(G, n, ignore_within))
				nodes_flagged |= s
				nodes_selected[n] = {'neighborhood': s}

		print(G.nodes())
		print("")
		print("Selected nodes:",nodes_selected)
		print("")

		cnt = 1
		k = sorted(nodes_selected.keys())
		for i in range(0, len(k)):
			for j in range(i+1, len(k)):
				#print(i,j)
				shortest_path = nx.dijkstra_path(G,k[i],k[j])
				print("Path",cnt)
				print("Nodes:", k[i], "-", k[j])
				print("Downsample:",self.downsample_entry.get())
				path_length = 0
				for node_id in range(0,len(shortest_path)-1):
					path_length += np.linalg.norm(self.skel.vertices[shortest_path[node_id]]-self.skel.vertices[shortest_path[node_id+1]])
				print("Path length:",path_length)
				#print("Vertex", ' '.join([str(x) for x in shortest_path]))
				#print("Radius", ' '.join([str(self.skel.radius[i]) for i in shortest_path]))
				print("Node\tRadius\tDegree")
				for n in shortest_path:
					print(str(n)+"\t"+str(self.skel.radius[n])+"\t"+str(G.degree[n]))
				print("")
				cnt += 1

		"""
		# Nth degree neighbourhood of a give  node.
		import networkx as nx
		G = nx.Graph()
		G.add_edges_from([('v1','v2'),('v2','v4'),('v1','v3')])

		def neighborhood(G, node, n):
				path_lengths = nx.single_source_dijkstra_path_length(G, node)
				return [node for node, length in path_lengths.iteritems() if length == n]

		print(neighborhood(G, 'v1', 1))
		# ['v2', 'v3']
		print(neighborhood(G, 'v1', 2))
		# ['v4']
		"""

		del(G)
		del(nodes_selected)
		del(nodes_flagged)


	def erode_images(self):
		###??? DELETE THIS FUNCTION LATER
		#Set 3d images from data loaded from files.
		#Apply erosion to 'threeDmatrix' based on user provided factor. Erosion needs to be performed separately on each segment label.
		#Use eroded 'threeDmatrix' to set 'matrices' variable.
		#Reset 'matrices_original' to updated 'matrices'.

		###? CAUTION: New section.
		### Erode images by a user provided factor.
		for l in self.uniq_labels:
			m = threeDmatrix[threeDmatrix == l]
			m = ndimage.binary_erosion(m, iterations=1).astype(threeDmatrix.dtype)
			

		self.matrices_original = np.copy(self.matrices)


	def load_data(self):
		if self.dirname == "":
			print("No directory selected.")
			return(0)

		a = os.listdir(self.dirname)
		print(a)
		print("***")
		b = sorted_nicely(a)
		print(b)
		print(type(b))

		#return(0)

		# Read PNGs and construct matrix representation of labels
		print ("Loading data...")
		files = []
		for fn in sorted_nicely(os.listdir(self.dirname)):
				if fn.endswith(".png"):
					files.append(os.path.join(self.dirname, fn))
		#files=sorted(files)
		print("Done")

		print("Note: Assuming that all images are of same dimensions.")

		self.threeDmatrix = []
		self.matrices = []

		for k, fn in enumerate(files):
			print(k,fn)
			#continue
			#im_frame = Image.open(fn)
			#matrices.append(np.array(im_frame.getdata()).reshape(im_frame.size[0],im_frame.size[1]))
			#if k % round(skip) == 0: # skips to ensure isotropic matrix
			image = cv2.imread(fn)
			print("###",image.shape)
			#print(np.unique(image))
			#print(np.sum(image[0]-image[1]), np.sum(image[1]-image[2]))
			if len(image.shape) == 3:
				image = image[:,:,0] #Assuming that images are gray scale, i.e. all channels are identical.
			#print(">>>",image.shape, np.array([image]*3).transpose((1,-1,0)).shape)

			h = image.shape[0]
			w = image.shape[1]
			image_dim_threshold = 500
			if (h >= image_dim_threshold or w >= image_dim_threshold) or (h < image_dim_threshold and w < image_dim_threshold):
				if h > w:
					self.image_height = image_dim_threshold
					self.image_width = int((w*image_dim_threshold)/h)
				else:
					self.image_width = image_dim_threshold
					self.image_height = int((h*image_dim_threshold)/w)
				print("Image",k,"is too large, (w,h) = ("+str(w)+","+str(h)+"). Resizing to "+str((self.image_width,self.image_height))+".")
				image_resized = cv2.resize(image,(self.image_width,self.image_height), interpolation = cv2.INTER_NEAREST) # resize without generating intermediate colors/values during interpolation
			else:
				self.image_width = w
				self.image_height = h



			###???CAUTION: Use image_resized in this step for testing skeletonization only. DO NOT use image_resized for final version.
			#self.threeDmatrix.append(image[:,:,0]) # Assuming that images are gray scale. The variable threeDmatrix will be used for skeletonization. Note that images with original resolution are stored here. Useful for quantitatie analysis.
			self.threeDmatrix.append(image) # Assuming that images are gray scale. The variable threeDmatrix will be used for skeletonization. Note that images with original resolution are stored here. Useful for quantitatie analysis.
			#self.threeDmatrix.append(image_resized[:,:,0]) # Comment out this line in final version. Use the above line instead.

			#self.matrices.append(image_resized) # The variable 'matrices' stores images in RGB format. Used in visualization of images. Note that resized images are stored here. Quantitative analysis with these images might not give correct results.
			self.matrices.append(np.array([image_resized]*3).transpose((1,-1,0))) # The variable 'matrices' stores images in RGB format. Used in visualization of images. Note that resized images are stored here. Quantitative analysis with these images might not give correct results.

		print("Original image shape:", image.shape)
		print("Resized image shape:", image_resized.shape)
		#print(">>>",image.shape,self.image_width,self.image_height)

		#Create a original copy of self.matrices. Useful for referring to original segments easily.
		self.matrices_original = np.copy(self.matrices)

		self.threeDmatrix = np.dstack(self.threeDmatrix)


		#"""
		### Detect labels and show as check buttons
		print('Data matrix constructed of size:')
		print(self.threeDmatrix.shape)
		self.uniq_labels = np.unique(self.threeDmatrix)
		print('Identified ' + str(len(self.uniq_labels)-1) + ' segmentations with labels:')
		print(self.uniq_labels[1:])

		### Assign random colors to the segments
		self.colormap = {l:[random.randint(16,255),random.randint(16,255),random.randint(16,255)] for l in self.uniq_labels[1:]}
		self.colormapHex = {}
		for label in self.colormap:
			#print(label, self.colormap[label], )
			self.colormapHex[label] = "#"+''.join([hex(x)[2:] for x in self.colormap[label]])
		print(self.colormap,self.colormapHex)

		#print(self.colormap[97])

		for im in self.matrices:
			#print(im.shape)
			for ch in [0,1,2]:
				#print(im[:,:,ch].shape)
				for l in self.uniq_labels[1:]:
					im[:,:,ch][im[:,:,ch] == l] = self.colormap[l][ch]


		#Configure image slider limits
		#self.image_slider.configure(from_=0)
		self.image_slider.configure(to=len(self.matrices)-1)

		self.image_num_cur = 0
		self.show_image()


		if self.segment_btns != []:
			for i in range(0,len(self.segment_btns)):
				self.segment_btns[i].destroy()
				self.segment_lbls[i].destroy()
				self.segment_color_btns[i].destroy()
			#for b in self.segment_btns:
			#	b.destroy()
			#for b in self.segment_lbls:
			#	b.destroy()
			#for b in self.segment_color_btns:
			#	b.destroy()
		self.segment_vars = []
		self.segment_btns = []
		self.segment_lbls = []
		self.segment_color_btns = []
		i = 0
		for label in self.uniq_labels[1:]:
			self.segment_vars.append(IntVar())

			#self.segment_btns.append(Checkbutton(self.annotation_top_frame.scrollable_frame, bg=self.colormapHex[label], text=str(label)+', RGB:'+' '.join([str(x) for x in self.colormap[label]]), variable=self.segment_vars[i], font=("Arial", 12)))
			self.segment_btns.append(Checkbutton(self.annotation_top_frame.scrollable_frame, variable=self.segment_vars[i], bg=bg_color_1, activebackground=active_bg_color_1, fg=fg_color_3, activeforeground=fg_color_1, highlightthickness=0, font=("Arial", 12)))#, bg=self.colormapHex[label]
			self.segment_lbls.append(Label(self.annotation_top_frame.scrollable_frame, text='Segment '+str(label), bg=bg_color_1, activebackground=active_bg_color_1, fg=fg_color_1, activeforeground=fg_color_1, highlightthickness=0, font=("Arial", 12)))

			### NOTE: the second statement contains an activebackground parameter which is adding 20 to R, G and B; capping at EB (EB = FF-20). This gives an effect of dark colors highlighted to slightly brighter and bright colors highlighted to slightly darker.
			#self.segment_color_btns.append(Button(self.annotation_top_frame.scrollable_frame, bg=self.colormapHex[label], highlightthickness=0, text="", font=("Arial", 4), command=lambda btn_id=i: self.choose_segment_color(btn_id)))#text="Color", bg=bg_color_1, image=self.segment_color_btn_image
			self.segment_color_btns.append(Button(self.annotation_top_frame.scrollable_frame, bg=self.colormapHex[label], activebackground='#'+''.join([hex(x)[2:] if x<=255 else "eb" for x in [int(self.colormapHex[label][i:i+2],base=16)+20 for i in range(1,6,2)]]), highlightthickness=0, text="", width=5, height=3, font=("Arial", 4), command=lambda btn_id=i: self.choose_segment_color(btn_id)))#text="Color", bg=bg_color_1, image=self.segment_color_btn_image
			
			i += 1

		for i in range(0,len(self.uniq_labels[1:])):
			self.segment_btns[i].grid(row=i, column=0, pady=2, sticky=NW)
			self.segment_lbls[i].grid(row=i, column=1, pady=2, sticky=NW)
			self.segment_color_btns[i].grid(row=i, column=2, pady=2, sticky=NE)

		#self.annotation_top_frame.configure(height=self.image_canvas_height)

		#"""

		#self.show_image()




	def set_labels(self, final_erosion=True):
		if self.matrices == []:
			print("No data loaded")
			return(0)
		print("***",np.unique(self.threeDmatrix))
		self.labels = self.threeDmatrix

		"""
		if bool(self.erosion.get()):
			print("Eroding...")
			labels = (self.threeDmatrix == 81) | (self.threeDmatrix == 108)
			labels[labels == 0] = A
			labels[labels == B] = 0
			labels = erode(labels)
			labels[self.labels == B] = B
			labels[self.labels == 0] = 0
		"""

		#"""
		if bool(self.erosion.get()):
			self.labels = np.copy(self.threeDmatrix)
			
			print("Eroding...")
			merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())

			erosion_group = {}
			i = 0
			for m in merge_list:
				for grp in re.findall(r"\((.+?)\)", m):#m.replace(" ","").split(")+("):
					lbls = [int(x) for x in re.split('\+', grp.replace("(","").replace(")",""))]
					for lbl in lbls:
						# Merge labels
						self.labels[self.labels == lbl] = lbls[0]

					erosion_group[lbls[0]] = i
					i += 1

			#(80+107)+(81+108)+109
			print("Erosion groups:")
			for k in erosion_group:
				print("Label",k,", Erosion group",erosion_group[k])

			#80,81,        109
			lbls = list(erosion_group.keys())
			for i in range(0,len(lbls)-1):
				for j in range(i+1,len(lbls)):
					print("Eroding boundaries between",lbls[i],"and",lbls[j])
					region1 = (lbls[i]==self.labels)
					region2 = (lbls[j]==self.labels)
					print(np.sum(region1), np.sum(region2))
					if self.erosioniter_entry.get().strip().isnumeric():
						iterations = int(self.erosioniter_entry.get())
					else:
						iterations = 2
						print("Erosion iterations were not given. Using 2 iterations by default.")
					
					region1_d = scipy.ndimage.binary_dilation(region1, iterations=iterations).astype(region1.dtype)
					region1_2_overlap = (region1_d & region2)
					print(np.sum(region1_d), np.sum(region1_2_overlap))
					self.labels[region1_2_overlap] = 0
			if 'region1' in globals(): del(region1)
			if 'region2' in globals(): del(region2)
			if 'region1_d' in globals(): del(region1_d)
			if 'region1_2_overlap' in globals(): del(region1_2_overlap)
			
			
			###?? TESTING METHOD FOR ERODING SPARSE CONNECTIONS
			#(80+107)+(81+108)+[109]
			erosion_group_sparse = {}
			i = 0
			for m in merge_list:
				for grp in re.findall(r"\[(.+?)\]", m):#m.replace(" ","").split(")+("):
					lbls = [int(x) for x in re.split('\+', grp.replace("[","").replace("]",""))]
					for lbl in lbls:
						# Merge labels
						self.labels[self.labels == lbl] = lbls[0]

					erosion_group_sparse[lbls[0]] = i
					i += 1

			print("Sparse erosion groups:")
			for k in erosion_group:
				print("Label",k,", Sparse erosion group",erosion_group[k])

			lbls_sparse = list(erosion_group_sparse.keys())
			lbls = list(erosion_group.keys())
			for i in range(0,len(lbls_sparse)):
				for j in range(0,len(lbls)):
					print("Eroding sparse connections between",lbls_sparse[i],"and",lbls[j])
					# Convert labels i and j to -1 and +2 so that their sum can become 1
					labels = self.labels.astype(int)
					print(np.unique(labels))
					labels[(labels != lbls_sparse[i]) & (labels != lbls[j])] = 0
					print(np.unique(labels))
					labels[labels == lbls_sparse[i]] = -1
					print(np.unique(labels))
					labels[labels == lbls[j]] = 2
					print(np.unique(labels))
					
					# scipy.ndimage.correlate: use weight matrix like
					# 0,0,0   0,0,0   0,0,0
					# 0,0,0 ; 0,1,1 ; 0,0,0
					# 0,0,0   0,0,0   0,0,0
					# Construct similar matrices for other directions (total 6)
					wx_1 = np.zeros((3,3,3))
					wx_1[0:2,1,1] = 1
					#wx_2 = np.zeros((3,3,3))
					#wx_2[1:3,1,1] = 1

					wy_1 = np.zeros((3,3,3))
					wy_1[1,0:2,1] = 1
					#wy_2 = np.zeros((3,3,3))
					#wy_2[1,1:3,1] = 1
					
					wz_1 = np.zeros((3,3,3))
					wz_1[1,1,0:2] = 1
					#wz_2 = np.zeros((3,3,3))
					#wz_2[1,1,1:3] = 1

					overlap_mask = np.zeros(labels.shape).astype(bool)
					for w in (wx_1,wy_1,wz_1):
						print(np.sum(scipy.ndimage.correlate(labels, w) == 1))
						overlap_mask += scipy.ndimage.correlate(labels, w) == 1
					
					filter_size = 3#3#3#3#3#11
					density_cutoff = 27#20#5#9#1#500#100#11
					pad = int((filter_size-1)/2)
					
					#print(overlap_mask)
					print("Before padding", np.unique(overlap_mask), np.sum(overlap_mask), overlap_mask.shape)
					overlap_mask = np.pad(overlap_mask,((pad,pad),(pad,pad),(pad,pad)))
					#print(overlap_mask)
					print("After padding", np.unique(overlap_mask), np.sum(overlap_mask), overlap_mask.shape)
					overlap_mask = overlap_mask#.astype(bool)
					print("After bool", np.unique(overlap_mask), np.sum(overlap_mask), overlap_mask.shape)

					#labels = np.pad(labels,((pad,pad),(pad,pad),(pad,pad)))

					print(np.transpose(np.nonzero(overlap_mask)))
					tobe_removed = []
					for p in np.transpose(np.nonzero(overlap_mask)):
						#print(p)
						s = np.sum(overlap_mask[p[0]-pad:p[0]+pad,p[1]-pad:p[1]+pad,p[2]-pad:p[2]+pad])
						if s <= density_cutoff:
							tobe_removed.append(p)
					# Remove selected points from self.labels
					for p in tobe_removed:
						self.labels[tuple(p-pad)] = 0
					
					for cnt in range(0,10):
						Image.fromarray(self.labels[:,:,cnt]).save(self.dirname+"/image_"+str(cnt)+".png")

					
					#
					# Get the map of all -1 values and scan it for density of these values.
					# Keep only those values around which the density is above threshold.
					# Try using np.count_nonzero over np.sum while calculating density.
			
				
			"""
			# ??? ERODE junctions between selected labels
			#labels_to_erode = set((2, 8))
			self.labels = np.zeros(self.threeDmatrix.shape, dtype=np.uint8)
			#print(self.labels[0,0,0], type(self.labels[0,0,0]))
			x,y,z = self.threeDmatrix.shape
			print("Data matrix shape:",x,y,z)
			print("Starting erosion loop.")
			for i in range(0,x):
				for j in range(0,y):
					for k in range(0,z):
						e = self.threeDmatrix[i,j,k]
						#print(e, type(e))
						if e and e in erosion_group:#labels_to_erode:#e == l1 or e == l2:
							break_flag = False
							for a in range(-1,2):
								for b in range(-1,2):
									for c in range(-1,2):
										n = self.threeDmatrix[i+a,j+b,k+c]
										if n and n in erosion_group and erosion_group[e] != erosion_group[n]:# and e != n and (n == l1 or n == l2) and e != n:
											#print("Eroding", x, y, z)
											self.labels[i,j,k] = 0
											break_flag = True
											break
										else:
											self.labels[i,j,k] = e
									if break_flag:
										break
								if break_flag:
									break
						else:
							self.labels[i,j,k] = e
				print("X iteration", i)
			print("Erosion done.")
		"""

		#print(">",len(np.where(self.labels == 97)))
		#print(self.labels.shape)


		#####################################################################
		#??? CAUTION: This is a test section, needs to be finalized

		#Use following section to merge all segments before segmentation
		"""		
		print(self.labels.shape)
		self.labels[self.labels != 0] = 1
		print("Unique labels:", np.unique(self.labels))
		"""

		# Use following section to use selected segments
		"""
		i = 0
		m = np.zeros(self.labels.shape, dtype=bool)
		for var in self.segment_vars:
			if var.get():
				l = self.uniq_labels[1:][i]
				print("Adding segment", l, "to skeletonization.")
				m += self.labels == l
			i += 1

		self.labels = self.labels * m
		"""

		# Use following section to merge segments as in merge_list
		merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())
		print("Using merged segments:",merge_list)

		labels_merged = np.zeros(self.labels.shape, dtype=np.uint8)

		print("Assigning new labels to merged segments.")
		new_l = 2
		for m in merge_list:
			print(m)
			print(re.split('\+|\(|\)|\[|\]', m))
			for l in [int(x) for x in re.split('\+|\(|\)|\[|\]', m) if x.isdigit()]:
				#temp = self.labels == l
				#print("***", temp.shape, type(temp))
				#labels_merged += self.labels == l
				labels_merged += scipy.ndimage.binary_fill_holes(self.labels == l)

				#labels_merged[labels_merged == 1] = new_l
				print("Added old label", l, "to new label", new_l)
			
			#Erode the newly labeled segment
			#if False:
			#	labels_merged = scipy.ndimage.binary_erosion(labels_merged, iterations=self.erosion_iter).astype(labels_merged.dtype)
			#	print("Eroded new label", new_l)
			
			#Assign new label
			labels_merged[labels_merged == 1] = new_l
			print("Assigned new label", new_l)
			
			new_l += 1
			print()
		#labels_merged += (self.labels == 97) | (self.labels == 96)
		#labels_merged[labels_merged == 1] == 2
		#labels_merged += self.labels == 19
		#labels_merged[labels_merged == 1] = 3
		#labels_merged += self.labels == 27
		#labels_merged[labels_merged == 1] = 4


		#"""
		# Section for overall erosion of final merged labels
		# This might be needed to remove self-junctions between surfaces. These junctions will cause problems with the skeleton.
		#print("Eroding merged labels")
		#labels_merged = scipy.ndimage.binary_erosion(labels_merged, iterations=2).astype(labels_merged.dtype)
		# iterations = 4 is a good number to start with.
		if final_erosion:
			if self.erosioniter_entry.get().strip().isnumeric():
				iterations = int(self.erosioniter_entry.get())
				#iterations = 4
				labels_merged = scipy.ndimage.binary_erosion(labels_merged, iterations=iterations).astype(labels_merged.dtype)
			else:
				print("Erosion not set or wrong erosion parameter.")
				print("Final erosion is not performed on the merged label. This may cause problems with skeletonization due to self junctions.")
		else:
			print("Final erosion is not performed on the merged label. This may cause problems with skeletonization due to self junctions.")
		#"""


		self.labels = labels_merged
		print("Unique labels:", np.unique(self.labels))
		#object_ids = [int(i) for i in np.unique(self.labels) if i != 0]
		#print("Object ids:", object_ids)





	def set_labels_slow(self):
		if self.matrices == []:
			print("No data loaded")
			return(0)
		print("***",np.unique(self.threeDmatrix))
		self.labels = self.threeDmatrix

		#"""
		if bool(self.erosion.get()):
			print("Eroding...")
			merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())
			erosion_group = {}
			i = 0
			for m in merge_list:
				for grp in re.findall(r"\((.+?)\)", m):#m.replace(" ","").split(")+("):
					for lbl in re.split('\+', grp.replace("(","").replace(")","")):
						erosion_group[int(lbl)] = i
					i += 1

			for k in erosion_group:
				print(k, erosion_group[k])

			# ??? ERODE junctions between selected labels
			#labels_to_erode = set((2, 8))
			self.labels = np.zeros(self.threeDmatrix.shape, dtype=np.uint8)
			#print(self.labels[0,0,0], type(self.labels[0,0,0]))
			x,y,z = self.threeDmatrix.shape
			print("Data matrix shape:",x,y,z)
			print("Starting erosion loop.")
			for i in range(0,x):
				for j in range(0,y):
					for k in range(0,z):
						e = self.threeDmatrix[i,j,k]
						#print(e, type(e))
						if e and e in erosion_group:#labels_to_erode:#e == l1 or e == l2:
							break_flag = False
							for a in range(-1,2):
								for b in range(-1,2):
									for c in range(-1,2):
										n = self.threeDmatrix[i+a,j+b,k+c]
										if n and n in erosion_group and erosion_group[e] != erosion_group[n]:# and e != n and (n == l1 or n == l2) and e != n:
											#print("Eroding", x, y, z)
											self.labels[i,j,k] = 0
											break_flag = True
											break
										else:
											self.labels[i,j,k] = e
									if break_flag:
										break
								if break_flag:
									break
						else:
							self.labels[i,j,k] = e
				print("X iteration", i)
			print("Erosion done.")
		#"""

		#print(">",len(np.where(self.labels == 97)))
		#print(self.labels.shape)


		#####################################################################
		#??? CAUTION: This is a test section, needs to be finalized

		#Use following section to merge all segments before segmentation
		"""		
		print(self.labels.shape)
		self.labels[self.labels != 0] = 1
		print("Unique labels:", np.unique(self.labels))
		"""

		# Use following section to use selected segments
		"""
		i = 0
		m = np.zeros(self.labels.shape, dtype=bool)
		for var in self.segment_vars:
			if var.get():
				l = self.uniq_labels[1:][i]
				print("Adding segment", l, "to skeletonization.")
				m += self.labels == l
			i += 1

		self.labels = self.labels * m
		"""

		# Use followint section to merge segments as in merge_list
		merge_list = re.split('\n|,', self.merge_list_txt.get("1.0",END).strip())
		print("Using merged segments:",merge_list)

		labels_merged = np.zeros(self.labels.shape, dtype=np.uint8)

		print("Assigning new labels to merged segments.")
		new_l = 2
		for m in merge_list:
			print(m)
			print(re.split('\+|\(|\)', m))
			for l in [int(x) for x in re.split('\+|\(|\)', m) if x.isdigit()]:
				temp = self.labels == l
				#print("***", temp.shape, type(temp))
				#labels_merged += self.labels == l
				labels_merged += scipy.ndimage.binary_fill_holes(self.labels == l)

				#labels_merged[labels_merged == 1] = new_l
				print("Added old label", l, "to new label", new_l)
			
			#Erode the newly labeled segment
			#if False:
			#	labels_merged = scipy.ndimage.binary_erosion(labels_merged, iterations=self.erosion_iter).astype(labels_merged.dtype)
			#	print("Eroded new label", new_l)
			
			#Assign new label
			labels_merged[labels_merged == 1] = new_l
			print("Assigned new label", new_l)
			
			new_l += 1
			print()
		#labels_merged += (self.labels == 97) | (self.labels == 96)
		#labels_merged[labels_merged == 1] == 2
		#labels_merged += self.labels == 19
		#labels_merged[labels_merged == 1] = 3
		#labels_merged += self.labels == 27
		#labels_merged[labels_merged == 1] = 4

		self.labels = labels_merged
		print("Unique labels:", np.unique(self.labels))
		#object_ids = [int(i) for i in np.unique(self.labels) if i != 0]
		#print("Object ids:", object_ids)

		"""
		if self.erosion:
			# ??? ERODE junctions between selected labels
			#labels_to_erode = set((2, 8))
			self.labels = np.zeros(self.threeDmatrix.shape, dtype=np.uint8)
			#print(self.labels[0,0,0], type(self.labels[0,0,0]))
			x,y,z = labels_merged.shape
			print(x,y,z)
			for i in range(0,x):
				for j in range(0,y):
					for k in range(0,z):
						e = labels_merged[i,j,k]
						#print(e, type(e))
						if e != 0:#in labels_to_erode:#e == l1 or e == l2:
							break_flag = False
							for a in range(-1,2):
								for b in range(-1,2):
									for c in range(-1,2):
										n = labels_merged[i+a,j+b,k+c]
										if n != 0 and e != n:#n in labels_to_erode and e != n:#(n == l1 or n == l2) and e != n:
											self.labels[i,j,k] = 0
											break_flag = True
											break
										else:
											self.labels[i,j,k] = e
									if break_flag:
										break
								if break_flag:
									break
						else:
							self.labels[i,j,k] = e
			print("Erosion applied to shared boundaries between segments.")
		"""

	def calc_skeleton_from_centroids(self):
		self.set_labels()
		print(self.labels.shape)
		skel = []
		for z in range(0,self.labels.shape[2]):
			img = self.labels[:,:,z]
			if np.sum(img) > 0:
				print(img.shape)
				M = measure.moments(img)
				centroid = [32*M[1, 0] / M[0, 0], 32*M[0, 1] / M[0, 0], 30*z]
				print(centroid)
				skel.append(centroid)
		

		self.skels = {}
		self.skels[1] = cloudvolume.PrecomputedSkeleton.from_path(np.array(skel))


		# Merge skeletons into one skeleton object
		if not self.skels:
			print("No skeleton found")
			return(0)
		skel_keys = sorted(self.skels.keys())
		self.skel_full = self.skels[skel_keys[0]]
		for l in skel_keys[1:]:
			print("Merging skeleton", skel_keys[0], "with skeleton", l, ".")
			self.skel_full = self.skel_full.merge(self.skels[l])

		self.skel_full.radius = np.ones(self.skel_full.radius.shape)
		print("Merged skeleton.")
		print(self.skel_full)
		
		print(self.skel_full.vertices)
		print(self.skel_full.edges)
		print(self.skel_full.radius)
		print(type(self.skel_full.radius))
		
		return(1)
		
		#return(cloudvolume.PrecomputedSkeleton.from_path(np.array(skel)))

			
		
		
	def calc_skeleton(self,
										mip_level='3',
										scale=1,
										const=500,
										pdrf_exponent=4,
										pdrf_scale=100000,
										soma_detection_threshold=1100,
										soma_acceptance_threshold=3500,
										soma_invalidation_scale=1.0,
										soma_invalidation_const=300,
										dust_threshold=1000,
										fix_branching=True,
										progress=False,
										fix_borders=True,
										parallel=1,
										parallel_chunk_size=100):



		# Set self.labels using the merge list
		# ??? NEED REVISION. set_labels is very slow when asked for erosion.
		self.set_labels()

		#####################################################################

		#return(0)

		#self.labels[self.labels != 97] = 0
		#labels[(labels != 90) & (labels != 97)] = 0
		#labels[(labels != 90) & (labels != 96) & (labels != 97)] = 0

		#labels[labels == 90] = 10
		#labels[labels == 96] = 90
		#labels[labels == 97] = 150

		# Take user-inputted conversion factors
		mip = mip_level#"3"#input("Specify the MIP level: ")

		if mip in ["0", "1", "2", "6", "7"]:
				print ("WARNING: You are using an unsupported MIP level and results may not be accurate. Supported levels are 3, 4, and 5.")
				skip = self.mip_dict[mip][0]/self.mip_dict[mip][2]/3
				print ('Using skip factor: '+str(round(skip)))
		else:
				skip = 1

		conv_factors = self.mip_dict[mip]
		nm_x = conv_factors[0]
		nm_y = conv_factors[1]
		nm_z = round(conv_factors[2]*skip) # adjust for anisotropism


		self.labels = np.ascontiguousarray(self.labels.astype(np.uint8))
		print("Created contiguous array (C type) in memory. Unique labels:", np.unique(self.labels))

		#self.labels = scipy.ndimage.binary_fill_holes(self.labels)
		#print("2.Unique labels:", np.unique(self.labels))
		#self.labels = self.labels.astype(np.uint8)
		#print("3.Unique labels:", np.unique(self.labels))

		#view(labels, segmentation=True)

		self.skels = kimimaro.skeletonize(
			self.labels,
			teasar_params={
				'scale': scale,
				'const': const,
				'pdrf_exponent': pdrf_exponent,
				'pdrf_scale': pdrf_scale,
				'soma_detection_threshold': soma_detection_threshold,
				'soma_acceptance_threshold': soma_acceptance_threshold,
				'soma_invalidation_scale': soma_invalidation_scale,
				'soma_invalidation_const': soma_invalidation_const
			},
			object_ids=None,#object_ids,
			dust_threshold=dust_threshold,
			anisotropy=(nm_x,nm_y,nm_z),
			fix_branching=fix_branching,
			progress=progress,
			fix_borders=fix_borders,
			parallel=parallel,
			parallel_chunk_size=parallel_chunk_size
		)

		"""
		###Original section
		self.skels = kimimaro.skeletonize(
			self.labels,
			teasar_params={
				'scale': float(self.kimimaro_scale_entry.get()),#1,#0.1,#4,
				'const': float(self.kimimaro_const_entry.get()),#2000,#500,
				'pdrf_exponent': 4,
				'pdrf_scale': 100000,
				'soma_detection_threshold': 1100,
				'soma_acceptance_threshold': 3500,
				'soma_invalidation_scale': 1.0,
				'soma_invalidation_const': 300,
			},
			dust_threshold=1000,
			anisotropy=(nm_x,nm_y,nm_z),
			fix_branching=True,
			progress=False, # default False, show progress bar
			fix_borders=True, # default True
			parallel=2, # <= 0 all cpu, 1 single process, 2+ multiprocess
			parallel_chunk_size=100 # how many skeletons to process before updating progress bar
		)
		"""

		print("Skeletonization done.")
		print(self.skels)


		# Merge skeletons into one skeleton object
		if not self.skels:
			print("No skeleton found")
			return(0)
		skel_keys = sorted(self.skels.keys())
		self.skel_full = self.skels[skel_keys[0]]
		for l in skel_keys[1:]:
			print("Merging skeleton", skel_keys[0], "with skeleton", l, ".")
			self.skel_full = self.skel_full.merge(self.skels[l])

		print("Merged skeleton.")
		print(self.skel_full)

		#print("=====Centroid skeleton")
		#self.calc_skeleton_from_centroids()

		return(1)

	#def on_press(self, event):
	#	x,y,z = simple_pick_info.pick_info.get_xyz_mouse_click(event, ax)
	#	print(f'Clicked at: x={x}, y={y}, z={z}')
	#	cid = fig.canvas.mpl_connect('button_press_event', on_press)

def quit_me():
	print('quit')
	root.quit()
	root.destroy()

if __name__ == '__main__':
	root = Root()
	root.protocol("WM_DELETE_WINDOW", quit_me)
	root.mainloop()



