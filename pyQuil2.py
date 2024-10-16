from q9 import *
if __name__=="__main__":
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
            S = og_program.get("1.0","end-1c")
            #S = open("mips_program.txt").read()
            S = S.split("\n")
            S = [extract_inst(s,PO.qc) for s in S]
            P = "\n".join(S)
            #print(S,"\n")
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
