#testscript with additional img frame for 2nd image
import customtkinter as ctk
from tkinter import Toplevel
from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.morphology import disk
import csv
from skimage.filters import threshold_otsu
from os import path, mkdir
from glob import glob

script_dir = path.dirname(path.realpath(__file__))
file_path = glob(path.join(script_dir, '*canny_temp_imglist*.txt'))[-1].replace('\\', '/')

### reading file paths
with open(file_path, "r") as file:
    image_paths = file.readlines()
image_paths = [path.strip() for path in image_paths]

### edge detection related functions
first_mask = []
first_img = cv2.cvtColor(cv2.imread(image_paths[0]), cv2.COLOR_BGR2RGB)
mask_er= 0
mask_er_iter = 0

def make_image(img): 
    ### creates a black image   
    dimensions = img.shape
    w, h = dimensions[0], dimensions[1]
    new_img = np.zeros((w, h, 3), dtype = np.uint8)
    return new_img

def enhance_contrast(image, limit, size):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=limit, tileGridSize=size)
    cl = clahe.apply(l_channel)
    limg = cv2.merge((cl,a,b))
    enhanced_img= cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return enhanced_img

def save_fig(totals, method, output_dir, hour):
    ### plots results and writes results to .csv file
    hours = np.arange(0, hour, 1, dtype = int)
    percent = [i*100/totals[0] for i in totals]

    plt.plot(hours, percent, linewidth = 1.5)
    plt.xticks(np.arange(0, hour, 4, dtype = int)) 
    plt.xlabel('time')
    plt.ylabel(f'wound {method} (%)')
    plt.title('Wound closure')
    plt.savefig(f'{output_dir}/quantification_by_{method}.jpg')
    plt.close('all')

    fields = ('timepoint', f'wound_{method}_in_pixel', 'percentage_of_closure')
    filename = f"{output_dir}/quantification_by_{method}_raw_data.csv"
    results = (hours, totals, percent)
    transposed = np.array(results).T.tolist()
    with open(filename, 'w', newline = '') as csvfile: 
        csvwriter = csv.writer(csvfile, dialect='excel') 
        csvwriter.writerow(fields) 
        csvwriter.writerows(transposed)

