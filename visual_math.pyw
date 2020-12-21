from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkinter.colorchooser import askcolor
from tkinter import ttk
from tkinter.ttk import Progressbar
from ctypes import windll
user32 = windll.user32
user32.SetProcessDPIAware()
from win32 import win32gui
import win32con
# from PIL import ImageGrab,ImageTk, Image
import math
import os
import io

import uuid

# import numpy
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')          

main = Tk()
screensize = main.winfo_screenwidth(),main.winfo_screenheight() 
windowWidth = int(0.65 * screensize[0])
windowHeight = int(0.6 * screensize[1])
lineThick = int(0.01 * (screensize[0]+screensize[1])/2)
DPI = windll.user32.GetDpiForWindow(main.winfo_id())
#print(DPI)
#home laptop: uFont = 13, uSpace = 2, mathSpace = 15
#study laptop: uFont = 12, uSpace = 4, mathSpace = 14
uFont = 13
uSpace = 2
mathSize = 13
boxColor = 'green'
canvasColor = 'white'
text_background = 'white'
text_color = 'black'
highlightColor = 'yellow'
lineColor = 'black'
invis = 1.0

main.title("Austin Notes")

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y
class Box(Frame):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color,cursor="target") 
        self.parent = parent
        self.name = uuid.uuid1()
        self.connected_to = []
        self.line_connects = {}
        self.line_id = canvas.create_line(0,0,0,0,width=10, fill=self.color)
        self.frame = None
        self.TLcorner = Point(-1,-1)
        self.w = -1
        self.h = -1
        self.cur_anchor = ''
        self.center = Point(-1,-1)
    def connectTo(self,box):
        if self.name not in box.line_connects and box.name not in self.line_connects: 
            #print('yo')
            self.connected_to.append(box)
            box.connected_to.append(self)
            x1 = self.TLcorner.x + self.w/2
            y1 = self.TLcorner.y + self.h/2
            x2 = box.TLcorner.x + box.w/2
            y2 = box.TLcorner.y + box.h/2
            l1 = canvas.create_line(x1,y1,x2,y2,width=10, fill=lineColor)
            l2 = canvas.create_line(x1,y1,x2,y2,width=10, fill=lineColor)
            self.line_connects[box.name] = l2
            box.line_connects[self.name] = l1
            #print(self.line_connects, box.line_connects)
    #def drawConnections(self):  #used for loading     
    def updateConnections(self): #used when redrawing lines
        for boxes in self.connected_to:
            if boxes.name in self.line_connects:
                l1 = self.line_connects[boxes.name]
                l2 = boxes.line_connects[self.name]
                x1 = self.TLcorner.x + self.w/2
                y1 = self.TLcorner.y + self.h/2
                x2 = boxes.TLcorner.x + boxes.w/2
                y2 = boxes.TLcorner.y + boxes.h/2
                canvas.coords(l1,x1,y1,x2,y2)
                canvas.coords(l2,x1,y1,x2,y2)
                #print(self.line_connects, boxes.line_connects)
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")

