from pyquil import Program,get_qc
from pyquil.api import WavefunctionSimulator
from sympy import preview
from numpy import round
import traceback

class ProgramOutput:
    def __init__(self,P=""):
        self.qc = get_qc("9q-square-qvm")
        self.wfs = WavefunctionSimulator()
        P = "\n".join([f"DECLARE s{i} BIT[32]" for i in range(32)]) + P
        P = Program(P)
        P = self.qc.compile(P)
        P = str(P)
        P = P.split("\n")
        self.Program = P
        self.end_line = len(P)
        self.Program = [f"I {i}" for i in range(9)] + self.Program
        #self.Program = [f"DECLARE s{i} BIT[32]" for i in range(32)] + self.Program

    def Burn(self,P):
        try:
            P = "\n".join([f"DECLARE s{i} BIT[32]" for i in range(32)]) + P
            P = Program(P)
            P = self.qc.compile(P)
            P = str(P)
            P = P.split("\n")
            self.Program = P
            self.end_line = len(P)
            self.Program = [f"I {i}" for i in range(9)] + self.Program
            return False
        except:
            return traceback.format_exc()

    def run(self,end_line=None):
        try:
            if end_line is None: end_line = len(self.Program)-41
            P = self.Program[:41 + end_line]
            P = "\n".join(P)
            P = Program(P)
            self.outqc = self.qc.run(P).get_register_map()
            self.outwfs = self.wfs.wavefunction(P)
            self.end_line = end_line
            return False
        except:
            return traceback.format_exc()
    
    def step(self):
        self.end_line = min(self.end_line + 1,len(self.Program)-41)
        self.run(self.end_line)

    def __repr__(self):
        s = [""]
        state = str(self.outwfs)
        if len(state) < 100:
            s.append("State :\t" + state)    
        else:
            s.append("State :\t" + state[:30] + " .... " + state[-30:])
        psi = [self.outwfs[i] for i in range(2**9)]
        s.append("Psi :\t " + str(psi))
        # Registers
        s.append("\nRegisters\n")
        for i in range(32):
            reg = f"s{i}"
            regval = self.outqc[reg][0]
            regval_bin = "".join([str(x) for x in regval])
            regval_int = sum([regval[i]*2**(31-i) for i in range(32)])
            if regval_int > 2**32 : regval_int = regval_int - 2**32
            regval_int = str(regval_int)
            reg_string = reg + "\t : 0b" +  regval_bin + " = " + regval_int
            s.append(reg_string)
        return "\n".join(s)

    def display(self,states=None,regs=range(32),canvas=None,ax=None):
        try:
            psi = [str(round(self.outwfs[i],4)) for i in range(2**9)]
            if states is None:
                psi = [psi[i] + r"& |" + str(i) + r"\rangle" for i in range(2**9) if psi[i]!="0j"]
                if len(psi) > 32:
                    psi = psi[:15] + [r"\vdots"]*2 +  psi[-15:] 
            else:
                psi = [psi[i] + r"& |" + str(i) + r"\rangle" for i in states] + [r"\vdots"]
            psi = r"\begin{bmatrix}" + (r" \\ ").join(psi) + r"\end{bmatrix}"
            s = [r"\text{register} & \text{binary value} & \text{signed decimal}"]
            for i in regs:
                reg = f"s{i}"
                regval = self.outqc[reg][0]
                regval_bin = "".join([str(x) for x in regval])
                regval_int = sum([regval[i]*2**(31-i) for i in range(32)])
                if regval_int > 2**32 : regval_int = regval_int - 2**32
                regval_int = str(regval_int)
                reg_string = reg + " & " +  regval_bin + " & " + regval_int
                s.append(reg_string)
            R = r"\begin{bmatrix}" + r"\\ ".join(s) +r" \end{bmatrix}"
            #P = self.Program[41:]
            #ran = P[:self.end_line]
            #not_ran = P[self.end_line:]
            #ran = [r"\text{" + x + r"}" for x in ran]
            #not_ran = [r"\underline{\text{" + x + r"}}" for x in not_ran]
            #P = ran + not_ran
            #P = r"\\ ".join(P)
            #P = r"\begin{bmatrix}" + P + r"\end{bmatrix}"
            #Full = r"$$ \boxed{\begin{matrix}" + r"P & |\Psi\rangle & C \\" + r" &".join([P,psi,R])+ r"\end{matrix}} $$"
            Full = r"$$ \boxed{\begin{matrix}" + r"|\Psi\rangle & C \\" + r" &".join([psi,R])+ r"\end{matrix}} $$"
            preview(Full,viewer="file",filename="QVMout.png")
            return False
        except:
            return traceback.format_exc()

    def run_and_display(self,i=None):
        self.run(i)
        self.display()