def first_analyze(self, int_inputs, float_inputs):  
    ### creates mask from the first image
    try:
        inputs_raw = [int(input.get()) for input in int_inputs]+[float(input.get().replace(',', '.')) for input in float_inputs]
        inputs = dict(zip(('contr1', 'contr2', 'edge_er_iter','dil_iter', 'er_iter', 'dil', 'er', 'edge_er'), inputs_raw))
    except ValueError:
        self.error_lab = ctk.CTkLabel(self, text='Error: restrict inputs to integers and decimals', text_color='red')
        self.error_lab.place(relx = 0.4, rely = 0.52)
        self.error_lab.after(3500, self.error_lab.destroy)
    # image preprocessing
    global first_mask
    global first_img  
    global mask_er 
    mask_er = inputs['edge_er']
    global mask_er_iter 
    mask_er_iter= inputs ['edge_er_iter']

    enhanced_img = enhance_contrast(first_img, inputs['contr1'], (inputs['contr2'], inputs['contr2']))
    blur_img = cv2.GaussianBlur(enhanced_img, (9, 9), 0)
    low_thresh = threshold_otsu(cv2.cvtColor(blur_img, cv2.COLOR_BGR2GRAY))
    canny_img = ~cv2.Canny(blur_img, low_thresh, 255)
    padded_img = cv2.copyMakeBorder(canny_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)
    # detecting borders
    dilated_img = cv2.erode(padded_img, disk(inputs['dil']), iterations=inputs['dil_iter']) 
    eroded_img = cv2.dilate(dilated_img, disk(inputs['er']), iterations=inputs['er_iter'])
    contours, hierarchy = cv2.findContours(eroded_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse= True) 
    blank_img = make_image(padded_img) 
    edges_img = cv2.drawContours(image=blank_img, contours=tuple(sorted_contours[:1]), contourIdx=-1, color=(255, 255, 255), 
                                 thickness= -1, lineType=cv2.LINE_AA) 
    first_mask = cv2.cvtColor(cv2.dilate(edges_img, disk(mask_er), iterations=mask_er_iter), cv2.COLOR_RGB2GRAY)
    output_img = cv2.drawContours(image=cv2.copyMakeBorder(first_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
                                  contours=tuple(sorted_contours[:1]), contourIdx=-1, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_AA)
    mask_img = ctk.CTkImage(light_image=Image.fromarray(output_img), size=(400, 400))
    imagewin.image_lab.configure(image = mask_img)
    return first_mask

def second_analyze(self, int_inputs, float_inputs, image_paths, mask_img):
    try:
        inputs_raw = [int(input.get()) for input in int_inputs ]+[float(input.get().replace(',', '.')) for input in float_inputs]
        entries = ('edge_contr1', 'edge_contr2', 'cell_contr1', 'cell_contr2', 'cell_fill', 
                'edge_er', 'edge_dil', 'cell_dil', 'cell_er', 'thresh')
        inputs = dict(zip(entries, inputs_raw))
    except ValueError:
        self.error_lab = ctk.CTkLabel(self, text='Error: restrict inputs to integers\n and decimals', text_color='red')
        self.error_lab.place(relx = 0.55, rely = 0.45)
        self.error_lab.after(3500, self.error_lab.destroy)

    cell_fill = inputs['cell_fill']
    if cell_fill%2 == 0:
        cell_fill += 1 

    mode = self.mode.get()
    global mask_er_iter
    global mask_er

    for file in image_paths[:2]:
        # image preprocessing for edges
        img = cv2.imread(file)
        enhanced_edges = enhance_contrast(img, inputs['edge_contr1'], (inputs['edge_contr2'], inputs['edge_contr2']))
        blur_edges = cv2.GaussianBlur(enhanced_edges, (9, 9), 0)
        canny_edges = ~cv2.Canny(blur_edges, threshold_otsu(cv2.cvtColor(blur_edges, cv2.COLOR_BGR2GRAY)), 255)
        padded_edges = cv2.copyMakeBorder(canny_edges, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)
        overlay_edges = cv2.addWeighted(src1=padded_edges,alpha=0.5,src2=mask_img,beta=0.5,gamma=0)
        binary_edges = cv2.threshold(overlay_edges, 250, 255, cv2.THRESH_BINARY)[1]

        # detecting borders
        dilate_edges = cv2.erode(binary_edges, disk(inputs['edge_dil']), iterations=1)
        erode_edges = cv2.dilate(dilate_edges, disk(inputs['edge_er']), iterations=1)
        contours, hierarchy = cv2.findContours(erode_edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        sorted_contours= sorted(contours, key=cv2.contourArea, reverse= True)
        ind = 0
        range_contours = range(len(sorted_contours))
        for n in range_contours[1:]:
            area = cv2.contourArea(sorted_contours[n])
            if area > 100:
                if area/cv2.contourArea(sorted_contours[n-1]) < inputs['thresh']:
                        ind = n
                        break
            else:
                ind = n
                break

        blank = make_image(erode_edges)
        edges_img = cv2.drawContours(image=blank, contours=tuple(sorted_contours[:ind]), contourIdx=-1, color=(255, 255, 255), thickness= -1, lineType=cv2.LINE_AA)
        mask_img = cv2.cvtColor(cv2.dilate(edges_img, disk(mask_er), iterations=mask_er_iter), cv2.COLOR_BGR2GRAY)

        if mode == 'quantification by area':
            # image preprocessing for cells
            enhanced_cells = enhance_contrast(img, inputs['cell_contr1'], (inputs['cell_contr2'], inputs['cell_contr2']))
            blur_cells = cv2.GaussianBlur(enhanced_cells, (9, 9), 0)
            canny_cells = ~cv2.Canny(blur_cells, threshold_otsu(cv2.cvtColor(blur_cells, cv2.COLOR_BGR2GRAY)), 255)
            padded_cells = cv2.copyMakeBorder(canny_cells, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)
    
            dilate_cells = cv2.erode(padded_cells, disk(inputs['cell_dil']), iterations=1)
            fill_cells = cv2.medianBlur(dilate_cells, cell_fill)
            erode_cells = cv2.dilate(fill_cells, disk(inputs['cell_er']), iterations=1)

            # combining cells and edges
            gray_edges_img = cv2.cvtColor(edges_img, cv2.COLOR_BGR2GRAY)
            combined_img = cv2.addWeighted(src1=gray_edges_img,alpha=0.5,src2=erode_cells,beta=0.5,gamma=0)
            combined_binary_img = cv2.threshold(combined_img, 254, 255, cv2.THRESH_BINARY)[1]
            contours, hierarchy = cv2.findContours(combined_binary_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            output_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
                                      contours=tuple(contours), contourIdx=-1, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_AA)
        
        else:
            output_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
                                      contours=tuple(sorted_contours[:ind]), contourIdx=-1, color=(255, 0, 0), thickness=2, lineType=cv2.LINE_AA)
        
        second_img = ctk.CTkImage(light_image=Image.fromarray(output_img), size=(400, 400))
        imagewin.image_lab.configure(image = second_img)
        self.end_label.place(relx = 0.3, rely = 0.4)
        self.yes_button.place(relx = 0.45, rely = 0.55)
        self.no_button.place(relx = 0.58, rely = 0.55)

def all_analyze(self, int_inputs, float_inputs, scratch_orient, image_paths, mask_img):
    try:
        inputs_raw = [int(input.get()) for input in int_inputs ]+[float(input.get().replace(',', '.')) for input in float_inputs]
        entries = ('edge_contr1', 'edge_contr2', 'cell_contr1', 'cell_contr2', 'cell_fill', 
                'edge_er', 'edge_dil', 'cell_dil', 'cell_er', 'thresh')
        inputs = dict(zip(entries, inputs_raw))

    except ValueError:
        self.error_lab = ctk.CTkLabel(self, text='Error: restrict inputs to integers and floats', text_color='red')
        self.error_lab.place(relx = 0.35, rely = 0.15)
        self.error_lab.after(3500, self.error_lab.destroy)

    hour = 0
    totals = []
    cell_fill = inputs['cell_fill']
    if cell_fill%2 == 0:
        cell_fill += 1 
        
    mode = self.mode.get()
    global mask_er
    global mask_er_iter

    method = 'area' if mode == 'quantification by area' else 'width'
    output_dir = f'{path.dirname(image_paths[0])}/results_{method}'
    if path. isdir(output_dir) == False:
        mkdir(output_dir)

    for file in image_paths:
        # image preprocessing for edges
        img = cv2.imread(file)
        enhanced_edges = enhance_contrast(img, inputs['edge_contr1'], (inputs['edge_contr2'], inputs['edge_contr2']))
        blur_edges = cv2.GaussianBlur(enhanced_edges, (9, 9), 0)
        canny_edges = ~cv2.Canny(blur_edges, threshold_otsu(cv2.cvtColor(blur_edges, cv2.COLOR_BGR2GRAY)), 255)
        padded_edges = cv2.copyMakeBorder(canny_edges, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)
        overlay_edges = cv2.addWeighted(src1=padded_edges,alpha=0.5,src2=mask_img,beta=0.5,gamma=0)
        binary_edges = cv2.threshold(overlay_edges, 250, 255, cv2.THRESH_BINARY)[1]

        # detecting borders
        dilate_edges = cv2.erode(binary_edges, disk(inputs['edge_dil']), iterations=1)
        erode_edges = cv2.dilate(dilate_edges, disk(inputs['edge_er']), iterations=1)
        contours, hierarchy = cv2.findContours(erode_edges, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        sorted_contours= sorted(contours, key=cv2.contourArea, reverse= True)
        ind = 0
        range_contours = range(len(sorted_contours))
        for n in range_contours[1:]:
            area = cv2.contourArea(sorted_contours[n])
            if area > 100:
                if area/cv2.contourArea(sorted_contours[n-1]) < inputs['thresh']:
                        ind = n
                        break
            else:
                ind = n
                break

        blank = make_image(erode_edges)
        edges_img = cv2.drawContours(image=blank, contours=tuple(sorted_contours[:ind]), contourIdx=-1, 
                                     color=(255, 255, 255), thickness= -1, lineType=cv2.LINE_AA)
        mask_img = cv2.cvtColor(cv2.dilate(edges_img, disk(mask_er), iterations=mask_er_iter), cv2.COLOR_BGR2GRAY)
        gray_edges_img = cv2.cvtColor(edges_img, cv2.COLOR_BGR2GRAY)

        if method == 'area':
            # image preprocessing for cells
            enhanced_cells = enhance_contrast(img, inputs['cell_contr1'], (inputs['cell_contr2'], inputs['cell_contr2']))
            blur_cells = cv2.GaussianBlur(enhanced_cells, (9, 9), 0)
            canny_cells = ~cv2.Canny(blur_cells, threshold_otsu(cv2.cvtColor(blur_cells, cv2.COLOR_BGR2GRAY)), 255)
            padded_cells = cv2.copyMakeBorder(canny_cells, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0)
            dilate_cells = cv2.erode(padded_cells, disk(inputs['cell_dil']), iterations=1)
            fill_cells = cv2.medianBlur(dilate_cells, cell_fill)
            erode_cells = cv2.dilate(fill_cells, disk(inputs['cell_er']), iterations=1)

            # combining cells and edges
            combined_img = cv2.addWeighted(src1=gray_edges_img,alpha=0.5,src2=erode_cells,beta=0.5,gamma=0)
            combined_binary_img = cv2.threshold(combined_img, 254, 255, cv2.THRESH_BINARY)[1]
            contours, hierarchy = cv2.findContours(combined_binary_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            output_img  = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
                                      contours=tuple(contours), contourIdx=-1, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
            ### use the following to create output images with wound area filled in red
            # output_fill_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
            #                           contours=tuple(contours), contourIdx=-1, color=(203, 203, 255), thickness=-1, lineType=cv2.LINE_AA)
            # output_nofill_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
            #                           contours=tuple(contours), contourIdx=-1, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
            # output_img = cv2.addWeighted(src1=output_fill_img,alpha=0.5,src2=output_nofill_img,beta=0.5,gamma=0)
            area = cv2.countNonZero(combined_binary_img)
            totals.append(area)
        
        else:
            output_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
                            contours=tuple(sorted_contours[:ind]), contourIdx=-1, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
            # output_fill_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
            #                 contours=tuple(sorted_contours[:ind]), contourIdx=-1, color=(203, 203, 255), thickness=-1, lineType=cv2.LINE_AA)
            # output_nofill_img = cv2.drawContours(image=cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, None, 0), 
            #                 contours=tuple(sorted_contours[:ind]), contourIdx=-1, color=(0, 0, 255), thickness=2, lineType=cv2.LINE_AA)
            # output_img = cv2.addWeighted(src1=output_fill_img,alpha=0.5,src2=output_nofill_img,beta=0.5,gamma=0)
            if scratch_orient == 'hor':
                edges_img = cv2.transpose(edges_img)
            widths = [cv2.countNonZero(row) for row in edges_img[9:-9]]
            mean = sum(widths)/len(widths)
            totals.append(mean)

        cv2.imwrite(f'{output_dir}/timepoint_{hour}.png', output_img)
        hour += 1
    save_fig(totals, method, output_dir, hour)

    self.end_label = ctk.CTkLabel(self, height=100, width=200, text='Processing has been completed', corner_radius=100,
                            bg_color='#2d91e0', text_color='white')
    self.end_label.place(relx = 0.25, rely = 0.4)
    self.end_button = ctk.CTkButton(self, text='OK', fg_color='#104E8B', text_color='white', bg_color='#2d91e0',
                                command=lambda: app.destroy())
    self.end_button.place(relx = 0.41, rely = 0.55)

# GUI related functions
def activate(checkbox_var, widgets):
    state = 'normal' if checkbox_var.get() == 'on' else 'disabled'
    color = 'black' if checkbox_var.get() == 'on' else 'light grey'
    for label, entry in widgets.items():
        label.configure(text_color = color)
        entry.configure(state = state, text_color = color)

def widget_destroy(*args):
    for arg in args:
        arg.place_forget()   
        
def default(widgets):
    for entry, var in widgets.items():
        entry.delete(0, ctk.END)
        entry.insert(0, var)

class App(ctk.CTk):
    def __init__(self, *args, **kwargs): 
        ctk.CTk.__init__(self, *args, **kwargs)
        ctk.set_appearance_mode("System")  
        ctk.set_default_color_theme("blue")  

        # creating a container
        self.container = ctk.CTkFrame(self)
        self.geometry('450x450')
        self.resizable(False, False)
        self.title('Scratch assay analysis')
        self.container.pack(side = "top", fill = "both", expand = True) 
        self.container.grid_rowconfigure(0, weight = 1)
        self.container.grid_columnconfigure(0, weight = 1)

        # initializing frames to an empty array
        self.frames = {}  

        # iterating through a tuple consisting of the different page layouts
        for F in (First, Second, Error):
            frame = F(self.container, self)
            self.frames[F] = frame 
            frame.grid(row = 0, column = 0, sticky ="nsew")
            self.show_frame(First)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class First(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent) 
        self.configure(fg_color = '#e6e8e6')
        
        # defining basic settings variables 
        self.contr1 = ctk.StringVar(value = '30') 
        self.contr2 = ctk.StringVar(value = '30') 
        self.dil = ctk.StringVar(value = '5') 
        self.er = ctk.StringVar(value =  '5.5')
        
        # defining advanced settings variables
        self.edges_er = ctk.StringVar(value = '5.5')
        self.edges_iter = ctk.StringVar(value = '2')
        self.dil_iter = ctk.StringVar(value = '2')
        self.er_iter = ctk.StringVar(value = '2')
        
        # defining additional variables
        self.checkbox_var = ctk.StringVar(value ="off")

        # adding widgets     
        self.set_lab = ctk.CTkLabel(self, height= 50, width = 100, text="Settings for the first wound mask", font=('Arial', 15))
        self.set_lab.place(relx=0.05, rely=0.05)

        self.contr1_lab = ctk.CTkLabel(self, text ="Contrast limit")
        self.contr1_lab.place(relx=0.05, rely=0.2)
        self.contr1_ent = ctk.CTkEntry(self, width = 50, textvariable=self.contr1)
        self.contr1_ent.place(relx = 0.35, rely = 0.2)

        self.contr2_lab = ctk.CTkLabel(self, text="Square grid size")
        self.contr2_lab.place(relx=0.55, rely=0.2)
        self.contr2_ent = ctk.CTkEntry(self, width = 50, textvariable=self.contr2)
        self.contr2_ent.place(relx = 0.85, rely = 0.2)

        self.dil_lab = ctk.CTkLabel(self, text="Dilation rad (dec)")
        self.dil_lab.place(relx=0.05, rely=0.28)
        self.dil_ent = ctk.CTkEntry(self, width = 50, textvariable=self.dil)
        self.dil_ent.place(relx=0.35, rely=0.28)

        self.dil_iter_lab = ctk.CTkLabel(self, text="Iterations", text_color='light grey')
        self.dil_iter_lab.place(relx=0.55, rely=0.28)
        self.dil_iter_ent = ctk.CTkEntry(self, width = 50, textvariable=self.dil_iter, state='disabled', text_color='light grey')
        self.dil_iter_ent.place(relx=0.85, rely=0.28)

        self.er_lab = ctk.CTkLabel(self, text="Erosion rad (dec)")
        self.er_lab.place(relx=0.05, rely=0.36)
        self.er_ent = ctk.CTkEntry(self, width = 50, textvariable=self.er)
        self.er_ent.place(relx=0.35, rely=0.36)
                
        self.er_iter_lab = ctk.CTkLabel(self, text="Iterations", text_color='light grey')
        self.er_iter_lab.place(relx=0.55, rely=0.36)
        self.er_iter_ent = ctk.CTkEntry(self, width = 50, textvariable=self.er_iter, state='disabled', text_color='light grey')
        self.er_iter_ent.place(relx=0.85, rely=0.36)

        self.edges_lab = ctk.CTkLabel(self, text="Mask erosion rad\n(dec)", text_color='light grey')
        self.edges_lab.place(relx=0.05, rely=0.44)
        self.edges_ent = ctk.CTkEntry(self, width = 50, textvariable=self.edges_er, state='disabled', text_color='light grey')
        self.edges_ent.place(relx=0.35, rely=0.44)
        
        self.edges_iter_lab = ctk.CTkLabel(self, text ="Iterations", text_color = 'light grey')
        self.edges_iter_lab.place(relx=0.55, rely=0.44)
        self.edges_iter_ent = ctk.CTkEntry(self, width = 50, textvariable=self.edges_iter, state='disabled', text_color='light grey')
        self.edges_iter_ent.place(relx=0.85, rely=0.44)

        self.scratch_orient = ctk.StringVar(value='hor')
        
        # adding buttons
        self.widgets = dict(zip((self.edges_lab, self.edges_iter_lab, self.dil_iter_lab, self.er_iter_lab), 
                                (self.edges_ent, self.edges_iter_ent, self.dil_iter_ent, self.er_iter_ent)))
        self.checkbox = ctk.CTkCheckBox(self, text="Apply advanced settings", variable=self.checkbox_var, onvalue="on", offvalue="off", 
                                        command=lambda: activate(self.checkbox_var, self.widgets))
        self.checkbox.place(relx=0.05, rely=0.65)

        self.int_entries = (self.contr1_ent, self.contr2_ent, self.edges_iter_ent, self.dil_iter_ent, self.er_iter_ent)
        self.fl_entries = (self.dil_ent, self.er_ent, self.edges_ent)
        self.button_apply = ctk.CTkButton(self, text="Apply", fg_color='#104E8B', width = 70, 
                                          command=lambda: first_analyze(self, self.int_entries, self.fl_entries))
        self.button_apply.place(relx=0.6, rely=0.9)
        
        self.button_next = ctk.CTkButton(self, text="Next", fg_color='#104E8B', width = 70,
                                         command=lambda: controller.show_frame(Error) if len(first_mask)== 0 else controller.show_frame(Second))
        self.button_next.place(relx=0.8, rely=0.9)
        
        default_entries = {self.contr1_ent:'30', self.contr2_ent:'30', self.dil_ent:'5', self.dil_iter_ent:'2', 
                           self.er_ent:'5.5', self.er_iter_ent:'2', self.edges_ent:'5.5', self.edges_iter_ent:'2'}
        self.button_default = ctk.CTkButton(self, text="Default", fg_color='#104E8B', width = 70, command=lambda: default(default_entries))
        self.button_default.place(relx=0.8, rely=0.025)

class Second(ctk.CTkFrame):
    def __init__(self, parent, controller):
     
        ctk.CTkFrame.__init__(self, parent)
        self.configure(fg_color = '#e6e8e6')

        # defining basic settings variables
        self.edge_contr1 = ctk.StringVar(value='30')
        self.edge_contr2 = ctk.StringVar(value='30')
        self.cell_contr1 = ctk.StringVar(value='20')
        self.cell_contr2 = ctk.StringVar(value='20')
        self.edge_dil = ctk.StringVar(value='5')
        self.edge_er = ctk.StringVar(value='5.5')
        self.cell_fill = ctk.StringVar(value='25')

        # defining advanced settings variables
        self.cell_dil = ctk.StringVar(value='3')
        self.cell_er = ctk.StringVar(value='3')
        self.mask_er = ctk.StringVar(value='5')
        self.mask_er_iter = ctk.StringVar(value='1')
        self.thresh = ctk.StringVar(value='0.15')

        # defining additional variables
        self.advanced_set = ctk.StringVar(value='off')
        self.scratch_orient = ctk.StringVar(value='hor')
        self.mode = ctk.StringVar(value = 'quantification by area')
        
        # adding widgets
        self.edge_lab = ctk.CTkLabel(self, width = 100, height = 50, text ="Settings for wound boundary detection",font = ('Arial', 15))
        self.edge_lab.place(relx = 0.05, rely = 0.05)
        
        self.edge_contr1_lab = ctk.CTkLabel(self, text ="Contrast limit")
        self.edge_contr1_lab.place(relx = 0.05, rely = 0.15)
        self.edge_contr1_ent = ctk.CTkEntry(self, width = 50, textvariable= self.edge_contr1)
        self.edge_contr1_ent.place(relx = 0.35, rely = 0.15)
        
        self.edge_contr2_lab = ctk.CTkLabel(self, text ="Square grid size") 
        self.edge_contr2_lab.place(relx = 0.55, rely = 0.15)
        self.edge_contr2_ent = ctk.CTkEntry(self, width = 50, textvariable= self.edge_contr2)
        self.edge_contr2_ent.place(relx = 0.85, rely = 0.15)
        
        self.edge_dil_lab = ctk.CTkLabel(self, text ="Dilation rad (dec)")
        self.edge_dil_lab.place(relx = 0.05, rely = 0.23)
        self.edge_dil_ent = ctk.CTkEntry(self, width = 50, textvariable= self.edge_dil)
        self.edge_dil_ent.place(relx = 0.35, rely = 0.23)
        
        self.edge_er_lab = ctk.CTkLabel(self, text ="Erosion rad (dec)")
        self.edge_er_lab.place(relx = 0.05, rely = 0.31)
        self.edge_er_ent = ctk.CTkEntry(self, width = 50, textvariable= self.edge_er)
        self.edge_er_ent.place(relx = 0.35, rely = 0.31)
        
        self.thresh_lab = ctk.CTkLabel(self, text ="Threshold", text_color = 'light grey')
        self.thresh_lab.place(relx = 0.05, rely = 0.39)
        self.thresh_ent = ctk.CTkEntry(self, width = 50, textvariable= self.thresh, text_color = 'light grey')
        self.thresh_ent.place(relx = 0.35, rely = 0.39)

        self.cell_lab = ctk.CTkLabel(self, width = 100, height = 50, text ="Settings for cells detection", font = ('Arial', 15))
        self.cell_lab.place(relx = 0.05, rely = 0.47)

        self.cell_contr1_lab = ctk.CTkLabel(self, text ="Contrast limit")
        self.cell_contr1_lab.place(relx = 0.05, rely = 0.57)
        self.cell_contr1_ent = ctk.CTkEntry(self, width = 50, textvariable= self.cell_contr1)
        self.cell_contr1_ent.place(relx = 0.35, rely = 0.57)
        
        self.cell_contr2_lab = ctk.CTkLabel(self, text ="Square grid size")
        self.cell_contr2_lab.place(relx = 0.55, rely = 0.57)
        self.cell_contr2_ent = ctk.CTkEntry(self, width = 50, textvariable= self.cell_contr2)
        self.cell_contr2_ent.place(relx = 0.85, rely = 0.57)
        
        self.cell_fill_lab = ctk.CTkLabel(self, text ="Cells filling rad")
        self.cell_fill_lab.place(relx = 0.05, rely = 0.65)
        self.cell_fill_ent = ctk.CTkEntry(self, width = 50, textvariable= self.cell_fill)
        self.cell_fill_ent.place(relx = 0.35, rely = 0.65)

        self.cell_dil_lab = ctk.CTkLabel(self, text ="Dilation rad (dec)", text_color = 'light grey')
        self.cell_dil_lab.place(relx = 0.05, rely = 0.73)
        self.cell_dil_ent = ctk.CTkEntry(self, width = 50, textvariable= self.cell_dil, text_color = 'light grey')
        self.cell_dil_ent.place(relx = 0.35, rely = 0.73)
        
        self.cell_er_lab = ctk.CTkLabel(self, text ="Erosion rad (dec)", text_color = 'light grey')
        self.cell_er_lab.place(relx = 0.05, rely = 0.81)
        self.cell_er_ent = ctk.CTkEntry(self, width = 50, textvariable= self.cell_er, text_color = 'light grey')
        self.cell_er_ent.place(relx = 0.35, rely = 0.81)

        # adding buttons
        self.lab_tuple = (self.cell_dil_lab, self.cell_er_lab, self.thresh_lab)
        self.entry_tuple = (self.cell_dil_ent, self.cell_er_ent, self.thresh_ent)

        self.checkbox_advanced = ctk.CTkCheckBox(self, text="Apply advanced settings", variable=self.advanced_set, onvalue="on", offvalue="off", 
                                        command=lambda: activate(self.advanced_set, dict(zip(self.lab_tuple, self.entry_tuple))))
        self.checkbox_advanced.place(relx = 0.05, rely = 0.9)
        
        self.checkbox_scratch = ctk.CTkCheckBox(self, text="Scratch is horizontal", variable=self.scratch_orient, onvalue="vert", offvalue="hor")
        self.checkbox_scratch.place(relx = 0.55, rely = 0.82)
        
        self.optionmenu = ctk.CTkOptionMenu(self, values = ['quantification by area', 'quantification by width'], variable = self.mode, anchor = 'center')
        self.optionmenu.place(relx = 0.55, rely = 0.72)
        
        self.button_back = ctk.CTkButton(self, text ="Back", fg_color = '#104E8B', width = 70, command=lambda : controller.show_frame(First))
        self.button_back.place(relx = 0.6, rely = 0.9)
        
        self.int_entries = (self.edge_contr1_ent, self.edge_contr2_ent, self.cell_contr1_ent, self.cell_contr2_ent, 
                            self.cell_fill_ent)
        self.fl_entries = (self.edge_er_ent, self.edge_dil_ent, self.cell_dil_ent, self.cell_er_ent, self.thresh_ent)

        self.button_apply = ctk.CTkButton(self, text ="Apply", fg_color = '#104E8B', width = 70, 
                                          command=lambda: second_analyze(self, self.int_entries, self.fl_entries, image_paths, first_mask))
        self.button_apply.place(relx = 0.8, rely = 0.9)

        self.default_entries = {self.edge_contr1_ent:'30', self.edge_contr2_ent:'30', self.cell_contr1_ent:'20', self.cell_contr2_ent:'20', 
                           self.edge_dil_ent:'5', self.edge_er_ent:'5.5', self.cell_dil_ent:'3', self.cell_er_ent:'3', self.cell_fill_ent:'25', 
                           self.thresh_ent:'0.15'}
        
        self.button_default = ctk.CTkButton(self, text="Default", fg_color='#104E8B', width = 70, command=lambda: default(self.default_entries))
        self.button_default.place(relx=0.8, rely=0.025)

        self.end_label = ctk.CTkLabel(self, height=100, width=200, text='Is the result satisfactory?', corner_radius=100,
                                        bg_color='#2d91e0', text_color='white')
        

        self.yes_button = ctk.CTkButton(self, width = 50, text='Yes', fg_color='#104E8B', text_color='white', bg_color='#2d91e0',
                            command=lambda: all_analyze(self, self.int_entries, self.fl_entries, self.scratch_orient.get(), image_paths, first_mask))
            

        self.no_button = ctk.CTkButton(self, width = 50, text='No', fg_color='#104E8B', text_color='white', bg_color='#2d91e0',
                            command=lambda: widget_destroy(self.no_button, self.yes_button, self.end_label))
            
class Error(ctk.CTkFrame):
    def __init__(self, parent, controller):
        
        ctk.CTkFrame.__init__(self, parent) 
        self.configure(fg_color = '#e6e8e6')

        self.label = ctk.CTkLabel(self, text = 'Please press Apply before proceeding!', text_color = 'red')
        self.label.place(relx = 0.35, rely = 0.4)
        
        self.button = ctk.CTkButton(self, text = 'OK', command = lambda: controller.show_frame(First))
        self.button.place(relx = 0.4, rely = 0.5)

class ImageWin(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.geometry('500x500')
        self.title('Output Image')
        self.wm_attributes('-toolwindow', 'True')
        global first_img
        self.image = ctk.CTkImage(light_image=Image.fromarray(first_img), size = (400, 400))
        self.image_lab = ctk.CTkLabel(self, image=self.image, text='')
        self.image_lab.place(relx = 0, rely = 0)

# Driver Code
app = App()
imagewin = ImageWin(app)
app.mainloop()