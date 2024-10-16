if __name__=="__main__":
    import os
    try:os.system("docker run --rm -it -p 5555:5555 rigetti/quilc -P -S")
    except:pass
    try:os.system("docker run --rm -it -p 5000:5000 rigetti/qvm -S")
    except:pass
    try:os.system("pip install numpy pyquil sympy")
    except:pass
from pyquil import Program,get_qc
from pyquil.api import WavefunctionSimulator
from numpy import round
from sympy import preview
import traceback
from numpy import round
import tkinter as tk
from threading import Thread

REG_MAP = {
    "at":"s31","1":"s31",
    "k0":"s30","26":"s30",
    "k1":"s29","27":"s29",
    "ra":"s28","31":"s28",
    "fp":"s27","30":"s27",
    "sp":"s26","29":"s26",
    "gp":"s25","28":"s25",

    "zero":"s24","0":"s24",

    "v0":"s8","2":"s8",
    "v1":"s9","3":"s9",
    "a0":"s10","4":"s10",
    "a1":"s11","5":"s11",
    "a2":"s12","6":"s12",
    "a3":"s13","7":"s13",
}
for i in range(10):REG_MAP[f"t{i}"]=f"s{14+i}"
for i in range(8):REG_MAP[f"{8+i}"]=f"s{14+i}"
REG_MAP["24"]="s22"
REG_MAP["25"]="s23"
for i in range(8):REG_MAP[f"s{i}"]=f"s{i}"
for i in range(8):REG_MAP[f"{16+i}"]=f"s{i}"

QUBITS = 9
def extract_inst(inst,qc=None):
    global REG_MAP,QUBITS
    inst = inst.split("#")[0]
    inst = inst.strip()
    if not inst:return ""
    if len(inst.split(":")) > 1:
        return "\n".join(["LABEL @" + x for x in inst.split(":") if x.strip()])
    inst,arg = inst.split(" ")
    inst = inst.upper()
    arg = arg.split(",")
    new_arg = []
    regs = 0
    for x in arg:
        if x[0] == "$": #reg
            regs += 1
            new_arg.append(REG_MAP[x[1:]])
        else:
            new_arg.append(x)
    if inst == "J":return f"JUMP @{new_arg[0]}"
    elif inst[:5] == "GATE_":
        x = new_arg[0]
        x = int(x)
        assert x>=0 and x<QUBITS,x
        toret = f"{inst[5:]} {x}"
        if qc is not None:
            toret = Program(toret)
            toret = qc.compile(toret)
            toret = str(toret)
        return toret
    elif inst == "MEASURE":
        if len(new_arg)==1:
            x = new_arg[0]
            x = int(x)
            assert x>=0 and x<QUBITS,x
            return f"MEASURE {x}"
        else:
            x,y,z = new_arg
            x = int(x)
            z = int(z)
            assert x>=0 and x<QUBITS,x
            assert z>=0 and z<32
            return f"MEASURE {x} {y}[{z}]"
    else:z,x,y = new_arg

    if regs == 3:
        return f"${inst}REG({z},{x},{y})"
    elif inst == "ADDI":
        y = int(y)
        if y == 1 and z==x:return f"$INCREG({z})"
        elif y == -1 and z==x:return f"$DECREG({z})"
        elif x == "s24":return f"$MOVI({z},{y})"
        else: return f"$ADDI({z},{x},{y})"
    elif regs == 2:
        return f"${inst}({z},{x},{y})"
    else:
        print(f"unknown instrucion {inst}({','.join(arg)})")

def ANDREG(arg):
    x,y = arg.split(",")
    return "\n".join([f"AND {x}[{i}] {y}[{i}]" for i in range(32)])

def ORREG(arg):
    x,y = arg.split(",")
    return "\n".join([f"IOR {x}[{i}] {y}[{i}]" for i in range(32)])

def NOTREG(arg):
    x = arg
    return "\n".join([f"NOT {x}[{i}]" for i in range(32)])

