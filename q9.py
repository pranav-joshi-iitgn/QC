from pyquil import Program,get_qc
from pyquil.api import WavefunctionSimulator
from numpy import round
from sympy import preview
import traceback
from IPython.display import display_latex,Latex

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


QUILE_TO_QUIL = {"ANDREG":ANDREG,
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
        #self.Program = [f"DECLARE s{i} BIT[32]" for i in range(32)] + self.Program

    def Burn(self,P):
        try:
            P = preproc(P)
            P = "\n".join([f"DECLARE s{i} BIT[32]" for i in range(32)]) + "\n" + P
            P = Program(P)
            #P = self.qc.compile(P)
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
                if regval_int >= 2**31 : regval_int = regval_int - 2**32
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
            f = open("out.md",'w')
            f.write(Full)
            f.close()
            preview(Full,viewer="file",filename="QVMout.png")
            return False
            return Latex(Full)
        except:
            return traceback.format_exc()

    def run_and_display(self,i=None):
        self.run(i)
        return self.display()