import tkinter as tk
from tkinter import PhotoImage,Button,Text,Label
from threading import Thread

# Create the main window
parent = tk.Tk()
parent.title("9q")
PO = ProgramOutput("")
PO.run_and_display()

image = PhotoImage(file="QVMout.png")
image_label = tk.Label(parent, image=image,borderwidth=5,relief='solid')
def start_tryout():
    compiled_program.configure(bg='yellow')
    compiled_program.bg = 'yellow'
    Thread(target=compute, daemon=True).start()
    # deamon=True is important so that you can close the program correctly

def compute():
    #P = open("QuilProgram.txt",'r').read()
    try:
        compiled_program.delete("1.0",'end')
        P = og_program.get("1.0","end-1c")
        rep = PO.Burn(P)
        if rep is not False:
            compiled_program.insert("end","COMPILATION PROBLEM\n" + rep)
            compiled_program.configure(bg='red')
            compiled_program.bg = 'red'
            return False
        rep = PO.run()
        if rep is not False:
            compiled_program.insert("end","RUNTIME PROBLEM\n" + rep)
            compiled_program.configure(bg='red')
            compiled_program.bg = 'red'
            return False
        rep = PO.display()
        if rep is not False:
            compiled_program.insert("end","RENDERING PROBLEM\n" + rep)
            compiled_program.configure(bg='red')
            compiled_program.bg = 'red'
            return False
        image = PhotoImage(file="QVMout.png")
        image_label.configure(image=image)
        image_label.image = image
        PC = PO.Program[41:]
        compiled_program.configure(bg='light green')
        compiled_program.bg = 'light green'
        compiled_program.insert("end","\n".join(PC))
        return True
    except:
        rep = traceback.format_exc()
        compiled_program.delete("1.0",'end')
        compiled_program.insert("end","GENERAL PROBLEM\n" + rep)
        compiled_program.configure(bg='red')
        compiled_program.bg = 'red'
        return False
og_program_label = Label(parent,text="Program")
compiled_program_label = Label(parent,text="Compiled Program")
output_label = Label(parent,text="States and Memory")
og_program = Text(parent,bg='light yellow',width=30,height=29,borderwidth=3,relief='solid')
compiled_program = Text(parent,bg='light green',width=30,height=29,borderwidth=3,relief='solid')
compile_button=Button(command = start_tryout, text = "Compile and Run",borderwidth=3) ###
og_program_label.grid(row=0,column=0,rowspan=1)
compiled_program_label.grid(row=0,column=1,rowspan=1)
output_label.grid(row=0,column=2,rowspan=1)
og_program.grid(row=1,column=0,rowspan=3,columnspan=1)
compiled_program.grid(row=1,column=1,rowspan=3,columnspan=1)
image_label.grid(row=1,column=2,rowspan=3,columnspan=1)
compile_button.grid(row=4,column=0,columnspan=3,ipadx=580)

n_rows =5
n_columns =3
for i in range(n_rows):
    parent.grid_rowconfigure(i,  weight =1)
for i in range(n_columns):
    parent.grid_columnconfigure(i,  weight =1)
# Start the Tkinter event loop
parent.mainloop()