def ADDREG(arg):
    t = arg.split(",")
    if len(t) == 2:
        x,y = t
        z = x
    else: z,x,y = t
    #reserve reg s31 for special things
    cin = "s31[31]"
    s = "s31[30]"
    cout = "s31[29]"
    temp1 = "s31[28]"
    temp2 = "s31[27]"
    L = [f"MOVE {cin} 0"]
    for i in range(31,-1,-1):
        xi = f"{x}[{i}]"
        yi = f"{y}[{i}]"
        zi = f"{z}[{i}]"
        # temp1 = xi XOR yi
        # s = cin XOR temp1
        # temp2 = xi AND yi
        # cout = temp2 OR (temp1 AND cin)
        L = L + [
        f"MOVE {temp1} {xi}",
        f"MOVE {temp2} {xi}",
        f"XOR {temp1} {yi}",
        f"AND {temp2} {yi}",
        f"MOVE {s} {cin}",
        f"XOR {s} {temp1}",
        f"MOVE {cout} {cin}",
        f"AND {cout} {temp1}",
        f"IOR {cout} {temp2}",
        f"MOVE {zi} {s}",
        f"MOVE {cin} {cout}"
        ]
    return "\n".join(L)

def MOVI(arg):
    reg,val = arg.split(",")
    val = int(val)
    val = "{:032b}".format(val%2**32)
    L = []
    for i in range(32):
        if val[i] == '0':
            L.append(f"MOVE {reg}[{i}] 0")
        elif val[i] == "1":
            L.append(f"MOVE {reg}[{i}] 1")
        else:
            raise ValueError()
    return "\n".join(L)

def MOVREG(arg):
    x,y = arg.split(",")
    return "\n".join([f"MOVE {x}[{i}] {y}[{i}]" for i in range(32)])

def INCREG(arg):
    x = arg
    c = "s31[31]"
    co = "s31[30]"
    L = [f"MOVE {c} 1",f"MOVE {co} 1"]
    for i in range(31,-1,-1):
        xi = f"{x}[{i}]"
        L.extend([
        f"AND {co} {xi}",
        f"XOR {xi} {c}",
        f"MOVE {c} {co}",
        ])
    return "\n".join(L)

def DECREG(arg):
    x = arg
    c = "s31[31]"
    co = "s31[30]"
    L = [f"MOVE {c} 1",f"MOVE {co} 1"] #co is always c
    for i in range(31,-1,-1):
        xi = f"{x}[{i}]"
        L.extend([
        f"MOVE {co} {xi}",
        f"NOT {co}",
        f"AND {co} {c}"
        f"XOR {xi} {c}",
        f"MOVE {c} {co}",
        ])
    return "\n".join(L)

def SUBREG(arg):
    t = arg.split(",")
    if len(t)==2:
        x,y=t
        z = x
    else:z,x,y = t
    #reserve reg s31 for special things
    cin = "s31[31]"
    s = "s31[30]"
    cout = "s31[29]"
    temp1 = "s31[28]"
    temp2 = "s31[27]"
    L = [f"MOVE {cin} 1"] #since we are substracting
    for i in range(31,-1,-1):
        xi = f"{x}[{i}]"
        yi = f"{y}[{i}]"
        zi = f"{z}[{i}]"
        # temp1 = xi XOR yi
        # s = cin XOR temp1
        # temp2 = xi AND yi
        # cout = temp2 OR (temp1 AND cin)
        L = L + [
        f"NOT {yi}", #basically, using the bits in ~y
        f"MOVE {temp1} {xi}",
        f"MOVE {temp2} {xi}",
        f"XOR {temp1} {yi}",
        f"AND {temp2} {yi}",
        f"MOVE {s} {cin}",
        f"XOR {s} {temp1}",
        f"MOVE {cout} {cin}",
        f"AND {cout} {temp1}",
        f"IOR {cout} {temp2}",
        f"MOVE {zi} {s}",
        f"MOVE {cin} {cout}",
        f"NOT {yi}", #correcting what we changed
        ]
    return "\n".join(L)

def NEQREG(arg):
    z,x,y = arg.split(",")
    #sets z = 1 if y==x
    L = [f"MOVE {z} 0"]
    for i in range(32):
        L.extend([
        f"MOVE s31[31] {x}[{i}]",
        f"XOR s31[31] {y}[{i}]",
        f"IOR {z} s31[31]",
        ])
    return "\n".join(L)

def BEQ(arg):
    x,y,z = arg.split(",")
    return NEQREG(f"s31[30],{x},{y}") + "\n" + f"JUMP-UNLESS @{z} s31[30]"