class MathBox(Box):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color)
        self.text_list = []
        self.text_list_orig = []
        self.select = None
        self.cursor_row = 0 #row where cursor is
        self.cursor_col = 0 #collum where cursor is
        self.change_home = False
        self.saved_text = ''
        #self.entry = Entry(self,font=14,justify='center')
        #bindtags = self.entry.bindtags()
        #self.entry.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3]))
        #print(str(type(self.entry)))
        self.label = Label(self)

        self.fig = matplotlib.figure.Figure(figsize=(1, 1), dpi=DPI,frameon=False)
        self.fig.set_size_inches(1,1)

        self.ax = plt.Axes(self.fig, [0., 0., 1., 1.])
        self.ax.set_axis_off()
        self.fig.add_axes(self.ax)

        self.fig_frame = FigureCanvasTkAgg(self.fig, master=self.label)
        self.fig_frame.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.fig_frame._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        self.bindEntry()
    def labelClicked(self,event):
        if self.select == None:
            if len(self.text_list) < 1:
                self.enter(1)
                return
            else:
                self.select = 0
                self.cursor_col = 0
        else:
            self.select = None
        self.drawMathText()
    def selectText(self,stuff):
        if len(self.text_list) > 0:
            self.select = 0
            self.cursor_col = 0
            self.drawMathText()
    def addMathArea(self):
            self.label.place(x = lineThick,y=lineThick,width=self.w-(2*lineThick),height=self.h - (2*lineThick)) 
    def addMathText(self,text,pos=-1):
        if pos == -1:
            self.text_list.insert(len(self.text_list),text)
        else:
            self.text_list.insert(pos,text)
    def popMathText(self,pos=-1):
        if len(self.text_list) > 0:
            del self.text_list[pos]
    def clearMathText(self):
        self.text_list.clear()
    def drawMathText(self,letter="",amt=0):
        self.ax.clear()
        if len(self.text_list) <= 0:
            self.fig_frame.draw()
            return
        #CHECK FOR EMPTY FRACTION AND SQRT STUFF
        if letter == "" and self.select != None:
            for x in range(10):
                empty = self.text_list[self.select-1].find("{}")
                num = -1
                if empty == -1:
                    pos = self.select + 1
                    if pos >= len(self.text_list):
                        pos = 0
                    empty = self.text_list[pos].find("{}")
                    num = 1
                if empty != -1:
                    self.text_list[self.select+num] = self.text_list[self.select+num][:empty + 1] + 'x' + self.text_list[self.select+num][empty + 1:]
                else:
                    break
        total = 1.0
        i = (total / len(self.text_list))
        placement = 1 + (0.5/len(self.text_list))
        for count,texts in enumerate(self.text_list):
            placement -= (i)
            if count == self.select and self.select != None:                
                first = texts[:self.cursor_col-amt]+letter
                # print("firsst " + first)
                second = texts[self.cursor_col:]
                # print("second " + second)
                texts = first + "|" + second
                self.text_list[self.select] = first + second
            self.ax.text(0.5,placement,'$' + texts + '$',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=mathSize, color='black',
            transform=self.ax.transAxes)
        try:
            self.fig_frame.draw()
        except:
            print('error typing math')
            self.text_list.pop()
            # self.text_list = self.text_list_orig.copy()
            self.select = 0
            self.drawMathText()
            #messagebox.showerror(title='Error', message='incorrect syntax')
            return
    def bindEntry(self):
        main.bind("<Key>",self.type)
        main.bind("<Return>",self.enter)
        main.bind("<BackSpace>",self.delete)
        main.bind("<space>",self.addSpace)
        main.bind("<Control_L> z",self.selectText)
        main.bind("<Control_L> c",self.copy)
        main.bind("<Control_L> v",self.paste)
        main.bind("<Up>",self.moveUp)
        main.bind("<Down>", self.moveDown)
        main.bind('<Right>',self.moveRight)
        main.bind('<Left>',self.moveLeft)
        self.fig_frame._tkcanvas.bind("<Double-Button-1>",self.labelClicked)
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.fig_frame._tkcanvas.unbind('<Button-1>')
        self.fig_frame._tkcanvas.unbind("<B1-Motion>")
        self.fig_frame._tkcanvas.unbind("<ButtonRelease-1>")
    def type(self,stuff):
        if self.select != None:
            symbols = ['^','_',',','!','@','&','*','(',')','-','=','+','[',']','|',':',';','/','?','.','>','<']
            if stuff.char.isalpha() or stuff.char.isdigit() or stuff.char in symbols:
                drawn_already = False
                drawn_already = self.addText(stuff.char)
                if drawn_already:
                    return
                else:
                    self.drawMathText(letter=stuff.char)
                    self.cursor_col += 1
    def addText(self,char):
        text = self.text_list[self.select]
        mapping = {
            'a':{
                'thet':'\\theta ',
                'delt':'\\Delta ',
                'lambd':"\\lambda ",
                'omeg':'\\Omega ',
                'sigm':"\\sigma "
            },
            'e':{
                'fe':'\\phi '
            },
            'i':{
                'ch':"\\chi ",
                'p':'\\pi '
            },
            'l':{
                'integra':'\\int_{b}^{a}',
                'partia':'\\partial ',
                'nequa':"\\ne ",
                'foral':"\\forall "
            },
            'n':{
                'summatio':'\\sum_{b}^{a}',
                'fractio':'\\frac{a}{b}',
                'withi':"\\in ",
                'neveri':"\\notin ",
                'negatio':"\\neg ",
                'unio':"\\cap ",
                'intersectio':"\\cap "
            },
            'o':{
                'rh':"\\rho "
            },
            'q':{
                'subore':"\\subseteq "
            },
            'r':{
                'exo':"\\oplus "
            },
            's':{
                'implie':"\\implies "
            },
            't':{
                'limi':'\\lim_{a}',
                'sqr':'\\sqrt{a}',
                'lef':'\\leftarrow ',
                'righ':'\\rightarrow ',
                'infini':"\\infty ",
                'gradien':"\\nabla ",
                'conjuc':"\\wedge ",
                'disjuc':"\\vee ",
                'exis':"\\exists ",
                'nevex':"\\nexists ",
                'subse':"\\subset "
            },
            'u':{
                'ta':'\\tau ',
                'm':"\\mu ",
                'n': "\\nu "
            },
            '^':"^{a}",
            "_":"_{a}",
            '*':'\\cdot '
        }
        if char in mapping:
            potential = mapping[char]
            if type(potential) == dict:
                for key in potential:
                    typed = len(key)
                    convert = len(potential[key])
                    if text[self.cursor_col-typed:self.cursor_col] == key:
                        self.drawMathText(amt=typed,letter=potential[key])
                        self.cursor_col += (convert - typed)
                        return True
            elif type(potential) == str:
                print(potential)
                for elem in mapping:
                    if char == elem:
                        
                        self.drawMathText(letter=mapping[elem])
                        self.cursor_col += len(mapping[elem])
                        return True
        else:
            return False
    def delete(self,stuff):
        if self.select != None and self.cursor_col > 0:
            # print(self.text_list[self.select][self.cursor_col-1])
            cursor = self.text_list[self.select][self.cursor_col-1]
            if cursor == "}" or cursor == " ":

                val = self.text_list[self.select].rfind("\\",0,self.cursor_col)
                if val == -1:
                    val = self.text_list[self.select].rfind("^",0,self.cursor_col)
                if val == -1:
                    val = self.text_list[self.select].rfind("_",0,self.cursor_col)
                sub = self.cursor_col - val
                try:
                    self.drawMathText(amt=sub)
                except:
                    val = self.text_list[self.select].rfind("\\",0,self.cursor_col)
                    sub = self.cursor_col - val + "}"
                    self.delete(1)
                    return
                self.cursor_col -= sub
                return
            elif cursor == "{":
                return
            else:
                self.drawMathText(amt=1)
                self.cursor_col -= 1
    def enter(self,stuff):
        if self.select == None:
            self.select = 0
        else:
            if len(self.text_list[self.select]) < 1:
                # print("enter")
                return
            self.select += 1
        self.cursor_col = 0
        self.text_list.insert(self.select,"")
        self.drawMathText(letter="")
    def copy(self,stuff):
        def flash():
            if self["background"] != 'red':
                self.configure(bg='red')
                self.after(300,flash)
            else:
                self.configure(bg=self.color)
                return
        flash()
        if self.select != None:
            self.saved_text = self.text_list[self.select]
        
    def paste(self,stuff):
        def flash():
            if self["background"] != 'blue':
                self.configure(bg='blue')
                self.after(300,flash)
            else:
                self.configure(bg=self.color)
                return
        flash()
        if self.select != None:
            self.drawMathText(letter=self.saved_text)
            self.cursor_col += len(self.saved_text)
        # threading.Thread(target=temp(self)).start()
    def addSpace(self,stuff):
        if self.select != None:
            self.drawMathText(letter="\\hspace{0.5}")
            self.cursor_col += 12
    
    def moveRight(self,stuff): 
        if self.select != None:
            text = self.text_list[self.select]
            if self.cursor_col < len(text):
                char = text[self.cursor_col]
            else:
                char = ""
            if char == "\\" or char == '}' or char == '^' or char == '_' or char == " ":
                space = text.find('}',self.cursor_col + 1)
                end = text.find("hspace",self.cursor_col)
                val1 = text.find("{",self.cursor_col) + 1
                val2 = text.find(' ',self.cursor_col) + 1
                if "hspace" not in text[self.cursor_col:space]:
                    if val1 != 0 and val2 != 0:
                        if val1 < val2:
                            self.cursor_col = val1
                        else:
                            self.cursor_col = val2
                    elif val1 == 0 and val2 != 0:
                        self.cursor_col = val2
                    elif val2 == 0 and val1 != 0:
                        self.cursor_col = val1
                    else:
                        self.cursor_col = len(text) 
                elif val1 < end or val2 < end:
                    if val1 != 0 and val2 != 0:
                        if val1 < val2:
                            self.cursor_col = val1
                        else:
                            self.cursor_col = val2
                    elif val1 == 0 and val2 != 0 and val2 < end:
                        self.cursor_col = val2
                    elif val2 == 0 and val1 != 0 and val1 < end:
                        self.cursor_col = val1
                    else:
                        self.cursor_col = space + 1
                else:
                    self.cursor_col = space + 1
            else:
                self.cursor_col += 1
                if self.cursor_col > len(text):
                    self.cursor_col = 0
            self.drawMathText()
    def moveLeft(self,stuff):
        default = ''
        if self.select != None:
            text = self.text_list[self.select]
            if self.cursor_col - 1 != -1:
                char = text[self.cursor_col - 1]
            else:
                char = ""
            if char == "}": 
                space = text.rfind("\\hspace{0.5}",0,self.cursor_col)
                start = text.rfind("\\",0,self.cursor_col)
                # print(space,start)
                if "hspace" not in text[start:self.cursor_col] or (self.cursor_col - space) != 12:
                    self.cursor_col -= 1
                else:
                    self.cursor_col = space
            elif char == '{' or char == " ":
                val1 = text.rfind('}',0,self.cursor_col)
                val2 = text.rfind("\\",0,self.cursor_col)

                val3 = text.rfind('^',0,self.cursor_col)
                val4 = text.rfind('_',0,self.cursor_col)

                max_val =max([val1,val2,val3,val4])
                if text[max_val - 1] == "}" and max_val - 1 != -1:
                    max_val -= 1
                elif text[max_val - 4:max_val] == "\\int" or text[max_val - 4:max_val] == "\\lim" or text[max_val - 4:max_val] == "\\sum":
                    max_val -= 4
                self.cursor_col = max_val
            else:
                self.cursor_col -= 1
                if self.cursor_col < 0:
                    self.cursor_col = len(text)
                # print('ya')
            print(self.text_list[self.select][:self.cursor_col] + "bb"+self.text_list[self.select][self.cursor_col:])
            self.drawMathText()      
    def moveUp(self,stuff):
        if self.select != None:
            if len(self.text_list[self.select]) < 1:
                # self.text_list = self.text_list[self.select-1:] + self.text_list[self.select:]
                self.text_list.pop(self.select)
            self.select -= 1
            if self.select < 0:
                self.select = len(self.text_list) - 1
            self.cursor_col = 0
            self.drawMathText()   
        #print(self.select)
    def moveDown(self,stuff):
        if self.select != None:
            if len(self.text_list[self.select]) < 1:
                # self.text_list = self.text_list[self.select-1:] + self.text_list[self.select:]
                self.text_list.pop(self.select)
            self.select += 1
            if self.select >= len(self.text_list):
                self.select = 0
            self.cursor_col = 0
            self.drawMathText()
            
mainWindow = Frame(main)
mainWindow.pack(fill="both", expand=True) 
canvas = Canvas(mainWindow, bg=canvasColor,highlightthickness=1,highlightbackground="lightgray")
canvas.pack(fill=BOTH,expand=True)
b1 = MathBox(canvas)
b1.place(x=10,y=20,width=400,height=400)
b1.w = 400
b1.h = 400
b1.addMathArea()
main.mainloop()