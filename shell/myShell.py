#! /usr/bin/env python3
import os, sys, time, re


debug = 0
pid = os.getpid()

while 1:
    '''
    While waitForPid: #wait for child to be reaped if not in background
        Wait with hang and report
            if zombie was waitForPid
                waitForPid = None
    while any other children have terminated
        wait without hang and report
    '''
    os.write(1, f"{os.getcwd()}$ ".encode())
    cmd = os.read(0, 100)
    cmd = cmd.decode().strip().split(" ")
    match cmd[0]:
        case '': pass
        case 'cd': 
            '''
            if theres stuff after cd 
                Get target directory
                append it to current directory
                set directory to new directory
            else
                set the directory to home?
            '''
            os.write(1, b'Totally changed the directory trust me bro\n')
        case 'exit': sys.exit(1)
        case 'Theres a pipe here':
            pr,pw = os.pipe()
            for f in (pr, pw):
                os.set_inheritable(f, True)
            print("pipe fds: pr=%d, pw=%d" % (pr, pw))

            import fileinput

            print("About to fork (pid=%d)" % pid)

            rc = os.fork()

            if rc < 0:
                print("fork failed, returning %d\n" % rc, file=sys.stderr)
                sys.exit(1)

            elif rc == 0:                   #  child - will write to pipe
                print("Child: My pid==%d.  Parent's pid=%d" % (os.getpid(), pid), file=sys.stderr)
                args = ["wc", "p3-exec.py"]

                os.close(1)                 # redirect child's stdout
                os.dup(pw)
                for fd in (pr, pw):
                    os.close(fd)
                print("hello from child")
                        
            else:                           # parent (forked ok)
                print("Parent: My pid==%d.  Child's pid=%d" % (os.getpid(), rc), file=sys.stderr)
                os.close(0)
                os.dup(pr)
                for fd in (pw, pr):
                    os.close(fd)
                for line in fileinput.input():
                    print("From child: <%s>" % line)
        case _:
            os.write(1, ("About to fork (pid:%d)\n" % pid).encode())
            rc = os.fork()

            if rc < 0:
                os.write(2, ("fork failed, returning %d\n" % rc).encode())
                sys.exit(1)

            elif rc == 0:                   # child
                os.write(1, ("Child: My pid==%d.  Parent's pid=%d\n" % 
                            (os.getpid(), pid)).encode())
                args = cmd
                #Check for redirect
                if cmd[-2] == b'>':
                    os.close(1) # redirect child's stdout
                    os.open(cmd[-1], os.O_CREAT | os.O_WRONLY);
                    os.set_inheritable(1, True)
                #args = ["wc", "p3-exec.py"]
                for dir in re.split(":", os.environ['PATH']): # try each directory in the path
                    program = "%s/%s" % (dir, args[0])
                    os.write(1, ("Child:  ...trying to exec %s\n" % program).encode())
                    try:
                        os.execve(program, args, os.environ) # try to exec program
                    except FileNotFoundError:             # ...expected
                        pass                              # ...fail quietly

                os.write(2, ("Child:    Could not exec %s\n" % args[0]).encode())
                sys.exit(1)                 # terminate with error

            else:                           # parent (forked ok)
                os.write(1, ("Parent: My pid=%d.  Child's pid=%d\n" % 
                            (pid, rc)).encode())
                childPidCode = os.wait()
                os.write(1, ("Parent: Child %d terminated with exit code %d\n" % 
                            childPidCode).encode())