def BNE(arg):
    x,y,z = arg.split(",")
    return NEQREG(f"s31[30],{x},{y}") + "\n" + f"JUMP-WHEN @{z} s31[30]"

def SLTREG(arg):
    z,x,y = arg.split(",")
    L = [SUBREG(f"{z},{x},{y}")]
    L.append(f"MOVE {z}[{31}] {z}[{0}]")
    for i in range(30,-1,-1):
        L.append(f"MOVE {z}[{i}] 0")
    return "\n".join(L)

def SGTREG(arg):
    z,x,y = arg.split(",")
    L = [SUBREG(f"{z},{x},{y}")]
    L.append(f"MOVE {z}[{31}] {z}[{0}]")
    for i in range(30,-1,-1):
        L.append(f"MOVE {z}[{i}] 0")
    return "\n".join(L)

def ADDI(arg):
    t = arg.split(",")
    if len(t) == 2:
        x,y = t
        z = x
    else:
        z,x,y = t
    if z!=x:
        return MOVI(f"{z},{y}") + "\n" + ADDREG(f"{z},{x}")
    else:
        return MOVI(f"s30,{y}") + "\n" + ADDREG(f"{z},s30")

def SLL(arg):
    t = arg.split(",")
    if len(t)==2:
        x,y = t
        z = x
    else:
        z,x,y = t
    y = int(y)
    L = []
    for i in range(32-y):L.append(f"MOVE {z}[{i}] {x}[{i+y}]")
    for i in range(32-y,32):L.append(f"MOVE {z}[{i}] 0")
    return "\n".join(L)

def SRL(arg):
    t = arg.split(",")
    if len(t)==2:
        x,y = t
        z = x
    else:
        z,x,y = t
    y = int(y)
    L = []
    for i in range(31,y-1,-1):L.append(f"MOVE {z}[{i}] {x}[{i-y}]")
    for i in range(y-1,-1,-1):L.append(f"MOVE {z}[{i}] 0")
    return "\n".join(L)

def SRA(arg):
    t = arg.split(",")
    if len(t)==2:
        x,y = t
        z = x
    else:
        z,x,y = t
    y = int(y)
    L = []
    for i in range(31,y-1,-1):L.append(f"MOVE {z}[{i}] {x}[{i-y}]")
    for i in range(y-1,-1,-1):L.append(f"MOVE {z}[{i}] {x}[0]")
    return "\n".join(L)


QUILE_TO_QUIL = {
    "ANDREG":ANDREG,
    "ADDREG":ADDREG,
    "ORREG":ORREG,
    "NOTREG":NOTREG,
    "MOVREG":MOVREG,
    "INCREG":INCREG,
    "DECREG":DECREG,
    "SUBREG":SUBREG,
    "NEQREG":NEQREG,
    "SLTREG":SLTREG,
    "SGTREG":SGTREG,
    "MOVI":MOVI,
    "ADDI":ADDI,
    "SLL":SLL,
    "SRL":SRL,
    "SLA":SLL,
    "SRA":SRA,
    "BEQ":BEQ,
    "BNE":BNE,
}

def preprocline(line):
    global QUILE_TO_QUIL
    if not line.strip():return ""
    if line[0] != "$":return line
    line = line[1:]
    inst,arg = line.split("(")
    assert arg[-1] == ")"
    arg = arg[:-1]
    f = QUILE_TO_QUIL[inst]
    s = f(arg)
    return s

def preproc(P):
    global preprocline
    P = P.split("\n")
    P = [preprocline(line) for line in P]
    P = "\n".join(P)
    return P

