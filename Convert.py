from pyquil import Program
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