class ProgramOutput:
    def __init__(self,P="",qc_name="9q-square-qvm"):
        global preproc
        self.qc = get_qc(qc_name)
        self.wfs = WavefunctionSimulator()
        P = preproc(P)
        P = "\n".join([f"DECLARE s{i} BIT[32]" for i in range(32)]) +"\n" + P
        P = Program(P)
        #P = self.qc.compile(P)
        P = str(P)
        P = P.split("\n")
        self.Program = P
        self.end_line = len(P)
        self.Program = [f"I {i}" for i in range(9)] + self.Program

    def Burn(self,P):
        try:
            P = preproc(P)
            P = "\n".join([f"DECLARE s{i} BIT[32]" for i in range(32)]) + "\n" + P
            P = Program(P)
            P = str(P)
            P = P.split("\n")
            self.Program = P
            self.end_line = len(P)
            self.Program = [f"I {i}" for i in range(9)] + self.Program
            return False
        except:return traceback.format_exc()

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
        except:return traceback.format_exc()
    
    def step(self):
        self.end_line = min(self.end_line + 1,len(self.Program)-41)
        self.run(self.end_line)

    def __repr__(self):
        s = [""]
        state = str(self.outwfs)
        if len(state) < 100:s.append("State :\t" + state)
        else:s.append("State :\t" + state[:30] + " .... " + state[-30:])
        psi = [self.outwfs[i] for i in range(2**9)]
        s.append("Psi :\t " + str(psi))
        # Registers
        s.append("\nRegisters\n")
        for i in range(32):
            reg = f"s{i}"
            regval = self.outqc[reg][0]
            regval_bin = "".join([str(x) for x in regval])
            regval_int = sum([regval[i]*2**(31-i) for i in range(32)])
            if regval_int >= 2**31 : regval_int = regval_int - 2**32
            regval_int = str(regval_int)
            reg_string = reg + "\t : 0b" +  regval_bin + " = " + regval_int
            s.append(reg_string)
        return "\n".join(s)

    def display(self,states=None,regs=range(32),canvas=None,ax=None):
        try:
            psi = [str(round(self.outwfs[i],4)) for i in range(2**9)]
            if states is None:
                psi = [psi[i] + r"& |" + str(i) + r"\rangle" for i in range(2**9) if psi[i]!="0j"]
                if len(psi) > 32:psi = psi[:15] + [r"\vdots"]*2 +  psi[-15:]
            else:
                psi = [psi[i] + r"& |" + str(i) + r"\rangle" for i in states] + [r"\vdots"]
            psi = r"\begin{bmatrix}" + (r" \\ ").join(psi) + r"\end{bmatrix}"
            s = [r"\text{register} & \text{binary value} & \text{signed decimal}"]
            for i in regs:
                reg = f"s{i}"
                regval = self.outqc[reg][0]
                regval_bin = "".join([str(x) for x in regval])
                regval_int = sum([regval[i]*2**(31-i) for i in range(32)])
                if regval_int >= 2**31 : regval_int = regval_int - 2**32
                regval_int = str(regval_int)
                reg_string = reg + " & " +  regval_bin + " & " + regval_int
                s.append(reg_string)
            R = r"\begin{bmatrix}" + r"\\ ".join(s) +r" \end{bmatrix}"
            Full = r"$$ \boxed{\begin{matrix}" + r"|\Psi\rangle & C \\" + r" &".join([psi,R])+ r"\end{matrix}} $$"
            f = open("out.md",'w')
            f.write(Full)
            f.close()
            preview(Full,viewer="file",filename="QVMout.png")
            return False
        except:
            return traceback.format_exc()

    def run_and_display(self,i=None):
        self.run(i)
        return self.display()


if __name__=="__main__":
    # Create the main window
    parent = tk.Tk()
    parent.title("9q")
    PO = ProgramOutput("")
    PO.run_and_display()

    image = tk.PhotoImage(file="QVMout.png")
    image_label = tk.Label(parent, image=image,borderwidth=5,relief='solid')
    def start_tryout():
        compiled_program.configure(bg='yellow')
        compiled_program.bg = 'yellow'
        Thread(target=compute, daemon=True).start()

    def compute():
        try:
            compiled_program.delete("1.0",'end')
            S = og_program.get("1.0","end-1c")
            S = S.split("\n")
            S = [extract_inst(s,PO.qc) for s in S]
            P = "\n".join(S)
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
            image = tk.PhotoImage(file="QVMout.png")
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
    og_program_label = tk.Label(parent,text="Program")
    compiled_program_label = tk.Label(parent,text="Compiled Program")
    output_label = tk.Label(parent,text="States and Memory")
    og_program = tk.Text(parent,bg='light yellow',width=30,height=29,borderwidth=3,relief='solid')
    compiled_program = tk.Text(parent,bg='light green',width=30,height=29,borderwidth=3,relief='solid')
    compile_button=tk.Button(command = start_tryout, text = "Compile and Run",borderwidth=3) ###
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
